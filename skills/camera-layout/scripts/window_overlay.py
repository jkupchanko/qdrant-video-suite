#!/usr/bin/env python
"""window_overlay.py: put the presenter in a rectangular window over a screen clip, framed by the rule.

  python window_overlay.py SCREEN.mp4 FACE.mp4 --out OUT.mp4 [--crop x,y,w,h] [--width 0.20] [--corner top-right]
                           [--screen-start 36 --face-start 18 --duration 12] [--aspect 4:3] [--margin 24]

--crop is the source box for the face (from frame_face.py's "small crop x= y= w= h=" line). Without it the
face is measured here with the same rule. The window is --width of the frame width, in --aspect, with rounded
corners and a thin off-white border, --margin px in from the corner. Audio comes from the screen clip.
"""
if __name__ == "__main__":                                   # run on the suite's own Python (.venv, made by setup.py), whichever python started it
    import os as _o, sys as _s, subprocess as _sp
    _v = _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), "..", "..", "..", ".venv", *(("Scripts", "python.exe") if _o.name == "nt" else ("bin", "python")))
    if _o.path.exists(_v) and _o.path.normcase(_o.path.realpath(_s.prefix)) != _o.path.normcase(_o.path.realpath(_o.path.dirname(_o.path.dirname(_v)))):
        _s.exit(_sp.call([_v, _o.path.realpath(__file__)] + _s.argv[1:]))
import argparse, os, subprocess, sys, tempfile
import imageio_ffmpeg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CORNER_ORDER = ["top-right", "top-left", "bottom-right", "bottom-left"]

def busy_score(gray, box):
    """how much is drawn under a box: share of edge pixels (text, lines, diagrams) in it"""
    import cv2
    x, y, w, h = box
    sub = gray[max(0, y):y + h, max(0, x):x + w]
    if sub.size == 0: return 1.0
    return float((cv2.Canny(sub, 60, 140) > 0).mean())

def safe_corner(screen_frame, pw, ph, margin, W, H, preferred="top-right", threshold=0.012):
    """the first corner in preference order where the window would not sit on content; None if every corner is busy.
    Returns (corner, scores). The window box is padded by 12 px so it does not kiss the text either."""
    import cv2
    gray = cv2.cvtColor(screen_frame, cv2.COLOR_BGR2GRAY)
    order = [preferred] + [c for c in CORNER_ORDER if c != preferred]
    scores = {}
    for c in order:
        px = W - pw - margin if "right" in c else margin; py = H - ph - margin if "bottom" in c else margin
        scores[c] = busy_score(gray, (px - 12, py - 12, pw + 24, ph + 24))
    for c in order:
        if scores[c] <= threshold: return c, scores
    return None, scores

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("screen"); ap.add_argument("face"); ap.add_argument("--out", required=True)
    ap.add_argument("--crop", help="x,y,w,h in the face source"); ap.add_argument("--width", type=float, default=0.20); ap.add_argument("--aspect", default="4:3")
    ap.add_argument("--corner", default="top-right", choices=["top-right", "top-left", "bottom-right", "bottom-left"]); ap.add_argument("--margin", type=int, default=24)
    ap.add_argument("--screen-start", type=float, default=0); ap.add_argument("--face-start", type=float, default=0); ap.add_argument("--duration", type=float)
    ap.add_argument("--frame", default="1920x1080")
    ap.add_argument("--auto-corner", action="store_true", help="check what is under the window on the screen clip's first frame and move it to the first clear corner (top-right, top-left, bottom-right, bottom-left); refuse if every corner is busy")
    a = ap.parse_args()
    W, H = (int(v) for v in a.frame.split("x")); aw, ah = (int(v) for v in a.aspect.split(":"))
    pw = int(W * a.width); ph = int(pw * ah / aw)
    if a.crop: x, y, w, h = (int(v) for v in a.crop.split(","))
    else:
        from frame_face import measure, crop_box, ASPECT
        img, env, hh, n = measure(a.face); (l, t, r, b), _ = crop_box(env, hh, aw / ah, img.shape[1], img.shape[0]); x, y, w, h = l, t, r - l, b - t
        print(f"face crop measured on {n} frame(s): x={x} y={y} w={w} h={h}")
    from PIL import Image, ImageDraw
    tmp = tempfile.mkdtemp(prefix="win_")
    m = Image.new("L", (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=16, fill=255); m.save(os.path.join(tmp, "mask.png"))
    bd = Image.new("RGBA", (pw + 8, ph + 8), (0, 0, 0, 0)); ImageDraw.Draw(bd).rounded_rectangle([0, 0, pw + 7, ph + 7], radius=20, outline=(245, 244, 240, 255), width=4); bd.save(os.path.join(tmp, "border.png"))
    if a.auto_corner:
        import cv2
        cap = cv2.VideoCapture(a.screen); cap.set(cv2.CAP_PROP_POS_MSEC, a.screen_start * 1000 + 500); ok, f0 = cap.read(); cap.release()
        if not ok: raise SystemExit("could not read the screen clip")
        f0 = cv2.resize(f0, (W, H))
        c, scores = safe_corner(f0, pw, ph, a.margin, W, H, a.corner)
        print("corner check (edge share under the window): " + ", ".join(f"{k} {v:.3f}" for k, v in scores.items()))
        if c is None: raise SystemExit("every corner has content under it: use NONE for this passage (no window), or a smaller window")
        if c != a.corner: print(f"{a.corner} would cover content; moving the window to {c}")
        a.corner = c
    px = W - pw - a.margin if "right" in a.corner else a.margin; py = H - ph - a.margin if "bottom" in a.corner else a.margin
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-ss", str(a.screen_start)] + (["-t", str(a.duration)] if a.duration else []) + ["-i", a.screen, "-ss", str(a.face_start)] + (["-t", str(a.duration)] if a.duration else []) + ["-i", a.face,
           "-loop", "1", "-i", os.path.join(tmp, "mask.png"), "-loop", "1", "-i", os.path.join(tmp, "border.png"),
           "-filter_complex", f"[1:v]crop={w}:{h}:{x}:{y},scale={pw}:{ph}[f];[2:v]format=gray[m];[f][m]alphamerge[fa];[0:v][3:v]overlay={px - 4}:{py - 4}:format=auto[b1];[b1][fa]overlay={px}:{py}:format=auto,format=yuv420p[v]",
           "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-crf", "16", "-c:a", "aac", "-shortest", a.out]
    subprocess.run(cmd, check=True)
    print(f"-> {a.out}  window {pw}x{ph} at ({px},{py}), {a.corner}, {int(a.width * 100)}% width")

if __name__ == "__main__":
    main()
