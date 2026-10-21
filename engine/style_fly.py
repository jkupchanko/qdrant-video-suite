"""FLY-THROUGH: nothing stands still. Every idea is a panel placed in one 3D world, and the camera flies through
it continuously: it swoops to each panel as its word is said, banks between the workload cards, rides along
the roadmap past each milestone, dives down through the HNSW layers, rushes to OPTION 01 and tilts down to follow
vectors falling from RAM to disk. A particle field streaks past to sell the speed; panels away from the focus go
soft. The presenter is a floating card that swings and tilts with the camera's moves, springs to a new place
each section, opens to full screen on key lines and flips away in a look-away.

  python style_fly.py 0 41             sample -> out/fly_0-41.mp4
  python style_fly.py stills 2 6 20    contact sheet
"""
import os, sys, math, numpy as np, skia
from PIL import Image, ImageDraw
import engine as E
import style_full as SF
import style_launch as LN
W, H = E.W, E.H; TR = E.TR
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\fly.mp4"
font, col, paint, text, ramp, ease, inout, back, lerp = LN.font, LN.col, LN.paint, LN.text, LN.ramp, E.ease, E.inout, E.back, LN.lerp
T, L, wd = LN.T, LN.L, LN.wd
NAVY, TXT, MUTE, RED, RED_L, VIOL, VIOL_L, TEAL_L, AMBER, GREEN = LN.NAVY, LN.TXT, LN.MUTE, LN.RED, LN.RED_L, LN.VIOL, LN.VIOL_L, LN.TEAL_L, LN.AMBER, LN.GREEN
SANS, SANS_B, MONO = LN.SANS, LN.SANS_B, LN.MONO
F = 1100.0; SS = 1.35                                                          # focal length (px); panels are drawn 1.35x for sharp close-ups
def ap(t, at, d=0.45): return ease(ramp(t, at - 0.25, d))

# ---------------------------------------------------------------- the world: panels
class P:
    def __init__(s, name, c, w, h, draw, at=0.0, yaw=0.0, flat=False, until=1e9): s.name, s.c, s.w, s.h, s.draw, s.at, s.yaw, s.flat, s.until = name, np.array(c, float), w, h, draw, at, yaw, flat, until
    def corners(s):
        hw, hh = s.w / 2, s.h / 2; a = math.radians(s.yaw); ca, sa = math.cos(a), math.sin(a)
        if s.flat: loc = [(-hw, 0, hh), (hw, 0, hh), (hw, 0, -hh), (-hw, 0, -hh)]           # lying flat: far edge first, so the image reads from above
        else: loc = [(-hw, -hh, 0), (hw, -hh, 0), (hw, hh, 0), (-hw, hh, 0)]
        return [s.c + np.array([x * ca + z * sa, y, -x * sa + z * ca]) for x, y, z in loc]
def card(c, w, h, a, accent=None, glow=0.0): LN.glass(c, 0, 0, w, h, a, accent=accent, glow=glow, shadow=False)
def d_code(c, w, h, t): LN.code_window(c, 0, 0, w, h, [("from qdrant_client import QdrantClient", None), ('client = QdrantClient("http://localhost:6333")', None), ("", None), ('points = load_points("data.jsonl")', None), ('client.upload_points("docs", points, batch_size=256)', T["up"] - 0.2)], t, 1.0, hl=(4, ap(t, T["up"] + 0.6)), cps=70)
def d_count(c, w, h, t):
    card(c, w, h, 1.0, VIOL_L, 0.5); n = 1_000_000 * ease(ramp(t, T["large"], 6.5)); text(c, LN.counter(n), w / 2, h * 0.62, 150, TXT, 1, SANS_B, max_w=w - 60, align="center"); text(c, "points uploaded", w / 2, h * 0.86, 34, MUTE, 1, MONO, align="center")
def d_node(c, w, h, t):
    card(c, w, h, 1.0, RED, 0.6 + 0.4 * math.sin(t * 2.5) ** 2); LN.logo(c, 40, 40, 70); text(c, "Qdrant", 130, 98, 60, TXT, 1, SANS_B)
    fill = min(1.0, ease(ramp(t, T["large"], 6.5))); text(c, "vectors", 40, 200, 32, MUTE, ap(t, T["vec"]), MONO)
    for k in range(30): c.drawRoundRect(skia.Rect(40 + k * 31, 225, 40 + k * 31 + 22, 300), 5, 5, paint(VIOL if k < 30 * fill else LN.DIM, ap(t, T["vec"])))
    text(c, "doesn't just store vectors", 40, h - 60, 40, TXT, ap(t, T["store"]), SANS_B)
def sub(name, fn, at, colr):
    def d(c, w, h, t): card(c, w, h, 1.0, colr, 0.4); text(c, name, 36, 70, 46, TXT, 1, SANS_B); fn(c, t, (36, 100, w - 72, h - 130), 1.0, 1.4, at)
    return d
def d_one(c, w, h, t):
    card(c, w, h, 1.0, RED if t > T["works"] else None, 0.6); text(c, "One config", 50, h * 0.48, 110, TXT, 1, SANS_B); text(c, "for every workload?", 50, h * 0.8, 60, MUTE, 1, SANS_B)
    k = ease(ramp(t, T["works"], 0.4))
    if k > 0: c.drawLine(40, h * 0.42, 40 + (w - 80) * k, h * 0.42, paint(RED, 1, 12))
def d_work(k):
    name, stat, cfg, colr = LN.WORKLOADS[k]
    def d(c, w, h, t):
        card(c, w, h, 1.0, colr, 0.5); text(c, name, 40, 100, 64, TXT, 1, SANS_B, max_w=w - 80); text(c, stat, 40, 160, 34, MUTE, 1, MONO, max_w=w - 80)
        good = ap(t, T["wf"] + 0.2 + 0.15 * k); bad = ap(t, T["works"] + 0.15 * k) * (1 - good)
        if bad > 0: LN.pill(c, "× default", 40, h - 60, RED_L, bad, 34)
        if good > 0: LN.pill(c, cfg, 40, h - 60, GREEN, good, 32)
    return d
def d_chip(k):
    num, name, colr = LN.ROAD[k]
    def d(c, w, h, t):
        card(c, w, h, 1.0, colr, 0.7); c.drawCircle(80, h / 2, 46, paint(colr, 1, 6)); text(c, num, 80, h / 2 + 22, 60, colr, 1, SANS_B, align="center")
        text(c, name, 150, h / 2 + 20, 54, TXT, 1, SANS_B, max_w=w - 180); text(c, "OPTION" if k < 4 else "BEST PRACTICE", 150, h / 2 - 34, 26, MUTE, 1, MONO)
    return d
def d_vs(c, w, h, t): text(c, "Dense", w * 0.27, h * 0.7, 150, VIOL_L, ap(t, T["diff"]), SANS_B, align="center"); text(c, "vs", w * 0.52, h * 0.7, 90, MUTE, ap(t, T["diff"] + 0.1), SANS_B, align="center"); text(c, "Sparse", w * 0.77, h * 0.7, 150, RED_L, ap(t, T["diff"] + 0.2), SANS_B, align="center")
def d_vec(dense):
    def d(c, w, h, t):
        card(c, w, h, 1.0, VIOL_L if dense else RED_L, 0.5); text(c, "Dense vector" if dense else "Sparse vector", 40, 80, 56, VIOL_L if dense else RED_L, 1, SANS_B)
        text(c, "768 dims · every value set" if dense else "30,000 dims · ~0.1% set", 40, 130, 32, MUTE, 1, MONO); LN.bars_viz(c, (40, 170, w - 80, h - 210), t, 1.0, dense, 1.4)
    return d
def d_layer(li):
    def d(c, w, h, t):
        g = ease(ramp(t, T["hnsw"] + 0.25 * li, 0.8)); c.drawRoundRect(skia.Rect(0, 0, w, h), 30, 30, paint(VIOL, 0.12)); c.drawRoundRect(skia.Rect(0, 0, w, h), 30, 30, paint(VIOL_L, 0.7, 4))
        rd = np.random.default_rng(li + 7); n = (4, 8, 16)[li]; pts = [(rd.uniform(80, w - 80), rd.uniform(80, h - 80)) for _ in range(n)]
        for i in range(n):
            j = (i + 1) % n
            if i / n < g: c.drawLine(*pts[i], *pts[j], paint(VIOL_L, 0.9, 5))
        for p_ in pts: c.drawCircle(*p_, 14, paint(TXT))
        text(c, f"layer {2 - li}", 50, 80, 50, VIOL_L, 1, MONO)
    return d
def d_inv(c, w, h, t):
    card(c, w, h, 1.0, RED_L, 0.5); text(c, "Inverted index", 40, 80, 56, RED_L, 1, SANS_B)
    for k, (term, posts) in enumerate((("t12", "4 · 9 · 31"), ("t77", "4 · 12"), ("t301", "9 · 18 · 77"))):
        a = ap(t, T["sidx"] + 0.15 * k); text(c, term, 40, 180 + k * 80, 46, RED_L, a, MONO); text(c, "->  doc " + posts, 190, 180 + k * 80, 46, TXT, a, MONO)
def d_gauge(dense):
    def d(c, w, h, t):
        card(c, w, h, 1.0, VIOL_L if dense else RED_L, 0.4); v = (0.78 if dense else 0.31) * ease(ramp(t, T["mem"] + (0 if dense else 0.2), 1.4))
        LN.gauge(c, w / 2, h * 0.52, h * 0.3, v, VIOL_L if dense else RED_L, 1.0, "RAM · dense + HNSW" if dense else "RAM · sparse index", f"{int(round(v * 100))}%", 1.6)
    return d
def d_opt(c, w, h, t): text(c, "OPTION 01", 10, 90, 64, RED_L, 1, MONO); text(c, "Store dense vectors", 10, 250, 140, TXT, 1, SANS_B, max_w=w - 20); text(c, "on disk", 10, 400, 140, TXT, 1, SANS_B)
DROP = [T["disk"] + 0.05 * k for k in range(16)]
def d_ram(c, w, h, t):
    card(c, w, h, 1.0, RED, 0.5); text(c, "RAM", 40, 80, 60, TXT, 1, SANS_B); gb = lerp(6.8, 2.1, ease(ramp(t, T["disk"] + 0.3, 1.4))); text(c, f"{gb:.1f} GB", w - 40, 80, 60, RED_L if gb > 3 else GREEN, 1, SANS_B, align="right")
    for k in range(16):
        if t < DROP[k]: c.drawRoundRect(skia.Rect(40 + (k % 8) * 115, 130 + (k // 8) * 110, 40 + (k % 8) * 115 + 95, 130 + (k // 8) * 110 + 85), 12, 12, paint(VIOL))
def d_disk(c, w, h, t):
    card(c, w, h, 1.0, TEAL_L if t > T["disk"] else None, 0.6); text(c, "Disk (SSD)", 40, 80, 60, TXT, 1, SANS_B)
    for k in range(16):
        r_ = skia.Rect(40 + (k % 8) * 115, 130 + (k // 8) * 110, 40 + (k % 8) * 115 + 95, 130 + (k // 8) * 110 + 85); c.drawRoundRect(r_, 12, 12, paint((255, 255, 255), 0.08))
        if t > DROP[k] + 0.7: c.drawRoundRect(r_, 12, 12, paint(LN.TEAL))
def d_flag(c, w, h, t): LN.code_window(c, 0, 0, w, h, [("models.VectorParams(", None), ("    size=768,", None), ("    on_disk=True,", T["disk"] - 0.5), (")", None)], t, 1.0, title="1_on_disk.py", hl=(2, ap(t, T["disk"])), cps=60)
def d_tile(c, w, h, t): c.drawRoundRect(skia.Rect(0, 0, w, h), 12, 12, paint(VIOL)); c.drawRoundRect(skia.Rect(0, 0, w, h), 12, 12, paint(VIOL_L, 0.8, 3))

ROAD_Z = [11800 + 900 * k for k in range(7)]; ROAD_X = [650 * math.sin(k * 0.95) for k in range(7)]
PANELS = [P("code", (0, 0, 0), 1000, 560, d_code, 0.5), P("count", (760, -180, 1700), 780, 330, d_count, T["large"] - 0.3, -25), P("node", (0, 0, 3300), 1060, 600, d_node, T["qd"] - 0.4),
          P("pay", (-1150, 0, 4300), 820, 420, sub("Payloads", LN.TAG_PANEL, T["pay"], AMBER), T["pay"] - 0.3, 35), P("idx", (1150, 0, 4300), 820, 420, sub("Indexes", LN.IDX_PANEL, T["idx"], VIOL_L), T["idx"] - 0.3, -35),
          P("bg", (0, 760, 4300), 900, 420, sub("Background work", LN.BG_PANEL, T["bg"], GREEN), T["bg"] - 0.3),
          P("one", (0, -760, 9300), 1100, 440, d_one, L[2] - 0.4), P("w0", (-900, -150, 9100), 820, 400, d_work(0), T["conf"] - 0.3, 22), P("w1", (0, 620, 9400), 820, 400, d_work(1), T["conf"] - 0.1),
          P("w2", (900, -150, 9100), 820, 400, d_work(2), T["conf"] + 0.1, -22)] + \
         [P(f"r{k}", (ROAD_X[k], -40, ROAD_Z[k]), 760, 220, d_chip(k), wd(3, "different") + 0.2 * k - 0.6, -25 * math.cos(k * 0.95)) for k in range(7)] + \
         [P("vs", (0, 0, 19000), 1300, 360, d_vs, L[4] - 0.2), P("dense", (-650, 0, 20600), 900, 520, d_vec(True), T["dense"] - 0.4, 18), P("sparse", (650, 0, 20600), 900, 520, d_vec(False), T["sparse"] - 0.4, -18)] + \
         [P(f"l{li}", (-650, 650 + li * 420, 21000), 900, 700, d_layer(li), T["hnsw"] - 0.5, 0, True) for li in range(3)] + \
         [P("inv", (850, 900, 21100), 900, 460, d_inv, T["sidx"] - 0.4, -25), P("g0", (-480, 0, 23200), 860, 560, d_gauge(True), T["mem"] - 0.4, 10), P("g1", (480, 0, 23200), 860, 560, d_gauge(False), T["mem"] - 0.2, -10),
          P("opt", (0, 0, 27200), 1400, 520, d_opt, T["first"] - 0.4), P("ram", (0, -260, 29200), 1000, 360, d_ram, L[9] - 0.2), P("disk", (0, 620, 29200), 1000, 360, d_disk, T["storing"] - 0.3),
          P("flag", (900, 120, 28900), 760, 400, d_flag, T["disk"] - 0.8, -25)]

# ---------------------------------------------------------------- the camera: keyed position and look-at point, roll; moves lead the word
def look(name, dz=1080, dx=0.0, dy=0.0):
    p = next(q for q in PANELS if q.name == name).c; return (p[0] + dx, p[1] + dy, p[2] - dz), tuple(p)
KEYS = [(0.0, (0, -60, -1700), (0, 0, 0), 0), (0.75, (-120, -40, -1300), (0, 0, 0), -2), (T["large"] - 0.3, (420, -160, 350), (760, -180, 1700), 3),
        (T["qd"] - 0.3, *look("node", 1450), 0), (T["vec"] - 0.3, (160, 80, 2450), (160, 80, 3300), -2), (L[1] - 0.1, (0, -260, 1500), (0, 200, 3900), 0),
        (T["pay"] - 0.3, (-560, -60, 3150), (-1150, 0, 4300), -6), (T["idx"] - 0.3, (560, -60, 3150), (1150, 0, 4300), 6), (T["bg"] - 0.3, (0, 120, 3050), (0, 760, 4300), 0),
        (L[2] - 0.3, *look("one", 1350), 0), (T["conf"] - 0.3, (-620, -120, 7900), (-900, -150, 9100), -12), (T["conf"] + 0.0, (0, 300, 8100), (0, 620, 9400), 0),
        (T["conf"] + 0.3, (620, -120, 7900), (900, -150, 9100), 12), (T["works"] - 0.2, (-380, -260, 6900), (-380, -120, 9250), 0)] + \
       [(wd(3, "different") + 0.22 * k - 0.4, (ROAD_X[k] * 0.55, -160, ROAD_Z[k] - 1250), (ROAD_X[k], -40, ROAD_Z[k]), -8 * math.sin(k * 0.95)) for k in range(7)] + \
       [(L[4] - 0.3, *look("vs", 1500), 0), (T["dense"] - 0.35, (-480, -40, 19350), (-650, 0, 20600), -5), (T["sparse"] - 0.35, (480, -40, 19350), (650, 0, 20600), 5),
        (T["hnsw"] - 0.45, (-650, -500, 19900), (-650, 900, 21000), 0), (T["hnsw"] + 0.8, (-650, 380, 20350), (-650, 1500, 21050), -4),
        (T["sidx"] - 0.35, (520, 760, 19950), (850, 900, 21100), 6), (T["mem"] - 0.35, (0, -40, 21850), (0, 0, 23200), 0), (T["perf"] + 0.4, (0, -20, 22250), (0, 0, 23200), 2),
        (L[8] + 0.2, (0, -40, 24600), (0, 0, 27200), 0), (T["first"] - 0.2, *look("opt", 1500), 0), (L[9] - 0.2, (0, -330, 27950), (0, -260, 29200), 0),
        (T["storing"] - 0.1, (0, 60, 27700), (0, 180, 29200), 0), (T["disk"] - 0.2, (250, 260, 27700), (300, 600, 29200), 3), (T["disk"] + 1.5, (200, 420, 27850), (150, 620, 29200), -2)]
KEYS = [(k[0], tuple(np.array(k[1]) + (np.array(k[2]) - np.array(k[1])) * 0.18), k[2], k[3]) for k in KEYS]
def cam_at(t):
    ks = KEYS; i = max(j for j, k in enumerate(ks) if t >= k[0] - 0.35); a, b = ks[max(0, i - 1)], ks[i]
    d = min(0.9, max(0.35, b[0] - a[0])); e = inout(ramp(t, b[0] - 0.35, d)) if i else 1.0
    C = np.array([lerp(x, y, e) for x, y in zip(a[1], b[1])]); Q = np.array([lerp(x, y, e) for x, y in zip(a[2], b[2])]); roll = lerp(a[3], b[3], e)
    C = C + np.array([30 * math.sin(t * 0.7), 18 * math.sin(t * 0.9 + 1), 60 * (t % 1000) * 0.0 + 40 * math.sin(t * 0.5)])   # it never stops: a slow sway
    return C, Q, roll
def basis(C, Q, roll):
    f = Q - C; f = f / (np.linalg.norm(f) + 1e-9); up = np.array([0, -1.0, 0]); r = np.cross(f, up); r = r / (np.linalg.norm(r) + 1e-9); u = np.cross(r, f)    # world y points down
    a = math.radians(roll); r2 = r * math.cos(a) + u * math.sin(a); u2 = -r * math.sin(a) + u * math.cos(a); return r2, u2, f
def project(pts, C, R, Uv, Fv, cx, cy):
    d = np.asarray(pts) - C; x, y, z = d @ R, d @ Uv, d @ Fv; return np.stack([cx + F * x / np.maximum(z, 1e-3), cy - F * y / np.maximum(z, 1e-3)], -1), z

# ---------------------------------------------------------------- the presenter's floating card
SPOTS = dict(full=(0, 0, W, H, 0), s1=(W - 60 - 460, H - 60 - 460, 460, 460, 26), s2=(60, 210, 480, 660, 26), s3=(W - 60 - 420, 60, 420, 420, 26), s4=(60, H - 60 - 440, 440, 440, 26), s5=(W - 60 - 480, 210, 480, 660, 26))
SKEYS = [(0.0, "full"), (0.75, "s1"), (L[2], "s2"), (L[3], "full"), (wd(3, "different") - 0.25, "s3"), (L[4], "s4"), (L[8], "full"), (L[9], "s5")]
LENS = dict(full=(W / 2, H / 2), s1=(W * 0.43, H * 0.44), s2=(W * 0.60, H * 0.5), s3=(W * 0.44, H * 0.56), s4=(W * 0.58, H * 0.44), s5=(W * 0.41, H * 0.5))
def spot_at(t):
    i = max(j for j, k in enumerate(SKEYS) if t >= k[0]); a, b = SPOTS[SKEYS[max(0, i - 1)][1]], SPOTS[SKEYS[i][1]]; e = back(ramp(t, SKEYS[i][0], 0.65), 1.2) if i else 1.0
    la, lb = LENS[SKEYS[max(0, i - 1)][1]], LENS[SKEYS[i][1]]; el = inout(ramp(t, SKEYS[i][0], 0.65)) if i else 1.0
    return tuple(lerp(x, y, e) for x, y in zip(a, b)), (lerp(la[0], lb[0], el), lerp(la[1], lb[1], el)), SKEYS[i][1]
def face_card(img, face_im, t, hide, swing):
    (x, y, w, h, r), _, name = spot_at(t); full = w > 1500
    flip = 0.0
    for a, b in hide:
        if a <= t < b + TR: flip = max(flip, min(ease(ramp(t, a, TR)), 1 - ease(ramp(t, b, TR))))
    if flip >= 0.999 or w < 20: return
    if full: fc = E.face_crop(face_im, W, H, 1.0 + 0.06 * ((t * 0.15) % 1)).convert("RGBA"); img.alpha_composite(fc); return
    bob = 10 * math.sin(t * 1.6); x += swing[0] * 0.35; y += bob + swing[1] * 0.2
    fc = E.face_crop(face_im, int(w), int(h), 1.12).convert("RGBA"); m = Image.new("L", (int(w), int(h)), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, int(w) - 1, int(h) - 1], radius=int(r), fill=255)
    fc.putalpha(m); ImageDraw.Draw(fc).rounded_rectangle([1, 1, int(w) - 2, int(h) - 2], radius=int(r), outline=(180, 168, 255, 230), width=4)
    ry = max(-28, min(28, -swing[0] * 0.05)) + flip * 90; rx = max(-14, min(14, swing[1] * 0.04)); s = skia.Surface(W, H); cv = s.getCanvas()
    sk = skia.Image.fromarray(np.ascontiguousarray(np.asarray(fc)), colorType=skia.kRGBA_8888_ColorType); mtx = LN.persp((x, y, w, h), ry=ry, rx=rx, f=1400)
    cv.save(); cv.translate(0, 22); cv.concat(mtx); cv.drawRoundRect(skia.Rect(x, y, x + w, y + h), r, r, paint((0, 0, 0), 0.5, blur=26)); cv.restore()
    cv.save(); cv.concat(mtx); cv.drawImage(sk, x, y, skia.SamplingOptions(skia.FilterMode.kLinear)); cv.restore()
    img.alpha_composite(Image.fromarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)))

# ---------------------------------------------------------------- frame
RD = np.random.default_rng(11); STARS = np.stack([RD.uniform(-4500, 4500, 6000), RD.uniform(-2800, 2800, 6000), RD.uniform(-2500, 32000, 6000)], -1)
GRID_Y = 1500
_bg = None
def bg():
    global _bg
    if _bg is None:
        s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col((6, 9, 18))); cv.drawCircle(W * 0.3, H * 0.2, 900, paint(VIOL, 0.16, blur=260)); cv.drawCircle(W * 0.8, H * 0.9, 800, paint(RED, 0.09, blur=260)); _bg = s.makeImageSnapshot()
    return _bg
def frame(t, face_im, hide):
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.drawImage(bg(), 0, 0)
    _, (cx, cy), _ = spot_at(t); C, Q, roll = cam_at(t); R, U, Fv = basis(C, Q, roll)
    C0, Q0, r0 = cam_at(t - 1 / 30); R0, U0, F0 = basis(C0, Q0, r0)
    p1, z1 = project(STARS, C, R, U, Fv, cx, cy); p0, z0 = project(STARS, C0, R0, U0, F0, cx, cy)        # the particle field, streaking with the move
    ok = (z1 > 60) & (z0 > 60) & (z1 < 9000) & (p1[:, 0] > -50) & (p1[:, 0] < W + 50) & (p1[:, 1] > -50) & (p1[:, 1] < H + 50)
    for (a0, a1, zz) in zip(p0[ok], p1[ok], z1[ok]):
        al = max(0.05, min(0.8, 1 - zz / 9000)); wdt = max(1.0, 900 / zz * 2.2)
        if math.dist(a0, a1) > 2: cv.drawLine(a0[0], a0[1], a1[0], a1[1], paint(VIOL_L, al, wdt))
        else: cv.drawCircle(a1[0], a1[1], wdt * 0.7, paint(VIOL_L, al))
    for gx in range(-6000, 6001, 500):                                              # a floor grid far below: motion reads everywhere, the frame is never empty
        seg = np.array([[gx, GRID_Y, C[2] + 150], [gx, GRID_Y, C[2] + 14000]]); pp, zz = project(seg, C, R, U, Fv, cx, cy)
        if (zz > 100).all(): cv.drawLine(*pp[0], *pp[1], paint(VIOL_L, 0.10, 1.5))
    for gz in range(int((C[2] + 150) // 600 + 1) * 600, int(C[2] + 14000), 600):
        seg = np.array([[-6000, GRID_Y, gz], [6000, GRID_Y, gz]]); pp, zz = project(seg, C, R, U, Fv, cx, cy)
        if (zz > 100).all(): cv.drawLine(*pp[0], *pp[1], paint(VIOL_L, 0.12 * max(0.0, 1 - (gz - C[2]) / 14000), 1.5))
    focus = np.linalg.norm(Q - C); items = []
    for p_ in PANELS:
        if t < p_.at - 0.05 or t > p_.until: continue
        cs = p_.corners(); pp, zz = project(cs, C, R, U, Fv, cx, cy)
        if (zz < 80).any() or zz.min() > 12000: continue
        if pp[:, 0].max() < -100 or pp[:, 0].min() > W + 100 or pp[:, 1].max() < -100 or pp[:, 1].min() > H + 100: continue
        items.append((zz.mean(), p_, pp))
    for depth, p_, pp in sorted(items, key=lambda it: -it[0]):
        sw, sh = int(p_.w * SS), int(p_.h * SS); surf = skia.Surface(sw, sh); c2 = surf.getCanvas(); c2.clear(skia.Color(0, 0, 0, 0)); c2.scale(SS, SS); p_.draw(c2, p_.w, p_.h, t)
        img = surf.makeImageSnapshot(); m = skia.Matrix(); m.setPolyToPoly([skia.Point(0, 0), skia.Point(sw, 0), skia.Point(sw, sh), skia.Point(0, sh)], [skia.Point(*q) for q in pp])
        a = ease(ramp(t, p_.at, 0.5)) * max(0.25, min(1.0, 1.6 - depth / 7000)); pt = paint((255, 255, 255), a)
        blur = min(10.0, abs(depth - focus) / 420.0)                                    # soft away from the focus
        if blur > 1.2: pt.setImageFilter(skia.ImageFilters.Blur(blur, blur))
        cv.save(); cv.concat(m); cv.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), pt); cv.restore()
    for k in range(16):                                                               # vectors falling from RAM to disk, in the world
        dk = ease(ramp(t, DROP[k], 0.7))
        if 0 < dk < 1:
            x0 = -500 + 40 + (k % 8) * 115 + 47 - 0; yA = -260 - 180 + 130 + (k // 8) * 110 + 42; yB = 620 - 180 + 130 + (k // 8) * 110 + 42
            tile = P("t", (x0, lerp(yA, yB, dk), 29150 - 140 * math.sin(math.pi * dk)), 95, 85, d_tile); pp, zz = project(tile.corners(), C, R, U, Fv, cx, cy)
            if (zz > 80).all():
                path = skia.Path(); path.addPoly([skia.Point(*q) for q in pp], True); cv.drawPath(path, paint(VIOL)); cv.drawPath(path, paint(VIOL_L, 0.8, 2))
    img = Image.fromarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGBA")
    d = (p1[ok] - p0[ok]); swing = (float(np.median(d[:, 0])) * 6 if len(d) else 0.0, float(np.median(d[:, 1])) * 6 if len(d) else 0.0)
    face_card(img, face_im, t, hide, swing); return img

def plan(p, t0, t1):
    hide = E.hidden_spans(p.look); cuts = sorted({t0, t1} | {x for a, b in hide for x in (a, b) if t0 < x < t1}); S_ = []
    for a, b in zip(cuts, cuts[1:]):
        on = not any(x < b and y > a for x, y in hide)
        S_.append(dict(t0=a, t1=b, kind="graphic", shows_face=on, draw=lambda lt, dur, ctx: frame(ctx["t"], ctx["face"], hide), tr="cut", _hidden=False))
    sfx = [(k[0] - 0.35, E.whoosh(0.03, 0.5)) for k in KEYS[1:] if t0 <= k[0] - 0.35 < t1] + [(k[0], E.tone(0.1, 500, 900, 0.025)) for k in SKEYS[1:] if t0 <= k[0] < t1]
    return S_, sfx

if __name__ == "__main__":
    a = sys.argv[1:]; p = SF.project()
    if a[:1] == ["stills"]:
        ts = [float(x) for x in a[1:]]; S_, sfx = plan(p, 0, max(ts) + 2); r = E.Renderer(p, S_, 0, p.dur, OUT, sfx, (6, 9, 18)); print(r.stills(ts, OUT.replace(".mp4", "_sheet.png"), cols=4))
    else:
        t0, t1 = (float(a[0]), float(a[1])) if len(a) >= 2 else (0.0, p.dur)
        S_, sfx = plan(p, t0, t1); E.Renderer(p, S_, t0, t1, OUT if (t0, t1) == (0.0, p.dur) else OUT.replace(".mp4", f"_{int(t0)}-{int(t1)}.mp4"), sfx, (6, 9, 18)).render()
