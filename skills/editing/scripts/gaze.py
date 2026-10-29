#!/usr/bin/env python
"""gaze.py: where the presenter is looking, frame by frame, from the iris position.

  python gaze.py VIDEO.mp4 --out gaze.json [--fps 10] [--start 0 --end 0]

Uses MediaPipe's face landmarker (478 points, iris included). For each sampled frame it measures:
  h   horizontal iris position inside the eye, 0 = outer corner, 1 = inner, averaged over both eyes
  v   vertical iris position inside the eye opening
  yaw head turn from the nose against the eye corners
  blink  eye opening ratio (a blink is not a look-away)
The presenter's own "on the lens" position is learned from the take itself: the frames fall into clusters
(the lens, a script or screen beside it, notes below it), and the heaviest cluster is the lens. A frame is
OFF when it sits in another cluster or outside the lens cluster (see classify). Stretches of OFF frames
of 0.25 s or more are reported, padded by 0.1 s.

  python gaze.py CUT.mp4 --out gaze.json --lookaways lookaways.json    on a finished cut: edit-time look-aways
  python gaze.py gaze.json --out gaze.json --lookaways lookaways.json  re-classify saved measurements
"""
if __name__ == "__main__":                                   # run on the suite's own Python (.venv, made by setup.py), whichever python started it
    import os as _o, sys as _s, subprocess as _sp
    _v = _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), "..", "..", "..", ".venv", *(("Scripts", "python.exe") if _o.name == "nt" else ("bin", "python")))
    if _o.path.exists(_v) and _o.path.normcase(_o.path.realpath(_s.prefix)) != _o.path.normcase(_o.path.realpath(_o.path.dirname(_o.path.dirname(_v)))):
        _s.exit(_sp.call([_v, _o.path.realpath(__file__)] + _s.argv[1:]))
import argparse, json, os, sys
import cv2, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("FACE_LANDMARKER", os.path.join(HERE, "face_landmarker.task"))
# landmark indices (MediaPipe face mesh with iris)
R_EYE = (33, 133, 159, 145); L_EYE = (362, 263, 386, 374)      # outer, inner, top, bottom
R_IRIS, L_IRIS = 468, 473; NOSE = 1

def measure(path, fps=10, start=0.0, end=0.0):
    import mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    det = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=MODEL), running_mode=vision.RunningMode.VIDEO, num_faces=1))
    cap = cv2.VideoCapture(path); src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    if start: cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    step = max(1, int(round(src_fps / fps))); i = int(start * src_fps); out = []
    while True:
        ok = cap.grab()
        if not ok: break
        t = i / src_fps
        if end and t > end: break
        if i % step == 0:
            ok, f = cap.retrieve()
            rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB); res = det.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), int(t * 1000))
            rec = {"t": round(t, 2), "face": False}
            if res.face_landmarks:
                p = res.face_landmarks[0]; P = lambda k: np.array([p[k].x, p[k].y])
                hs, vs, op = [], [], []
                for (o, n, tp, bt), ir in ((R_EYE, R_IRIS), (L_EYE, L_IRIS)):
                    a, b, c, d, e = P(o), P(n), P(tp), P(bt), P(ir)
                    w = np.linalg.norm(b - a) + 1e-9; hs.append(np.dot(e - a, b - a) / w ** 2)
                    hgt = np.linalg.norm(d - c) + 1e-9; vs.append(np.dot(e - c, d - c) / hgt ** 2); op.append(hgt / w)
                ro, li = P(33), P(263); nose = P(NOSE)
                yaw = (np.linalg.norm(nose - ro) - np.linalg.norm(nose - li)) / (np.linalg.norm(li - ro) + 1e-9)
                rec.update(face=True, h=round(float(np.mean(hs)), 3), v=round(float(np.mean(vs)), 3), yaw=round(float(yaw), 3), open=round(float(np.mean(op)), 3))
            out.append(rec)
        i += 1
    cap.release(); det.close(); return out

def _kmeans_loop_fallback():
    """scikit-learn's k-means inner loop (_k_means_lloyd), in numpy, for a machine whose policy blocks that one DLL
    (this one, since 2026-10-26). GaussianMixture starts from k-means, so the same loop keeps the same fit."""
    try: import sklearn.cluster._k_means_lloyd; return
    except ImportError: pass
    m = type(sys)("sklearn.cluster._k_means_lloyd")
    def dense(X, sample_weight, centers_old, centers_new, weight_in_clusters, labels, center_shift, n_threads, update_centers=True):
        d = (centers_old ** 2).sum(1)[None, :] - 2 * X @ centers_old.T                 # the loop's own distance: |c|^2 - 2 x.c
        labels[:] = d.argmin(1)
        if not update_centers: return
        centers_new[:] = 0; weight_in_clusters[:] = 0
        np.add.at(centers_new, labels, X * sample_weight[:, None]); np.add.at(weight_in_clusters, labels, sample_weight)
        from sklearn.cluster._k_means_common import _relocate_empty_clusters_dense
        _relocate_empty_clusters_dense(X, sample_weight, centers_old, centers_new, weight_in_clusters, labels)
        nz = weight_in_clusters > 0; centers_new[nz] /= weight_in_clusters[nz][:, None]
        center_shift[:] = np.sqrt(((centers_new - centers_old) ** 2).sum(1))
    def sparse(*a, **k): raise NotImplementedError("sparse k-means is not needed here")
    m.lloyd_iter_chunked_dense, m.lloyd_iter_chunked_sparse = dense, sparse; sys.modules[m.__name__] = m

def _smooth(recs, keys=("h", "v", "yaw"), k=3):
    """median of k neighbouring frames, so one noisy landmark frame does not flip the call"""
    out = {}
    for key in keys:
        xs = [r.get(key) for r in recs]
        for i, r in enumerate(recs):
            if not r["face"]: continue
            win = [x for x in xs[max(0, i - k // 2): i + k // 2 + 1] if x is not None]
            out.setdefault(i, {})[key] = float(np.median(win))
    return out

def _merge_modes(gm, d_min=2.0):
    """Group mixture components that are one gaze target. BIC often splits one elongated blob (the lens,
    with the head drifting) into two or three components; picking the heaviest component would then call
    half the lens frames OFF. Two components are separate targets only when Ashman's D between them, along
    the line joining their means, is over 2 (the usual test for two modes rather than one wide one)."""
    k = gm.n_components; parent = list(range(k))
    def root(a):
        while parent[a] != a: a = parent[a]
        return a
    for i in range(k):
        for j in range(i + 1, k):
            dm = gm.means_[i] - gm.means_[j]; n = np.linalg.norm(dm) + 1e-12; u = dm / n
            si, sj = u @ gm.covariances_[i] @ u, u @ gm.covariances_[j] @ u
            if np.sqrt(2) * n / np.sqrt(si + sj) < d_min: parent[root(j)] = root(i)
    out = {}
    for i in range(k): out.setdefault(root(i), []).append(i)
    return [np.array(v) for v in out.values()]

def classify(recs, min_len=0.25, bridge=0.3, pad=0.1, z=3.5, dv=0.10, lens_at=None):
    """Learn where this presenter's eyes sit when they are on the lens; mark every frame that is not there.

    A presenter reading a script beside the camera has two gaze positions, the lens and the screen. On a
    long take the screen can be a third of all frames, so the median of the take lands between the two and
    the screen is missed (Bulk Uploads at 0:53: eyes and head toward the script, 0.05 from the median,
    under a 0.07 threshold). So instead: fit a Gaussian mixture to (h, yaw) over the open-eyed frames,
    pick the number of clusters (1 to 4) by BIC, and take the heaviest cluster as the lens (or the one
    holding the frame at `lens_at`, when the presenter reads more than they look up). A frame is OFF when
    it belongs more to another cluster than to the lens, when it lies outside the lens cluster itself
    (Mahalanobis distance over z: a sideways glance or a head turn no cluster explains), or when the iris
    sits more than `dv` above or below its lens height (looking down at notes). The vertical measure is
    kept out of the clustering: it is taken against the eyelids, so wide eyes, raised brows and half
    blinks move it while the presenter is still on the lens (checked by eye on Bulk Uploads: most
    "eyes up" calls from a 3-feature model were exactly that).
    Runs of OFF frames closer than `bridge` s are joined, runs shorter than `min_len` s dropped, and each
    stretch is padded by `pad` s so the face is gone a moment before the eyes leave and after they return.
    A run shorter than `min_len` still counts when one of its frames is plainly on another target (lens
    probability under 0.1 or distance over 4.5): on Bulk Uploads that separated a real 0.15 s glance to the
    side (probability 0, distance 5 to 7) from landmark noise (0.3 to 0.5, under 3.1)."""
    _kmeans_loop_fallback(); from sklearn.mixture import GaussianMixture
    sm = _smooth(recs); opens = [r["open"] for r in recs if r["face"]]
    if not opens: return recs, [], {}
    mo = float(np.median(opens))
    idx = [i for i, r in enumerate(recs) if r["face"] and r["open"] > 0.75 * mo]
    X = np.array([[sm[i]["h"], sm[i]["yaw"]] for i in idx])
    mu, sd = X.mean(0), X.std(0) + 1e-9; Z = (X - mu) / sd
    fits = [GaussianMixture(k, covariance_type="full", n_init=5, random_state=0).fit(Z) for k in range(1, 5)]
    gm = min(fits, key=lambda g: g.bic(Z))
    groups = _merge_modes(gm)                                                        # components of one gaze target, joined
    def group_post(z): pp = gm.predict_proba(z); return np.stack([pp[:, g].sum(1) for g in groups], 1)
    if lens_at is not None:
        j = min(range(len(idx)), key=lambda q: abs(recs[idx[q]]["t"] - lens_at)); lens = int(np.argmax(group_post(Z[j:j + 1])[0]))
    else: lens = int(np.argmax([gm.weights_[g].sum() for g in groups]))
    g = groups[lens]; w = gm.weights_[g] / gm.weights_[g].sum(); gmean = (w[:, None] * gm.means_[g]).sum(0)
    gcov = sum(wi * (gm.covariances_[c] + np.outer(gm.means_[c] - gmean, gm.means_[c] - gmean)) for wi, c in zip(w, g))
    lm = gmean * sd + mu; icov = np.linalg.inv(gcov); spread = np.sqrt(np.diag(gcov)) * sd
    lens_rows = [i for q, i in enumerate(idx) if np.argmax(group_post(Z[q:q + 1])[0]) == lens]
    lv = float(np.median([sm[i]["v"] for i in lens_rows]))                             # the iris height on the lens
    base = {"h": float(lm[0]), "v": lv, "yaw": float(lm[1]), "open": mo, "clusters": int(gm.n_components),
            "targets": len(groups), "weights": [round(float(gm.weights_[gg].sum()), 3) for gg in groups], "lens_cluster": lens,
            "means": [[round(float(x), 3) for x in m * sd + mu] for m in gm.means_]}
    for i, r in enumerate(recs):
        r.pop("blink", None)
        if not r["face"]: r["off"] = True; r["why"] = "no face"; continue
        f = np.array([sm[i]["h"], sm[i]["yaw"]]); zf = (f - mu) / sd
        if r["open"] < 0.75 * mo: r["off"] = None; r["blink"] = True; continue        # a blink or half blink: decided by its neighbours
        post = group_post(zf[None])[0]; dz = zf - gmean; maha = float(np.sqrt(dz @ icov @ dz))
        vdev = sm[i]["v"] - lv
        off = post[lens] < 0.5 or maha > z or abs(vdev) > dv
        why = []
        if off:
            d = f - lm                                                                  # against the lens group's own spread, in h and yaw
            if abs(d[0]) > 2 * spread[0]: why.append("eyes " + ("left" if d[0] < 0 else "right"))
            if abs(d[1]) > 2 * spread[1]: why.append("head turned")
            if abs(vdev) > dv: why.append("eyes " + ("up" if vdev < 0 else "down"))
        r["off"] = bool(off); r["why"] = ", ".join(why) if why else ("off the lens" if off else "")
        r["p_lens"] = round(float(post[lens]), 3); r["dist"] = round(maha, 2)
    for i, r in enumerate(recs):                                                      # a blink takes the state around it
        if r.get("off") is None:
            nb = [recs[j].get("off") for j in (i - 1, i + 1) if 0 <= j < len(recs) and recs[j].get("off") is not None]
            r["off"] = bool(nb) and all(nb); r["why"] = "blink" if not r["off"] else "off the lens"
    step = (recs[1]["t"] - recs[0]["t"]) if len(recs) > 1 else 0.1
    clear = lambda r: (r.get("p_lens") is not None and r["p_lens"] < 0.1) or (r.get("dist") or 0) > 4.5 or r["why"] == "no face"
    runs = []; cur = None
    for r in recs:
        if r["off"]:
            if cur and r["t"] - cur[1] <= bridge + step: cur[1] = r["t"]; cur[2].update(x for x in r["why"].split(", ") if x); cur[3] |= clear(r)
            else:
                if cur: runs.append(cur)
                cur = [r["t"], r["t"], set(x for x in r["why"].split(", ") if x), clear(r)]
    if cur: runs.append(cur)
    st = []
    for a, b, w, sure in runs:
        b = b + step
        if b - a < min_len and not sure: continue           # a short run is kept only when the eyes are plainly elsewhere (a real glance, not landmark noise)
        st.append({"start": round(max(0.0, a - pad), 2), "end": round(b + pad, 2), "len": round(b - a + 2 * pad, 2), "why": ", ".join(sorted(w - {"off the lens"}) or ["off the lens"])})
    return recs, st, base

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video"); ap.add_argument("--out", required=True); ap.add_argument("--fps", type=float, default=15); ap.add_argument("--start", type=float, default=0); ap.add_argument("--end", type=float, default=0)
    ap.add_argument("--min-len", type=float, default=0.25, help="shortest look-away kept, seconds")
    ap.add_argument("--lens-at", type=float, default=None, help="a time where the presenter is surely on the lens, if they read more than they look up")
    ap.add_argument("--lookaways", default=None, help="the video is a finished cut: also write its look-aways in edit time (lookaways.json format)")
    a = ap.parse_args()
    recs = json.load(open(a.video))["frames"] if a.video.endswith(".json") else measure(a.video, a.fps, a.start, a.end)
    recs, st, base = classify(recs, min_len=a.min_len, lens_at=a.lens_at)
    if a.lookaways:
        json.dump([{"edit_start": x["start"], "edit_end": x["end"], "len": x["len"], "why": x["why"], "source": None, "line": ""} for x in st], open(a.lookaways, "w"), indent=1)
    print(f"{base.get('clusters')} components, {base.get('targets')} gaze targets weighing {base.get('weights')}; lens = target {base.get('lens_cluster')} at h {base['h']:.3f} v {base['v']:.3f} yaw {base['yaw']:.3f}")
    json.dump({"base": base, "frames": recs, "lookaways": st}, open(a.out, "w"), indent=0)
    on = sum(1 for r in recs if not r.get("off")) / max(1, len(recs))
    print(f"{len(recs)} frames, on the lens {100 * on:.0f}%, {len(st)} look-aways of {a.min_len} s or more -> {a.out}")
    for s in st: print(f"  {s['start']:7.2f}-{s['end']:7.2f}  {s['len']:4.1f} s  {s['why']}")

if __name__ == "__main__":
    main()
