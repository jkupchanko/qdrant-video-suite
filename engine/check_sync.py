"""check_sync.py: prove that a render keeps the presenter's voice and face one to one with the cut, start to end.

  python check_sync.py OUTPUT.mp4 CUT.mp4

Voice: at a point every ~15 s, 1.5 s of the render's audio is cross-correlated with the cut's; the lag must
be within 45 ms. (The render adds sound effects on top; the voice still dominates the correlation.)
Face: wherever the render shows the cut full frame (cropped inside its bars, as the engine shows it), the render's frame is matched against the cut's frames
a third of a second either side; the best match must be the same frame (within one frame, 33 ms).
This catches the old drift: a cut whose video timestamps have gaps, read frame by frame, ran the face up
to 1.4 s ahead of the voice by the end. Exits 1 on any failure.
"""
import sys, subprocess, numpy as np, cv2, imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()

def pcm(path, t, d):
    out = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", path, "-t", f"{d}", "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(out, np.int16).astype(np.float32)

def lag_ms(a, b, maxlag=0.4, sr=16000):
    a = a - a.mean(); b = b - b.mean(); n = min(len(a), len(b)); a, b = a[:n], b[:n]
    c = np.fft.irfft(np.fft.rfft(a, 2 * n) * np.conj(np.fft.rfft(b, 2 * n))); m = int(maxlag * sr)
    cand = np.concatenate([c[-m:], c[:m + 1]]); return (int(np.argmax(cand)) - m) * 1000 / sr

def small(f): return cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (192, 108)).astype(np.float32)

def main(out, cut):
    co, cc = cv2.VideoCapture(out), cv2.VideoCapture(cut); fps = co.get(cv2.CAP_PROP_FPS) or 30
    n = int(min(co.get(cv2.CAP_PROP_FRAME_COUNT), cc.get(cv2.CAP_PROP_FRAME_COUNT))); dur = n / fps; bad = []
    print("voice (render against cut):")
    for t in np.arange(2.0, dur - 2.0, 15.0).tolist() + [dur - 2.2]:
        L = lag_ms(pcm(out, t, 1.5), pcm(cut, t, 1.5)); ok = abs(L) <= 45; bad += [] if ok else [("voice", round(t, 1), L)]
        print(f"  {t:7.1f} s  lag {L:+6.1f} ms  {'ok' if ok else 'OFF'}")
    import engine as E                                                            # the render shows the face cropped inside the cut's bars
    from PIL import Image
    cut_frames = []
    while True:
        ok, f = cc.read()
        if not ok: break
        cut_frames.append(small(cv2.cvtColor(np.asarray(E.full_face(Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)))), cv2.COLOR_RGB2BGR)))
    print("face (where the render shows the cut full frame):"); checked = 0; i = 0
    while True:
        ok, f = co.read()
        if not ok: break
        if i % 10 == 0 and i < len(cut_frames):
            g = small(f)
            if np.abs(g - cut_frames[i]).mean() < 4:                                 # the cut is on screen untouched here (a frame mid-transition scores over 10)
                errs = [(np.abs(g - cut_frames[j]).mean(), j - i) for j in range(max(0, i - 10), min(len(cut_frames), i + 11))]
                e, k = min(errs); checked += 1
                if abs(k) > 1: bad.append(("face", round(i / fps, 2), k * 1000 / fps))
                if checked % 10 == 1 or abs(k) > 1: print(f"  {i / fps:7.2f} s  best match {k:+d} frames  {'ok' if abs(k) <= 1 else 'OFF'}")
        i += 1
    print(f"face checked at {checked} points; {'all within one frame' if not [b for b in bad if b[0] == 'face'] else 'OFF somewhere'}")
    print("IN SYNC" if not bad else f"OUT OF SYNC: {bad[:20]}")
    return 1 if bad else 0

if __name__ == "__main__":
    if len(sys.argv) < 3: print(__doc__); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
