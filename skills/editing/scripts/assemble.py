#!/usr/bin/env python
"""assemble.py: join pieces of a take into one cut with the voice and the picture locked frame by frame.

Why this exists: cutting each piece to its own AAC + H.264 file and joining them with the concat demuxer
(-c copy) drifts. Every AAC piece carries up to one packet (21 ms) of padding, so at each join the audio
overlaps the next piece while the video gets a timestamp gap. Over the 53 joins of Bulk Uploads that was
1.4 s of picture against voice by the end. The lips visibly lead the words, and anything that reads frames
in order (a compositor, a gaze tracker) is off by that much.

Here every piece is cut twice from the source with input seeking: the video with exactly N frames, and the
audio as PCM with exactly N * sr / fps samples (1600 per frame at 48 kHz, 30 fps). Piece boundaries are
whole frames on the edit timeline. The video pieces are joined by stream copy (same encoder settings, exact
durations, so no gaps), the audio pieces are joined sample by sample, and the audio is encoded to AAC once.
Picture and sound cannot drift, because each piece has the same length in both by construction.

  from assemble import assemble
  times = assemble(src, spans, out, vf_for=lambda k: "hflip", times=None)

spans    [(x0, x1), ...] in source seconds
times    edit-time start of each piece (a cut list's times); default: the running sum of span lengths.
         Boundaries are snapped to frames, and piece k runs from times[k] to times[k+1] on the edit
         timeline, taken from x0 onwards in the source.
vf_for   k -> the video filter chain for piece k (mirror, crop and push, bars); fps and format are added here
"""
import os, sys, wave, subprocess, tempfile, shutil
from concurrent.futures import ThreadPoolExecutor
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()

def _run(cmd): subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def assemble(src, spans, out, vf_for=lambda k: "", times=None, fps=30, sr=48000, fade=0.02, crf=16, jobs=4, keep=False, quiet=False):
    if times is None:
        times, t = [], 0.0
        for x0, x1 in spans: times.append(t); t += x1 - x0
    end = times[-1] + (spans[-1][1] - spans[-1][0])
    F = [round(t * fps) for t in times] + [round(end * fps)]
    N = [F[k + 1] - F[k] for k in range(len(spans))]
    spf = sr // fps
    work = tempfile.mkdtemp(prefix="assemble_")
    def piece(k):
        x0 = spans[k][0]; n = N[k]; d = n / fps; vf = vf_for(k)
        chain = f"fps={fps}" + ("," + vf if vf else "") + f",format=yuv420p,tpad=stop_mode=clone:stop_duration=1,trim=end_frame={n}"
        _run([FF, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{x0:.4f}", "-i", src, "-t", f"{d + 0.5:.4f}", "-an", "-vf", chain, "-frames:v", str(n),
              "-c:v", "libx264", "-crf", str(crf), "-preset", "medium", "-pix_fmt", "yuv420p", "-video_track_timescale", str(fps * 512), os.path.join(work, f"v{k:03d}.mp4")])
        af = f"aresample={sr},apad,atrim=end_sample={n * spf},afade=t=in:st=0:d={fade},afade=t=out:st={max(0.0, d - fade):.4f}:d={fade}"
        _run([FF, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{x0:.4f}", "-i", src, "-t", f"{d + 0.5:.4f}", "-vn", "-af", af, "-ac", "2", "-c:a", "pcm_s16le", os.path.join(work, f"a{k:03d}.wav")])
    with ThreadPoolExecutor(jobs) as ex: list(ex.map(piece, range(len(spans))))
    lst = os.path.join(work, "v.txt"); open(lst, "w").write("".join(f"file 'v{k:03d}.mp4'\n" for k in range(len(spans))))
    _run([FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", os.path.join(work, "video.mp4")])
    total = 0
    with wave.open(os.path.join(work, "audio.wav"), "wb") as wo:
        wo.setnchannels(2); wo.setsampwidth(2); wo.setframerate(sr)
        for k in range(len(spans)):
            with wave.open(os.path.join(work, f"a{k:03d}.wav"), "rb") as wi:
                fr = wi.readframes(wi.getnframes()); n_s = len(fr) // 4
                if n_s != N[k] * spf: raise RuntimeError(f"piece {k}: {n_s} samples, expected {N[k] * spf}")
                wo.writeframes(fr); total += n_s
    _run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i", os.path.join(work, "video.mp4"), "-i", os.path.join(work, "audio.wav"), "-map", "0:v", "-map", "1:a",
          "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    frames = verify(out, fps)
    if frames != sum(N): raise RuntimeError(f"{out}: {frames} frames, expected {sum(N)}")
    if not quiet: print(f"assembled {len(spans)} pieces -> {out}: {frames} frames = {frames / fps:.3f} s, audio {total / sr:.3f} s (locked: {total == frames * spf})")
    if not keep: shutil.rmtree(work, ignore_errors=True)
    return [f / fps for f in F[:-1]]

def verify(path, fps=30):
    """count the video frames, and fail if the video timestamps have a gap (the symptom of the old join)"""
    import cv2
    c = cv2.VideoCapture(path); n = 0; last = -1.0; gaps = 0
    while c.grab():
        t = c.get(cv2.CAP_PROP_POS_MSEC) / 1000
        if last >= 0 and t - last > 1.5 / fps: gaps += 1
        last = t; n += 1
    if gaps: raise RuntimeError(f"{path}: {gaps} timestamp gaps in the video")
    return n

if __name__ == "__main__":
    print(__doc__)
