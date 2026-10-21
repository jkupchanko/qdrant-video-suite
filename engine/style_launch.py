"""LAUNCH: the coding vocabulary (real code, real components) with the finish of a dev-tool launch video.

Built after John called the IDE and System Design samples "a little too basic". It keeps what the top coding
channels show (code, the components of the system) and adds what they lack, following his motion rules
(memory: motion-design-feedback):
  - a different kind of element in every section: a 3D code window with a data beam, flipping workload cards,
    a roadmap that draws itself, live vector visualizations with a 3D HNSW graph, gauges, a memory hierarchy
  - varied entrances: rise, draw-on, pop, slide-stagger, flip, count-up, mask reveal, drop
  - varied transitions between sections: push-through, glide, drop, tilt-away
  - exact layout: every element sits in a fraction of the content region and text is fitted to its box
The face changes layout (full, side card, half screen, corner) while the content region reflows to fill the
space it leaves, so there is no dead space. Inside a look-away the face leaves and the content fills the frame.

  python style_launch.py 0 41             sample -> out/launch_0-41.mp4
  python style_launch.py stills 2 6 20    contact sheet
"""
import os, sys, json, math, numpy as np, skia
from PIL import Image
import engine as E
import style_full as SF
W, H = E.W, E.H; TR = E.TR
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\launch.mp4"
FONTS = r"C:\Users\ADMIN\camera_audit\fonts"; LOGO = r"C:\Users\ADMIN\camera_audit\assets\qdrant-brandmark-red.png"
NAVY = (11, 15, 25); CARD0, CARD1 = (25, 32, 54), (15, 20, 35); TXT, MUTE, DIM = (240, 243, 250), (138, 144, 166), (70, 78, 102)
RED, RED_L, VIOL, VIOL_L, TEAL, TEAL_L, AMBER, GREEN = (220, 36, 76), (255, 135, 146), (96, 71, 255), (180, 168, 255), (0, 150, 136), (79, 209, 197), (255, 183, 77), (61, 220, 132)
SANS, SANS_B, MONO = "MonaSans-SemiBold.ttf", "MonaSans-Bold.ttf", "GeistMono-Regular.ttf"
RAD = 20; M = 56
_tf = {}
def font(name, size):
    if name not in _tf: _tf[name] = skia.Typeface.MakeFromFile(os.path.join(FONTS, name))
    return skia.Font(_tf[name], max(1.0, size))
def col(c, a=1.0): return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(255 * max(0.0, min(1.0, a))))
def paint(c, a=1.0, stroke=0.0, blur=0.0, cap=True):
    p = skia.Paint(AntiAlias=True, Color=col(c, a))
    if stroke: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke); p.setStrokeCap(skia.Paint.kRound_Cap if cap else skia.Paint.kButt_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p
def fitsize(name, s, max_w, size):
    w = font(name, size).measureText(s); return size if w <= max_w else size * max_w / max(1.0, w)
def text(cv, s, x, y, size, c=TXT, a=1.0, name=SANS, max_w=None, align="left"):
    if a <= 0.004 or not s: return 0
    if max_w: size = fitsize(name, s, max_w, size)
    f = font(name, size); w = f.measureText(s); x = x - w / 2 if align == "center" else (x - w if align == "right" else x)
    cv.drawString(s, x, y, f, paint(c, a)); return w
def ramp(t, a, d=0.45): return max(0.0, min(1.0, (t - a) / d))
ease, inout, back = E.ease, E.inout, E.back
def ap(t, at, d=0.45): return ease(ramp(t, at - 0.25, d))                    # an element lands just ahead of its word
def lerp(a, b, k): return a + (b - a) * k
def lerpr(r0, r1, k): return tuple(lerp(a, b, k) for a, b in zip(r0, r1))
WORDS = json.load(open(r"C:\Users\ADMIN\camera_audit\styles\out\v2_words.json"))["pieces"]
def wd(i, w, nth=0):
    hits = [t for x, t in WORDS[i]["words"] if x.lower().strip(",.?!").startswith(w.lower())]; return hits[min(nth, len(hits) - 1)]
L = [p["t0"] for p in WORDS]
T = dict(up=wd(0, "uploading"), large=wd(0, "large"), data=wd(0, "data"), qd=wd(0, "qdrant"), store=wd(0, "store"), vec=wd(0, "vectors"),
         pay=wd(1, "payloads"), idx=wd(1, "indexes"), bg=wd(1, "much"), single=wd(2, "single"), conf=wd(2, "configuration"), works=wd(2, "works"), wf=wd(2, "workflows"),
         opt=wd(3, "options"), best=wd(3, "best"), diff=wd(4, "difference"), dense=wd(4, "dense"), sparse=wd(4, "sparse"), hnsw=wd(5, "hnsw"), sidx=wd(6, "completely"),
         mem=wd(7, "memory"), perf=wd(7, "performance"), bulk=wd(7, "bulk"), first=wd(8, "first"), storing=wd(9, "storing"), disk=wd(9, "disk"))

# ---------------------------------------------------------------- drawing kit
def rr(x, y, w, h, r=RAD): return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)
def glass(cv, x, y, w, h, a=1.0, accent=None, glow=0.0, r=RAD, shadow=True):
    """a card: soft shadow, a top-lit fill, a hairline border; an accent border and glow when it is the focus"""
    if a <= 0.004 or w <= 2 or h <= 2: return
    if shadow: cv.drawRRect(rr(x, y + 18, w, h, r), paint((0, 0, 0), 0.45 * a, blur=26))
    p = skia.Paint(AntiAlias=True); p.setShader(skia.GradientShader.MakeLinear([skia.Point(x, y), skia.Point(x, y + h)], [col(CARD0, 0.96 * a), col(CARD1, 0.96 * a)])); cv.drawRRect(rr(x, y, w, h, r), p)
    b = skia.Paint(AntiAlias=True); b.setStyle(skia.Paint.kStroke_Style); b.setStrokeWidth(1.5)
    b.setShader(skia.GradientShader.MakeLinear([skia.Point(x, y), skia.Point(x, y + h)], [col((255, 255, 255), 0.16 * a), col((255, 255, 255), 0.04 * a)])); cv.drawRRect(rr(x, y, w, h, r), b)
    if accent is not None:
        if glow > 0: cv.drawRRect(rr(x, y, w, h, r), paint(accent, 0.55 * glow * a, 3, blur=14))
        cv.drawRRect(rr(x, y, w, h, r), paint(accent, 0.9 * a, 2))
def pill(cv, s, x, y, c, a=1.0, size=22, name=MONO, fillc=None, align="left"):
    if a <= 0.004: return 0
    f = font(name, size); w = f.measureText(s) + size * 1.2; h = size * 1.7; x0 = x - w / 2 if align == "center" else x
    cv.drawRRect(rr(x0, y - h / 2, w, h, h / 2), paint(fillc or c, 0.16 * a)); cv.drawRRect(rr(x0, y - h / 2, w, h, h / 2), paint(c, 0.75 * a, 1.5))
    cv.drawString(s, x0 + size * 0.6, y + size * 0.36, f, paint(c, a)); return w
def kicker(cv, s, x, y, u, a, c=RED_L, max_w=None): return text(cv, s, x, y, 20 * u, c, a, MONO, max_w)
def segment(path, k0, k1):
    pm = skia.PathMeasure(path, False); L_ = pm.getLength(); d = skia.Path(); pm.getSegment(L_ * max(0, k0), L_ * min(1, k1), d, True); return d, L_
def point_on(path, k):
    pm = skia.PathMeasure(path, False); r = pm.getPosTan(pm.getLength() * max(0.0, min(1.0, k))); return (r[0].x(), r[0].y()) if isinstance(r, tuple) else (r.x(), r.y())
def beam(cv, path, t, a, c, draw=1.0, width=3.0, speed=0.9, n=3):
    """a connector that draws itself on, then carries glowing pulses along it"""
    if a <= 0.004 or draw <= 0: return
    base, _ = segment(path, 0, draw); cv.drawPath(base, paint(c, 0.28 * a, width)); cv.drawPath(base, paint(c, 0.18 * a, width * 4, blur=10))
    if draw < 1:
        hx, hy = point_on(path, draw); cv.drawCircle(hx, hy, width * 3, paint(c, a, blur=6)); cv.drawCircle(hx, hy, width * 1.4, paint(TXT, a)); return
    for k in range(n):
        ph = (t * speed + k / n) % 1; seg, _ = segment(path, ph - 0.10, ph)
        cv.drawPath(seg, paint(c, 0.9 * a, width * 2.2, blur=7)); cv.drawPath(seg, paint(TXT, 0.85 * a, width * 0.9))
def persp(r, ry=0.0, rx=0.0, f=1600.0):
    """a matrix that maps the rect r onto itself turned ry degrees about its vertical axis (rx about horizontal), in perspective"""
    x, y, w, h = r; cx, cy = x + w / 2, y + h / 2; ay, ax = math.radians(ry), math.radians(rx); dst = []
    for (px, py) in ((x, y), (x + w, y), (x + w, y + h), (x, y + h)):
        X, Y, Z = px - cx, py - cy, 0.0
        X, Z = X * math.cos(ay) + Z * math.sin(ay), -X * math.sin(ay) + Z * math.cos(ay)
        Y, Z = Y * math.cos(ax) - Z * math.sin(ax), Y * math.sin(ax) + Z * math.cos(ax)
        s = f / (f + Z); dst.append(skia.Point(cx + X * s, cy + Y * s))
    m = skia.Matrix(); m.setPolyToPoly([skia.Point(x, y), skia.Point(x + w, y), skia.Point(x + w, y + h), skia.Point(x, y + h)], dst); return m
_logo = None
def logo(cv, x, y, s, a=1.0):
    global _logo
    if _logo is None: _logo = skia.Image.open(LOGO)
    cv.drawImageRect(_logo, skia.Rect.MakeXYWH(x, y, s, s * _logo.height() / _logo.width()), skia.SamplingOptions(skia.FilterMode.kLinear), paint(TXT, a))

CODE_COL = dict(kw=VIOL_L, st=TEAL_L, num=RED_L, com=(110, 118, 140), fn=TXT, cls=AMBER, arg=(156, 220, 254), txt=(205, 210, 225))
import re
def tokens(s):
    out = []
    for m_ in re.finditer(r'(#.*$)|("[^"]*"?)|(\b\d[\d_,.]*\b)|(\w+)(?=\s*=(?!=))|(\w+)(?=\()|(\b[A-Z]\w*)|(\w+)|(\s+)|(.)', s):
        g = m_.lastindex; v = m_.group(0)
        c = {1: "com", 2: "st", 3: "num", 4: "arg", 5: "fn", 6: "cls", 7: "kw" if v in ("from", "import", "def", "return", "True", "False", "None") else "txt"}.get(g, "txt"); out.append((v, CODE_COL[c]))
    return out
def code_window(cv, x, y, w, h, lines, t, a, title="bulk_upload.py", hl=None, cps=48, fs=None):
    """a floating editor window; lines = [(text, t_start or None)]; hl = (line index, alpha) to select a line"""
    glass(cv, x, y, w, h, a)
    for k, c in enumerate(((255, 95, 87), (254, 188, 46), (40, 200, 64))): cv.drawCircle(x + 26 + k * 22, y + 26, 6.5, paint(c, a))
    text(cv, title, x + w / 2, y + 32, 17, MUTE, a, MONO, align="center"); cv.drawLine(x, y + 52, x + w, y + 52, paint((255, 255, 255), 0.07 * a, 1))
    longest = max(len(s) for s, _ in lines) or 1; fs = fs or min(26.0, (w - 90) / (longest * 0.62), (h - 80) / (len(lines) * 1.6)); f = font(MONO, fs); cw = f.measureText("M"); lh = fs * 1.6
    for k, (s, ts) in enumerate(lines):
        yy = y + 52 + 22 + (k + 0.8) * lh
        n = len(s) if ts is None else (0 if t < ts else min(len(s), int((t - ts) * cps)))
        if hl and hl[0] == k and hl[1] > 0: cv.drawRRect(rr(x + 10, yy - fs * 1.05, w - 20, lh, 6), paint(VIOL, 0.28 * hl[1] * a)); cv.drawRect(skia.Rect.MakeXYWH(x + 10, yy - fs * 1.05, 3, lh), paint(VIOL_L, hl[1] * a))
        text(cv, str(k + 1), x + 40, yy, fs * 0.86, DIM, a, MONO, align="right"); xx = x + 58; shown = 0
        for v, c in tokens(s):
            if shown >= n: break
            part = v[: n - shown]; cv.drawString(part, xx, yy, f, paint(c, a)); xx += cw * len(part); shown += len(v)
        if ts is not None and 0 < n < len(s): cv.drawRect(skia.Rect.MakeXYWH(xx + 1, yy - fs * 0.95, 2.5, fs * 1.2), paint(TXT, a))

def counter(n): return f"{int(n):,}"
def gauge(cv, cx, cy, r, v, c, a, label, value_s, u):
    """a radial gauge, 270 degrees, filling to v"""
    if a <= 0.004: return
    rect = skia.Rect(cx - r, cy - r, cx + r, cy + r); cv.drawArc(rect, 135, 270, False, paint((255, 255, 255), 0.08 * a, 18 * u, cap=True))
    if v > 0: cv.drawArc(rect, 135, 270 * v, False, paint(c, 0.5 * a, 22 * u, blur=10)); cv.drawArc(rect, 135, 270 * v, False, paint(c, a, 18 * u))
    text(cv, value_s, cx, cy + 14 * u, 50 * u, TXT, a, SANS_B, align="center"); text(cv, label, cx, cy + r * 0.86, 21 * u, MUTE, a, SANS, max_w=r * 1.8, align="center")

# ---------------------------------------------------------------- background (drawn once) and face layouts
_bg = None
def background():
    global _bg
    if _bg is not None: return _bg
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col(NAVY))
    for (gx, gy, gr, c, a) in ((260, 120, 760, VIOL, 0.22), (1720, 980, 820, RED, 0.12), (1500, 160, 520, TEAL, 0.07)): cv.drawCircle(gx, gy, gr, paint(c, a, blur=220))
    for gx in range(16, W, 32):
        for gy in range(16, H, 32):
            d = math.hypot(gx - W / 2, gy - H / 2) / (W * 0.6); cv.drawCircle(gx, gy, 1.2, paint((255, 255, 255), 0.07 * max(0, 1 - d)))
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), W * 0.75, [col((0, 0, 0), 0), col((0, 0, 0), 0.55)], [0.55, 1.0])); cv.drawRect(skia.Rect(0, 0, W, H), p)
    _bg = s.makeImageSnapshot(); return _bg

FACE_R = dict(full=(0, 0, W, H), side=(W - M - 620, M, 620, H - 2 * M), half=(0, 0, W // 2, H), corner=(W - M - 360, M, 360, 360))
REGION = dict(side=(M, M, W - 3 * M - 620 + 16, H - 2 * M), half=(W // 2 + 44, M, W // 2 - 44 - M, H - 2 * M), corner=(M, M, W - 3 * M - 360 + 16, H - 2 * M), none=(M, M, W - 2 * M, H - 2 * M))
FACE_RAD = dict(full=0, side=RAD, half=0, corner=RAD); FACE_Z = dict(full=1.0, side=1.0, half=1.0, corner=1.25)
LKEYS = [(0.0, "full"), (0.9, "side"), (L[1], "corner"), (L[2], "half"), (L[3], "full"), (wd(3, "different") - 0.2, "corner"), (L[4], "side"),
         (L[6], "corner"), (L[7], "half"), (L[8], "full"), (L[9], "side")]
def layout_keys(look):
    hide = E.hidden_spans(look); keys = []
    for k, (t0, lay) in enumerate(LKEYS):
        t1 = LKEYS[k + 1][0] if k + 1 < len(LKEYS) else 1e9; cur = t0
        for a, b in hide:
            if b <= cur or a >= t1: continue
            if a > cur: keys.append((cur, lay))
            keys.append((max(a, cur), "none")); cur = min(b, t1)
        if cur < t1: keys.append((cur, lay))
    out = []
    for k in keys:
        if not out or out[-1][1] != k[1]: out.append(k)
    return out
def offscreen(r):
    x, y, w, h = r; return (x - w - 80, y, w, h) if x + w / 2 < W / 2 else (W + 80, y, w, h)
def layout_at(keys, t):
    """face rect, radius, zoom, border alpha; the content region; how much of the content shows (not under a full face)"""
    i = max(j for j, k in enumerate(keys) if t >= k[0]); cur = keys[i][1]; prev = keys[i - 1][1] if i else cur; e = inout(ramp(t, keys[i][0], TR))
    def fr(lay, other): return offscreen(FACE_R[other if other in FACE_R else "side"]) if lay == "none" else FACE_R[lay]
    def rg(lay, j):
        if lay != "full": return REGION[lay]
        for k_ in keys[j:] + keys[:j][::-1]:
            if k_[1] != "full": return REGION[k_[1]]
        return REGION["none"]
    f0, f1 = fr(prev, cur), fr(cur, prev); face = lerpr(f0, f1, e)
    rad = lerp(FACE_RAD.get(prev, RAD), FACE_RAD.get(cur, RAD), e); z = lerp(FACE_Z.get(prev, 1.0), FACE_Z.get(cur, 1.0), e)
    bord = lerp(1.0 if prev in ("side", "corner") else 0.0, 1.0 if cur in ("side", "corner") else 0.0, e)
    region = lerpr(rg(prev, max(0, i - 1)), rg(cur, i), e); vis = lerp(0.0 if prev == "full" else 1.0, 0.0 if cur == "full" else 1.0, e)
    shows = not (cur == "none" and e >= 1) and not (prev == "none" and cur == "none")
    return face, rad, z, bord, region, vis, shows

# ---------------------------------------------------------------- the sections; each lays itself out in the content region R
def S1(cv, t, R):
    """the hook: a 3D code window streams the upload into the Qdrant node, which then opens up"""
    x, y, w, h = R; u = min(w / 1148, h / 968, 1.25); kb = inout(ramp(t, L[1] - 0.05, 0.7))         # phase B: the node opens
    kicker(cv, "BULK UPLOADS IN QDRANT", x, y + 24 * u, u, ap(t, 0.9))
    cr = lerpr((x, y + 0.10 * h, 0.62 * w, 0.58 * h), (x, y + 0.08 * h, 0.40 * w, 0.40 * h), kb)
    nr = lerpr((x + 0.70 * w, y + 0.10 * h, 0.30 * w, 0.58 * h), (x + 0.47 * w, y + 0.0 * h, 0.53 * w, 1.0 * h), kb)
    a_code = ap(t, T["up"] - 0.1, 0.6); rise = (1 - ease(ramp(t, T["up"] - 0.35, 0.7))) * 60 * u
    lines = [("from qdrant_client import QdrantClient", None), ('client = QdrantClient("http://localhost:6333")', None), ("", None),
             ('points = load_points("data.jsonl")  # 1,000,000', None), ('client.upload_points("docs", points, batch_size=256)', None)]
    cv.save(); cv.translate(0, rise); cv.concat(persp(cr, ry=lerp(28, 10, ease(ramp(t, T["up"] - 0.3, 1.2))) + 2 * math.sin(t * 0.6), rx=-4))
    code_window(cv, *cr, lines, t, a_code, hl=(3 if t < T["qd"] else 4, ap(t, T["large"]) if t < L[1] else 0.0)); cv.restore()
    # the beam: code -> node
    p = skia.Path(); sx, sy = cr[0] + cr[2] * 0.97, cr[1] + cr[3] * 0.62; ex, ey = nr[0], nr[1] + min(nr[3], 0.42 * h) * 0.5
    p.moveTo(sx, sy); p.cubicTo(sx + (ex - sx) * 0.5, sy, sx + (ex - sx) * 0.5, ey, ex, ey)
    beam(cv, p, t, ap(t, T["up"]), VIOL_L, draw=ease(ramp(t, T["up"] + 0.2, 0.7)), width=3 * u, speed=0.8 + 0.8 * ease(ramp(t, T["large"], 0.5)), n=2 + int(4 * ease(ramp(t, T["large"], 0.5))))
    n = 1_000_000 * ease(ramp(t, T["large"], 6.5)); cy_ = lerp(y + 0.84 * h, y + 0.56 * h, kb); cx_ = lerp(x + 0.5 * w, x + 0.20 * w, kb)
    a_n = ap(t, T["large"]); text(cv, counter(n), cx_, cy_, lerp(96, 66, kb) * u, TXT, a_n, SANS_B, align="center"); text(cv, "points uploaded", cx_, cy_ + 34 * u, 22 * u, MUTE, a_n, SANS, align="center")
    # throughput card fills the left column once the node opens
    a_tp = ease(ramp(t, L[1] + 0.3, 0.6))
    if a_tp > 0:
        tx, ty, tw, th = x, y + 0.66 * h, 0.40 * w, 0.34 * h; glass(cv, tx, ty + (1 - a_tp) * 40 * u, tw, th, a_tp); ty += (1 - a_tp) * 40 * u
        text(cv, "throughput", tx + 26 * u, ty + 40 * u, 20 * u, MUTE, a_tp, MONO); text(cv, f"{int(14200 + 900 * math.sin(t * 2.1)):,} pts/s", tx + 26 * u, ty + 86 * u, 40 * u, TXT, a_tp, SANS_B, max_w=tw - 52 * u)
        pth = skia.Path(); n_ = 60
        for k in range(n_):
            tt = t - (n_ - k) * 0.08; v = 0.55 + 0.25 * math.sin(tt * 2.1) + 0.12 * math.sin(tt * 5.3); px, py = tx + 26 * u + (tw - 52 * u) * k / (n_ - 1), ty + th - 30 * u - v * (th - 150 * u)
            pth.moveTo(px, py) if k == 0 else pth.lineTo(px, py)
        cv.drawPath(pth, paint(TEAL_L, 0.35 * a_tp, 8 * u, blur=8)); cv.drawPath(pth, paint(TEAL_L, a_tp, 3 * u))
    # the Qdrant node, opening into what it does besides storing vectors
    a_node = back(ramp(t, T["qd"] - 0.3, 0.5)) if t < T["qd"] + 0.3 else 1.0
    if a_node > 0:
        cv.save(); cx0, cy0 = nr[0] + nr[2] / 2, nr[1] + nr[3] / 2; cv.translate(cx0, cy0); s_ = 0.8 + 0.2 * min(1.0, a_node); cv.scale(s_, s_); cv.translate(-cx0, -cy0)
        nx, ny, nw, nh = nr; a_ = min(1.0, a_node); glass(cv, nx, ny, nw, nh, a_, accent=RED, glow=0.5 + 0.5 * math.sin(t * 2.5) ** 2)
        logo(cv, nx + 26 * u, ny + 26 * u, 46 * u, a_); text(cv, "Qdrant", nx + 86 * u, ny + 62 * u, 34 * u, TXT, a_, SANS_B)
        cv.drawCircle(nx + nw - 34 * u, ny + 50 * u, 7 * u, paint(GREEN, a_)); cv.drawCircle(nx + nw - 34 * u, ny + 50 * u, 14 * u, paint(GREEN, 0.4 * a_ * abs(math.sin(t * 3)), blur=6))
        vs = ap(t, T["store"]); vy = ny + 100 * u                                     # the vectors it stores
        text(cv, "vectors", nx + 26 * u, vy + 22 * u, 20 * u, MUTE, vs * a_, MONO); fillk = min(1.0, n / 1_000_000)
        cols_ = max(8, int((nw - 52 * u) / (16 * u)))
        for k in range(cols_):
            on = k < cols_ * fillk; cv.drawRRect(rr(nx + 26 * u + k * 16 * u, vy + 36 * u, 11 * u, 26 * u, 3 * u), paint(VIOL if on else DIM, (0.95 if on else 0.4) * vs * a_))
        subs = [("Payloads", T["pay"], TAG_PANEL), ("Indexes", T["idx"], IDX_PANEL), ("Background work", T["bg"], BG_PANEL)]
        for k, (name, at, fn) in enumerate(subs):
            a_s = ease(ramp(t, at - 0.3, 0.5)) * kb
            if a_s <= 0: continue
            sy0 = ny + 190 * u + k * (nh - 210 * u) / 3; sh = (nh - 210 * u) / 3 - 16 * u; off = (1 - a_s) * 80 * u
            glass(cv, nx + 22 * u + off, sy0, nw - 44 * u, sh, a_s, shadow=False); text(cv, name, nx + 46 * u + off, sy0 + 40 * u, 26 * u, TXT, a_s, SANS_B)
            fn(cv, t, (nx + 46 * u + off, sy0 + 56 * u, nw - 92 * u, sh - 70 * u), a_s, u, at)
        cv.restore()
def TAG_PANEL(cv, t, r, a, u, at):
    x, y, w, h = r; s = '{"category": "news", "lang": "en", "year": 2024}'; fs = fitsize(MONO, s, w, 23 * u); f = font(MONO, fs); xx = x
    for v, c in tokens(s): cv.drawString(v, xx, y + h * 0.42, f, paint(c, a)); xx += f.measureText(v)
    pill(cv, "filterable", x, y + h * 0.82, TEAL_L, a * ease(ramp(t, at + 0.3, 0.4)), 18 * u)
def IDX_PANEL(cv, t, r, a, u, at):
    x, y, w, h = r; rd = np.random.default_rng(4); pts = [(x + rd.uniform(0.02, 0.62) * w, y + rd.uniform(0.1, 0.92) * h) for _ in range(14)]; g = ease(ramp(t, at, 1.4))
    edges = [(i, j) for i in range(14) for j in range(i + 1, 14) if math.dist(pts[i], pts[j]) < w * 0.17]
    for k, (i, j) in enumerate(edges[: int(len(edges) * g)]): cv.drawLine(*pts[i], *pts[j], paint(VIOL_L, 0.6 * a, 2 * u))
    for p in pts: cv.drawCircle(*p, 5 * u, paint(VIOL_L, a))
    pill(cv, "HNSW", x + 0.72 * w, y + h * 0.5, VIOL_L, a * g, 20 * u)
def BG_PANEL(cv, t, r, a, u, at):
    x, y, w, h = r
    for k, (name, job) in enumerate((("optimizer", "merging segments"), ("wal", "flushing to disk"), ("indexer", "building HNSW"))):
        a_k = a * ease(ramp(t, at + 0.25 * k, 0.35)); yy = y + (k + 0.7) * h / 3.3
        cv.drawArc(skia.Rect(x, yy - 16 * u, x + 22 * u, yy + 6 * u), (t * 400 + k * 120) % 360, 260, False, paint(TEAL_L, a_k, 3 * u))
        text(cv, name, x + 38 * u, yy, 21 * u, TEAL_L, a_k, MONO); text(cv, job, x + 190 * u, yy, 21 * u, MUTE, a_k, MONO, max_w=w - 200 * u)

WORKLOADS = [("RAG chatbot", "10M vectors · low latency", "on_disk=False · m=32", VIOL_L), ("Analytics", "heavy payload filters", "payload index first", TEAL_L), ("Multi-tenant SaaS", "thousands of tenants", "is_tenant · 6 shards", AMBER)]
def S2(cv, t, R):
    """one config does not fit every workload: a default config, and workload cards that flip in"""
    x, y, w, h = R; u = min(w / 864, h / 968, 1.25)
    kicker(cv, "NO ONE-SIZE-FITS-ALL", x, y + 24 * u, u, ap(t, L[2] + 0.1)); text(cv, "One config won't fit every workload", x, y + 76 * u, 44 * u, TXT, ap(t, T["single"]), SANS_B, max_w=w)
    a_d = ap(t, T["single"]); dy = (1 - back(ramp(t, T["single"] - 0.25, 0.5))) * -120 * u; dx_, dy_, dw, dh = x, y + 0.12 * h + dy, w, 0.17 * h
    glass(cv, dx_, dy_, dw, dh, a_d, accent=RED if t > T["works"] else None, glow=0.6 if t > T["works"] else 0)
    text(cv, "default config", dx_ + 28 * u, dy_ + 46 * u, 26 * u, TXT, a_d, SANS_B); text(cv, "on_disk=False   m=16   shards=1", dx_ + 28 * u, dy_ + 98 * u, 26 * u, MUTE, a_d, MONO, max_w=dw - 56 * u)
    for k, (name, stat, cfg, c) in enumerate(WORKLOADS):
        at = T["conf"] + 0.22 * k; fk = ease(ramp(t, at - 0.25, 0.55)); cy0 = y + (0.36 + 0.215 * k) * h; ch = 0.19 * h
        if fk <= 0: continue
        cv.save(); cv.concat(persp((x, cy0, w, ch), rx=(1 - fk) * 85)); glass(cv, x, cy0, w, ch, fk)
        cv.drawRRect(rr(x + 22 * u, cy0 + 22 * u, ch - 44 * u, ch - 44 * u, 14 * u), paint(c, 0.18 * fk)); text(cv, name[0], x + 22 * u + (ch - 44 * u) / 2, cy0 + ch / 2 + 14 * u, 40 * u, c, fk, SANS_B, align="center")
        text(cv, name, x + ch + 10 * u, cy0 + 50 * u, 30 * u, TXT, fk, SANS_B, max_w=w * 0.5); text(cv, stat, x + ch + 10 * u, cy0 + 90 * u, 22 * u, MUTE, fk, SANS, max_w=w * 0.5)
        bad = ease(ramp(t, T["works"] + 0.15 * k, 0.3)) * (1 - ease(ramp(t, T["wf"] + 0.2 + 0.15 * k, 0.3))); good = ease(ramp(t, T["wf"] + 0.2 + 0.15 * k, 0.3))
        pill(cv, "× default", x + w - 30 * u, cy0 + ch / 2, RED_L, fk * bad, 20 * u, align="right") if False else None
        if bad > 0: pw = font(MONO, 20 * u).measureText("× default") + 24 * u; pill(cv, "× default", x + w - 28 * u - pw, cy0 + ch / 2, RED_L, fk * bad, 20 * u)
        if good > 0: pw = font(MONO, 18 * u).measureText(cfg) + 22 * u; pill(cv, cfg, x + w - 28 * u - pw, cy0 + ch / 2, GREEN, fk * good, 18 * u)
        cv.restore()

ROAD = [("1", "Vectors on disk", RED_L), ("2", "Payload index first", RED_L), ("3", "Quantization", RED_L), ("4", "Sparse index on disk", RED_L),
        ("5", "Batch uploads", TEAL_L), ("6", "Parallel workers", TEAL_L), ("7", "Multiple shards", TEAL_L)]
def S3(cv, t, R):
    """what we'll cover: a roadmap that draws itself; each milestone pops as the line reaches it"""
    x, y, w, h = R; u = min(w / 1408, h / 968, 1.25); t0 = wd(3, "different") + 0.1
    kicker(cv, "WHAT WE'LL COVER", x, y + 24 * u, u, ap(t, t0)); text(cv, "4 options · 3 best practices", x, y + 78 * u, 46 * u, TXT, ap(t, T["opt"]), SANS_B, max_w=w)
    p = skia.Path(); ys = y + 0.55 * h; p.moveTo(x + 0.02 * w, ys)
    for k in range(4): x0 = x + (0.02 + 0.24 * k) * w; amp = 0.10 * h * (1 if k % 2 == 0 else -1); p.cubicTo(x0 + 0.08 * w, ys - amp, x0 + 0.16 * w, ys - amp, x0 + 0.24 * w, ys)
    prog = ramp(t, t0, T["best"] + 0.9 - t0); prog = prog * prog * (3 - 2 * prog)
    beam(cv, p, t, 1.0 if t > t0 else 0.0, VIOL_L, draw=prog, width=4 * u, speed=0.35, n=2)
    fr = [0.06, 0.20, 0.34, 0.48, 0.66, 0.80, 0.94]
    for k, ((num, name, c), f_) in enumerate(zip(ROAD, fr)):
        a = back(ramp(t, t0 + (T["best"] + 0.9 - t0) * f_ * 0.92, 0.45)) if prog >= f_ * 0.98 else 0.0
        if a <= 0: continue
        px, py = point_on(p, f_); r_ = 38 * u * min(1.15, a); am = min(1.0, a)
        cv.drawCircle(px, py, r_ * 1.6, paint(c, 0.25 * am, blur=14)); cv.drawCircle(px, py, r_, paint(CARD0, am)); cv.drawCircle(px, py, r_, paint(c, am, 3 * u))
        text(cv, num, px, py + 13 * u, 34 * u, c, am, SANS_B, align="center")
        above = k % 2 == 0; ly = py - 0.13 * h if above else py + 0.13 * h; lw = 0.19 * w
        glass(cv, px - lw / 2, ly - 34 * u, lw, 68 * u, am, shadow=False); text(cv, name, px, ly + 9 * u, 25 * u, TXT, am, SANS_B, max_w=lw - 24 * u, align="center")
        cv.drawLine(px, py + (-r_ if above else r_), px, ly + (34 * u if above else -34 * u), paint(c, 0.6 * am, 2 * u))
    a_o, a_b = ap(t, T["opt"]), ap(t, T["best"]); gy = y + 0.88 * h
    cv.drawLine(x + 0.04 * w, gy, x + 0.52 * w, gy, paint(RED_L, 0.6 * a_o, 2 * u)); text(cv, "OPTIONS  ·  dense or sparse", x + 0.28 * w, gy + 40 * u, 22 * u, RED_L, a_o, MONO, align="center")
    cv.drawLine(x + 0.60 * w, gy, x + 0.98 * w, gy, paint(TEAL_L, 0.6 * a_b, 2 * u)); text(cv, "BEST PRACTICES  ·  both", x + 0.79 * w, gy + 40 * u, 22 * u, TEAL_L, a_b, MONO, align="center")

def bars_viz(cv, r, t, a, dense, u):
    x, y, w, h = r; n = 40; bw = w / n
    for k in range(n):
        if dense: v = 0.35 + 0.3 * math.sin(k * 1.7 + t * 1.5) * math.cos(k * 0.6 - t) + 0.15 * math.sin(k * 3.1); c = VIOL
        else: v = (0.9 if k in (5, 17, 29) else (0.55 if k == 34 else 0.0)) * (0.9 + 0.1 * math.sin(t * 2 + k)); c = RED
        if v <= 0.01: cv.drawCircle(x + k * bw + bw / 2, y + h - 3 * u, 2 * u, paint(DIM, a)); continue
        bh = abs(v) * h; cv.drawRRect(rr(x + k * bw + bw * 0.18, y + h - bh, bw * 0.64, bh, 2 * u), paint(c, a))
def hnsw3d(cv, r, t, a, g, u):
    """three graph layers in perspective, slowly orbiting; edges draw on with g"""
    x, y, w, h = r; cx, cy = x + w / 2, y + h * 0.52; rd = np.random.default_rng(9); ang = t * 0.25
    layers = [(-0.36, 3), (0.0, 7), (0.36, 14)]; P = []
    for li, (lz, n) in enumerate(layers):
        pts = [(rd.uniform(-1, 1), rd.uniform(-1, 1)) for _ in range(n)]
        def proj(px, py, lz=lz): X = px * math.cos(ang) - py * math.sin(ang); Y = px * math.sin(ang) + py * math.cos(ang); return cx + X * w * 0.36, cy + lz * h + Y * h * 0.10
        quad = [proj(-1.1, -1.1), proj(1.1, -1.1), proj(1.1, 1.1), proj(-1.1, 1.1)]; path = skia.Path(); path.addPoly([skia.Point(*q) for q in quad], True)
        cv.drawPath(path, paint(VIOL, 0.08 * a)); cv.drawPath(path, paint(VIOL_L, 0.25 * a, 1.5 * u)); P.append([proj(*p_) for p_ in pts])
    for li, pts in enumerate(P):
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            if (i / len(pts)) < g: cv.drawLine(*pts[i], *pts[j], paint(VIOL_L, 0.8 * a, 2 * u))
        if li < 2 and g > 0.5:
            for p_ in pts: q = min(P[li + 1], key=lambda z: math.dist(z, p_)); cv.drawLine(*p_, *q, paint(VIOL_L, 0.3 * a, 1.5 * u, blur=0))
        for p_ in pts: cv.drawCircle(*p_, 5 * u, paint(TXT, a))
def S4(cv, t, R):
    """dense vs sparse: live vectors, the HNSW graph, the inverted index, then what each costs"""
    x, y, w, h = R; u = min(w / 1148, h / 968, 1.25); kc = inout(ramp(t, L[7] - 0.1, 0.7))                 # phase C: costs
    kicker(cv, "BEFORE WE START", x, y + 24 * u, u, ap(t, L[4] + 0.2)); text(cv, "Dense vs sparse vectors", x, y + 78 * u, 46 * u, TXT, ap(t, T["diff"]), SANS_B, max_w=w)
    k_dh = inout(ramp(t, T["hnsw"] - 0.6, 0.6)); k_sh = inout(ramp(t, T["sidx"] - 0.6, 0.6))
    def card_rect(left, k_short):
        fx = 0.0 if left else 0.52; full = (x + fx * w, y + 0.13 * h, 0.48 * w, 0.85 * h); short = (x + fx * w, y + 0.13 * h, 0.48 * w, 0.36 * h)
        compact = (x + fx * w, y + 0.12 * h, 0.48 * w, 0.20 * h); return lerpr(lerpr(full, short, k_short), compact, kc)
    for left, at, name, stat, c, k_s in ((True, T["dense"], "Dense vector", "768 dims · every value set", VIOL_L, k_dh), (False, T["sparse"], "Sparse vector", "30,000 dims · ~0.1% set", RED_L, k_sh)):
        a_card = ap(t, L[4] + 0.35 + (0 if left else 0.15), 0.5); a = ap(t, at, 0.5); cx_, cy_, cw_, ch_ = card_rect(left, k_s)
        cy_ += (1 - ease(ramp(t, L[4] + 0.1 + (0 if left else 0.15), 0.6))) * 70 * u          # the cards arrive with the sentence, fill on their word
        glass(cv, cx_, cy_, cw_, ch_, a_card, accent=c if a > 0 else None, glow=0.35 * a)
        if a < 1: text(cv, "?", cx_ + cw_ / 2, cy_ + ch_ / 2 + 40 * u, 120 * u, DIM, a_card * (1 - a), SANS_B, align="center")
        text(cv, name, cx_ + 26 * u, cy_ + 48 * u, 32 * u, c, a, SANS_B, max_w=cw_ - 52 * u); text(cv, stat, cx_ + 26 * u, cy_ + 84 * u, 21 * u, MUTE, a, MONO, max_w=cw_ - 52 * u)
        vh = max(30 * u, ch_ - 140 * u); bars_viz(cv, (cx_ + 26 * u, cy_ + 108 * u, cw_ - 52 * u, min(vh, 0.6 * ch_)), t, a, left, u)
    a_h = ap(t, T["hnsw"]) * (1 - kc)                                              # under dense: the HNSW graph
    if a_h > 0:
        r = (x, y + 0.52 * h + (1 - a_h) * 60 * u, 0.48 * w, 0.46 * h); glass(cv, *r, a_h); text(cv, "HNSW graph", r[0] + 26 * u, r[1] + 44 * u, 26 * u, TXT, a_h, SANS_B)
        hnsw3d(cv, (r[0] + 20 * u, r[1] + 60 * u, r[2] - 40 * u, r[3] - 80 * u), t, a_h, ease(ramp(t, T["hnsw"], 1.2)), u)
    a_i = ap(t, T["sidx"]) * (1 - kc)                                              # under sparse: the inverted index
    if a_i > 0:
        r = (x + 0.52 * w, y + 0.52 * h + (1 - a_i) * 60 * u, 0.48 * w, 0.46 * h); glass(cv, *r, a_i); text(cv, "Inverted index", r[0] + 26 * u, r[1] + 44 * u, 26 * u, TXT, a_i, SANS_B)
        for k, (term, posts) in enumerate((("t12", [4, 9, 31]), ("t77", [4, 12]), ("t301", [9, 18, 77]), ("t5", [2]))):
            ry = r[1] + 80 * u + k * (r[3] - 100 * u) / 4; rh = (r[3] - 100 * u) / 4 - 10 * u
            cv.drawRRect(rr(r[0] + 24 * u, ry, 100 * u, rh, 10 * u), paint(RED, 0.2 * a_i)); text(cv, term, r[0] + 74 * u, ry + rh / 2 + 9 * u, 24 * u, RED_L, a_i, MONO, align="center")
            for q, d in enumerate(posts):
                a_q = a_i * back(ramp(t, T["sidx"] + 0.1 + 0.12 * (k * 3 + q), 0.4)); a_q = min(1.0, a_q)
                if a_q > 0: pill(cv, f"doc {d}", r[0] + 150 * u + q * 120 * u, ry + rh / 2, TXT, a_q, 19 * u)
    if kc > 0:                                                                     # phase C: memory and performance per kind
        for k, (left, v, c, lab, at) in enumerate(((True, 0.78, VIOL_L, "RAM · dense + HNSW", T["mem"]), (False, 0.31, RED_L, "RAM · sparse index", T["mem"] + 0.2))):
            a = ap(t, at) * kc; gx = x + (0.25 if left else 0.75) * w; gy = y + 0.53 * h; r_ = min(0.18 * w, 0.15 * h)
            vv = v * ease(ramp(t, at, 1.4)); gauge(cv, gx, gy + (1 - a) * 50 * u, r_, vv, c, a, lab, f"{int(round(vv * 100))}%", u)
        a_p = ap(t, T["perf"]) * kc; py = y + 0.76 * h
        if a_p > 0:
            glass(cv, x, py, w, 0.10 * h, a_p); text(cv, "search latency", x + 26 * u, py + 0.06 * h, 22 * u, MUTE, a_p, MONO)
            for k, (lab, v, c) in enumerate((("dense  ·  RAM", 0.22, VIOL_L), ("dense  ·  disk", 0.55, AMBER))):
                bx = x + 0.30 * w + k * 0.35 * w; bw = 0.30 * w * v * ease(ramp(t, T["perf"] + 0.15 * k, 0.8))
                cv.drawRRect(rr(bx, py + 0.035 * h, max(4, bw), 0.03 * h, 6 * u), paint(c, a_p)); text(cv, lab, bx, py + 0.092 * h, 19 * u, MUTE, a_p, MONO)
        a_b = ap(t, T["bulk"]) * kc; by = y + 0.89 * h
        if a_b > 0:
            glass(cv, x, by, w, 0.09 * h, a_b, accent=AMBER, glow=0.5); text(cv, "during bulk uploads, both grow together", x + 26 * u, by + 0.058 * h, 26 * u, AMBER, a_b, SANS_B, max_w=w - 52 * u)

def S5(cv, t, R):
    """option 1: the original dense vectors move out of RAM onto disk"""
    x, y, w, h = R; u = min(w / 1148, h / 968, 1.25)
    kicker(cv, "OPTION 01", x, y + 24 * u, u, ap(t, L[9])); text(cv, "Dense vectors on disk", x, y + 78 * u, 46 * u, TXT, ap(t, L[9] + 0.1), SANS_B, max_w=0.6 * w)
    ram = (x, y + 0.13 * h, 0.56 * w, 0.40 * h); ssd = (x, y + 0.58 * h, 0.56 * w, 0.40 * h); a_r, a_s = ap(t, L[9] + 0.2), ap(t, T["storing"])
    glass(cv, *ram, a_r, accent=RED, glow=0.4 * (1 - ease(ramp(t, T["disk"] + 0.4, 0.8)))); text(cv, "RAM", ram[0] + 26 * u, ram[1] + 46 * u, 30 * u, TXT, a_r, SANS_B)
    glass(cv, *ssd, a_s, accent=TEAL_L if t > T["disk"] else None, glow=0.5 if t > T["disk"] else 0); text(cv, "Disk (SSD)", ssd[0] + 26 * u, ssd[1] + 46 * u, 30 * u, TXT, a_s, SANS_B)
    cols, rows = 10, 4; gx0, gw = ram[0] + 26 * u, ram[2] - 52 * u; cell = gw / cols
    for k in range(cols * rows):
        c_, r_ = k % cols, k // cols; x0, y0 = gx0 + c_ * cell, ram[1] + 70 * u + r_ * min(cell, (ram[3] - 90 * u) / rows); x1, y1 = gx0 + c_ * cell, ssd[1] + 70 * u + r_ * min(cell, (ssd[3] - 90 * u) / rows)
        cv.drawRRect(rr(x1 + 3 * u, y1 + 3 * u, cell - 6 * u, min(cell, (ssd[3] - 90 * u) / rows) - 6 * u, 5 * u), paint((255, 255, 255), 0.05 * a_s))
        dk = ease(ramp(t, T["disk"] + 0.025 * k, 0.55)); xx, yy = lerp(x0, x1, dk), lerp(y0, y1, dk) - math.sin(math.pi * dk) * 40 * u
        cv.drawRRect(rr(xx + 3 * u, yy + 3 * u, cell - 6 * u, min(cell, (ram[3] - 90 * u) / rows) - 6 * u, 5 * u), paint(VIOL if dk < 1 else TEAL, a_r * (0.95 if dk < 1 else 0.85)))
    cw = (x + 0.62 * w, y + 0.13 * h, 0.38 * w, 0.48 * h); a_c = ap(t, T["storing"] - 0.2)
    lines = [("client.create_collection(", T["storing"] - 0.2), ('    "docs",', T["storing"]), ("    vectors_config=models.VectorParams(", T["storing"] + 0.2),
             ("        size=768,", T["storing"] + 0.6), ("        distance=models.Distance.COSINE,", T["storing"] + 0.8), ("        on_disk=True,", T["disk"] - 0.5), ("    ),", T["storing"] + 1.3), (")", T["storing"] + 1.4)]
    cv.save(); cv.concat(persp(cw, ry=-8 + 2 * math.sin(t * 0.7))); code_window(cv, *cw, lines, t, a_c, title="1_on_disk.py", hl=(5, ap(t, T["disk"] + 0.1)), cps=60); cv.restore()
    st = (x + 0.62 * w, y + 0.67 * h, 0.38 * w, 0.31 * h); a_t = ap(t, T["storing"] + 0.3)
    glass(cv, *st, a_t); gb = lerp(6.8, 2.1, ease(ramp(t, T["disk"] + 0.2, 1.4))); text(cv, "RAM in use", st[0] + 26 * u, st[1] + 44 * u, 21 * u, MUTE, a_t, MONO)
    text(cv, f"{gb:.1f} GB", st[0] + 26 * u, st[1] + 0.62 * st[3], 64 * u, TXT if gb > 3 else TEAL_L, a_t, SANS_B, max_w=st[2] * 0.6)
    if t > T["disk"] + 0.3: pill(cv, "-69%", st[0] + st[2] - 26 * u - 100 * u, st[1] + 0.52 * st[3], GREEN, ap(t, T["disk"] + 0.9), 24 * u)

SECTIONS = [  # (draw, start, end, how it enters, how it leaves)
    (S1, 0.75, L[2], "rise", "push"), (S2, L[2], L[3], "push", "glide"), (S3, L[3], L[4], "glide", "drop"), (S4, L[4], L[8], "drop", "tilt"), (S5, L[8], 999, "tilt", None)]
TRS = 0.6
def draw_section(cv, fn, t, R, enter, leave, s0, s1):
    ki, ko = ease(ramp(t, s0, TRS)), (ramp(t, s1, TRS) if leave else 0.0)
    if ki <= 0 and enter != "rise": return
    if ko >= 1: return
    x, y, w, h = R; cx, cy = x + w / 2, y + h / 2; a = 1.0; cv.save()
    if enter == "push": s_ = 0.86 + 0.14 * ki; cv.translate(cx, cy); cv.scale(s_, s_); cv.translate(-cx, -cy); a *= ki
    elif enter == "glide": cv.translate((1 - ki) * 0.4 * W, 0); a *= ki
    elif enter == "drop": cv.translate(0, -(1 - back(ramp(t, s0, TRS))) * 0.3 * H); a *= ki
    elif enter == "tilt": cv.concat(persp(R, ry=(1 - ki) * 40)); a *= ki
    ko_e = inout(ko)
    if leave == "push": s_ = 1 + 0.5 * ko_e; cv.translate(cx, cy); cv.scale(s_, s_); cv.translate(-cx, -cy); a *= 1 - ko_e
    elif leave == "glide": cv.translate(-ko_e * 0.4 * W, 0); a *= 1 - ko_e
    elif leave == "drop": cv.translate(0, ko_e * 0.25 * H); a *= 1 - ko_e
    elif leave == "tilt": cv.concat(persp(R, ry=-ko_e * 40)); a *= 1 - ko_e
    if a < 0.999: cv.saveLayerAlpha(None, int(255 * a))
    fn(cv, t, R)
    if a < 0.999: cv.restore()
    cv.restore()

KEYS = None
def frame(t, face_im):
    surf = skia.Surface(W, H); cv = surf.getCanvas(); cv.drawImage(background(), 0, 0)
    face, rad, z, bord, R, vis, shows = layout_at(KEYS, t)
    if vis > 0.004:
        if vis < 0.999: cv.saveLayerAlpha(None, int(255 * vis))
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(R[0] - 40, R[1] - 40, R[2] + 80, R[3] + 80))   # content stays in its region, clear of the face
        for fn, s0, s1, en, lv in SECTIONS:
            if s0 - 0.01 <= t < s1 + TRS: draw_section(cv, fn, t, R, en, lv, s0, s1)
        cv.restore()
        if vis < 0.999: cv.restore()
    fx, fy, fw, fh = face
    if fx < W and fx + fw > 0 and fw > 4:                                        # the presenter
        if bord > 0.01: cv.drawRRect(rr(fx, fy + 18, fw, fh, rad), paint((0, 0, 0), 0.5 * bord, blur=26))
        im = E.face_crop(face_im, int(fw), int(fh), z).convert("RGBA"); arr = np.ascontiguousarray(np.asarray(im)); img = skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType)
        cv.save(); cv.clipRRect(rr(fx, fy, int(fw), int(fh), rad), skia.ClipOp.kIntersect, True); cv.drawImage(img, fx, fy); cv.restore()
        if bord > 0.01:
            b = skia.Paint(AntiAlias=True); b.setStyle(skia.Paint.kStroke_Style); b.setStrokeWidth(2)
            b.setShader(skia.GradientShader.MakeLinear([skia.Point(fx, fy), skia.Point(fx + fw, fy + fh)], [col(VIOL_L, 0.9 * bord), col(RED_L, 0.6 * bord)])); cv.drawRRect(rr(fx, fy, fw, fh, rad), b)
    lt = ease(ramp(t, T["first"] - 0.35, 0.5)) * (1 - inout(ramp(t, L[9] - 0.2, 0.45)))   # the chapter lower third over the full face
    if lt > 0:
        lx, ly, lw, lh = M + 30, H - M - 190, 760, 150; cv.save(); cv.clipRect(skia.Rect.MakeXYWH(lx - 40, ly - 40, (lw + 80) * lt, lh + 80))
        glass(cv, lx, ly, lw, lh, 1.0, accent=RED, glow=0.6); cv.drawRect(skia.Rect.MakeXYWH(lx, ly + 22, 6, lh - 44), paint(RED))
        text(cv, "OPTION 01", lx + 36, ly + 52, 22, RED_L, 1, MONO); text(cv, "Store dense vectors on disk", lx + 36, ly + 108, 46, TXT, 1, SANS_B, max_w=lw - 70); cv.restore()
    return Image.fromarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGBA"), shows

def plan(p, t0, t1):
    global KEYS
    KEYS = layout_keys(p.look); hide = E.hidden_spans(p.look); cuts = sorted({t0, t1} | {x for a, b in hide for x in (a, b) if t0 < x < t1}); S_ = []
    for a, b in zip(cuts, cuts[1:]):
        on = not any(x < b and y > a for x, y in hide)
        S_.append(dict(t0=a, t1=b, kind="graphic", shows_face=on, draw=lambda lt, dur, ctx: frame(ctx["t"], ctx["face"])[0], tr="cut", _hidden=False))
    sfx = [(k[0] - 0.05, E.whoosh(0.025, 0.4)) for k in KEYS[1:] if t0 <= k[0] < t1] + [(s[1] - 0.05, E.whoosh(0.035, 0.45)) for s in SECTIONS[1:] if t0 <= s[1] < t1]
    sfx += [(x - 0.25, E.tone(0.05, 1500, 1000, 0.022)) for x in (T["up"], T["qd"], T["store"], T["pay"], T["idx"], T["bg"], T["single"], T["conf"], T["dense"], T["sparse"], T["hnsw"], T["sidx"], T["mem"], T["perf"], T["disk"]) if t0 <= x < t1]
    return S_, sfx

if __name__ == "__main__":
    a = sys.argv[1:]; p = SF.project()
    if a[:1] == ["stills"]:
        ts = [float(x) for x in a[1:]]; S_, sfx = plan(p, 0, max(ts) + 2); r = E.Renderer(p, S_, 0, p.dur, OUT, sfx, NAVY); print(r.stills(ts, OUT.replace(".mp4", "_sheet.png"), cols=4))
    else:
        t0, t1 = (float(a[0]), float(a[1])) if len(a) >= 2 else (0.0, p.dur)
        S_, sfx = plan(p, t0, t1); E.Renderer(p, S_, t0, t1, OUT if (t0, t1) == (0.0, p.dur) else OUT.replace(".mp4", f"_{int(t0)}-{int(t1)}.mp4"), sfx, NAVY).render()
