"""SWISS: an editorial print layout in motion. Off-white paper, black type on a strict 12-column grid, hairline
rules, Qdrant red as the only colour. Headlines mask-reveal upward, rules draw across, huge numerals count,
bars grow. The presenter is a photograph locked to grid cells that change per section; each new page arrives
with a different wipe (columns dropping, horizontal, vertical). In a look-away his cell holds the sentence he
is saying as a pull-quote, so the grid never has a hole.

  python style_swiss.py 0 41             sample -> out/swiss_0-41.mp4
  python style_swiss.py stills 2 6 20    contact sheet
"""
import os, sys, math, numpy as np, skia
from PIL import Image
import engine as E
import style_full as SF
import style_launch as LN
W, H = E.W, E.H; TR = E.TR
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\swiss.mp4"
font, col, ramp, ease, inout, back, lerp, lerpr = LN.font, LN.col, LN.ramp, E.ease, E.inout, E.back, LN.lerp, LN.lerpr
T, L, wd, WORDS = LN.T, LN.L, LN.wd, LN.WORDS
PAPER, K, R, GREY = (242, 240, 235), (17, 17, 17), (220, 36, 76), (150, 148, 142)
BLACK, BOLD, SEMI, MONO = "MonaSansCondensed-Black.ttf", "MonaSans-Bold.ttf", "MonaSans-SemiBold.ttf", "GeistMono-Regular.ttf"
MG, GUT = 80, 24; CW = (W - 2 * MG - 11 * GUT) / 12
def cx(c): return MG + c * (CW + GUT)                                              # left edge of column c (0..11)
def span(c0, c1): return cx(c0), cx(c1) + CW - cx(c0)
def paint(c, a=1.0, w=0.0):
    p = skia.Paint(AntiAlias=True, Color=col(c, a))
    if w: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(w)
    return p
def ap(t, at, d=0.45): return ease(ramp(t, at - 0.25, d))
def reveal(cv, s, x, y, size, t, at, c=K, name=SEMI, max_w=None, d=0.5):
    """mask reveal: the line rises into place from behind its own baseline"""
    k = ease(ramp(t, at - 0.2, d))
    if k <= 0 or not s: return 0
    if max_w: size = LN.fitsize(name, s, max_w, size)
    f = font(name, size); cv.save(); cv.clipRect(skia.Rect(x - 4, y - size * 1.05, x + f.measureText(s) + 8, y + size * 0.3)); cv.drawString(s, x, y + (1 - k) * size * 1.1, f, paint(c)); cv.restore(); return f.measureText(s)
def rule(cv, x, y, w, t, at, c=K, wd_=2.0, d=0.6):
    k = ease(ramp(t, at - 0.2, d))
    if k > 0: cv.drawLine(x, y, x + w * k, y, paint(c, 1, wd_))
def header(cv, t, num, title, at):
    rule(cv, MG, 150, W - 2 * MG, t, at, K, 3); reveal(cv, num, MG, 118, 42, t, at, K, BOLD); reveal(cv, title, cx(1), 118, 42, t, at + 0.08, K, SEMI)
    reveal(cv, "Qdrant · Bulk uploads", W - MG - font(SEMI, 26).measureText("Qdrant · Bulk uploads"), 112, 26, t, at + 0.15, GREY, SEMI)

# ---------------------------------------------------------------- pages
def p1(cv, t):
    header(cv, t, "01", "What happens in a bulk upload", 0.8); n = 1_000_000 * ease(ramp(t, T["large"], 6.5))
    f = font(BLACK, 300); x, w = span(0, 7); s = f"{int(n):,}" if t > T["large"] - 0.3 else ""
    if s: size = LN.fitsize(BLACK, "1,000,000", w, 300); cv.drawString(s, x - 6, 470, font(BLACK, size), paint(K))
    if t > T["large"]: cv.drawCircle(cx(7) + CW - 30, 230, 22, paint(R, ap(t, T["large"])))
    reveal(cv, "points uploaded. Qdrant stores each vector,", x, 560, 42, t, T["qd"], K, SEMI, w); reveal(cv, "its payload, and the index around it.", x, 612, 42, t, T["store"], K, SEMI, w)
    rule(cv, x, 680, w, t, T["pay"] - 0.3, K, 1.2)
    for k, (lab, v, at) in enumerate((("vectors", 1.0, T["store"] + 0.3), ("payloads", 0.42, T["pay"]), ("HNSW index", 0.66, T["idx"]), ("background", 0.25, T["bg"]))):
        y = 720 + k * 78; g = ease(ramp(t, at - 0.2, 0.7)); hot = (k == 1 and T["pay"] - 0.2 < t < T["idx"] - 0.2) or (k == 2 and T["idx"] - 0.2 < t < T["bg"] - 0.2) or (k == 3 and t > T["bg"] - 0.2)
        reveal(cv, lab, x, y + 34, 30, t, at, K, SEMI); bx = cx(2)
        if g > 0: cv.drawRect(skia.Rect(bx, y + 4, bx + (cx(7) + CW - 80 - bx) * v * g, y + 44), paint(R if hot else K)); reveal(cv, f"{int(v * 100 * g)}", bx + (cx(7) + CW - 80 - bx) * v * g + 14, y + 36, 30, t, at, K, BOLD)
def p2(cv, t):
    header(cv, t, "02", "No one-size-fits-all", L[2] + 0.1); x, w = span(4, 11)
    reveal(cv, "One config.", x, 330, 130, t, T["single"], K, BLACK, w); k = ease(ramp(t, T["works"], 0.5))
    if k > 0: f = font(BLACK, 130); cv.drawLine(x, 290, x + f.measureText("One config.") * k, 290, paint(R, 1, 12))
    for j, (name, stat, cfg, _) in enumerate(LN.WORKLOADS):
        y = 470 + j * 175; at = T["conf"] + 0.22 * j; rule(cv, x, y - 70, w, t, at - 0.1, K, 1.2)
        reveal(cv, name, x, y + 20, 74, t, at, K, BLACK, w * 0.6); reveal(cv, stat, x, y + 70, 28, t, at + 0.1, GREY, SEMI)
        reveal(cv, cfg, cx(9), y + 20, 30, t, T["wf"] + 0.2 + 0.15 * j, R, MONO, span(9, 11)[1])
def p3(cv, t):
    t0 = wd(3, "different") - 0.1; header(cv, t, "03", "What we'll cover", t0); x, w = span(0, 8)
    reveal(cv, "4", x - 10, 560, 420, t, T["opt"] - 0.1, K, BLACK); reveal(cv, "+3", x + 250, 560, 420, t, T["best"] - 0.1, R, BLACK)
    for j, (num, name, _) in enumerate(LN.ROAD):
        best = j >= 4; col_ = 0 if not best else 4; row = j if not best else j - 4; y = 700 + row * 72; at = (T["opt"] if not best else T["best"]) + 0.12 * row
        rule(cv, cx(col_), y - 46, span(col_, col_ + 3)[1], t, at - 0.1, K, 1)
        reveal(cv, num, cx(col_), y, 34, t, at, R if best else K, BOLD); reveal(cv, name, cx(col_) + 60, y, 34, t, at + 0.05, K, SEMI, span(col_, col_ + 3)[1] - 60)
    reveal(cv, "options · dense or sparse", cx(0), 628, 24, t, T["opt"], GREY, MONO); reveal(cv, "best practices · both", cx(4), 628, 24, t, T["best"], GREY, MONO)
def p4(cv, t):
    header(cv, t, "04", "Dense and sparse vectors", L[4] + 0.1); x, w = span(0, 7); kc = ease(ramp(t, L[7] - 0.1, 0.5))
    for j, (lab, at, dense) in enumerate((("Dense · 768 dims, every value set", T["dense"], True), ("Sparse · 30,000 dims, ~0.1% set", T["sparse"], False))):
        y = 250 + j * 200; reveal(cv, lab, x, y, 36, t, at, K, SEMI, w)
        for k in range(40):
            a = ease(ramp(t, at + 0.01 * k, 0.3)); px = x + 14 + k * (w - 28) / 39; v = (0.35 + 0.5 * abs(math.sin(k * 1.7 + t * 1.2))) if dense else (0.9 if k in (6, 19, 31) else 0.0)
            if a > 0: cv.drawCircle(px, y + 70, (4 + 11 * v) * a if v > 0 else 2.5 * a, paint(K if dense else (R if v else GREY)))
    a_mid = 1 - kc
    if a_mid > 0 and t > T["hnsw"] - 0.3:
        reveal(cv, "HNSW: a graph in layers", x, 700, 36, t, T["hnsw"], K, SEMI)
        for li in range(3):
            y = 760 + li * 70; n = (3, 6, 12)[li]; g = ease(ramp(t, T["hnsw"] + 0.15 * li, 0.6)); pts = [x + 20 + (w / 2 - 60) * (q + 0.5) / n for q in range(n)]
            cv.drawLine(pts[0], y, pts[0] + (pts[-1] - pts[0]) * g, y, paint(K, a_mid, 2))
            for px in pts[: int(n * g + 0.5)]: cv.drawCircle(px, y, 9, paint(K, a_mid))
    if a_mid > 0 and t > T["sidx"] - 0.3:
        x2 = x + w / 2 + 20; reveal(cv, "Sparse: an inverted index", x2, 700, 36, t, T["sidx"], R, SEMI)
        for k, l in enumerate(("t12   4 · 9 · 31", "t77   4 · 12", "t301  9 · 18 · 77")): reveal(cv, l, x2, 780 + k * 62, 32, t, T["sidx"] + 0.15 * k, K, MONO)
    if kc > 0:
        for j, (v, lab, c) in enumerate(((78, "of RAM · dense + HNSW", K), (31, "of RAM · sparse index", R))):
            xx = x + j * (w / 2 + 20); vv = int(v * ease(ramp(t, T["mem"] + 0.2 * j, 1.2)))
            if t > T["mem"] - 0.2: cv.drawString(f"{vv}%", xx, 900, font(BLACK, 230), paint(c, kc))
            reveal(cv, lab, xx, 960, 30, t, T["mem"] + 0.2 * j, K, SEMI)
        reveal(cv, "Search latency: 2.1 ms in RAM, 4.8 ms on disk.", x, 1020, 30, t, T["perf"], GREY, SEMI, w)
def p5(cv, t):
    header(cv, t, "05", "Option 1 · Dense vectors on disk", L[9] - 0.1); x, w = span(4, 11)
    for j, (lab, xx) in enumerate((("RAM", x), ("Disk", x + w / 2 + 12))): reveal(cv, lab, xx, 250, 48, t, L[9] + 0.1 * j, K, BOLD); rule(cv, xx, 275, w / 2 - 12, t, L[9] + 0.1 * j, K, 2)
    for k in range(24):
        dk = ease(ramp(t, T["disk"] + 0.03 * k, 0.55)); c_, r_ = k % 4, k // 4; s = (w / 2 - 12 - 3 * 18) / 4
        x0, x1 = x + c_ * (s + 18), x + w / 2 + 12 + c_ * (s + 18); yy = 310 + r_ * (s * 0.32 + 14)
        if t > L[9] + 0.3 + 0.02 * k: cv.drawRect(skia.Rect(lerp(x0, x1, dk), yy - math.sin(math.pi * dk) * 30, lerp(x0, x1, dk) + s, yy + s * 0.32 - math.sin(math.pi * dk) * 30), paint(R if 0 < dk < 1 else K))
    gb = lerp(6.8, 2.1, ease(ramp(t, T["disk"] + 0.2, 1.4)))
    if t > T["storing"] - 0.2: cv.drawString(f"{gb:.1f} GB", x, 900, font(BLACK, 200), paint(K if gb > 3 else R))
    reveal(cv, "RAM in use", x, 960, 30, t, T["storing"], GREY, SEMI); reveal(cv, "VectorParams(size=768, on_disk=True)", x, 1020, 32, t, T["disk"] - 0.3, R, MONO, w)
PAGES = [(p1, 0.75), (p2, L[2]), (p3, L[3]), (p4, L[4]), (p5, L[8])]
WIPES = [None, "columns", "horizontal", "vertical", "cut"]
FACE = [(0.0, (0, 0, W, H)), (0.75, (*span(8, 11), 0))]                          # face cells: (x, w) per section; heights fixed below
CELLS = [(0.0, (0, 0, W, H)), (0.75, (cx(8), 200, span(8, 11)[1], 820)), (L[2], (cx(0), 200, span(0, 3)[1], 820)), (L[3], (0, 0, W, H)), (wd(3, "different") - 0.2, (cx(9), 200, span(9, 11)[1], 420)),
         (L[4], (cx(8), 200, span(8, 11)[1], 560)), (L[8], (0, 0, W, H)), (L[9], (cx(0), 200, span(0, 3)[1], 820))]
def cell_at(t):
    i = max(j for j, c in enumerate(CELLS) if t >= c[0]); cur = CELLS[i][1]; prev = CELLS[i - 1][1] if i else cur; return lerpr(prev, cur, inout(ramp(t, CELLS[i][0], 0.5)))
def spoken(t):
    for p in WORDS:
        if p["t0"] <= t < p["t1"] + 0.3: return " ".join(w for w, _ in p["words"])
    return ""
def wrap(s, f, w):
    out, cur = [], ""
    for word in s.split():
        if f.measureText((cur + " " + word).strip()) > w and cur: out.append(cur); cur = word
        else: cur = (cur + " " + word).strip()
    return out + ([cur] if cur else [])

def frame(t, face_im, hide):
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col(PAPER))
    for c in range(13): cv.drawLine(cx(c) - GUT / 2, 0, cx(c) - GUT / 2, H, paint(K, 0.04, 1))
    i = max(j for j, p in enumerate(PAGES) if t >= p[1] - 1e-6) if t >= PAGES[0][1] else 0; fn = PAGES[i][0]; k = ramp(t, PAGES[i][1], 0.6) if i else 1.0
    if k < 1 and i:                                                                  # the page change: a black wipe, different each time
        PAGES[i - 1][0](cv, t) if k < 0.5 else fn(cv, t); e = inout(k); wipe = WIPES[i]; cover = 1 - abs(2 * e - 1)
        if wipe == "columns":
            for c in range(12): kk = min(1, max(0, cover * 1.6 - c * 0.05)); cv.drawRect(skia.Rect(cx(c) - GUT / 2, 0, cx(c) + CW + GUT / 2, H * kk), paint(K))
        elif wipe == "horizontal": x0 = -W + 2 * W * e; cv.drawRect(skia.Rect(x0, 0, x0 + W, H), paint(K))
        elif wipe == "vertical": y0 = H - 2 * H * e; cv.drawRect(skia.Rect(0, y0, W, y0 + H), paint(K))
    else: fn(cv, t)
    img = Image.fromarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGBA")
    x, y, w, h = cell_at(t); hidden = any(a <= t < b for a, b in hide)
    if w > 10 and h > 10:
        if not hidden:
            fc = E.face_crop(face_im, int(w), int(h), 1.0 if w > 1500 else 1.1); img.paste(fc, (int(x), int(y)))
            if w < 1500:
                cs = skia.Surface(W, H); c2 = cs.getCanvas(); c2.clear(skia.Color(0, 0, 0, 0)); c2.drawString("John Kupchanko, Developer Relations", x, y + h + 40, font(SEMI, 24), paint(K))
                img.alpha_composite(Image.fromarray(cs.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)))
        else:                                                                        # the pull-quote holds his cell
            cs = skia.Surface(W, H); c2 = cs.getCanvas(); c2.clear(skia.Color(0, 0, 0, 0)); c2.drawRect(skia.Rect(x, y, x + w, y + h), paint(PAPER)); c2.drawLine(x, y, x + w, y, paint(R, 1, 6))
            q = spoken(t); size = 52 if w > 400 else 38; f = font(BOLD, size); lines = wrap("“" + q + "”", f, w - 20)
            for j, l in enumerate(lines[: int((h - 60) / (size * 1.2))]): c2.drawString(l, x, y + 80 + j * size * 1.2, f, paint(K))
            img.alpha_composite(Image.fromarray(cs.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)))
    if T["first"] - 0.3 < t < L[9]:                                                  # the chapter caption over the full photo
        cs = skia.Surface(W, H); c2 = cs.getCanvas(); c2.clear(skia.Color(0, 0, 0, 0)); kk = ease(ramp(t, T["first"] - 0.3, 0.4))
        c2.drawRect(skia.Rect(MG, H - 260, MG + 900 * kk, H - 100), paint(K)); c2.save(); c2.clipRect(skia.Rect(MG, H - 260, MG + 900 * kk, H - 100))
        c2.drawString("05", MG + 40, H - 190, font(BOLD, 40), paint(R)); c2.drawString("Option 1 · Dense vectors on disk", MG + 40, H - 135, font(SEMI, 46), paint(PAPER)); c2.restore()
        img.alpha_composite(Image.fromarray(cs.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)))
    return img

def plan(p, t0, t1):
    hide = E.hidden_spans(p.look); cuts = sorted({t0, t1} | {x for a, b in hide for x in (a, b) if t0 < x < t1}); S_ = []
    for a, b in zip(cuts, cuts[1:]):
        on = not any(x < b and y > a for x, y in hide)
        S_.append(dict(t0=a, t1=b, kind="graphic", shows_face=on, draw=lambda lt, dur, ctx: frame(ctx["t"], ctx["face"], hide), tr="cut", _hidden=False))
    sfx = [(pg[1] - 0.05, E.whoosh(0.03, 0.45)) for pg in PAGES[1:] if t0 <= pg[1] < t1] + [(c[0] - 0.05, E.whoosh(0.02, 0.35)) for c in CELLS[1:] if t0 <= c[0] < t1]
    sfx += [(x - 0.2, E.tone(0.04, 1100, 800, 0.02)) for x in (T["large"], T["qd"], T["pay"], T["idx"], T["single"], T["works"], T["opt"], T["best"], T["dense"], T["sparse"], T["hnsw"], T["sidx"], T["mem"], T["disk"]) if t0 <= x < t1]
    return S_, sfx

if __name__ == "__main__":
    a = sys.argv[1:]; p = SF.project()
    if a[:1] == ["stills"]:
        ts = [float(x) for x in a[1:]]; S_, sfx = plan(p, 0, max(ts) + 2); r = E.Renderer(p, S_, 0, p.dur, OUT, sfx, PAPER); print(r.stills(ts, OUT.replace(".mp4", "_sheet.png"), cols=4))
    else:
        t0, t1 = (float(a[0]), float(a[1])) if len(a) >= 2 else (0.0, p.dur)
        S_, sfx = plan(p, t0, t1); E.Renderer(p, S_, t0, t1, OUT if (t0, t1) == (0.0, p.dur) else OUT.replace(".mp4", f"_{int(t0)}-{int(t1)}.mp4"), sfx, PAPER).render()
