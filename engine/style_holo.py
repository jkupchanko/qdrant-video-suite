"""HOLOGRAM STAGE: the presenter, cut out of his room, stands in a dark space while holographic glass panels
materialize around him on his words.

The presenter is the cut frame with the rembg matte (matte.py) as alpha, rim-lit in cyan, standing on a
perspective floor grid. Panels are drawn flat and mapped into 3D (turned toward him, in perspective), with
scanlines, HUD corner brackets and a little flicker. Each section has its own arrangement and its own
entrance: unfold (S1), rotate-in (S2), an arc of milestones over his head (S3), slide in from depth (S4),
unfold with a scan (S5). Panels collapse at the end of their section, and the camera pans him across the
stage between sections. In a look-away he beams out and the panels move to the centre.

  MATTE_CUT=v2 python matte.py 0 41.5      (once: the cutout matte for the sample)
  python style_holo.py 0 41                sample -> out/holo_0-41.mp4
  python style_holo.py stills 2 6 20       contact sheet
"""
import os, sys, json, math, numpy as np, skia
from PIL import Image, ImageFilter
import engine as E
import style_full as SF
import style_launch as LN
W, H = E.W, E.H; TR = E.TR
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\holo.mp4"; MATTE = r"C:\Users\ADMIN\camera_audit\edit\full_edit\matte_v2_0-41.mp4"
font, col, paint, text, ramp, ease, inout, back, lerp = LN.font, LN.col, LN.paint, LN.text, LN.ramp, E.ease, E.inout, E.back, LN.lerp
SANS, SANS_B, MONO = LN.SANS, LN.SANS_B, LN.MONO
CY, CY_L, WHT, VIO, RED_L, AMB, GRN, MUTE = (79, 209, 230), (170, 240, 255), (240, 250, 255), (170, 160, 255), (255, 135, 146), (255, 200, 120), (110, 240, 170), (120, 170, 190)
T, L, wd = LN.T, LN.L, LN.wd
def ap(t, at, d=0.45): return ease(ramp(t, at - 0.25, d))

# ---------------------------------------------------------------- stage: background, camera, presenter
_bg = None
def stage_bg():
    global _bg
    if _bg is None:
        s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col((3, 7, 14)))
        cv.drawCircle(W / 2, -260, 1000, paint((30, 90, 140), 0.38, blur=230)); cv.drawCircle(W / 2, 1180, 700, paint((79, 209, 230), 0.08, blur=200))
        _bg = s.makeImageSnapshot()
    return _bg
PCX = [(0.0, 900), (L[2], 1260), (L[3], 960), (L[8], 600)]                    # where the presenter stands, per section
def presenter_x(t):
    x = PCX[0][1]
    for (t0, v), (_, v_prev) in zip(PCX[1:], PCX[:-1]): x = lerp(x, v, inout(ramp(t, t0 - 0.1, 0.8))) if t >= t0 - 0.1 else x
    return x
def floor(cv, t, cam):
    vx, vy = W / 2 - cam * 0.25, 500
    for k in range(-22, 23): x_b = vx + k * 260 - (cam * 0.9) % 260; cv.drawLine(vx + (x_b - vx) * 0.15, vy, x_b, H, paint(CY, 0.16, 1.5))
    for k in range(14): y = vy + (H - vy) * ((k + (t * 0.15) % 1) / 14) ** 1.9; cv.drawLine(0, y, W, y, paint(CY, 0.05 + 0.10 * (y - vy) / (H - vy), 1.5))
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, vy - 40), skia.Point(0, vy + 160)], [col((3, 7, 14), 1), col((3, 7, 14), 0)])); cv.drawRect(skia.Rect(0, vy - 40, W, vy + 160), p)
PS = 0.75; HEAD_Y = 470; FOOT = 851                                              # he stands inside the stage; the torso fades into the floor
def presenter(cv, t, face_im, cx, beam_out=0.0):
    """the cutout with a cyan rim; beam_out 0..1 dissolves him in scan bands"""
    if beam_out >= 1: return
    m = E.clip(MATTE).frame(t).convert("L"); a = np.asarray(m).astype(np.float32) / 255
    rgb = np.asarray(face_im.convert("RGB")).astype(np.float32)
    if beam_out > 0:
        band = ((np.arange(H)[:, None] % 10) / 10.0) > beam_out; a = a * band * (1 - beam_out); rgb = rgb * (1 - beam_out) + np.array(CY) * beam_out
    y0_ = HEAD_Y - 500 * PS; fade = np.clip((FOOT - (y0_ + np.arange(H) * PS)) / 200.0, 0, 1); a = a * fade[:, None]
    small = Image.fromarray((a * 255).astype(np.uint8)).resize((480, 270)).filter(ImageFilter.GaussianBlur(9)); g = np.asarray(small.resize((W, H))).astype(np.float32) / 255
    glow = np.zeros((H, W, 4), np.uint8); glow[..., :3] = CY; glow[..., 3] = (np.clip(g * 1.4 - a * 0.6, 0, 1) * 150).astype(np.uint8)
    cut = np.dstack([rgb.clip(0, 255).astype(np.uint8), (a * 255).astype(np.uint8)])
    w_, h_ = int(W * PS), int(H * PS); x0, y0 = cx - 960 * PS, HEAD_Y - 500 * PS
    cv.drawOval(skia.Rect(cx - 380, FOOT - 70, cx + 380, FOOT + 40), paint(CY, 0.22 * (1 - beam_out), blur=40))
    for arr in (glow, cut): cv.drawImageRect(skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kRGBA_8888_ColorType), skia.Rect.MakeXYWH(x0, y0, w_, h_), skia.SamplingOptions(skia.FilterMode.kLinear))

# ---------------------------------------------------------------- holographic panels
def quad_of(cx, cy, w, h, ry, sy=1.0, f=1700.0):
    pts = []
    for (px, py) in ((-w / 2, -h / 2 * sy), (w / 2, -h / 2 * sy), (w / 2, h / 2 * sy), (-w / 2, h / 2 * sy)):
        a = math.radians(ry); X, Z = px * math.cos(a), -px * math.sin(a); s = f / (f + Z); pts.append(skia.Point(cx + X * s, cy + py * s))
    return pts
def holo_panel(cv, t, cx, cy, w, h, ry, a, draw, title=None, accent=CY, sy=1.0, seed=0):
    if a <= 0.01 or sy <= 0.01: return
    a = a * (0.93 + 0.07 * math.sin(t * 37 + seed * 3.1))
    s = skia.Surface(int(w), int(h)); c = s.getCanvas(); c.clear(skia.Color(0, 0, 0, 0))
    p = skia.Paint(AntiAlias=True); p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, h)], [col((40, 120, 160), 0.34), col((20, 60, 100), 0.18)])); c.drawRoundRect(skia.Rect(0, 0, w, h), 18, 18, p)
    for y in range(0, int(h), 5): c.drawLine(0, y, w, y, paint(CY_L, 0.035, 1))
    c.drawRoundRect(skia.Rect(1.5, 1.5, w - 1.5, h - 1.5), 18, 18, paint(accent, 0.55, 2))
    for (x0, y0, dx, dy) in ((14, 14, 1, 1), (w - 14, 14, -1, 1), (w - 14, h - 14, -1, -1), (14, h - 14, 1, -1)):
        c.drawLine(x0, y0, x0 + 30 * dx, y0, paint(accent, 1, 3)); c.drawLine(x0, y0, x0, y0 + 30 * dy, paint(accent, 1, 3))
    if title: text(c, title, 34, 58, 26, accent, 1, MONO)
    draw(c, w, h)
    sweep = (t * 0.6 + seed * 0.37) % 1.6                                                 # a slow scan line across the glass
    if sweep < 1: c.drawRect(skia.Rect(0, sweep * h - 2, w, sweep * h + 2), paint(CY_L, 0.18))
    img = s.makeImageSnapshot(); q = quad_of(cx, cy, w, h, ry, sy)
    path = skia.Path(); path.addPoly(q, True); cv.drawPath(path, paint(accent, 0.35 * a, 6, blur=18))
    m = skia.Matrix(); m.setPolyToPoly([skia.Point(0, 0), skia.Point(w, 0), skia.Point(w, h), skia.Point(0, h)], q)
    cv.save(); cv.concat(m); cv.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), paint((255, 255, 255), a)); cv.restore()

def code_lines(c, x, y, lines, t, size=30, cps=55, hl=None):
    f = font(MONO, size)
    for k, (s_, ts) in enumerate(lines):
        n = len(s_) if ts is None else (0 if t < ts else min(len(s_), int((t - ts) * cps))); xx = x; yy = y + k * size * 1.55; shown = 0
        if hl is not None and hl[0] == k and hl[1] > 0: c.drawRect(skia.Rect(x - 14, yy - size * 1.0, x + 900, yy + size * 0.45), paint(CY, 0.18 * hl[1]))
        for v, colr in LN.tokens(s_):
            if shown >= n: break
            part = v[: n - shown]; c.drawString(part, xx, yy, f, paint(colr)); xx += f.measureText(part); shown += len(v)
def bars(c, x, y, w, h, t, dense):
    n = 34; bw = w / n
    for k in range(n):
        v = (0.35 + 0.3 * math.sin(k * 1.7 + t * 1.5) * math.cos(k * 0.6 - t) + 0.15 * math.sin(k * 3.1)) if dense else ((0.9 if k in (5, 17, 26) else 0.0) * (0.9 + 0.1 * math.sin(t * 2 + k)))
        if v <= 0.02: c.drawCircle(x + k * bw + bw / 2, y + h - 3, 2.5, paint(MUTE)); continue
        c.drawRect(skia.Rect(x + k * bw + bw * 0.2, y + h - abs(v) * h, x + k * bw + bw * 0.8, y + h), paint(VIO if dense else RED_L))
def graph(c, x, y, w, h, g, seed=4, n=16, colr=VIO):
    rd = np.random.default_rng(seed); pts = [(x + rd.uniform(0.05, 0.95) * w, y + rd.uniform(0.08, 0.92) * h) for _ in range(n)]
    edges = [(i, j) for i in range(n) for j in range(i + 1, n) if math.dist(pts[i], pts[j]) < w * 0.24]
    for (i, j) in edges[: int(len(edges) * g)]: c.drawLine(*pts[i], *pts[j], paint(colr, 0.85, 2.5))
    for p_ in pts: c.drawCircle(*p_, 7, paint(WHT))
def gauge(c, cx, cy, r, v, colr, lab):
    rect = skia.Rect(cx - r, cy - r, cx + r, cy + r); c.drawArc(rect, 135, 270, False, paint(CY, 0.15, 16)); c.drawArc(rect, 135, 270 * v, False, paint(colr, 1, 16))
    text(c, f"{int(round(v * 100))}%", cx, cy + 16, 54, WHT, 1, SANS_B, align="center"); text(c, lab, cx, cy + r * 0.9, 24, CY_L, 1, MONO, align="center")

# ---------------------------------------------------------------- what is on stage, per section
def unfold(t, at, d=0.5): return ease(ramp(t, at - 0.25, d))
def collapse(t, at, d=0.35): return 1 - ease(ramp(t, at, d))
def panels(cv, t, shift):
    P = []                                                                         # (cx, cy, w, h, ry, alpha, sy, draw, title, accent)
    if t < L[2] + 0.4:                                                             # S1, presenter right of centre: unfold
        out = collapse(t, L[2] - 0.15)
        n = 1_000_000 * ease(ramp(t, T["large"], 6.5))
        def d_count(c, w, h): text(c, LN.counter(n), 34, 175, 104, WHT, 1, SANS_B, max_w=w - 68); text(c, "points uploaded", 34, 225, 26, CY_L, 1, MONO)
        def d_code(c, w, h): code_lines(c, 34, 110, [("points = load_points(", None), ('    "data.jsonl")', None), ("client.upload_points(", None), ('    "docs", points,', None), ("    batch_size=256)", None)], t, 28, hl=(2, ap(t, T["qd"])))
        P += [(300, 300, 470, 270, 22, out, unfold(t, T["large"]), d_count, "POINTS UPLOADED", CY), (300, 650, 470, 360, 22, out, unfold(t, T["up"]), d_code, "bulk_upload.py", CY)]
        fill = min(1.0, n / 1_000_000)
        def d_qd(c, w, h):
            LN.logo(c, 34, 82, 50); text(c, "Qdrant", 100, 120, 44, WHT, 1, SANS_B); text(c, "vectors", 34, 175, 24, CY_L, 1, MONO)
            for k in range(26): c.drawRect(skia.Rect(34 + k * 22, 192, 34 + k * 22 + 15, 226), paint(VIO if k < 26 * fill else (60, 90, 120)))
        P.append((1560, 190, 600, 260, -22, out, unfold(t, T["qd"]), d_qd, None, RED_L))
        def d_pay(c, w, h): code_lines(c, 34, 120, [('{"category": "news",', None), (' "lang": "en", "year": 2024}', None)], t, 28)
        def d_idx(c, w, h): graph(c, 34, 80, w - 68, h - 110, ease(ramp(t, T["idx"], 1.3)))
        def d_bg(c, w, h):
            for k, (nm, job) in enumerate((("optimizer", "merging segments"), ("wal", "flushing"), ("indexer", "building HNSW"))):
                yy = 115 + k * 52; c.drawArc(skia.Rect(34, yy - 22, 60, yy + 4), (t * 400 + k * 120) % 360, 260, False, paint(GRN, ap(t, T["bg"] + 0.25 * k), 3.5))
                text(c, nm, 76, yy, 26, GRN, ap(t, T["bg"] + 0.25 * k), MONO); text(c, job, 250, yy, 26, CY_L, ap(t, T["bg"] + 0.25 * k), MONO)
        P += [(1560, 470, 600, 230, -22, out, unfold(t, T["pay"]), d_pay, "PAYLOADS", AMB), (1560, 760, 600, 300, -22, out, unfold(t, T["idx"]), d_idx, "INDEXES  ·  HNSW", VIO),
              (300, 960, 470, 220, 22, out, unfold(t, T["bg"]), d_bg, "BACKGROUND", GRN)]
    if L[2] - 0.2 < t < L[3] + 0.4:                                                # S2, presenter right: rotate-in, stacked left
        out = collapse(t, L[3] - 0.15); a_in = ap(t, L[2] + 0.2)
        def d_def(c, w, h): text(c, "default config", 34, 120, 40, WHT, 1, SANS_B); text(c, "on_disk=False   m=16   shards=1", 34, 180, 30, CY_L, 1, MONO, max_w=w - 68)
        P.append((470, 210, 760, 230, 16, out * a_in, 1.0, d_def, "ONE CONFIG?", RED_L if t > T["works"] else CY))
        for k, (name, stat, cfg, colr) in enumerate(LN.WORKLOADS):
            at = T["conf"] + 0.22 * k; ry = 16 + (1 - ease(ramp(t, at - 0.25, 0.55))) * 80
            good = ease(ramp(t, T["wf"] + 0.2 + 0.15 * k, 0.3)); bad = ease(ramp(t, T["works"] + 0.15 * k, 0.3)) * (1 - good)
            def d_w(c, w, h, name=name, stat=stat, cfg=cfg, good=good, bad=bad):
                text(c, name, 34, 70, 36, WHT, 1, SANS_B); text(c, stat, 34, 112, 24, CY_L, 1, MONO)
                if bad > 0: text(c, "× default", w - 34, 70, 28, RED_L, bad, MONO, align="right")
                if good > 0: text(c, cfg, w - 34, 112, 24, GRN, good, MONO, align="right", max_w=w * 0.45)
            P.append((470, 430 + k * 190, 760, 160, ry, out * ap(t, at, 0.5), 1.0, d_w, None, colr))
    if L[3] - 0.2 < t < L[4] + 0.4:                                                # S3, presenter centred: an arc of milestones over his head
        out = collapse(t, L[4] - 0.15); t0 = wd(3, "different") - 0.1
        def d_ttl(c, w, h): text(c, "4 options", 34, 110, 46, RED_L, 1, SANS_B); text(c, "3 best practices", 34, 170, 46, (110, 230, 210), 1, SANS_B)
        P.append((330, 900, 520, 230, 20, out * ap(t, T["opt"]), unfold(t, T["opt"]), d_ttl, "WHAT WE'LL COVER", CY))
        arc_draw = ease(ramp(t, t0, T["best"] + 0.9 - t0))
        for k, (num, name, colr) in enumerate(LN.ROAD):
            th = math.radians(198 + k * 24); ax, ay = 960 + 800 * math.cos(th), 720 + 640 * math.sin(th); f_ = k / 6        # the arc clears his head
            a = (back(ramp(t, t0 + (T["best"] + 0.9 - t0) * f_ * 0.92, 0.45)) if arc_draw >= f_ * 0.98 else 0.0) * out
            def d_r(c, w, h, num=num, name=name, colr=colr): c.drawCircle(52, h / 2, 30, paint(colr, 1, 4)); text(c, num, 52, h / 2 + 12, 32, colr, 1, SANS_B, align="center"); text(c, name, 100, h / 2 + 11, 28, WHT, 1, SANS_B, max_w=w - 120)
            P.append((ax, ay, 360, 92, (ax - 960) / 800 * 30, min(1.0, a), 1.0, d_r, None, RED_L if k < 4 else (110, 230, 210)))
    if L[4] - 0.2 < t < L[8] + 0.4:                                                # S4, presenter centred: panels slide in from depth either side
        out = collapse(t, L[8] - 0.15); kc = ease(ramp(t, L[7] - 0.1, 0.6))
        def depth(at): k = ease(ramp(t, at - 0.3, 0.6)); return k
        def d_dense(c, w, h): text(c, "768 dims · every value set", 34, 110, 26, CY_L, 1, MONO); bars(c, 34, 140, w - 68, h - 180, t, True)
        def d_sparse(c, w, h): text(c, "30,000 dims · ~0.1% set", 34, 110, 26, CY_L, 1, MONO); bars(c, 34, 140, w - 68, h - 180, t, False)
        kd, ks = depth(T["dense"]), depth(T["sparse"])
        P += [(320 + (1 - kd) * 200, 330, 560, 380, 24 - (1 - kd) * 30, out * kd, 1.0, d_dense, "DENSE VECTOR", VIO), (1600 - (1 - ks) * 200, 330, 560, 380, -24 + (1 - ks) * 30, out * ks, 1.0, d_sparse, "SPARSE VECTOR", RED_L)]
        def d_hnsw(c, w, h):
            for li in range(3): c.drawLine(40, 110 + li * 90, w - 40, 110 + li * 90, paint(CY, 0.25, 1.5))
            graph(c, 34, 80, w - 68, h - 110, ease(ramp(t, T["hnsw"], 1.2)), seed=9, n=18)
        def d_inv(c, w, h):
            for k, (term, posts) in enumerate((("t12", "4 · 9 · 31"), ("t77", "4 · 12"), ("t301", "9 · 18 · 77"))):
                yy = 120 + k * 64; a_k = ap(t, T["sidx"] + 0.15 * k); text(c, term, 34, yy, 30, RED_L, a_k, MONO); text(c, "->  doc " + posts, 140, yy, 30, WHT, a_k, MONO)
        kh, ki = depth(T["hnsw"]) * (1 - kc), depth(T["sidx"]) * (1 - kc)
        P += [(320, 800, 560, 340, 24, out * kh, 1.0, d_hnsw, "HNSW GRAPH", VIO), (1600, 800, 560, 340, -24, out * ki, 1.0, d_inv, "INVERTED INDEX", RED_L)]
        def d_g1(c, w, h): gauge(c, w / 2, h / 2 + 30, 110, 0.78 * ease(ramp(t, T["mem"], 1.4)), VIO, "RAM · dense + HNSW")
        def d_g2(c, w, h): gauge(c, w / 2, h / 2 + 30, 110, 0.31 * ease(ramp(t, T["mem"] + 0.2, 1.4)), RED_L, "RAM · sparse index")
        kg = depth(T["mem"]) * kc
        P += [(320, 800, 560, 340, 24, out * kg, 1.0, d_g1, "MEMORY", VIO), (1600, 800, 560, 340, -24, out * kg, 1.0, d_g2, "MEMORY", RED_L)]
    if t > L[8] - 0.2:                                                             # S5, presenter left: unfold with a scan
        def d_title(c, w, h): text(c, "OPTION 01", 40, 110, 34, RED_L, 1, MONO); text(c, "Store dense vectors", 40, 200, 64, WHT, 1, SANS_B, max_w=w - 80); text(c, "on disk", 40, 280, 64, WHT, 1, SANS_B)
        kt = unfold(t, T["first"]) * collapse(t, L[9] - 0.25)
        P.append((1400, 470, 820, 340, -18, kt, kt, d_title, None, RED_L))
        dk = [ease(ramp(t, T["disk"] + 0.03 * k, 0.5)) for k in range(24)]
        def d_ram(c, w, h):
            for k in range(24):
                if dk[k] < 0.5: c.drawRect(skia.Rect(34 + (k % 12) * 62, 90 + (k // 12) * 62, 34 + (k % 12) * 62 + 50, 90 + (k // 12) * 62 + 50), paint(VIO, 1 - 2 * dk[k]))
            gb = lerp(6.8, 2.1, ease(ramp(t, T["disk"] + 0.2, 1.4))); text(c, f"{gb:.1f} GB in use", w - 34, h - 26, 30, RED_L if gb > 3 else GRN, 1, MONO, align="right")
        def d_ssd(c, w, h):
            for k in range(24):
                c.drawRect(skia.Rect(34 + (k % 12) * 62, 90 + (k // 12) * 62, 34 + (k % 12) * 62 + 50, 90 + (k // 12) * 62 + 50), paint(CY, 0.25, 1.5))
                if dk[k] > 0.5: c.drawRect(skia.Rect(34 + (k % 12) * 62, 90 + (k // 12) * 62, 34 + (k % 12) * 62 + 50, 90 + (k // 12) * 62 + 50), paint(GRN, 2 * dk[k] - 1))
        def d_code(c, w, h): code_lines(c, 34, 110, [("models.VectorParams(", T["storing"] - 0.1), ("    size=768,", T["storing"] + 0.3), ("    on_disk=True,", T["disk"] - 0.5), (")", T["storing"] + 0.6)], t, 30, cps=60, hl=(2, ap(t, T["disk"] + 0.1)))
        ka = unfold(t, L[9] + 0.1)
        P += [(1420, 220, 860, 280, -18, ka, ka, d_ram, "RAM", RED_L), (1420, 540, 860, 280, -18, unfold(t, T["storing"]), unfold(t, T["storing"]), d_ssd, "DISK  ·  SSD", GRN),
              (1420, 860, 860, 300, -18, unfold(t, T["storing"] - 0.2), unfold(t, T["storing"] - 0.2), d_code, "1_on_disk.py", CY)]
    for k, (cx, cy, w, h, ry, a, sy, dr, ttl, acc) in enumerate(P): holo_panel(cv, t, cx + shift, cy, w, h, ry, a, dr, ttl, acc, sy, seed=k)

def beam(cv, t):
    """S1: points travel from the code panel over his head into the Qdrant panel"""
    a = ap(t, T["up"] + 0.3) * (1 - ramp(t, L[2] - 0.3, 0.3))
    if a <= 0: return
    p = skia.Path(); p.moveTo(520, 600); p.cubicTo(720, 60, 1100, 60, 1270, 190)
    LN.beam(cv, p, t, a, CY_L, draw=ease(ramp(t, T["up"] + 0.3, 0.8)), width=3.5, speed=0.7 + 0.9 * ease(ramp(t, T["large"], 0.5)), n=2 + int(5 * ease(ramp(t, T["large"], 0.5))))

def frame(t, face_im, hide):
    surf = skia.Surface(W, H); cv = surf.getCanvas(); cv.drawImage(stage_bg(), 0, 0)
    out_k = 0.0
    for a, b in hide:                                                               # a look-away: he beams out, then back in
        if a <= t < b + TR: out_k = max(out_k, min(ease(ramp(t, a, TR)), 1 - ease(ramp(t, b, TR))))
    cx = presenter_x(t); shift = -out_k * (cx - 960) * 0.7 if out_k > 0 else 0.0           # with him gone, the panels move toward the centre
    floor(cv, t, cx - 960); panels(cv, t, shift); beam(cv, t); presenter(cv, t, face_im, cx, out_k)
    return Image.fromarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGBA")

def plan(p, t0, t1):
    hide = E.hidden_spans(p.look); cuts = sorted({t0, t1} | {x for a, b in hide for x in (a, b) if t0 < x < t1}); S_ = []
    for a, b in zip(cuts, cuts[1:]):
        on = not any(x < b and y > a for x, y in hide)
        S_.append(dict(t0=a, t1=b, kind="graphic", shows_face=on, draw=lambda lt, dur, ctx: frame(ctx["t"], ctx["face"], hide), tr="cut", _hidden=False))
    sfx = [(x - 0.25, E.tone(0.12, 600, 1400, 0.02, noise=0.2)) for x in (T["up"], T["large"], T["qd"], T["pay"], T["idx"], T["bg"], T["single"], T["opt"], T["dense"], T["sparse"], T["hnsw"], T["sidx"], T["mem"], T["first"], T["storing"], T["disk"]) if t0 <= x < t1]
    sfx += [(c[0] - 0.1, E.whoosh(0.03, 0.6)) for c in PCX[1:] if t0 <= c[0] < t1]
    return S_, sfx

if __name__ == "__main__":
    a = sys.argv[1:]; p = SF.project()
    if a[:1] == ["stills"]:
        ts = [float(x) for x in a[1:]]; S_, sfx = plan(p, 0, max(ts) + 2); r = E.Renderer(p, S_, 0, p.dur, OUT, sfx, (3, 7, 14)); print(r.stills(ts, OUT.replace(".mp4", "_sheet.png"), cols=4))
    else:
        t0, t1 = (float(a[0]), float(a[1])) if len(a) >= 2 else (0.0, p.dur)
        S_, sfx = plan(p, t0, t1); E.Renderer(p, S_, t0, t1, OUT if (t0, t1) == (0.0, p.dur) else OUT.replace(".mp4", f"_{int(t0)}-{int(t1)}.mp4"), sfx, (3, 7, 14)).render()
