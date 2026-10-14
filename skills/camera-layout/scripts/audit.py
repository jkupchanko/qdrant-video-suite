#!/usr/bin/env python
"""audit.py: measure how a video uses the presenter's camera over time.

  python audit.py VIDEO.mp4 [--step 1.0] [--out report.json]
  python audit.py --dir videos/ --out audit/            (one json per video + summary.csv)

Per sampled second it records the camera layout:
  full    the presenter fills the frame (talking head)
  half    presenter in a split next to content (face off-centre, about a third to a half of the frame)
  inset   a large picture-in-picture window (round or square, roughly a fifth to a quarter of the width)
  small   a small picture-in-picture window
  none    no face: screen, code, slides, B-roll

plus where the small window sits (corner), and a rough content class for the rest of the frame
(dark-editor / light-page / other). Face detection is OpenCV's frontal + profile Haar cascades; a
layout is kept only when it holds for 2 consecutive samples, which removes blinks and turns.
"""
import argparse, csv, json, os, subprocess, sys
import cv2, numpy as np

def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def frames(path, step):
    """yield (t, frame) every `step` seconds at 640 px wide"""
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    every = max(1, int(round(fps * step)))
    i = 0
    while True:
        ok = cap.grab()
        if not ok: break
        if i % every == 0:
            ok, f = cap.retrieve()
            if not ok: break
            h, w = f.shape[:2]
            if w != 640: f = cv2.resize(f, (640, int(h * 640 / w)))
            yield i / fps, f
        i += 1
    cap.release()

CASC = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
PROF = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")

def faces(gray):
    """face boxes in 640-px frame coordinates. Small corner windows are found on a 2x upscale."""
    out = [tuple(int(v) for v in b) for b in CASC.detectMultiScale(gray, 1.1, 4, minSize=(22, 22))]
    if not out:
        out = [tuple(int(v) for v in b) for b in PROF.detectMultiScale(gray, 1.1, 4, minSize=(22, 22))]
    if not out or max(b[2] for b in out) < 60:
        # small windows live in the corners: search each corner at 2x, which is cheap
        H, W = gray.shape
        for (x0, y0) in ((0, 0), (W - int(W * 0.42), 0), (0, H - int(H * 0.5)), (W - int(W * 0.42), H - int(H * 0.5))):
            crop = gray[y0:y0 + int(H * 0.5), x0:x0 + int(W * 0.42)]
            big = cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
            for b in CASC.detectMultiScale(big, 1.12, 4, minSize=(20, 20), maxSize=(90, 90)):
                x, y, w, h = (int(v / 2) for v in b); x += x0; y += y0
                if not any(abs(x - o[0]) < o[2] and abs(y - o[1]) < o[3] for o in out): out.append((x, y, w, h))
    return out

LAYOUTS = ("full", "half", "inset", "small", "none")

def classify(f):
    """full: talking head. half: presenter in a split next to content. inset: a large PiP (round or square).
    small: a small PiP. none: no presenter on screen."""
    h, w = f.shape[:2]
    gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
    fs = faces(gray)
    if not fs:
        return "none", None, content_class(f, None)
    x, y, fw, fh = max(fs, key=lambda b: b[2] * b[3])
    rel = fw / w                      # face width as a share of the frame width
    cx, cy = (x + fw / 2) / w, (y + fh / 2) / h
    body_h, body_w, to_bottom = body_blob(f, (x, y, fw, fh))
    if rel < 0.065 and not (0.12 < body_w < 0.6): body_h = 0.0   # a tiny face whose "body" spans the frame is a flood-fill leak, not a wide shot
    tall = body_h >= 0.5                        # the presenter's body runs most of the frame height: a wide shot or a full-height panel
    off_centre = cx < 0.36 or cx > 0.64
    if tall: layout = "half" if (off_centre and body_w < 0.55) else "full"
    elif rel >= 0.16: layout = "full"
    elif rel >= 0.065: layout = "inset"
    else: layout = "small"
    corner = None
    if layout in ("small", "inset", "half"):
        corner = ("bottom" if cy > 0.5 else "top") + "-" + ("right" if cx > 0.5 else "left")
    return layout, corner, content_class(f, (x, y, fw, fh))

def body_blob(f, face):
    """flood-fill the shirt just below the face; returns (blob height / H measured from the face top,
    blob width / W, reaches the bottom edge). A picture-in-picture clips the body at its border; a wide shot
    or a full-height panel lets it run to the bottom of the frame."""
    H, W = f.shape[:2]; x, y, fw, fh = face
    sx, sy = int(x + fw / 2), int(min(H - 2, y + fh * 1.7))
    blur = cv2.GaussianBlur(f, (7, 7), 0)
    mask = np.zeros((H + 2, W + 2), np.uint8)
    try:
        cv2.floodFill(blur, mask, (sx, sy), 255, (14, 14, 14), (14, 14, 14), 4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8))
    except cv2.error:
        return 0.0, 0.0, False
    m = mask[1:-1, 1:-1] > 0
    ys, xs = np.where(m)
    if len(ys) < 50: return 0.0, 0.0, False
    bottom = int(ys.max()); width = (xs.max() - xs.min()) / W
    return (bottom - y) / H, width, bottom >= H - 4

def window_extent(gray, face):
    """(top, bottom) rows of the window or body that contains the face: the nearest strong horizontal border
    above and below the face in the face's column; frame edges when there is none."""
    H, W = gray.shape; x, y, fw, fh = face
    # a window border is a straight line across a band wider than the face; clothes and hair are not
    x0, x1 = max(0, x - fw), min(W, x + 2 * fw)
    band = gray[:, x0:x1].astype(np.int16)
    line = (np.abs(np.diff(band, axis=0)) > 20).mean(axis=1)      # share of the band's pixels that jump on this row
    top = 0
    for r in range(y - 1, max(0, y - int(2.5 * fh)), -1):
        if line[r] > 0.6: top = r; break
    bot = H
    for r in range(min(H - 2, y + fh), H - 3):
        if line[r] > 0.6: bot = r; break
    return top, bot

def reaches_bottom(gray, face):
    """True when the column under the face continues to the bottom of the frame without a horizontal border line
    (a picture-in-picture window ends in a border or a margin; a person in a wide shot runs off the frame)."""
    H, W = gray.shape; x, y, fw, fh = face
    x0, x1 = max(0, x), min(W, x + fw)
    col = gray[min(H - 2, y + fh):H - 2, x0:x1].astype(np.int16)
    if col.shape[0] < 6: return True
    dy = np.abs(np.diff(col, axis=0)).mean(axis=1)          # per-row vertical gradient
    strong = dy > max(18, 4 * np.median(dy))
    return not strong.any()

def content_class(f, face):
    """what the rest of the frame looks like: dark-editor / light-page / other"""
    h, w = f.shape[:2]
    m = np.ones((h, w), bool)
    if face:
        x, y, fw, fh = face
        m[max(0, y - fh):min(h, y + 3 * fh), max(0, x - fw):min(w, x + 2 * fw)] = False   # ignore head + shoulders
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)[m]
    if g.size < 100: return "other"
    lum = float(g.mean()); edges = float((cv2.Canny(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), 80, 160)[m] > 0).mean())
    if lum < 70 and edges > 0.03: return "dark-editor"
    if lum > 140 and edges > 0.02: return "light-page"
    return "other"

def persist(layouts, corners, gap=20):
    """a corner window that drops out for a few samples is still there: carry small/inset across gaps <= `gap`"""
    out = list(layouts); last = None; since = 0
    for i, (l, c) in enumerate(zip(layouts, corners)):
        if l in ("small", "inset"): last, since = (l, c), 0
        elif l == "none" and last and since < gap:
            out[i] = last[0]; corners[i] = last[1]; since += 1
        else:
            since += 1
            if l in ("full", "half"): last = None
    return out

def smooth(seq, hold=2):
    """keep a layout only when it persists `hold` samples; otherwise carry the previous one"""
    out, cur, run = [], None, 0
    for i, s in enumerate(seq):
        if cur is None: cur = s
        if s == cur: run += 1
        else:
            ahead = seq[i:i + hold]
            if len(ahead) == hold and all(a == s for a in ahead): cur, run = s, 1
        out.append(cur)
    return out

def segments(times, layouts):
    segs = []
    for t, l in zip(times, layouts):
        if segs and segs[-1]["layout"] == l: segs[-1]["end"] = t
        else: segs.append({"layout": l, "start": t, "end": t})
    return segs

def audit(path, step=1.0):
    times, raw, corners, contents = [], [], [], []
    for t, f in frames(path, step):
        l, c, k = classify(f)
        times.append(round(t, 1)); raw.append(l); corners.append(c); contents.append(k)
    if not times: raise SystemExit(f"no frames read from {path}")
    lay = smooth(persist(raw, corners))
    segs = segments(times, lay)
    dur = times[-1] + step
    share = {k: round(sum(1 for l in lay if l == k) * step / dur, 3) for k in LAYOUTS}
    switches = len(segs) - 1
    corner_counts = {}
    for l, c in zip(lay, corners):
        if l in ("small", "inset") and c: corner_counts[c] = corner_counts.get(c, 0) + 1
    main_corner = max(corner_counts, key=corner_counts.get) if corner_counts else None
    # what the face sits over, when it is small
    over = {}
    for l, k in zip(lay, contents):
        if l in ("small", "inset"): over[k] = over.get(k, 0) + 1
    # where in the timeline the switches happen (thirds)
    thirds = [0, 0, 0]
    for s in segs[1:]:
        thirds[min(2, int(3 * s["start"] / dur))] += 1
    seg_len = {k: round(float(np.mean([s["end"] - s["start"] + step for s in segs if s["layout"] == k])), 1) for k in LAYOUTS if any(s["layout"] == k for s in segs)}
    first = segs[0]["layout"]; last = segs[-1]["layout"]
    transitions = {}
    for a, b in zip(segs, segs[1:]):
        key = f"{a['layout']}->{b['layout']}"; transitions[key] = transitions.get(key, 0) + 1
    return {"file": os.path.basename(path), "duration": round(dur, 1), "step": step, "share": share, "switches": switches,
            "switches_per_min": round(switches / (dur / 60), 2), "avg_segment_s": seg_len, "opens_with": first, "closes_with": last,
            "small_corner": main_corner, "small_over": over, "switches_by_third": thirds, "transitions": transitions,
            "segments": [{**s, "end": round(s["end"] + step, 1)} for s in segs]}

def sheet(path, out, every=10.0, cols=8):
    """contact sheet with the detected layout written on each frame, for checking the classifier by eye"""
    tiles = []
    for t, f in frames(path, every):
        l, c, k = classify(f)
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        for (x, y, w, h) in faces(g): cv2.rectangle(f, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.putText(f, f"{int(t)}s {l} {c or ''} {k}", (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
        tiles.append(cv2.resize(f, (320, 180)))
    rows = [np.hstack(tiles[i:i + cols] + [np.zeros((180, 320, 3), np.uint8)] * (cols - len(tiles[i:i + cols]))) for i in range(0, len(tiles), cols)]
    cv2.imwrite(out, np.vstack(rows)); print(f"sheet -> {out}")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", nargs="?"); ap.add_argument("--dir"); ap.add_argument("--step", type=float, default=1.0); ap.add_argument("--out")
    ap.add_argument("--sheet", help="write a labelled contact sheet (png) instead of a report")
    a = ap.parse_args()
    if a.sheet: sheet(a.video, a.sheet); return
    if a.dir:
        os.makedirs(a.out or "audit", exist_ok=True); rows = []
        for fn in sorted(os.listdir(a.dir)):
            if not fn.lower().endswith((".mp4", ".webm", ".mkv", ".mov")): continue
            try: r = audit(os.path.join(a.dir, fn), a.step)
            except Exception as e: print(f"  {fn}: FAILED {e}", file=sys.stderr); continue
            json.dump(r, open(os.path.join(a.out or "audit", os.path.splitext(fn)[0] + ".json"), "w"), indent=1)
            rows.append(r); print(f"  {fn[:24]:24s} {r['duration']:6.0f}s  full {r['share']['full']:.2f} half {r['share']['half']:.2f} inset {r['share']['inset']:.2f} small {r['share']['small']:.2f} none {r['share']['none']:.2f}  sw/min {r['switches_per_min']:.1f}  corner {r['small_corner']}")
        with open(os.path.join(a.out or "audit", "summary.csv"), "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["file", "duration", "full", "half", "inset", "small", "none", "switches", "switches_per_min", "opens_with", "closes_with", "corner", "avg_full", "avg_half", "avg_inset", "avg_small", "avg_none", "sw_third1", "sw_third2", "sw_third3"])
            for r in rows:
                w.writerow([r["file"], r["duration"], *(r["share"][k] for k in LAYOUTS), r["switches"], r["switches_per_min"], r["opens_with"], r["closes_with"], r["small_corner"],
                            *(r["avg_segment_s"].get(k, "") for k in LAYOUTS), *r["switches_by_third"]])
        print(f"summary -> {os.path.join(a.out or 'audit', 'summary.csv')}")
    else:
        r = audit(a.video, a.step)
        if a.out: json.dump(r, open(a.out, "w"), indent=1)
        print(json.dumps({k: v for k, v in r.items() if k != "segments"}, indent=1))

if __name__ == "__main__":
    main()
