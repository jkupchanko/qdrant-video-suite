#!/usr/bin/env python
"""audit_transitions.py: find every shot change in a video and say what kind of transition it is.

  python audit_transitions.py VIDEO.mp4 [--out report.json] [--layout audit.json]
  python audit_transitions.py --dir videos/ --out transitions/ [--layouts audit/]

Reads frames at 320 px wide, measures how much each frame differs from the one before, and finds the
boundaries. Each boundary is classified by what the frames around it do:
  cut        one frame to the next, no in-between
  punch-in   a cut where the new frame is the old one scaled up (same shot, tighter): the creator jump-zoom
  punch-out  the reverse
  dissolve   in-between frames are a blend of the shot before and the shot after
  fade-black / fade-white   in-between frames pass through black or white
  slide      the content moves across the frame over a few frames (push, slide-in, wipe: one side old, the other new)
  zoom       the content scales over a few frames (a push-in or pull-out as a move, not a cut)
  element-in / element-anim   a label, card or caption appears over a shot that stays (less than 35% of the frame changes); not a shot change
  other      a whole-frame change that is none of the above (an animated wipe, a 3D flip, a glitch)
With --layout (the camera audit's json) each boundary also gets its context: face->screen, screen->face,
screen->screen, face->face. The report has the list and the counts.
"""
import argparse, csv, json, os, sys
import cv2, numpy as np

SW, SH = 320, 180

def stream_diffs(path):
    """pass 1: frame-to-frame difference for the whole video without keeping the frames (long videos do not fit in memory)"""
    cap = cv2.VideoCapture(path); fps = cap.get(cv2.CAP_PROP_FPS) or 30
    prev = None; d = [0.0]; n = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        g = cv2.resize(f, (SW, SH), interpolation=cv2.INTER_AREA).astype(np.int16)
        if prev is not None: d.append(float(np.abs(g - prev).mean()))
        prev = g; n += 1
    cap.release()
    return np.array(d[:n]), fps, n

def frames_around(path, i_from, i_to):
    """pass 2: the small frames i_from..i_to (inclusive) by seeking once"""
    cap = cv2.VideoCapture(path); cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, i_from)); out = []
    for _ in range(i_to - max(0, i_from) + 1):
        ok, f = cap.read()
        if not ok: break
        out.append(cv2.resize(f, (SW, SH), interpolation=cv2.INTER_AREA))
    cap.release()
    return out

def is_scaled(a, b, scales=(1.05, 1.1, 1.15, 1.2, 1.3, 1.4)):
    """is b the centre of a scaled up (punch-in) or a the centre of b (punch-out)? returns +scale, -scale or 0"""
    ga = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32); gb = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float32)
    def corr(x, y):
        x = x - x.mean(); y = y - y.mean(); n = np.sqrt((x * x).sum() * (y * y).sum()); return float((x * y).sum() / n) if n else 0.0
    base = corr(ga, gb)
    best, bs = base, 0
    for s in scales:
        w, h = int(SW / s), int(SH / s); x0, y0 = (SW - w) // 2, (SH - h) // 2
        za = cv2.resize(ga[y0:y0 + h, x0:x0 + w], (SW, SH)); c = corr(za, gb)
        if c > best: best, bs = c, s
        zb = cv2.resize(gb[y0:y0 + h, x0:x0 + w], (SW, SH)); c2 = corr(ga, zb)
        if c2 > best: best, bs = c2, -s
    return bs if (best > 0.8 and best > base + 0.15) else 0, best, base

def blend_fit(a, b, mids):
    """how well the in-between frames are explained as blends of a and b (dissolve)"""
    A = a.astype(np.float32); B = b.astype(np.float32); errs = []
    for m in mids:
        M = m.astype(np.float32)
        t = float(np.clip(((M - A) * (B - A)).sum() / max(1e-6, ((B - A) ** 2).sum()), 0, 1))
        errs.append(np.abs(M - (A + t * (B - A))).mean())
    return float(np.mean(errs)) if errs else 99.0

def shift(a, b):
    ga = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32); gb = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float32)
    (dx, dy), resp = cv2.phaseCorrelate(ga, gb)
    return float(np.hypot(dx, dy)), float(resp)

def coverage(a, b):
    """share of the frame that actually changed between a and b (an element popping in changes a corner; a shot change changes everything)"""
    d = np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=2)
    return float((d > 28).mean())

def wipe_test(a, b, m):
    """is the mid frame old on one side and new on the other (a slide-in, push or wipe)? returns axis or None"""
    A = a.astype(np.int16); B = b.astype(np.int16); M = m.astype(np.int16)
    for axis in ("x", "y"):
        da = np.abs(M - A).mean(axis=(0, 2) if axis == "x" else (1, 2)); db = np.abs(M - B).mean(axis=(0, 2) if axis == "x" else (1, 2))
        n = len(da); best = None
        for c in range(n // 6, n - n // 6):
            left_old = da[:c].mean() < 14 and db[c:].mean() < 14
            left_new = db[:c].mean() < 14 and da[c:].mean() < 14
            if left_old or left_new: best = c; break
        if best is not None: return axis
    return None

def classify(frames, i0, i1, fps):
    """boundary spanning frames i0..i1 (inclusive of the changed frames). a = frame before, b = frame after."""
    a = frames[0]; b = frames[-1]
    span = i1 - i0 + 1; mids = list(frames[i0:i1 + 1])
    cov = coverage(a, b)
    if cov < 0.35:
        return ("element-in" if span <= 2 else "element-anim"), span     # a label, card or caption appears over a shot that stays
    lum = [float(cv2.cvtColor(m, cv2.COLOR_BGR2GRAY).mean()) for m in mids]
    if span >= 3 and min(lum) < 18: return "fade-black", span
    if span >= 3 and max(lum) > 238: return "fade-white", span
    if span <= 2:
        s, best, base = is_scaled(a, b)
        if s > 0: return "punch-in", span
        if s < 0: return "punch-out", span
        return "cut", span
    bf = blend_fit(a, b, mids)
    if bf < 9: return "dissolve", span
    sh, resp = shift(a, mids[len(mids) // 2])
    if sh > 25 and resp > 0.08: return "slide", span
    if any(wipe_test(a, b, m) for m in mids[max(0, len(mids) // 2 - 1):len(mids) // 2 + 2]): return "slide", span
    s, best, base = is_scaled(a, b, scales=(1.1, 1.2, 1.3, 1.5, 1.7, 2.0))
    if s != 0: return "zoom", span
    return "other", span

def boundaries(d, fps):
    """runs of frames whose diff is well above the local baseline"""
    med = float(np.median(d)); thr = max(6.0, med * 4 + 4)
    hot = d > thr
    out = []; i = 0; n = len(d)
    while i < n:
        if hot[i]:
            j = i
            while j + 1 < n and (hot[j + 1] or (j + 2 < n and hot[j + 2])): j += 1   # allow one quiet frame inside a run
            out.append((i, j)); i = j + 1
        else: i += 1
    # merge runs separated by less than 4 frames (one transition flickering)
    merged = []
    for s, e in out:
        if merged and s - merged[-1][1] <= 3: merged[-1] = (merged[-1][0], e)
        else: merged.append((s, e))
    return [(s, e) for s, e in merged if (e - s + 1) <= int(fps * 1.5)]   # longer runs are motion/scroll, not transitions

def context(t, layout):
    if not layout: return None
    segs = layout["segments"]
    def at(tt):
        for s in segs:
            if s["start"] <= tt < s["end"]: return "face" if s["layout"] in ("full", "half") else ("window" if s["layout"] in ("small", "inset") else "screen")
        return None
    return f"{at(t - 1.0)}->{at(t + 1.0)}"

def audit(path, layout_path=None):
    d, fps, n = stream_diffs(path)
    bs = boundaries(d, fps)
    layout = json.load(open(layout_path)) if layout_path and os.path.exists(layout_path) else None
    events = []
    for s_, e_ in bs:
        lo = max(0, s_ - 2); win = frames_around(path, lo, min(n - 1, e_ + 2))
        if len(win) < 3: continue
        kind, span = classify(np.array(win), s_ - lo, min(len(win) - 1, e_ - lo), fps)
        t = s_ / fps
        events.append({"t": round(t, 2), "kind": kind, "frames": span, "dur": round(span / fps, 2), "context": context(t, layout)})
    dur = n / fps
    counts = {}
    for ev in events: counts[ev["kind"]] = counts.get(ev["kind"], 0) + 1
    by_ctx = {}
    for ev in events:
        if ev["context"]:
            by_ctx.setdefault(ev["context"], {}); by_ctx[ev["context"]][ev["kind"]] = by_ctx[ev["context"]].get(ev["kind"], 0) + 1
    soft = [ev["dur"] for ev in events if ev["kind"] in ("dissolve", "fade-black", "fade-white", "slide", "zoom")]
    return {"file": os.path.basename(path), "duration": round(dur, 1), "fps": round(fps, 2), "n": len(events), "per_min": round(len(events) / (dur / 60), 2) if dur else 0,
            "counts": counts, "by_context": by_ctx, "soft_median_s": round(float(np.median(soft)), 2) if soft else None, "events": events}

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", nargs="?"); ap.add_argument("--dir"); ap.add_argument("--out"); ap.add_argument("--layout"); ap.add_argument("--layouts")
    a = ap.parse_args()
    if a.dir:
        os.makedirs(a.out or "transitions", exist_ok=True); rows = []
        for fn in sorted(os.listdir(a.dir)):
            if not fn.lower().endswith((".mp4", ".webm", ".mkv", ".mov")): continue
            lp = os.path.join(a.layouts, os.path.splitext(fn)[0] + ".json") if a.layouts else None
            done = os.path.join(a.out or "transitions", os.path.splitext(fn)[0] + ".json")
            if os.path.exists(done):
                r = json.load(open(done)); rows.append(r); print(f"  {fn[:22]:22s} (done)"); continue
            try: r = audit(os.path.join(a.dir, fn), lp)
            except Exception as ex: print(f"  {fn}: FAILED {ex}", file=sys.stderr); continue
            json.dump(r, open(os.path.join(a.out or "transitions", os.path.splitext(fn)[0] + ".json"), "w"), indent=1); rows.append(r)
            c = r["counts"]; print(f"  {fn[:22]:22s} {r['duration']:6.0f}s  {r['n']:4d} changes ({r['per_min']:.1f}/min)  cut {c.get('cut', 0)}  punch {c.get('punch-in', 0) + c.get('punch-out', 0)}  dissolve {c.get('dissolve', 0)}  fade {c.get('fade-black', 0) + c.get('fade-white', 0)}  slide {c.get('slide', 0)}  zoom {c.get('zoom', 0)}  other {c.get('other', 0)}  element {c.get('element-in', 0) + c.get('element-anim', 0)}", flush=True)
        kinds = ["cut", "punch-in", "punch-out", "dissolve", "fade-black", "fade-white", "slide", "zoom", "other", "element-in", "element-anim"]
        with open(os.path.join(a.out or "transitions", "summary.csv"), "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["file", "duration", "n", "per_min", "soft_median_s"] + kinds)
            for r in rows: w.writerow([r["file"], r["duration"], r["n"], r["per_min"], r["soft_median_s"]] + [r["counts"].get(k, 0) for k in kinds])
        print(f"summary -> {os.path.join(a.out or 'transitions', 'summary.csv')}")
    else:
        r = audit(a.video, a.layout)
        if a.out: json.dump(r, open(a.out, "w"), indent=1)
        print(json.dumps({k: v for k, v in r.items() if k != "events"}, indent=1))
        for ev in r["events"][:40]: print(f"  {ev['t']:7.2f}s  {ev['kind']:10s} {ev['frames']:3d} f  {ev['context'] or ''}")

if __name__ == "__main__":
    main()
