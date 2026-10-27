#!/usr/bin/env python
"""make_images.py: the pictures in this skill's README, drawn from a real cut (Get Started, 2026-10-22) and the 49-video research.

  python make_images.py --cut CUT_DIR --captions CAPTIONS_DIR --script SCRIPT.md --audit CORPUS_DIR --out ../images

CUT_DIR holds cut.mp4, cut_voice.mp4, cutlist.md, words.json and voice.json (the voice stage's outputs); CAPTIONS_DIR is
captions.py's output for that cut; CORPUS_DIR holds audio_captions_audit/ and voice_measure_49.json.

  how-it-works.png   the four steps: measure, clean only what is needed, even the pieces, captions from the script
  voice-levels.png   every piece of the cut, before and after evening
  captions.png       what the transcript heard against the caption, and a frame with the optional burned-in look
  research.png       the 49 videos against this skill's limits
"""
import argparse, glob, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SK = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE); sys.path.append(os.path.join(SK, "raw-edit", "scripts"))
import importlib.util, voice_clean as V, captions as CP
_s = importlib.util.spec_from_file_location("raw_edit_images", os.path.join(SK, "raw-edit", "scripts", "make_images.py")); RI = importlib.util.module_from_spec(_s); _s.loader.exec_module(RI)
F, panel, wrap, BG, PANEL, LINE, INK, SOFT, RED, BLUE, AMBER = (RI.F, RI.panel, RI.wrap, RI.BG, RI.PANEL, RI.LINE, RI.INK, RI.SOFT, RI.RED, RI.BLUE, RI.AMBER)   # raw-edit's look

def levels(cut_dir):
    P = V.pieces(os.path.join(cut_dir, "cutlist.md"), 1e9)
    b = V.measure(V.decode(os.path.join(cut_dir, "cut.mp4")), P); a = V.measure(V.decode(os.path.join(cut_dir, "cut_voice.mp4")), P)
    return b, a

def respelled(cut_dir, script):
    """(heard, caption) pairs where the caption changed what the transcript wrote"""
    W = json.load(open(os.path.join(cut_dir, "words.json"), encoding="utf-8")); G = CP.glossary(); out = []
    for g, line in CP.placed(W, CP.rows(os.path.join(cut_dir, "cutlist.md"))):
        for (h, _, _), (c, _, _) in zip(g, CP.respell(g, line if not line.startswith("(") else "", G)):
            if h.strip(".,?!") != c.strip(".,?!") and (h.strip(".,?!"), c.strip(".,?!")) not in out: out.append((h.strip(".,?!"), c.strip(".,?!")))
    return sorted(out, key=lambda hc: CP.norm(hc[0]) == CP.norm(hc[1]))      # real misspellings first, then capitals for names

def dots(d, box, before, after, med, lo, hi, r=4):
    x0, y0, x1, y1 = box; n = len(before); Y = lambda v: y1 - (v - lo) / (hi - lo) * (y1 - y0)
    d.rectangle([x0, Y(med + 1.5), x1, Y(med - 1.5)], fill=tuple(int(c * 0.22 + p * 0.78) for c, p in zip(BLUE, PANEL)))
    d.line([x0, Y(med), x1, Y(med)], fill=BLUE, width=2)
    for i, (b, a) in enumerate(zip(before, after)):
        if b is None or a is None: continue
        x = x0 + (i + 0.5) / n * (x1 - x0); off = abs(b - med) > 1.5
        if off and abs(a - b) > 0.3: d.line([x, Y(b), x, Y(a)], fill=SOFT, width=1)
        d.ellipse([x - r, Y(b) - r, x + r, Y(b) + r], fill=RED if off else SOFT)
        d.ellipse([x - r, Y(a) - r, x + r, Y(a) + r], outline=BLUE, width=2)
    return Y

def voice_levels(B, A, out):
    W_, H_ = 1600, 720; im = Image.new("RGB", (W_, H_), BG); d = ImageDraw.Draw(im)
    d.text((40, 28), "One level: every piece of a real cut, before and after", font=F(34, "Bold"), fill=INK)
    d.text((40, 74), f"Get Started, {len(B['piece_db'])} pieces. Red pieces sat more than 1.5 dB off the cut's own level; each moved to the blue band.", font=F(20), fill=SOFT)
    d.rounded_rectangle([40, 120, 1560, 690], 18, fill=PANEL, outline=LINE)
    vals = [v for v in B["piece_db"] + A["piece_db"] if v is not None]; lo, hi = min(vals) - 1, max(vals) + 1
    Y = dots(d, (120, 160, 1530, 600), B["piece_db"], A["piece_db"], A["median_db"], lo, hi)
    for v in range(int(np.ceil(lo)), int(hi) + 1, 2): d.text((70, Y(v)), f"{v}", font=F(15, "Mono"), fill=SOFT, anchor="lm")
    d.text((70, 610), "dB", font=F(15, "Mono"), fill=SOFT, anchor="lt")
    d.ellipse([120, 638, 132, 650], fill=RED); d.text((142, 644), "before (off level)", font=F(17), fill=SOFT, anchor="lm")
    d.ellipse([330, 638, 342, 650], fill=SOFT); d.text((352, 644), "before (already level)", font=F(17), fill=SOFT, anchor="lm")
    d.ellipse([580, 638, 592, 650], outline=BLUE, width=2); d.text((602, 644), "after", font=F(17), fill=SOFT, anchor="lm")
    d.text((1530, 644), f"joins jumping over 3 dB: {B['jumps_over_3db']} before, {A['jumps_over_3db']} after", font=F(19, "Semi"), fill=INK, anchor="rm")
    im.save(out); print("->", out)

def burned_frame(cut_dir, cap_dir, t, out):
    import imageio_ffmpeg
    fonts = os.path.join(SK, "brand-consistency", "assets", "fonts").replace("\\", "/").replace(":", "\\:")
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-y", "-i", os.path.abspath(os.path.join(cut_dir, "cut_voice.mp4")),
                    "-vf", f"subtitles=captions.ass:fontsdir='{fonts}'", "-ss", str(t), "-frames:v", "1", os.path.abspath(out)], check=True, cwd=cap_dir)
    return Image.open(out).convert("RGB")

def captions_img(pairs, srt, frame, out):
    W_, H_ = 1600, 820; im = Image.new("RGB", (W_, H_), BG); d = ImageDraw.Draw(im)
    d.text((40, 28), "Captions: what was said, spelled the way the script spells it", font=F(34, "Bold"), fill=INK)
    d.text((40, 74), "The transcript hears sounds; the script knows the names. A real word said differently stays as it was said.", font=F(20), fill=SOFT)
    dl, y = panel(im, (40, 120, 760, 790), 1, "Heard, then captioned", "From the Get Started cut: every word the captions changed.")
    dl.text((66, y + 14), "HEARD", font=F(14, "Semi"), fill=SOFT); dl.text((380, y + 14), "CAPTION", font=F(14, "Semi"), fill=BLUE); y += 44
    for h, c in pairs[:9]:
        dl.text((66, y), h, font=F(24, "Mono"), fill=SOFT); dl.text((330, y), "->", font=F(24, "Mono"), fill=SOFT); dl.text((380, y), c, font=F(24, "Mono"), fill=INK); y += 42
    dl.text((66, 740), f"{len(pairs)} different words respelled across {len(CP.re.findall(r'-->', open(srt, encoding='utf-8').read()))} captions", font=F(18, "Semi"), fill=BLUE)
    dr, y = panel(im, (780, 120, 1560, 790), 2, "A file, or burned in", "captions.srt and .vtt go to YouTube (the default, as all 49 pros do). With --burn-captions, a copy in the picture:")
    f = frame.resize((640, int(640 * frame.height / frame.width)), Image.LANCZOS); im.paste(f, (806, y + 12))
    first = open(srt, encoding="utf-8").read().split("\n\n")[0].splitlines()
    yy = y + 24 + f.height
    dr.text((806, yy), "captions.srt", font=F(15, "Semi"), fill=SOFT); yy += 24
    for line in first: dr.text((806, yy), line, font=F(17, "Mono"), fill=INK); yy += 24
    im.save(out); print("->", out)

def strip(d, box, vals, limit, label, unit, fmt, ours=None, lo=None, hi=None, note=""):
    x0, y0, x1, y1 = box; lo = min(vals) if lo is None else lo; hi = max(vals) if hi is None else hi; X = lambda v: x0 + (min(max(v, lo), hi) - lo) / (hi - lo) * (x1 - x0)
    d.text((x0, y0), label, font=F(22, "Bold"), fill=INK); d.text((x1, y0 + 4), note, font=F(17), fill=SOFT, anchor="ra")
    cy = y0 + 70; d.line([x0, cy, x1, cy], fill=LINE, width=2)
    seen = {}
    for v in sorted(vals):
        k = round(X(v) / 9); seen[k] = seen.get(k, 0) + 1; yy = cy - 12 * (seen[k] - 1)
        if seen[k] > 4:                                                     # a tall pile (values past the axis end): a count, not a tower
            if seen[k] == 5: d.text((X(v), yy + 2), "+", font=F(15, "Semi"), fill=SOFT, anchor="mm")
            continue
        d.ellipse([X(v) - 5, yy - 5, X(v) + 5, yy + 5], fill=SOFT if limit is None or not limit[1](v) else AMBER)
    if limit is not None:
        d.line([X(limit[0]), y0 + 34, X(limit[0]), cy + 22], fill=RED, width=3); d.text((X(limit[0]) + 6, cy + 10), limit[2], font=F(16, "Semi"), fill=RED)
    if ours is not None:
        d.polygon([(X(ours), cy + 8), (X(ours) - 8, cy + 22), (X(ours) + 8, cy + 22)], fill=BLUE); d.text((X(ours), cy + 26), "Get Started", font=F(15), fill=BLUE, anchor="mt")
    d.text((x0, cy + 50), fmt(lo) + unit, font=F(15, "Mono"), fill=SOFT); d.text((x1, cy + 50), fmt(hi) + unit, font=F(15, "Mono"), fill=SOFT, anchor="ra")

def research(audit, B, out):
    R = [json.load(open(p)) for p in glob.glob(os.path.join(audit, "audio_captions_audit", "*.json"))]; M = json.load(open(os.path.join(audit, "voice_measure_49.json")))
    burned = sum(1 for r in R if r.get("caption_share")); n = len(R)
    W_, H_ = 1600, 1000; im = Image.new("RGB", (W_, H_), BG); d = ImageDraw.Draw(im)
    d.text((40, 28), f"{n} popular technical videos, against this skill's limits", font=F(34, "Bold"), fill=INK)
    d.text((40, 74), "Each dot is one video. Amber is past the limit, where the voice tool would step in; the rest are left alone.", font=F(20), fill=SOFT)
    d.rounded_rectangle([40, 120, 1560, 270], 18, fill=PANEL, outline=LINE)
    d.text((70, 140), "Captions burned into the picture", font=F(22, "Bold"), fill=INK)
    for i in range(n): x = 70 + i * 29; d.ellipse([x, 190, x + 20, 210], fill=RED if i < burned else LINE)
    d.text((70, 228), f"{burned} of {n}: none. Captions ship as a file to upload; burning in is an option.", font=F(19, "Semi"), fill=BLUE)
    d.rounded_rectangle([40, 290, 1560, 970], 18, fill=PANEL, outline=LINE)
    snr = [m[1] for m in M]; low = [m[2] * 100 for m in M]; lufs = [r["audio"]["lufs"] for r in R]
    strip(d, (90, 320, 1510, 480), snr, (30, lambda v: v < 30, "denoise under 30 dB"), "Voice above the room", " dB", lambda v: f"{v:.0f}", ours=B["snr_db"], lo=20, hi=60,
          note=f"median {np.median(snr):.1f} dB; {sum(v < 30 for v in snr)} under the limit")
    strip(d, (90, 540, 1510, 700), low, (5, lambda v: v > 5, "high-pass over 5%"), "Energy under 100 Hz (rumble)", "%", lambda v: f"{v:.0f}", ours=B["low_share"] * 100, lo=0, hi=20,
          note=f"median {np.median(low):.1f}%; {sum(v > 5 for v in low)} over the limit")
    strip(d, (90, 760, 1510, 920), lufs, (-14, lambda v: False, "our master: -14 LUFS"), "Loudness", " LUFS", lambda v: f"{v:.0f}", lo=-34, hi=-12,
          note=f"median {np.median(lufs):.1f} LUFS; YouTube never turns a quiet video up")
    im.save(out); print("->", out)

def how_it_works(B, A, pairs, frame, rep, out):
    W_, H_ = 1600, 900; im = Image.new("RGB", (W_, H_), BG); d = ImageDraw.Draw(im)
    d.text((40, 28), "How the voice and captions are made", font=F(34, "Bold"), fill=INK)
    d.text((40, 74), "Your cut in; one even, clean voice and captions spelled like your script out. Each step measures first.", font=F(20), fill=SOFT)
    boxes = [(40, 120, 790, 500), (810, 120, 1560, 500), (40, 515, 790, 885), (810, 515, 1560, 885)]
    d1, y = panel(im, boxes[0], 1, "Measure the take", "The room, the hum, the rumble and every piece's level, on this take: no fixed recipe.")
    for k, (lab, val) in enumerate((("voice above the room", f"{B['snr_db']:.0f} dB"), ("energy under 100 Hz", f"{B['low_share'] * 100:.1f}%"),
                                    ("mains hum", "none" if not B["hum"] or max(B["hum"].values()) < 6 else f"{max(B['hum'].values())} dB"),
                                    ("pieces off level", f"{sum(1 for v in B['piece_db'] if v is not None and abs(v - B['median_db']) > 1.5)} of {len(B['piece_db'])}"))):
        d1.text((66, y + 24 + k * 46), lab, font=F(21), fill=SOFT); d1.text((764, y + 24 + k * 46), val, font=F(22, "Semi"), fill=INK, anchor="ra")
    d2, y = panel(im, boxes[1], 2, "Fix only what it needs", "Each fix has a limit set from 49 pro videos. Under it, the take is left alone.")
    for k, (lab, on) in enumerate((("denoise if under 30 dB", B["snr_db"] < 30), ("high-pass if over 5%", B["low_share"] > 0.05),
                                   ("notch if hum 6 dB or more", bool(B["hum"]) and max(B["hum"].values()) >= 6), ("even pieces 1.5 dB off", True))):
        d2.text((836, y + 24 + k * 46), lab, font=F(21), fill=SOFT); d2.text((1534, y + 24 + k * 46), "done" if on else "not needed", font=F(22, "Semi"), fill=BLUE if on else SOFT, anchor="ra")
    d2.text((836, y + 220), "and the voice never moves: same length to the sample", font=F(17), fill=SOFT)
    d3, y = panel(im, boxes[2], 3, "One level", f"Every piece within 1 dB of the cut's own level. Joins over 3 dB: {B['jumps_over_3db']} -> {A['jumps_over_3db']}.")
    dots(d3, (70, y + 20, 760, 860), B["piece_db"], A["piece_db"], A["median_db"], min(v for v in B["piece_db"] if v is not None) - 1, max(v for v in B["piece_db"] if v is not None) + 1, r=3)
    d4, y = panel(im, boxes[3], 4, "Captions from the script", "What was said, spelled like the script; a file to upload, or burned in.")
    for k, (h, c) in enumerate(pairs[:3]):
        d4.text((836, y + 16 + k * 38), h, font=F(20, "Mono"), fill=SOFT); d4.text((1060, y + 16 + k * 38), "->  " + c, font=F(20, "Mono"), fill=INK)
    f = frame.crop((280, 760, 1640, 1000)).resize((698, int(698 * 240 / 1360)), Image.LANCZOS); im.paste(f, (836, 885 - 22 - f.height))
    im.save(out); print("->", out)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cut", required=True); ap.add_argument("--captions", required=True); ap.add_argument("--script", required=True)
    ap.add_argument("--audit", required=True); ap.add_argument("--out", default=os.path.join(os.path.dirname(HERE), "images"))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    B, A = levels(a.cut); pairs = respelled(a.cut, a.script); rep = json.load(open(os.path.join(a.cut, "voice.json")))
    print("respelled:", pairs)
    frame = burned_frame(a.cut, a.captions, 5.0, os.path.join(a.captions, "frame_burned.png"))
    voice_levels(B, A, os.path.join(a.out, "voice-levels.png"))
    captions_img(pairs, os.path.join(a.captions, "captions.srt"), frame, os.path.join(a.out, "captions.png"))
    research(a.audit, B, os.path.join(a.out, "research.png"))
    how_it_works(B, A, pairs, frame, rep, os.path.join(a.out, "how-it-works.png"))

if __name__ == "__main__":
    main()
