"""SYSTEM DESIGN: line-icon architecture diagrams, the way ByteByteGo and TechWorld with Nana explain
(see coding_audit/report.md).

A dark charcoal canvas, thin line icons in teal and yellow (client, Qdrant server, database, RAM, SSD, gear,
graph, users), small white labels, and dashed arrows with data dots flowing along them. Each diagram builds
piece by piece on the spoken words, then clears for the next. Diagrams are drawn large, filling the frame.
The presenter is in a small round cam top right, hidden whenever he looks away.

  python style_sysdesign.py 0 41            sample -> out/sysdesign_0-41.mp4
  python style_sysdesign.py stills 2 6 20   contact sheet
"""
import os, sys, json, math, numpy as np, skia
from PIL import Image, ImageDraw
import engine as E
import style_full as SF
W, H = E.W, E.H
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\sysdesign.mp4"
FONTS = r"C:\Users\ADMIN\camera_audit\fonts"; LOGO = r"C:\Users\ADMIN\camera_audit\assets\qdrant-brandmark-red.png"
BG, BLOB, TEAL, YEL, WHITE, MUTE, RED, VIOL = (0x1B, 0x1D, 0x22), (0x24, 0x27, 0x2E), (0x4F, 0xD1, 0xC5), (0xF5, 0xC5, 0x42), (0xEC, 0xEE, 0xF2), (0x8B, 0x92, 0xA3), (0xE8, 0x4A, 0x5F), (0x9B, 0x8C, 0xFF)
_tf = {}
def font(size, name="Inter[opsz,wght].ttf"):
    if name not in _tf: _tf[name] = skia.Typeface.MakeFromFile(os.path.join(FONTS, name))
    return skia.Font(_tf[name], size)
def col(c, a=1.0): return skia.Color(c[0], c[1], c[2], int(255 * max(0, min(1, a))))
def stroke(c, a=1.0, w=3.0, dash=None):
    p = skia.Paint(AntiAlias=True, Color=col(c, a)); p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(w); p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if dash: p.setPathEffect(skia.DashPathEffect.Make(dash, 0))
    return p
def fill(c, a=1.0): return skia.Paint(AntiAlias=True, Color=col(c, a))
def label(cv, s, x, y, size=24, c=WHITE, a=1.0, name="Inter[opsz,wght].ttf"):
    f = font(size, name); cv.drawString(s, x - f.measureText(s) / 2, y, f, fill(c, a))
def ramp(t, a, d=0.45): return max(0.0, min(1.0, (t - a) / d))
ease, inout, back = E.ease, E.inout, E.back
WORDS = json.load(open(r"C:\Users\ADMIN\camera_audit\styles\out\v2_words.json"))["pieces"]
def wd(i, w, nth=0):
    hits = [t for x, t in WORDS[i]["words"] if x.lower().strip(",.?!").startswith(w.lower())]; return hits[min(nth, len(hits) - 1)]
T = dict(up=wd(0, "uploading"), large=wd(0, "large"), qd=wd(0, "qdrant"), store=wd(0, "store"), pay=wd(1, "payloads"), idx=wd(1, "indexes"), bg=wd(1, "much"),
         single=wd(2, "single"), conf=wd(2, "configuration"), works=wd(2, "workflows"), opt=wd(3, "options"), best=wd(3, "best"), dense=wd(4, "dense"), sparse=wd(4, "sparse"),
         hnsw=wd(5, "hnsw"), sidx=wd(6, "completely"), mem=wd(7, "memory"), perf=wd(7, "performance"), first=wd(8, "first"), storing=wd(9, "storing"), disk=wd(9, "disk"))
L = [WORDS[i]["t0"] for i in range(10)]

# ---------------------------------------------------------------- line icons (centred at x, y; s = size in px)
def pop(cv, x, y, a):                                                          # every element scales in from 85% as it fades in
    cv.save(); k = 0.85 + 0.15 * a; cv.translate(x, y); cv.scale(k, k); cv.translate(-x, -y)
def i_laptop(cv, x, y, s, c, a):
    pop(cv, x, y, a); cv.drawRoundRect(skia.Rect(x - s * 0.5, y - s * 0.38, x + s * 0.5, y + s * 0.22), 8, 8, stroke(c, a)); cv.drawLine(x - s * 0.62, y + s * 0.34, x + s * 0.62, y + s * 0.34, stroke(c, a, 4))
    f = font(s * 0.28, "FiraCode[wght].ttf"); cv.drawString("</>", x - f.measureText("</>") / 2, y + s * 0.02, f, fill(c, a)); cv.restore()
def i_server(cv, x, y, s, c, a, logo=False):
    pop(cv, x, y, a)
    for k in range(3):
        yy = y - s * 0.5 + k * s * 0.36; cv.drawRoundRect(skia.Rect(x - s * 0.42, yy, x + s * 0.42, yy + s * 0.28), 6, 6, stroke(c, a)); cv.drawCircle(x + s * 0.28, yy + s * 0.14, 4, fill(c, a))
        cv.drawLine(x - s * 0.3, yy + s * 0.14, x + s * 0.05, yy + s * 0.14, stroke(c, a * 0.7, 2.5))
    if logo:
        img = skia.Image.open(LOGO); r = s * 0.22; cv.drawImageRect(img, skia.Rect(x - s * 0.42 - r * 2.4, y - s * 0.62, x - s * 0.42 - r * 0.4, y - s * 0.62 + r * 2), skia.SamplingOptions(skia.FilterMode.kLinear), fill(WHITE, a))
    cv.restore()
def i_db(cv, x, y, s, c, a):
    pop(cv, x, y, a); w, h = s * 0.45, s * 0.6; cv.drawOval(skia.Rect(x - w, y - h - s * 0.12, x + w, y - h + s * 0.12), stroke(c, a))
    for yy in (0, h * 0.95): cv.drawArc(skia.Rect(x - w, y - h - s * 0.12 + yy, x + w, y - h + s * 0.12 + yy), 0, 180, False, stroke(c, a))
    cv.drawLine(x - w, y - h, x - w, y - h + h * 0.95, stroke(c, a)); cv.drawLine(x + w, y - h, x + w, y - h + h * 0.95, stroke(c, a)); cv.restore()
def i_tag(cv, x, y, s, c, a):
    pop(cv, x, y, a); p = skia.Path(); p.moveTo(x - s * 0.4, y - s * 0.3); p.lineTo(x + s * 0.15, y - s * 0.3); p.lineTo(x + s * 0.45, y); p.lineTo(x + s * 0.15, y + s * 0.3); p.lineTo(x - s * 0.4, y + s * 0.3); p.close()
    cv.drawPath(p, stroke(c, a)); cv.drawCircle(x + s * 0.1, y, s * 0.06, stroke(c, a, 2.5)); cv.restore()
def i_graph(cv, x, y, s, c, a, layers=False):
    pop(cv, x, y, a); rd = np.random.default_rng(3); pts = [(x + rd.uniform(-0.45, 0.45) * s, y + rd.uniform(-0.38, 0.38) * s) for _ in range(9)]
    if layers:
        pts = []
        for li, (n, yy) in enumerate(((2, -0.38), (4, 0.0), (7, 0.38))):
            row = [(x + (j - (n - 1) / 2) * s * 0.9 / max(1, n - 1), y + yy * s) for j in range(n)]; pts += row
            for j in range(n - 1): cv.drawLine(*row[j], *row[j + 1], stroke(c, a * 0.8, 2.2))
            cv.drawLine(x - s * 0.55, y + yy * s, x + s * 0.55, y + yy * s, stroke(MUTE, a * 0.3, 1.5, [6, 6]))
        for p_ in pts: cv.drawCircle(*p_, 6, fill(c, a))
    else:
        for i in range(9):
            for j in (i + 1, i + 3):
                if j < 9: cv.drawLine(*pts[i], *pts[j], stroke(c, a * 0.8, 2.2))
        for p_ in pts: cv.drawCircle(*p_, 6, fill(c, a))
    cv.restore()
def i_gear(cv, x, y, s, c, a, t):
    pop(cv, x, y, a); cv.save(); cv.translate(x, y); cv.rotate((t * 50) % 360); p = skia.Path()
    for k in range(16):
        r = s * (0.42 if k % 2 == 0 else 0.32); ang = 2 * math.pi * k / 16; (p.moveTo if k == 0 else p.lineTo)(r * math.cos(ang), r * math.sin(ang))
    p.close(); cv.drawPath(p, stroke(c, a)); cv.drawCircle(0, 0, s * 0.13, stroke(c, a)); cv.restore(); cv.restore()
def i_ram(cv, x, y, s, c, a):
    pop(cv, x, y, a); cv.drawRoundRect(skia.Rect(x - s * 0.55, y - s * 0.22, x + s * 0.55, y + s * 0.18), 6, 6, stroke(c, a))
    for k in range(4): cv.drawRect(skia.Rect(x - s * 0.45 + k * s * 0.24, y - s * 0.12, x - s * 0.3 + k * s * 0.24, y + s * 0.08), stroke(c, a, 2.5))
    for k in range(10): cv.drawLine(x - s * 0.5 + k * s * 0.11, y + s * 0.18, x - s * 0.5 + k * s * 0.11, y + s * 0.28, stroke(c, a, 2.5))
    cv.restore()
def i_ssd(cv, x, y, s, c, a):
    pop(cv, x, y, a); cv.drawRoundRect(skia.Rect(x - s * 0.5, y - s * 0.3, x + s * 0.5, y + s * 0.3), 10, 10, stroke(c, a)); cv.drawCircle(x + s * 0.32, y + s * 0.16, 5, fill(c, a))
    f = font(s * 0.2, "FiraCode[wght].ttf"); cv.drawString("SSD", x - s * 0.36, y + s * 0.05, f, fill(c, a)); cv.restore()
def i_users(cv, x, y, s, c, a):
    pop(cv, x, y, a)
    for dx in (-0.22, 0.22): cv.drawCircle(x + dx * s, y - s * 0.12, s * 0.13, stroke(c, a)); cv.drawArc(skia.Rect(x + dx * s - s * 0.22, y + s * 0.05, x + dx * s + s * 0.22, y + s * 0.45), 180, 180, False, stroke(c, a))
    cv.restore()
def i_chat(cv, x, y, s, c, a):
    pop(cv, x, y, a); cv.drawRoundRect(skia.Rect(x - s * 0.45, y - s * 0.32, x + s * 0.45, y + s * 0.2), 12, 12, stroke(c, a)); p = skia.Path(); p.moveTo(x - s * 0.2, y + s * 0.2); p.lineTo(x - s * 0.3, y + s * 0.38); p.lineTo(x, y + s * 0.2); cv.drawPath(p, stroke(c, a))
    for k in range(3): cv.drawCircle(x - s * 0.18 + k * s * 0.18, y - s * 0.06, 4, fill(c, a))
    cv.restore()
def i_bars(cv, x, y, s, c, a):
    pop(cv, x, y, a)
    for k, hh in enumerate((0.3, 0.55, 0.42, 0.7)): cv.drawRect(skia.Rect(x - s * 0.4 + k * s * 0.22, y + s * 0.35 - hh * s, x - s * 0.26 + k * s * 0.22, y + s * 0.35), stroke(c, a))
    cv.drawLine(x - s * 0.48, y + s * 0.35, x + s * 0.5, y + s * 0.35, stroke(c, a)); cv.restore()
def flow(cv, pts, t, a, c=YEL, rate=3, speed=0.6, dots=True):
    """a dashed arrow along pts with data dots travelling it"""
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    cv.drawPath(p, stroke(MUTE, 0.9 * a, 2.5, [10, 8]))
    (x1, y1), (x2, y2) = pts[-2], pts[-1]; ang = math.atan2(y2 - y1, x2 - x1)
    for s_ in (-1, 1): cv.drawLine(x2, y2, x2 - 16 * math.cos(ang + s_ * 0.45), y2 - 16 * math.sin(ang + s_ * 0.45), stroke(MUTE, a, 2.5))
    if not dots or a <= 0: return
    seg = [math.dist(u, v) for u, v in zip(pts, pts[1:])]; Ltot = sum(seg)
    for k in range(int(rate)):
        d = (((t * speed) + k / rate) % 1) * Ltot
        for (u, v), sl in zip(zip(pts, pts[1:]), seg):
            if d <= sl: q = (u[0] + (v[0] - u[0]) * d / sl, u[1] + (v[1] - u[1]) * d / sl); cv.drawCircle(*q, 8, fill(c, a)); break
            d -= sl
def chip(cv, s, x, y, c=YEL, a=1.0, size=26):
    f = font(size, "FiraCode[wght].ttf"); w = f.measureText(s) + 30; cv.drawRoundRect(skia.Rect(x - w / 2, y - size, x + w / 2, y + size * 0.55), 8, 8, fill((0x2A, 0x2D, 0x35), a))
    cv.drawRoundRect(skia.Rect(x - w / 2, y - size, x + w / 2, y + size * 0.55), 8, 8, stroke(c, a, 2)); cv.drawString(s, x - w / 2 + 15, y, f, fill(c, a))
def strip(cv, x, y, n, on, c, a, cell=34):
    for k in range(n):
        lit = k in on; cv.drawRect(skia.Rect(x + k * cell, y, x + k * cell + cell - 5, y + cell - 5), fill(c, a * (1 if lit else 0.0)) if lit else stroke(MUTE, a * 0.6, 2))

# ---------------------------------------------------------------- the diagrams, one per idea, building on the words
def appear(t, at, d=0.4): return ease(ramp(t, at - 0.25, d))                 # an element lands just before its word
def scene(cv, t):
    cv.clear(col(BG))
    for k, (bx, by, br) in enumerate(((300, 900, 380), (1600, 200, 320), (1100, 1000, 260))): cv.drawCircle(bx, by, br, fill(BLOB, 0.9))   # the soft shapes behind
    f = font(22); cv.drawString("Bulk Uploads in Qdrant", 40, 52, f, fill(MUTE)); cv.drawLine(40, 66, 300, 66, stroke(MUTE, 0.5, 1.5))
    k_ = 0 if t < L[2] - 0.2 else 1 if t < L[3] - 0.2 else 2 if t < L[4] - 0.2 else 3 if t < L[8] - 0.2 else 4
    sc, dy, cx = ((1.12, 30, 960), (1.15, 20, 960), (1.0, 60, 900), (0.98, 70, 940), (1.1, 30, 940))[k_]   # each diagram scaled to fill the frame, clear of the cam
    cv.save(); cv.translate(cx, 560 + dy); cv.scale(sc, sc); cv.translate(-960, -560)
    scene_body(cv, t)
    cv.restore()

def scene_body(cv, t):
    if t < L[2] - 0.2:                                                            # 1: client -> Qdrant, and what it does besides storing
        a0 = 1 - ramp(t, L[2] - 0.5, 0.3)
        i_laptop(cv, 330, 470, 210, TEAL, appear(t, T["up"]) * a0); label(cv, "your app", 330, 610, 28, WHITE, appear(t, T["up"]) * a0)
        i_server(cv, 980, 470, 230, TEAL, appear(t, T["qd"]) * a0, logo=True); label(cv, "Qdrant", 980, 630, 30, WHITE, appear(t, T["qd"]) * a0)
        rate = 2 + 6 * ease(ramp(t, T["large"] - 0.2, 0.6)); flow(cv, [(470, 470), (840, 470)], t, appear(t, T["up"] + 0.2) * a0, rate=rate)
        if t > T["large"] - 0.3: chip(cv, "1,000,000 points", 655, 420, YEL, appear(t, T["large"]) * a0)
        i_db(cv, 1520, 500, 200, YEL, appear(t, T["store"]) * a0); label(cv, "vectors", 1520, 640, 28, WHITE, appear(t, T["store"]) * a0); flow(cv, [(1110, 470), (1390, 470)], t, appear(t, T["store"] + 0.2) * a0, rate=2, dots=True)
        for k, (fn, name, at) in enumerate(((i_tag, "payloads", T["pay"]), (i_graph, "indexes", T["idx"]), (i_gear, "background work", T["bg"]))):
            x = 640 + k * 340; y = 860; a = appear(t, at) * a0
            flow(cv, [(980, 640), (980, 720), (x, 720), (x, 790)], t, a, c=TEAL, rate=1, speed=0.5)
            (fn(cv, x, y, 120, YEL, a, t) if fn is i_gear else fn(cv, x, y, 120, YEL, a)); label(cv, name, x, y + 100, 26, WHITE, a)
    elif t < L[3] - 0.2:                                                          # 2: one configuration does not fit every workload
        a0 = ramp(t, L[2] - 0.2, 0.3) * (1 - ramp(t, L[3] - 0.5, 0.3))
        cv.drawRoundRect(skia.Rect(200, 380, 620, 640), 18, 18, stroke(TEAL, appear(t, T["single"]) * a0)); label(cv, "one configuration", 410, 470, 34, WHITE, appear(t, T["single"]) * a0)
        chip(cv, "on_disk=?  m=?  shards=?", 410, 560, YEL, appear(t, T["conf"]) * a0, 24)
        for k, (fn, name) in enumerate(((i_chat, "RAG app"), (i_bars, "analytics"), (i_users, "multi-tenant SaaS"))):
            y = 250 + k * 280; a = appear(t, T["conf"] + 0.3 + 0.25 * k) * a0
            flow(cv, [(620, 510), (980, y + 20)], t, a, c=TEAL, rate=1, dots=False); fn(cv, 1150, y, 150, TEAL, a); label(cv, name, 1150, y + 120, 28, WHITE, a)
            if t > T["works"] - 0.3: x_ = 1360; cv.drawLine(x_ - 30, y - 30, x_ + 30, y + 30, stroke(RED, appear(t, T["works"] + 0.15 * k), 7)); cv.drawLine(x_ + 30, y - 30, x_ - 30, y + 30, stroke(RED, appear(t, T["works"] + 0.15 * k), 7))
    elif t < L[4] - 0.2:                                                          # 3: the options and the best practices
        a0 = ramp(t, L[3] - 0.2, 0.3) * (1 - ramp(t, L[4] - 0.5, 0.3))
        label(cv, "options", 520, 230, 40, YEL, appear(t, T["opt"]) * a0); label(cv, "best practices", 1300, 230, 40, TEAL, appear(t, T["best"]) * a0)
        opts = [(i_ssd, "vectors on disk"), (i_tag, "payload index first"), (i_ram, "quantization"), (i_graph, "sparse index on disk")]
        for k, (fn, name) in enumerate(opts):
            a = appear(t, T["opt"] + 0.12 * k) * a0; y = 330 + k * 170; fn(cv, 330, y, 100, YEL, a); f2 = font(32); cv.drawString(f"{k + 1}. {name}", 420, y + 12, f2, fill(WHITE, a))
        for k, (fn, name) in enumerate(((i_bars, "batch your uploads"), (i_gear, "parallel workers"), (i_server, "multiple shards"))):
            a = appear(t, T["best"] + 0.12 * k) * a0; y = 330 + k * 170; (fn(cv, 1120, y, 100, TEAL, a, t) if fn is i_gear else fn(cv, 1120, y, 100, TEAL, a)); f2 = font(32); cv.drawString(name, 1210, y + 12, f2, fill(WHITE, a))
    elif t < L[8] - 0.2:                                                          # 4: dense and sparse, two indexes, two memory profiles
        a0 = ramp(t, L[4] - 0.2, 0.3) * (1 - ramp(t, L[8] - 0.5, 0.3))
        ad, as_ = appear(t, T["dense"]) * a0, appear(t, T["sparse"]) * a0
        label(cv, "dense vector", 480, 230, 36, VIOL, ad); strip(cv, 200, 260, 16, set(range(16)), VIOL, ad); label(cv, "every value set", 480, 350, 24, MUTE, ad)
        label(cv, "sparse vector", 1360, 230, 36, RED, as_); strip(cv, 1080, 260, 16, {2, 9, 13}, RED, as_); label(cv, "a few values set", 1360, 350, 24, MUTE, as_)
        ah = appear(t, T["hnsw"]) * a0; flow(cv, [(480, 380), (480, 470)], t, ah, c=VIOL, rate=1, speed=0.8); i_graph(cv, 480, 620, 260, VIOL, ah, layers=True); label(cv, "HNSW graph", 480, 800, 32, WHITE, ah)
        ai = appear(t, T["sidx"]) * a0; flow(cv, [(1360, 380), (1360, 470)], t, ai, c=RED, rate=1, speed=0.8)
        for k, (term, post) in enumerate((("t12", "4, 9, 31"), ("t77", "4, 12"), ("t301", "9, 18, 77"))):
            y = 520 + k * 76; cv.drawRoundRect(skia.Rect(1170, y, 1270, y + 58), 8, 8, stroke(RED, ai)); f3 = font(26, "FiraCode[wght].ttf"); cv.drawString(term, 1188, y + 39, f3, fill(WHITE, ai))
            cv.drawLine(1270, y + 29, 1320, y + 29, stroke(MUTE, ai, 2.5)); cv.drawString(post, 1335, y + 39, f3, fill(WHITE, ai))
        label(cv, "inverted index", 1360, 800, 32, WHITE, ai)
        am, ap = appear(t, T["mem"]) * a0, appear(t, T["perf"]) * a0
        for (x, mem_v, sp_v) in ((480, 0.85, 0.85), (1360, 0.35, 0.6)):
            cv.drawRoundRect(skia.Rect(x - 220, 860, x + 220, 884), 12, 12, fill((0x2A, 0x2D, 0x35), am)); cv.drawRoundRect(skia.Rect(x - 220, 860, x - 220 + 440 * mem_v * am, 884), 12, 12, fill(RED if mem_v > 0.7 else TEAL, am))
            f4 = font(22); cv.drawString("memory", x - 220, 850, f4, fill(MUTE, am)); cv.drawString("search speed", x - 220, 935, f4, fill(MUTE, ap))
            cv.drawRoundRect(skia.Rect(x - 220, 945, x + 220, 969), 12, 12, fill((0x2A, 0x2D, 0x35), ap)); cv.drawRoundRect(skia.Rect(x - 220, 945, x - 220 + 440 * sp_v * ap, 969), 12, 12, fill(TEAL, ap))
    else:                                                                         # 5: option 1, the original vectors move from RAM to disk
        a0 = ramp(t, L[8] - 0.2, 0.3)
        f5 = font(46); s5 = "Option 1: dense vectors on disk"; cv.drawString(s5, (W - f5.measureText(s5)) / 2, 200, f5, fill(WHITE, appear(t, T["first"]) * a0))
        i_server(cv, 360, 560, 230, TEAL, a0, logo=True); label(cv, "Qdrant", 360, 720, 30, WHITE, a0)
        i_ram(cv, 1000, 420, 220, RED, a0); label(cv, "RAM", 1000, 520, 30, WHITE, a0); i_ssd(cv, 1000, 760, 230, VIOL, appear(t, T["storing"]) * a0); label(cv, "disk", 1000, 880, 30, WHITE, appear(t, T["storing"]) * a0)
        flow(cv, [(500, 520), (850, 430)], t, a0, c=YEL, rate=2, dots=t < T["disk"]); flow(cv, [(1000, 480), (1000, 670)], t, appear(t, T["disk"]) * a0, c=VIOL, rate=4, speed=0.9)
        if t > T["disk"] - 0.4: chip(cv, "VectorParams(on_disk=True)", 1450, 640, YEL, appear(t, T["disk"]), 28)
        rf = 1 - 0.65 * ease(ramp(t, T["disk"] + 0.2, 1.0)); cv.drawRoundRect(skia.Rect(1240, 400, 1660, 424), 12, 12, fill((0x2A, 0x2D, 0x35), a0)); cv.drawRoundRect(skia.Rect(1240, 400, 1240 + 420 * rf, 424), 12, 12, fill(RED if rf > 0.6 else TEAL, a0))
        cv.drawString("RAM in use", 1240, 390, font(22), fill(MUTE, a0))

CAM_R = 130; CAM_C = (W - 50 - CAM_R, 50 + CAM_R)
def frame(t, face_im, show_face):
    surf = skia.Surface(W, H); cv = surf.getCanvas(); scene(cv, t)
    fr = Image.fromarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGBA")
    if show_face:
        d = 2 * CAM_R; f = E.face_crop(face_im, d, d, 1.3); m = Image.new("L", (d, d), 0); ImageDraw.Draw(m).ellipse([0, 0, d - 1, d - 1], fill=255); f.putalpha(m)
        ring = Image.new("RGBA", (d + 10, d + 10), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse([0, 0, d + 9, d + 9], fill=TEAL + (255,))
        fr.alpha_composite(ring, (CAM_C[0] - CAM_R - 5, CAM_C[1] - CAM_R - 5)); fr.paste(f, (CAM_C[0] - CAM_R, CAM_C[1] - CAM_R), f)
    return fr

def plan(p, t0, t1):
    hide = E.hidden_spans(p.look); cuts = sorted({t0, t1} | {x for a, b in hide for x in (a, b) if t0 < x < t1}); S_ = []
    for a, b in zip(cuts, cuts[1:]):
        on = not any(x < b and y > a for x, y in hide)
        S_.append(dict(t0=a, t1=b, kind="graphic", shows_face=on, draw=(lambda on_: lambda lt, dur, ctx: frame(ctx["t"], ctx["face"], on_))(on), tr="cut", _hidden=False))
    sfx = [(x - 0.25, E.tone(0.05, 1300, 900, 0.025)) for x in (T["up"], T["qd"], T["store"], T["pay"], T["idx"], T["bg"], T["dense"], T["sparse"], T["hnsw"], T["sidx"], T["disk"]) if t0 <= x < t1]
    return S_, sfx

if __name__ == "__main__":
    a = sys.argv[1:]; p = SF.project()
    if a[:1] == ["stills"]:
        ts = [float(x) for x in a[1:]]; S_, sfx = plan(p, 0, max(ts) + 2); r = E.Renderer(p, S_, 0, p.dur, OUT, sfx, BG); print(r.stills(ts, OUT.replace(".mp4", "_sheet.png"), cols=4))
    else:
        t0, t1 = (float(a[0]), float(a[1])) if len(a) >= 2 else (0.0, p.dur)
        S_, sfx = plan(p, t0, t1); E.Renderer(p, S_, t0, t1, OUT if (t0, t1) == (0.0, p.dur) else OUT.replace(".mp4", f"_{int(t0)}-{int(t1)}.mp4"), sfx, BG).render()
