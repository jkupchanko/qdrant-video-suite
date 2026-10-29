#!/usr/bin/env python
"""audit_audio_captions.py: how the 49 audited videos treat their voice and their captions, to set this skill's rules from.

  python audit_audio_captions.py CORPUS_DIR [--workers 4]   -> CORPUS_DIR/audio_captions_audit/{ID}.json

Uses the 360p copies and the words raw-edit's audit_raw_edit.py already transcribed (CORPUS_DIR/raw_edit_audit/ID_words.json),
over the first 5 minutes of each video (a look every 10 s; a second-by-second read where captions show).

  voice     integrated loudness (LUFS) and peak; the voice level, the level in the gaps between words (room noise or a
            music bed), and the difference (how clean the voice sits); the share of the voice's energy under 100 Hz (rumble a
            high-pass removes); the loudness range over 3 s windows (how much it is compressed)
  captions  every second, the text on screen (OCR) that matches the words being said around then: burned-in captions. For
            each: where it sits (height on the frame), how big (text height), how many words and lines at once, all capitals
            or not, how long it stays, and whether one word is coloured differently from the rest (a word highlight)
"""
if __name__ == "__main__":                                   # run on the suite's own Python (.venv, made by setup.py), whichever python started it
    import os as _o, sys as _s, subprocess as _sp
    _v = _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), "..", "..", "..", ".venv", *(("Scripts", "python.exe") if _o.name == "nt" else ("bin", "python")))
    if _o.path.exists(_v) and _o.path.normcase(_o.path.realpath(_s.prefix)) != _o.path.normcase(_o.path.realpath(_o.path.dirname(_o.path.dirname(_v)))):
        _s.exit(_sp.call([_v, _o.path.realpath(__file__)] + _s.argv[1:]))
import argparse, glob, json, os, re, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SK = os.path.dirname(os.path.dirname(HERE)); sys.path.append(os.path.join(SK, "video-review", "scripts"))
SPAN = 300.0

def norm(w): return re.sub(r"[^a-z0-9]", "", w.lower())

def audio(mp4, W):
    import imageio_ffmpeg, pyloudnorm as pyln
    x = np.frombuffer(subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", mp4, "-t", str(SPAN), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                                     capture_output=True).stdout, np.int16).astype(np.float64) / 32768
    sr = 16000; lufs = float(pyln.Meter(sr).integrated_loudness(x)); peak = float(20 * np.log10(np.abs(x).max() + 1e-9))
    n = len(x) // 160; env = 20 * np.log10(np.maximum(1e-6, np.sqrt((x[:n * 160].reshape(n, 160) ** 2).mean(axis=1))))
    inw = np.zeros(n, bool); gap = np.zeros(n, bool)
    for a, b in zip(W, W[1:]):
        inw[int(a["s"] * 100):int(a["e"] * 100)] = True
        if 0.15 <= b["s"] - a["e"] <= 1.0: gap[int(a["e"] * 100) + 3:int(b["s"] * 100) - 3] = True
    inw &= ~gap; voice = float(np.percentile(env[inw[:n]], 90)) if inw.any() else None; g = float(np.median(env[gap[:n]])) if gap.any() else None
    # rumble: the share of voiced energy under 100 Hz
    seg = x[: sr * 60]; sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2; f = np.fft.rfftfreq(len(seg), 1 / sr)
    low = float(sp[(f > 20) & (f < 100)].sum() / max(1e-12, sp[(f > 20) & (f < 8000)].sum()))
    st = [pyln.Meter(sr).integrated_loudness(x[i:i + 3 * sr]) for i in range(0, len(x) - 3 * sr, sr)]
    st = [v for v in st if v > -70]; lra = float(np.percentile(st, 95) - np.percentile(st, 10)) if len(st) > 10 else None
    return dict(lufs=round(lufs, 1), peak_db=round(peak, 1), voice_db=round(voice, 1) if voice else None, gap_db=round(g, 1) if g else None,
                clean_db=round(voice - g, 1) if voice and g else None, low_share=round(low, 4), lra=round(lra, 1) if lra else None)

def captions(mp4, W, step=1.0):
    import cv2
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR(); c = cv2.VideoCapture(mp4); H = c.get(4); Wd = c.get(3); out = []
    for t in np.arange(1.0, SPAN, step):
        c.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = c.read()
        if not ok: break
        said = {norm(w["w"]) for w in W if t - 3.0 <= w["s"] <= t + 2.0} - {""}
        if len(said) < 2: continue
        f = cv2.resize(f, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)            # 360p captions are small for OCR
        res, _ = ocr(f)
        for box, text, score in (res or []):
            toks = [norm(x) for x in text.split() if norm(x)]
            if len(toks) < 1 or score < 0.6: continue
            blob = "".join(toks); spoken = [k for k in said if len(k) >= 3]
            hit = sum(1 for k in toks if k in said) + (sum(1 for k in spoken if k in blob) if len(toks) <= 2 else 0)   # OCR glues words: "semanticsearch"
            if hit / len(toks) < 0.6 or (len(toks) == 1 and len(toks[0]) < 4 and hit < 2): continue
            ys = [p[1] / 2 for p in box]; xs = [p[0] / 2 for p in box]; y0, y1 = min(ys), max(ys); x0, x1 = min(xs), max(xs)
            crop = f[int(y0 * 2):int(y1 * 2), int(x0 * 2):int(x1 * 2)]
            hl = False
            if crop.size:                                        # a word in another colour: two clusters of saturated, bright pixels
                hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV).reshape(-1, 3); bright = hsv[(hsv[:, 2] > 200)]
                white = (bright[:, 1] < 50).mean() if len(bright) else 0; sat = bright[bright[:, 1] > 140]
                hl = len(bright) > 60 and 0.15 < len(sat) / len(bright) < 0.7 and white > 0.25   # white text with a strongly coloured part
            out.append(dict(t=float(t), text=text, words=len(toks), y=round((y0 + y1) / 2 / H, 3), h=round((y1 - y0) / H, 3), x=round((x0 + x1) / 2 / Wd, 3),
                            caps=text.upper() == text and any(ch.isalpha() for ch in text), hl=bool(hl)))
    return out

def caption_track(C, speech_s):
    """captions, not slides: text that matches the words being said, in one band of the frame, changing as the words go by.
    A slide that repeats the speech holds still; a caption changes most seconds. Control (2026-10-26): the same video with its
    own words burned in -> 56 of 59 speech seconds; without them, slides and animated text that echo the speech -> 0"""
    bands = {}
    for x in C: bands.setdefault(round(x["y"] * 10) / 10, []).append(x)
    keep = []
    for y, xs in bands.items():
        by = {}
        for x in xs: by.setdefault(x["t"], []).append(norm(x["text"]))           # "Google,and" and "Google and" are the same text
        ts = sorted(by); pairs = [(a, b) for a, b in zip(ts, ts[1:]) if b - a <= 1.01]
        change = sum(1 for a, b in pairs if sorted(by[a]) != sorted(by[b])) / max(1, len(pairs))
        if len(ts) >= max(5, 0.4 * speech_s) and change >= 0.5: keep += xs       # captions run the whole time; animated text comes and goes
    return keep

def one(mp4, odir, corpus):
    vid = os.path.basename(mp4)[:-4]; p = os.path.join(odir, vid + ".json")
    if os.path.exists(p): return json.load(open(p))
    wp = os.path.join(corpus, "raw_edit_audit", vid + "_words.json")
    W = json.load(open(wp, encoding="utf-8")) if os.path.exists(wp) else []
    if len(W) < 200: r = dict(id=vid, words=len(W)); json.dump(r, open(p, "w")); return r
    A = audio(mp4, W); speech_s = sum(1 for t in range(1, int(SPAN)) if len({norm(w["w"]) for w in W if t - 3 <= w["s"] <= t + 2}) >= 2)
    # two passes: a look every 10 s, and the full second-by-second read only where speech text keeps showing in one band
    # (reading 300 frames took ~25 min a video; most of the 49 have no captions)
    first = captions(mp4, W, step=10.0); bands = {}
    for x in first: bands.setdefault(round(x["y"] * 10) / 10, set()).add(x["t"])
    C = caption_track(captions(mp4, W), speech_s) if any(len(v) >= 6 for v in bands.values()) else []
    secs = sorted({x["t"] for x in C}); frames = {}
    for x in C: frames.setdefault(x["t"], []).append(x)
    lines = [len(v) for v in frames.values()]; words = [sum(y["words"] for y in v) for v in frames.values()]
    runs, cur, last = [], 0, None                                                          # how long one caption stays: same text, consecutive seconds
    for t in secs:
        txt = " ".join(sorted(y["text"] for y in frames[t]))
        cur = cur + 1 if (last and txt == last[1] and t - last[0] <= 1.01) else 1; last = (t, txt)
        if cur == 1: runs.append(1)
        else: runs[-1] = cur
    r = dict(id=vid, words=len(W), audio=A, caption_seconds=len(secs), caption_share=round(len(secs) / max(1, speech_s), 3),
             cap=dict(y=float(np.median([x["y"] for x in C])) if C else None, h=float(np.median([x["h"] for x in C])) if C else None,
                      x=float(np.median([x["x"] for x in C])) if C else None,
                      words_on_screen=float(np.median(words)) if words else None, lines=float(np.median(lines)) if lines else None,
                      caps=round(float(np.mean([x["caps"] for x in C])), 2) if C else None, highlight=round(float(np.mean([x["hl"] for x in C])), 2) if C else None,
                      stays_s=float(np.median(runs)) if runs else None), sample=[x["text"] for x in C[:8]])
    json.dump(r, open(p, "w"), indent=1); return r

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument("corpus"); ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(); odir = os.path.join(a.corpus, "audio_captions_audit"); os.makedirs(odir, exist_ok=True)
    from concurrent.futures import ProcessPoolExecutor, as_completed
    with ProcessPoolExecutor(a.workers) as ex:
        fut = {ex.submit(one, v, odir, a.corpus): v for v in sorted(glob.glob(os.path.join(a.corpus, "*.mp4")))}
        for f in as_completed(fut):
            try: r = f.result(); print(r["id"], r.get("audio", {}).get("lufs"), r.get("caption_share"), r.get("cap", {}).get("words_on_screen"), flush=True)
            except Exception as e: print(os.path.basename(fut[f]), "FAILED", e, flush=True)

if __name__ == "__main__":
    main()
