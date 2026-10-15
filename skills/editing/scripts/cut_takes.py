#!/usr/bin/env python
"""cut_takes.py: turn a raw talking-head recording and its script into a clean cut.

  python cut_takes.py RAW.mp4 SCRIPT.md --out DIR [--max-seconds 30] [--mirror] [--bars 72] [--push 1.06]
                      [--handle-in 0.08 --handle-out 0.3] [--model small.en]

What it does, in order:
  1. transcribes the recording with word timestamps
  2. finds every take of every script line (retakes, stumbles, ad-libs), and keeps the last complete one
  3. checks eye contact on every chosen take, frame by frame, and reports any look-away
  4. cuts each take on word boundaries with short handles; drops ad-libs between lines
  5. mirrors the picture (--mirror), covers a recording tag with matching bars top and bottom (--bars N px),
     alternates a slight push between cuts (--push), fades the audio 20 ms at every join
  6. writes cut.mp4, cutlist.md (which take each line came from), gaze_sheet.png (the eyes on every take)
Stops at --max-seconds on a sentence boundary when given. Spoken wording wins over the script: the cut keeps
what was said; the cut list shows where it differs.
"""
import argparse, json, os, re, subprocess, sys
import numpy as np

def norm(s): return re.sub(r"[^a-z0-9 ]+", " ", s.lower().replace("’", "").replace("'", "")).split()

def script_lines(path):
    out = []
    for l in open(path, encoding="utf-8"):
        l = l.strip()
        if not l or l.startswith(("#", "[", "**", "🎥", "🎙", "💻", "✅", "⚖", "```", "<")) or l.isupper() or len(l.split()) < 3: continue
        if re.match(r"^(🎥|🎙|💻|✅|⚖)", l): continue
        out.append(l)
    return out

def transcribe(path, model_name):
    from faster_whisper import WhisperModel
    import imageio_ffmpeg
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.float32)
    m = WhisperModel(model_name, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(audio, language="en", vad_filter=True, beam_size=2, word_timestamps=True)
    words = []
    for s in segs:
        for w in (s.words or []): words.append({"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)})
    return words

def fuzzy_eq(a, b):
    """spoken vs scripted word: exact; or, for words of 5+ letters, the same first four letters or a close spelling
    (amount/amounts, store/storing, quadrant/qdrant). Short words must match exactly, so 'the' never equals 'there'."""
    if a == b: return True
    if len(a) >= 5 and len(b) >= 5:
        if a[:4] == b[:4]: return True
        import difflib
        return difflib.SequenceMatcher(None, a, b).ratio() >= 0.8
    return False

def find_takes(words, line, min_cover=0.6):
    """windows of the transcript that cover the script line: (start_idx, end_idx, coverage, extra_words).
    Alignment is a small LCS so a changed word (every/all, isn't/does) does not stall the match."""
    target = norm(line); n = len(target)
    if n == 0: return []
    W = [(norm(w["w"]) or [""])[0] for w in words]
    takes = []
    for i in range(len(W)):
        if not fuzzy_eq(W[i], target[0]): continue
        best = None
        for L in range(max(2, int(n * 0.6)), min(len(W) - i, int(n * 1.8) + 3) + 1):
            seg = W[i:i + L]
            # LCS count between seg and target
            dp = [[0] * (n + 1) for _ in range(L + 1)]
            for x in range(1, L + 1):
                for y in range(1, n + 1):
                    dp[x][y] = dp[x - 1][y - 1] + 1 if fuzzy_eq(seg[x - 1], target[y - 1]) else max(dp[x - 1][y], dp[x][y - 1])
            m = dp[L][n]; cover = m / n; extra = L - m
            if not fuzzy_eq(seg[-1], target[-1]) and cover < 0.85: continue        # a take ends on the line's last word, unless nearly every word matched (a mis-heard last word)
            sc = cover - 0.06 * extra                                                 # extra words cost; the tightest full match wins
            if cover >= min_cover and (best is None or sc > best[4]):
                best = (i, i + L - 1, round(cover, 2), extra, sc)
        if best: takes.append(best)
    takes.sort(key=lambda t: t[0]); out = []
    for t in takes:
        if out and t[0] <= out[-1][1]:
            if t[4] >= out[-1][4] - 0.02: out[-1] = t       # overlapping windows: the later, tighter start wins (a restart replaces its stumble)
        else: out.append(t)
    return [t[:4] for t in out]

def eye_check(path, spans, step=0.5):
    """per chosen span, the share of sampled frames with a frontal face and both eyes near centre"""
    import cv2
    face_c = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml"); eye_c = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
    cap = cv2.VideoCapture(path); report = []; tiles = []
    for (a, b) in spans:
        t = a; ok_frames = 0; total = 0
        while t < b:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read()
            if ok:
                g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY); fs = face_c.detectMultiScale(g, 1.1, 5, minSize=(g.shape[0] // 6,) * 2); total += 1
                good = False
                if len(fs):
                    x, y, w, h = max(fs, key=lambda r: r[2] * r[3]); roi = g[y:y + int(h * 0.55), x:x + w]
                    eyes = [e for e in eye_c.detectMultiScale(roi, 1.1, 6, minSize=(int(w * 0.12),) * 2) if e[1] > h * 0.15]
                    if len(eyes) >= 2:
                        eyes = sorted(eyes, key=lambda e: e[0])[:2]; mid = np.mean([e[0] + e[2] / 2 for e in eyes]); yaw = (mid - w / 2) / w
                        good = abs(yaw) < 0.06
                    z = f[max(0, y - 20):y + h, max(0, x - 20):x + w + 20]
                    tiles.append(cv2.resize(z, (160, 160)) if z.size else np.zeros((160, 160, 3), np.uint8))
                ok_frames += good
            t += step
        report.append(round(ok_frames / max(1, total), 2))
    cap.release()
    return report, tiles

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raw"); ap.add_argument("script"); ap.add_argument("--out", required=True)
    ap.add_argument("--max-seconds", type=float); ap.add_argument("--mirror", action="store_true"); ap.add_argument("--bars", type=int, default=0, help="bar height in output px, top and bottom")
    ap.add_argument("--push", type=float, default=1.06, help="alternate 1.0 and this scale between cuts; 1.0 disables"); ap.add_argument("--handle-in", type=float, default=0.08); ap.add_argument("--handle-out", type=float, default=0.3)
    ap.add_argument("--model", default="small.en"); ap.add_argument("--size", default="1920x1080"); ap.add_argument("--max-gap", type=float, default=0.8, help="a silence longer than this inside a take is cut out")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    import imageio_ffmpeg; FF = imageio_ffmpeg.get_ffmpeg_exe()
    tp = os.path.join(a.out, "words.json")
    words = json.load(open(tp)) if os.path.exists(tp) else transcribe(a.raw, a.model)
    json.dump(words, open(tp, "w"))
    lines = script_lines(a.script); chosen = []; t_acc = 0.0
    for line in lines:
        takes = find_takes(words, line)
        if not takes: chosen.append((line, None, "NO TAKE FOUND: not said on the recording, or said too differently")); continue
        i, j, cover, extra = takes[-1]                       # the last take is the keeper (the retake a presenter settles on)
        note = f"take {len(takes)} of {len(takes)} at {words[i]['s']:.1f}s, cover {cover}" + (f", {extra} extra word(s)" if extra else "")
        # split at silences inside the take (a presenter pausing mid-line): each piece is its own cut
        pieces = []; p0 = i
        for q in range(i, j):
            if words[q + 1]["s"] - words[q]["e"] > a.max_gap: pieces.append((p0, q)); p0 = q + 1
        pieces.append((p0, j))
        total = sum(words[q1]["e"] + a.handle_out - max(0, words[q0]["s"] - a.handle_in) for q0, q1 in pieces)
        if a.max_seconds and t_acc + total > a.max_seconds + 0.5:
            chosen.append((line, None, f"beyond --max-seconds ({a.max_seconds}); the cut stops here")); break
        for k_, (q0, q1) in enumerate(pieces):
            a0 = max(0, words[q0]["s"] - a.handle_in); b0 = words[q1]["e"] + a.handle_out
            said = " ".join(w["w"] for w in words[q0:q1 + 1])
            chosen.append((line if k_ == 0 else "(same line, after a pause)", (a0, b0, said), note if k_ == 0 else f"pause of {words[q0]['s'] - words[q0 - 1]['e']:.1f} s removed")); t_acc += b0 - a0
    spans = [c[1][:2] for c in chosen if c[1]]
    gaze, tiles = eye_check(a.raw, spans)
    W, H = (int(v) for v in a.size.split("x")); parts = []; rows = []; t_edit = 0.0; k = 0
    import cv2
    src = cv2.VideoCapture(a.raw); sw, sh = int(src.get(cv2.CAP_PROP_FRAME_WIDTH)), int(src.get(cv2.CAP_PROP_FRAME_HEIGHT)); src.release()
    gi = 0
    for line, span, note in chosen:
        if not span: rows.append(("", "", "", line, "", note)); continue
        a0, b0, said = span; push = 1.0 if (k % 2 == 0 or a.push <= 1.0) else a.push; k += 1
        cw, ch = int(sw / push), int(sh / push); cx, cy = (sw - cw) // 2, (sh - ch) // 2
        vf = (("hflip," if a.mirror else "") + f"crop={cw}:{ch}:{cx}:{cy},scale={W}:{H}:flags=lanczos" +
              (f",drawbox=x=0:y=0:w={W}:h={a.bars}:color=black:t=fill,drawbox=x=0:y={H - a.bars}:w={W}:h={a.bars}:color=black:t=fill" if a.bars else "") + ",fps=30,format=yuv420p")
        d = b0 - a0; p = os.path.join(a.out, f"part_{len(parts):02d}.mp4")
        subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{a0:.3f}", "-to", f"{b0:.3f}", "-i", a.raw, "-vf", vf, "-af", f"afade=t=in:st=0:d=0.02,afade=t=out:st={d - 0.02:.3f}:d=0.02",
                        "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k", p], check=True)
        parts.append(p); g = gaze[gi]; gi += 1
        rows.append((f"{t_edit:.2f}", f"{a0:.2f}-{b0:.2f}", f"x{push:.2f}", line, said, note + f"; eyes on lens {int(g * 100)}%" + ("" if g >= 0.8 else "  <- CHECK"))); t_edit += d
    lst = os.path.join(a.out, "parts.txt"); open(lst, "w").write("".join(f"file '{os.path.abspath(p).replace(os.sep, '/')}'\n" for p in parts))
    out = os.path.join(a.out, "cut.mp4"); subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", out], check=True)
    if tiles:
        cols = 10; rows_img = [np.hstack(tiles[i:i + cols] + [np.zeros((160, 160, 3), np.uint8)] * (cols - len(tiles[i:i + cols]))) for i in range(0, len(tiles), cols)]
        cv2.imwrite(os.path.join(a.out, "gaze_sheet.png"), np.vstack(rows_img))
    with open(os.path.join(a.out, "cutlist.md"), "w", encoding="utf-8") as fh:
        fh.write(f"# Cut list: {os.path.basename(a.raw)}\n\n| edit time | source | push | script line | said | take and eyes |\n|---|---|---|---|---|---|\n")
        for r in rows: fh.write("| " + " | ".join(r) + " |\n")
        fh.write(f"\nTotal {t_edit:.1f} s, {len(parts)} cuts. " + ("Mirrored. " if a.mirror else "") + (f"Bars {a.bars} px top and bottom. " if a.bars else "") + (f"Push alternates 1.00 / {a.push:.2f}. " if a.push > 1 else "") + "20 ms audio fades at every join.\n")
    print(f"-> {out}  {t_edit:.1f} s, {len(parts)} cuts; cutlist.md, gaze_sheet.png")
    for r in rows:
        if "CHECK" in r[5] or "NO TAKE" in r[5] or "beyond" in r[5]: print("   note:", r[3][:60], "|", r[5])

if __name__ == "__main__":
    main()
