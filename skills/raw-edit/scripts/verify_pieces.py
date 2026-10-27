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
SK = os.path.dirname(os.path.dirname(HERE)); sys.path += [os.path.join(SK, "editing", "scripts"), os.path.join(SK, "video-review", "scripts")]   # shared: assemble, respan, gaze; join_checks
from assemble import assemble
ROW = re.compile(r"^\| ([\d.]+) \| ([\d.]+)-([\d.]+) \| x([\d.]+) \| (.*?) \| (.*?) \| (.*?) \|$")
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
FILLER = set("and then so now but um uh okay well".split())
CUTOFF = set("the a an to of and or is are was we you i it this that in on for with our your my be can will".split())

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cut_dir"); ap.add_argument("raw"); ap.add_argument("--mirror", action="store_true")
    ap.add_argument("--bars", type=int, default=0); ap.add_argument("--size", default="1920x1080"); ap.add_argument("--model", default="small.en"); ap.add_argument("--literal", help="the take transcribed phrase by phrase (transcribe_literal.py), for stutters a piece heard alone smooths over")
    a = ap.parse_args()
    try: import av                                    # faster-whisper imports av only to read files; where a policy blocks
    except ImportError: sys.modules["av"] = type(sys)("av")   # av's DLL, the audio goes in as an array
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
    fr = audio[:len(audio) // 160 * 160].reshape(-1, 160); env = 20 * np.log10(np.maximum(1e-6, np.sqrt((fr ** 2).mean(axis=1))))   # 10 ms loudness
    floor, speech = np.percentile(env, [10, 90]); quiet = floor + 0.45 * (speech - floor)
    def quiet_after(x, limit):                                                 # the first silence after a word, or the quietest moment
        i0, i1 = int(round(x * 100)), int(round(limit * 100))
        k = next((k for k in range(i0, max(i0, i1 - 1)) if env[k] < quiet and env[k + 1] < quiet), None)
        return min(limit, (k + 2) / 100) if k is not None else (i0 + int(np.argmin(env[i0:max(i0 + 1, i1)]))) / 100
    def quiet_before(x, limit):
        i0, i1 = int(round(x * 100)), int(round(limit * 100))
        k = next((k for k in range(i0, i1, -1) if env[k] < quiet and env[k - 1] < quiet), None)
        return max(limit, (k - 1) / 100) if k is not None else (i1 + int(np.argmin(env[i1:max(i1 + 1, i0)]))) / 100
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
            for x0_ in range(len(keep) - 1):
                if not phrase_start(keep[x0_]) or not n[keep[x0_]]: continue
                xs = [x0_]                                                     # the opening as said, and without a leading "and then"
                while xs[-1] + 2 < len(keep) and n[keep[xs[-1]]] in FILLER: xs.append(xs[-1] + 1)   # ("And then on the left..." / "On the left...");
                for y in range(x0_ + 1, min(len(keep) - 1, x0_ + 15)):           # "Now" and "But" also stay comparable as they are
                    if not phrase_start(keep[y]): continue
                    tried = [words[i]["w"] for i in keep[x0_:y]]                     # a false start is cut off, or very short; "you can run
                    cut_off = len(tried) <= 3 or re.search(r"(\.\.\.|…|-)$", tried[-1]) or norm(tried[-1]) in CUTOFF   # it locally, you can deploy" is a list
                    for x in xs:
                        if x >= y: break
                        three = y + 2 < len(keep) and x + 2 < y and same(n[keep[x + 2]], n[keep[y + 2]])
                        if same(n[keep[x]], n[keep[y]]) and same(n[keep[x + 1]], n[keep[y + 1]]) and (three or cut_off):
                            drop |= set(keep[x0_:y]); changed = True; break
                    if changed: break
                if changed: break
        if len(words) > 1 and re.search(r"\.$", words[0]["w"]) and words[1]["w"][:1].isupper() and 0 not in drop:
            drop.add(0)                                                         # "this. You can also visit": the last word of the line before
        tiny = {k for k, r in enumerate(g) if float(r[2]) - float(r[1]) < 0.7 and len(g) > 1}   # a scrap between two halves of a line:
        for k in tiny: drop |= {i for i, w in enumerate(words) if w["k"] == k}                 # a glance and a stray word ("you", heard as
        if tiny: print(f"  scrap cut: {[g[k][1] + '-' + g[k][2] for k in tiny]}")              # "Thanks for watching!")
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
            pw = [w for w in words if w["k"] == k]
            for run in runs:                                                   # a piece keeps its own edges unless a false start was cut
                x0 = float(r[1]) if run[0] is pw[0] else quiet_before(run[0]["s"], float(r[1]))   # right there; a new edge goes to the
                x1 = float(r[2]) if run[-1] is pw[-1] else quiet_after(run[-1]["e"], float(r[2]))  # silence (word times end early)
                out.append((x0, x1, float(r[3]), r[4] if first else "(same line, after a pause)", " ".join(w["w"] for w in run) if first else "",
                            (r[6] + "; restart taken out") if first else "restart taken out")); first = False
    json.dump(cache, open(cache_p, "w"))
    # a stutter a piece heard alone smooths over ("you can only, you can only display" at 2:20 of Get Started was heard once):
    # the take transcribed phrase by phrase (--literal) is read inside each piece, and only an immediate repeat, two or more
    # words said again right after a pause, is taken out. Nothing wider: its word times are a little off for anything more
    if a.literal and os.path.exists(a.literal):
        LIT = json.load(open(a.literal, encoding="utf-8")); out2 = []
        for p in out:
            ws = [w for w in LIT if p[0] - 0.02 <= w["s"] < p[1]]; nw = [norm(w["w"]) for w in ws]; cut = None
            for i in range(len(ws) - 3):
                start_i = i == 0 or ws[i]["s"] - ws[i - 1]["e"] > 0.2 or re.search(r"[,.…]$", ws[i - 1]["w"])
                if not start_i or not nw[i]: continue
                for j in range(i + 2, min(len(ws) - 1, i + 7)):
                    short = j - i <= 3 or nw[j - 1] in CUTOFF or (j + 2 < len(ws) and same(nw[i + 2], nw[j + 2]))   # not a list: "you can run
                    if short and (ws[j]["s"] - ws[j - 1]["e"] > 0.2 or re.search(r"[,.…]$", ws[j - 1]["w"])) and same(nw[i], nw[j]) and same(nw[i + 1], nw[j + 1]):   # it locally, you can deploy"
                        cut = (i, j); break
                if cut: break
            if not cut: out2.append(p); continue
            i, j = cut; print(f"  stutter cut: {' '.join(w['w'] for w in ws[i:j])!r} before {' '.join(w['w'] for w in ws[j:j + 4])!r}")
            if i > 0: out2.append((p[0], quiet_after(ws[i - 1]["e"], ws[i]["s"]), *p[2:]))
            out2.append((quiet_before(ws[j]["s"], ws[j - 1]["e"]), p[1], *(p[2:] if i == 0 else (p[2], "(same line, after a pause)", "", "stutter taken out"))))
        out = out2
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
