"""Cut the presenter out of the webcam background for the lightboard look: writes a grayscale matte video
(white = presenter) for an edit-time range of the cut, one frame per cut frame, with rembg's human
segmentation model and a little temporal smoothing so edges do not flicker.
  python matte.py 0 40.94      -> edit\\full_edit\\matte_0-41.mp4
"""
import os, sys, subprocess, numpy as np, cv2, imageio_ffmpeg
from PIL import Image
from rembg import remove, new_session
FF = imageio_ffmpeg.get_ffmpeg_exe(); EDIT = r"C:\Users\ADMIN\camera_audit\edit"
CUT = os.environ.get("MATTE_CUT", "v1")                               # v1: bulk_uploads_full_edit.mp4, v2: the v2 cut
BASE = os.path.join(EDIT, "full_edit", "bulk_uploads_full_edit.mp4" if CUT == "v1" else f"bulk_uploads_full_edit_{CUT}.mp4"); t0, t1 = float(sys.argv[1]), float(sys.argv[2])
OUT = os.path.join(EDIT, "full_edit", f"matte_{int(t0)}-{int(t1)}.mp4" if CUT == "v1" else f"matte_{CUT}_{int(t0)}-{int(t1)}.mp4"); W, H, FPS = 1920, 1080, 30
sess = new_session("u2net_human_seg"); cap = cv2.VideoCapture(BASE); cap.set(cv2.CAP_PROP_POS_MSEC, t0 * 1000); n = int((t1 - t0) * FPS)
cmd = [FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv420p", OUT]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE); prev = None; last = None
for i in range(n):
    ok, f = cap.read()
    if not ok: f = last
    last = f; im = Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
    a = np.asarray(remove(im, session=sess, only_mask=True)).astype(np.float32)
    if prev is not None: a = 0.6 * a + 0.4 * prev          # temporal smoothing
    prev = a; p.stdin.write(np.clip(a, 0, 255).astype(np.uint8).tobytes())
    if i % 150 == 0: print(f"  {t0 + i / FPS:6.1f}s", flush=True)
p.stdin.close(); p.wait(); print("->", OUT)
