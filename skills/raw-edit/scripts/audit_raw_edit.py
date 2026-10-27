#!/usr/bin/env python
"""audit_raw_edit.py: how the 50 audited videos are cut at the level of the raw edit, to test the raw edit rules against.

  python audit_raw_edit.py CORPUS_DIR [--workers 3] [--only ID,ID]   -> CORPUS_DIR/raw_edit_audit/{ID}.json, summary.csv

The transitions and camera audits (2026-10-14) measured shot changes and layouts. The raw edit rules
(references/rules.md) are about what happens inside the talking: pauses, jump cuts, restarts, the eyes. This measures
those on the same 50 videos (360p is enough for all of it), over the first 5 minutes of each:

  speech   every word, transcribed the way the raw edit check reads a take (transcribe_literal.py's settings, small.en, greedy)
  pauses   every silence between words, from the sound (join_checks.envelope), split by the word before it: inside a
           sentence, at a comma, at a full stop
  cuts     every hard cut (frame difference far above the video's own), and which are jump cuts: a face before and after,
           in about the same place (MediaPipe face detection); at each, the silence heard across it, whether the word
           before ends a sentence, and the face's size change (a punch-in or the 'push' between takes)
  eyes     the iris position at 3 frames a second (gaze.py) on frames where the face is large, against the speaker's own
           resting place and spread, as raw_edit_checks.py measures a glance
  checks   raw_edit_checks.py run on the video as if it were our raw edit (pieces = the stretches between jump cuts): how
           often a finished, professional edit trips our restart, stop and glance rules
"""
import argparse, glob, json, os, re, subprocess, sys
import numpy as np
SPAN = 300.0                                   # the first 5 minutes of each video: a creator's cutting habits hold for the whole video
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
SK = os.path.dirname(os.path.dirname(HERE)); sys.path += [os.path.join(SK, "editing", "scripts"), os.path.join(SK, "video-review", "scripts")]   # shared: assemble, respan, gaze; join_checks

def words_of(mp4, out):
    if os.path.exists(out): return json.load(open(out, encoding="utf-8"))
    try: import av                                    # faster-whisper imports av only to read files; where a policy blocks
    except ImportError: sys.modules["av"] = type(sys)("av")   # av's DLL, the audio goes in as an array
    from faster_whisper import WhisperModel
    import imageio_ffmpeg
    audio = np.frombuffer(subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", mp4, "-t", str(SPAN), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                                         capture_output=True).stdout, np.int16).astype(np.float32) / 32768
    m = WhisperModel("small.en", device="cpu", compute_type="int8", cpu_threads=4)         # greedy: a restart needs the words,
    segs, _ = m.transcribe(audio, language="en", beam_size=1, word_timestamps=True,           # not the best spelling of them
                           condition_on_previous_text=False, vad_filter=True, vad_parameters=dict(min_silence_duration_ms=300, speech_pad_ms=120))
    W = [dict(w=w.word.strip(), s=round(w.start, 2), e=round(w.end, 2)) for s in segs for w in (s.words or []) if w.word.strip()]
    json.dump(W, open(out, "w", encoding="utf-8")); return W

def cuts_of(mp4):
    """hard cuts, with the face (box) on each side: [(t, face_before, face_after)]"""
    import cv2
    c = cv2.VideoCapture(mp4); fps = c.get(cv2.CAP_PROP_FPS) or 30; small, keep = [], {}
    while len(small) < SPAN * fps:
        ok, f = c.read()
        if not ok: break
        small.append(cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (64, 36), interpolation=cv2.INTER_AREA).astype(np.int16))
    d = np.r_[0, [np.abs(small[i] - small[i - 1]).mean() for i in range(1, len(small))]]
    # a jump cut between two takes of the same framing barely changes the picture (2.75 on our approved cut, where a scene
    # change is 12+), so a cut is a frame 5x its own neighbourhood: 68 of 73 known joins found, 7 false in 200 s (gestures)
    spikes = []
    for i in range(2, len(d) - 2):
        m = np.median(np.r_[d[max(0, i - 15):i - 1], d[i + 2:i + 16]])
        if d[i] > 0.8 and d[i] > 5 * max(m, 0.15) and d[i] >= d[i - 1] and d[i] >= d[i + 1] and (not spikes or i - spikes[-1] > 5): spikes.append(i)
    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    def face(i):
        c.set(cv2.CAP_PROP_POS_FRAMES, max(0, i)); ok, f = c.read()
        if not ok: return None
        H, W = f.shape[:2]; r = det.detectMultiScale(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), 1.1, 6, minSize=(int(W * 0.05), int(W * 0.05)))
        if not len(r): return None
        x, y, w, h = max(r, key=lambda b: b[2])
        return ((x + w / 2) / W, (y + h / 2) / H, w / W)
    out = [(i / fps, face(i - 2), face(i + 2)) for i in spikes]
    c.release(); return out, len(small) / fps

def gaze_of(mp4, out):
    if not os.path.exists(out):
        subprocess.run([sys.executable, os.path.join(SK, "editing", "scripts", "gaze.py"), mp4, "--out", out, "--fps", "3", "--end", str(SPAN)], capture_output=True)
    return json.load(open(out)) if os.path.exists(out) else None

def one(mp4, odir):
    import join_checks as JC, raw_edit_checks as RE
    vid = os.path.basename(mp4)[:-4]; res_p = os.path.join(odir, vid + ".json")
    if os.path.exists(res_p): return json.load(open(res_p))
    W = words_of(mp4, os.path.join(odir, vid + "_words.json")); env, quiet, loud = JC.envelope(mp4)
    starts = [w["s"] for w in W]; P = dict(inside=[], comma=[], stop=[])
    env = env[:int(SPAN * 100)]
    for a, b in RE.quiet_runs(env > quiet):
        k = int(np.searchsorted(starts, a)) - 1
        if not (0.1 <= b - a < 3) or k < 0 or k + 1 >= len(W) or W[k + 1]["s"] < b - 0.3: continue      # between two words, not music
        w = W[k]["w"]; P["stop" if re.search(r"[.?!]$", w) else "comma" if w.endswith(",") else "inside"].append(round(b - a, 2))
    cuts, dur = cuts_of(mp4)
    jumps = []
    for t, f0, f1 in cuts:
        if not (f0 and f1) or abs(f0[0] - f1[0]) > 0.15 or abs(f0[1] - f1[1]) > 0.15 or min(f0[2], f1[2]) < 0.06: continue
        i = int(round(t * 100)); lo, hi = i, i
        while lo > 0 and env[lo - 1] <= quiet and i - lo < 300: lo -= 1
        while hi < len(env) - 1 and env[hi] <= quiet and hi - i < 300: hi += 1
        before = [w for w in W if w["e"] <= t + 0.05]
        jumps.append(dict(t=round(t, 2), heard=round((hi - lo) / 100, 2), scale=round(f1[2] / f0[2], 3),
                          sentence_end=bool(before and re.search(r"[.?!]$", before[-1]["w"]))))
    G = gaze_of(mp4, os.path.join(odir, vid + "_gaze.json")); eyes = None
    if G and G.get("frames"):
        fr = [f for f in G["frames"] if f.get("face") and f.get("open", 1) > 0.15]
        if len(fr) > 200:
            S = RE.speaker(W, env, quiet, dict(frames=fr)); Z = np.sqrt(sum(((np.array([f[k] for f in fr]) - S[k][0]) / S[k][1]) ** 2 for k in ("h", "v")))
            T = np.array([f["t"] for f in fr]); speaking = np.array([any(w["s"] <= t <= w["e"] for w in W[max(0, int(np.searchsorted(starts, t)) - 3):int(np.searchsorted(starts, t)) + 1]) for t in T])
            runs, cur = [], []
            for q in range(len(T)):
                if Z[q] > 3 and (not cur or T[q] - T[cur[-1]] < 0.4): cur.append(q); continue
                if cur and T[cur[-1]] - T[cur[0]] + 0.33 >= 0.3: runs.append(round(float(T[cur[-1]] - T[cur[0]] + 0.33), 2))
                cur = [q] if Z[q] > 3 else []
            eyes = dict(face_s=round(len(fr) / 3, 1), off_share=round(float((Z > 3).mean()), 3), off_share_speaking=round(float((Z[speaking] > 3).mean()), 3) if speaking.any() else None,
                        glances=len(runs), glances_per_face_min=round(len(runs) / max(1e-6, len(fr) / 3 / 60), 2), glance_s=runs)
    # our checks on the finished video, as if it were our raw edit: pieces are the stretches between jump cuts
    edges = [0.0] + [j["t"] for j in jumps] + [dur]
    cl = os.path.join(odir, vid + "_cutlist.md")
    open(cl, "w", encoding="utf-8").write("| edit time | source | push | script line | said | take |\n|---|---|---|---|---|---|\n" +
                                          "".join(f"| {a:.2f} | {a:.2f}-{b:.2f} | x1.00 | {'(none)' if k == 0 else '(same line, after a pause)'} |  |  |\n" for k, (a, b) in enumerate(zip(edges, edges[1:])) if b - a > 0.05))
    F, S = RE.checks((env, quiet, loud), cl, W, G if eyes else None)
    found = {k: sum(1 for f in F if f["kind"] == k and f["sev"] == "fix") for k in ("restart", "stop", "glance")}
    found.update({k + "_check": sum(1 for f in F if f["kind"] == k and f["sev"] == "check") for k in ("stop", "glance")})
    res = dict(id=vid, dur=round(dur, 1), words=len(W), wpm=round(len(W) / dur * 60, 1), speaker_pause=round(S["pause"], 2), stop_limit=round(S["stop"], 2),
               pauses={k: dict(n=len(v), p50=float(np.median(v)) if v else None, p90=float(np.percentile(v, 90)) if v else None, over_limit=round(sum(x > S["stop"] for x in v) / max(1, len(v)), 3)) for k, v in P.items()},
               cuts=len(cuts), jumps=len(jumps), jumps_per_min=round(len(jumps) / dur * 60, 2), jump_heard=[j["heard"] for j in jumps],
               jump_sentence_end=round(sum(j["sentence_end"] for j in jumps) / max(1, len(jumps)), 3), jump_scale=[j["scale"] for j in jumps],
               eyes=eyes, checks=found, examples=[dict(t=round(f["t"], 1), kind=f["kind"], msg=f["msg"][:140]) for f in F if f["sev"] == "fix"][:12])
    json.dump(res, open(res_p, "w"), indent=1); return res

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corpus"); ap.add_argument("--workers", type=int, default=3); ap.add_argument("--only")
    a = ap.parse_args(); odir = os.path.join(a.corpus, "raw_edit_audit"); os.makedirs(odir, exist_ok=True)
    vids = sorted(glob.glob(os.path.join(a.corpus, "*.mp4")))
    if a.only: vids = [v for v in vids if os.path.basename(v)[:-4] in a.only.split(",")]
    from concurrent.futures import ProcessPoolExecutor, as_completed
    with ProcessPoolExecutor(a.workers) as ex:
        fut = {ex.submit(one, v, odir): v for v in vids}
        for f in as_completed(fut):
            try: r = f.result(); print(f"{r['id']}: {r['dur'] / 60:.1f} min, {r['jumps_per_min']} jump cuts/min, pause {r['speaker_pause']} s, checks {r['checks']}", flush=True)
            except Exception as e: print(f"{os.path.basename(fut[f])}: FAILED {e}", flush=True)

if __name__ == "__main__":
    main()
