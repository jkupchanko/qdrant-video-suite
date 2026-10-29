#!/usr/bin/env python
"""cut_takes.py: turn a raw talking-head recording and its script into a clean cut.

  python cut_takes.py RAW.mp4 SCRIPT.md --out DIR [--max-seconds 30] [--mirror] [--bars 72] [--push 1.04] [--push-blocks 3]
                      [--handle-in 0.08 --handle-out 0.3] [--model small.en]

What it does, in order:
  1. transcribes the recording with word timestamps
  2. finds every take of every script line (retakes, stumbles, ad-libs), and keeps the last complete one
  3. checks eye contact on every chosen take, frame by frame, and reports any look-away
  4. cuts each take on word boundaries with short handles; drops ad-libs between lines
  5. mirrors the picture (--mirror), covers a recording tag with matching bars top and bottom (--bars N px),
     zooms in slightly (--push) for a stretch and back out, only a couple of times (--push-blocks), fades the audio 20 ms at every join
  6. writes cut.mp4, cutlist.md (which take each line came from), gaze_sheet.png (the eyes on every take)
Stops at --max-seconds on a sentence boundary when given. Spoken wording wins over the script: the cut keeps
what was said; the cut list shows where it differs.
"""
if __name__ == "__main__":                                   # run on the suite's own Python (.venv, made by setup.py), whichever python started it
    import os as _o, sys as _s, subprocess as _sp
    _v = _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), "..", "..", "..", ".venv", *(("Scripts", "python.exe") if _o.name == "nt" else ("bin", "python")))
    if _o.path.exists(_v) and _o.path.normcase(_o.path.realpath(_s.prefix)) != _o.path.normcase(_o.path.realpath(_o.path.dirname(_o.path.dirname(_v)))):
        _s.exit(_sp.call([_v, _o.path.realpath(__file__)] + _s.argv[1:]))
import argparse, json, os, re, subprocess, sys
import numpy as np

def norm(s): return re.sub(r"[^a-z0-9 ]+", " ", s.lower().replace("’", "").replace("'", "")).split()

NOT_SPOKEN = ("count", "notes", "sources", "references", "checks")
def script_lines(path):
    """the lines meant to be said: not headings, [directions], tables, <!-- notes --> (however many lines they run), and
    nothing under a ## Count / Notes / Sources section (the three-layer script ends with a Count of its own layers)"""
    text = re.sub(r"<!--.*?-->", "", open(path, encoding="utf-8").read(), flags=re.S); out = []; skip = False
    for l in text.splitlines():
        l = l.strip()
        if l.startswith("## "): skip = l[3:].strip().lower().startswith(NOT_SPOKEN); continue
        if skip or l.startswith("|"): continue
        if not l or l.startswith(("#", "[", "**", "🎥", "🎙", "💻", "✅", "⚖", "```", "<")) or l.isupper() or len(l.split()) < 3: continue
        if re.match(r"^(🎥|🎙|💻|✅|⚖)", l): continue
        out.append(l)
    return out

def transcribe(path, model_name):
    try: import av                                    # faster-whisper imports av only to read files; where a policy blocks
    except ImportError: sys.modules["av"] = type(sys)("av")   # av's DLL, the audio goes in as an array
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
    if len(a) >= 4 and len(b) >= 4 and a[:4] == b[:4]: return True
    if len(a) >= 5 and len(b) >= 5:
        import difflib
        return difflib.SequenceMatcher(None, a, b).ratio() >= 0.8
    return False

def find_takes(words, line, min_cover=0.55):
    """windows of the transcript that cover the script line: (start_idx, end_idx, coverage, extra_words).
    Alignment is a small LCS so a changed word (every/all, isn't/does) does not stall the match."""
    target = norm(line); n = len(target)
    if n == 0: return []
    W = [(norm(w["w"]) or [""])[0] for w in words]
    takes = []
    for i in range(len(W)):
        if not (fuzzy_eq(W[i], target[0]) or (n >= 4 and fuzzy_eq(W[i], target[1]))): continue
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
            if cover >= min_cover and sc >= 0.3 and (best is None or sc > best[4]):
                best = (i, i + L - 1, round(cover, 2), extra, sc)
        if best: takes.append(best)
    takes.sort(key=lambda t: t[0]); out = []
    for t in takes:
        if out and t[0] <= out[-1][1]:
            if t[4] >= out[-1][4] - 0.02: out[-1] = t       # overlapping windows: the later, tighter start wins (a restart replaces its stumble)
        else: out.append(t)
    return out            # (start_idx, end_idx, cover, extra, score)

STOP = set("a an the and or but so to of for in on at is are was were be been being can could it its this that these those you your we "
            "our they their with as by from if then than when while which what into just also more most very not no do does did "
            "have has had will would should may might there here now well let lets gonna going".split())
def content_words(ws): return [w for w in ws if w and w not in STOP and len(w) > 2]

def find_in_gap(words, line, lo, hi):
    """a line said in other words: the presenter's wording wins, so a line the strict match missed is looked for only where
    it must be, between the takes of the lines either side of it. A run of the take counts when it says at least half of
    the line's content words; runs that start and end at a pause (whole spoken sentences) are preferred, and of several
    attempts the last one, as in the strict match. -> (start_idx, end_idx, recall, extra, score) or None"""
    target = norm(line); tc = sorted(set(content_words(target)))
    if len(tc) < 2 or hi - lo < 2: return None
    Wd = [(norm(w["w"]) or [""])[0] for w in words]; n = len(target); cands = []
    pause_before = lambda i: i == 0 or words[i]["s"] - words[i - 1]["e"] >= 0.25
    pause_after = lambda j: j + 1 >= len(words) or words[j + 1]["s"] - words[j]["e"] >= 0.25
    for i in range(lo, hi + 1):
        for j in range(i + max(2, n // 2) - 1, min(hi, i + 2 * n + 4) + 1):
            seg = Wd[i:j + 1]; hit = sum(1 for c in tc if any(fuzzy_eq(c, x) for x in seg))
            if hit < 2 or hit / len(tc) < 0.5: continue
            extra = len(seg) - hit; sc = hit / len(tc) - 0.02 * extra + 0.08 * pause_before(i) + 0.08 * pause_after(j)
            cands.append((i, j, round(hit / len(tc), 2), extra, sc))
    if not cands: return None
    top = max(c[4] for c in cands); near = [c for c in cands if c[4] >= top - 0.05]
    last = max(near, key=lambda c: c[0]); i, j, rec, extra, sc = max([c for c in near if c[0] >= last[0] - 2], key=lambda c: c[4])
    # the whole spoken sentence: trim to the first and last words the line has, then out to the transcript's own sentence ends
    # (its punctuation), never into the takes either side
    tw = set(target); hits = [q for q in range(i, j + 1) if any(fuzzy_eq(Wd[q], t) for t in tc)]      # the line's content words, not "now" ~ "on"
    i, j = hits[0], hits[-1]
    end = lambda q: words[q]["w"].rstrip().endswith((".", "?", "!")) or (q + 1 < len(words) and words[q + 1]["s"] - words[q]["e"] >= 0.35)   # a full stop, or a pause
    own = lambda q: Wd[q] in tw
    while i > lo and i > hits[0] - 8 and (not end(i - 1) or own(i - 1)): i -= 1                      # back to the start of what was said
    j0 = j
    ahead = lambda q: any(Wd[r] in tc for r in range(q + 1, min(hi, q + 8) + 1))                      # more of the line still to come (a few words on)
    while j < hi and j < hits[-1] + 14 and (not end(j) or ahead(j)): j += 1                           # on to the end of the sentence
    while j > j0 and Wd[j] in ("now", "so", "but", "and", "because", "then", "okay"): j -= 1          # not the next sentence's first word
    half = i + max(2, (j - i) // 2); restart = i                                                      # a restart ("this avoids this avoids"):
    for p in range(i, half):                                                                          # start at the last time the line began
        for q in range(p + 2, min(j, half + 2)):
            if Wd[p] == Wd[q] and Wd[p + 1] == Wd[q + 1]: restart = max(restart, q)
    return (restart, j, rec, extra, sc)

def silences(path, a0, b0, min_len=0.7, noise="-42dB"):
    """[(start, end)] of silences longer than min_len inside [a0, b0], in source seconds"""
    import imageio_ffmpeg, re as _re
    r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-ss", f"{a0:.3f}", "-to", f"{b0:.3f}", "-i", path, "-af", f"silencedetect=noise={noise}:d={min_len}", "-f", "null", "-"], capture_output=True, text=True).stderr
    starts = [float(x) for x in _re.findall(r"silence_start: ([\d.]+)", r)]; ends = [float(x) for x in _re.findall(r"silence_end: ([\d.]+)", r)]
    out = []
    for st in starts:
        en = next((e for e in ends if e > st), b0 - a0)
        out.append((a0 + st, a0 + en))
    return out

def split_on_silence(path, a0, b0, keep=0.25, min_len=0.7):
    """pieces of [a0, b0] with long silences removed, keeping a little air on each side"""
    cuts = [(st, en) for st, en in silences(path, a0, b0, min_len) if st - a0 > 0.4 and b0 - en > 0.4]
    if not cuts: return [(a0, b0)]
    pieces = []; cur = a0
    for st, en in cuts:
        pieces.append((cur, st + keep)); cur = en - keep
    pieces.append((cur, b0))
    return [(x, y) for x, y in pieces if y - x > 0.3]

_env, _zcr = {}, {}
def envelope(path):
    """the take's loudness, 10 ms a step (dB), decoded once, with its quiet and voice levels (from the take's own floor and speech);
    _zcr[path] is each step's zero-crossing rate (above about 0.25 a hiss: s, sh, ch, a breath; below 0.15 a voiced sound)"""
    if path not in _env:
        import imageio_ffmpeg
        raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
        x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768; n = len(x) // 160
        fr = x[:n * 160].reshape(n, 160); env = 20 * np.log10(np.maximum(1e-6, np.sqrt((fr ** 2).mean(axis=1))))
        _zcr[path] = (np.abs(np.diff(np.sign(fr), axis=1)) > 0).mean(axis=1)
        floor, speech = np.percentile(env, [10, 90])
        _env[path] = (env, floor + 0.45 * (speech - floor), floor + 0.7 * (speech - floor))
    return _env[path]

def pauses(path, a, b, n=3):
    """(start, end) of every pause in [a, b]: n or more 10 ms steps below the take's quiet level (a stop consonant inside a
    word is shorter or less quiet)"""
    env, quiet, _ = envelope(path); out, run = [], 0; i0, i1 = max(0, int(a * 100)), min(len(env), int(b * 100))
    for i in range(i0, i1):
        if env[i] < quiet: run += 1; continue
        if run >= n: out.append(((i - run) / 100, i / 100))
        run = 0
    if run >= n: out.append(((i1 - run) / 100, i1 / 100))
    return out

def voice_onset(path, a, b):
    """where the next word really starts in [a, b]: the end of a pause that the voice rises out of (a click or a breath
    after a pause is not a word). The transcript's word times can be a quarter of a second off, and a cut placed by
    them alone clips the next word's first sound"""
    env, _, loud = envelope(path)
    for p0, p1 in pauses(path, a, b + 0.15):
        if p1 <= b and env[int(p1 * 100):int(p1 * 100) + 12].max(initial=-120) > loud: return p1
    return None

def quietest(path, a, b):
    env = envelope(path)[0]; i0, i1 = max(0, int(a * 100)), min(len(env), int(b * 100))
    return (i0 + int(np.argmin(env[i0:i1]))) / 100 if i1 > i0 else a

def start_point(path, words, q0, handle):
    """the in-point: just before the first word's sound starts, with a little room tone (at most `handle`). Placed by the
    transcript alone it started mid-sound at 20 of the first Listed Sections build's 26 joins (the word before still sounding,
    or the first word's own first sound gone), so it is the end of the last pause up to 0.45 s before the first word;
    with no pause (one word running into the next), the quietest moment"""
    s0 = words[q0]["s"]; ps = pauses(path, s0 - 0.45, s0 + 0.05)
    if not ps: return quietest(path, s0 - 0.2, s0 + 0.02)
    p0, p1 = ps[-1]
    return max(0, p1 - min(handle, p1 - p0))

_ends = {}
def take_end(path):
    """the last moment of the take with a whole frame in it: a piece's end handle cannot reach past the file"""
    if path not in _ends:
        import cv2
        c = cv2.VideoCapture(path); fps = c.get(cv2.CAP_PROP_FPS) or 30; n = c.get(cv2.CAP_PROP_FRAME_COUNT); c.release()
        _ends[path] = max(0.0, (n - 2) / fps)
    return _ends[path]

def speech_end(path, x1, next_start=None, air=0.25, look=1.2, last_end=None):
    """the out-point: the first silence after the last word, plus some air, never more than `look` s later, and never into
    the next word. x1 is the last word's end plus a handle; when the pause was shorter than the handle, the out-point
    reached into the next word and kept its first sound ("...dense and sparse vectors. Wh-" at 0:21.9 of the first Listed
    Sections build). So the next word is found by its sound: after a pause just after the last word, the voice rising
    out of it; with no pause (one word running into the next), the quietest moment between the two. A hiss right after the
    last word (the s of "vectors", the ch of "search": the transcript often ends a word before its last consonant) is that
    word's tail and stays in; a voiced sound there is the next word"""
    sil = silences(path, max(0, x1 - 0.3), x1 + look, min_len=0.25)
    end = max((sil[0][0] + air) if sil else (x1 + look), x1)
    if last_end is None:
        if next_start is not None: end = min(end, next_start - 0.06)
        return max(x1, end)
    env, quiet, _ = envelope(path); near = pauses(path, last_end - 0.05, last_end + 0.3)
    i0, i1 = int(last_end * 100), int((near[0][0] if near else last_end + 0.3) * 100)
    heard = [_zcr[path][i] for i in range(i0, i1) if env[i] >= quiet]
    if heard and np.median(heard) < 0.2 and next_start is not None and next_start < last_end + 0.15:
        return quietest(path, last_end - 0.08, last_end + 0.1)
    on = voice_onset(path, near[0][0] if near else last_end, end + 0.05)
    return min(end, on - 0.02) if on is not None else end

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
    ap.add_argument("--push", type=float, default=1.04, help="the zoomed-in scale; 1.0 disables"); ap.add_argument("--push-blocks", type=int, default=3, help="the video in this many stretches, out / in / out (3 = one zoom-in held in the middle); 0 = alternate at every cut"); ap.add_argument("--handle-in", type=float, default=0.08); ap.add_argument("--handle-out", type=float, default=0.3)
    ap.add_argument("--model", default="small.en"); ap.add_argument("--size", default="1920x1080"); ap.add_argument("--max-gap", type=float, default=0.8, help="a silence longer than this inside a take is cut out")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    import imageio_ffmpeg; FF = imageio_ffmpeg.get_ffmpeg_exe()
    tp = os.path.join(a.out, "words.json")
    words = json.load(open(tp)) if os.path.exists(tp) else transcribe(a.raw, a.model)
    json.dump(words, open(tp, "w"))
    lines = script_lines(a.script); chosen = []; t_acc = 0.0; picks = []
    for line in lines:
        takes = find_takes(words, line)
        if not takes: picks.append([line, None, None]); continue
        # retakes sit close together in time; choose the best-scoring group (within 45 s of each other), then the LAST take in it
        groups = []
        for t in takes:
            if groups and words[t[0]]["s"] - words[groups[-1][-1][0]]["s"] <= 45: groups[-1].append(t)
            else: groups.append([t])
        g = max(groups, key=lambda gr: max(x[4] for x in gr))
        i, j, cover, extra, _ = g[-1]
        note = f"take {g.index(g[-1]) + 1} of {len(g)} at {words[i]['s']:.1f}s, cover {cover}" + (f", {extra} extra word(s)" if extra else "") + (f"; {len(takes) - len(g)} other match(es) elsewhere ignored" if len(takes) > len(g) else "")
        picks.append([line, (i, j), note])
    for k, (line, tk, note) in enumerate(picks):                                   # second pass: lines said in other words
        if tk: continue
        lo = next((picks[q][1][1] + 1 for q in range(k - 1, -1, -1) if picks[q][1]), 0)
        hi = next((picks[q][1][0] - 1 for q in range(k + 1, len(picks)) if picks[q][1]), len(words) - 1)
        g = find_in_gap(words, line, lo, hi)
        if g: picks[k][1] = (g[0], g[1]); picks[k][2] = f"said in other words at {words[g[0]]['s']:.1f}s ({g[2]:.0%} of its key words), found between its neighbours' takes"
        else: picks[k][2] = "NO TAKE FOUND: not said on the recording, or said too differently"
    for line, tk, note in picks:
        if not tk: chosen.append((line, None, note)); continue
        i, j = tk
        # split at silences inside the take (a presenter pausing mid-line): each piece is its own cut
        pieces = []; p0 = i
        for q in range(i, j):
            if words[q + 1]["s"] - words[q]["e"] > a.max_gap: pieces.append((p0, q)); p0 = q + 1
        pieces.append((p0, j))
        total = sum(words[q1]["e"] + a.handle_out - max(0, words[q0]["s"] - a.handle_in) for q0, q1 in pieces)
        if a.max_seconds and t_acc + total > a.max_seconds + 0.5:
            chosen.append((line, None, f"beyond --max-seconds ({a.max_seconds}); the cut stops here")); break
        first = True
        for k_, (q0, q1) in enumerate(pieces):
            a0 = start_point(a.raw, words, q0, a.handle_in); b0 = words[q1]["e"] + a.handle_out
            said = " ".join(w["w"] for w in words[q0:q1 + 1])
            nxt = words[q1 + 1]["s"] if q1 + 1 < len(words) else None
            b0 = min(speech_end(a.raw, b0, nxt, last_end=words[q1]["e"]), take_end(a.raw))   # a take that stops right after its last word
            subs = split_on_silence(a.raw, a0, b0, min_len=a.max_gap)
            for m_, (x0, x1) in enumerate(subs):
                lab = line if first else "(same line, after a pause)"
                nt = note if first else (f"pause of {words[q0]['s'] - words[q0 - 1]['e']:.1f} s removed" if (m_ == 0 and q0 > 0) else "silence inside the take removed")
                chosen.append((lab, (x0, x1, said if first else ""), nt)); t_acc += x1 - x0; first = False
    # a piece never runs past the in-point of the piece after it in the take, or the overlap is heard twice ("before you
    # upload. If | If you already know...": the transcript put "if" inside "upload", so both pieces kept it)
    ks = [k for k, c in enumerate(chosen) if c[1]]
    for k0, k1 in zip(ks, ks[1:]):
        (l0, (x0, x1, s0), n0), y0 = chosen[k0], chosen[k1][1][0]
        if x0 < y0 < x1: chosen[k0] = (l0, (x0, y0, s0), n0)
    spans = [c[1][:2] for c in chosen if c[1]]
    gaze, tiles = eye_check(a.raw, spans)
    W, H = (int(v) for v in a.size.split("x")); parts = []; rows = []; t_edit = 0.0; k = 0
    import cv2
    src = cv2.VideoCapture(a.raw); sw, sh = int(src.get(cv2.CAP_PROP_FRAME_WIDTH)), int(src.get(cv2.CAP_PROP_FRAME_HEIGHT)); src.release()
    # every piece is cut with exactly its frames and 1600 samples a frame and joined by assemble.py, so the voice
    # and the lips stay locked; the old per-piece AAC + concat copy drifted about 27 ms a join (1.4 s over 53)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from assemble import assemble
    gi = 0; spans, vfs, pend = [], [], []
    # the push: John, 2026-10-21, "a little too many small zoom-ins... one or two, keep it in and then keep it out". The
    # video is split into --push-blocks stretches at the cuts nearest the even marks; the zoom changes only there
    durs = [c[1][1] - c[1][0] for c in chosen if c[1]]; starts = np.cumsum([0.0] + durs[:-1]); total_d = sum(durs)
    flips = sorted({int(np.argmin(np.abs(starts - total_d * j / a.push_blocks))) for j in range(1, a.push_blocks)}) if a.push_blocks > 1 else []
    for line, span, note in chosen:
        if not span: pend.append((None, line, note)); continue
        a0, b0, said = span
        if a.push <= 1.0: push = 1.0
        elif a.push_blocks > 1: push = a.push if sum(1 for f in flips if f <= k) % 2 == 1 else 1.0
        else: push = 1.0 if k % 2 == 0 else a.push
        k += 1
        cw, ch = int(sw / push), int(sh / push); cx, cy = (sw - cw) // 2, (sh - ch) // 2
        vfs.append(("hflip," if a.mirror else "") + f"crop={cw}:{ch}:{cx}:{cy},scale={W}:{H}:flags=lanczos" +
                   (f",drawbox=x=0:y=0:w={W}:h={a.bars}:color=black:t=fill,drawbox=x=0:y={H - a.bars}:w={W}:h={a.bars}:color=black:t=fill" if a.bars else ""))
        spans.append((a0, b0)); pend.append(((a0, b0, said, push), line, note))
    out = os.path.join(a.out, "cut.mp4")
    times = assemble(a.raw, spans, out, vf_for=lambda q: vfs[q]) if spans else []
    q = 0
    for sp, line, note in pend:
        if sp is None: rows.append(("", "", "", line, "", note)); continue
        a0, b0, said, push = sp; g = gaze[gi]; gi += 1; parts.append(q)
        rows.append((f"{times[q]:.2f}", f"{a0:.2f}-{b0:.2f}", f"x{push:.2f}", line, said, note + f"; eyes on lens {int(g * 100)}%" + ("" if g >= 0.8 else "  <- CHECK"))); q += 1
    t_edit = (times[-1] + (spans[-1][1] - spans[-1][0])) if spans else 0.0
    if tiles:
        cols = 10; rows_img = [np.hstack(tiles[i:i + cols] + [np.zeros((160, 160, 3), np.uint8)] * (cols - len(tiles[i:i + cols]))) for i in range(0, len(tiles), cols)]
        cv2.imwrite(os.path.join(a.out, "gaze_sheet.png"), np.vstack(rows_img))
    with open(os.path.join(a.out, "cutlist.md"), "w", encoding="utf-8") as fh:
        fh.write(f"# Cut list: {os.path.basename(a.raw)}\n\n| edit time | source | push | script line | said | take and eyes |\n|---|---|---|---|---|---|\n")
        for r in rows: fh.write("| " + " | ".join(r) + " |\n")
        fh.write(f"\nTotal {t_edit:.1f} s, {len(parts)} cuts. " + ("Mirrored. " if a.mirror else "") + (f"Bars {a.bars} px top and bottom. " if a.bars else "") + ((f"Push x{a.push:.2f} held in stretch {', '.join(str(i + 2) for i in range(0, max(0, a.push_blocks - 1), 2))} of {a.push_blocks}, changing at {len(flips)} cuts. " if a.push_blocks > 1 else f"Push alternates 1.00 / {a.push:.2f}. ") if a.push > 1 else "") + "20 ms audio fades at every join.\n")
    print(f"-> {out}  {t_edit:.1f} s, {len(parts)} cuts; cutlist.md, gaze_sheet.png")
    for r in rows:
        if "CHECK" in r[5] or "NO TAKE" in r[5] or "beyond" in r[5]: print("   note:", r[3][:60], "|", r[5])

if __name__ == "__main__":
    main()
