#!/usr/bin/env python
"""chain_test.py: the whole suite, end to end, on the repo's 30-second demo. Run it after any change and before every push.

  python chain_test.py [--out DIR]      -> CHAIN TEST PASSED, or FAILED with the stage and what broke (exit 1)

Each skill has its own self-test, but nothing else runs the skills one after another, the way a person's build does. On
2026-10-26 two files Windows began blocking (av, scikit-learn's k-means) would have stopped every build, and nothing but
a build would have shown it. This builds demos/bulk-uploads-first30 (face_only_720.mp4 and its script) through every
stage, captions included, then checks what each stage made, not only that it finished:

  every stage   ok in build.json
  cut           every script line found (no NO TAKE FOUND)
  voice         cut/cut_voice.mp4 the cut's length to the millisecond (the voice stays on the lips)
  broll         the script's one marker recorded as a clip
  master        video_master.mp4 opens, within 1.5 s of the cut's length, about -14 LUFS (within 1.5)
  review        review/report.json written
  upload        a title and a description written, the description passing upload-kit's checks with nothing to fix
  captions      captions.srt written, "Qdrant" spelled right, and the caption check with nothing to fix

The numbers a run gives (lengths, loudness, the review's counts, the caption count) are kept in DIR/baseline.json from the
last passing run; a change is printed under "changed since the last pass", so a quiet regression is seen, not missed.
It takes several minutes and needs the network (the B-roll records the docs page) and Chrome.
"""
import argparse, glob, json, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
DEMO = os.path.join(REPO, "demos", "bulk-uploads-first30")

def length(p):
    import cv2
    c = cv2.VideoCapture(p); n, f = c.get(cv2.CAP_PROP_FRAME_COUNT), c.get(cv2.CAP_PROP_FPS) or 30; c.release(); return n / f if n else 0.0

def audio_length(p):
    import imageio_ffmpeg
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", p, "-ac", "1", "-ar", "48000", "-f", "s16le", "-"], capture_output=True).stdout
    return len(raw) / 2 / 48000

def lufs(p):
    import imageio_ffmpeg, numpy as np, pyloudnorm as pyln
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", p, "-ac", "2", "-ar", "48000", "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float64).reshape(-1, 2) / 32768
    return float(pyln.Meter(48000).integrated_loudness(x))

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(REPO, ".chaintest")); a = ap.parse_args()
    B = os.path.join(a.out, "build"); os.makedirs(a.out, exist_ok=True)
    import shutil; shutil.rmtree(B, ignore_errors=True)                                   # every run builds from nothing
    cmd = [sys.executable, os.path.join(HERE, "build.py"), "--take", "face_only_720.mp4", "--script", "script-with-camera-and-transitions.md",
           "--out", B, "--take-is-edited", "--captions", "file", "--label", "chain test"]
    print("building the 30 s demo through every stage (several minutes)...", flush=True); t0 = time.time()
    log = os.path.join(a.out, "build.log")
    with open(log, "w", encoding="utf-8") as f: r = subprocess.run(cmd, cwd=DEMO, stdout=f, stderr=subprocess.STDOUT)
    took = time.time() - t0
    S = json.load(open(os.path.join(B, "build.json"), encoding="utf-8")) if os.path.exists(os.path.join(B, "build.json")) else {}
    checks, got = [], {}
    def check(what, ok, detail=""): checks.append((what, bool(ok), detail))
    for st in ["cut", "voice", "words", "gaze", "camera", "keyterms", "broll", "assets", "style", "master", "review", "upload", "captions"]:
        s = S.get(st); check(f"stage {st}", s and s["ok"], (s or {}).get("note", "did not run")[:110] if not (s and s["ok"]) else f"{s['seconds']:.0f} s")
        if s: got[f"seconds {st}"] = s["seconds"]
    p = lambda *x: os.path.join(B, *x)
    if os.path.exists(p("cut", "cutlist.md")):
        cl = open(p("cut", "cutlist.md"), encoding="utf-8").read(); check("cut: every script line found", "NO TAKE FOUND" not in cl, "a line has no take")
    if os.path.exists(p("cut", "cut.mp4")) and os.path.exists(p("cut", "cut_voice.mp4")):
        d = abs(audio_length(p("cut", "cut.mp4")) - audio_length(p("cut", "cut_voice.mp4"))); check("voice: the cut's length kept", d < 0.001, f"{d * 1000:.1f} ms longer or shorter")
    clips = [c for c in glob.glob(p("broll", "*.mp4"))]; check("broll: the marker recorded", clips, "no clip in broll/")
    if os.path.exists(p("video_master.mp4")):
        L, cut_L = length(p("video_master.mp4")), length(p("cut", "cut.mp4")); got["master length s"] = round(L, 2)
        check("master: opens, the cut's length", L > 0 and abs(L - cut_L) < 1.5, f"{L:.2f} s against the cut's {cut_L:.2f} s")
        lo = lufs(p("video_master.mp4")); got["master LUFS"] = round(lo, 1); check("master: about -14 LUFS", abs(lo + 14) <= 1.5, f"{lo:.1f} LUFS")
    else: check("master: video_master.mp4 made", False, "missing")
    rj = p("review", "report.json"); check("review: report written", os.path.exists(rj), "no review/report.json")
    if os.path.exists(rj):
        R = json.load(open(rj, encoding="utf-8")).get("findings", [])
        for sev in ("fix", "check"): got[f"review {sev}"] = sum(1 for f in R if f.get("sev") == sev)
    if os.path.exists(p("upload", "description.txt")):
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "upload-kit", "scripts")); import upload_kit as UK
        T, D = open(p("upload", "title.txt"), encoding="utf-8").read().strip(), open(p("upload", "description.txt"), encoding="utf-8").read()
        U = UK.check(T, D); got["upload check"] = sum(1 for s_, _ in U if s_ == "check")
        check("upload: title and description, nothing to fix", T and not [m for s_, m in U if s_ == "fix"], "; ".join(m for s_, m in U if s_ == "fix")[:110])
    else: check("upload: description written", False, "no upload/description.txt")
    srt = p("captions", "captions.srt"); check("captions: file written", os.path.exists(srt), "no captions/captions.srt")
    if os.path.exists(srt):
        txt = open(srt, encoding="utf-8").read(); got["captions"] = txt.count("-->")
        check("captions: Qdrant spelled right", "Qdrant" in txt and "Quadrant" not in txt, "a misspelled Qdrant")
        cr = p("captions", "captions_report.json")
        if os.path.exists(cr):
            C = json.load(open(cr, encoding="utf-8")); got["caption check"] = C["check"]; check("captions: nothing to fix", C["fix"] == 0, f"{C['fix']} to fix (captions/captions_report.md)")
        else: check("captions: checked against the video", False, "no captions_report.json")
    ok = all(c[1] for c in checks)
    for what, good, detail in checks: print(f"  {'ok    ' if good else 'FAILED'}  {what}" + (f"  ({detail})" if detail and (not good or what.startswith('stage')) else ""))
    base_p = os.path.join(a.out, "baseline.json"); base = json.load(open(base_p)) if os.path.exists(base_p) else {}
    moved = [f"{k}: {base[k]} -> {v}" for k, v in got.items() if k in base and not k.startswith("seconds") and base[k] != v]
    if base: print("  changed since the last pass: " + ("; ".join(moved) if moved else "nothing"))
    if ok: json.dump(got, open(base_p, "w"), indent=1)
    print(f"  {took / 60:.1f} minutes; the build's own log: {log}")
    print("CHAIN TEST PASSED" if ok else "CHAIN TEST FAILED"); return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
