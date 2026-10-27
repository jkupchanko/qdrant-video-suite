#!/usr/bin/env python
"""selftest.py: prove the voice and caption tools still catch and fix what they are meant to, on faults planted in made-up files.

  python selftest.py [--out DIR]      -> SELF-TEST PASSED, or FAILED with what was missed (exit 1)

voice      a two-piece take, the second 7 dB quieter, with a 60 Hz hum and room noise -> the jump evened out (under 3 dB),
           the hum notched, the noise down 3 dB or more; the same take clean and even -> nothing done; the length the same
           to the sample and the voice within 1 ms of where it was (on the lips), both times
captions   a transcript saying "quadrant" and "started" for a script that says "Qdrant" and "start" -> "Qdrant" (a
           misspelling of the script's word), "started" kept (a real word that was said); "web ui" -> "Web UI";
           "Quadrant's" -> "Qdrant's" (the possessive kept); "quadrant .tech" -> "qdrant.tech" (one web address)
hearing    a spoken test line (a Windows system voice) captioned from the video's own sound, with no word list: every
           phrase there, "Quadrant" as "Qdrant"
checks     a subtitle file with "Quadrant", a 60-character line and two overlapping cues -> each a fix; a clean one -> none
"""
import argparse, json, os, shutil, subprocess, sys, wave
import numpy as np, imageio_ffmpeg
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
FF = imageio_ffmpeg.get_ffmpeg_exe(); SR = 48000

def take(path, quiet_second, hum, noise):
    t = np.arange(8 * SR) / SR; rng = np.random.default_rng(4); x = rng.normal(0, noise, len(t))
    for k in range(16):                                                 # syllables like speech: a pitch that glides, harmonics,
        a = 0.25 + k * 0.5; m = (t >= a) & (t < a + 0.25); amp = 0.25 * (10 ** (-7 / 20) if quiet_second and a >= 4 else 1)   # a rise and fall
        tt = t[m] - a; f0 = rng.uniform(110, 230) * (1 + 0.15 * np.sin(2 * np.pi * 3 * tt)); ph = 2 * np.pi * np.cumsum(f0) / SR
        x[m] += amp * np.sin(np.pi * tt / 0.25) * sum(np.sin(h * ph) / h for h in (1, 2, 3, 4)) * (1 + 0.3 * rng.normal(0, 1, m.sum()))
    if hum: x += 0.01 * np.sin(2 * np.pi * 60 * t)
    with wave.open(path + ".wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run([FF, "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=gray:s=320x180:r=25:d=8", "-i", path + ".wav", "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k", "-shortest", path + ".mp4"], check=True)
    open(path + "_cutlist.md", "w").write("| edit time | source | push | script line | said | take |\n|---|---|---|---|---|---|\n| 0.00 | 0.00-4.00 | x1.00 | a | a | t |\n| 4.00 | 4.00-8.00 | x1.00 | (same line, after a pause) | b | t |\n")

def voice_test(out):
    ok = True; py = sys.executable
    for name, quiet, hum, noise, expect in (("faulty", True, True, 0.004, True), ("clean", False, False, 0.0003, False)):
        p = os.path.join(out, name); take(p, quiet, hum, noise)
        subprocess.run([py, os.path.join(HERE, "voice_clean.py"), p + ".mp4", "--out", p + "_voice.mp4", "--cutlist", p + "_cutlist.md", "--report", p + ".json"], check=True, capture_output=True)
        R = json.load(open(p + ".json")); B, A = R["before"], R["after"]; did = " ".join(R["did"])
        if expect:
            checks = [("level jump evened", B["biggest_jump_db"] > 5 and A["biggest_jump_db"] < 3), ("hum notched", "hum:" in did), ("noise reduced", "noise:" in did and A["floor_db"] < B["floor_db"] - 3)]
        else:
            checks = [("clean take left alone", R["did"] == ["nothing: this take needs no fix"])]
        checks.append((f"{name}: same length", abs(R["length_s"]["after"] - R["length_s"]["before"]) < 0.001))
        dec = lambda f: np.frombuffer(subprocess.run([FF, "-v", "error", "-i", f, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout, np.int16).astype(np.float64)
        u, v = dec(p + ".mp4")[SR:SR * 7], dec(p + "_voice.mp4")[SR:SR * 7]; cc = np.fft.irfft(np.fft.rfft(u, 2 * len(u)) * np.conj(np.fft.rfft(v, 2 * len(u))))
        lag = abs(int(np.argmax(np.r_[cc[-2400:], cc[:2400]])) - 2400) / SR * 1000
        checks.append((f"{name}: voice on the lips ({lag:.1f} ms)", lag <= 1.0))
        for what, good in checks: print(f"  {'caught' if good else 'MISSED'}  voice    {what}"); ok &= good
    return ok

def caption_test(out):
    import captions as CP
    words = [dict(w=w, s=i * 0.4, e=i * 0.4 + 0.35) for i, w in enumerate("Before we get started building with quadrant, open the web ui.".split())]
    groups = [[[(w["w"], w["s"], w["e"]) for w in words], "Before you start building with Qdrant, open the Web UI."]]
    got = " ".join(w for w, _, _ in CP.respell(groups[0][0], groups[0][1], CP.glossary()))
    ws = [("Subscribe", 0, .3), ("to", .3, .4), ("Quadrant's", .4, .8), ("channel", .8, 1), ("at", 1, 1.1), ("quadrant", 1.1, 1.4), (".tech.", 1.4, 1.7)]
    tail = " ".join(w for w, _, _ in CP.sentence_case(CP.respell(ws, "Subscribe to the Qdrant YouTube channel at qdrant.tech.", CP.glossary())))
    ok = True
    for what, good in (('"quadrant" -> "Qdrant"', "Qdrant," in got), ('"started" kept (it was said)', "started" in got), ('"web ui" -> "Web UI"', "Web UI." in got),
                       ('"Quadrant\'s" -> "Qdrant\'s"', "Qdrant's channel" in tail), ('"quadrant .tech" -> "qdrant.tech"', tail.endswith("at qdrant.tech."))):
        print(f"  {'caught' if good else 'MISSED'}  captions {what}" + ("" if good else f"  -> {got}")); ok &= good
    return ok

def checks_test(out):
    import checks as CK
    bad = os.path.join(out, "bad.srt"); good = os.path.join(out, "good.srt")
    open(bad, "w", encoding="utf-8").write("1\n00:00:00,000 --> 00:00:02,500\nWelcome to Quadrant\n\n2\n00:00:02,400 --> 00:00:05,000\nThis line is far too long to read comfortably on any screen size\n")
    open(good, "w", encoding="utf-8").write("1\n00:00:00,000 --> 00:00:02,500\nWelcome to Qdrant\n\n2\n00:00:02,600 --> 00:00:05,000\nLet's get it running.\n")
    F = CK.srt_findings(bad); G = CK.srt_findings(good); ok = True
    for kind in ("spelling", "line_length", "overlap"):
        hit = any(f["kind"] == kind and f["sev"] == "fix" for f in F); print(f"  {'caught' if hit else 'MISSED'}  checks   {kind}"); ok &= hit
    extra = [f for f in G if f["sev"] == "fix"]
    for f in extra: print(f"  INVENTED checks   {f['kind']}: {f['msg']}")
    return ok and not extra

def hear_test(out):
    """captions from the video's own sound: a spoken take whose word list would be wrong is still captioned in full"""
    wav = os.path.join(out, "spoken.wav"); mp4 = os.path.join(out, "spoken.mp4")
    say = "Make sure you subscribe to the Quadrant YouTube channel. You can also visit the docs."
    if os.name != "nt" or subprocess.run(["powershell", "-NoProfile", "-Command", "Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                                          f"$s.SetOutputToWaveFile('{os.path.abspath(wav)}'); $s.Speak('{say}'); $s.Dispose()"], capture_output=True).returncode or not os.path.exists(wav):
        print("  skipped  captions heard from the video (no system voice to speak a test line)"); return True
    subprocess.run([FF, "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=gray:s=320x180:r=25", "-i", wav, "-c:v", "libx264", "-c:a", "aac", "-shortest", mp4], check=True)
    open(os.path.join(out, "spoken_cutlist.md"), "w").write("| edit time | source | push | script line | said | take |\n|---|---|---|---|---|---|\n"
        "| 0.00 | 0.00-3.50 | x1.00 | Make sure you subscribe to the Qdrant YouTube channel. | x | t |\n| 3.50 | 3.50-9.00 | x1.00 | You can also visit the docs. | x | t |\n")
    cap = os.path.join(out, "spoken_captions"); shutil.rmtree(cap, ignore_errors=True)
    subprocess.run([sys.executable, os.path.join(HERE, "captions.py"), mp4, "--cutlist", os.path.join(out, "spoken_cutlist.md"), "--out", cap], check=True, capture_output=True)
    text = " ".join(open(os.path.join(cap, "captions.srt"), encoding="utf-8").read().split())
    ok = True
    for what, good in (('"Make sure you subscribe" heard', "Make sure you subscribe" in text), ('"Quadrant" heard, captioned "Qdrant"', "Qdrant" in text and "Quadrant" not in text),
                       ('the last line heard', "visit the docs" in text)):
        print(f"  {'caught' if good else 'MISSED'}  captions {what}" + ("" if good else f"  -> {text[:120]}")); ok &= good
    return ok

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="audio_captions_selftest"); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    ok = voice_test(a.out) & caption_test(a.out) & hear_test(a.out) & checks_test(a.out)
    print("SELF-TEST PASSED" if ok else "SELF-TEST FAILED"); return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
