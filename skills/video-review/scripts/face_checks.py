"""Face pass: every face on screen, whose it is, and how it is shown.

For each sampled frame of the output it finds the faces (MediaPipe face landmarker; when none is found
full frame, again in each quarter at 2x, so a small corner window is not missed), and, given the cut, decides
which one is the presenter: the presenter on screen is the cut's own frame scaled and cropped, so their face
crop correlates with the cut's face at the same frame (64x64 grey, over MATCH); a meme or photo face does not.
For the presenter it then fits the map from the cut's landmarks to the output's (a full affine) and reads off:

  aspect   the two axis scales of that map: equal unless the face was stretched (the 2.05:1-into-16:9 bug)
  window   the region where the output still equals the warped cut frame: the face window's rectangle
  head     the cut's whole-head box (landmarks widened to hair and chin) mapped into the output: the share of
           it that the window does not show is how much of the head is cut off
  sync     the cut frame (within +-4) whose face crop best matches: 0 when the face is one-to-one with the voice

Returns one record per sample; review.py turns them into findings.
"""
import os, cv2, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("FACE_LANDMARKER", os.path.normpath(os.path.join(HERE, "..", "..", "editing", "scripts", "face_landmarker.task")))
MATCH = 0.5

def _crop64(img, box):
    x0, y0, x1, y1 = [int(round(v)) for v in box]; x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(img.shape[1], x1), min(img.shape[0], y1)
    if x1 - x0 < 8 or y1 - y0 < 8: return None
    g = cv2.cvtColor(cv2.resize(img[y0:y1, x0:x1], (64, 64)), cv2.COLOR_RGB2GRAY).astype(np.float32); g -= g.mean(); n = np.linalg.norm(g)
    return g / n if n > 0 else None

class Faces:
    def __init__(self):
        import mediapipe as mp
        from mediapipe.tasks.python import vision, BaseOptions
        self.mp = mp
        mk = lambda: vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=MODEL), running_mode=vision.RunningMode.VIDEO, num_faces=3))
        self.full, self.quarters, self.cut = mk(), [mk() for _ in range(4)], mk()
    def _run(self, det, rgb, ms, x0=0, y0=0, s=1.0):
        out = []; h, w = rgb.shape[:2]
        for lm in det.detect_for_video(self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb)), ms).face_landmarks:
            pts = np.array([[x0 + p.x * w * s, y0 + p.y * h * s] for p in lm], np.float32)
            out.append(pts)
        return out
    def find(self, rgb, ms):
        f = self._run(self.full, rgb, ms)
        if f: return f
        h, w = rgb.shape[:2]
        for k, (y0, x0) in enumerate(((0, 0), (0, w // 2), (h // 2, 0), (h // 2, w // 2))):
            q = cv2.resize(rgb[y0:y0 + h // 2, x0:x0 + w // 2], (w, h)); f = self._run(self.quarters[k], q, ms, x0, y0, 0.5)
            if f: return f
        return []
    def find_cut(self, rgb, ms): return self._run(self.cut, rgb, ms)

def picture_area(rgb, thr=12):
    """the cut's picture inside any black bars: (x0, y0, x1, y1)"""
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY); rows = np.where(g.max(axis=1) > thr)[0]; cols = np.where(g.max(axis=0) > thr)[0]
    if not len(rows) or not len(cols): return (0, 0, rgb.shape[1], rgb.shape[0])
    return (int(cols[0]), int(rows[0]), int(cols[-1] + 1), int(rows[-1] + 1))

def box_of(pts): return (float(pts[:, 0].min()), float(pts[:, 1].min()), float(pts[:, 0].max()), float(pts[:, 1].max()))

def head_box(pts):
    """the whole head from the face landmarks: the mesh stops at the hairline and the chin; hair adds ~45% of the face height above"""
    x0, y0, x1, y1 = box_of(pts); fw, fh = x1 - x0, y1 - y0
    return np.array([[x0 - 0.12 * fw, y0 - 0.45 * fh], [x1 + 0.12 * fw, y0 - 0.45 * fh], [x1 + 0.12 * fw, y1 + 0.06 * fh], [x0 - 0.12 * fw, y1 + 0.06 * fh]], np.float32)

def ecc_aspect(out_rgb, cut_rgb, A, box):
    """the output's face region aligned to the cut by ECC (an affine, started from the landmark fit): its true x/y scale ratio"""
    x0, y0, x1, y1 = [int(v) for v in box]; mx, my = (x1 - x0) // 5, (y1 - y0) // 5; H, W = out_rgb.shape[:2]
    x0, y0, x1, y1 = max(0, x0 - mx), max(0, y0 - my), min(W, x1 + mx), min(H, y1 + my)
    if x1 - x0 < 40 or y1 - y0 < 40: return None
    tpl = cv2.cvtColor(out_rgb[y0:y1, x0:x1], cv2.COLOR_RGB2GRAY).astype(np.float32); inp = cv2.cvtColor(cut_rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    Wm = cv2.invertAffineTransform(A).astype(np.float32); Wm[:, 2] += Wm[:, :2] @ np.array([x0, y0], np.float32)   # crop coords -> cut coords
    try: _, Wm = cv2.findTransformECC(tpl, inp, Wm, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 80, 1e-5), None, 5)
    except cv2.error: return None
    B = cv2.invertAffineTransform(Wm); return round(float(np.hypot(B[0, 0], B[1, 0]) / np.hypot(B[0, 1], B[1, 1])), 3)

def refine(out_rgb, cut_rgb, A, box, margin=0.3):
    """the landmark fit sharpened by ECC over the face and its surround: sub-pixel near the face, and the scale right, so the map
    still holds at the window's edges (a 1% scale error is 3 px there, and against a sharp painting that reads as 'not the cut')"""
    x0, y0, x1, y1 = [int(v) for v in box]; mx, my = int((x1 - x0) * margin), int((y1 - y0) * margin); H, W = out_rgb.shape[:2]
    x0, y0, x1, y1 = max(0, x0 - mx), max(0, y0 - my), min(W, x1 + mx), min(H, y1 + my)
    if x1 - x0 < 40 or y1 - y0 < 40: return A
    hs = 0.5 if (x1 - x0) > 200 else 1.0
    tpl = cv2.resize(cv2.cvtColor(out_rgb[y0:y1, x0:x1], cv2.COLOR_RGB2GRAY), None, fx=hs, fy=hs, interpolation=cv2.INTER_AREA).astype(np.float32)
    inp = cv2.resize(cv2.cvtColor(cut_rgb, cv2.COLOR_RGB2GRAY), None, fx=hs, fy=hs, interpolation=cv2.INTER_AREA).astype(np.float32)
    Wm = cv2.invertAffineTransform(A).astype(np.float32); Wm[:, 2] += Wm[:, :2] @ np.array([x0, y0], np.float32); Wm[:, 2] *= hs
    try: _, Wm = cv2.findTransformECC(tpl, inp, Wm, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 60, 1e-6), None, 3)
    except cv2.error: return A
    Wm[:, 2] /= hs; Wm[:, 2] -= Wm[:, :2] @ np.array([x0, y0], np.float32); return cv2.invertAffineTransform(Wm)

def analyse(out_rgb, cut_rgb, out_faces, cut_faces, cut_ring=None, cut_safe=None):
    """-> dict(presenter=bool, faces=n, box, aspect, window, head_cut, head_cut_side, sync_off, face_h) for the presenter, if on screen"""
    rec = dict(faces=len(out_faces), presenter=False)
    if not out_faces or cut_rgb is None or not cut_faces: return rec
    refs = [(c, _crop64(cut_rgb, box_of(c))) for c in cut_faces]; best = (-1, None, None)
    for o in out_faces:
        oc = _crop64(out_rgb, box_of(o))
        if oc is None: continue
        for c, rc in refs:
            if rc is None: continue
            s = float((oc * rc).sum())
            if s > best[0]: best = (s, o, c)
    rec["match"] = round(best[0], 3)
    if best[0] < MATCH: return rec
    o, c = best[1], best[2]; rec.update(presenter=True, box=[round(v) for v in box_of(o)], face_h=round(box_of(o)[3] - box_of(o)[1]))
    A, _ = cv2.estimateAffine2D(c, o, ransacReprojThreshold=4.0)
    if A is None: return rec
    H, W = out_rgb.shape[:2]
    sx0_, sy0_ = float(np.hypot(A[0, 0], A[1, 0])), float(np.hypot(A[0, 1], A[1, 1])); rec["aspect_landmarks"] = round(sx0_ / sy0_, 3)
    Ar = refine(out_rgb, cut_rgb, A, box_of(o))                                  # landmarks on a small face jitter a few percent
    ar = float(np.hypot(Ar[0, 0], Ar[1, 0]) / np.hypot(Ar[0, 1], Ar[1, 1]))
    if abs(ar - rec["aspect_landmarks"]) < 0.05: A = Ar                           # a diverged ECC (off the landmarks by 5%+) is not trusted
    sx, sy = float(np.hypot(A[0, 0], A[1, 0])), float(np.hypot(A[0, 1], A[1, 1])); rec["aspect"] = round(sx / sy, 3); rec["scale"] = round((sx + sy) / 2, 3)
    ref = cut_rgb
    if cut_ring:
        # lip sync first: which nearby cut frame is the one on screen? Each candidate is aligned to the output's face area on its
        # own (ECC, an affine from the landmark fit), so head motion is taken out of it; the frame really on screen then matches to
        # the pixel (correlation ~0.99+) and the others keep their mouth and eye differences. A fit from the same-numbered frame
        # alone would always pick that frame. (Finding the window first fails on a desync too: the window is where they are equal.)
        x0, y0, x1, y1 = [int(v) for v in box_of(o)]; mx, my = (x1 - x0) // 4, (y1 - y0) // 4
        x0, y0, x1, y1 = max(0, x0 - mx), max(0, y0 - my), min(W, x1 + mx), min(H, y1 + my)
        if x1 - x0 > 24 and y1 - y0 > 24:
            hs = 0.5 if (x1 - x0) > 160 else 1.0                                       # big faces at half size: 4x faster, as exact
            tpl = cv2.resize(cv2.cvtColor(out_rgb[y0:y1, x0:x1], cv2.COLOR_RGB2GRAY), None, fx=hs, fy=hs, interpolation=cv2.INTER_AREA).astype(np.float32)
            W0 = cv2.invertAffineTransform(A).astype(np.float32); W0[:, 2] += W0[:, :2] @ np.array([x0, y0], np.float32)
            Wh = np.hstack([W0[:, :2], W0[:, 2:] * hs])                                  # template px (scaled) -> cut px (scaled): same linear part
            sc = []
            for off, fr in cut_ring:
                inp = cv2.resize(cv2.cvtColor(fr, cv2.COLOR_RGB2GRAY), None, fx=hs, fy=hs, interpolation=cv2.INTER_AREA).astype(np.float32)
                try: cc, Wk = cv2.findTransformECC(tpl, inp, Wh.copy(), cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 1e-5), None, 3)
                except cv2.error: continue
                Wk = np.hstack([Wk[:, :2], Wk[:, 2:] / hs]).astype(np.float32)           # back to full-size px
                sc.append((float(cc), off, fr, Wk))
            if len(sc) >= 5:
                sc.sort(key=lambda z: -z[0]); rec["sync_cc"] = [round(z[0], 4) for z in sc[:3]]
                e1, e2 = 1 - sc[0][0], 1 - sc[1][0]; rec["sync_best"] = sc[0][1]
                # the frame on screen leaves almost nothing unexplained, its neighbours several times more; a still face leaves every
                # frame equal (no verdict), and an overlay on the face raises every error alike (no verdict either)
                if e1 < 0.005 and e2 > 2.5 * max(e1, 2e-5):
                    rec["sync_off"] = sc[0][1]; rec["sync_ratio"] = round(e2 / max(e1, 2e-5), 1); ref = sc[0][2]
                    Wb = sc[0][3].copy(); Wb[:, 2] -= Wb[:, :2] @ np.array([x0, y0], np.float32); A = cv2.invertAffineTransform(Wb)   # its exact map
    warped = cv2.warpAffine(ref, A, (W, H), flags=cv2.INTER_LINEAR, borderValue=(255, 0, 255))
    # compare blurred: a sub-pixel misfit makes fine texture (hair) differ pixel by pixel and split the window at the hairline;
    # blurred, the cut's own pixels still match and the board around the window (another picture entirely) still does not
    bw, bo = cv2.GaussianBlur(warped, (9, 9), 0), cv2.GaussianBlur(out_rgb, (9, 9), 0)
    diff = np.abs(bw.astype(np.int16) - bo.astype(np.int16)).mean(axis=2).astype(np.float32)
    if cut_safe:                                                                 # outside the cut's picture (its black bars, or past its edge)
        pm = np.zeros(cut_rgb.shape[:2], np.uint8); sx0, sy0, sx1, sy1 = cut_safe; pm[sy0:sy1, sx0:sx1] = 1   # nothing can be the window
        diff[cv2.warpAffine(pm, A, (W, H), flags=cv2.INTER_NEAREST) == 0] = 255
    # the window's edges: walk out from the face along rows and columns while the output is still the cut. Judged by the size of the
    # difference, not a pixel count: a 2-3 px misfit of the hairline makes a whole row "differ" a little, while past the window's
    # edge the output is another picture (the board) and differs a lot
    bx0, by0, bx1, by1 = box_of(o); fxc, fyc = int((bx0 + bx1) / 2), int((by0 + by1) / 2); hw, hh = int((bx1 - bx0) * 0.4), int((by1 - by0) * 0.4)
    fyc, fxc = min(max(fyc, 0), H - 1), min(max(fxc, 0), W - 1)
    rows = diff[:, max(0, fxc - hw):min(W, fxc + hw)].mean(axis=1); cols = diff[max(0, fyc - hh):min(H, fyc + hh), :].mean(axis=0)
    def edge(prof, start, step):
        k, miss = start, 0
        while 0 <= k + step < len(prof):
            k += step; miss = miss + 1 if prof[k] > 45 else 0
            if miss >= 4: return k - 4 * step
        return k
    if rows[fyc] <= 45:
        top, bot = edge(rows, fyc, -1), edge(rows, fyc, 1); left, right = edge(cols, fxc, -1), edge(cols, fxc, 1)
        x, y, w, h = int(left), int(top), int(right - left + 1), int(bot - top + 1); rec["window"] = [x, y, w, h]
        hb0 = head_box(c)
        if cut_safe:                                                             # only what the camera framed: the cut's picture inside its bars
            sx0, sy0, sx1, sy1 = cut_safe; hb0[:, 0] = np.clip(hb0[:, 0], sx0, sx1); hb0[:, 1] = np.clip(hb0[:, 1], sy0, sy1)
        hb = cv2.transform(hb0[None], A)[0]; hx0, hy0 = hb[:, 0].min(), hb[:, 1].min(); hx1, hy1 = hb[:, 0].max(), hb[:, 1].max()
        inter_w = max(0.0, min(hx1, x + w) - max(hx0, x)); inter_h = max(0.0, min(hy1, y + h) - max(hy0, y))
        shown = (inter_w * inter_h) / max(1.0, (hx1 - hx0) * (hy1 - hy0)); rec["head_cut"] = round(1 - shown, 3)
        sides = []
        if hy0 < y - 2: sides.append(f"top {int(y - hy0)} px")
        if hy1 > y + h + 2: sides.append(f"bottom {int(hy1 - y - h)} px")
        if hx0 < x - 2: sides.append(f"left {int(x - hx0)} px")
        if hx1 > x + w + 2: sides.append(f"right {int(hx1 - x - w)} px")
        rec["head_cut_side"] = ", ".join(sides); rec["head_box"] = [int(hx0), int(hy0), int(hx1), int(hy1)]
        rec["overlay"] = w >= 0.9 * W and (y > 2 or y + h < H - 2)               # full width but stopped short: a caption over the face, not a window
    return rec
