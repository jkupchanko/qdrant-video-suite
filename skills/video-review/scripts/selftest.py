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
And the reading pace, on a made-up card track (OCR reads, no video) where the picture never stops moving:
  two cards of 30 words, 2 s each, back to back -> read (fix) on each; a card typed in over 10 s -> nothing.
  Cards split by motion merge all three into one long card and miss both (build 4, 0:43-0:53).
And the raw edit (raw_edit_checks), on a made-up take: a restart left in, a script list item dropped, a piece running into
  a thinking pause as the eyes leave, a stop inside a sentence -> each caught; a list that repeats its opening -> nothing.
Without CUT.mp4 only the joins, the reading pace and the raw edit run (they need no video).
Run it after changing any check. Exit 1 if a fault is missed or a fix is invented.
"""
import os, sys, json, argparse, subprocess, cv2, imageio_ffmpeg
HERE = os.path.dirname(os.path.abspath(__file__))
WANT = {"blank": (2.0, 2.5), "aspect": (3.0, 6.0), "sync": (6.0, 10.0), "edge": (7.0, 9.0)}
ALSO = {"abrupt": (1.9, 2.6)}          # the blank plant is also a hard cut in and out of a plain frame: true, not invented

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

def raw_edit_selftest(out):
    """a made-up take (words as voiced bursts), its literal words, the eyes, and a cut list with four faults planted:
      a sentence started, dropped and said again, both kept       -> restart
      a list item of the script said between two pieces, left out -> dropped
      a piece ending on "to" that runs into a thinking pause as the eyes leave -> glance
      a 1.6 s silence inside one sentence                          -> stop
    and two lists that repeat their opening on purpose ("you can run it locally, you can deploy it"; "it can diagnose, it can
    assemble") that must not be fixed as restarts"""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "raw-edit", "scripts"))   # the raw-edit skill
    import numpy as np, wave, raw_edit_checks as RE
    sr = 16000; W, bursts, t = [], [], 0.5
    def say(text, gap=0.12):
        nonlocal t
        for w in text.split():
            d = 0.08 * len(w.strip(",.")) + 0.1; W.append(dict(w=w, s=round(t, 2), e=round(t + d, 2))); bursts.append((t, t + d)); t += d + gap
        t -= gap
    def pause(s): 
        nonlocal t; t += s
    P = {}
    P["list"] = t; say("You can run it locally, you can deploy it, or use the cloud."); pause(0.4)
    say("It can diagnose, it can assemble, it can assess."); P["list_e"] = t; pause(1.5)       # a list said on purpose (49 pro videos)
    P["try1"] = t; say("Now this can be useful if you want more"); P["try1_e"] = t; pause(1.2)
    P["try2"] = t; say("Now this can be useful if you want more control."); P["try2_e"] = t; pause(1.5)
    P["web"] = t; say("The Web UI lets us explore the cluster, manage collections,"); P["web_e"] = t; pause(0.8)
    say("run requests,"); pause(0.8); P["web2"] = t; say("and follow tutorials."); P["web2_e"] = t; pause(1.5)
    P["tool"] = t; say("This tool allows you to"); P["tool_e"] = t; pause(2.0); P["tool2"] = t; say("explore the data."); P["tool2_e"] = t; pause(1.5)
    P["stop"] = t; say("Then we open the"); pause(1.6); say("settings page."); P["stop_e"] = t; pause(1.0)
    n = int((t + 1) * sr); tt = np.arange(n) / sr; x = np.random.default_rng(2).normal(0, 0.001, n)
    for a, b in bursts:
        m = (tt >= a) & (tt < b); x[m] += 0.3 * np.sin(2 * np.pi * 180 * tt[m])
    wp = os.path.join(out, "raw_take.wav")
    with wave.open(wp, "w") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    rng = np.random.default_rng(3); fr = []
    for k in range(int(t * 12.5)):
        ft = k / 12.5; away = P["tool_e"] + 0.05 < ft < P["tool2"] - 0.3
        fr.append(dict(t=ft, face=True, h=(0.37 if away else 0.43) + rng.normal(0, 0.015), v=0.47 + rng.normal(0, 0.015), off=False))
    h = 0.06
    spans = [(P["list"] - h, P["list_e"] + h, "You can run it locally, you can deploy it, or use the cloud. It can diagnose, it can assemble, it can assess."),
             (P["try1"] - h, P["try1_e"] + h, "Now this can be useful if you want more control."), (P["try2"] - h, P["try2_e"] + h, "(same line, after a pause)"),
             (P["web"] - h, P["web_e"] + h, "The Web UI lets us explore the cluster, manage collections, run requests, and follow interactive tutorials."),
             (P["web2"] - h, P["web2_e"] + h, "(same line, after a pause)"),
             (P["tool"] - h, P["tool_e"] + 0.35, "This tool allows you to explore the data."), (P["tool2"] - h, P["tool2_e"] + h, "(same line, after a pause)"),
             (P["stop"] - h, P["stop_e"] + h, "Then we open the settings page.")]
    e, rows = 0.0, []
    for a, b, line in spans: rows.append(f"| {e:.2f} | {a:.2f}-{b:.2f} | x1.00 | {line} | {line} | test |"); e += b - a
    cl = os.path.join(out, "raw_cutlist.md"); open(cl, "w", encoding="utf-8").write("| edit time | source | push | script line | said | take |\n|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
    F, S = RE.checks(wp, cl, W, dict(frames=fr)); ok = True
    edit = lambda src: next(float(r.split("|")[1]) + src - float(r.split("|")[2].split("-")[0]) for r in rows if float(r.split("|")[2].split("-")[0]) <= src + 0.1 <= float(r.split("|")[2].split("-")[1]) + 0.2)
    want = [("restart", edit(P["try1"]), "a sentence started, dropped and said again"), ("dropped", edit(P["web"]), '"run requests" left out of the list'),
            ("glance", edit(P["tool_e"]), 'a piece running past "to" into a thinking pause'), ("stop", edit(P["stop"]), "a 1.6 s stop inside a sentence")]
    for kind, t0, what in want:
        hit = [f for f in F if f["kind"] == kind and f["sev"] == "fix" and t0 - 0.5 <= f["t"] <= t0 + 3 and f.get("edit")]   # and it says how to fix it
        print(f"  {'caught' if hit else 'MISSED'}  {kind:7s} {what}" + (f"  -> {hit[0]['msg'][:50]} | fix {hit[0]['edit']}"[:150] if hit else "")); ok &= bool(hit)
    extra = [f for f in F if f["sev"] == "fix" and not any(f["kind"] == k and t0 - 0.5 <= f["t"] <= t0 + 3 for k, t0, _ in want)]
    for f in extra: print(f"  INVENTED  {f['kind']} at {f['t']:.2f} s: {f['msg'][:80]}")
    return ok and not extra

def reading_selftest(fps=30, H=1080):
    """a 16 s card track read once a second: the face, two short cards, then a card typed in line by line. The picture moves
    throughout (live typing), so only the words on screen tell the cards apart"""
    import numpy as np, string, pace_checks as PC, text_checks as TX
    small = np.full((16 * fps, 90, 160), 30, np.uint8); small[:2 * fps] = 150                  # face for the first 2 s, then graphics
    motion = np.full(len(small), 4.0)
    def words(c, n): return [c + a + b for a in string.ascii_lowercase for b in string.ascii_lowercase][:n]
    def lines(ws): return [dict(text=" ".join(ws[k:k + 6]), score=0.95, box=[200, 300 + 40 * k, 1500, 328 + 40 * k], h=28) for k in range(0, len(ws), 6)]
    res = {}
    for t in (2, 3): res[t * fps] = lines(words("q", 30))
    for t in (4, 5): res[t * fps] = lines(words("r", 30))
    for t in range(6, 16): res[t * fps] = lines(words("s", min(25, 13 + 2 * (t - 6))))          # typed in: 13 words, then 2 more a second
    rd = PC.reading(small, motion, fps, res, H, TX.is_code)
    ok = True
    for t0, what in [(2, "a 2 s card of 30 words"), (4, "the next 2 s card, straight after")]:
        hit = [r for r in rd if r[0] == "fix" and abs(r[1] - t0) < 0.6 and r[2] < t0 + 1.6]
        print(f"  {'caught' if hit else 'MISSED'}  read    {what}" + (f"  -> {hit[0][4][:80]}" if hit else "")); ok &= bool(hit)
    extra = [r for r in rd if r[2] >= 5.6]
    for r in extra: print(f"  INVENTED  read at {r[1]:.1f}-{r[2]:.1f} s: {r[4][:80]}")
    return ok and not extra

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cut", nargs="?"); ap.add_argument("--gaze"); ap.add_argument("--lookaways"); ap.add_argument("--out", default="review_selftest")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); joins_ok = joins_selftest(a.out) & reading_selftest() & raw_edit_selftest(a.out)
    if not a.cut:
        print("  (no CUT.mp4: the planted-clip checks did not run)"); print("SELF-TEST PASSED" if joins_ok else "SELF-TEST FAILED"); return 0 if joins_ok else 1
    clip = os.path.join(a.out, "planted.mp4"); plant(a.cut, clip)
    cmd = [sys.executable, os.path.join(HERE, "review.py"), clip, "--out", os.path.join(a.out, "report"), "--cut", a.cut, "--label", "self-test"]
    if a.gaze and a.lookaways: cmd += ["--gaze", a.gaze, "--lookaways", a.lookaways]
    subprocess.run(cmd, capture_output=True)
    found = json.load(open(os.path.join(a.out, "report", "report.json")))["findings"]; ok = True
    for kind, (t0, t1) in WANT.items():
        hit = [f for f in found if f["kind"] == kind and f["t"] < t1 and (f["t1"] or f["t"]) >= t0]
        print(f"  {'caught' if hit else 'MISSED'}  {kind:7s} planted {t0}-{t1} s" + (f"  -> {hit[0]['msg'][:80]}" if hit else "")); ok &= bool(hit)
    extra = [f for f in found if f["sev"] == "fix" and f["kind"] not in WANT and not (f["kind"] in ALSO and ALSO[f["kind"]][0] <= f["t"] <= ALSO[f["kind"]][1])]
    for f in extra: print(f"  INVENTED  {f['kind']} at {f['t']} s: {f['msg'][:80]}")
    ok &= joins_ok
    print("SELF-TEST PASSED" if ok and not extra else "SELF-TEST FAILED"); return 0 if ok and not extra else 1

if __name__ == "__main__":
    sys.exit(main())
