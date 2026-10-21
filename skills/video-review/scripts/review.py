"""review.py: audit a finished video for the small things, and say where each one is.

  python review.py VIDEO.mp4 --out REVIEW_DIR [--cut CUT.mp4] [--script SCRIPT.md] [--words WORDS.json]
                   [--gaze GAZE.json] [--lookaways LOOKAWAYS.json] [--broll BROLL_DIR] [--label NAME] [--skip ocr,face]

Everything but VIDEO is optional; each input switches on the checks that need it:
  (always)       black and frozen frames, static stretches, dead space, text cut at the edges, tiny text, spelling,
                 stale API spellings, loudness, peaks and clipping
  --cut          the presenter: stretched face, head cut off by its window, lip sync, voice drift, and which face is his
  --lookaways    (with --gaze) the face on screen while the eyes are off the lens
  --script       (with --words) every script line in the cut; each B-roll on its line, its section, no ghost frames;
                 each camera call against what is on screen; code on screen with the top-right window; the
                 script's own Count claims; numbers on screen that the script, transcript and docs do not contain
  --broll        the recorded clips (and their *_sections.json: the docs page's own text, for numbers and spelling)
  --take         (with --cutlist) the raw recording: every join of the cut heard in the take, a word clipped at a join,
                 a piece starting or ending mid-word, the same words heard twice where two pieces overlap
  (always)       the pace: a graphic cut in or out with no transition (the house wants soft changes), a card gone before
                 its words can be read, accents outside the Qdrant palette on the graphics
  (with --broll) the first B-roll of each page shows which page it is (its title, breadcrumb, menu)
  (with --script) the brand: the presenter's name lower third ([**Lower third:** NAME | TITLE | 5 s]) read on screen,
                 spelled as the script gives it, held its time, low left, with the face on screen; a script without
                 one is a fix (Qdrant videos always show the presenter's name)

Writes REVIEW_DIR/report.md (findings by time, with a frame for each), report.json, frames/*.jpg, sheet.jpg.
Severity: fix (wrong), check (probably wrong, a person decides), note (worth knowing).
"""
import os, sys, json, glob, argparse, time, collections, math
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import text_checks as TX, script_checks as SC, pace_checks as PC
TH = TX.RULES["thresholds"]

FIXES = {
    "eyes": "the face must be off screen while the eyes are off the lens: widen the hidden span (engine.hidden_spans) or re-run gaze.py on the cut (editing-style skill)",
    "aspect": "the face is stretched: crop the face at the output's own aspect (engine.face_crop; never resize a 2:1 crop into 16:9)",
    "head": "the window cuts the head off: make the window taller or zoom the face crop out, so the whole head shows (house rule)",
    "covered": "a caption or graphic sits over the face (the chin or mouth): move it below the face or shorten the hold",
    "small_face": "the face is too small to read: a bigger window (the cam should show the whole head at ~460x520)",
    "sync": "face and voice are not one to one: rebuild the cut frame-exact (editing skill: assemble.py / rebuild_locked.py) and re-run check_sync.py",
    "voice": "the voice drifts against the cut: the render's audio is not the cut's; re-mux from the cut",
    "edge": "text runs off the frame: shrink or move the element; for docs B-roll do not push or crop past the page's margins",
    "small": "text too small for a phone: docs B-roll at --zoom 1.4 (broll-recorder), bigger fonts on cards",
    "spelling": "fix the source text, or add the word to references/rules.json (lexicon) if it is a real term",
    "number": "show a figure the script or the docs give, or label it as illustrative: viewers read numbers on screen as fact",
    "stale": "show the API the current docs use",
    "overlap": "the text runs past its card or panel (or a shape is drawn over it): widen the box, shorten the label, or move it",
    "code_window": "house rule: code on screen keeps a small top-right presenter window (20%) while the eyes are on the lens",
    "broll_missing": "the B-roll the script asks for is not in the video: check the clip and the splice (broll_layer.py)",
    "broll_late": "the B-roll should land on the first sound of its line: time it to the audio, not the first transcribed word",
    "broll_section": "the B-roll shows another section: pin it (section: in the marker) and record with --style readthrough so it opens on the heading",
    "broll_other": "another section's heading is in the B-roll frame: fine if brief; for a short section use a tighter clip",
    "ghost": "blended (ghost) frames: record without motion interpolation (broll.py default, no --interp)",
    "cadence": "the capture repeats frames while scrolling: smooth enough at 30 fps output, judder at 60",
    "camera": "the edit departs from the script's camera call here: follow the call, or change the call",
    "black": "black frames: a gap in the shot list or a failed decode",
    "static": "nothing moves on screen for this long while he talks: add a move, a highlight or a cut (more movement than not)",
    "dead": "much of the frame is empty background: fill it (no dead space)",
    "blank": "an insert is on screen before anything is drawn in it: start it when its first element lands, and let the shot before run on",
    "loud": "loudness: YouTube plays at -14 LUFS; master to about -14",
    "peak": "peaks near 0 dBFS clip on some players: limit to -1 dBFS",
    "clip": "audio clipping: lower the mix or limit",
    "line": "a script line is not in the cut (or is said very differently): check the take or the script",
    "repeat": "a retake is left in the cut: keep one take (editing skill: the last complete take wins) and re-cut",
    "dead_air": "a long silence is left in the cut: tighten the cut (editing skill, --max-gap) or cover it",
    "count": "the script's Count section disagrees with the script itself: correct the claim",
}

class Video:
    def __init__(self, path):
        self.path = path; c = cv2.VideoCapture(path); self.fps = c.get(cv2.CAP_PROP_FPS) or 30; self.n = int(c.get(cv2.CAP_PROP_FRAME_COUNT))
        self.W, self.H = int(c.get(3)), int(c.get(4)); self.dur = self.n / self.fps; c.release(); self._c = None
    def frame(self, i):
        if self._c is None: self._c = cv2.VideoCapture(self.path)
        self._c.set(cv2.CAP_PROP_POS_FRAMES, i); ok, f = self._c.read(); return f if ok else None

def ts(t): return f"{int(t // 60)}:{t % 60:05.2f}"

def held_off(look, tr=0.5, lead=0.1, min_face=2.0):
    """where the edit keeps the face off by design: each look-away widened by the leaving transition before it, joined when
    the face could not stay min_face between two (engine.hidden_spans). The face missing there is the eye-contact rule."""
    merged = []
    for a, b in sorted([max(0.0, x["edit_start"] - tr - lead), x["edit_end"] + lead] for x in look):
        if merged and a - merged[-1][1] < min_face + tr: merged[-1][1] = max(merged[-1][1], b)
        else: merged.append([a, b])
    return merged

class Findings:
    def __init__(self): self.items = []
    def add(self, kind, sev, t, msg, box=None, t1=None, frame=None, **extra):
        self.items.append(dict(kind=kind, sev=sev, t=round(float(t), 2), t1=round(float(t1), 2) if t1 is not None else None, msg=msg, box=box, frame=frame, **extra))
    def grouped(self, gap=1.6):
        """same kind and message close together: one finding over a stretch"""
        out = []; key = lambda f: (f["kind"], f["msg"] if f["kind"] not in ("eyes", "aspect", "head", "covered", "sync", "small_face", "code_window", "dead") else "")
        for f in sorted(self.items, key=lambda f: (key(f), f["t"])):
            if out and key(out[-1]) == key(f) and f["t"] - (out[-1]["t1"] or out[-1]["t"]) <= gap: out[-1]["t1"] = max(out[-1]["t1"] or out[-1]["t"], f["t1"] or f["t"]); out[-1]["n"] = out[-1].get("n", 1) + 1
            else: out.append(dict(f))
        return sorted(out, key=lambda f: f["t"])

# ---------------------------------------------------------------- pass A: every frame, small
def frame_pass(v, F):
    c = cv2.VideoCapture(v.path); small, mean = [], []
    while True:
        ok, f = c.read()
        if not ok: break
        g = cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (160, 90), interpolation=cv2.INTER_AREA); small.append(g); mean.append(float(g.mean()))
    small = np.array(small); motion = np.r_[0, np.abs(small[1:].astype(np.int16) - small[:-1].astype(np.int16)).mean(axis=(1, 2))]
    flat = [i for i in range(len(small)) if mean[i] >= TH["black_mean"] and float(small[i].std()) < 1.5]       # nothing but background
    for run in _runs(flat):
        if len(run) >= 3: F.add("blank", "fix", run[0] / v.fps, f"{len(run)} empty frame(s), {len(run) / v.fps:.2f} s of plain background: an insert starts before anything is drawn in it", t1=run[-1] / v.fps, frame=run[0])
    black = [i for i, m in enumerate(mean) if m < TH["black_mean"]]
    for run in _runs(black):
        F.add("black", "fix", run[0] / v.fps, f"{len(run)} black frame(s)", t1=run[-1] / v.fps, frame=run[0])
    trans = motion > TH["transition_motion"]
    trans = np.convolve(trans.astype(int), np.ones(int(v.fps * 0.5)), "same") > 0          # half a second around any big move
    return small, motion, trans

def _runs(idx):
    out = []
    for i in idx:
        if out and i == out[-1][-1] + 1: out[-1].append(i)
        else: out.append([i])
    return out

# ---------------------------------------------------------------- pass B: faces (needs the cut)
def face_pass(v, cut, look, gaze, F, step=2, trans=None):
    import face_checks as FC
    fx = FC.Faces(); co, cc = cv2.VideoCapture(v.path), cv2.VideoCapture(cut); recs = []
    gz = json.load(open(gaze))["frames"] if gaze else []
    gzt = np.array([r["t"] for r in gz]) if gz else None
    def off(t):
        if any(x["edit_start"] <= t < x["edit_end"] for x in look): return True
        if gzt is None: return False
        r = gz[int(np.argmin(np.abs(gzt - t)))]
        return bool(r.get("off")) and ((r.get("p_lens") is not None and r["p_lens"] < 0.1) or (r.get("dist") or 0) > 4.5)
    ring = collections.deque(maxlen=9); outs = collections.deque(maxlen=9); i = 0; safe = None
    while True:
        ok1, fo = co.read(); ok2, fc = cc.read()
        if not ok1: break
        ring.append(cv2.cvtColor(fc, cv2.COLOR_BGR2RGB) if ok2 else None); outs.append(fo)
        if len(outs) == 9:
            j = i - 4
            if j % step == 0:
                t = j / v.fps; o_rgb = cv2.cvtColor(outs[4], cv2.COLOR_BGR2RGB); c_rgb = ring[4]
                if safe is None and c_rgb is not None: safe = FC.picture_area(c_rgb)
                ofs = fx.find(o_rgb, int(t * 1000)); cfs = fx.find_cut(c_rgb, int(t * 1000)) if c_rgb is not None else []
                sync_ring = [(k - 4, ring[k]) for k in range(9) if ring[k] is not None] if j % 10 == 0 else None   # three times a second: ECC x9 is slow
                r = FC.analyse(o_rgb, c_rgb, ofs, cfs, sync_ring, safe); r.update(t=round(t, 3), i=j, off=off(t)); recs.append(r)
        i += 1
    W, H = v.W, v.H
    for r in recs:
        if not r["presenter"]: continue
        t, j = r["t"], r["i"]; moving = trans is not None and bool(trans[min(j, len(trans) - 1)])    # a window mid-transition is resized on purpose
        if r["off"]: F.add("eyes", "fix", t, "the presenter's face is on screen while the eyes are off the lens", r.get("box"), frame=j)
        if moving: continue
        if r.get("overlay") and r.get("head_cut") is not None and r["head_cut"] > TH["head_cut_max"]:
            F.add("covered", "check", t, f"a caption or graphic covers {r['head_cut'] * 100:.0f}% of the head ({r.get('head_cut_side')})", r.get("head_box"), frame=j)
        if r.get("face_h") and r["face_h"] < TH["face_min_px"]: F.add("small_face", "check", t, f"the face is {r['face_h']} px tall", r.get("box"), frame=j)
    # head cut: like the stretch, judged per layout. A window does not change between transitions, so its rectangle is the median
    # over the stretch (one sample's measure can stop short at a misfit hairline); the head is measured against that
    hruns, cur = [], []
    for r in recs:
        ok = r["presenter"] and r.get("window") and r.get("head_box") and not r.get("overlay") and r["window"][2] * r["window"][3] < 0.8 * W * H
        if not ok or (trans is not None and trans[min(r["i"], len(trans) - 1)]) or (cur and r["t"] - cur[-1]["t"] > 0.5):
            if cur: hruns.append(cur); cur = []
            if not ok: continue
        if not (trans is not None and trans[min(r["i"], len(trans) - 1)]): cur.append(r)
    if cur: hruns.append(cur)
    for run in hruns:
        if len(run) < 5: continue
        wx0, wy0 = np.median([r["window"][0] for r in run]), np.median([r["window"][1] for r in run])
        wx1, wy1 = np.median([r["window"][0] + r["window"][2] for r in run]), np.median([r["window"][1] + r["window"][3] for r in run])
        cuts, sides = [], collections.Counter()
        for r in run:
            hx0, hy0, hx1, hy1 = r["head_box"]; iw = max(0, min(hx1, wx1) - max(hx0, wx0)); ih = max(0, min(hy1, wy1) - max(hy0, wy0))
            cuts.append(1 - iw * ih / max(1.0, (hx1 - hx0) * (hy1 - hy0)))
            for name, d in (("top", wy0 - hy0), ("bottom", hy1 - wy1), ("left", wx0 - hx0), ("right", hx1 - wx1)):
                if d > 2: sides[name] += 1
        med = float(np.median(cuts))
        if med > TH["head_cut_max"]:
            side = ", ".join(n for n, c in sides.most_common() if c >= len(run) / 2)
            F.add("head", "check", run[0]["t"], f"{med * 100:.0f}% of the head is outside the face window ({side or 'edges'}; median of {len(run)} samples in this window)",
                  run[0]["head_box"], t1=run[-1]["t"], frame=run[0]["i"])
    # stretch: a crop's shape is fixed for a whole layout, so a real stretch holds across it; one frame off is measurement noise
    runs, cur = [], []
    for r in recs:
        if not r["presenter"] or not r.get("aspect") or not r.get("window") or (trans is not None and trans[min(r["i"], len(trans) - 1)]):
            if cur: runs.append(cur); cur = []
            continue
        key = tuple(int(round(u / 24)) for u in r["window"])
        if cur and key != cur[-1][0]: runs.append(cur); cur = []
        cur.append((key, r))
    if cur: runs.append(cur)
    for run in runs:
        if len(run) < 5: continue
        med = float(np.median([r["aspect"] for _, r in run]))
        if abs(med - 1) > TH["aspect_tol"]:
            r0 = run[0][1]; F.add("aspect", "fix", r0["t"], f"face stretched: {abs(med - 1) * 100:.0f}% {'wider' if med > 1 else 'taller'} than the camera's (median of {len(run)} samples in this window)", r0.get("box"), t1=run[-1][1]["t"], frame=r0["i"])
    sy = [r for r in recs if r.get("sync_off") is not None]
    if sy:                                                            # judge sync over stretches, not single frames: a still face is ambiguous
        t_end = sy[-1]["t"]; t = sy[0]["t"]
        while t <= t_end:                                             # 6 s windows, half overlapping; a verdict needs 3 samples that agree
            win = [r for r in sy if t <= r["t"] < t + 6.0]
            if len(win) >= 3:
                med = float(np.median([r["sync_off"] for r in win]))
                if abs(med) > TH["sync_frames"]:
                    F.add("sync", "fix", win[0]["t"], f"the picture runs {abs(med):.0f} frame(s) {'ahead of' if med > 0 else 'behind'} the voice (median of {len(win)} measured samples)", t1=win[-1]["t"], frame=win[0]["i"])
            t += 3.0
        desync = [(f["t"], f["t1"]) for f in F.items if f["kind"] == "sync"]          # a head "cut" inside a desync is only its symptom
        F.items = [f for f in F.items if not (f["kind"] == "head" and any(a - 1 <= f["t"] <= b + 1 for a, b in desync))]
    return recs

# ---------------------------------------------------------------- audio
def audio_checks(v, cut, F):
    import subprocess, imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    raw = subprocess.run([ff, "-v", "error", "-i", v.path, "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2) if raw else np.zeros((0, 2), np.float32)
    res = {}
    if len(x) > 48000:
        import pyloudnorm as pyln
        lufs = pyln.Meter(48000).integrated_loudness(x); peak = 20 * np.log10(max(1e-9, float(np.abs(x).max()))); res.update(lufs=round(lufs, 1), peak_dbfs=round(peak, 2))
        lo, hi = TH["lufs"]
        if not lo <= lufs <= hi: F.add("loud", "check", 0, f"integrated loudness {lufs:.1f} LUFS (YouTube plays at -14)")
        if peak > TH["peak_dbfs"]: F.add("peak", "check", float(np.argmax(np.abs(x).max(axis=1))) / 48000, f"peak {peak:.2f} dBFS")
        mono = x.mean(axis=1); n = 2400; rms = np.array([np.sqrt((mono[i:i + n] ** 2).mean()) for i in range(0, len(mono) - n, n)])
        quiet = [k for k, r in enumerate(rms) if 20 * np.log10(max(r, 1e-6)) < -45 and 0.5 < k * 0.05 < len(mono) / 48000 - 0.8]
        for run in _runs(quiet):                                          # silence left in the cut: dead air
            if len(run) * 0.05 >= TH["dead_air_s"]: F.add("dead_air", "check", run[0] * 0.05, f"{len(run) * 0.05:.1f} s of silence", t1=run[-1] * 0.05 + 0.05)
        hot = np.where(np.abs(x).max(axis=1) >= 0.999)[0]
        for run in _runs(list(hot)):
            if len(run) >= 3: F.add("clip", "fix", run[0] / 48000, f"{len(run)} clipped samples in a row")
    if cut:                                                           # the voice, against the cut, every 15 s
        def pcm(p, t, d):
            o = subprocess.run([ff, "-v", "error", "-ss", f"{t:.3f}", "-i", p, "-t", f"{d}", "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
            return np.frombuffer(o, np.int16).astype(np.float32)
        lags = []
        for t in list(np.arange(2.0, v.dur - 2.0, 15.0)) + [max(2.0, v.dur - 2.2)]:
            a, b = pcm(v.path, t, 1.5), pcm(cut, t, 1.5); n = min(len(a), len(b))
            if n < 8000: continue
            a, b = a[:n] - a[:n].mean(), b[:n] - b[:n].mean(); cc = np.fft.irfft(np.fft.rfft(a, 2 * n) * np.conj(np.fft.rfft(b, 2 * n))); m = int(0.4 * 16000)
            L = (int(np.argmax(np.concatenate([cc[-m:], cc[:m + 1]]))) - m) * 1000 / 16000; lags.append((round(t, 1), L))
            if abs(L) > TH["voice_lag_ms"]: F.add("voice", "fix", t, f"the voice is {L:+.0f} ms off the cut here")
        res["voice_lags_ms"] = lags
    return res

# ---------------------------------------------------------------- pass C: text (OCR), the B-roll and the camera calls
def text_pass(v, F, lex, trans, faces, every=1.0, cache=None, broll_windows=(), sections=None, hide=()):
    hide = list(hide)
    cache = cache or {}; samples = []; t = 0.3
    while t < v.dur - 0.2:
        i = int(t * v.fps); k = 0
        while k < int(v.fps * 0.6) and i + k < v.n - 1 and trans[i + k]: k += 1          # step out of a transition
        samples.append(i + k); t += every
    for w in broll_windows:                                                        # and every half second inside every B-roll:
        if w.get("t0") is None: continue                                           # a heading scrolls ~55 px between reads, none is missed
        u = w["t0"] + 0.6
        while u < w["t1"] - 0.1: samples.append(int(u * v.fps)); u += 0.5
    samples = sorted(set(samples)); fr_by_t = {r["i"]: r for r in faces} if faces else {}
    face_is = np.array(sorted(fr_by_t)) if fr_by_t else None
    def face_at(i):
        if face_is is None: return None
        j = face_is[int(np.argmin(np.abs(face_is - i)))]; return fr_by_t[j] if abs(j - i) <= 6 else None
    results = {}
    for i in samples:
        key = str(i)
        if key not in cache:
            f = v.frame(i)
            if f is None: continue
            cache[key] = TX.ocr(f)
        lines = cache[key]; t = i / v.fps; results[i] = lines
        in_broll = next((w for w in broll_windows if w.get("t0") is not None and w["t0"] <= t <= w["t1"]), None)              # on the page
        page = in_broll or next((w for w in broll_windows if w.get("t0") is not None and w["t0"] - 0.8 <= t < w["t0"]), None)   # or zooming into it
        for kind, sev, msg, box in TX.check_frame(lines, v.W, v.H, lex, in_transition=bool(trans[min(i, len(trans) - 1)]), bgr=v.frame(i), page=bool(page)):
            F.add(kind, sev, t, msg, box, frame=i)
        cl = TX.code_lines(lines); fa = face_at(i)
        if len(cl) >= 2 and not in_broll and fa is not None and not fa.get("off") and not any(a_ <= t <= b_ for a_, b_ in hide):
            win = fa.get("window") if fa.get("presenter") else None
            in_tr = win and win[0] + win[2] / 2 > v.W * 0.6 and win[1] + win[3] / 2 < v.H * 0.45 and win[2] * win[3] < 0.2 * v.W * v.H
            corner_busy = any(l["box"][2] > v.W * 0.72 and l["box"][1] < v.H * 0.4 for l in cl)
            if not in_tr and not corner_busy:
                F.add("code_window", "check", t, "code on screen and the eyes on the lens, but no small top-right presenter window" + (" (the face is full or elsewhere)" if win else " (no face)"),
                      [min(l["box"][0] for l in cl), min(l["box"][1] for l in cl), max(l["box"][2] for l in cl), max(l["box"][3] for l in cl)], frame=i)
        if in_broll and sections:
            sec, how, others = TX.section_of(lines, sections, v.H, v.W); in_broll.setdefault("seen", []).append((round(t, 2), sec, how, others, i))
    return results

def broll_pass(v, small, motion, trans, script, pcs, cut, broll_dir, F):
    """find each B-roll clip in the output by its frames, and compare where it lands with where its line starts"""
    out = []
    for m in script["markers"]:
        clip = os.path.join(broll_dir, m["name"] + ".mp4")
        _, t_line, r = SC.line_time(m["line"], pcs, cut) if pcs else (None, None, 0)
        w = dict(name=m["name"], section=m["section"], line=m["line"], t_line=t_line, match=round(r, 2), t0=None, t1=None, url=m.get("url", ""))
        if t_line is not None and t_line > v.dur - 0.5: continue                        # past the end of this video (a sample range)
        if not os.path.exists(clip): F.add("broll_missing", "fix", t_line or 0, f'B-roll "{m["name"]}": no clip at {clip}'); out.append(w); continue
        c = cv2.VideoCapture(clip); cf = []
        while True:
            ok, f = c.read()
            if not ok: break
            cf.append(cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (160, 90), interpolation=cv2.INTER_AREA))
        cf = np.array(cf[::2])[:, ::2, ::2].astype(np.int16)                  # 80x45 is plenty to know which clip frame it is
        lo = int(max(0, (t_line or 0) - 8) * v.fps); hi = int(min(v.dur, (t_line or v.dur) + 14) * v.fps) if t_line is not None else v.n
        err = np.full(v.n, 255.0)
        for i in range(lo, min(hi, len(small)), 2):
            err[i] = float(np.abs(cf - small[i, ::2, ::2].astype(np.int16)).mean(axis=(1, 2)).min())
        hit = [i for i in range(lo, min(hi, len(small)), 2) if err[i] < 7.0]
        if not hit:
            F.add("broll_missing", "fix", t_line or 0, f'B-roll "{m["name"]}" ({m["section"]}) is not on screen near its line'); out.append(w); continue
        runs = _runs([h // 2 for h in hit]); best = max(runs, key=len); a, b = best[0] * 2, best[-1] * 2
        w.update(t0=round(a / v.fps, 2), t1=round(b / v.fps, 2))
        k0 = max(lo, a - int(v.fps * 0.7)); arrive = k0 + int(np.argmax(motion[k0:a + 1]))   # the arrival: the biggest change just before the
        if motion[arrive] < TH["transition_motion"]: arrive = a                               # clip's own frames match (its zoom-in frames do not)
        w["t_arrive"] = round(arrive / v.fps, 2)
        if t_line is not None and abs(arrive / v.fps - t_line) > TH["broll_late_s"]:
            F.add("broll_late", "check", arrive / v.fps, f'B-roll "{m["name"]}" arrives {arrive / v.fps - t_line:+.2f} s from the first sound of its line ({ts(t_line)})', frame=arrive)
        seg = small[a + int(v.fps * 0.6): b].astype(np.int16)            # ghosts: a frame that is the average of its neighbours
        g = 0; base = a + int(v.fps * 0.6)
        for k in range(1, len(seg) - 1):
            d1 = np.abs(seg[k] - seg[k - 1]).mean(); d2 = np.abs(seg[k] - seg[k + 1]).mean()
            if d1 > 0.6 and d2 > 0.6 and np.abs(seg[k] - (seg[k - 1] + seg[k + 1]) / 2).mean() < 0.25 * min(d1, d2):
                # at 160x90 a slow scroll moves under a pixel a frame and any frame looks like its neighbours' average: confirm at full size,
                # where a real blend shows doubled text (it sits between its neighbours) and a clean frame does not
                fs = [v.frame(base + k + q) for q in (-1, 0, 1)]
                if any(f is None for f in fs): continue
                p0, p1, p2 = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for f in fs]
                e_mid = np.abs(p1 - (p0 + p2) / 2).mean(); e_side = min(np.abs(p1 - p0).mean(), np.abs(p1 - p2).mean())
                if e_mid < 0.35 * e_side: g += 1
        if g: F.add("ghost", "fix", a / v.fps, f'{g} blended frame(s) inside B-roll "{m["name"]}"', t1=b / v.fps, frame=a)
        out.append(w)
    return out

def camera_pass(v, calls, faces, F, hide=()):
    """each camera call against the screen: FULL = a big face, SMALL = a small top-right window, NONE = no face"""
    res = []
    for c in calls:
        rs = [r for r in faces if c["t0"] + 0.6 <= r["t"] <= c["t1"] - 0.3]
        if not rs: continue
        on = [r for r in rs if not r["off"] and not any(a_ <= r["t"] <= b_ for a_, b_ in hide)]
        def kind(r):
            if not r["presenter"]: return "NONE"
            w = r.get("window") or [0, 0, v.W, v.H]; a = w[2] * w[3] / (v.W * v.H)
            if a > 0.7: return "FULL"
            if a < 0.2 and w[0] + w[2] / 2 > v.W * 0.6 and w[1] + w[3] / 2 < v.H * 0.45: return "SMALL"
            return "OTHER"
        ref = on if c["layout"] != "NONE" else rs
        if not ref: res.append(dict(c, agree=None)); continue
        ks = collections.Counter(kind(r) for r in ref); agree = ks[c["layout"]] / len(ref); res.append(dict(c, agree=round(agree, 2), seen=dict(ks)))
        if agree < 0.6:
            F.add("camera", "check" if c["layout"] != "NONE" else "fix", c["t0"], f'camera call {c["layout"]} ({ts(c["t0"])}-{ts(c["t1"])}): on screen {", ".join(f"{k} {n * 100 // len(ref)}%" for k, n in ks.most_common())}'
                  + (" (while on the lens)" if c["layout"] != "NONE" else ""), t1=c["t1"], frame=int(c["t0"] * v.fps))
    return res

# ---------------------------------------------------------------- report
def brand_pass(v, res, script, faces, F):
    """the name lower third: read on screen (OCR), spelled as the script gives it, held its time, low left, over the face"""
    import difflib
    lowers = script.get("lowers", []) if script else []
    if not lowers:
        F.add("brand", "fix", 0, "no name lower third: Qdrant videos show the presenter's name and title (add [**Lower third:** NAME | TITLE | 5 s] after the line it comes in on)")
        return "no lower third in the script"
    fr_by_i = {r["i"]: r for r in faces} if faces else {}; fis = sorted(fr_by_i); out = []
    def face_near(i):
        if not fis: return None
        j = min(fis, key=lambda j_: abs(j_ - i)); return fr_by_i[j] if abs(j - i) <= 6 else None
    for lw in lowers:
        want, title = TX.norm(lw["name"]), TX.norm(lw["title"]); seen, near = [], []
        for i in sorted(res):
            for l in res[i]:
                got = TX.norm(l["text"])
                if not got: continue
                r = difflib.SequenceMatcher(None, got, want).ratio()
                if want in got or r >= 0.93: seen.append((i, l))
                elif r >= 0.75: near.append((i, l, r))
        if not seen:
            if near:
                i, l, r = max(near, key=lambda x: x[2]); F.add("brand", "fix", i / v.fps, f'the name card reads "{l["text"]}", not "{lw["name"]}"', l["box"], frame=i)
            else: F.add("brand", "fix", 0, f'the name lower third ("{lw["name"]}, {lw["title"]}") never appears on screen')
            out.append(f'{lw["name"]}: not found'); continue
        i0, i1 = seen[0][0], seen[-1][0]; held = (i1 - i0) / v.fps + 1.0                      # read about once a second: first to last, plus a step
        if not any(title in TX.norm(" ".join(l["text"] for l in res[i])) for i, _ in seen):
            F.add("brand", "fix", i0 / v.fps, f'the name card shows the name but not the title "{lw["title"]}"', seen[0][1]["box"], frame=i0)
        if held < lw["secs"] - 1.5: F.add("brand", "check", i0 / v.fps, f'the name card is on screen about {held:.0f} s; the script asks for {lw["secs"]:g} s', seen[0][1]["box"], t1=i1 / v.fps, frame=i0)
        bx = seen[0][1]["box"]
        if not (bx[0] < v.W * 0.45 and bx[1] > v.H * 0.55): F.add("brand", "check", i0 / v.fps, "the name card is not in the lower left", bx, frame=i0)
        off = [i for i, _ in seen if face_near(i) is not None and not face_near(i).get("presenter")]
        if off: F.add("brand", "check", off[0] / v.fps, f"the name card is up while the presenter is not on screen ({len(off)} of {len(seen)} reads)", bx, frame=off[0])
        if i0 / v.fps > 4.0: F.add("brand", "check", i0 / v.fps, f"the name card is first read at {ts(i0 / v.fps)}: Qdrant videos open on it, before the title")
        out.append(f'{lw["name"]} on screen {ts(i0 / v.fps)} to {ts(i1 / v.fps)} (about {held:.0f} s)')
    return "; ".join(out)

def annotate(v, f, out_path):
    fr = v.frame(f["frame"]) if f.get("frame") is not None else v.frame(int(f["t"] * v.fps))
    if fr is None: return None
    if f.get("box"):
        x0, y0, x1, y1 = [int(u) for u in f["box"]]; cv2.rectangle(fr, (x0 - 6, y0 - 6), (x1 + 6, y1 + 6), (40, 40, 255), 4)
    cv2.putText(fr, f'{ts(f["t"])}  {f["kind"]}', (24, v.H - 30), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 8); cv2.putText(fr, f'{ts(f["t"])}  {f["kind"]}', (24, v.H - 30), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (60, 220, 255), 3)
    im = cv2.resize(fr, (960, int(960 * v.H / v.W))); cv2.imwrite(out_path, im, [cv2.IMWRITE_JPEG_QUALITY, 85]); return out_path

def write_report(v, out, label, items, stats):
    os.makedirs(os.path.join(out, "frames"), exist_ok=True); tiles = []
    for k, f in enumerate(items):
        if f["sev"] in ("fix", "check") or f["kind"] in ("broll_other",):
            p = annotate(v, f, os.path.join(out, "frames", f"{k:03d}_{f['kind']}_{int(f['t'] * 100):06d}.jpg"))
            if p:
                f["image"] = os.path.relpath(p, out).replace("\\", "/")
                if f["sev"] == "fix" or len(tiles) < 40: tiles.append(cv2.imread(p))
    if tiles:
        cols = 4; h, w = tiles[0].shape[:2]; rows = math.ceil(len(tiles) / cols); sheet = np.zeros((rows * h // 2, cols * w // 2, 3), np.uint8)
        for k, im in enumerate(tiles): sheet[(k // cols) * h // 2:(k // cols + 1) * h // 2, (k % cols) * w // 2:(k % cols + 1) * w // 2] = cv2.resize(im, (w // 2, h // 2))
        cv2.imwrite(os.path.join(out, "sheet.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 80])
    by = collections.Counter(f["sev"] for f in items); kinds = collections.Counter((f["sev"], f["kind"]) for f in items)
    L = [f"# Review: {label}", "", f"`{v.path}`  {v.W}x{v.H}, {v.fps:g} fps, {ts(v.dur)}  reviewed {time.strftime('%Y-%m-%d %H:%M')}", "",
         f"**{by['fix']} to fix, {by['check']} to check, {by['note']} notes.**", ""]
    L += ["| check | result |", "|---|---|"]
    for name, val in stats.items(): L.append(f"| {name} | {val} |")
    L += ["", "| severity | kind | count |", "|---|---|---|"] + [f"| {s} | {k} | {n} |" for (s, k), n in sorted(kinds.items())]
    for sev, title in (("fix", "To fix"), ("check", "To check"), ("note", "Notes")):
        sel = [f for f in items if f["sev"] == sev]
        if not sel: continue
        L += ["", f"## {title}", ""]
        for f in sel:
            when = ts(f["t"]) + (f"-{ts(f['t1'])}" if f.get("t1") and f["t1"] - f["t"] > 0.05 else "")
            L.append(f"- **{when}** (frame {f.get('frame') if f.get('frame') is not None else int(f['t'] * v.fps)}) `{f['kind']}` {f['msg']}" + (f"  ({f['n']} samples)" if f.get("n", 1) > 1 else ""))
            L.append(f"  - fix: {FIXES.get(f['kind'], '')}")
            if f.get("image"): L.append(f"  - ![]({f['image']})")
    open(os.path.join(out, "report.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    json.dump(dict(video=v.path, label=label, stats=stats, findings=items), open(os.path.join(out, "report.json"), "w"), indent=1, default=str)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video"); ap.add_argument("--out", required=True); ap.add_argument("--cut"); ap.add_argument("--script"); ap.add_argument("--words")
    ap.add_argument("--gaze"); ap.add_argument("--lookaways"); ap.add_argument("--broll"); ap.add_argument("--label"); ap.add_argument("--skip", default="")
    ap.add_argument("--cutlist", help="the editing skill's cut list: a line it found no take for is reported missing, not guessed at")
    ap.add_argument("--assets", help="page_assets.py's assets.json: the page's code and captions are its own words and numbers too")
    ap.add_argument("--take", help="the raw recording the cut was made from (with --cutlist): the sound at every join")
    ap.add_argument("--ocr-every", type=float, default=1.0); ap.add_argument("--face-step", type=int, default=2)
    a = ap.parse_args(); skip = set(filter(None, a.skip.split(","))); os.makedirs(a.out, exist_ok=True)
    v = Video(a.video); F = Findings(); stats = collections.OrderedDict(); T0 = time.time()
    def step(name): print(f"[{time.time() - T0:6.0f} s] {name}", flush=True)
    step("frames"); small, motion, trans = frame_pass(v, F)
    static = [i for i in range(len(motion)) if motion[i] < 0.12]
    for run in _runs(static):
        if len(run) >= TH["static_s"] * v.fps: F.add("static", "check", run[0] / v.fps, f"the picture does not move for {len(run) / v.fps:.1f} s", t1=run[-1] / v.fps, frame=run[0])
    cuts = PC.hard_cuts(small, motion, v.fps)
    for i, g0, g1 in cuts:
        if small[min(len(small) - 1, i + 1)].mean() > 200: continue                    # a white flash the script asked for
        what = "into a card" if g1 and not g0 else ("out of a card" if g0 and not g1 else "from one card to the next")
        F.add("abrupt", "fix", i / v.fps, f"a hard cut {what}, no transition: the house wants soft changes of about 0.8 s (a jump cut between two face takes is fine)", frame=i)
    stats["pace"] = f"{len(cuts)} hard cuts into, out of or between cards"
    stats["frames"] = f"{v.n} frames; moving {100 * (motion > 0.12).mean():.0f}% of the time; black {sum(1 for f in F.items if f['kind'] == 'black')} stretches"
    script = SC.parse(a.script) if a.script else None; pcs = SC.pieces(a.words) if a.words else None
    texts = []
    if script: texts += script["lines"] + [m["section"] for m in script["markers"]] + [c["text"] for c in script["calls"]] + [f'{lw["name"]} {lw["title"]}' for lw in script.get("lowers", [])]
    if pcs: texts += [" ".join(p[2]) for p in pcs]
    sections = None; page_titles = {}
    if a.broll:
        sj = sorted(glob.glob(os.path.join(a.broll, "*_sections.json")))
        if sj:
            d = json.load(open(sj[0], encoding="utf-8")); sections = [s for s in d["sections"] if s.get("text")]
            h1 = next((s_["text"] for s_ in d["sections"] if s_.get("tag") == "H1"), d.get("title", ""))
            for m in (script["markers"] if script else []): page_titles[m["url"].split("#")[0].rstrip("/")] = h1
            texts += [s["text"] + " " + s.get("body", "") for s in sections] + [d.get("title", "")]
    if a.assets and os.path.exists(a.assets):
        A = json.load(open(a.assets, encoding="utf-8"))
        texts += [s_["text"] + " " + s_.get("best_fit", "") + " " + s_.get("watch_for", "") + " " + " ".join(c["text"] for c in s_.get("code", [])) + " " + " ".join(f["caption"] for f in s_.get("figures", [])) for s_ in A["sections"]]
    lex = TX.Lexicon(texts)
    no_take, other_words = set(), set()
    if a.cutlist and os.path.exists(a.cutlist):
        import re as _re
        for row in open(a.cutlist, encoding="utf-8"):
            cells = [c.strip() for c in row.strip().strip("|").split("|")]; ln = next((c for c in cells if len(c.split()) >= 3 and "NO TAKE" not in c and "said in other words" not in c), "")
            if "NO TAKE FOUND" in row: no_take.add(ln)
            elif "said in other words" in row: other_words.add(ln)
    look = json.load(open(a.lookaways)) if a.lookaways else []
    faces = []
    if a.cut and "face" not in skip:
        step("faces"); faces = face_pass(v, a.cut, look, a.gaze, F, a.face_step, trans)
        json.dump(faces, open(os.path.join(a.out, "faces.json"), "w"), default=str)       # every face sample, for a closer look
        pres = [r for r in faces if r["presenter"]]
        stats["face"] = (f"presenter on screen in {len(pres)} of {len(faces)} samples; while the eyes were off the lens: {sum(1 for r in pres if r['off'])}; "
                         f"aspect {np.median([r['aspect'] for r in pres if r.get('aspect')]) if pres else 0:.3f} (1 = true)")
    if "audio" not in skip:
        step("audio"); au = audio_checks(v, a.cut, F)
        stats["audio"] = f"{au.get('lufs')} LUFS, peak {au.get('peak_dbfs')} dBFS" + (f"; voice vs cut max {max(abs(l) for _, l in au['voice_lags_ms']):.0f} ms over {len(au['voice_lags_ms'])} points" if au.get("voice_lags_ms") else "")
    windows = []
    if script and a.broll and "broll" not in skip:
        step("b-roll"); windows = broll_pass(v, small, motion, trans, script, pcs, a.cut, a.broll, F)
        stats["b-roll"] = ", ".join(f"{w['name']} {ts(w['t_arrive']) if w.get('t_arrive') is not None else 'MISSING'}" + (f" ({w['t_arrive'] - w['t_line']:+.2f} s vs its line)" if w.get('t_arrive') is not None and w.get('t_line') is not None else "") for w in windows)
    if "ocr" not in skip:
        step("text (ocr)"); cp = os.path.join(a.out, "ocr_cache.json")
        cache = json.load(open(cp)) if os.path.exists(cp) and json.load(open(cp)).get("_video") == [v.path, os.path.getmtime(v.path)] else {"_video": [v.path, os.path.getmtime(v.path)]}
        res = text_pass(v, F, lex, trans, faces, a.ocr_every, cache, windows, sections, held_off(look))
        json.dump(cache, open(cp, "w"))
        stats["text"] = f"{len(res)} frames read"
        if script: stats["brand"] = brand_pass(v, res, script, faces, F)
        bspans = [(w["t0"], w["t1"]) for w in windows if w.get("t0") is not None]
        rd = PC.reading(small, motion, v.fps, res, v.H, TX.is_code, bspans, TH.get("read_wps", 3.8))
        for sev, t0_, t1_, i, msg in rd: F.add("read", sev, t0_, msg, t1=t1_, frame=i)
        stats["pace"] = stats.get("pace", "") + f"; {sum(1 for r in rd if r[0] == 'fix')} cards gone before they can be read, {sum(1 for r in rd if r[0] == 'check')} tight"
        for t_, i, msg in PC.broll_context(res, v.fps, windows, page_titles): F.add("broll_context", "fix", t_, msg, frame=i)
        off_n = 0                                                                     # the palette, on the graphics (not the face, not a recorded page)
        for i in range(int(v.fps), v.n, int(2 * v.fps)):
            t_ = i / v.fps
            if small[i].mean() >= 70 or any(x0 - 0.3 <= t_ <= x1 + 0.3 for x0, x1 in bspans): continue
            fr = v.frame(i)
            if fr is None: continue
            fa = min(faces, key=lambda r: abs(r["i"] - i)) if faces else None
            boxes = [fa["window"]] if fa and fa.get("presenter") and fa.get("window") else [(int(v.W * 0.74), 0, int(v.W * 0.26), int(v.H * 0.4))]
            sh, hexc = PC.brand_colours(fr, boxes)
            if hexc: F.add("brand_colour", "check", t_, f"{sh * 100:.0f}% of the accent colour on this card is off the Qdrant palette (mostly {hexc}): take colours from brand-consistency's brand.py", frame=i); off_n += 1
        stats["brand"] = (stats.get("brand", "") + f"; {off_n} card frames with off-palette accents").lstrip("; ")
        for w in windows:                                             # the section each B-roll shows: the page scrolls continuously, so it
            state = None                                              # stays the last heading that crossed the middle until another one does
            title = TX.norm(page_titles.get((w.get("url") or "").split("#")[0].rstrip("/"), ""))
            t_in = next((x for x in (w.get("t_arrive"), w.get("t0")) if x is not None), 0.0)
            for t, sec, how, others, i in sorted(w.get("seen", [])):
                if how.startswith("heading"): state = sec
                elif state: sec, how = state, "the last heading that crossed the middle"
                if sec and title and TX.norm(sec) == title and t - t_in < 2.5: continue   # the arrival opens on the page's title on purpose
                if sec and w["section"] and TX.norm(sec) != TX.norm(w["section"]):
                    F.add("broll_section", "fix", t, f'B-roll "{w["name"]}" shows "{sec}" ({how}), not "{w["section"]}"', frame=i)
                elif others: F.add("broll_other", "note", t, f'B-roll "{w["name"]}": other headings in frame: {", ".join(o[:40] for o in others)}', frame=i)
        dead_runs = []
        for i in sorted(res):                                         # dead space, on the frames read
            g = cv2.resize(cv2.cvtColor(v.frame(i), cv2.COLOR_BGR2GRAY), (192, 108)).astype(np.float32); bgv = np.median(np.r_[g[0], g[-1], g[:, 0], g[:, -1]])
            blocks = g.reshape(9, 12, 16, 12).swapaxes(1, 2).reshape(9, 16, -1)   # 12x12-pixel blocks of a 192x108 frame
            empty = (blocks.std(axis=2) < 2.5) & (np.abs(blocks.mean(axis=2) - bgv) < 6)     # 9 x 16 blocks
            cols, rows = empty.all(axis=0), empty.all(axis=1)
            run = lambda v: next((k for k, x in enumerate(v) if not x), len(v))           # empty bands from an edge inward
            sw, sh_ = TH["dead_side_w"], TH["dead_side_h"]
            bands = [(run(cols) / 16, "left", sw), (run(cols[::-1]) / 16, "right", sw), (run(rows) / 9, "top", sh_), (run(rows[::-1]) / 9, "bottom", sh_)]
            band = max(((f, n) for f, n, need in bands if f >= need), default=None)                # a whole side: 35% of the width, 40% of the height
            key, frac = ("all", empty.mean()) if empty.mean() > TH["dead_frame"] else ((band[1], band[0]) if band else (None, 0))
            dead_runs.append((i, key, float(frac)))
        # dead space is a layout that leaves a whole side empty ("the whole left side is completely empty"), or an empty
        # frame; words or a card centred on plain background (a Fireship-style stack or title) are a look, not dead space
        cur = []
        for i, key, frac in dead_runs + [(None, None, 0.0)]:
            if i is not None and key and (not cur or cur[-1][1] == key): cur.append((i, key, frac)); continue
            if cur and (cur[-1][0] - cur[0][0]) / v.fps >= TH["dead_space_s"]:
                lo, hi = min(c[2] for c in cur), max(c[2] for c in cur); pct = f"{lo * 100:.0f}%" if hi - lo < 0.05 else f"{lo * 100:.0f}-{hi * 100:.0f}%"
                what = f"nearly the whole frame ({pct}) is empty" if cur[0][1] == "all" else f"the {cur[0][1]} {pct} of the frame is empty, edge to edge"
                F.add("dead", "check", cur[0][0] / v.fps, f"{what} for {(cur[-1][0] - cur[0][0]) / v.fps:.1f} s", t1=cur[-1][0] / v.fps, frame=cur[0][0])
            cur = [(i, key, frac)] if (i is not None and key) else []
    if a.take and a.cutlist and os.path.exists(a.cutlist) and "joins" not in skip:
        step("joins"); import join_checks as JC; J = JC.joins(a.take, a.cutlist)
        for j in J: F.add("join", j["sev"], j["t"], j["msg"])
        stats["joins"] = f"{len(JC.rows(a.cutlist))} pieces; " + (", ".join(f"{sum(1 for j in J if j['sev'] == s_)} {s_}" for s_ in ("fix", "check", "note")) if J else "every join clean")
    if script:
        if pcs:
            missing = [(l, SC.find_line(l, pcs)) for l in script["lines"]]
            for l, (pi, t0, r) in missing:
                if l in no_take:
                    F.add("line", "fix", 0, f'missing from the cut: the editing skill found no take of "{l[:70]}"'); continue
                if l in other_words and r < 0.45:
                    F.add("line", "note", t0 or 0, f'said in other words (the cut list found it between its neighbours): "{l[:70]}"'); continue
                if r >= 0.45 or pi is None: continue
                rec = SC.recall(l, pcs, pi); gap = (t0 or 0) - SC.onset(a.cut, pcs[pi][0], (t0 or 0) + 0.01) if a.cut else 0
                if gap > 0.8: F.add("line", "note", t0 or 0, f'the transcript misses the first {gap:.1f} s of this line (the audio has speech there), so it reads as changed: "{l[:70]}"')
                elif rec >= 0.5: F.add("line", "note", t0 or 0, f'said differently ({rec * 100:.0f}% of its words, match {r:.2f}): "{l[:70]}"')
                elif r < 0.35 and rec < 0.5: F.add("line", "fix", t0 or 0, f'missing from the cut (best match {r:.2f}, {rec * 100:.0f}% of its words): "{l[:70]}"')
                else: F.add("line", "check", t0 or 0, f'script line not found in the cut (best match {r:.2f}, {rec * 100:.0f}% of its words): "{l[:70]}"')
            stats["script"] = f"{len(script['lines'])} lines, {sum(1 for _, (pi, t0, r) in missing if r >= 0.45)} found word for word in the cut; {len(script['markers'])} B-roll markers; {len(script['calls'])} camera calls"
        if pcs:                                                           # the same words said twice: a retake left in the cut
            flat = [(w.lower().strip(".,!?'"), t) for p_ in pcs for w, t in zip(p_[2], p_[3])]
            seen, last_end = {}, -1.0
            for k in range(len(flat) - 5):
                g = " ".join(w for w, _ in flat[k:k + 6]); t = flat[k][1]
                if g in seen and t - seen[g] < 25 and t > last_end:
                    F.add("repeat", "fix", t, f'said twice: "{g}" ({ts(seen[g])} and {ts(t)})', t1=flat[k + 5][1]); last_end = flat[k + 5][1]
                seen.setdefault(g, t)
        cl = script["counts"]
        if cl.get("calls") is not None and cl["calls"] != len(script["calls"]): F.add("count", "fix", 0, f"the Count section says {cl['calls']} camera calls; the script has {len(script['calls'])}")
        if cl.get("broll") is not None and cl["broll"] != len(script["markers"]): F.add("count", "fix", 0, f"the Count section says {cl['broll']} B-roll; the script has {len(script['markers'])}")
        if cl.get("dur_s") and v.dur > 0.8 * cl["dur_s"] and abs(cl["dur_s"] - v.dur) > 1.5: F.add("count", "check", 0, f"the Count section says the video is {cl['dur_s']} s; it is {v.dur:.1f} s")
        if faces and pcs:
            spans = SC.call_spans(script["calls"], pcs, a.cut, v.dur); cr = camera_pass(v, spans, faces, F, held_off(look))
            stats["camera calls"] = f"{sum(1 for c in cr if c.get('agree') is not None and c['agree'] >= 0.6)} of {len(cr)} followed (60%+ of the time)"
    items = F.grouped()
    step("report"); write_report(v, a.out, a.label or os.path.basename(a.video), items, stats)
    by = collections.Counter(f["sev"] for f in items)
    print(f"-> {os.path.join(a.out, 'report.md')}: {by['fix']} to fix, {by['check']} to check, {by['note']} notes")
    return 1 if by["fix"] else 0

if __name__ == "__main__":
    sys.exit(main())
