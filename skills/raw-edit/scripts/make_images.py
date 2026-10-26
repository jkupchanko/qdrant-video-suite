#!/usr/bin/env python
"""make_images.py: the pictures in this skill's README, drawn from a real take (the Get Started recording, 2026-10-22).

  python make_images.py --raw RAW.mp4 --literal words_literal.json --cut CUT_DIR --audit AUDIT_DIR --out ../images

  how-it-works.png   the six steps, each with a picture of what it does
  four-faults.png    the four faults on the real take: the sound, the words, what comes out and what goes back
  review-page.png    the review page (a screenshot of CUT_DIR/review.html, made with Playwright and Chrome)
  research.png       the 50 videos against our limits (from audit_raw_edit.py's results in AUDIT_DIR)
"""
import argparse, glob, json, os, re, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SK = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(SK, "video-review", "scripts"))
FONTS = os.path.join(SK, "brand-consistency", "assets", "fonts")
BG, PANEL, LINE, INK, SOFT, RED, BLUE, AMBER = (11, 15, 26), (20, 26, 40), (42, 50, 68), (238, 240, 244), (150, 158, 176), (220, 36, 76), (64, 140, 255), (240, 168, 58)

def F(size, w="Regular"): return ImageFont.truetype(os.path.join(FONTS, {"Regular": "MonaSans-Regular.ttf", "Bold": "MonaSans-Bold.ttf", "Semi": "MonaSans-SemiBold.ttf", "Mono": "GeistMono-Regular.ttf"}[w]), size)

class Take:
    def __init__(self, raw, literal):
        import join_checks as JC
        self.raw = raw; self.W = json.load(open(literal, encoding="utf-8"))
        self.env, self.quiet, self.loud = JC.envelope(raw); self.cap = cv2.VideoCapture(raw)
    def frame(self, t, crop=None, w=None):
        self.cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = self.cap.read()
        if crop: x, y, cw, ch = crop; f = f[y:y + ch, x:x + cw]
        im = Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
        return im.resize((w, int(w * im.height / im.width)), Image.LANCZOS) if w else im
    def words(self, t0, t1): return [w for w in self.W if t0 <= w["s"] < t1]

def wave(d, T, box, t0, t1, marks=(), labels=True, fs=17):
    """the take's loudness from t0 to t1 in box, marks = [(a, b, colour, text)], the words under it"""
    x0, y0, x1, y1 = box; top = y0 + (24 if any(m[3] for m in marks) else 0)          # room for the marks' labels above
    mid = (top + y1) // 2 - (14 if labels else 0); h = (y1 - top) // 2 - (30 if labels else 8)
    for a, b, col, txt in marks:
        xa, xb = x0 + (a - t0) / (t1 - t0) * (x1 - x0), x0 + (b - t0) / (t1 - t0) * (x1 - x0)
        d.rounded_rectangle([xa, top, xb, y1 - (30 if labels else 0)], 6, fill=tuple(int(c * 0.28 + p * 0.72) for c, p in zip(col, PANEL)), outline=col, width=2)
        if txt: d.text((min(max((xa + xb) / 2, x0 + d.textlength(txt, font=F(16, "Semi")) / 2), x1 - d.textlength(txt, font=F(16, "Semi")) / 2), y0), txt, font=F(16, "Semi"), fill=col, anchor="mt")
    lo, hi = T.quiet - 4, T.loud + 22
    for i in range(int(t0 * 100), int(t1 * 100)):
        v = float(np.clip((T.env[i] - lo) / (hi - lo), 0, 1)); x = x0 + (i / 100 - t0) / (t1 - t0) * (x1 - x0)
        hh = max(1, v * h); col = INK if v > 0.05 else SOFT
        for a, b, c, _ in marks:
            if a <= i / 100 <= b: col = c
        d.line([x, mid - hh, x, mid + hh], fill=col, width=2)
    if labels:
        last = -1e9
        for w in T.words(t0, t1):
            x = x0 + (w["s"] - t0) / (t1 - t0) * (x1 - x0)
            if x - last < 8: continue
            tw = d.textlength(w["w"], font=F(fs)); d.text((x, y1 - 24), w["w"], font=F(fs), fill=SOFT); last = x + tw

def panel(im, box, n, title, sub):
    d = ImageDraw.Draw(im); x0, y0, x1, y1 = box
    d.rounded_rectangle(box, 18, fill=PANEL, outline=LINE)
    d.ellipse([x0 + 22, y0 + 22, x0 + 58, y0 + 58], fill=RED); d.text((x0 + 40, y0 + 40), str(n), font=F(20, "Bold"), fill=INK, anchor="mm")
    d.text((x0 + 72, y0 + 22), title, font=F(26, "Bold"), fill=INK)
    yy = y0 + 64
    for line in wrap(d, sub, F(18), x1 - x0 - 50): d.text((x0 + 26, yy), line, font=F(18), fill=SOFT); yy += 25
    return d, yy

def wrap(d, text, font, width):
    out, cur = [], ""
    for w in text.split():
        if d.textlength((cur + " " + w).strip(), font=font) > width: out.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    return out + [cur]

def four_faults(T, out):
    W_, H_ = 1600, 900; im = Image.new("RGB", (W_, H_), BG); d = ImageDraw.Draw(im)
    d.text((40, 28), "The four faults, on a real take", font=F(34, "Bold"), fill=INK)
    d.text((40, 74), "The sound of the take, its words, and what the raw edit does: red comes out, blue goes back in.", font=F(20), fill=SOFT)
    boxes = [(40, 120, 790, 500), (810, 120, 1560, 500), (40, 515, 790, 885), (810, 515, 1560, 885)]
    # 1. said twice: "For the first, / for the first cluster" (8:21 of the take)
    d1, y = panel(im, boxes[0], 1, "Said twice", "A sentence started, stopped and said again. The first try comes out; the second stays.")
    wave(d1, T, (66, y + 20, 764, 480), 500.85, 504.75, [(501.02, 501.52, RED, "taken out")])
    # 2. a stop inside a sentence: "deploying and ... monitoring" (5:51)
    d2, y = panel(im, boxes[1], 2, "A stop mid-sentence", "A long silence where the sentence goes on. It is cut down to a natural pause, measured on you.")
    wave(d2, T, (836, y + 20, 1534, 480), 350.0, 354.6, [(351.82, 353.52, RED, "2.0 s cut to 0.3 s")])
    # 3. a glance at the end: "...allows you to" then the eyes go up (2:33 of the cut)
    d3, y = panel(im, boxes[2], 3, "A glance at a cut", "Stopped mid-thought, then the eyes leave the lens to think. The piece ends on the word, before they move.")
    for k, (t, lab) in enumerate(((697.2, "on the word"), (698.0, "+0.6 s"), (698.8, "+1.4 s"))):
        e = T.frame(t, crop=(500, 300, 240, 100), w=140); x = 300 + k * 156; im.paste(e, (x, y + 4))
        d3.text((x + 70, y + 66), lab, font=F(14), fill=RED if k else SOFT, anchor="mt")
    d3.text((66, y + 22), "the eyes, after the", font=F(16), fill=SOFT); d3.text((66, y + 44), "last word:", font=F(16), fill=SOFT)
    wave(d3, T, (66, y + 92, 764, 866), 694.9, 699.4, [(697.46, 699.4, RED, "eyes leave: the cut goes before")])
    # 4. words left out: "run requests, and" between two pieces of the line (2:36)
    d4, y = panel(im, boxes[3], 4, "Words left out", "Part of the script line was said but fell between two pieces. The phrase goes back in, whole.")
    wave(d4, T, (836, y + 20, 1534, 866), 703.0, 712.5, [(704.46, 706.86, RED, "pause"), (706.86, 708.44, BLUE, "put back"), (708.44, 709.40, RED, "")], fs=15)
    im.save(out); print("->", out)

def how_it_works(T, out, cut_dir, shot):
    W_, H_ = 1600, 960; im = Image.new("RGB", (W_, H_), BG); d = ImageDraw.Draw(im)
    d.text((40, 28), "How the raw edit is made", font=F(34, "Bold"), fill=INK)
    d.text((40, 74), "Your full recording and your script in; one clean pass out, each thought said once, looking at the viewer.", font=F(20), fill=SOFT)
    cw, ch = 492, 400; boxes = [(40 + c * (cw + 22), 120 + r * (ch + 22), 40 + c * (cw + 22) + cw, 120 + r * (ch + 22) + ch) for r in range(2) for c in range(3)]
    steps = [("Your raw take", "The whole recording, retakes and all. Nothing to trim first."),
             ("Every attempt, written down", "Each stretch between pauses is heard on its own, so a restart is written twice, where it was said."),
             ("Whole sentences, matched", "Each script line is matched to the sentence that says it best. Close is enough; it must make sense."),
             ("Measured on you", "Your own pauses and your eyes' resting place set the limits. Nobody else's numbers."),
             ("Fixed before you watch", "Restarts, stops, glances and dropped words are fixed, each cut placed in a pause."),
             ("You review by clicking", "A page with the cut and every flagged moment. Fine or Fix, or press M to add one.")]
    for k, (box, (t, s)) in enumerate(zip(boxes, steps)):
        dd, y = panel(im, box, k + 1, t, s); x0, _, x1, y1 = box; inner = (x0 + 26, y + 14, x1 - 26, y1 - 22)
        if k == 0:
            f = T.frame(30.0, w=inner[2] - inner[0]); f = f.crop((0, 0, f.width, min(f.height, inner[3] - inner[1]))); im.paste(f, (inner[0], inner[1]))
        elif k == 1:
            yy = inner[1] + 6
            for w0, w1, col in ((501.0, 501.5, RED), (501.5, 504.6, INK)):
                ws = T.words(w0, w1); ln = f"{int(ws[0]['s'] // 60)}:{ws[0]['s'] % 60:04.1f}  " + " ".join(w["w"] for w in ws)
                for line in wrap(dd, ln, F(19, "Mono"), inner[2] - inner[0]): dd.text((inner[0], yy), line, font=F(19, "Mono"), fill=col); yy += 30
                yy += 12
            dd.text((inner[0], yy + 8), "Whisper's usual transcript writes this once,", font=F(17), fill=SOFT); dd.text((inner[0], yy + 32), "and hides the restart.", font=F(17), fill=SOFT)
        elif k == 2:
            yy = inner[1] + 4
            for lab, txt, col in (("script", "Before you start building with Qdrant, you need somewhere to run it.", SOFT), ("said", "Before we get started building with Quadrant, we're going to need somewhere to actually run it.", INK)):
                dd.text((inner[0], yy), lab.upper(), font=F(14, "Semi"), fill=RED); yy += 22
                for line in wrap(dd, txt, F(19), inner[2] - inner[0]): dd.text((inner[0], yy), line, font=F(19), fill=col); yy += 27
                yy += 14
            dd.text((inner[0], yy), "match 0.86: kept, in your own words", font=F(17, "Semi"), fill=BLUE)
        elif k == 3:
            import raw_edit_checks as RE
            starts = [w["s"] for w in T.W]; mid = []
            for a, b in RE.quiet_runs(T.env > T.quiet):
                j = int(np.searchsorted(starts, a)) - 1
                if 0.1 <= b - a < 3 and j >= 0 and not re.search(r"[.,?!]$", T.W[j]["w"]): mid.append(b - a)
            S = RE.speaker(T.W, T.env, T.quiet); hist, edges = np.histogram(mid, bins=24, range=(0, 2.4))
            gx0, gy0, gx1, gy1 = inner[0], inner[1] + 10, inner[2], inner[3] - 40; bw = (gx1 - gx0) / len(hist)
            for i, n in enumerate(hist):
                hh = (gy1 - gy0) * n / hist.max(); col = RED if edges[i] >= S["stop"] else SOFT
                dd.rectangle([gx0 + i * bw + 2, gy1 - hh, gx0 + (i + 1) * bw - 2, gy1], fill=col)
            xs = gx0 + S["stop"] / 2.4 * (gx1 - gx0); dd.line([xs, gy0, xs, gy1], fill=RED, width=3)
            dd.text((xs + 8, gy0), f"your limit {S['stop']:.2f} s", font=F(17, "Semi"), fill=RED)
            dd.text((gx0, gy1 + 8), "your pauses inside a sentence, 0 to 2.4 s; red are cut down", font=F(16), fill=SOFT)
        elif k == 4:
            hh = (inner[3] - inner[1]) // 2 - 6
            dd.text((inner[0], inner[1]), "before", font=F(14, "Semi"), fill=SOFT); wave(dd, T, (inner[0], inner[1] + 18, inner[2], inner[1] + hh), 500.85, 504.75, [(501.02, 501.52, RED, "")], labels=False)
            dd.text((inner[0], inner[1] + hh + 10), "after", font=F(14, "Semi"), fill=SOFT); wave(dd, T, (inner[0], inner[1] + hh + 28, inner[2], inner[3]), 501.44, 504.75, [], labels=False)
        elif k == 5 and shot and os.path.exists(shot):
            s_ = Image.open(shot).convert("RGB"); s_.thumbnail((inner[2] - inner[0], inner[3] - inner[1])); im.paste(s_, (inner[0], inner[1]))
    im.save(out); print("->", out)

def review_shot(cut_dir, out):
    from playwright.sync_api import sync_playwright
    page = os.path.abspath(os.path.join(cut_dir, "review.html"))
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome"); pg = b.new_page(viewport={"width": 1440, "height": 820}, color_scheme="dark")
        pg.goto("file:///" + page.replace("\\", "/"))
        pg.wait_for_function("document.getElementById('v').readyState >= 1", timeout=30000); pg.wait_for_timeout(1500)   # no loading spinner
        pg.evaluate("document.querySelectorAll('.fix').forEach(b => b.click())")                                      # all marked Fix
        pg.screenshot(path=out); b.close()
    print("->", out)

def research(audit, out, ours=None):
    R = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(audit, "*.json"))) if not re.search(r"_(words|gaze)\.json$", f)]
    R = [r for r in R if r.get("words", 0) > 200]; O = json.load(open(ours)) if ours and os.path.exists(ours) else None
    W_, H_ = 1600, 860; im = Image.new("RGB", (W_, H_), BG); d = ImageDraw.Draw(im)
    d.text((40, 28), f"Checked against {len(R)} popular technical videos", font=F(34, "Bold"), fill=INK)
    d.text((40, 74), "The first five minutes of each, measured the way the raw edit measures your take.", font=F(20), fill=SOFT)
    cols = [(40, 120, 530, 840), (555, 120, 1045, 840), (1070, 120, 1560, 840)]
    # 1. each creator's own pause inside a sentence: the limit is learned, with a floor
    dd, y = panel(im, cols[0], 1, "Everyone pauses differently", "Each dot is one video: its creator's typical pause inside a sentence. Red: your approved cut.")
    v = sorted(r["speaker_pause"] for r in R); x0, x1 = cols[0][0] + 40, cols[0][2] - 40; gy = y + 30
    for i, p in enumerate(v):
        x = x0 + p / 0.5 * (x1 - x0); dd.ellipse([x - 6, gy + i * 8 - 6, x + 6, gy + i * 8 + 6], fill=SOFT)
    yb = gy + len(v) * 8 + 16
    if O: xo = x0 + O["speaker_pause"] / 0.5 * (x1 - x0); dd.ellipse([xo - 9, yb - 9, xo + 9, yb + 9], fill=RED); yb += 22
    dd.line([x0, yb, x1, yb], fill=LINE, width=2)
    for t in (0, 0.1, 0.2, 0.3, 0.4, 0.5): xx = x0 + t / 0.5 * (x1 - x0); dd.text((xx, yb + 8), f"{t:.1f}", font=F(15), fill=SOFT, anchor="mt")
    dd.text((x0, yb + 38), f"{v[0]:.2f} to {v[-1]:.2f} s, so the limit is learned", font=F(18, "Semi"), fill=INK)
    dd.text((x0, yb + 64), "from you: twice your pause, at least 0.5 s", font=F(18, "Semi"), fill=INK)
    # 2. how often a finished pro edit gets a fix from each check
    dd, y = panel(im, cols[1], 2, "Pro edits pass our checks", "Our checks run on each finished video as if it were our cut. Blue: videos with no fix at all.")
    keys = [("restart", "said twice"), ("stop", "stop mid-sentence"), ("glance", "glance at a cut")]
    for k, (key, lab) in enumerate(keys):
        n = [r["checks"].get(key, 0) for r in R]; zero = sum(1 for x in n if x == 0) / len(n); yy = y + 26 + k * 140
        dd.text((cols[1][0] + 30, yy), lab, font=F(21, "Semi"), fill=INK)
        dd.rounded_rectangle([cols[1][0] + 30, yy + 36, cols[1][2] - 30, yy + 70], 8, fill=LINE)
        dd.rounded_rectangle([cols[1][0] + 30, yy + 36, cols[1][0] + 30 + zero * (cols[1][2] - cols[1][0] - 60), yy + 70], 8, fill=BLUE)
        dd.text((cols[1][0] + 30, yy + 80), f"{sum(1 for x in n if x == 0)} of {len(n)} videos: none", font=F(17), fill=SOFT)
    dd.text((cols[1][0] + 30, y + 26 + 3 * 140), "Your approved cut: no fix from any of them.", font=F(18, "Semi"), fill=RED)
    # 3. glances: pros look away briefly all the time, so only long ones are flagged
    dd, y = panel(im, cols[2], 3, "Pros glance too", "Every look away from the lens of 0.3 s or more, across all the videos with a face.")
    g = [x for r in R if r.get("eyes") for x in r["eyes"]["glance_s"]]
    hist, edges = np.histogram(np.clip(g, 0, 2.39), bins=8, range=(0, 2.4)); gx0, gy0, gx1, gy1 = cols[2][0] + 30, y + 30, cols[2][2] - 30, y + 330; bw = (gx1 - gx0) / len(hist)
    for i, n in enumerate(hist):
        hh = (gy1 - gy0) * n / max(1, hist.max()); dd.rectangle([gx0 + i * bw + 3, gy1 - hh, gx0 + (i + 1) * bw - 3, gy1], fill=RED if edges[i] >= 1.0 else SOFT)
    for t in (0, 0.6, 1.2, 1.8, 2.4): xx = gx0 + t / 2.4 * (gx1 - gx0); dd.text((xx, gy1 + 8), f"{t:.1f} s", font=F(15), fill=SOFT, anchor="mt")
    per = np.median([r["eyes"]["glances_per_face_min"] for r in R if r.get("eyes") and r["eyes"]["face_s"] > 60])
    dd.text((gx0, gy1 + 44), f"{per:.0f} a minute, {np.mean(np.array(g) < 1.0) * 100:.0f}% under 1 s", font=F(18, "Semi"), fill=INK)
    dd.text((gx0, gy1 + 72), "so a glance is flagged from 1 s (red)", font=F(18, "Semi"), fill=INK)
    im.save(out); print("->", out)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--raw"); ap.add_argument("--literal"); ap.add_argument("--cut"); ap.add_argument("--audit"); ap.add_argument("--out", required=True)
    ap.add_argument("--ours", help="audit_raw_edit.py's result for our own approved cut, marked on research.png")
    ap.add_argument("--only", default="faults,how,review,research"); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); only = a.only.split(",")
    shot = os.path.join(a.out, "review-page.png")
    if "review" in only and a.cut: review_shot(a.cut, shot)
    if {"faults", "how"} & set(only):
        T = Take(a.raw, a.literal)
        if "faults" in only: four_faults(T, os.path.join(a.out, "four-faults.png"))
        if "how" in only: how_it_works(T, os.path.join(a.out, "how-it-works.png"), a.cut, shot)
    if "research" in only and a.audit: research(a.audit, os.path.join(a.out, "research.png"), a.ours)

if __name__ == "__main__":
    main()
