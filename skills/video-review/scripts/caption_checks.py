#!/usr/bin/env python
"""caption_checks.py: the captions, checked against the finished video they were made for.

  python caption_checks.py VIDEO.mp4 CAPTIONS_DIR [--overlays video_overlays.json] [--script SCRIPT.md] [--out DIR]
      -> DIR/captions_report.md and .json (default DIR: CAPTIONS_DIR); exit 1 if anything is to fix

Captions are the last step of a build, after the review, so the review cannot see them in the video; this runs inside
the captions stage, and review.py --captions DIR runs it too.

  words    every word heard in the video is in the captions, in order. A run of 4 or more heard words missing from them
           is a fix: Get Started's captions once lost 143 words this way, sentence openings above all ("Make sure you
           subscribe" at 5:18). A run of 4 or more caption words nobody says is a fix too. Heard = CAPTIONS_DIR/heard.json
           when it is newer than the video, otherwise the video is heard again (audio-captions' captions.hear).
  timing   a caption up over silence its whole time (no word heard, the sound quiet) -> fix; 2 s or more of speech with
           no caption up -> fix; a caption more than 0.5 s before its first word or 1 s after it -> check.
  text     audio-captions' checks.py: names spelled as the glossary says, two lines of 42 characters at most, no
           overlapping captions (fix); fast or short captions (check). With --script: a caption word where the script
           has a different, similar real word ("Dense factors" for "Dense vectors"): misheard as another real word,
           which no speller can catch (check: listen).
  burned   with CAPTIONS_DIR/captioned.mp4: the caption is found where the burn changed the picture against VIDEO, at the
           middle of every burned caption (captions.ass: shorter than the file's, with pauses between them). Over the name card (overlays) -> fix; over other text on screen (code, a card, read
           under the caption box in VIDEO) -> fix; over the mouth -> check.
"""
if __name__ == "__main__":                                   # run on the suite's own Python (.venv, made by setup.py), whichever python started it
    import os as _o, sys as _s, subprocess as _sp
    _v = _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), "..", "..", "..", ".venv", *(("Scripts", "python.exe") if _o.name == "nt" else ("bin", "python")))
    if _o.path.exists(_v) and _o.path.normcase(_o.path.realpath(_s.prefix)) != _o.path.normcase(_o.path.realpath(_o.path.dirname(_o.path.dirname(_v)))):
        _s.exit(_sp.call([_v, _o.path.realpath(__file__)] + _s.argv[1:]))
import argparse, difflib, json, os, re, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SK = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(SK, "audio-captions", "scripts"))
LIMITS = dict(run_words=4, gap_s=2.0, early_s=0.5, late_s=1.0)

def norm(w): return re.sub(r"[^a-z0-9]", "", w.lower())
def ts(t): return f"{int(t // 60)}:{t % 60:04.1f}"

def heard(video, cap_dir):
    p = os.path.join(cap_dir, "heard.json")
    if os.path.exists(p) and os.path.getmtime(p) > os.path.getmtime(video): return json.load(open(p, encoding="utf-8"))
    import captions as CP
    return CP.hear(video, p)

def words_and_timing(video, C, W):
    """C: [(s, e, lines)] from the SRT; W: heard words [{w, s, e}]"""
    F = []
    cw = [(norm(x), s) for s, e, L in C for x in " ".join(L).split() if norm(x)]
    hw = [(norm(w["w"]), w["s"]) for w in W if norm(w["w"])]
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, [h for h, _ in hw], [c for c, _ in cw], autojunk=False).get_opcodes():
        miss, extra = (i2 - i1) - (j2 - j1 if op == "replace" else 0), (j2 - j1) - (i2 - i1 if op == "replace" else 0)   # a respelling
        if op in ("delete", "replace") and miss >= LIMITS["run_words"]:                                                      # is a replace
            F.append(dict(t=hw[i1][1], kind="caption_missing", sev="fix", msg=f'{miss} words said here are not in the captions: "{" ".join(W_[0] for W_ in hw[i1:i2])[:70]}"'))
        if op in ("insert", "replace") and extra >= LIMITS["run_words"]:
            F.append(dict(t=cw[j1][1], kind="caption_extra", sev="fix", msg=f'{extra} caption words nobody says here: "{" ".join(c for c, _ in cw[j1:j2])[:70]}"'))
    import join_checks as JC
    env, quiet, _ = JC.envelope(video)
    spans = [(w["s"], w["e"]) for w in W]
    for s, e, L in C:
        on = [a for a, b in spans if a < e and b > s]
        loud = env[int(s * 100):max(int(s * 100) + 1, int(e * 100))]
        if not on and (len(loud) == 0 or float(np.percentile(loud, 90)) < quiet):
            F.append(dict(t=s, kind="caption_silent", sev="fix", msg=f'a caption over silence ({e - s:.1f} s, nothing said): "{" ".join(L)[:60]}"'))
        elif on:
            first = min(on)
            if s < first - LIMITS["early_s"]: F.append(dict(t=s, kind="caption_timing", sev="check", msg=f"up {first - s:.1f} s before its first word"))
            elif s > first + LIMITS["late_s"] and first >= s - 30: F.append(dict(t=s, kind="caption_timing", sev="check", msg=f"up {s - first:.1f} s after its first word"))
    up = np.zeros(int((max([e for _, e, _ in C] + [b for _, b in spans] + [0]) + 1) * 100), bool)
    for s, e, _ in C: up[int(s * 100):int(e * 100)] = True
    talk = np.zeros_like(up)
    for a, b in spans: talk[int(a * 100):int(b * 100)] = True
    for k in range(1, len(spans)):                                     # speech runs through short pauses between words
        if spans[k][0] - spans[k - 1][1] < 0.6: talk[int(spans[k - 1][1] * 100):int(spans[k][0] * 100)] = True
    bare = talk & ~up; i = 0
    while i < len(bare):
        if bare[i]:
            j = i
            while j < len(bare) and bare[j]: j += 1
            if (j - i) / 100 >= LIMITS["gap_s"]:
                said = " ".join(w["w"] for w in W if i / 100 <= w["s"] < j / 100)
                F.append(dict(t=i / 100, t1=j / 100, kind="caption_gap", sev="fix", msg=f'{(j - i) / 100:.1f} s of speech with no caption up: "{said[:60]}"'))
            i = j
        else: i += 1
    return F

def ass_cues(path):
    """the burned captions' own cues (they are shorter than the subtitle file's): [(s, e, [text])]"""
    sec = lambda x: (lambda h, m, s_: int(h) * 3600 + int(m) * 60 + float(s_))(*x.split(":"))
    out = []
    for ln in open(path, encoding="utf-8"):
        if ln.startswith("Dialogue:"):
            p = ln.rstrip("\n").split(",", 9); text = re.sub(r"\{[^}]*\}", "", p[9]).replace("\\N", " ")
            if out and out[-1][2] == [text] and abs(out[-1][1] - sec(p[1])) < 0.05: out[-1] = (out[-1][0], sec(p[2]), [text])   # a highlight's steps
            else: out.append((sec(p[1]), sec(p[2]), [text]))
    return out

def burned(video, captioned, C, overlays):
    """where the caption sits in the burned copy, and what it covers in the video under it; C = the burned cues"""
    F = []; a, b = cv2.VideoCapture(video), cv2.VideoCapture(captioned); fps = a.get(cv2.CAP_PROP_FPS) or 30
    face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml"); ocr = None
    for s, e, L in C:
        t = (s + e) / 2; i = int(t * fps)
        a.set(cv2.CAP_PROP_POS_FRAMES, i); b.set(cv2.CAP_PROP_POS_FRAMES, i); ok1, fa = a.read(); ok2, fb = b.read()
        if not (ok1 and ok2): continue
        d = cv2.absdiff(cv2.cvtColor(fa, cv2.COLOR_BGR2GRAY), cv2.cvtColor(fb, cv2.COLOR_BGR2GRAY)) > 40
        d = cv2.morphologyEx(d.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(d)
        boxes = [st[k] for k in range(1, n) if st[k][4] > 200]
        if not boxes:
            F.append(dict(t=t, kind="caption_burn", sev="fix", msg=f'the caption "{" ".join(L)[:40]}" is not in the burned copy', frame=i)); continue
        x0 = min(bx[0] for bx in boxes); y0 = min(bx[1] for bx in boxes); x1 = max(bx[0] + bx[2] for bx in boxes); y1 = max(bx[1] + bx[3] for bx in boxes)
        hit = lambda r: r[0] < x1 and r[0] + r[2] > x0 and r[1] < y1 and r[1] + r[3] > y0
        for o in overlays:
            if o.get("box") and o.get("t_in", 0) <= t <= o.get("t_out", 0) and hit(o["box"]):
                F.append(dict(t=t, kind="caption_covers", sev="fix", msg=f'the caption covers the {o.get("kind", "overlay").replace("_", " ")} ({o.get("name", "")}): move the captions up while it is on screen, or start them after it', frame=i))
        pad = 8; top = max(0, y0 - pad); strip = fa[top:y1 + pad]                         # the whole strip, so a word under the caption's
        if strip.size:                                                                    # edge is read whole, then kept if it is under it
            if ocr is None:
                from rapidocr_onnxruntime import RapidOCR
                ocr = RapidOCR()
            res, _ = ocr(cv2.resize(strip, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC))
            under = [txt for bx, txt, sc in (res or []) if float(sc) > 0.7 and len(norm(txt)) >= 3
                     and min(q[0] for q in bx) / 2 < x1 and max(q[0] for q in bx) / 2 > x0]
            if under: F.append(dict(t=t, kind="caption_covers", sev="fix", msg=f'the caption covers text on screen: "{" ".join(under)[:60]}"', frame=i))
        g = cv2.cvtColor(fa, cv2.COLOR_BGR2GRAY)
        for fx, fy, fw, fh in face.detectMultiScale(g, 1.2, 6, minSize=(fa.shape[0] // 8, fa.shape[0] // 8)):
            if hit((fx + fw // 4, fy + int(fh * 0.6), fw // 2, int(fh * 0.25))):       # the mouth: under the chin is fine
                F.append(dict(t=t, kind="caption_covers", sev="check", msg="the caption sits over the mouth", frame=i)); break
    return F

def against_script(C, script):
    """a caption word where the script has a different but similar word ("Dense factors" for "Dense vectors"): the
    transcript misheard it as another real word, which the speller cannot know; a person listens (check)"""
    from spellchecker import SpellChecker
    text = open(script, encoding="utf-8").read().replace("’", "'")
    text = "\n".join(l for l in text.splitlines() if l.strip() and not l.lstrip().startswith(("[", "<!--", "#", "|", ">")))   # the spoken lines
    sw = [norm(x) for x in re.findall(r"[\w'.-]+", text) if norm(x)]
    cw = [(norm(x), x.strip(".,:;!?"), s) for s, e, L in C for x in " ".join(L).split() if norm(x)]
    known, F, seen = SpellChecker(), [], set()
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, [c for c, _, _ in cw], sw, autojunk=False).get_opcodes():
        if op != "replace" or i2 - i1 != j2 - j1: continue
        for (c, shown, t), w in zip(cw[i1:i2], sw[j1:j2]):
            if len(c) >= 4 and len(w) >= 4 and c[:4] != w[:4] and c in known and w in known and difflib.SequenceMatcher(None, c, w).ratio() >= 0.6 and (c, w) not in seen:   # a shared stem (store, storing) was said that way
                seen.add((c, w)); F.append(dict(t=t, kind="caption_word", sev="check", msg=f'the caption says "{shown}" where the script says "{w}": listen, and fix the caption if it was "{w}"'))
    return F

def findings(video, cap_dir, overlays=None, script=None):
    import checks as CK
    srt = os.path.join(cap_dir, "captions.srt"); C = CK.parse_srt(srt)
    F = [dict(f, kind="caption_" + f["kind"]) for f in CK.srt_findings(srt)]
    F += words_and_timing(video, C, heard(video, cap_dir))
    if script and os.path.exists(script): F += against_script(C, script)
    cp, ap_ = os.path.join(cap_dir, "captioned.mp4"), os.path.join(cap_dir, "captions.ass")
    if os.path.exists(cp) and os.path.exists(ap_):
        O = json.load(open(overlays, encoding="utf-8")) if overlays and os.path.exists(overlays) else []
        F += burned(video, cp, ass_cues(ap_), O)
    return group(sorted(F, key=lambda f: f["t"]))

def group(F, gap=12.0):
    """the same finding again and again (a list item under every caption for a minute): one line over its stretch"""
    out = []
    for f in F:
        last = next((o for o in reversed(out) if o["kind"] == f["kind"] and o["msg"] == f["msg"]), None)
        if last and f["t"] - last.get("t1", last["t"]) <= gap: last["t1"] = f.get("t1", f["t"]); last["n"] = last.get("n", 1) + 1
        else: out.append(dict(f))
    return out

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video"); ap.add_argument("captions"); ap.add_argument("--overlays"); ap.add_argument("--script"); ap.add_argument("--out")
    a = ap.parse_args(); out = a.out or a.captions; os.makedirs(out, exist_ok=True)
    F = findings(a.video, a.captions, a.overlays, a.script)
    nf, nc = sum(f["sev"] == "fix" for f in F), sum(f["sev"] == "check" for f in F)
    json.dump(dict(fix=nf, check=nc, findings=F), open(os.path.join(out, "captions_report.json"), "w"), indent=1, default=int)
    span = lambda f: ts(f["t"]) + (f"-{ts(f['t1'])}" if f.get("t1") and f["t1"] - f["t"] >= 0.5 else "") + (f" ({f['n']} times)" if f.get("n", 1) > 1 else "")
    L = ["# Captions checked against the video", "", f"{nf} to fix, {nc} to check.", ""] + [f"- {span(f)}  **{f['sev']}**  {f['kind']}: {f['msg']}" for f in F]
    open(os.path.join(out, "captions_report.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    for f in F: print(f"{span(f):22s} {f['sev']:5s} {f['kind']:16s} {f['msg']}")
    print(f"captions: {nf} to fix, {nc} to check -> {os.path.join(out, 'captions_report.md')}")
    return 1 if nf else 0

if __name__ == "__main__":
    sys.exit(main())
