"""cut_marks.py: tighten a long screen capture into a clip using action timestamps.

Keeps a window around each marked action (pre seconds before, post seconds after), finds when the page stops
changing after the last action (so the final hold starts on a fully loaded screen), and concatenates the pieces.

usage: python cut_marks.py RAW.mp4 OUT.mp4 --marks 4.12,37.83,75.28 [--pre 1.6] [--post 3.4] [--hold 3.0] [--start 2.0]
"""
import argparse, re, subprocess, tempfile, os
import imageio_ffmpeg

ap = argparse.ArgumentParser()
ap.add_argument("raw"); ap.add_argument("out"); ap.add_argument("--marks", required=True)
ap.add_argument("--pre", type=float, default=1.6); ap.add_argument("--post", type=float, default=3.4)
ap.add_argument("--hold", type=float, default=3.0); ap.add_argument("--start", type=float, default=2.0)
ap.add_argument("--settle", type=float, default=1.5, help="seconds without change that count as 'loaded'")
a = ap.parse_args()
ff = imageio_ffmpeg.get_ffmpeg_exe()
marks = [float(m) for m in a.marks.split(",")]

# when does the screen reach its final state after the last action? Compare each half-second to the frame 60 s on.
import glob, numpy as np
from PIL import Image
last = marks[-1]
tmp = tempfile.mkdtemp(prefix="cut_")
subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-ss", str(last), "-t", "60", "-i", a.raw, "-vf", "fps=2,scale=320:-1", os.path.join(tmp, "f_%04d.png")], check=True)
files = sorted(glob.glob(os.path.join(tmp, "f_*.png")))
frames = [np.asarray(Image.open(f).convert("L"), dtype=np.float32) for f in files]
final = frames[-1]
loaded = last + 1.0
for i, f in enumerate(frames):
    if np.abs(f - final).mean() < 2.0:
        loaded = last + i / 2 + 0.5; break
for f in files: os.remove(f)
os.rmdir(tmp)
print(f"screen reaches its final state at {loaded:.2f}s")

segs = []
for i, m in enumerate(marks):
    s = a.start if i == 0 else m - a.pre
    e = (m + a.post) if i < len(marks) - 1 else (loaded + a.hold)
    segs.append((max(0, s), e))
print("segments:", [(round(s, 2), round(e, 2)) for s, e in segs], "total", round(sum(e - s for s, e in segs), 2), "s")
filt = []
for k, (s, e) in enumerate(segs):
    filt.append(f"[0:v]trim=start={s:.3f}:end={e:.3f},setpts=PTS-STARTPTS[v{k}]")
filt.append("".join(f"[v{k}]" for k in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=0[v]")
subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", a.raw, "-filter_complex", ";".join(filt), "-map", "[v]", "-r", "30",
                "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out], check=True)
print("wrote", a.out)
