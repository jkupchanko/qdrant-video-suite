"""CHARACTER WORLD: ideas as characters in an illustrated world, the way Kurzgesagt and TED-Ed explain
(see paradigm_audit/report.md).

Vectors are round creatures with big eyes that bob as they walk, blink and react. Payloads are backpacks.
The index is a librarian in glasses. RAM is a hall with a face that sweats when it gets crowded, and disk is
a calm vault below it. A new scene every four or five seconds, revealed with an iris wipe, each with a slow
camera drift and parallax hills under a starry gradient sky. The presenter is part of the world: while he is
on the lens his face fills the moon; when he looks away it is only a moon.

  python style_world.py 0 41             sample -> out/world_0-41.mp4
  python style_world.py stills 2 6 20    contact sheet
"""
import os, sys, json, math, numpy as np, skia
from PIL import Image
import engine as E
import style_full as SF
W, H = E.W, E.H
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\world.mp4"
FONTS = r"C:\Users\ADMIN\camera_audit\fonts"; LOGO = r"C:\Users\ADMIN\camera_audit\assets\qdrant-brandmark-red.png"
SKY0, SKY1, HILL0, HILL1, GROUND = (0x14, 0x10, 0x3A), (0x5B, 0x2A, 0x86), (0x2A, 0x1E, 0x5C), (0x3B, 0x26, 0x70), (0x23, 0x1A, 0x4A)
DENSE, SPARSE, TAGC, GOLD, WHITE, INK, HOT, MINT = (0x7B, 0x6C, 0xFF), (0xFF, 0x7A, 0x6E), (0x2E, 0xD8, 0xB6), (0xFF, 0xC8, 0x57), (0xF6, 0xF4, 0xFF), (0x1A, 0x14, 0x33), (0xDC, 0x24, 0x4C), (0x7D, 0xF3, 0xD0)
_tf = {}
def font(name, size):
    if name not in _tf: _tf[name] = skia.Typeface.MakeFromFile(os.path.join(FONTS, name))
    return skia.Font(_tf[name], size)
def col(c, a=1.0): return skia.Color(c[0], c[1], c[2], int(255 * max(0, min(1, a))))
def paint(c, a=1.0, stroke=0, blur=0):
    p = skia.Paint(AntiAlias=True, Color=col(c, a))
    if stroke: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke); p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p
def text(cv, s, x, y, size, c=WHITE, a=1.0, name="Fredoka[wdth,wght].ttf", align="center"):
    f = font(name, size); w = f.measureText(s); x = x - w / 2 if align == "center" else x
    cv.drawString(s, x, y, f, paint(c, a))
def ramp(t, a, d=0.5): return max(0.0, min(1.0, (t - a) / d))
ease, inout, back = E.ease, E.inout, E.back
WORDS = json.load(open(r"C:\Users\ADMIN\camera_audit\styles\out\v2_words.json"))["pieces"]
def wd(i, w, nth=0):
    hits = [t for x, t in WORDS[i]["words"] if x.lower().strip(",.?!").startswith(w.lower())]; return hits[min(nth, len(hits) - 1)]
_logo = None
def logo():
    global _logo
    if _logo is None: _logo = skia.Image.open(LOGO)
    return _logo

# ---------------------------------------------------------------- the cast
def creature(cv, x, y, r, body, t, ph=0.0, walk=False, look=(0.3, 0.0), mood=0.6, sparse=False, tag=False, glasses=False, sweat=0.0, scale=1.0):
    r *= scale; bob = abs(math.sin(t * 7 + ph)) * r * 0.18 if walk else math.sin(t * 2 + ph) * r * 0.04; y -= bob
    cv.drawOval(skia.Rect(x - r * 0.75, y + bob + r * 0.82, x + r * 0.75, y + bob + r * 1.05), paint((0, 0, 0), 0.28, blur=r * 0.08))
    for s in (-1, 1): cv.drawLine(x + s * r * 0.35, y + r * 0.7, x + s * r * 0.4, y + r * 0.95 + bob * 0.5, paint(INK, 1, r * 0.16))   # little legs
    if sparse:                                                              # a sparse vector: mostly empty, a few values
        cv.drawCircle(x, y, r, paint((0xFF, 0xE6, 0xE2))); cv.drawCircle(x, y, r * 0.93, paint(body, 1, r * 0.14))
        for k, (dx, dy) in enumerate([(-0.45, 0.35), (0.5, 0.2), (0.05, 0.55)]): cv.drawCircle(x + dx * r, y + dy * r, r * 0.11, paint(body))
    else:
        sh = skia.GradientShader.MakeRadial(skia.Point(x - r * 0.35, y - r * 0.45), r * 1.5, [col(tuple(min(255, c + 70) for c in body)), col(body), col(tuple(int(c * 0.6) for c in body))], [0.0, 0.55, 1.0])
        p = skia.Paint(AntiAlias=True); p.setShader(sh); cv.drawCircle(x, y, r, p)
    if tag:                                                                 # payload: a little backpack
        cv.drawRoundRect(skia.Rect(x + r * 0.62, y - r * 0.15, x + r * 1.12, y + r * 0.5), r * 0.12, r * 0.12, paint(TAGC)); cv.drawLine(x + r * 0.7, y - r * 0.1, x + r * 0.4, y - r * 0.5, paint(INK, 0.8, r * 0.07))
    blink = (math.sin(t * 1.7 + ph * 3) > 0.985)
    for s in (-1, 1):
        ex, ey = x + s * r * 0.33, y - r * 0.15
        if blink: cv.drawLine(ex - r * 0.18, ey, ex + r * 0.18, ey, paint(INK, 1, r * 0.08)); continue
        cv.drawOval(skia.Rect(ex - r * 0.22, ey - r * 0.27, ex + r * 0.22, ey + r * 0.27), paint(WHITE))
        cv.drawCircle(ex + look[0] * r * 0.1, ey + look[1] * r * 0.1, r * 0.11, paint(INK))
        if glasses: cv.drawCircle(ex, ey, r * 0.3, paint(INK, 1, r * 0.07))
    if glasses: cv.drawLine(x - r * 0.05, y - r * 0.17, x + r * 0.05, y - r * 0.17, paint(INK, 1, r * 0.07))
    m = skia.Path(); mw = r * 0.22; my = y + r * 0.32; m.moveTo(x - mw, my); m.quadTo(x, my + (mood - 0.5) * r * 0.5, x + mw, my); cv.drawPath(m, paint(INK, 1, r * 0.08))
    if sweat > 0:
        for k in range(2): cv.drawCircle(x + r * (0.85 + 0.1 * k), y - r * 0.6 + ((t * 2 + k * 0.5) % 1) * r * 0.9, r * 0.09, paint((0x9F, 0xE8, 0xFF), sweat))

def truck(cv, x, y, s, t, body=(0x3E, 0x9B, 0xFF), riders=3, ph=0.0):
    cv.drawRoundRect(skia.Rect(x, y - 120 * s, x + 260 * s, y), 18 * s, 18 * s, paint(body)); cv.drawRoundRect(skia.Rect(x + 260 * s, y - 85 * s, x + 340 * s, y), 18 * s, 18 * s, paint(tuple(int(c * 0.8) for c in body)))
    cv.drawRoundRect(skia.Rect(x + 275 * s, y - 72 * s, x + 325 * s, y - 40 * s), 6 * s, 6 * s, paint((0xBF, 0xE6, 0xFF)))
    for k in range(riders): creature(cv, x + (45 + k * 80) * s, y - 125 * s, 32, DENSE, t, ph + k, scale=s)
    for wx in (60, 210, 300): cv.drawCircle(x + wx * s, y + 4 * s, 26 * s, paint(INK)); cv.drawCircle(x + wx * s, y + 4 * s, 10 * s, paint((0x8A, 0x84, 0xA8)))

def building(cv, x, y, w, h, body, t, lit=1.0, face=None, sweat=0.0, label=None):
    sh = skia.GradientShader.MakeLinear([skia.Point(x, y - h), skia.Point(x, y)], [col(tuple(min(255, c + 40) for c in body)), col(body)])
    p = skia.Paint(AntiAlias=True); p.setShader(sh); cv.drawRoundRect(skia.Rect(x, y - h, x + w, y), 24, 24, p)
    for i in range(int(w // 70)):
        for j in range(int((h - 60) // 80)):
            on = ((i * 7 + j * 3) % 5 != 0); cv.drawRoundRect(skia.Rect(x + 25 + i * 70, y - h + 40 + j * 80, x + 65 + i * 70, y - h + 90 + j * 80), 6, 6, paint(GOLD if on else INK, (0.9 * lit if on else 0.5)))
    if face is not None:                                                   # a building with a mood
        fx, fy = x + w / 2, y - h * 0.45; cv.drawRoundRect(skia.Rect(fx - w * 0.38, fy - 70, fx + w * 0.38, fy + 90), 30, 30, paint(INK, 0.85))
        for s in (-1, 1): cv.drawOval(skia.Rect(fx + s * 70 - 30, fy - 35, fx + s * 70 + 30, fy + 25), paint(WHITE)); cv.drawCircle(fx + s * 70, fy - 2, 13, paint(INK))
        m = skia.Path(); m.moveTo(fx - 50, fy + 55); m.quadTo(fx, fy + 55 + (face - 0.5) * 60, fx + 50, fy + 55); cv.drawPath(m, paint(WHITE, 1, 9))
        if sweat > 0:
            for k in range(3): cv.drawCircle(fx + w * 0.42, fy - 60 + ((t * 1.5 + k * 0.33) % 1) * 160, 12, paint((0x9F, 0xE8, 0xFF), sweat))
    if label: text(cv, label, x + w / 2, y + 52, 40, WHITE, 1)

def sky(cv, t, cam):
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)], [col(SKY0), col(SKY1)]); p = skia.Paint(); p.setShader(sh); cv.drawRect(skia.Rect(0, 0, W, H), p)
    r = np.random.default_rng(3)
    for k in range(90):
        x, y, s = r.uniform(0, W), r.uniform(0, H * 0.55), r.uniform(1, 3); a = 0.4 + 0.6 * abs(math.sin(t * r.uniform(0.5, 2) + k))
        cv.drawCircle((x - cam * 0.05) % W, y, s, paint(WHITE, a))
def hills(cv, cam, y0=760):
    for k, (c, amp, off, par) in enumerate([(HILL0, 70, 0, 0.15), (HILL1, 50, 300, 0.3)]):
        path = skia.Path(); path.moveTo(0, H)
        for x in range(0, W + 41, 40): path.lineTo(x, y0 + k * 60 - amp * math.sin((x + cam * par + off) / 260))
        path.lineTo(W, H); path.close(); cv.drawPath(path, paint(c))
def ground(cv, y=900): cv.drawRect(skia.Rect(0, y, W, H), paint(GROUND))

MOON = (1725, 195, 150)                                                     # the top-right corner is kept clear for it in every scene
def moon(cv, t, glow=1.0):
    x, y, r = MOON; cv.drawCircle(x, y, r * 1.35, paint((0xB9, 0xA8, 0xFF), 0.18 * glow, blur=40)); cv.drawCircle(x, y, r + 10, paint((0xE8, 0xE2, 0xFF)))
    cv.drawCircle(x, y, r, paint((0xD6, 0xCF, 0xF5)))
    for dx, dy, cr in ((-60, -40, 30), (50, 30, 22), (-20, 70, 16)): cv.drawCircle(x + dx, y + dy, cr, paint((0xB8, 0xAE, 0xE0)))

# ---------------------------------------------------------------- the scenes, keyed to the spoken words
T = dict(up=wd(0, "uploading"), large=wd(0, "large"), qd=wd(0, "qdrant"), store=wd(0, "store"), pay=wd(1, "payloads"), idx=wd(1, "indexes"), bg=wd(1, "much"),
         conf=wd(2, "configuration"), work=wd(2, "workflows"), opt=wd(3, "options"), best=wd(3, "best"), dense=wd(4, "dense"), sparse=wd(4, "sparse"),
         hnsw=wd(5, "hnsw"), sidx=wd(6, "completely"), mem=wd(7, "memory"), perf=wd(7, "performance"), bulk=wd(7, "bulk"), first=wd(8, "first"), storing=wd(9, "storing"), disk=wd(9, "disk"))
SCENES = [WORDS[i]["t0"] for i in range(10)]                          # one scene per spoken line, revealed with an iris wipe

def s_upload(cv, t, lt):
    cam = lt * 60; sky(cv, t, cam); hills(cv, cam); ground(cv)
    building(cv, 1180 - cam * 0.5, 900, 420, 560, (0x3B, 0x2F, 0x8F), t, lit=0.3 + 0.7 * ease(ramp(t, T["qd"] - 0.2, 0.5)))
    lg = ease(ramp(t, T["qd"] - 0.2, 0.4)); cv.drawImageRect(logo(), skia.Rect(1330 - cam * 0.5, 380 - 60 * lg, 1450 - cam * 0.5, 500 - 60 * lg), skia.SamplingOptions(skia.FilterMode.kLinear), paint(WHITE, lg)) if lg > 0 else None
    n = 1 + int(3 * ease(ramp(t, T["large"] - 0.2, 0.6)))
    for k in range(n):
        x = -420 + (lt * 260 + k * 330) % 1500; truck(cv, x, 930 + (k % 2) * 40, 0.75, t, riders=3, ph=k)
    if t > T["store"] - 0.2:
        for k in range(6):
            a = ease(ramp(t, T["store"] - 0.2 + 0.12 * k, 0.6)); creature(cv, 1050 + k * 30 - cam * 0.5 + 120 * a, 860 - 220 * math.sin(math.pi * a) * (1 - a * 0.3), 34, DENSE, t, k, walk=True)
    text(cv, "uploading a large amount of data", 560, 160, 54, WHITE, ease(ramp(t, T["large"] - 0.3, 0.5)))

def s_hall(cv, t, lt):
    cam = lt * 40; cv.drawRect(skia.Rect(0, 0, W, H), paint((0x2B, 0x22, 0x5E)))
    for k in range(4):                                                      # shelves of the collection
        y = 300 + k * 170; cv.drawRoundRect(skia.Rect(140 - cam, y + 52, 1380 - cam, y + 70), 8, 8, paint((0x5A, 0x48, 0xA8)))
        for j in range(9): creature(cv, 200 + j * 135 - cam, y, 40, DENSE, t, j + k * 9, tag=t > T["pay"] - 0.2 + 0.03 * (j + k * 9), look=(math.sin(t + j), 0))
    n_lines = int(30 * ease(ramp(t, T["idx"] - 0.2, 1.4)))
    for k in range(n_lines):                                                # the librarian ties neighbours together: the index
        a, b = (k * 7) % 36, (k * 7 + 10) % 36; ax, ay = 200 + (a % 9) * 135 - cam, 300 + (a // 9) * 170; bx, by = 200 + (b % 9) * 135 - cam, 300 + (b // 9) * 170
        cv.drawLine(ax, ay, bx, by, paint(GOLD, 0.55, 3))
    if t > T["idx"] - 0.5: creature(cv, 1500 - cam * 0.3, 640, 70, (0xFF, 0xB3, 0x47), t, 3, glasses=True, mood=0.8, look=(-0.8, 0))
    if t > T["bg"] - 0.3:                                                   # much more in the background: gears turning
        for k, (gx, gy, gr) in enumerate(((1560, 760, 70), (1700, 840, 50), (1630, 930, 36))):
            cv.save(); cv.translate(gx - cam * 0.2, gy); cv.rotate((t * 60 * (1 if k % 2 == 0 else -1.4)) % 360)
            for q in range(8): cv.rotate(45); cv.drawRect(skia.Rect(-gr * 0.18, -gr * 1.15, gr * 0.18, -gr * 0.8), paint((0x8E, 0x7B, 0xD8)))
            cv.drawCircle(0, 0, gr * 0.85, paint((0x8E, 0x7B, 0xD8))); cv.drawCircle(0, 0, gr * 0.3, paint((0x2B, 0x22, 0x5E))); cv.restore()
    text(cv, "payloads", 330, 160, 46, TAGC, ease(ramp(t, T["pay"] - 0.2, 0.4))); text(cv, "indexes", 760, 160, 46, GOLD, ease(ramp(t, T["idx"] - 0.2, 0.4)))
    text(cv, "...and much more", 1180, 160, 46, WHITE, ease(ramp(t, T["bg"] - 0.2, 0.4)))

def s_config(cv, t, lt):
    cam = lt * 50; sky(cv, t, cam); hills(cv, cam); ground(cv)
    for k, (w, h, c, lab) in enumerate(((300, 640, (0x3B, 0x2F, 0x8F), "huge"), (520, 360, (0x2F, 0x6F, 0x8F), "steady"), (220, 230, (0x8F, 0x2F, 0x6F), "tiny"))):
        a = ease(ramp(t, SCENES[2] + 0.15 * k, 0.5)); building(cv, 170 + k * 560 - cam * 0.4, 900 + (1 - a) * 300, w, h, c, t, label=lab)
    q = ease(ramp(t, T["conf"] - 0.3, 0.5)); creature(cv, 960, 980, 60, DENSE, t, 1, mood=0.35, look=(0, -1))
    if q > 0: text(cv, "?", 1030, 880, 110, GOLD, q, align="left")
    text(cv, "no single configuration", 960, 170, 60, WHITE, q)

def s_signpost(cv, t, lt):
    cam = lt * 40; sky(cv, t, cam); hills(cv, cam); ground(cv)
    cv.drawRect(skia.Rect(940, 300, 975, 940), paint((0x8A, 0x5A, 0x3C)))
    signs = [("on disk", 0), ("payload index first", 1), ("quantization", 0), ("sparse on disk", 1), ("batch", 0), ("workers", 1), ("shards", 0)]
    for k, (lab, side) in enumerate(signs):
        a = back(ramp(t, (T["opt"] if k < 4 else T["best"]) - 0.3 + 0.14 * (k % 4), 0.45)); y = 330 + k * 82
        if a <= 0: continue
        w = 360; x = 975 if side else 940 - w; c = HOT if k < 4 else TAGC
        path = skia.Path(); tip = 40 if side else -40; xe = x + w if side else x
        path.moveTo(x, y); path.lineTo(x + w, y) if side else path.lineTo(x + w, y); path.lineTo(xe + tip, y + 32); path.lineTo(x + w if side else x, y + 64); path.lineTo(x if side else x + w, y + 64); path.close()
        cv.save(); cv.translate(957, y + 32); cv.scale(a, a); cv.translate(-957, -(y + 32)); cv.drawPath(path, paint(c)); text(cv, lab, x + w / 2, y + 46, 34, WHITE); cv.restore()
    creature(cv, 760, 980, 56, DENSE, t, 2, mood=0.85, look=(1, -0.6))
    text(cv, "options", 520, 190, 56, HOT, ease(ramp(t, T["opt"] - 0.3, 0.4))); text(cv, "best practices", 1250, 190, 56, TAGC, ease(ramp(t, T["best"] - 0.3, 0.4)))

def s_tribes(cv, t, lt):
    cam = lt * 30; sky(cv, t, cam); hills(cv, cam); ground(cv)
    rd = np.random.default_rng(5)
    for k in range(14): creature(cv, 140 + (k % 5) * 130 + rd.uniform(-20, 20), 760 + (k // 5) * 110, 46, DENSE, t, k, walk=t < T["dense"], look=(1, 0), mood=0.8 if t > T["dense"] else 0.6)
    for k in range(10): creature(cv, 1150 + (k % 4) * 150 + rd.uniform(-20, 20), 760 + (k // 4) * 120, 46, SPARSE, t, k + 9, walk=t < T["sparse"], look=(-1, 0), sparse=True, mood=0.8 if t > T["sparse"] else 0.6)
    text(cv, "dense", 470, 620, 72, DENSE, ease(ramp(t, T["dense"] - 0.25, 0.4))); text(cv, "sparse", 1420, 620, 72, SPARSE, ease(ramp(t, T["sparse"] - 0.25, 0.4)))
    text(cv, "full of numbers", 470, 690, 34, WHITE, ease(ramp(t, T["dense"] - 0.1, 0.4))); text(cv, "mostly empty", 1420, 690, 34, WHITE, ease(ramp(t, T["sparse"] - 0.1, 0.4)))

def s_hnsw(cv, t, lt):
    cam = lt * 40; cv.drawRect(skia.Rect(0, 0, W, H), paint((0x1E, 0x18, 0x48))); rd = np.random.default_rng(6)
    layers = [(400, 4), (620, 8), (850, 14)]; pts = []
    for li, (y, n) in enumerate(layers):
        cv.drawRoundRect(skia.Rect(180 - cam, y + 40, 1740 - cam, y + 60), 10, 10, paint((0x4A, 0x3C, 0x96)))
        pts.append([(260 + (j + 0.5) * (1400 / n) + rd.uniform(-30, 30) - cam, y) for j in range(n)])
    g = ease(ramp(t, T["hnsw"] - 0.3, 1.0))
    for li, row in enumerate(pts):
        for j in range(len(row) - 1):
            if (j / len(row)) < g: cv.drawLine(row[j][0], row[j][1], row[j + 1][0], row[j + 1][1], paint(GOLD, 0.8, 4))
        if li < 2:
            for j, (x, y) in enumerate(row):
                nx = min(pts[li + 1], key=lambda p: abs(p[0] - x))
                if g > 0.5: cv.drawLine(x, y, nx[0], nx[1], paint(GOLD, 0.35, 3))
    for li, row in enumerate(pts):
        for j, (x, y) in enumerate(row): creature(cv, x, y, 34, DENSE, t, li * 10 + j, look=(0.5, 0.3))
    text(cv, "HNSW: a graph of bridges, layer on layer", 820, 170, 54, WHITE, ease(ramp(t, T["hnsw"] - 0.4, 0.5)))

def s_catalog(cv, t, lt):
    cam = lt * 30; cv.drawRect(skia.Rect(0, 0, W, H), paint((0x2A, 0x1C, 0x4A)))
    cx, cy = 860 - cam * 0.3, 360; terms = ["t12", "t77", "t301", "t5", "t40", "t9"]
    cv.drawRoundRect(skia.Rect(cx, cy, cx + 640, cy + 620), 24, 24, paint((0x8A, 0x5A, 0x3C)))
    for k, term in enumerate(terms):
        r_, c_ = k // 2, k % 2; x, y = cx + 30 + c_ * 300, cy + 30 + r_ * 195; o = ease(ramp(t, T["sidx"] - 0.2 + 0.15 * k, 0.4)) * 60
        cv.drawRoundRect(skia.Rect(x + o, y, x + 280 + o, y + 170), 14, 14, paint((0xB0, 0x7A, 0x52))); text(cv, term, x + 140 + o, y + 100, 52, INK)
    for k in range(7):
        a = ease(ramp(t, T["sidx"] + 0.15 * k, 0.8)); x = 200 + k * 110 + (cx + 300 - 200 - k * 110) * a; y = 860 - 300 * math.sin(math.pi * a)
        if a < 1: creature(cv, x, y, 44, SPARSE, t, k, walk=True, sparse=True, look=(1, 0))
    text(cv, "sparse vectors: filed by term", 560, 170, 54, WHITE, ease(ramp(t, T["sidx"] - 0.4, 0.5)))

def s_memory(cv, t, lt):
    cam = lt * 40; sky(cv, t, cam); hills(cv, cam); ground(cv)
    crowd = ease(ramp(t, T["mem"] - 0.4, 1.2)); building(cv, 300 - cam * 0.3, 900, 760, 600, (0x8F, 0x2F, 0x5A), t, face=0.75 - 0.6 * crowd, sweat=crowd, label="RAM")
    for k in range(int(6 + 18 * crowd)): creature(cv, 340 + (k % 9) * 80 - cam * 0.3, 890 - (k // 9) * 40, 30, DENSE, t, k)
    sp = ease(ramp(t, T["perf"] - 0.3, 0.5)); gx, gy = 1450, 640
    cv.drawArc(skia.Rect(gx - 230, gy - 230, gx + 230, gy + 230), 180, 180, False, paint(WHITE, sp, 26))
    ang = math.radians(180 + 160 * (0.85 - 0.5 * crowd + 0.06 * math.sin(t * 9))); cv.drawLine(gx, gy, gx + 200 * math.cos(ang), gy + 200 * math.sin(ang), paint(HOT, sp, 12))
    text(cv, "memory", 680, 170, 60, HOT, ease(ramp(t, T["mem"] - 0.3, 0.4))); text(cv, "performance", 1450, 740, 54, WHITE, sp)
    if t > T["bulk"] - 0.4: truck(cv, -380 + (t - T["bulk"]) * 500, 1000, 0.6, t, riders=3)

def s_disk(cv, t, lt):
    cam = lt * 30; cv.drawRect(skia.Rect(0, 0, W, H), paint((0x1E, 0x18, 0x48)))
    cv.drawRect(skia.Rect(0, 620, W, H), paint((0x14, 0x10, 0x30))); text(cv, "DISK", 300, 1000, 64, (0x7A, 0x6E, 0xC8), 1)
    calm = ease(ramp(t, T["disk"] + 0.3, 0.8)); building(cv, 220, 560, 900, 480, (0x8F, 0x2F, 0x5A), t, face=0.2 + 0.7 * calm, sweat=1 - calm, label="RAM")
    ex = 1320; cv.drawRoundRect(skia.Rect(ex, 220, ex + 200, 1040), 16, 16, paint((0x4A, 0x3C, 0x96))); y_el = 380 + 560 * inout(ramp(t, T["disk"] - 0.1, 1.2))
    cv.drawRoundRect(skia.Rect(ex + 20, y_el - 130, ex + 180, y_el + 30), 12, 12, paint(GOLD, 0.9))
    for k in range(3): creature(cv, ex + 55 + k * 45, y_el - 10, 26, DENSE, t, k, mood=0.8)
    cv.drawRoundRect(skia.Rect(1600, 700, 1880, 1040), 26, 26, paint((0x3A, 0x30, 0x7A)))
    for k in range(int(10 * ease(ramp(t, T["disk"] + 0.6, 0.8)))): creature(cv, 1640 + (k % 4) * 65, 1000 - (k // 4) * 70, 26, DENSE, t, k, mood=0.9)
    b = back(ramp(t, T["first"] - 0.3, 0.45))
    if b > 0: cv.drawCircle(1250, 170, 80 * b, paint(HOT)); text(cv, "1", 1250, 205, 100, WHITE)
    text(cv, "vectors on disk", 900, 800, 64, GOLD, ease(ramp(t, T["storing"] - 0.2, 0.4)))

SCENE_FN = [s_upload, s_hall, s_config, s_signpost, s_tribes, s_hnsw, s_catalog, s_memory, s_disk, s_disk]

def frame(t, face_im, show_face):
    surf = skia.Surface(W, H); cv = surf.getCanvas(); k = max(i for i, s0 in enumerate(SCENES) if t >= s0 - 1e-6) if t >= 0 else 0
    if k == 9: k = 8                                                         # lines 8 and 9 share the disk scene
    SCENE_FN[k](cv, t, t - SCENES[k])
    iris = ramp(t, SCENES[k], 0.55)                                          # the previous scene shrinks away into an iris
    if 0 < k < 9 and iris < 1:
        prev = skia.Surface(W, H); pc = prev.getCanvas(); SCENE_FN[k - 1](pc, t, t - SCENES[k - 1]); img = prev.makeImageSnapshot()
        r = math.hypot(W, H) * (1 - inout(iris)); path = skia.Path(); path.addCircle(W / 2, H / 2, r); cv.save(); cv.clipPath(path, skia.ClipOp.kIntersect, True); cv.drawImage(img, 0, 0); cv.restore()
        cv.drawCircle(W / 2, H / 2, r, paint(WHITE, 0.8, 8))
    moon(cv, t)
    img = Image.fromarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGBA")
    if show_face:
        x, y, r = MOON; d = int(2 * r); f = E.face_crop(face_im, d, d, 1.35); m = Image.new("L", (d, d), 0)
        from PIL import ImageDraw; ImageDraw.Draw(m).ellipse([0, 0, d - 1, d - 1], fill=255); f.putalpha(m); img.paste(f, (int(x - r), int(y - r)), f)
    return img

def plan(p, t0, t1):
    hide = E.hidden_spans(p.look); cuts = sorted({t0, t1} | {x for a, b in hide for x in (a, b) if t0 < x < t1}); S_ = []
    for a, b in zip(cuts, cuts[1:]):
        on = not any(x < b and y > a for x, y in hide)
        S_.append(dict(t0=a, t1=b, kind="graphic", shows_face=on, draw=(lambda on_: lambda lt, dur, ctx: frame(ctx["t"], ctx["face"], on_))(on), tr="cut", _hidden=False))
    sfx = [(s0, E.whoosh(0.03, 0.4)) for s0 in SCENES[1:9] if t0 <= s0 < t1] + [(x, E.tone(0.07, 700, 1200, 0.03)) for x in (T["pay"], T["idx"], T["hnsw"], T["disk"]) if t0 <= x < t1]
    return S_, sfx

if __name__ == "__main__":
    a = sys.argv[1:]; p = SF.project()
    if a[:1] == ["stills"]:
        ts = [float(x) for x in a[1:]]; S_, sfx = plan(p, 0, max(ts) + 2); r = E.Renderer(p, S_, 0, p.dur, OUT, sfx, (0, 0, 0)); print(r.stills(ts, OUT.replace(".mp4", "_sheet.png"), cols=4))
    else:
        t0, t1 = (float(a[0]), float(a[1])) if len(a) >= 2 else (0.0, p.dur)
        S_, sfx = plan(p, t0, t1); E.Renderer(p, S_, t0, t1, OUT if (t0, t1) == (0.0, p.dur) else OUT.replace(".mp4", f"_{int(t0)}-{int(t1)}.mp4"), sfx, (0, 0, 0)).render()
