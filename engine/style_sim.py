"""SIMULATION: the upload runs live, the way Primer explains (see paradigm_audit/report.md).

One continuous simulation on a lab table seen in perspective. Points stream out of an upload pipe and land
on a collection; payload tags pop onto them; index links grow between neighbours; quiet pulses run along
the links (the work in the background). Each idea the presenter names is a change to the same running
world, never a new slide. Beside the table sits a lab dashboard: the presenter's live monitor (only while he
is on the lens; otherwise the monitor shows the rules panel), a points counter and live charts. Every pixel
is part of the lab, so there is no dead space.

  python style_sim.py 0 41             sample -> out/sim_0-41.mp4
  python style_sim.py stills 2 6 9 20   contact sheet
"""
import os, sys, json, math, numpy as np, skia
from PIL import Image
import engine as E
import style_full as SF
W, H = E.W, E.H
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\sim.mp4"
FONTS = r"C:\Users\ADMIN\camera_audit\fonts"
BG, PANEL, TABLE, RIM, GRID = (0x1C, 0x1F, 0x26), (0x25, 0x29, 0x32), (0xEC, 0xEE, 0xF2), (0xB9, 0xBE, 0xC9), (0x2C, 0x31, 0x3B)
INK, MUTE, DENSE, SPARSE, TAG, HOT, OKC = (0xF2, 0xF4, 0xF8), (0x8D, 0x94, 0xA6), (0x6A, 0x5B, 0xFF), (0xFF, 0x6B, 0x6B), (0x1F, 0xC9, 0xA8), (0xDC, 0x24, 0x4C), (0x2E, 0xCC, 0x71)
VIEW = (40, 40, 1240, 1000); TILE = (1310, 40, 570, 420); READ = (1310, 490, 570, 550)
_tf = {}
def font(name, size):
    if name not in _tf: _tf[name] = skia.Typeface.MakeFromFile(os.path.join(FONTS, name))
    return skia.Font(_tf[name], size)
def col(c, a=1.0): return skia.Color(c[0], c[1], c[2], int(255 * max(0, min(1, a))))
def paint(c, a=1.0, stroke=0, aa=True):
    p = skia.Paint(AntiAlias=aa, Color=col(c, a))
    if stroke: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke); p.setStrokeCap(skia.Paint.kRound_Cap)
    return p
def text(cv, s, x, y, size, c=INK, a=1.0, name="Geist-SemiBold.ttf", align="left"):
    f = font(name, size); w = f.measureText(s)
    if align == "center": x -= w / 2
    elif align == "right": x -= w
    cv.drawString(s, x, y, f, paint(c, a))
def rrect(cv, x, y, w, h, r, c, a=1.0, stroke=0): cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), paint(c, a, stroke))
def ease(x): return E.ease(x)
def inout(x): return E.inout(x)
def ramp(t, a, d=0.5): return max(0.0, min(1.0, (t - a) / d))

WORDS = json.load(open(r"C:\Users\ADMIN\camera_audit\styles\out\v2_words.json"))["pieces"]
def wd(i, w, nth=0):
    hits = [t for x, t in WORDS[i]["words"] if x.lower().strip(",.?!").startswith(w.lower())]; return hits[min(nth, len(hits) - 1)]

# ---------------------------------------------------------------- the world, as a function of time
class Table:
    """a rounded platform in perspective: (u, v) in [-1, 1]^2 -> screen; nearer rows (v > 0) are larger"""
    def __init__(self, cx, cy, A, B, k=0.22): self.cx, self.cy, self.A, self.B, self.k = cx, cy, A, B, k
    def xy(self, u, v): s = 1 + self.k * v; return self.cx + u * self.A * s, self.cy + v * self.B, s
    def outline(self, n=96, r=0.18):
        pts = []
        for j in range(n):                                                       # a rounded square traced by angle
            a = 2 * math.pi * j / n; c, s = math.cos(a), math.sin(a); m = max(abs(c), abs(s)); u, v = c / m, s / m
            u = max(-1 + r, min(1 - r, u)) + (r * c if abs(u) >= 1 - r else 0); v = max(-1 + r, min(1 - r, v)) + (r * s if abs(v) >= 1 - r else 0)
            pts.append(self.xy(u * 1.06, v * 1.06)[:2])
        return pts
def lerp_table(a, b, k): return Table(*[x + (y - x) * k for x, y in zip((a.cx, a.cy, a.A, a.B, a.k), (b.cx, b.cy, b.A, b.B, b.k))])
MAIN = Table(660, 650, 480, 300); LEFT = Table(255, 610, 185, 200); MID = Table(660, 610, 185, 200); RIGHT = Table(1065, 610, 185, 200)
UPPER = Table(660, 480, 440, 165); LOWER = Table(660, 840, 440, 150)
PIPE = (40, 330)

rng = np.random.default_rng(7)
def stream(t_start, rates, n_max, urange, vrange, seed):
    r = np.random.default_rng(seed); s, t = [], t_start
    for (t_end, rate) in rates:
        while t < t_end and len(s) < n_max: s.append(t); t += 1.0 / rate
    n = len(s); return dict(s=np.array(s), u=r.uniform(*urange, n), v=r.uniform(*vrange, n), ph=r.uniform(0, 6.28, n))
def knn_edges(u, v, k=2):
    e = set()
    for i in range(len(u)):
        d = (u - u[i]) ** 2 + (v - v[i]) ** 2; d[i] = 9
        for j in np.argsort(d)[:k]: e.add((min(i, int(j)), max(i, int(j))))
    return sorted(e, key=lambda p: u[p[0]])

T_UP = wd(0, "uploading"); T_LARGE = wd(0, "large")
A = stream(T_UP - 0.1, [(T_LARGE, 18), (9.3, 58)], 520, (-0.92, 0.92), (-0.85, 0.85), 1)
A_EDGES = knn_edges(A["u"], A["v"]); T_TAGS = wd(1, "payloads"); T_IDX = wd(1, "indexes"); T_BG = wd(1, "much")
T_SPLIT = WORDS[2]["t0"]; T_MERGE = WORDS[3]["t0"]; T_OPT = wd(3, "options"); T_BEST = wd(3, "best"); T_D0 = WORDS[4]["t0"]
D = stream(T_D0 + 0.5, [(T_D0 + 3.4, 70)], 200, (-0.92, -0.08), (-0.85, 0.85), 2)
S = stream(T_D0 + 1.0, [(T_D0 + 3.6, 40)], 100, (0.08, 0.92), (-0.85, 0.85), 3)
T_DENSE, T_SPARSE = wd(4, "dense"), wd(4, "sparse"); T_HNSW = wd(5, "hnsw"); D_EDGES = knn_edges(D["u"], D["v"], 3)
T_SIDX = wd(6, "sparse"); T_MEM, T_PERF = wd(7, "memory"), wd(7, "performance"); T_F = WORDS[8]["t0"]; T_FIRST = wd(8, "option")
T_STORE, T_DISK = wd(9, "storing"), wd(9, "disk")
TERMS = ["t12", "t77", "t301", "t5", "t40", "t9"]; S_TERM = np.random.default_rng(4).integers(0, len(TERMS), len(S["s"]))

def table_at(t):
    if t < T_SPLIT: return [("collection", MAIN, 1.0)]
    if t < T_MERGE:
        k = inout(ramp(t, T_SPLIT, 0.6)); return [("config A", lerp_table(MAIN, LEFT, k), 1.0), ("config B", MID, k), ("config C", RIGHT, k)]
    if t < T_F + 3.6:
        k = inout(ramp(t, T_MERGE, 0.6)); return [("collection", lerp_table(LEFT, MAIN, k), 1.0)]
    k = inout(ramp(t, T_STORE - 0.2, 0.7)); return [("RAM", lerp_table(MAIN, UPPER, k), 1.0), ("disk", LOWER, k)]

def draw_table(cv, tb, name, alpha, heat=0.0):
    pts = tb.outline(); path = skia.Path(); path.addPoly([skia.Point(x, y + 16) for x, y in pts], True); cv.drawPath(path, paint(RIM, 0.9 * alpha))
    path = skia.Path(); path.addPoly([skia.Point(x, y) for x, y in pts], True); cv.drawPath(path, paint(TABLE, alpha))
    if heat > 0: cv.drawPath(path, paint(HOT, 0.22 * heat * alpha))
    x, y, s = tb.xy(-1.0, -1.08); text(cv, name.upper(), x, y - 14, 22, MUTE, alpha, "GeistMono-Medium.ttf")

def point_xy(P, i, t, tb, land=0.6):
    a = (t - P["s"][i]) / land
    if a < 0: return None
    u, v = P["u"][i] + 0.012 * math.sin(t * 0.9 + P["ph"][i]), P["v"][i] + 0.012 * math.cos(t * 0.7 + P["ph"][i]); x1, y1, s = tb.xy(u, v)
    if a >= 1: return x1, y1, s, 1.0
    e = inout(a); x = PIPE[0] + (x1 - PIPE[0]) * e; y = PIPE[1] + (y1 - PIPE[1]) * e - 160 * math.sin(math.pi * e); return x, y, s * (0.7 + 0.3 * e), e

def world(cv, t):
    cv.save(); cv.clipRect(skia.Rect.MakeXYWH(*VIEW)); rrect(cv, *VIEW, 22, PANEL)
    for gx in range(VIEW[0] + 40, VIEW[0] + VIEW[2], 60): cv.drawLine(gx, VIEW[1], gx, VIEW[1] + VIEW[3], paint(GRID, 0.5, 1))
    for gy in range(VIEW[1] + 40, VIEW[1] + VIEW[3], 60): cv.drawLine(VIEW[0], gy, VIEW[0] + VIEW[2], gy, paint(GRID, 0.5, 1))
    rrect(cv, PIPE[0] - 30, PIPE[1] - 34, 70, 68, 14, (0x3A, 0x40, 0x4D)); text(cv, "upload", PIPE[0] - 20, PIPE[1] + 62, 20, MUTE, 1, "GeistMono-Medium.ttf")
    tables = table_at(t); heat = ease(ramp(t, T_MEM - 0.2, 0.5)) * (1 - ease(ramp(t, T_F, 0.4)))
    for name, tb, al in tables: draw_table(cv, tb, name, al)
    main = tables[0][1]
    # scene A: the first upload, tags, links, background pulses
    fade_a = 1 - ease(ramp(t, T_D0 - 0.2, 0.5))
    if fade_a > 0:
        if t < T_SPLIT or t >= T_MERGE:
            tb = main; xy = [point_xy(A, i, t, tb) for i in range(len(A["s"]))]
            n_e = int(len(A_EDGES) * ease(ramp(t, T_IDX - 0.2, 1.6)))
            for (i, j) in A_EDGES[:n_e]:
                if xy[i] and xy[j] and xy[i][3] >= 1 and xy[j][3] >= 1: cv.drawLine(xy[i][0], xy[i][1], xy[j][0], xy[j][1], paint(DENSE, 0.35 * fade_a, 1.6))
            if t > T_BG:                                                          # quiet work in the background: pulses along links
                for k in range(14):
                    i, j = A_EDGES[(k * 37 + int(t * 3)) % max(1, n_e)] if n_e else (0, 0); ph = (t * 1.3 + k * 0.17) % 1
                    if xy[i] and xy[j]: cv.drawCircle(xy[i][0] + (xy[j][0] - xy[i][0]) * ph, xy[i][1] + (xy[j][1] - xy[i][1]) * ph, 4, paint(TAG, 0.9 * fade_a))
            for i, p in enumerate(xy):
                if not p: continue
                x, y, s, e = p; cv.drawCircle(x, y + 6 * s, 7 * s, paint((0, 0, 0), 0.12 * fade_a)); cv.drawCircle(x, y, 7.5 * s, paint(DENSE, fade_a))
                if t > T_TAGS + (A["u"][i] + 1) * 0.35 and e >= 1: rrect(cv, x + 4 * s, y - 12 * s, 7 * s, 7 * s, 2, TAG, fade_a)
        else:                                                                     # the three configurations: same points, three ways of keeping them
            for k, (name, tb, al) in enumerate(tables):
                for i in range(0, len(A["s"]), 3):
                    p = point_xy(A, i, max(t, A["s"][i] + 1), tb)
                    if p: cv.drawCircle(p[0], p[1], 5 * p[2], paint([DENSE, SPARSE, TAG][k], 0.95))
                g = ease(ramp(t, T_SPLIT + 0.6 + 0.25 * k, 0.6)); x, y, _ = tb.xy(-0.9, 1.25); val = [0.92, 0.18, 0.45][k] * g
                rrect(cv, x, y + 26, 300, 16, 8, GRID); rrect(cv, x, y + 26, max(16, 300 * val), 16, 8, HOT if val > 0.7 else OKC)
                text(cv, ["RAM-heavy", "on disk", "compressed"][k], x, y + 74, 22, INK, g)
    # scene D: dense and sparse, HNSW links, the inverted index
    if t >= T_D0:
        tb = main; xd = [point_xy(D, i, t, tb) for i in range(len(D["s"]))]; xs = [point_xy(S, i, t, tb) for i in range(len(S["s"]))]
        drop = [ease(ramp(t, T_DISK + 0.03 * (i % 30), 0.6)) for i in range(len(D["s"]))]
        if t >= T_STORE - 0.2:                                                    # the RAM tray holds them until the switch sends them down
            for i, p in enumerate(xd):
                if p and drop[i] > 0:
                    x2, y2, s2 = LOWER.xy(D["u"][i], D["v"][i]); xd[i] = (p[0] + (x2 - p[0]) * drop[i], p[1] + (y2 - p[1]) * drop[i], p[2], p[3])
        n_e = int(len(D_EDGES) * ease(ramp(t, T_HNSW - 0.25, 1.0)))
        fade_e = 1 - ease(ramp(t, T_DISK - 0.3, 0.3))                               # the links let go before the points drop
        for (i, j) in D_EDGES[:n_e] if fade_e > 0 else []:
            if xd[i] and xd[j] and xd[i][3] >= 1 and xd[j][3] >= 1: cv.drawLine(xd[i][0], xd[i][1], xd[j][0], xd[j][1], paint(DENSE, 0.45 * fade_e, 1.8))
        hl_d = ease(ramp(t, T_DENSE - 0.2, 0.3)) * (1 - ease(ramp(t, T_SPARSE - 0.1, 0.3))); hl_s = ease(ramp(t, T_SPARSE - 0.2, 0.3)) * (1 - ease(ramp(t, T_HNSW - 0.4, 0.3)))
        if heat > 0:
            x0, y0, _ = tb.xy(-0.5, 0); cv.drawCircle(x0, y0, 260 * heat, paint(HOT, 0.10 * heat))
        for i, p in enumerate(xd):
            if p: cv.drawCircle(p[0], p[1] + 6 * p[2], 7 * p[2], paint((0, 0, 0), 0.12)); cv.drawCircle(p[0], p[1], (8 + 3 * hl_d) * p[2], paint(DENSE))
        for i, p in enumerate(xs):
            if p: cv.drawCircle(p[0], p[1], (8 + 3 * hl_s) * p[2], paint(SPARSE, 1, 3.2 * p[2]))
        # the inverted index: a column per term, sparse points drop in as postings
        ki = ease(ramp(t, T_SIDX - 0.3, 0.5)) * (1 - ease(ramp(t, T_F, 0.4)))
        if ki > 0:
            bx, by = 920, 120
            for c_, term in enumerate(TERMS):
                x = bx + c_ * 50; rrect(cv, x, by, 40, 200, 8, (0x31, 0x36, 0x42), ki); text(cv, term, x + 20, by - 12, 18, MUTE, ki, "GeistMono-Medium.ttf", "center")
            for i in range(len(S["s"])):
                a = ease(ramp(t, T_SIDX + 0.012 * i, 0.5)) * ki
                if a <= 0 or not xs[i]: continue
                c_ = S_TERM[i]; n_before = int((S_TERM[:i] == c_).sum()); tx, ty = bx + c_ * 50 + 20, by + 188 - n_before * 11
                x, y = xs[i][0] + (tx - xs[i][0]) * a, xs[i][1] + (ty - xs[i][1]) * a; rrect(cv, x - 14, y - 5, 28, 10, 3, SPARSE, 0.9 * ki)
        if T_PERF - 0.2 < t < T_F:                                                # a query walks the graph
            hop = int((t - T_PERF) * 6) % 8; i, j = D_EDGES[(hop * 11) % len(D_EDGES)]
            if xd[i] and xd[j]: cv.drawCircle(xd[i][0], xd[i][1], 15, paint(HOT, 0.9, 4))
    # scene F: the rules panel in the world, the on_disk switch
    kp = ease(ramp(t, T_MERGE + 0.3, 0.5)) * (1 - ease(ramp(t, T_D0 - 0.3, 0.4))) + ease(ramp(t, T_F, 0.5))
    if kp > 0: rules(cv, t, VIEW[0] + 30, VIEW[1] + 20 - 140 * (1 - min(1, kp)), min(1, kp))      # the rules slide down from the top
    cv.restore()

RULES = [("on_disk", "opt"), ("payload index first", "opt"), ("quantization", "opt"), ("sparse index on_disk", "opt"), ("batch size", "bp"), ("upload workers", "bp"), ("shards", "bp")]
def rules(cv, t, x, y, k):
    rrect(cv, x, y, VIEW[2] - 60, 112, 18, (0x30, 0x35, 0x41), 0.97 * k)
    cx = x + 22
    for n, (name, kind) in enumerate(RULES):
        appear = T_OPT - 0.3 + 0.12 * n if kind == "opt" else T_BEST - 0.3 + 0.12 * (n - 4)
        a = ease(ramp(t, appear, 0.35)) if t < T_D0 else 1.0
        if a <= 0: cx += 160; continue
        focus = (n == 0 and t >= T_FIRST - 0.3); on = n == 0 and t >= T_DISK - 0.1
        w = 156 if kind == "opt" else 150
        rrect(cv, cx, y + 18, w, 76, 12, HOT if focus else (0x3A, 0x40, 0x4D), (0.35 if focus else 1) * a * k)
        if focus: rrect(cv, cx, y + 18, w, 76, 12, HOT, a * k, 3)
        text(cv, name if len(name) < 16 else name[:15] + "…", cx + 12, y + 46, 17, INK, a * k)
        if kind == "opt":
            sw = cx + 12; rrect(cv, sw, y + 60, 46, 22, 11, OKC if on else (0x55, 0x5C, 0x6B), a * k); cv.drawCircle(sw + (35 if on else 11), y + 71, 9, paint(INK, a * k))
        else:
            rrect(cv, cx + 12, y + 68, 120, 6, 3, (0x55, 0x5C, 0x6B), a * k); cv.drawCircle(cx + 12 + 120 * (0.3 + 0.2 * (n - 4)), y + 71, 9, paint(TAG, a * k))
        cx += w + 12

def landed(P, t): return int(np.sum(P["s"] + 0.6 <= t))
def ram_value(t):
    if t < T_D0: return min(1.0, landed(A, t) / 520 * 0.9)
    v = 0.25 + 0.55 * landed(D, t) / 200 + 0.12 * landed(S, t) / 100
    return v * (1 - 0.7 * ease(ramp(t, T_DISK, 0.9)))

def readouts(cv, t):
    x, y, w, h = READ; rrect(cv, x, y, w, h, 22, PANEL)
    n = landed(A, t) * 2000 if t < T_D0 else (landed(D, t) + landed(S, t)) * 2000 + 1040000
    text(cv, "POINTS UPLOADED", x + 30, y + 52, 20, MUTE, 1, "GeistMono-Medium.ttf"); text(cv, f"{n:,}", x + 30, y + 128, 64, INK, 1, "Geist-Bold.ttf")
    cx0, cy0, cw, ch = x + 30, y + 190, w - 60, 150
    text(cv, "RAM", cx0, cy0 - 12, 20, MUTE, 1, "GeistMono-Medium.ttf"); rrect(cv, cx0, cy0, cw, ch, 10, (0x1E, 0x22, 0x2A))
    t_exp = 0.0 if t < T_D0 else T_D0; path = skia.Path(); t_s = max(t_exp, t - 20); first = True    # a new experiment restarts the chart
    for k in range(0, 121):
        tt = t_s + (t - t_s) * k / 120; v = ram_value(tt); px, py = cx0 + cw * k / 120, cy0 + ch - 10 - (ch - 20) * v
        path.moveTo(px, py) if first else path.lineTo(px, py); first = False
    cv.drawPath(path, paint(HOT if ram_value(t) > 0.75 else TAG, 1, 4))
    links = (int(len(A_EDGES) * ease(ramp(t, T_IDX - 0.2, 1.6))) if t < T_D0 else int(len(D_EDGES) * ease(ramp(t, T_HNSW - 0.25, 1.0)))) * 5000
    text(cv, "INDEX LINKS", x + 30, y + 400, 20, MUTE, 1, "GeistMono-Medium.ttf"); text(cv, f"{links:,}", x + 30, y + 460, 46, DENSE if links else MUTE, 1, "Geist-Bold.ttf")
    bg = t > T_BG and t < T_SPLIT
    text(cv, "BACKGROUND", x + 330, y + 400, 20, MUTE, 1, "GeistMono-Medium.ttf")
    for k in range(5): rrect(cv, x + 330 + k * 40, y + 425, 30, 30, 6, TAG if bg and (int(t * 6) + k) % 5 < 3 else (0x3A, 0x40, 0x4D))

def frame(t, face_im, show_face):
    surf = skia.Surface(W, H); cv = surf.getCanvas(); cv.clear(col(BG)); world(cv, t); readouts(cv, t)
    x, y, w, h = TILE; rrect(cv, x, y, w, h, 22, PANEL)
    if not show_face:
        text(cv, "THE RULES", x + 30, y + 60, 22, MUTE, 1, "GeistMono-Medium.ttf")
        for n, (name, kind) in enumerate(RULES):
            on = n == 0 and t >= T_DISK - 0.1; text(cv, ("● " if on else "○ ") + name, x + 30, y + 110 + n * 42, 26, OKC if on else INK, 1, "Geist-Medium.ttf")
    img = Image.fromarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGBA")
    if show_face:                                                                 # the presenter's live monitor, cropped inside the cut's bars
        f = E.face_crop(face_im, w - 16, h - 16, 1.15); m = E.rounded_mask(w - 16, h - 16, 16); f.putalpha(m); img.paste(f, (x + 8, y + 8), f)
        d = skia.Surface(140, 44); c2 = d.getCanvas(); c2.clear(skia.Color(0, 0, 0, 0)); rrect(c2, 0, 0, 120, 40, 20, (0, 0, 0), 0.55); c2.drawCircle(24, 20, 8, paint(HOT, 0.6 + 0.4 * math.sin(t * 5) ** 2)); text(c2, "LIVE", 42, 28, 20, INK, 1, "Geist-SemiBold.ttf")
        lab = Image.fromarray(d.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)); img.alpha_composite(lab, (x + 24, y + 24))
    return img

def plan(p, t0, t1):
    hide = E.hidden_spans(p.look); cuts = sorted({t0, t1} | {x for a, b in hide for x in (a, b) if t0 < x < t1}); S_ = []
    for a, b in zip(cuts, cuts[1:]):
        on = not any(x < b and y > a for x, y in hide)
        S_.append(dict(t0=a, t1=b, kind="graphic", shows_face=on, draw=(lambda on_: lambda lt, dur, ctx: frame(ctx["t"], ctx["face"], on_))(on), tr="cut", _hidden=False))
    sfx = [(x, E.tone(0.06, 900, 600, 0.03)) for x in (T_TAGS, T_IDX, T_SPLIT, T_MERGE, T_HNSW, T_SIDX, T_DISK) if t0 <= x < t1]
    return S_, sfx

if __name__ == "__main__":
    a = sys.argv[1:]; p = SF.project()
    if a[:1] == ["stills"]:
        ts = [float(x) for x in a[1:]]; S_, sfx = plan(p, 0, max(ts) + 2); r = E.Renderer(p, S_, 0, p.dur, OUT, sfx, BG); print(r.stills(ts, OUT.replace(".mp4", "_sheet.png"), cols=4))
    else:
        t0, t1 = (float(a[0]), float(a[1])) if len(a) >= 2 else (0.0, p.dur)
        S_, sfx = plan(p, t0, t1); E.Renderer(p, S_, t0, t1, OUT if (t0, t1) == (0.0, p.dur) else OUT.replace(".mp4", f"_{int(t0)}-{int(t1)}.mp4"), sfx, BG).render()
