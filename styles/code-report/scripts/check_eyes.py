"""check_eyes.py: prove from the pixels that a finished video never shows the presenter while the eyes are off the lens.

  python check_eyes.py OUTPUT.mp4 GAZE.json LOOKAWAYS.json [CUT.mp4]

The render's own check trusts the shot plan; this one does not. It finds a face in every frame of the
output (MediaPipe face landmarker, whatever size the face is: full frame, card, inset) and, wherever a face
is on screen, asks the gaze measured on the cut (gaze.py --out GAZE.json, same edit times) whether the eyes
were off the lens then: inside a listed look-away, or a frame plainly on another gaze target.

Given the cut (CUT.mp4), it also checks WHOSE face it is: a styles with memes and photos puts other people's
faces on screen (Drake, Disaster Girl, Roll Safe), which are not the presenter. Each face found in a look-away
is compared with the presenter's face in the cut at the same frame (normalised correlation of the two face
crops, 64x64 grey); only a match (over 0.5) counts. The presenter's face in a render is that same frame,
scaled and cropped, so it matches at 0.8 or more; another person's face scores near 0.

Prints the offending times and exits 1 if there are any. Run it on every render before it goes to anyone.
"""
import sys, os, json, cv2, numpy as np
MODEL = os.environ.get("FACE_LANDMARKER", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "editing", "scripts", "face_landmarker.task"))
MATCH = 0.5

def main(video, gaze, lookaways, cut=None, step=1):
    import mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    mk = lambda: vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=MODEL), running_mode=vision.RunningMode.VIDEO, num_faces=3))
    det = mk(); dets = [mk() for _ in range(4)]; det_cut = mk()
    look = json.load(open(lookaways)); frames = json.load(open(gaze))["frames"]
    def off(t):
        if any(x["edit_start"] <= t < x["edit_end"] for x in look): return True
        r = min(frames, key=lambda r: abs(r["t"] - t))
        return bool(r.get("off")) and ((r.get("p_lens") is not None and r["p_lens"] < 0.1) or (r.get("dist") or 0) > 4.5)
    def faces(detector, rgb, ms, x0=0, y0=0, sx=1.0, sy=1.0):
        out = []
        for lm in detector.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb)), ms).face_landmarks:
            xs = [p.x for p in lm]; ys = [p.y for p in lm]; h, w = rgb.shape[:2]
            out.append((x0 + min(xs) * w * sx, y0 + min(ys) * h * sy, x0 + max(xs) * w * sx, y0 + max(ys) * h * sy))
        return out
    def crop(img, box):
        x0, y0, x1, y1 = [int(round(v)) for v in box]; x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(img.shape[1], x1), min(img.shape[0], y1)
        if x1 - x0 < 8 or y1 - y0 < 8: return None
        g = cv2.cvtColor(cv2.resize(img[y0:y1, x0:x1], (64, 64)), cv2.COLOR_RGB2GRAY).astype(np.float32); g -= g.mean(); n = np.linalg.norm(g); return g / n if n > 0 else None
    c = cv2.VideoCapture(video); cc = cv2.VideoCapture(cut) if cut else None; fps = c.get(cv2.CAP_PROP_FPS) or 30; i = shown = others = 0; bad = []
    while c.grab():
        cut_rgb = None
        if cc is not None:
            okc, fc = cc.read(); cut_rgb = cv2.cvtColor(fc, cv2.COLOR_BGR2RGB) if okc else None
        if i % step == 0:
            t = i / fps; ms = int(t * 1000); _, f = c.retrieve(); rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB); h, w = rgb.shape[:2]
            boxes = faces(det, rgb, ms)
            if not boxes:                                                     # a small face window: look again in each quarter at 2x
                for k, (y0, x0) in enumerate(((0, 0), (0, w // 2), (h // 2, 0), (h // 2, w // 2))):
                    q = cv2.resize(rgb[y0:y0 + h // 2, x0:x0 + w // 2], (w, h)); boxes = faces(dets[k], q, ms, x0, y0, 0.5, 0.5)
                    if boxes: break
            if boxes:
                shown += 1
                if off(t):
                    if cut_rgb is None: bad.append(round(t, 2))
                    else:                                                     # is it the presenter, or a face in a meme or photo?
                        ref = [crop(cut_rgb, b) for b in faces(det_cut, cut_rgb, ms)]; ref = [r for r in ref if r is not None]
                        sims = [float((crop(rgb, b) * r).sum()) for b in boxes for r in ref if crop(rgb, b) is not None]
                        if not ref or (sims and max(sims) > MATCH): bad.append(round(t, 2))
                        else: others += 1
        i += 1
    print(f"{video}: {i // step} frames checked, a face on screen in {shown}" + (f", other people's faces (memes, photos) during look-aways: {others}" if cut else "") +
          f", the presenter's face on screen while the eyes are off the lens: {len(bad)}")
    if bad: print("  at", bad[:80])
    return 1 if bad else 0

if __name__ == "__main__":
    if len(sys.argv) < 4: print(__doc__); sys.exit(2)
    sys.exit(main(*sys.argv[1:5]))
