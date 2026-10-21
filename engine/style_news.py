"""NEWSROOM: the video as a broadcast package. A studio set with drifting light streaks, a LIVE bug and clock,
a channel bug and a stats ticker crawling along the bottom. Name and topic straps slide in; a data wall counts
up; a coming-up rundown lists the options; dense vs sparse is a head-to-head with a VS badge; option 1 slams
in as a title. The presenter is in full shot, two-box splits (him and a graphic side by side), an over-the-
shoulder box, or a small corner box over a full graphic; in a look-away the graphic takes the whole screen.

  python style_news.py 0 41             sample -> out/news_0-41.mp4
  python style_news.py stills 2 6 20    contact sheet
"""
import os, sys, math, numpy as np, skia
from PIL import Image
import engine as E
import style_full as SF
import style_launch as LN
W, H = E.W, E.H; TR = E.TR
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\news.mp4"
font, col, ramp, ease, inout, back, lerp, lerpr, text = LN.font, LN.col, LN.ramp, E.ease, E.inout, E.back, LN.lerp, LN.lerpr, LN.text
T, L, wd = LN.T, LN.L, LN.wd
NAVY, RED, WHT, INK, TEAL, VIO, AMB = (8, 20, 52), (220, 36, 76), (255, 255, 255), (12, 20, 40), (79, 209, 197), (180, 168, 255), (255, 183, 77)
BOLD, SEMI, MONO, BLACK = "MonaSans-Bold.ttf", "MonaSans-SemiBold.ttf", "GeistMono-Regular.ttf", "MonaSansCondensed-Black.ttf"
def paint(c, a=1.0, w=0.0, blur=0.0):
    p = skia.Paint(AntiAlias=True, Color=col(c, a))
    if w: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(w)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p
def ap(t, at, d=0.45): return ease(ramp(t, at - 0.25, d))
TICK_Y = 980
# ---------------------------------------------------------------- layouts: (face rect, face boxed?, graphic rect)
LAY = {"full": ((0, 0, W, TICK_Y), False, None), "ots": ((0, 0, W, TICK_Y), False, (1180, 90, 680, 420)), "two_l": ((60, 150, 860, 700), True, (960, 150, 900, 700)),
       "two_r": ((1000, 150, 860, 700), True, (60, 150, 900, 700)), "corner": ((1420, 560, 440, 330), True, (60, 110, 1320, 820)), "wall": (None, False, (60, 110, W - 120, 820))}
KEYS = [(0.0, "full"), (T["large"] - 0.4, "ots"), (L[1], "two_l"), (L[2], "two_r"), (L[3], "full"), (wd(3, "different") - 0.2, "corner"), (L[4], "corner"), (L[7], "two_l"), (L[8], "full"), (L[9], "two_r")]
def keys_with(hide):
    out = []
    for k, (t0, lay) in enumerate(KEYS):
        t1 = KEYS[k + 1][0] if k + 1 < len(KEYS) else 1e9; cur = t0
        for a, b in hide:
            if b <= cur or a >= t1: continue
            if a > cur: out.append((cur, lay))
            out.append((max(a, cur), "wall")); cur = min(b, t1)
        if cur < t1: out.append((cur, lay))
    return out
def lay_at(keys, t):
    i = max(j for j, k in enumerate(keys) if t >= k[0]); cur, prev = keys[i][1], (keys[i - 1][1] if i else keys[i][1]); e = inout(ramp(t, keys[i][0], 0.5))
    fc, fp = LAY[cur][0], LAY[prev][0]
    if fc is None: fc = (fp[0] + fp[2] / 2, fp[1] + fp[3] / 2, 0, 0) if fp else (W / 2, H / 2, 0, 0)
    if fp is None: fp = (fc[0] + fc[2] / 2, fc[1] + fc[3] / 2, 0, 0)
    gc, gp = LAY[cur][2], LAY[prev][2]; ga = 1.0
    if gc is None and gp is None: g, ga = None, 0
    elif gc is None: g, ga = gp, 1 - e
    elif gp is None: g, ga = gc, e
    else: g = lerpr(gp, gc, e)
    return lerpr(fp, fc, e), lerp(1.0 if LAY[prev][1] else 0.0, 1.0 if LAY[cur][1] else 0.0, e), g, ga, cur

# ---------------------------------------------------------------- graphics, laid out in the graphic rect
def tile(cv, x, y, w, h, lab, val, c, a, size=None):
    if a <= 0.01: return
    cv.drawRect(skia.Rect(x, y, x + w, y + h), paint(NAVY, 0.88 * a)); cv.drawRect(skia.Rect(x, y, x + w, y + h), paint(WHT, 0.06 * a)); cv.drawRect(skia.Rect(x, y, x + 10, y + h), paint(c, a))
    text(cv, lab, x + 34, y + min(56, h * 0.32), min(26, h * 0.16), (190, 200, 220), a, MONO, max_w=w - 50); text(cv, val, x + 34, y + h * 0.78, size or min(84, h * 0.42), c, a, BOLD, max_w=w - 50)
def g_s1(cv, t, R, a):
    x, y, w, h = R; n = 1_000_000 * ease(ramp(t, T["large"], 6.5))
    if w > 800:                                                                        # the data wall
        rows = [("POINTS UPLOADED", f"{int(n):,}", WHT, T["large"]), ("PAYLOAD FIELDS", "3 / point", TEAL, T["pay"]), ("INDEX", "HNSW · m=16", VIO, T["idx"]), ("BACKGROUND", "optimizer · WAL", AMB, T["bg"])]
        th = (h - 3 * 16) / 4
        for k, (lab, val, c, at) in enumerate(rows): tile(cv, x + (1 - ap(t, at)) * 60, y + k * (th + 16), w, th, lab, val, c, a * ap(t, at))
    else: tile(cv, x, y, w, h, "POINTS UPLOADED", f"{int(n):,}", WHT, a * ap(t, T["large"]), 110)
def g_s2(cv, t, R, a):
    x, y, w, h = R; tile(cv, x, y, w, h * 0.22, "ONE CONFIG FOR EVERYTHING?", "on_disk=F · m=16 · 1 shard", RED if t > T["works"] else WHT, a * ap(t, T["single"]), 44)
    for k, (name, stat, cfg, c) in enumerate(LN.WORKLOADS):
        at = T["conf"] + 0.22 * k; yy = y + h * (0.27 + 0.245 * k); hh = h * 0.215; aa = a * ap(t, at)
        if aa <= 0: continue
        cv.drawRect(skia.Rect(x, yy, x + w, yy + hh), paint(WHT, 0.08 * aa)); cv.drawRect(skia.Rect(x, yy, x + 10, yy + hh), paint(c, aa))
        text(cv, name, x + 34, yy + hh * 0.45, 40, WHT, aa, BOLD, max_w=w * 0.5); text(cv, stat, x + 34, yy + hh * 0.8, 24, (190, 200, 220), aa, MONO, max_w=w * 0.5)
        good = ap(t, T["wf"] + 0.2 + 0.15 * k); bad = ap(t, T["works"] + 0.15 * k) * (1 - good)
        if bad > 0: text(cv, "✗ DEFAULT" if False else "x DEFAULT", x + w - 30, yy + hh * 0.6, 32, RED, aa * bad, BOLD, align="right")
        if good > 0: text(cv, cfg, x + w - 30, yy + hh * 0.6, 26, (130, 230, 160), aa * good, MONO, align="right", max_w=w * 0.42)
def g_s3(cv, t, R, a):
    x, y, w, h = R; t0 = wd(3, "different") - 0.1; cv.drawRect(skia.Rect(x, y, x + w, y + 90), paint(RED, a * ap(t, t0)))
    text(cv, "COMING UP", x + 30, y + 62, 46, WHT, a * ap(t, t0), BOLD); text(cv, "4 options · 3 best practices", x + w - 30, y + 60, 30, WHT, a * ap(t, T["opt"]), SEMI, align="right")
    for k, (num, name, _) in enumerate(LN.ROAD):
        at = (T["opt"] if k < 4 else T["best"]) + 0.12 * (k % 4); aa = a * ap(t, at); yy = y + 110 + k * (h - 120) / 7; hh = (h - 120) / 7 - 8; xx = x + (1 - ap(t, at)) * -80
        cv.drawRect(skia.Rect(xx, yy, xx + w, yy + hh), paint(WHT, (0.16 if k == 0 else 0.07) * aa)); cv.drawRect(skia.Rect(xx, yy, xx + hh, yy + hh), paint(RED if k < 4 else TEAL, aa))
        text(cv, num, xx + hh / 2, yy + hh * 0.72, hh * 0.6, WHT, aa, BOLD, align="center"); text(cv, name, xx + hh + 26, yy + hh * 0.68, hh * 0.5, WHT, aa, SEMI, max_w=w - hh - 60)
        text(cv, "OPTION" if k < 4 else "BEST PRACTICE", xx + w - 24, yy + hh * 0.66, hh * 0.32, (190, 200, 220), aa, MONO, align="right")
def g_s4(cv, t, R, a):
    x, y, w, h = R; kc = ease(ramp(t, L[7] - 0.1, 0.5))
    if kc < 1:
        aa = a * (1 - kc); cw = (w - 120) / 2
        for k, (name, c, at, stats) in enumerate((("DENSE", VIO, T["dense"], [("dims", "768", 0.3), ("values set", "100%", 1.0), ("index", "HNSW", 0.8)]), ("SPARSE", RED, T["sparse"], [("dims", "30,000", 1.0), ("values set", "0.1%", 0.03), ("index", "inverted", 0.6)]))):
            xx = x + k * (cw + 120); a2 = aa * ap(t, at); cv.drawRect(skia.Rect(xx, y, xx + cw, y + 110), paint(c, a2)); text(cv, name, xx + cw / 2, y + 82, 70, WHT, a2, BLACK, align="center")
            for j, (lab, val, v) in enumerate(stats):
                at2 = (T["hnsw"] if (j == 2 and k == 0) else T["sidx"] if (j == 2 and k == 1) else at + 0.2 + 0.15 * j); a3 = aa * ap(t, at2); yy = y + 150 + j * (h - 160) / 3
                text(cv, lab.upper(), xx, yy + 30, 24, (190, 200, 220), a3, MONO); text(cv, val, xx + cw, yy + 30, 40, WHT, a3, BOLD, align="right")
                cv.drawRect(skia.Rect(xx, yy + 54, xx + cw, yy + 74), paint(WHT, 0.1 * a3)); cv.drawRect(skia.Rect(xx, yy + 54, xx + cw * v * ease(ramp(t, at2, 0.8)), yy + 74), paint(c, a3))
        vs = back(ramp(t, T["sparse"] - 0.1, 0.4)) * aa
        if vs > 0: cx_, cy_ = x + w / 2, y + 55; cv.drawCircle(cx_, cy_, 56 * min(1.2, vs), paint(WHT, min(1, vs))); text(cv, "VS", cx_, cy_ + 20, 54, NAVY, min(1, vs), BLACK, align="center")
    if kc > 0:
        aa = a * kc; tile(cv, x, y, w, h * 0.3, "RAM · DENSE + HNSW", f"{int(78 * ease(ramp(t, T['mem'], 1.2)))}%", VIO, aa * ap(t, T["mem"]))
        tile(cv, x, y + h * 0.34, w, h * 0.3, "RAM · SPARSE INDEX", f"{int(31 * ease(ramp(t, T['mem'] + 0.2, 1.2)))}%", RED, aa * ap(t, T["mem"] + 0.2))
        tile(cv, x, y + h * 0.68, w, h * 0.32, "SEARCH LATENCY", "2.1 ms RAM · 4.8 ms disk", TEAL, aa * ap(t, T["perf"]), 50)
def g_s5(cv, t, R, a):
    x, y, w, h = R; gb = lerp(6.8, 2.1, ease(ramp(t, T["disk"] + 0.2, 1.4)))
    cv.drawRect(skia.Rect(x, y, x + w, y + 100), paint(RED, a * ap(t, L[9]))); text(cv, "OPTION 1 · DENSE VECTORS ON DISK", x + 30, y + 68, 40, WHT, a * ap(t, L[9]), BOLD, max_w=w - 60)
    tile(cv, x, y + 130, w, h * 0.36, "RAM IN USE", f"{gb:.1f} GB", RED if gb > 3 else (130, 230, 160), a * ap(t, L[9] + 0.3), 120)
    if t > T["disk"] + 0.4: v = back(ramp(t, T["disk"] + 0.4, 0.4)); cv.save(); cx_, cy_ = x + w - 160, y + 130 + h * 0.18; cv.translate(cx_, cy_); cv.scale(min(1.2, v), min(1.2, v)); cv.drawCircle(0, 0, 110, paint(RED, a)); text(cv, "-69%", 0, 20, 64, WHT, a, BLACK, align="center"); cv.restore()
    tile(cv, x, y + 160 + h * 0.36, w, h * 0.3, "THE CHANGE", "VectorParams(on_disk=True)", AMB, a * ap(t, T["storing"]), 40)
GRAPHICS = [(g_s1, 0.0), (g_s2, L[2]), (g_s3, L[3]), (g_s4, L[4]), (g_s5, L[8])]
STRAPS = [(0.75, L[1] - 0.2, "JOHN KUPCHANKO", "Developer Relations, Qdrant"), (L[3] + 0.1, wd(3, "different") - 0.3, "COMING UP", "Options and best practices for bulk uploads"),
          (T["first"] - 0.3, L[9] - 0.1, "OPTION 1", "Store dense vectors on disk")]
TICKER = "QDRANT BULK UPLOADS  ·  4 OPTIONS, 3 BEST PRACTICES  ·  ON_DISK CUTS RAM 69%  ·  BATCH 64-256 POINTS  ·  PARALLEL UPLOAD WORKERS  ·  MULTIPLE SHARDS  ·  PAYLOAD INDEXES FIRST  ·  "

_bg = None
def studio(cv, t):
    global _bg
    if _bg is None:
        s = skia.Surface(W, H); c = s.getCanvas(); p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(W, H)], [col((8, 20, 52)), col((34, 10, 44))])); c.drawRect(skia.Rect(0, 0, W, H), p)
        for (bx, by, br, bc) in ((300, 200, 280, (60, 90, 200)), (1600, 300, 320, (200, 40, 90)), (1100, 900, 260, (60, 160, 200))): c.drawCircle(bx, by, br, paint(bc, 0.25, blur=120))
        _bg = s.makeImageSnapshot()
    cv.drawImage(_bg, 0, 0)
    for k in range(6): x0 = ((t * 60 + k * 420) % (W + 800)) - 400; cv.drawLine(x0, -50, x0 - 500, H + 50, paint(WHT, 0.035, 60))
def frame(t, face_im, keys):
    s = skia.Surface(W, H); cv = s.getCanvas(); studio(cv, t); face_r, boxed, g, ga, cur = lay_at(keys, t)
    fx, fy, fw, fh = face_r
    if fw > 8 and fh > 8:
        im = E.face_crop(face_im, int(fw), int(fh), 1.0 if fw > 1500 else 1.05).convert("RGBA"); img = skia.Image.fromarray(np.ascontiguousarray(np.asarray(im)), colorType=skia.kRGBA_8888_ColorType)
        if boxed > 0: cv.drawRect(skia.Rect(fx - 6, fy - 6 + 20, fx + fw + 6, fy + fh + 6 + 20), paint((0, 0, 0), 0.5 * boxed, blur=24))
        cv.drawImage(img, fx, fy)
        if boxed > 0: cv.drawRect(skia.Rect(fx - 3, fy - 3, fx + fw + 3, fy + fh + 3), paint(WHT, boxed, 5)); cv.drawRect(skia.Rect(fx, fy + fh - 52, fx + min(fw, 440), fy + fh), paint(RED, boxed)); text(cv, "LIVE · JOHN KUPCHANKO", fx + 18, fy + fh - 16, 24, WHT, boxed, BOLD)
    if g is not None and ga > 0.01:
        i = max(j for j, gg in enumerate(GRAPHICS) if t >= gg[1] - 1e-6); kk = ramp(t, GRAPHICS[i][1], 0.5)
        if i and kk < 1:                                                               # a red diagonal swipe between graphics
            (GRAPHICS[i - 1][0] if kk < 0.5 else GRAPHICS[i][0])(cv, t, g, ga); e = inout(kk); sx = g[0] - 300 + (g[2] + 600) * e
            p_ = skia.Path(); p_.moveTo(sx, g[1] - 20); p_.lineTo(sx + 260, g[1] - 20); p_.lineTo(sx + 160, g[1] + g[3] + 20); p_.lineTo(sx - 100, g[1] + g[3] + 20); p_.close(); cv.drawPath(p_, paint(RED, ga))
        else: GRAPHICS[i][0](cv, t, g, ga)
    for t0, t1, a_, b_ in STRAPS:                                                     # lower-third straps
        k_in, k_out = ease(ramp(t, t0, 0.4)), ease(ramp(t, t1, 0.35))
        if k_in > 0 and k_out < 1:
            y0 = 800 + 160 * k_out; w1 = 760 * k_in; cv.save(); cv.clipRect(skia.Rect(0, 0, W, TICK_Y - 2))
            cv.drawRect(skia.Rect(60, y0, 60 + w1, y0 + 72), paint(RED)); cv.drawRect(skia.Rect(60, y0 + 72, 60 + w1 * 1.18, y0 + 122), paint(WHT))
            cv.save(); cv.clipRect(skia.Rect(60, y0, 60 + w1 * 1.18, y0 + 122)); text(cv, a_, 90, y0 + 52, 42, WHT, 1, BOLD); text(cv, b_, 90, y0 + 108, 30, INK, 1, SEMI); cv.restore(); cv.restore()
    cv.drawRect(skia.Rect(60, 40, 170, 86), paint(RED)); text(cv, "LIVE", 115, 75, 32, WHT, 1, BOLD, align="center"); text(cv, f"10:{int(14 + t // 60):02d}", 190, 75, 30, WHT, 1, SEMI)
    cv.drawRect(skia.Rect(0, TICK_Y, W, H), paint(WHT)); cv.drawRect(skia.Rect(0, TICK_Y, 300, H), paint(RED)); text(cv, "QDRANT", 150, TICK_Y + 66, 40, WHT, 1, BOLD, align="center")
    f = font(SEMI, 34); tw = f.measureText(TICKER); off = (t * 140) % tw; cv.save(); cv.clipRect(skia.Rect(300, TICK_Y, W, H))
    for k in range(3): cv.drawString(TICKER, 330 - off + k * tw, TICK_Y + 63, f, paint(INK))
    cv.restore()
    return Image.fromarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGBA")

def plan(p, t0, t1):
    hide = E.hidden_spans(p.look); keys = keys_with(hide); cuts = sorted({t0, t1} | {x for a, b in hide for x in (a, b) if t0 < x < t1}); S_ = []
    for a, b in zip(cuts, cuts[1:]):
        on = not any(x < b and y > a for x, y in hide)
        S_.append(dict(t0=a, t1=b, kind="graphic", shows_face=on, draw=lambda lt, dur, ctx: frame(ctx["t"], ctx["face"], keys), tr="cut", _hidden=False))
    sfx = [(k[0] - 0.05, E.whoosh(0.03, 0.45)) for k in keys[1:] if t0 <= k[0] < t1] + [(st[0], E.tone(0.15, 700, 1400, 0.03)) for st in STRAPS if t0 <= st[0] < t1]
    sfx += [(x - 0.2, E.tone(0.05, 1300, 900, 0.022)) for x in (T["large"], T["pay"], T["idx"], T["bg"], T["conf"], T["opt"], T["best"], T["dense"], T["sparse"], T["mem"], T["disk"]) if t0 <= x < t1]
    return S_, sfx

if __name__ == "__main__":
    a = sys.argv[1:]; p = SF.project()
    if a[:1] == ["stills"]:
        ts = [float(x) for x in a[1:]]; S_, sfx = plan(p, 0, max(ts) + 2); r = E.Renderer(p, S_, 0, p.dur, OUT, sfx, NAVY); print(r.stills(ts, OUT.replace(".mp4", "_sheet.png"), cols=4))
    else:
        t0, t1 = (float(a[0]), float(a[1])) if len(a) >= 2 else (0.0, p.dur)
        S_, sfx = plan(p, t0, t1); E.Renderer(p, S_, t0, t1, OUT if (t0, t1) == (0.0, p.dur) else OUT.replace(".mp4", f"_{int(t0)}-{int(t1)}.mp4"), sfx, NAVY).render()
