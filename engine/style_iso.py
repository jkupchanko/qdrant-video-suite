"""ISOMETRIC MACHINE: one model of the real machine, the camera flies to the part being explained, the way
Branch Education and Jared Owen explain (see paradigm_audit/report.md).

An isometric Qdrant node on a dark grid floor: network card, CPU with a heatsink, six RAM sticks and an SSD,
joined by traces on the board. Data is light moving along the traces. The lid lifts off to show the inside.
Each option is a tag pinned to the part it acts on. Dense and sparse vectors are full and mostly empty slabs
in RAM; HNSW is a hologram graph above them; on_disk sends them down a trace into the SSD. The presenter is
on an isometric monitor standing in the scene, which shows the node's status screen while he looks away.

  python style_iso.py 0 41             sample -> out/iso_0-41.mp4
  python style_iso.py stills 2 6 20    contact sheet
"""
import os, sys, json, math, numpy as np, skia
from PIL import Image
import engine as E
import style_full as SF
W, H = E.W, E.H
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\iso.mp4"
FONTS = r"C:\Users\ADMIN\camera_audit\fonts"
BG, FLOOR, GRIDC = (0x0E, 0x12, 0x1A), (0x14, 0x19, 0x24), (0x1F, 0x27, 0x36)
BOARD, CHASSIS, LIDC, TRACE, DATA, HOT, COOL, DENSE, SPARSE, TAG, WHITE, MUTE = (0x13, 0x4E, 0x3A), (0x3A, 0x41, 0x52), (0x55, 0x5E, 0x72), (0xC9, 0x9A, 0x3A), (0x4F, 0xE3, 0xFF), (0xDC, 0x24, 0x4C), (0x2E, 0xCC, 0x71), (0x7B, 0x6C, 0xFF), (0xFF, 0x7A, 0x6E), (0xFF, 0xC8, 0x57), (0xF2, 0xF4, 0xF8), (0x8D, 0x94, 0xA6)
C30, S30 = math.cos(math.radians(30)), 0.5
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
def shade(c, k): return tuple(max(0, min(255, int(v * k))) for v in c)
def ramp(t, a, d=0.5): return max(0.0, min(1.0, (t - a) / d))
ease, inout, back = E.ease, E.inout, E.back
WORDS = json.load(open(r"C:\Users\ADMIN\camera_audit\styles\out\v2_words.json"))["pieces"]
def wd(i, w, nth=0):
    hits = [t for x, t in WORDS[i]["words"] if x.lower().strip(",.?!").startswith(w.lower())]; return hits[min(nth, len(hits) - 1)]
T = dict(up=wd(0, "uploading"), large=wd(0, "large"), qd=wd(0, "qdrant"), just=wd(0, "just"), pay=wd(1, "payloads"), idx=wd(1, "indexes"), bg=wd(1, "much"),
         conf=wd(2, "configuration"), opt=wd(3, "options"), best=wd(3, "best"), dense=wd(4, "dense"), sparse=wd(4, "sparse"), hnsw=wd(5, "hnsw"),
         sidx=wd(6, "completely"), mem=wd(7, "memory"), perf=wd(7, "performance"), first=wd(8, "first"), storing=wd(9, "storing"), disk=wd(9, "disk"))
LINE = [WORDS[i]["t0"] for i in range(10)]

# ---------------------------------------------------------------- camera: world (x, y, z) -> screen
CAM = [  # (time, focus x, y, z, zoom): the camera flies between these
    (0.0, 380, 250, 40, 1.35), (LINE[1] - 0.3, 400, 260, 40, 1.4), (LINE[1] + 0.9, 470, 230, 30, 1.65), (LINE[2] - 0.2, 470, 230, 30, 1.7),
    (LINE[2] + 0.9, 1420, -760, 40, 0.44), (LINE[3] - 0.2, 1420, -760, 40, 0.45), (LINE[3] + 0.9, 400, 270, 40, 1.3), (LINE[4] - 0.2, 400, 270, 40, 1.32),
    (LINE[4] + 1.0, 640, 250, 70, 2.1), (LINE[7] - 0.2, 650, 250, 90, 2.0), (LINE[7] + 0.9, 520, 270, 50, 1.45), (LINE[8] - 0.2, 520, 270, 50, 1.45),
    (LINE[8] + 1.0, 420, 330, 30, 1.55), (60.0, 420, 330, 30, 1.6)]
def camera(t):
    for (t0, *a), (t1, *b) in zip(CAM, CAM[1:]):
        if t0 <= t < t1: k = inout((t - t0) / max(0.01, t1 - t0)); return [x + (y - x) * k for x, y in zip(a, b)]
    return CAM[-1][1:]
class View:
    def __init__(self, t): fx, fy, fz, z = camera(t); self.z = z; self.fsx, self.fsy = self.raw(fx, fy, fz)
    @staticmethod
    def raw(x, y, z): return (x - y) * C30, (x + y) * S30 - z
    def p(self, x, y, z): sx, sy = self.raw(x, y, z); return skia.Point(W * 0.56 + (sx - self.fsx) * self.z, H * 0.50 + (sy - self.fsy) * self.z)   # framed right of the monitor

def poly(cv, pts, c, a=1.0, stroke=0):
    path = skia.Path(); path.addPoly(pts, True); cv.drawPath(path, paint(c, a, stroke))
def box(cv, v, x, y, z, w, d, h, c, a=1.0, edge=True):
    """three visible faces: top, the +x face (lit) and the +y face (shadow)"""
    P = v.p
    top = [P(x, y, z + h), P(x + w, y, z + h), P(x + w, y + d, z + h), P(x, y + d, z + h)]
    fx = [P(x + w, y, z + h), P(x + w, y + d, z + h), P(x + w, y + d, z), P(x + w, y, z)]
    fy = [P(x, y + d, z + h), P(x + w, y + d, z + h), P(x + w, y + d, z), P(x, y + d, z)]
    poly(cv, fy, shade(c, 0.62), a); poly(cv, fx, shade(c, 0.82), a); poly(cv, top, c, a)
    if edge:
        for f in (top, fx, fy): poly(cv, f, shade(c, 1.25), 0.35 * a, max(1, v.z))
def label(cv, v, anchor, dx, dy, s, c=WHITE, a=1.0, size=30):
    size = int(size * 1.35)                                                       # readable at 1080p
    if a <= 0: return
    p = v.p(*anchor); q = skia.Point(p.x() + dx, p.y() + dy); cv.drawLine(p, q, paint(c, 0.8 * a, 2)); cv.drawCircle(p, 6, paint(c, a))
    f = font("SpaceGrotesk[wght].ttf", size); w = f.measureText(s); x = q.x() - (w + 24 if dx < 0 else 0)
    cv.drawRoundRect(skia.Rect(x - 4, q.y() - size * 0.95, x + w + 24, q.y() + size * 0.45), 8, 8, paint((0x0B, 0x0F, 0x18), 0.85 * a)); cv.drawRoundRect(skia.Rect(x - 4, q.y() - size * 0.95, x + w + 24, q.y() + size * 0.45), 8, 8, paint(c, 0.9 * a, 2))
    cv.drawString(s, x + 10, q.y(), f, paint(c, a))

# ---------------------------------------------------------------- the machine
RAM_X = [560 + i * 30 for i in range(6)]
TRACES = {"in": [(-600, 70, 40), (-60, 70, 40), (40, 70, 16)], "nic_cpu": [(160, 70, 16), (260, 70, 12), (260, 250, 12), (330, 250, 12)],
          "cpu_ram": [(470, 250, 12), (540, 250, 12), (540, 160, 12), (640, 160, 12)], "ram_disk": [(640, 380, 12), (520, 420, 12), (360, 420, 12)]}
def along(path, u):
    seg = [math.dist(a, b) for a, b in zip(path, path[1:])]; L = sum(seg); d = u * L
    for (a, b), s in zip(zip(path, path[1:]), seg):
        if d <= s: k = d / max(1e-6, s); return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))
        d -= s
    return path[-1]
def draw_trace(cv, v, path, glow=0.0):
    pts = [v.p(*q) for q in path]
    for a, b in zip(pts, pts[1:]): cv.drawLine(a, b, paint(TRACE, 0.9, 3 * v.z))
    if glow > 0:
        for a, b in zip(pts, pts[1:]): cv.drawLine(a, b, paint(DATA, 0.25 * glow, 7 * v.z, blur=4))
def packets(cv, v, path, t, rate, a=1.0, c=DATA, tag=False, speed=0.7):
    for k in range(int(rate)):
        u = ((t * speed) + k / rate) % 1; q = v.p(*along(path, u)); cv.drawCircle(q, 7 * v.z, paint(c, a, blur=3)); cv.drawCircle(q, 4 * v.z, paint(WHITE, a))
        if tag: cv.drawRect(skia.Rect(q.x() + 4 * v.z, q.y() - 12 * v.z, q.x() + 11 * v.z, q.y() - 5 * v.z), paint(TAG, a))

def server(cv, v, t, ox=0, oy=0, lid=1.0, ram_heat=0.0, n_ram=6, disk_big=False, glow=1.0, fans=True):
    box(cv, v, ox, oy, 0, 800, 520, 70, CHASSIS); box(cv, v, ox + 10, oy + 10, 70, 780, 500, 4, BOARD, edge=False)
    for name, path in TRACES.items():
        if name != "in": draw_trace(cv, v, [(x + ox, y + oy, z + 62) for x, y, z in path], glow)
    box(cv, v, ox + 40, oy + 40, 74, 120, 60, 30, (0x2E, 0x6F, 0xD8))                                     # network card
    box(cv, v, ox + 330, oy + 180, 74, 140, 140, 22, (0x55, 0x5E, 0x72))                                   # CPU
    for k in range(7): box(cv, v, ox + 336 + k * 19, oy + 186, 96, 8, 128, 40, (0xA7, 0xB1, 0xC2), edge=False)  # heatsink fins
    for i, rx in enumerate(RAM_X[:n_ram]):                                                                  # RAM sticks, warming red as they fill
        c = tuple(int(a + (b - a) * ram_heat) for a, b in zip((0x2E, 0x8F, 0x5A), (0xDC, 0x24, 0x4C))); box(cv, v, ox + rx, oy + 120, 74, 14, 260, 70, c)
    if disk_big:
        for k in range(3): box(cv, v, ox + 80 + k * 90, oy + 350, 74, 80, 140, 60, (0x6A, 0x5B, 0xC8))
    else: box(cv, v, ox + 120, oy + 360, 74, 240, 120, 30, (0x6A, 0x5B, 0xC8))                             # SSD
    if fans:
        q = v.p(ox + 720, oy + 440, 110); cv.save(); cv.translate(q.x(), q.y()); cv.scale(1, 0.55); cv.rotate((t * 400) % 360)
        for k in range(4): cv.rotate(90); cv.drawOval(skia.Rect(-6 * v.z, -34 * v.z, 6 * v.z, 0), paint(MUTE, 0.8))
        cv.restore()
    if lid > 0: box(cv, v, ox, oy, 74 + 320 * (1 - lid), 800, 520, 12, LIDC, lid)

def slabs(cv, v, t, dense_a, sparse_a, drop=0.0):
    """vectors as slabs in RAM: a dense one is lit all along, a sparse one has only a few cells lit"""
    for i in range(10):
        x0, y0, z0 = 600, 140 + i * 22, 150
        a = dense_a if i < 6 else sparse_a
        if a <= 0: continue
        if i < 6 and drop > 0:
            k = ease(ramp(drop, i * 0.06, 0.5)); x0, y0, z0 = x0 + (180 - x0) * k, y0 + (380 + i * 14 - y0) * k, z0 + (110 - z0) * k
        for c in range(12):
            on = True if i < 6 else (c in ((i * 5) % 12, (i * 7 + 3) % 12))
            box(cv, v, x0 + c * 9, y0, z0, 8, 16, 6, (DENSE if i < 6 else SPARSE) if on else (0x2A, 0x30, 0x40), a * (1 if on else 0.6), edge=False)

def hologram(cv, v, t, a):
    rd = np.random.default_rng(2)
    for li, z in enumerate((260, 330, 400)):
        n = (14, 7, 3)[li]; pts = [v.p(600 + rd.uniform(0, 110), 140 + rd.uniform(0, 130), z) for _ in range(n)]
        corners = [v.p(590, 130, z), v.p(720, 130, z), v.p(720, 280, z), v.p(590, 280, z)]; poly(cv, corners, DATA, 0.08 * a); poly(cv, corners, DATA, 0.35 * a, 2)
        for j in range(n - 1): cv.drawLine(pts[j], pts[j + 1], paint(DATA, 0.7 * a, 2))
        for q in pts: cv.drawCircle(q, 5, paint(WHITE, a))

def drawers(cv, v, t, a):
    for k, term in enumerate(("t12", "t77", "t301", "t5")):
        box(cv, v, 760, 120 + k * 70, 74, 60, 60, 40 + 20 * a, (0x8A, 0x5A, 0x3C), a)
        q = v.p(790, 150 + k * 70, 140 + 20 * a); f = font("GeistMono-Medium.ttf", 24); cv.drawString(term, q.x() - 20, q.y(), f, paint(WHITE, a))

MON = (60, 640, 480, 330)                                                     # the presenter's monitor, bottom left, in the world's isometric slant
def monitor_quad():
    x, y, w, h = MON; slope = math.tan(math.radians(14)); return [(x, y), (x + w, y + w * slope), (x + w, y + w * slope + h), (x, y + h)]

def scene(cv, t):
    v = View(t); cv.clear(col(BG))
    for k in range(-30, 40):                                                     # the floor grid
        a, b = v.p(k * 100, -2000, 0), v.p(k * 100, 3000, 0); cv.drawLine(a, b, paint(GRIDC, 0.7, 1)); a, b = v.p(-2000, k * 100, 0), v.p(4000, k * 100, 0); cv.drawLine(a, b, paint(GRIDC, 0.7, 1))
    three = ramp(t, LINE[2] - 0.2, 0.6) * (1 - ramp(t, LINE[3], 0.6))
    if three > 0:
        for k, (n_ram, big) in enumerate(((6, False), (2, True), (3, False))):
            if k == 0: continue
            server(cv, v, t, ox=900 * k, oy=-900 * k, lid=0, n_ram=n_ram, disk_big=big, glow=0.5)        # a row across the screen
    lid = 1 - ease(ramp(t, T["just"] - 0.2, 0.9)); heat = ease(ramp(t, T["mem"] - 0.3, 1.0)) * (1 - ease(ramp(t, T["disk"] + 0.2, 1.2)))
    draw_trace(cv, v, TRACES["in"], 1.0)
    server(cv, v, t, lid=lid, ram_heat=heat, glow=ease(ramp(t, T["up"], 0.6)))
    rate = 3 + 9 * ease(ramp(t, T["large"] - 0.2, 0.6)); packets(cv, v, TRACES["in"], t, rate, speed=0.9)
    if lid < 1:
        for name in ("nic_cpu", "cpu_ram"): packets(cv, v, [(x, y, z + 62) for x, y, z in TRACES[name]], t + 0.3, 4, ease(ramp(t, T["just"], 0.6)), tag=t > T["pay"] - 0.2)
    if T["idx"] - 0.3 < t < LINE[2]: hologram(cv, v, t, ease(ramp(t, T["idx"] - 0.3, 0.6)) * 0.7)
    if T["bg"] - 0.2 < t < LINE[2]:
        for k, (x, y) in enumerate(((150, 80), (400, 200), (650, 300), (200, 400))):
            q = v.p(x, y, 110); cv.drawCircle(q, 7, paint(COOL, 0.5 + 0.5 * math.sin(t * 8 + k)))
    if three > 0:
        for k, (lab, ox) in enumerate((("RAM-heavy", 0), ("disk-heavy", 900), ("compact", 1800))): label(cv, v, (ox + 400, 260 - ox, 160), 0, -170, lab, WHITE, three, 46)
    if T["opt"] - 0.4 < t < LINE[4]:                                              # options pinned to the parts they act on
        tags = [((240, 420, 104), -40, 120, "on_disk", HOT), ((400, 250, 120), -260, -120, "payload index first", HOT), ((640, 250, 150), 160, -160, "quantization", HOT),
                ((240, 420, 104), 160, 130, "sparse index on_disk", HOT), ((100, 70, 104), -120, -130, "batch size", TAG), ((400, 250, 150), 150, -260, "upload workers", TAG), ((800, 520, 74), 120, 90, "shards", TAG)]
        for k, (anc, dx, dy, s, c) in enumerate(tags):
            a = ease(ramp(t, (T["opt"] if k < 4 else T["best"]) - 0.3 + 0.12 * (k % 4), 0.35)) * (1 - ease(ramp(t, LINE[4] - 0.3, 0.3))); label(cv, v, anc, dx, dy, s, c, a, 28)
    da = ease(ramp(t, T["dense"] - 0.3, 0.5)); sa = ease(ramp(t, T["sparse"] - 0.3, 0.5))
    if t > LINE[4] - 0.1:
        slabs(cv, v, t, da, sa, drop=max(0.0, t - T["disk"]))
        label(cv, v, (650, 140, 160), -180, -120, "dense: every value", DENSE, da * (1 - ramp(t, LINE[8], 0.4)), 30); label(cv, v, (650, 330, 160), 160, 60, "sparse: a few values", SPARSE, sa * (1 - ramp(t, T["sidx"] - 0.4, 0.3)), 30)
    if T["hnsw"] - 0.3 < t < LINE[8]: hologram(cv, v, t, ease(ramp(t, T["hnsw"] - 0.3, 0.6))); label(cv, v, (660, 210, 400), 120, -60, "HNSW", DATA, ease(ramp(t, T["hnsw"] - 0.2, 0.4)), 34)
    if T["sidx"] - 0.3 < t < LINE[8]: drawers(cv, v, t, ease(ramp(t, T["sidx"] - 0.3, 0.5))); label(cv, v, (790, 330, 140), 140, 40, "sparse index", TAG, ease(ramp(t, T["sidx"], 0.4)), 30)
    if T["mem"] - 0.3 < t < LINE[8]: label(cv, v, (560, 380, 144), -120, 170, "RAM filling up", HOT, heat, 32)
    if T["perf"] - 0.3 < t < LINE[8]:
        q = v.p(400, 250, 150); g = ease(ramp(t, T["perf"] - 0.3, 0.4)); cv.drawArc(skia.Rect(q.x() - 90, q.y() - 220, q.x() + 90, q.y() - 40), 180, 180, False, paint(WHITE, g, 12))
        ang = math.radians(180 + 180 * (0.7 - 0.4 * heat + 0.05 * math.sin(t * 10))); cv.drawLine(skia.Point(q.x(), q.y() - 130), skia.Point(q.x() + 80 * math.cos(ang), q.y() - 130 + 80 * math.sin(ang)), paint(HOT, g, 6))
    if t > T["first"] - 0.3:
        b = back(ramp(t, T["first"] - 0.3, 0.45)); label(cv, v, (200, 470, 104), -30, 230, "option 1: vectors on disk", HOT, min(1, b), 34)
    if t > T["disk"] - 0.2: packets(cv, v, [(x, y, z + 62) for x, y, z in TRACES["ram_disk"]], t, 6, ease(ramp(t, T["disk"] - 0.2, 0.4)), c=DENSE)
    return v

def frame(t, face_im, show_face):
    surf = skia.Surface(W, H); cv = surf.getCanvas(); scene(cv, t)
    q = monitor_quad(); x, y, w, h = MON; slope = math.tan(math.radians(14))
    bez = [skia.Point(a - 14 * (i in (0, 3)) + 14 * (i in (1, 2)), b - 14 * (i in (0, 1)) + 14 * (i in (2, 3))) for i, (a, b) in enumerate(q)]
    poly(cv, [skia.Point(x + w * 0.45, y + h + w * slope * 0.45), skia.Point(x + w * 0.55, y + h + w * slope * 0.55), skia.Point(x + w * 0.58, y + h + 70 + w * slope * 0.58), skia.Point(x + w * 0.42, y + h + 70 + w * slope * 0.42)], (0x2A, 0x30, 0x3C))
    poly(cv, bez, (0x22, 0x28, 0x33)); poly(cv, [skia.Point(*p) for p in q], (0x05, 0x08, 0x0E))
    if not show_face:                                                            # the node's status screen
        f = font("GeistMono-Medium.ttf", 26)
        for k, s in enumerate(("QDRANT NODE", "status: ok", f"points: {int(min(t, 40) * 52000):,}", "optimizer: running")):
            cv.save(); cv.translate(x + 30, y + 60 + k * 50 + 30 * slope); cv.skew(0, slope); cv.drawString(s, 0, 0, f, paint(COOL if k == 1 else WHITE)); cv.restore()
    img = Image.fromarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGBA")
    if show_face:                                                                # the face sheared onto the monitor's slanted plane
        fw, fh = w, h; f = E.face_crop(face_im, fw, fh, 1.1).convert("RGBA"); out_h = int(h + w * slope) + 2
        patch = f.transform((w, out_h), Image.AFFINE, (1, 0, 0, -slope, 1, 0), resample=Image.BILINEAR)
        mask = Image.new("L", (fw, fh), 255).transform((w, out_h), Image.AFFINE, (1, 0, 0, -slope, 1, 0)); img.paste(patch, (x, y), mask)
    return img

def plan(p, t0, t1):
    hide = E.hidden_spans(p.look); cuts = sorted({t0, t1} | {x for a, b in hide for x in (a, b) if t0 < x < t1}); S_ = []
    for a, b in zip(cuts, cuts[1:]):
        on = not any(x < b and y > a for x, y in hide)
        S_.append(dict(t0=a, t1=b, kind="graphic", shows_face=on, draw=(lambda on_: lambda lt, dur, ctx: frame(ctx["t"], ctx["face"], on_))(on), tr="cut", _hidden=False))
    sfx = [(c[0], E.whoosh(0.03, 0.5)) for c in CAM[1:] if t0 <= c[0] < t1] + [(x, E.tone(0.07, 600, 900, 0.03)) for x in (T["just"], T["idx"], T["hnsw"], T["disk"]) if t0 <= x < t1]
    return S_, sfx

if __name__ == "__main__":
    a = sys.argv[1:]; p = SF.project()
    if a[:1] == ["stills"]:
        ts = [float(x) for x in a[1:]]; S_, sfx = plan(p, 0, max(ts) + 2); r = E.Renderer(p, S_, 0, p.dur, OUT, sfx, BG); print(r.stills(ts, OUT.replace(".mp4", "_sheet.png"), cols=4))
    else:
        t0, t1 = (float(a[0]), float(a[1])) if len(a) >= 2 else (0.0, p.dur)
        S_, sfx = plan(p, t0, t1); E.Renderer(p, S_, t0, t1, OUT if (t0, t1) == (0.0, p.dur) else OUT.replace(".mp4", f"_{int(t0)}-{int(t1)}.mp4"), sfx, BG).render()
