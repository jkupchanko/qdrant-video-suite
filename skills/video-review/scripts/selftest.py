"""selftest.py: prove the review still catches what it is meant to, on faults planted in a clip of a real cut.

  python selftest.py CUT.mp4 [--gaze GAZE.json --lookaways LOOKAWAYS.json] [--out DIR]

Builds a 10 s clip from the cut's first 10 s with known faults, reviews it, and checks each is reported where it was planted:
  2.0-2.5 s   empty frames                        -> blank
  3-6 s       the face stretched 10% wider         -> aspect
  6-10 s      the picture 3 frames behind the voice -> sync
  7-9 s       a caption running off the left edge  -> edge
and that nothing else is reported as a fix. Then the joins, on a made-up take (words as voiced bursts) and its cut list:
  a piece that keeps the first 40 ms of the next word, and one that starts in the middle of a word -> join (fix),
  a piece cut cleanly in the pauses -> nothing.
Run it after changing any check. Exit 1 if a fault is missed or a fix is invented.
"""
import os, sys, json, argparse, subprocess, cv2, imageio_ffmpeg
HERE = os.path.dirname(os.path.abspath(__file__))
WANT = {"blank": (2.0, 2.5), "aspect": (3.0, 6.0), "sync": (6.0, 10.0), "edge": (7.0, 9.0)}

def plant(cut, out):
    c = cv2.VideoCapture(cut); fps = c.get(cv2.CAP_PROP_FPS) or 30; frames = []
    for _ in range(int(10 * fps) + 4):
        ok, f = c.read(); frames.append(f)
    raw = out.replace(".mp4", "_raw.mp4"); w = cv2.VideoWriter(raw, cv2.VideoWriter_fourcc(*"mp4v"), fps, (frames[0].shape[1], frames[0].shape[0])); H, W = frames[0].shape[:2]
    for i in range(int(10 * fps)):
        t = i / fps; f = frames[i].copy()
        if 3 <= t < 6: s = cv2.resize(f, (int(W * 1.1), H)); d = (s.shape[1] - W) // 2; f = s[:, d:d + W].copy()
        if t >= 6: f = frames[i - 3].copy()
        if 2.0 <= t < 2.5: f[:] = (24, 18, 17)
        if 7 <= t < 9: cv2.putText(f, "BULK UPLOADS EXPLAINED", (-140, H - 100), cv2.FONT_HERSHEY_DUPLEX, 2.2, (255, 255, 255), 5)
        w.write(f)
    w.release()
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-y", "-i", raw, "-t", "10", "-i", cut, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", out], check=True); os.remove(raw)

def joins_selftest(out):
    """a 7 s take of five 'words' (voiced bursts, 0.12 s pauses between the first two) and a cut list with two bad joins"""
    import numpy as np, wave, join_checks as JC
    sr = 16000; t = np.arange(7 * sr) / sr; x = np.random.default_rng(1).normal(0, 0.001, len(t))
    for a, b in [(1.0, 1.5), (1.62, 2.1), (3.0, 3.6), (4.2, 4.7), (5.0, 5.5)]:
        m = (t >= a) & (t < b); x[m] += 0.3 * np.sin(2 * np.pi * 180 * t[m]) + 0.1 * np.sin(2 * np.pi * 540 * t[m])
    wp = os.path.join(out, "joins_take.wav")
    with wave.open(wp, "w") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    rows = [(0.0, 0.9, 1.66, "keeps the next word's first 40 ms"), (0.76, 3.2, 3.8, "starts mid-word"), (1.36, 4.1, 4.85, "clean"), (2.11, 4.9, 5.6, "clean")]
    cl = os.path.join(out, "joins_cutlist.md")
    open(cl, "w", encoding="utf-8").write("| edit time | source | push | script line | said | take and eyes |\n|---|---|---|---|---|---|\n" +
                                          "".join(f"| {e:.2f} | {a:.2f}-{b:.2f} | x1.00 | {n} | {n} | test |\n" for e, a, b, n in rows))
    J = JC.joins(wp, cl); ok = True
    for e, edge, what in [(0.0, "out", "the next word's first sound kept"), (0.76, "in", "a piece starting mid-word")]:
        hit = [j for j in J if j["sev"] == "fix" and j["edge"] == edge and e - 0.05 <= j["t"] <= e + 0.8]
        print(f"  {'caught' if hit else 'MISSED'}  join    {what}" + (f"  -> {hit[0]['msg'][:80]}" if hit else "")); ok &= bool(hit)
    extra = [j for j in J if j["t"] >= 1.3]
    for j in extra: print(f"  INVENTED  join at {j['t']:.2f} s: {j['msg'][:80]}")
    return ok and not extra

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cut"); ap.add_argument("--gaze"); ap.add_argument("--lookaways"); ap.add_argument("--out", default="review_selftest")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); joins_ok = joins_selftest(a.out); clip = os.path.join(a.out, "planted.mp4"); plant(a.cut, clip)
    cmd = [sys.executable, os.path.join(HERE, "review.py"), clip, "--out", os.path.join(a.out, "report"), "--cut", a.cut, "--label", "self-test"]
    if a.gaze and a.lookaways: cmd += ["--gaze", a.gaze, "--lookaways", a.lookaways]
    subprocess.run(cmd, capture_output=True)
    found = json.load(open(os.path.join(a.out, "report", "report.json")))["findings"]; ok = True
    for kind, (t0, t1) in WANT.items():
        hit = [f for f in found if f["kind"] == kind and f["t"] < t1 and (f["t1"] or f["t"]) >= t0]
        print(f"  {'caught' if hit else 'MISSED'}  {kind:7s} planted {t0}-{t1} s" + (f"  -> {hit[0]['msg'][:80]}" if hit else "")); ok &= bool(hit)
    extra = [f for f in found if f["sev"] == "fix" and f["kind"] not in WANT]
    for f in extra: print(f"  INVENTED  {f['kind']} at {f['t']} s: {f['msg'][:80]}")
    ok &= joins_ok
    print("SELF-TEST PASSED" if ok and not extra else "SELF-TEST FAILED"); return 0 if ok and not extra else 1

if __name__ == "__main__":
    sys.exit(main())
