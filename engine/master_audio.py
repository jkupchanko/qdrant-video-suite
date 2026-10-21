"""master_audio.py: bring a finished render to YouTube loudness without touching the picture.

  python master_audio.py IN.mp4 [OUT.mp4] [--lufs -14] [--tp -1.5]

The cut and the styles mix at about -24 LUFS. YouTube turns loud videos down to about -14 LUFS but never turns quiet ones up,
so a -24 LUFS video plays 10 dB under everything around it. This runs ffmpeg's loudnorm in two passes (measure, then apply the
measured values linearly, so the dynamics and the timing stay as they are) with a true-peak ceiling, and copies the video
stream as it is. Run video-review on the result: its audio pass checks the loudness, the peaks and that the voice still sits on
the lips (lag against the cut).
"""
import sys, json, re, subprocess, argparse, imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("inp"); ap.add_argument("out", nargs="?"); ap.add_argument("--lufs", type=float, default=-14.0); ap.add_argument("--tp", type=float, default=-1.5)
    a = ap.parse_args(); out = a.out or a.inp.replace(".mp4", "_master.mp4")
    target = f"I={a.lufs}:TP={a.tp}:LRA=11"
    info = subprocess.run([FF, "-hide_banner", "-i", a.inp], capture_output=True, text=True).stderr
    h, mi, se = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info).groups(); dur = int(h) * 3600 + int(mi) * 60 + float(se)
    # loudnorm looks 3 s ahead; at the end of the stream it flushes that buffer and the last ~3 s came out 65 ms late
    # (video-review caught it as voice drift). 4 s of silence after the end take the flush; the trim restores the length.
    pad, trim = "apad=pad_dur=4,", f",atrim=end={dur:.3f},asetpts=N/SR/TB"
    r = subprocess.run([FF, "-hide_banner", "-i", a.inp, "-af", f"loudnorm={target}:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(re.findall(r"\{[^{}]*\}", r.stderr)[-1])
    af = (pad + f"loudnorm={target}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
          f":offset={m['target_offset']}:linear=true,aresample=48000" + trim)
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i", a.inp, "-map", "0:v", "-map", "0:a", "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "192k",
                    "-t", f"{dur:.3f}", "-movflags", "+faststart", out], check=True)
    print(f"{a.inp}: {m['input_i']} LUFS, true peak {m['input_tp']} dBTP -> {out} (target {a.lufs} LUFS, {a.tp} dBTP)")

if __name__ == "__main__":
    main()
