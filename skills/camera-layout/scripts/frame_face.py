#!/usr/bin/env python
"""frame_face.py: cut a presenter crop around the face, the same way every time.

  python frame_face.py IMAGE_OR_VIDEO --out DIR [--layouts full,inset,small,half] [--guides]

The rule, in face heights (h = height of the detected face box, brow to chin):
  top     head top (about 0.35 h above the box) plus 0.25 h of headroom
  bottom  chin plus 0.9 h: the neck and the top of the chest, so the shoulders are in
  sides   at least 0.6 h of clear space left and right of the face, so a turn or a lean stays in frame
  centre  the face centre sits on the vertical centre line of the crop; eyes land near the upper third
The crop is then widened to the layout's aspect (16:9 full and inset, 4:3 small, 9:16 half panel) and
clamped to the source. With a video, the face is measured on frames through the whole clip and the crop
is built around where the face GOES, not one frame, so movement is covered.

Writes one png per layout plus <name>_guides.png showing the detected face, the clearances and the centre
line, and prints the crop boxes (source pixels) for the editor.
"""
import argparse, os, sys
import cv2, numpy as np

ASPECT = {"full": 16 / 9, "inset": 16 / 9, "small": 4 / 3, "half": 9 / 16}
OUT_SIZE = {"full": (1920, 1080), "inset": (960, 540), "small": (640, 480), "half": (608, 1080)}
CASC = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def faces_in(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    fs = CASC.detectMultiScale(g, 1.08, 4, minSize=(max(24, img.shape[1] // 40),) * 2)
    return [tuple(int(v) for v in b) for b in fs]

def measure(path, step=0.5):
    """face box to frame around: on an image the biggest face; on a video the envelope of where the face goes"""
    if path.lower().endswith((".mp4", ".mov", ".webm", ".mkv")):
        cap = cv2.VideoCapture(path); fps = cap.get(cv2.CAP_PROP_FPS) or 30; every = max(1, int(fps * step)); i = 0; boxes = []; first = None
        while True:
            ok = cap.grab()
            if not ok: break
            if i % every == 0:
                ok, f = cap.retrieve()
                fs = faces_in(f)
                if fs:
                    boxes.append(max(fs, key=lambda b: b[2] * b[3]))
                    if first is None: first = f          # the preview frame is the first one with a face, not a fade-in
                elif first is None and f.mean() > 40: first = f
            i += 1
        cap.release()
        if not boxes: raise SystemExit("no face found in the video")
        b = np.array(boxes, float)
        h = float(np.median(b[:, 3])); w = float(np.median(b[:, 2]))
        x0 = float(np.percentile(b[:, 0], 5)); x1 = float(np.percentile(b[:, 0] + b[:, 2], 95))
        y0 = float(np.percentile(b[:, 1], 5)); y1 = float(np.percentile(b[:, 1] + b[:, 3], 95))
        # the envelope: where the face was, between the 5th and 95th percentile of its positions
        return first, (x0, y0, x1 - x0, y1 - y0), h, len(boxes)
    img = cv2.imread(path)
    if img is None: raise SystemExit(f"cannot read {path}")
    fs = faces_in(img)
    if not fs: raise SystemExit("no face found")
    x, y, w, h = max(fs, key=lambda b: b[2] * b[3])
    return img, (float(x), float(y), float(w), float(h)), float(h), 1

def crop_box(env, h, aspect, W, H, headroom=0.25, head_top=0.35, chin_buffer=0.9, side=0.6):
    ex, ey, ew, eh = env
    top = ey - head_top * h - headroom * h
    bottom = ey + eh + chin_buffer * h
    left = ex - side * h; right = ex + ew + side * h
    ch = bottom - top; cw = right - left
    cx = ex + ew / 2
    # widen (never shrink) to the aspect, keeping the face centred horizontally
    if cw / ch < aspect: cw = ch * aspect
    else: ch = cw / aspect; top = (ey + eh / 2) - ch * 0.42   # face centre a little above the crop centre: eyes near the upper third
    left = cx - cw / 2; right = cx + cw / 2; bottom = top + ch
    # clamp to the source, shifting rather than shrinking; report the shift
    dx = max(0, -left) - max(0, right - W); dy = max(0, -top) - max(0, bottom - H)
    left += dx; right += dx; top += dy; bottom += dy
    if left < 0 or right > W or top < 0 or bottom > H:    # still too big: scale the crop down around the face centre
        k = min(W / cw, H / ch); cw *= k; ch *= k; left = min(max(0, cx - cw / 2), W - cw); top = min(max(0, (ey + eh / 2) - ch * 0.42), H - ch); right, bottom = left + cw, top + ch; dx = dy = 0
    return (int(left), int(top), int(right), int(bottom)), (dx, dy)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src"); ap.add_argument("--out", required=True); ap.add_argument("--layouts", default="full,inset,small,half"); ap.add_argument("--guides", action="store_true", default=True)
    ap.add_argument("--mirror", action="store_true", help="flip left-right first (house rule for self-recorded talking heads)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    img, env, h, n = measure(a.src)
    if a.mirror:
        img = cv2.flip(img, 1); W = img.shape[1]; ex, ey, ew, eh = env; env = (W - ex - ew, ey, ew, eh)
    H, W = img.shape[:2]; name = os.path.splitext(os.path.basename(a.src))[0]
    ex, ey, ew, eh = env
    print(f"{name}: face {int(ew)}x{int(eh)} px at ({int(ex)},{int(ey)}), measured on {n} frame(s); unit h = {h:.0f} px")
    # is the source framed loosely enough for the rule? report what is missing rather than silently cropping tighter
    need_top = ey - 0.6 * h; need_bottom = ey + eh + 0.9 * h; need_l = ex - 0.6 * h; need_r = ex + ew + 0.6 * h
    short = []
    if need_top < 0: short.append(f"{int(-need_top)} px above the head")
    if need_bottom > H: short.append(f"{int(need_bottom - H)} px below the chin (shoulders are cut)")
    if need_l < 0: short.append(f"{int(-need_l)} px on the left")
    if need_r > W: short.append(f"{int(need_r - W)} px on the right")
    if short: print("  SOURCE TOO TIGHT: the rule wants " + ", ".join(short) + ". Step the camera back or widen the lens; the crops below are the best fit, not the rule.")
    else: print("  source has room for the rule on every side")
    g = img.copy()
    cv2.rectangle(g, (int(ex), int(ey)), (int(ex + ew), int(ey + eh)), (0, 0, 255), 3)
    for lay in a.layouts.split(","):
        (l, t, r, b), (dx, dy) = crop_box(env, h, ASPECT[lay], W, H)
        crop = cv2.resize(img[t:b, l:r], OUT_SIZE[lay], interpolation=cv2.INTER_AREA)
        cv2.imwrite(os.path.join(a.out, f"{name}_{lay}.png"), crop)
        col = {"full": (255, 200, 0), "inset": (0, 200, 255), "small": (0, 255, 120), "half": (255, 120, 255)}[lay]
        cv2.rectangle(g, (l, t), (r, b), col, 3); cv2.putText(g, lay, (l + 8, t + 34), cv2.FONT_HERSHEY_SIMPLEX, 1.0, col, 2)
        off = f"  (shifted {int(dx)},{int(dy)} px to stay inside the source)" if (dx or dy) else ""
        print(f"  {lay:5s} crop x={l} y={t} w={r - l} h={b - t}  face centre at {100 * ((ex + ew / 2) - l) / (r - l):.0f}% across, {100 * ((ey + eh / 2) - t) / (b - t):.0f}% down{off}")
    # guide lines: head top + headroom, chin buffer, side clearance, centre line
    cx = int(ex + ew / 2)
    cv2.line(g, (cx, 0), (cx, H), (255, 255, 255), 1)
    for yy, label in ((int(ey - 0.35 * h), "head top"), (int(ey - 0.6 * h), "headroom"), (int(ey + eh), "chin"), (int(ey + eh + 0.9 * h), "chin + 0.9h: shoulders")):
        cv2.line(g, (0, yy), (W, yy), (255, 255, 255), 1); cv2.putText(g, label, (10, max(20, yy - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    for xx in (int(ex - 0.6 * h), int(ex + ew + 0.6 * h)):
        cv2.line(g, (xx, 0), (xx, H), (255, 255, 255), 1)
    cv2.putText(g, "0.6h side clearance", (int(ex - 0.6 * h) + 6, H - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.imwrite(os.path.join(a.out, f"{name}_guides.png"), g)
    print(f"-> {a.out}")

if __name__ == "__main__":
    main()
