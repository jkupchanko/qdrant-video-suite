#!/usr/bin/env python
"""verify_pieces.py: listen to every piece of a cut on its own, and keep only the last attempt where a restart is heard.

  python verify_pieces.py CUT_DIR RAW.mp4 [--mirror] [--bars 72]

A transcript of a whole take smooths restarts away (Whisper writes "Now this can be useful if you want more of a... /
Now this can be useful if you want more control" once), so a cut built on it can keep both attempts. A piece a few
seconds long, transcribed alone, is written as said. For each script line (its first piece and its "same line" pieces)
the words are read again; where the same three words come round again within fifteen words, everything from the first
to the second is a false start and is cut out, at the word edges. The cut is rebuilt the same way (assemble.py, the
cut list's own push), and the old one kept as cut_before_verify.mp4.
"""
import argparse, json, os, re, shutil, subprocess, sys
import numpy as np, imageio_ffmpeg, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from assemble import assemble
ROW = re.compile(r"^\| ([\d.]+) \| ([\d.]+)-([\d.]+) \| x([\d.]+) \| (.*?) \| (.*?) \| (.*?) \|$")
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
CUTOFF = set("the a an to of and or is are was we you i it this that in on for with our your my be can will".split())

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cut_dir"); ap.add_argument("raw"); ap.add_argument("--mirror", action="store_true")
    ap.add_argument("--bars", type=int, default=0); ap.add_argument("--size", default="1920x1080"); ap.add_argument("--model", default="small.en")
    a = ap.parse_args()
    from faster_whisper import WhisperModel
    m = WhisperModel(a.model, device="cpu", compute_type="int8")
    FF = imageio_ffmpeg.get_ffmpeg_exe(); cl = os.path.join(a.cut_dir, "cutlist.md"); L = open(cl, encoding="utf-8").read().splitlines()
    rows = [ROW.match(l).groups() for l in L if ROW.match(l)]
    audio = np.frombuffer(subprocess.run([FF, "-v", "error", "-i", a.raw, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],   # decoded once
                                         capture_output=True).stdout, np.int16).astype(np.float32) / 32768
    cache_p = os.path.join(a.cut_dir, "heard_cache.json"); cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    def heard(x0, x1):                                                         # a piece transcribed alone, remembered by its span
        key = f"{x0:.2f}-{x1:.2f}"
        if key not in cache:
            segs, _ = m.transcribe(audio[int(x0 * 16000):int(x1 * 16000)], language="en", beam_size=5, word_timestamps=True, condition_on_previous_text=False)
            cache[key] = [dict(w=w.word.strip(), s=x0 + w.start, e=x0 + w.end) for s in segs for w in (s.words or []) if w.word.strip()]
            json.dump(cache, open(cache_p, "w"))
        return cache[key]
    groups, cur = [], None                                                     # one script line: its pieces
    for r in rows:
        if r[4].startswith("(same line") and cur: cur.append(r)
        else: cur = [r]; groups.append(cur)
    out, fixed = [], 0
    for g in groups:
        words = []
        for k, r in enumerate(g):
            for w in heard(float(r[1]), float(r[2])): words.append(dict(w, k=k))
        n = [norm(w["w"]) for w in words]; drop = set(); changed = True
        def phrase_start(i):                                                   # where a speaker restarts: the first word, or after a pause or a mark
            return i == 0 or words[i]["s"] - words[i - 1]["e"] > 0.2 or re.search(r"[.,?!…]$", words[i - 1]["w"]) or words[i]["k"] != words[i - 1]["k"]
        same = lambda u, v: u == v or (len(u) > 1 and len(v) > 1 and (u.startswith(v) or v.startswith(u)))   # "we" / "we're"
        while changed:                                                         # the same opening again after a pause: the first try was a false start
            changed = False; keep = [i for i in range(len(words)) if i not in drop]
            for x in range(len(keep) - 1):
                if not phrase_start(keep[x]) or not n[keep[x]]: continue
                for y in range(x + 1, min(len(keep) - 1, x + 15)):
                    three = y + 2 < len(keep) and x + 2 < y and same(n[keep[x + 2]], n[keep[y + 2]])
                    tried = [words[i]["w"] for i in keep[x:y]]                     # a false start is cut off, or very short; "you can run
                    cut_off = len(tried) <= 3 or re.search(r"(\.\.\.|…|-)$", tried[-1]) or norm(tried[-1]) in CUTOFF   # it locally, you can deploy" is a list
                    if phrase_start(keep[y]) and same(n[keep[x]], n[keep[y]]) and same(n[keep[x + 1]], n[keep[y + 1]]) and (three or cut_off):
                        drop |= set(keep[x:y]); changed = True; break
                if changed: break
        if len(words) > 1 and re.search(r"\.$", words[0]["w"]) and words[1]["w"][:1].isupper() and 0 not in drop:
            drop.add(0)                                                         # "this. You can also visit": the last word of the line before
        if not drop:
            out += [(float(r[1]), float(r[2]), float(r[3]), r[4], r[5], r[6]) for r in g]; continue
        fixed += 1; kept = [w for i, w in enumerate(words) if i not in drop]
        print(f"  restart cut: {' '.join(words[i]['w'] for i in sorted(drop))[:80]!r}  ->  keeps {' '.join(w['w'] for w in kept)[:80]!r}")
        first = True
        for k, r in enumerate(g):                                              # each piece shrinks to its kept words
            ws = [w for w in kept if w["k"] == k]
            if not ws: continue
            runs, run = [], [ws[0]]
            for w in ws[1:]:
                if words.index(w) != words.index(run[-1]) + 1: runs.append(run); run = []
                run.append(w)
            runs.append(run)
            for run in runs:
                x0 = max(float(r[1]), run[0]["s"] - 0.08); x1 = min(float(r[2]), run[-1]["e"] + 0.15)
                out.append((x0, x1, float(r[3]), r[4] if first else "(same line, after a pause)", " ".join(w["w"] for w in run) if first else "",
                            (r[6] + "; restart taken out") if first else "restart taken out")); first = False
    json.dump(cache, open(cache_p, "w"))
    W_, H_ = (int(v) for v in a.size.split("x")); c = cv2.VideoCapture(a.raw); sw, sh = int(c.get(3)), int(c.get(4)); c.release()
    def vf(k):
        push = out[k][2]; cw, ch = int(sw / push), int(sh / push); cx, cy = (sw - cw) // 2, (sh - ch) // 2
        return ("hflip," if a.mirror else "") + f"crop={cw}:{ch}:{cx}:{cy},scale={W_}:{H_}:flags=lanczos" + \
               (f",drawbox=x=0:y=0:w={W_}:h={a.bars}:color=black:t=fill,drawbox=x=0:y={H_ - a.bars}:w={W_}:h={a.bars}:color=black:t=fill" if a.bars else "")
    video = os.path.join(a.cut_dir, "cut.mp4"); shutil.copy(video, os.path.join(a.cut_dir, "cut_before_verify.mp4")); shutil.copy(cl, os.path.join(a.cut_dir, "cutlist_before_verify.md"))
    tmp = os.path.join(a.cut_dir, "cut_verify.mp4"); times = assemble(a.raw, [(p[0], p[1]) for p in out], tmp, vf_for=vf); os.replace(tmp, video)
    first_row = next(i for i, l in enumerate(L) if ROW.match(l)); last_row = max(i for i, l in enumerate(L) if ROW.match(l))
    missing = [l for l in L[first_row:last_row + 1] if l.startswith("|  |")]
    body = [f"| {t:.2f} | {p[0]:.2f}-{p[1]:.2f} | x{p[2]:.2f} | {p[3]} | {p[4]} | {p[5]} |" for t, p in zip(times, out)]
    total = times[-1] + out[-1][1] - out[-1][0]
    tail = [re.sub(r"Total [\d.]+ s, \d+ cuts", f"Total {total:.1f} s, {len(out)} cuts", l) for l in L[last_row + 1:]]
    open(cl, "w", encoding="utf-8").write("\n".join(L[:first_row] + body + missing + tail) + "\n")
    print(f"{fixed} line(s) had a restart taken out; {len(out)} pieces, {total:.1f} s -> {video}")

if __name__ == "__main__":
    main()
