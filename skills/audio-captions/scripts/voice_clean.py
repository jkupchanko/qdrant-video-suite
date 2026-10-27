#!/usr/bin/env python
"""voice_clean.py: the voice of a cut, made even and clean, with only the fixes this take needs. The picture is copied as it is.

  python voice_clean.py CUT.mp4 --out CUT_voice.mp4 [--cutlist cutlist.md] [--report voice.json]

Measured first, on this take (never a fixed recipe; everyone records in a different room with a different microphone):

  level jumps   the voice level of every piece of the cut (from the cut list). Pieces come from different takes, so one can
                sit 7 dB under the next (Get Started: 36 of 127 joins jumped over 3 dB; 0 after). A piece more than 1.5 dB from the
                cut's own median is brought most of the way back (all but 1 dB, at most 6 dB), with a short ramp at its edges.
  noise         the room under the voice: the voice level against the floor between words. Under the limit (research.md) a
                denoise (ffmpeg anlmdn). Every filter's delay is measured and taken back, so the voice stays on the lips.
  hum           a mains hum (50 or 60 Hz and its harmonics standing out of the quiet parts by 6 dB or more) is notched out.
  rumble        energy under 100 Hz well above what a voice has: an 80 Hz high-pass.

Loudness is not set here: master_audio.py (the build's master stage) brings the finished video to about -14 LUFS.
Writes what it measured, what it did and why (--report), and checks the result: the same length to the sample (the voice
stays on the lips), level jumps after, the floor after.
"""
import argparse, json, os, re, subprocess, sys
import numpy as np, imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe(); SR = 48000
LIMITS = dict(jump_db=1.5, keep_db=1.0, max_gain_db=6.0, snr_db=30.0, hum_db=6.0, low_share=0.05)   # see references/research.md

def decode(path):
    return np.frombuffer(subprocess.run([FF, "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout,
                         np.int16).astype(np.float64) / 32768

def envelope(x):
    n = len(x) // 480; return 20 * np.log10(np.maximum(1e-7, np.sqrt((x[:n * 480].reshape(n, 480) ** 2).mean(axis=1))))   # 10 ms

def pieces(cutlist, dur):
    if not cutlist or not os.path.exists(cutlist): return [(0.0, dur)]
    t = [float(v) for v in re.findall(r"^\| ([\d.]+) \| [\d.]+-[\d.]+ \|", open(cutlist, encoding="utf-8").read(), flags=re.M)]
    return list(zip(t, t[1:] + [dur])) if t else [(0.0, dur)]

def measure(x, P):
    env = envelope(x); floor, voice = float(np.percentile(env, 3)), float(np.percentile(env, 90))
    loud = voice - 12                                               # the voice's own body, not the floor: denoising must not move it
    lv = []
    for a, b in P:
        e = env[int(a * 100):int(b * 100)]                          # a piece's level: the power mean of its voiced part (as loudness is
        v = e[e > np.percentile(e, 95) - 15] if len(e) > 20 else e  # heard), voiced meaning within 15 dB of the piece's own peak: it moves
        lv.append(float(10 * np.log10(np.mean(10 ** (v / 10)))) if len(e) > 20 and (e > loud).mean() > 0.2 else None)   # exactly with a gain
    ok = [v for v in lv if v is not None]; med = float(np.median(ok)) if ok else voice
    jumps = [abs(b - a) for a, b in zip(lv, lv[1:]) if a is not None and b is not None]
    q = np.repeat(env < floor + 3, 480); q = np.r_[q, np.zeros(max(0, len(x) - len(q)), bool)][:len(x)]; xq = x[q][: SR * 20]
    hum = {}
    if len(xq) > SR:                                                    # averaged over 1 s slices (Welch): a hum stands out of
        segs = xq[: len(xq) // SR * SR].reshape(-1, SR) * np.hanning(SR)  # room noise only once the noise is averaged down
        s = (np.abs(np.fft.rfft(segs, axis=1)) ** 2).mean(axis=0); f = np.fft.rfftfreq(SR, 1 / SR)
        for hz in (50, 60):
            peaks = []
            for k in (1, 2, 3):
                band = (f >= hz * k - 1) & (f <= hz * k + 1); ref = (f > hz * k - 20) & (f < hz * k + 20) & ~((f > hz * k - 3) & (f < hz * k + 3))
                peaks.append(10 * np.log10(max(1e-30, s[band].max()) / max(1e-30, np.median(s[ref]))))   # digital silence: no hum
            hum[hz] = round(float(peaks[0]), 1) if peaks[0] >= 3 else round(float(min(peaks[0], max(peaks))), 1)   # a hum shows at its fundamental
    seg = x[: SR * 60]; s = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2; f = np.fft.rfftfreq(len(seg), 1 / SR)
    low = float(s[(f > 20) & (f < 100)].sum() / max(1e-12, s[(f > 20) & (f < 8000)].sum()))
    return dict(floor_db=round(floor, 1), voice_db=round(voice, 1), snr_db=round(voice - floor, 1), piece_db=[None if v is None else round(v, 1) for v in lv],
                median_db=round(med, 1), jumps_over_3db=sum(1 for j in jumps if j > 3), biggest_jump_db=round(max(jumps), 1) if jumps else 0.0,
                hum=hum, low_share=round(low, 4))

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cut"); ap.add_argument("--out", required=True); ap.add_argument("--cutlist"); ap.add_argument("--report")
    a = ap.parse_args(); x = decode(a.cut); dur = len(x) / SR; P = pieces(a.cutlist, dur); M = measure(x, P); L = LIMITS; did = []
    # 1. the room, the hum, the rumble: only what this take has
    af = []
    if M["low_share"] > L["low_share"]: af.append("highpass=f=80"); did.append(f"rumble: {M['low_share'] * 100:.1f}% of the energy under 100 Hz, so an 80 Hz high-pass")
    for hz, pk in sorted(M["hum"].items(), key=lambda kv: -kv[1])[:1]:      # mains is 50 or 60 Hz, never both: the stronger one
        if pk >= L["hum_db"]:
            af += [f"bandreject=f={hz * k}:width_type=h:w=4" for k in (1, 2, 3)]; did.append(f"hum: {hz} Hz stands {pk} dB out of the quiet, notched with two harmonics")
    if M["snr_db"] < L["snr_db"]:
        af.append("anlmdn=s=7:p=0.002:r=0.002"); did.append(f"noise: the voice is {M['snr_db']} dB over the room (limit {L['snr_db']}), so a denoise (anlmdn)")
        # anlmdn, not afftdn: on real speech with room noise added it took the floor down 7 dB to afftdn's 5, and delays the
        # voice 4 ms to afftdn's 25 (most of a frame: the voice would sit late on the lips)
    if af:                                                                  # filter, then measure the filters' delay and take it back
        y = np.frombuffer(subprocess.run([FF, "-v", "error", "-f", "f64le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", ",".join(af), "-f", "f64le", "-"],
                                         input=x.astype(np.float64).tobytes(), capture_output=True).stdout, np.float64)[: len(x)]
        n = min(len(x), SR * 20); A_, B_ = x[SR:n], y[SR:n]
        cc = np.fft.irfft(np.fft.rfft(A_, 2 * len(A_)) * np.conj(np.fft.rfft(B_, 2 * len(A_)))); lag = int(np.argmax(np.r_[cc[-4800:], cc[:4800]])) - 4800
        y = np.r_[y[-lag:], np.zeros(-lag)] if lag < 0 else np.r_[np.zeros(lag), y[:len(y) - lag]]   # the voice back on the lips
        did.append(f"sync: the filters delayed the voice {-lag / SR * 1000:.1f} ms; taken back"); x = y[: len(x)]; af = []
    # 2. even the pieces, measured after the cleaning (a denoise quiets a soft piece more than a loud one):
    #    each one most of the way to the cut's own median, with 30 ms ramps
    ML = measure(x, P) if any(d.startswith(('noise', 'hum', 'rumble')) for d in did) else M
    g = np.zeros(len(x)); changed = 0
    for (s0, s1), v in zip(P, ML["piece_db"]):
        if v is None: continue
        d = ML["median_db"] - v
        if abs(d) > L["jump_db"]:
            gain = float(np.clip(np.sign(d) * (abs(d) - L["keep_db"]), -L["max_gain_db"], L["max_gain_db"])); g[int(s0 * SR):int(s1 * SR)] = gain; changed += 1
    if changed:
        k = int(0.03 * SR); ramp = np.convolve(g, np.ones(k) / k, mode="same")     # no step in the gain, ever
        x = x * 10 ** (ramp / 20); did.append(f"levels: {changed} of {len(P)} pieces brought toward the cut's median ({ML['median_db']} dB)")
    wav = a.out + ".wav"
    with open(wav, "wb") as f:
        import wave
        pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)              # both channels written here: ffmpeg's own mono-to-stereo
        w = wave.open(f, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.repeat(pcm, 2).tobytes()); w.close()   # costs 3 dB
    cmd = [FF, "-v", "error", "-y", "-i", a.cut, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy"] + (["-af", ",".join(af)] if af else []) + \
          ["-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.4f}", "-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True); os.remove(wav)
    y = decode(a.out); A = measure(y, P)
    res = dict(before=M, after={k: A[k] for k in ("floor_db", "voice_db", "snr_db", "jumps_over_3db", "biggest_jump_db")}, did=did or ["nothing: this take needs no fix"],
               length_s=dict(before=round(dur, 4), after=round(len(y) / SR, 4)), limits=L)
    if a.report: json.dump(res, open(a.report, "w"), indent=1)
    print("\n".join(res["did"]))
    print(f"jumps over 3 dB: {M['jumps_over_3db']} -> {A['jumps_over_3db']} (biggest {M['biggest_jump_db']} -> {A['biggest_jump_db']} dB); "
          f"voice over the room: {M['snr_db']} -> {A['snr_db']} dB; length {dur:.3f} -> {len(y) / SR:.3f} s -> {a.out}")

if __name__ == "__main__":
    main()
