"""BLUEPRINT: the explanation is an engineering drawing being drafted on blueprint paper.

Every line draws itself like a pen stroke; parts get leader lines with circled letters; numbers are dimension
lines; red pencil marks the changes (a strike-through on the default config, a revision cloud on on_disk).
Each section is a new sheet that slides in over the last or is zoomed into; the title block in the corner
updates its sheet number. The presenter is DETAIL A, a circular callout that moves around the sheet and
closes like an iris in a look-away.

  python style_blueprint.py 0 41             sample -> out/blueprint_0-41.mp4
  python style_blueprint.py stills 2 6 20    contact sheet
"""
import os, sys, math, numpy as np, skia
from PIL import Image, ImageDraw
import engine as E
import style_full as SF
import style_launch as LN
W, H = E.W, E.H; TR = E.TR
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\blueprint.mp4"
font, col, ramp, ease, inout, back, lerp = LN.font, LN.col, LN.ramp, E.ease, E.inout, E.back, LN.lerp
T, L, wd = LN.T, LN.L, LN.wd
PAPER, WH, MK = (22, 70, 140), (236, 243, 255), (255, 120, 140)                    # blueprint blue, white line, red pencil
MONO = "GeistMono-Regular.ttf"; MONO_B = "GeistMono-Bold.ttf"
def paint(c, a=1.0, w=0.0, blur=0.0):
    p = skia.Paint(AntiAlias=True, Color=col(c, a))
    if w: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(w); p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p

# ---------------------------------------------------------------- pen primitives: everything draws on over a time window
def prog(t, t0, d): return max(0.0, min(1.0, (t - t0) / d)) if d > 0 else (1.0 if t >= t0 else 0.0)
def stroke(cv, pts, t, t0, d=0.5, c=WH, w=2.6, closed=False, a=1.0):
    k = prog(t, t0, d)
    if k <= 0: return
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    if closed: p.close()
    if k < 1:
        pm = skia.PathMeasure(p, False); L_ = pm.getLength(); seg = skia.Path(); pm.getSegment(0, L_ * k, seg, True); r = pm.getPosTan(L_ * k)
        cv.drawPath(seg, paint(c, a, w)); pos = r[0] if isinstance(r, tuple) else r; cv.drawCircle(pos.x(), pos.y(), 5, paint(c, a, blur=2))   # the pen tip
    else: cv.drawPath(p, paint(c, a, w))
def circle(cv, cx, cy, r, t, t0, d=0.4, c=WH, w=2.6, a=1.0):
    k = prog(t, t0, d)
    if k > 0: cv.drawArc(skia.Rect(cx - r, cy - r, cx + r, cy + r), -90, 360 * k, False, paint(c, a, w))
def letter(cv, s, x, y, size, t, t0, cps=40, c=WH, name=MONO, align="left", a=1.0):
    if t < t0: return
    n = min(len(s), int((t - t0) * cps) + 1); f = font(name, size); sub = s[:n]; w = f.measureText(s)
    x = x - w / 2 if align == "center" else (x - w if align == "right" else x); cv.drawString(sub, x, y, f, paint(c, a))
def dim(cv, x1, y1, x2, y2, label, t, t0, off=40, c=WH):
    """a dimension line: extension lines, the line with arrowheads, the figure written over it"""
    ang = math.atan2(y2 - y1, x2 - x1); nx, ny = -math.sin(ang) * off, math.cos(ang) * off
    stroke(cv, [(x1, y1), (x1 + nx * 1.2, y1 + ny * 1.2)], t, t0, 0.15, c, 1.6); stroke(cv, [(x2, y2), (x2 + nx * 1.2, y2 + ny * 1.2)], t, t0, 0.15, c, 1.6)
    a1, a2 = (x1 + nx, y1 + ny), (x2 + nx, y2 + ny); stroke(cv, [a1, a2], t, t0 + 0.1, 0.4, c, 1.8)
    if t > t0 + 0.4:
        for (px, py), s in ((a1, 1), (a2, -1)):
            for sg in (-1, 1): cv.drawLine(px, py, px + s * 18 * math.cos(ang + sg * 0.35), py + s * 18 * math.sin(ang + sg * 0.35), paint(c, 1, 1.8))
    letter(cv, label, (a1[0] + a2[0]) / 2, (a1[1] + a2[1]) / 2 - 12, 28, t, t0 + 0.4, 30, c, align="center")
def leader(cv, px, py, tx, ty, tag, label, t, t0, c=WH):
    cv.drawCircle(px, py, 6, paint(c, prog(t, t0, 0.1))); stroke(cv, [(px, py), (tx, ty)], t, t0, 0.3, c, 2); right = tx > px
    stroke(cv, [(tx, ty), (tx + (220 if right else -220), ty)], t, t0 + 0.3, 0.2, c, 2); bx = tx + 26 if right else tx - 220 + 26
    circle(cv, bx, ty - 30, 22, t, t0 + 0.4, 0.25, c, 2); letter(cv, tag, bx, ty - 20, 26, t, t0 + 0.55, 30, c, MONO_B, "center"); letter(cv, label, bx + 34, ty - 20, 25, t, t0 + 0.55, 40, c)
def hatch(cv, x, y, w, h, t, t0, c=WH, a=0.8):
    k = prog(t, t0, 0.5)
    if k <= 0: return
    cv.save(); cv.clipRect(skia.Rect(x, y, x + w * k, y + h))
    for d in range(-int(h), int(w), 12): cv.drawLine(x + d, y + h, x + d + h, y, paint(c, a, 1.4))
    cv.restore()
def iso(x, y, z, ox=760, oy=640, s=1.0): return ox + (x - y) * 0.866 * s, oy + (x + y) * 0.5 * s - z * s
def ibox(cv, x, y, z, w, d, h, t, t0, dur=0.6, c=WH, ox=760, oy=640, s=1.0):
    P = lambda *q: iso(*q, ox=ox, oy=oy, s=s)
    top = [P(x, y, z + h), P(x + w, y, z + h), P(x + w, y + d, z + h), P(x, y + d, z + h)]
    stroke(cv, top, t, t0, dur * 0.5, c, 2.6, closed=True)
    stroke(cv, [P(x + w, y, z + h), P(x + w, y, z), P(x + w, y + d, z), P(x + w, y + d, z + h)], t, t0 + dur * 0.4, dur * 0.4, c, 2.6)
    stroke(cv, [P(x + w, y + d, z), P(x, y + d, z), P(x, y + d, z + h)], t, t0 + dur * 0.6, dur * 0.4, c, 2.6)

# ---------------------------------------------------------------- sheets
def s1(cv, t):
    """SHEET 1: the upload path, an exploded isometric Qdrant node"""
    stroke(cv, [(90, 300), (330, 300), (330, 450), (90, 450)], t, T["up"] - 0.3, 0.6, closed=True); letter(cv, "CLIENT", 210, 390, 34, t, T["up"], 30, align="center")
    n = 1_000_000 * ease(ramp(t, T["large"], 6.5)); dim(cv, 340, 470, 600, 560, f"{int(n):,} PTS", t, T["large"] - 0.2, 60)
    stroke(cv, [(330, 375), (520, 470)], t, T["up"] + 0.2, 0.5, WH, 2.6)
    if t > T["up"] + 0.7: cv.drawLine(520, 470, 500, 448, paint(WH, 1, 2.6)); cv.drawLine(520, 470, 492, 472, paint(WH, 1, 2.6))
    q = T["qd"] - 0.3; ox, oy, s = 820, 560, 1.15
    ibox(cv, 0, 0, 0, 520, 360, 50, t, q, 0.9, ox=ox, oy=oy, s=s); ibox(cv, 30, 30, 50, 90, 50, 25, t, q + 0.5, ox=ox, oy=oy, s=s); ibox(cv, 220, 130, 50, 110, 110, 20, t, q + 0.6, ox=ox, oy=oy, s=s)
    for k in range(5): ibox(cv, 380 + k * 22, 80, 50, 10, 200, 55, t, q + 0.7 + 0.05 * k, 0.4, ox=ox, oy=oy, s=s)
    ibox(cv, 60, 250, 50, 170, 80, 22, t, q + 0.9, ox=ox, oy=oy, s=s)
    lift = 160 * ease(ramp(t, LN.wd(0, "just") - 0.2, 0.9)); ibox(cv, 0, 0, 120 + lift, 520, 360, 10, t, q + 1.0, 0.6, c=WH, ox=ox, oy=oy, s=s)
    letter(cv, "QDRANT NODE (EXPLODED)", *iso(260, 0, 330 + lift, ox=ox, oy=oy, s=s), 26, t, T["qd"] + 0.4, 40, align="center")
    leader(cv, *iso(145, 290, 72, ox=ox, oy=oy, s=s), 520, 940, "A", "PAYLOAD STORE", t, T["pay"] - 0.3)
    leader(cv, *iso(430, 180, 105, ox=ox, oy=oy, s=s), 1270, 690, "B", "HNSW INDEX (RAM)", t, T["idx"] - 0.3)
    leader(cv, *iso(275, 185, 70, ox=ox, oy=oy, s=s), 330, 760, "C", "OPTIMIZER / WAL", t, T["bg"] - 0.3)
def s2(cv, t):
    """SHEET 2: a configuration table; the default row is struck through, each workload gets its own"""
    x0, y0, cw, rh = 120, 250, [300, 260, 260, 260], 92; rows = ["", "ON_DISK", "HNSW M", "PAYLOAD IDX", "SHARDS"]; cols = ["", "RAG", "ANALYTICS", "SAAS"]
    t0 = L[2] + 0.2; xs = [x0]; [xs.append(xs[-1] + c) for c in cw]
    for r in range(len(rows) + 2): stroke(cv, [(x0, y0 + r * rh), (xs[-1], y0 + r * rh)], t, t0 + 0.05 * r, 0.4, WH, 2 if r in (0, 1, len(rows) + 1) else 1.4)
    for k, x in enumerate(xs): stroke(cv, [(x, y0), (x, y0 + (len(rows) + 1) * rh)], t, t0 + 0.2 + 0.05 * k, 0.4, WH, 1.6)
    for k, c in enumerate(cols): letter(cv, c, xs[k] + cw[k] / 2, y0 + 58, 30, t, T["conf"] + 0.22 * max(0, k - 1), 30, WH, MONO_B, "center")
    for r, nm in enumerate(rows[1:]): letter(cv, nm, xs[0] + 24, y0 + (r + 1) * rh + 58, 27, t, t0 + 0.6, 40)
    letter(cv, "DEFAULT", xs[0] + 24, y0 + 5 * rh + 58, 27, t, T["single"], 30, MK, MONO_B)
    vals = [["false", "false", "true"], ["32", "16", "16"], ["-", "category", "tenant_id"], ["1", "2", "6"]]
    for c in range(3):
        for r in range(4): letter(cv, vals[r][c], xs[c + 1] + cw[c + 1] / 2, y0 + (r + 1) * rh + 58, 28, t, T["wf"] + 0.2 + 0.15 * c, 30, WH, align="center")
        letter(cv, "on_disk=F m=16 1", xs[c + 1] + cw[c + 1] / 2, y0 + 5 * rh + 58, 22, t, T["single"] + 0.2, 40, MK, align="center")
    stroke(cv, [(x0 + 10, y0 + 5.5 * rh), (xs[-1] - 10, y0 + 5.5 * rh)], t, T["works"], 0.6, MK, 4)                       # the default does not fit
    letter(cv, "NOTE 1: NO SINGLE CONFIGURATION FITS EVERY WORKLOAD.", x0, y0 + 6 * rh + 60, 26, t, T["wf"] + 0.4, 50)
def s3(cv, t):
    """SHEET 3: the process line, seven stations, two dimensioned groups"""
    t0 = wd(3, "different") - 0.1; xs = [160 + k * 205 for k in range(7)]; y = 580
    stroke(cv, [(90, y), (xs[-1] + 90, y)], t, t0, 1.6, WH, 3)
    for k, ((num, name, _), x) in enumerate(zip(LN.ROAD, xs)):
        at = (T["opt"] if k < 4 else T["best"]) - 0.25 + 0.12 * (k % 4); c = MK if k < 4 else WH
        circle(cv, x, y, 54, t, at, 0.3, c, 3); letter(cv, num, x, y + 16, 48, t, at + 0.25, 30, c, MONO_B, "center")
        up = k % 2 == 0; stroke(cv, [(x, y + (-54 if up else 54)), (x, y + (-130 if up else 130))], t, at + 0.2, 0.2, c, 1.8)
        for j, part in enumerate(name.upper().split(" ")[:3]): letter(cv, part, x, y + (-150 - 38 * (len(name.split(" ")[:3]) - 1 - j) if up else 172 + 38 * j), 30, t, at + 0.35, 40, c, align="center")
    dim(cv, xs[0] - 55, y - 330, xs[3] + 55, y - 330, "OPTIONS (DENSE OR SPARSE)", t, T["opt"] + 0.4, 30, MK)
    dim(cv, xs[4] - 55, y - 330, xs[6] + 55, y - 330, "BEST PRACTICES (BOTH)", t, T["best"] + 0.4, 30, WH)
def s4(cv, t):
    """SHEET 4: dense and sparse as parts; their indexes in section; memory as hatched tanks"""
    kc = ease(ramp(t, L[7] - 0.1, 0.5)); y1, y2 = 300, 470
    letter(cv, "PART 1: DENSE VECTOR", 120, y1 - 20, 28, t, T["dense"] - 0.3, 40, WH, MONO_B); stroke(cv, [(120, y1), (1140, y1), (1140, y1 + 60), (120, y1 + 60)], t, T["dense"] - 0.2, 0.5, closed=True)
    for k in range(32): stroke(cv, [(120 + k * 32, y1), (120 + k * 32, y1 + 60)], t, T["dense"] + 0.2 + 0.01 * k, 0.1, WH, 1.2)
    hatch(cv, 120, y1, 1020, 60, t, T["dense"] + 0.4); dim(cv, 120, y1 + 60, 1140, y1 + 60, "768 DIMS, ALL SET", t, T["dense"] + 0.5, 50)
    letter(cv, "PART 2: SPARSE VECTOR", 120, y2 + 80, 28, t, T["sparse"] - 0.3, 40, WH, MONO_B); yy = y2 + 100; stroke(cv, [(120, yy), (1140, yy), (1140, yy + 60), (120, yy + 60)], t, T["sparse"] - 0.2, 0.5, closed=True)
    for k in (5, 17, 26): hatch(cv, 120 + k * 32, yy, 32, 60, t, T["sparse"] + 0.3, MK, 1.0)
    dim(cv, 120, yy + 60, 1140, yy + 60, "30,000 DIMS, ~0.1% SET", t, T["sparse"] + 0.5, 50)
    a_sec = 1 - kc
    if a_sec > 0:                                                                   # the indexes, in section
        for li in range(3):
            z = li * 70; ox, oy = 300, 900
            pts = [iso(0, 0, z, ox, oy, 0.6), iso(400, 0, z, ox, oy, 0.6), iso(400, 300, z, ox, oy, 0.6), iso(0, 300, z, ox, oy, 0.6)]
            stroke(cv, pts, t, T["hnsw"] - 0.3 + 0.15 * li, 0.4, WH, 1.8, True, a_sec)
            rd = np.random.default_rng(li + 3); nodes = [iso(rd.uniform(30, 370), rd.uniform(30, 270), z, ox, oy, 0.6) for _ in range((3, 6, 10)[2 - li])]
            for j in range(len(nodes) - 1): stroke(cv, [nodes[j], nodes[j + 1]], t, T["hnsw"] + 0.2 + 0.1 * li + 0.04 * j, 0.15, WH, 1.6, a=a_sec)
        letter(cv, "SECTION A-A: HNSW (3 LAYERS)", 120, 1020, 24, t, T["hnsw"], 40, WH, a=a_sec)
        for k, l in enumerate(("T12  -> 4, 9, 31", "T77  -> 4, 12", "T301 -> 9, 18, 77")): letter(cv, l, 760, 830 + k * 50, 28, t, T["sidx"] + 0.15 * k, 40, MK, a=a_sec)
        stroke(cv, [(730, 780), (1140, 780), (1140, 990), (730, 990)], t, T["sidx"] - 0.3, 0.5, MK, 2, True, a_sec); letter(cv, "SECTION B-B: INVERTED INDEX", 730, 1020, 24, t, T["sidx"], 40, MK, a=a_sec)
    if kc > 0:                                                                      # memory: two hatched tanks
        for k, (x, v, lab, c) in enumerate(((300, 0.78, "RAM: DENSE + HNSW", WH), (860, 0.31, "RAM: SPARSE INDEX", MK))):
            at = T["mem"] + 0.2 * k; top, bot = 760, 1000; stroke(cv, [(x - 110, top), (x - 110, bot), (x + 110, bot), (x + 110, top)], t, at - 0.3, 0.5, c, 2.6)
            lv = v * ease(ramp(t, at, 1.2)); hatch(cv, x - 108, bot - (bot - top) * lv, 216, (bot - top) * lv, t, at, c, 0.9)
            letter(cv, f"{int(lv * 100)}%", x + 130, bot - (bot - top) * lv + 10, 30, t, at, 40, c, MONO_B); letter(cv, lab, x, bot + 40, 24, t, at, 40, c, align="center")
def s5(cv, t):
    """SHEET 5: option 01, the memory hierarchy in elevation; vectors move from RAM to disk"""
    letter(cv, "OPTION 01", 120, 230, 30, t, L[9] - 0.2, 30, MK, MONO_B); letter(cv, "STORE DENSE VECTORS ON DISK", 120, 290, 46, t, L[9], 40, WH, MONO_B)
    stroke(cv, [(120, 360), (900, 360), (900, 560), (120, 560)], t, L[9] + 0.2, 0.6, closed=True); letter(cv, "RAM", 140, 400, 28, t, L[9] + 0.5, 30)
    stroke(cv, [(120, 720), (900, 720), (900, 920), (120, 920)], t, T["storing"], 0.6, closed=True); letter(cv, "DISK (SSD)", 140, 760, 28, t, T["storing"] + 0.3, 30)
    for k in range(16):
        dk = ease(ramp(t, T["disk"] + 0.04 * k, 0.6)); x = 150 + (k % 8) * 92; y = lerp(430 + (k // 8) * 60, 790 + (k // 8) * 60, dk)
        if t > L[9] + 0.6 + 0.03 * k: cv.drawRect(skia.Rect(x, y, x + 70, y + 44), paint(WH, 1, 2)); hatch(cv, x, y, 70, 44, t, L[9] + 0.8 + 0.03 * k, WH, 0.7)
    stroke(cv, [(980, 460), (980, 820)], t, T["disk"] - 0.2, 0.5, MK, 3)
    if t > T["disk"] + 0.3: cv.drawLine(980, 820, 962, 790, paint(MK, 1, 3)); cv.drawLine(980, 820, 998, 790, paint(MK, 1, 3))
    letter(cv, "VectorParams(on_disk=True)", 1010, 650, 30, t, T["disk"] - 0.4, 40, MK, MONO_B)
    k = prog(t, T["disk"] + 0.2, 0.8)                                                # a revision cloud around the change
    if k > 0:
        p = skia.Path(); cx, cy, rx, ry = 1215, 640, 240, 60; n = 18
        for j in range(n + 1):
            a0 = 2 * math.pi * j / n; x_, y_ = cx + rx * math.cos(a0), cy + ry * math.sin(a0)
            if j == 0: p.moveTo(x_, y_)
            else: pa = 2 * math.pi * (j - 0.5) / n; p.quadTo(cx + rx * 1.15 * math.cos(pa), cy + ry * 1.4 * math.sin(pa), x_, y_)
        pm = skia.PathMeasure(p, False); seg = skia.Path(); pm.getSegment(0, pm.getLength() * k, seg, True); cv.drawPath(seg, paint(MK, 1, 2.6))
    dim(cv, 120, 560, 120, 720, "MOVE", t, T["disk"] + 0.3, -50, MK)
SHEETS = [(s1, 0.75, L[2], "SHEET 1 OF 5", "THE UPLOAD PATH"), (s2, L[2], L[3], "SHEET 2 OF 5", "CONFIGURATION"), (s3, L[3], L[4], "SHEET 3 OF 5", "WHAT WE COVER"),
          (s4, L[4], L[8], "SHEET 4 OF 5", "DENSE VS SPARSE"), (s5, L[8], 999, "SHEET 5 OF 5", "OPTION 01")]
DETAIL = [(0.0, (W / 2, H / 2, 1150)), (0.75, (1590, 300, 200)), (L[2], (1590, 300, 190)), (L[3], (960, 250, 170)), (wd(3, "different") + 0.2, (1640, 280, 170)), (L[4], (1590, 300, 190)),
          (L[8], (W / 2, H / 2, 1150)), (L[9], (1590, 300, 200))]                    # full frame at the open and the chapter, a callout otherwise

_paper = None
def paper():
    global _paper
    if _paper is None:
        s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col(PAPER))
        p = skia.Paint(); p.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), W * 0.8, [col((30, 84, 160)), col((16, 54, 118))], [0, 1])); cv.drawRect(skia.Rect(0, 0, W, H), p)
        for x in range(0, W, 30): cv.drawLine(x, 0, x, H, paint(WH, 0.06 if x % 150 else 0.13, 1))
        for y in range(0, H, 30): cv.drawLine(0, y, W, y, paint(WH, 0.06 if y % 150 else 0.13, 1))
        cv.drawRect(skia.Rect(30, 30, W - 30, H - 30), paint(WH, 0.9, 3)); cv.drawRect(skia.Rect(42, 42, W - 42, H - 42), paint(WH, 0.5, 1.2))
        _paper = s.makeImageSnapshot()
    return _paper
def sheet_image(fn, t):
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.drawImage(paper(), 0, 0); fn(cv, t); return s.makeImageSnapshot()
def title_block(cv, t, sheet, name):
    x, y, w, h = 1330, 780, 560, 270; cv.drawRect(skia.Rect(x, y, x + w, y + h), paint(PAPER, 0.92)); cv.drawRect(skia.Rect(x, y, x + w, y + h), paint(WH, 1, 3))
    f, fb = font(MONO, 20), font(MONO, 27)
    for k, (a, b) in enumerate((("TITLE", "BULK UPLOADS"), ("SHEET", sheet), ("SECTION", name), ("DRAWN", "J. KUPCHANKO"))):
        yy = y + 58 + k * 60; cv.drawLine(x, yy + 20, x + w, yy + 20, paint(WH, 0.6, 1.4)); cv.drawString(a, x + 20, yy, f, paint(WH, 0.8)); cv.drawString(b, x + 160, yy, fb, paint(WH))
def detail_at(t):
    i = max(j for j, d in enumerate(DETAIL) if t >= d[0]); cur = DETAIL[i][1]; prev = DETAIL[i - 1][1] if i else cur; e = inout(ramp(t, DETAIL[i][0], 0.6)); return tuple(lerp(a, b, e) for a, b in zip(prev, cur))
def frame(t, face_im, hide):
    surf = skia.Surface(W, H); cv = surf.getCanvas(); cv.drawImage(paper(), 0, 0)
    i = max(j for j, s in enumerate(SHEETS) if t >= s[1] - 1e-6) if t >= SHEETS[0][1] else 0; fn, s0, s1_, sh, nm = SHEETS[i]
    k = ramp(t, s0, 0.7)
    if i > 0 and k < 1:                                                              # the sheet change: slide over, or zoom into the last
        prev = sheet_image(SHEETS[i - 1][0], t); cur = sheet_image(fn, t); e = inout(k)
        if i in (1, 3):
            cv.drawImage(prev, 0, 0); cv.drawRect(skia.Rect(W * (1 - e) - 30, 0, W * (1 - e), H), paint((0, 0, 0), 0.35, blur=20)); cv.drawImage(cur, W * (1 - e), 0)
        else:
            cv.save(); z = 1 + 1.2 * e; cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-W / 2, -H / 2); cv.drawImage(prev, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), paint(WH, 1 - e)); cv.restore()
            cv.drawImage(cur, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), paint(WH, e))
    else: fn(cv, t)
    title_block(cv, t, sh, nm)
    cx, cy, r = detail_at(t); close = 0.0
    for a, b in hide:
        if a <= t < b + TR: close = max(close, min(ease(ramp(t, a, TR)), 1 - ease(ramp(t, b, TR))))
    r_eff = r * (1 - close)
    img = Image.fromarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGBA")
    if r_eff > 2:                                                                   # DETAIL A: the presenter, through a circular callout
        full = r > 600; d = int(2 * r_eff); fc = E.face_crop(face_im, d, d, 1.0 if full else 1.25)
        if full and r_eff > 600: fc = E.face_crop(face_im, W, H, 1.0); m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).ellipse([cx - r_eff, cy - r_eff, cx + r_eff, cy + r_eff], fill=255); fc.putalpha(m); img.alpha_composite(fc)
        else:
            m = Image.new("L", (d, d), 0); ImageDraw.Draw(m).ellipse([0, 0, d - 1, d - 1], fill=255); fc.putalpha(m); img.alpha_composite(fc, (int(cx - r_eff), int(cy - r_eff)))
        dr = ImageDraw.Draw(img); dr.ellipse([cx - r_eff - 4, cy - r_eff - 4, cx + r_eff + 4, cy + r_eff + 4], outline=WH + (255,), width=5)
        if not full and close < 0.5:
            from PIL import ImageFont
            fnt = ImageFont.truetype(os.path.join(LN.FONTS, MONO), 22); dr.text((cx - 110, cy + r_eff + 18), "DETAIL A · PRESENTER", font=fnt, fill=WH + (255,))
    return img

def plan(p, t0, t1):
    hide = E.hidden_spans(p.look); cuts = sorted({t0, t1} | {x for a, b in hide for x in (a, b) if t0 < x < t1}); S_ = []
    for a, b in zip(cuts, cuts[1:]):
        on = not any(x < b and y > a for x, y in hide)
        S_.append(dict(t0=a, t1=b, kind="graphic", shows_face=on, draw=lambda lt, dur, ctx: frame(ctx["t"], ctx["face"], hide), tr="cut", _hidden=False))
    sfx = [(s[1] - 0.05, E.whoosh(0.025, 0.5)) for s in SHEETS[1:] if t0 <= s[1] < t1]
    for x in (T["up"], T["qd"], T["pay"], T["idx"], T["bg"], T["conf"], T["works"], T["opt"], T["best"], T["dense"], T["sparse"], T["hnsw"], T["sidx"], T["mem"], T["disk"]):
        if t0 <= x < t1: sfx.append((x - 0.3, E.tone(0.35, 2600, 2400, 0.008, noise=0.95)))      # pencil on paper
    return S_, sfx

if __name__ == "__main__":
    a = sys.argv[1:]; p = SF.project()
    if a[:1] == ["stills"]:
        ts = [float(x) for x in a[1:]]; S_, sfx = plan(p, 0, max(ts) + 2); r = E.Renderer(p, S_, 0, p.dur, OUT, sfx, PAPER); print(r.stills(ts, OUT.replace(".mp4", "_sheet.png"), cols=4))
    else:
        t0, t1 = (float(a[0]), float(a[1])) if len(a) >= 2 else (0.0, p.dur)
        S_, sfx = plan(p, t0, t1); E.Renderer(p, S_, t0, t1, OUT if (t0, t1) == (0.0, p.dur) else OUT.replace(".mp4", f"_{int(t0)}-{int(t1)}.mp4"), sfx, PAPER).render()
