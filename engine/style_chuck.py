"""CHUCK: copied from NetworkChuck ("You've Been Using AI the Hard Way (Use This Instead)", 2.3M views; storyboard
in ref_MsQA/sheets). Real screens, hand-drawn marker on top, a gold-framed face cam:

  screen     the real thing full frame: the Qdrant docs in a browser that scrolls to each section, or a terminal
             running the upload. The face cam sits top right in a rounded frame with a thick gold border while
             the presenter is on the lens, and slides out during a look-away.
  marker     hand-drawn annotations that draw themselves over the screen on the spoken words: wobbly circles,
             underlines, arrows, scrawled notes. They are pinned to the page, so they scroll with it.
  sketch     on talking-head shots, a diagram sketches itself on the wall beside the presenter (boxes, arrows,
             labels, doodles), building as he explains
  strip      a segment title top left ("OPTION 1: Store dense vectors on disk")

Hard cuts between talk and screen; slow holds, kept alive by the marker.

  python style_chuck.py 0 41             sample -> out/chuck_0-41.mp4
  python style_chuck.py stills 2 6 20    contact sheet
"""
import os, sys, json, math, numpy as np, skia
from PIL import Image
import engine as E
import style_full as SF
import style_launch as LN
W, H = E.W, E.H; TR = E.TR
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\chuck.mp4"
PAGE = r"C:\Users\ADMIN\camera_audit\chuck_style\page.png"; PJ = json.load(open(r"C:\Users\ADMIN\camera_audit\chuck_style\page.json"))
font, col, ramp, ease, inout, back, lerp = LN.font, LN.col, LN.ramp, E.ease, E.inout, E.back, LN.lerp
T, L, wd = LN.T, LN.L, LN.wd
HAND = "Kalam-Bold.ttf"; MONO = "GeistMono-Regular.ttf"; BOLD = "MonaSans-Bold.ttf"
YEL, WHITE, INK, GOLD = (255, 210, 63), (255, 255, 255), (28, 28, 30), (229, 179, 58)
def paint(c, a=1.0, w=0.0, blur=0.0):
    p = skia.Paint(AntiAlias=True, Color=col(c, a))
    if w: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(w); p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p

# ---------------------------------------------------------------- marker: everything draws itself, with a hand's wobble
def wobble(pts, seed, amp=2.2):
    rd = np.random.default_rng(seed); return [(x + rd.normal(0, amp), y + rd.normal(0, amp)) for x, y in pts]
def smooth_path(pts):
    p = skia.Path(); p.moveTo(*pts[0])
    for i in range(1, len(pts) - 1): mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2; p.quadTo(pts[i][0], pts[i][1], mx, my)
    p.lineTo(*pts[-1]); return p
def draw_on(cv, path, k, c, w, shadow=True):
    if k <= 0: return
    pm = skia.PathMeasure(path, False); seg = skia.Path(); pm.getSegment(0, pm.getLength() * min(1.0, k), seg, True)
    if shadow: cv.save(); cv.translate(2, 3); cv.drawPath(seg, paint((0, 0, 0), 0.45, w + 2, 2)); cv.restore()
    cv.drawPath(seg, paint(c, 1, w))
def m_line(cv, pts, t, t0, d=0.35, c=YEL, w=7, seed=0):
    draw_on(cv, smooth_path(wobble(pts, seed)), ease(ramp(t, t0, d)), c, w)
def m_circle(cv, x, y, rw, rh, t, t0, d=0.45, c=YEL, w=7, seed=0):
    """a hand-drawn loop: a bit more than one turn, uneven, the ends not meeting"""
    rd = np.random.default_rng(seed); a0 = rd.uniform(-2.6, -2.0); pts = []
    for k in range(48):
        a = a0 + 2 * math.pi * 1.12 * k / 47; s = 1 + 0.06 * math.sin(a * 2 + seed); pts.append((x + rw * s * math.cos(a), y + rh * s * math.sin(a) + 4 * k / 47))
    draw_on(cv, smooth_path(pts), ease(ramp(t, t0, d)), c, w)
def m_square(cv, x, y, w, h, t, t0, d=0.45, c=YEL, wdt=4.5, pad=7, seed=0):
    """a marker box drawn tight around a phrase in one continuous stroke, clockwise from the top left, the end just
    past the start (as a hand closes a box); slightly rounded corners, a hair of wobble"""
    px, py = pad, max(3, pad * 0.5); x0, y0, x1, y1 = x - px, y - py, x + w + px, y + h + py; r = min(8, (y1 - y0) / 4)
    path = skia.Path(); path.moveTo(x0 + r, y0); path.lineTo(x1 - r, y0 - 0.5); path.quadTo(x1, y0, x1, y0 + r); path.lineTo(x1 + 0.5, y1 - r); path.quadTo(x1, y1, x1 - r, y1)
    path.lineTo(x0 + r, y1 + 0.5); path.quadTo(x0, y1, x0, y1 - r); path.lineTo(x0 - 0.5, y0 + r); path.quadTo(x0, y0, x0 + r, y0); path.lineTo(x0 + r + 14, y0 - 1)
    draw_on(cv, path, ease(ramp(t, t0, d)), c, wdt)
def m_arrow(cv, x0, y0, x1, y1, t, t0, d=0.35, c=YEL, w=7, bend=0.25, seed=0):
    mx, my = (x0 + x1) / 2 - (y1 - y0) * bend, (y0 + y1) / 2 + (x1 - x0) * bend; pts = [(x0 + (mx - x0) * u * 2 if u < 0.5 else mx + (x1 - mx) * (u - 0.5) * 2, y0 + (my - y0) * u * 2 if u < 0.5 else my + (y1 - my) * (u - 0.5) * 2) for u in np.linspace(0, 1, 12)]
    k = ease(ramp(t, t0, d)); draw_on(cv, smooth_path(wobble(pts, seed, 1.5)), k, c, w)
    if k >= 1:
        ang = math.atan2(y1 - pts[-3][1], x1 - pts[-3][0])
        for s in (-1, 1): m_line(cv, [(x1, y1), (x1 - 30 * math.cos(ang + s * 0.5), y1 - 30 * math.sin(ang + s * 0.5))], t, t0 + d, 0.1, c, w, seed + 7 + s)
def m_text(cv, s, x, y, size, t, t0, c=YEL, cps=22, align="left", shadow=True):
    if t < t0: return
    n = min(len(s), int((t - t0) * cps) + 1); f = font(HAND, size); w = f.measureText(s); x = x - w / 2 if align == "center" else x
    if shadow: cv.drawString(s[:n], x + 2, y + 3, f, paint((0, 0, 0), 0.5, blur=2))
    cv.drawString(s[:n], x, y, f, paint(c))
def m_box(cv, x, y, w, h, t, t0, d=0.5, c=INK, wdt=6, seed=0):
    m_line(cv, [(x, y), (x + w, y + 3), (x + w - 2, y + h), (x + 3, y + h - 2), (x, y - 4)], t, t0, d, c, wdt, seed)

# ---------------------------------------------------------------- screens
_page = None
def page_img():
    global _page
    if _page is None: _page = skia.Image.open(PAGE)
    return _page
S = PJ["scale"]; CHROME = 86; VX0 = 440; ZOOM = 1.34                # the view: page x 400 at the left edge, the text column filling the frame left of the face cam
def tgt(name, k=0):
    x, y, w, h = PJ["targets"][name][k]; return x * S, y * S, w * S, h * S
SCROLL = [  # (time the scroll lands, page y at the top of the view); scrolls take 0.7 s, or longer when far
    (0.0, 0), (L[2] - 0.2, tgt("Choosing the Right Bulk Upload Strategy")[1] - 130), (L[3] + 0.7, tgt("Option 1: Reduce Memory Pressure")[1] - 90),
    (wd(3, "options") + 0.2, tgt("Option 4: Reduce Sparse Index Memory During Uploads")[1] - 90), (wd(3, "practices") + 0.5, tgt("Use Multiple Shards for Larger Uploads")[1] - 160),
    (L[5] - 0.2, tgt("Why Vector Type Matters")[1] - 120), (L[9] - 0.2, tgt("Option 1: Reduce Memory Pressure")[1] - 70), (wd(9, "disk") + 0.3, tgt("Option 1: Reduce Memory Pressure")[1] + 110)]
def scroll_y(t):
    y = SCROLL[0][1]
    for (t1, y1), (t0, y0) in zip(SCROLL[1:], SCROLL[:-1]):
        d = min(1.6, max(0.6, abs(y1 - y0) / 2400)); k = inout(ramp(t, t1 - d, d)); y = lerp(y, y1, k) if t >= t1 - d else y
    return y
def browser(cv, t, notes):
    sy = scroll_y(t); cv.clear(col((16, 18, 27)))
    cv.save(); cv.clipRect(skia.Rect(0, CHROME, W, H)); cv.translate(0, CHROME); cv.scale(ZOOM, ZOOM); cv.translate(-VX0, -sy)
    cv.drawImage(page_img(), 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)); notes(cv, t); cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, CHROME), paint((32, 33, 36)))                               # the browser chrome
    for k, c in enumerate(((255, 95, 87), (254, 188, 46), (40, 200, 64))): cv.drawCircle(26 + k * 24, 22, 7, paint(c))
    cv.drawRoundRect(skia.Rect(110, 8, 470, 38), 8, 8, paint((53, 54, 58))); cv.drawString("Bulk Uploading Data to Qdrant", 128, 29, font("Inter[opsz,wght].ttf", 15), paint((230, 230, 230)))
    cv.drawRoundRect(skia.Rect(100, 46, W - 300, 78), 16, 16, paint((53, 54, 58))); cv.drawString("qdrant.tech/documentation/production-operations/bulk-data-import/", 130, 68, font("Inter[opsz,wght].ttf", 17), paint((210, 210, 210)))
TERM_BG = (48, 10, 36)
def terminal(cv, t, lines, notes):
    """an Ubuntu-style terminal; lines = [(t_start, text, colour, typed)]"""
    cv.clear(col(TERM_BG)); cv.drawRect(skia.Rect(0, 0, W, 44), paint((44, 44, 44))); cv.drawString("john@qdrant: ~/bulk-upload", W / 2 - 150, 29, font(BOLD, 18), paint((220, 220, 220)))
    f = font(MONO, 32); y = 116
    for ts, s, c, typed in lines:
        if t < ts: continue
        if typed:
            pr = "john@qdrant:~/bulk-upload$ "; cv.drawString("john@qdrant", 40, y, f, paint((138, 226, 52))); x = 40 + f.measureText("john@qdrant")
            cv.drawString(":~/bulk-upload", x, y, f, paint((114, 159, 207))); x += f.measureText(":~/bulk-upload"); cv.drawString("$ ", x, y, f, paint(WHITE)); x += f.measureText("$ ")
            n = min(len(s), int((t - ts) * 32)); cv.drawString(s[:n], x, y, f, paint(c))
        else: cv.drawString(s, 40, y, f, paint(c))
        y += 50
    notes(cv, t)

# ---------------------------------------------------------------- the presenter: full frame for talk, a gold-framed cam over screens
CAM = (W - 36 - 460, 36, 460, 520)                                     # bigger, and the whole head in it
def talk_face(face_im, t, t0):
    z = 1.16 + 0.02 * min(1.0, (t - t0) / 8); cw = W / z; ch = cw * H / W                 # same 16:9 shape as the frame: nothing is stretched
    y0 = 72 + (H - 144 - ch) / 2; im = face_im.crop((0, int(y0), int(cw), int(y0 + ch))).resize((W, H), Image.BILINEAR).convert("RGBA")
    return skia.Image.fromarray(np.ascontiguousarray(np.asarray(im)), colorType=skia.kRGBA_8888_ColorType)
def face_cam(cv, face_im, t, show):
    if show <= 0.01: return
    x, y, w, h = CAM; x = lerp(W + 40, x, ease(show)); fc = E.face_crop(face_im, w, h, 1.05).convert("RGBA")
    img = skia.Image.fromarray(np.ascontiguousarray(np.asarray(fc)), colorType=skia.kRGBA_8888_ColorType)
    cv.drawRoundRect(skia.Rect(x - 4, y + 10, x + w + 4, y + h + 18), 44, 44, paint((0, 0, 0), 0.5, blur=18))
    cv.save(); cv.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), 40, 40), skia.ClipOp.kIntersect, True); cv.drawImage(img, x, y); cv.restore()
    cv.drawRoundRect(skia.Rect(x, y, x + w, y + h), 40, 40, paint(GOLD, 1, 8))
def strip(cv, t, at, a_txt, b_txt, until):
    k = ease(ramp(t, at, 0.4)) * (1 - ease(ramp(t, until, 0.3)))
    if k <= 0: return
    fa, fb = font(BOLD, 44), font(BOLD, 44); wa = fa.measureText(a_txt + " "); wb = fb.measureText(b_txt); x = 40 - (1 - k) * 600
    cv.drawRoundRect(skia.Rect(x - 16, 34, x + wa + wb + 24, 104), 10, 10, paint((0, 0, 0), 0.62)); cv.drawString(a_txt, x, 84, fa, paint(WHITE)); cv.drawString(b_txt, x + wa, 84, fb, paint(YEL))

# ---------------------------------------------------------------- the edit
def sk_upload(cv, t):                                          # 0-9.3: data -> Qdrant -> what it does besides storing
    for k in range(9): m_box(cv, 70 + (k % 3) * 52, 150 + (k // 3) * 46, 40, 34, t, wd(0, "large") - 0.1 + 0.05 * k, 0.2, INK, 5, k)
    m_text(cv, "DATA", 100, 330, 46, t, wd(0, "data") - 0.1, INK, shadow=False); m_text(cv, "1,000,000 pts", 60, 380, 34, t, wd(0, "data") + 0.2, INK, shadow=False)
    m_arrow(cv, 250, 220, 360, 230, t, wd(0, "qdrant") - 0.35, 0.3, INK, 6, 0.1, 3); m_box(cv, 380, 150, 290, 170, t, wd(0, "qdrant") - 0.2, 0.45, INK, 7, 4)
    m_text(cv, "Qdrant", 525, 225, 60, t, wd(0, "qdrant"), (220, 36, 76), align="center", shadow=False); m_text(cv, "vectors", 525, 290, 38, t, wd(0, "store"), INK, align="center", shadow=False)
    for k, (word, lab, x) in enumerate((("payloads", "payloads", 150), ("indexes", "indexes", 400), ("much", "+ much more", 640))):
        at = wd(1, word); m_arrow(cv, 525, 330, x, 520, t, at - 0.3, 0.3, INK, 6, 0.1 * (1 - k), 10 + k); m_text(cv, lab, x, 580, 42, t, at, INK, align="center", shadow=False)
    at = wd(1, "background") - 0.3; cx, cy = 400, 760
    m_circle(cv, cx, cy, 52, 52, t, at, 0.4, INK, 6, 21)
    for k in range(8): a = k * math.pi / 4; m_line(cv, [(cx + 52 * math.cos(a), cy + 52 * math.sin(a)), (cx + 76 * math.cos(a), cy + 76 * math.sin(a))], t, at + 0.3 + 0.03 * k, 0.1, INK, 8, 30 + k)
    m_text(cv, "in the background", 400, 890, 42, t, wd(1, "background"), INK, align="center", shadow=False)
LOG = [(L[1] + 0.05, "python bulk_upload.py --points 1000000", WHITE, True), (L[1] + 1.4, "Uploading 1,000,000 points  [######################----]  86%", (220, 220, 220), False),
       (wd(1, "payloads") - 0.2, "payload    storing 3 fields per point (category, tenant_id, source)", (255, 196, 100), False), (wd(1, "indexes") - 0.2, "index      building HNSW graph  m=16  ef_construct=100", (170, 160, 255), False),
       (wd(1, "much") - 0.1, "optimizer  merging segments 4 -> 2", (130, 220, 160), False), (wd(1, "more") + 0.1, "wal        flushed 41.2 MB to disk", (130, 220, 160), False)]
def notes_term(cv, t):
    f = font(MONO, 32)
    for k, (word, i) in enumerate((("payloads", 2), ("indexes", 3))):                 # box the whole log line, to the edges of its text
        line = LOG[i][1]; m_square(cv, 40, 116 + 50 * i - 30, f.measureText(line), 40, t, wd(1, word), 0.45, YEL, 4.5, 4, k + 1)
    m_line(cv, [(1230, 290), (1260, 300), (1260, 360), (1230, 370)], t, wd(1, "background") - 0.4, 0.3, YEL, 7, 3)
    m_arrow(cv, 1500, 520, 1260, 330, t, wd(1, "background") - 0.1, 0.35, YEL, 7, -0.2, 4); m_text(cv, "all in the background!", 1260, 600, 56, t, wd(1, "background"), YEL)
def underline(cv, name, t, t0, d, seed, c=YEL):
    rs = PJ["targets"][name]; tot = sum(r[2] for r in rs); acc = 0.0
    for k, (x, y, w, h) in enumerate(rs):
        m_line(cv, [(x * S, (y + h) * S + 3), ((x + w) * S, (y + h) * S + 2)], t, t0 + d * acc / tot, d * w / tot, c, 4.5, seed + k); acc += w
def notes_choose(cv, t):
    underline(cv, "there is no single configuration that works best for every bulk upload", t, wd(2, "no") - 0.1, 1.4, 40)
    x, y, w, h = tgt("availability, or a balance of all three"); m_text(cv, "<- no one-size-fits-all!", x + w + 24, y + h - 3, 32, t, wd(2, "works"), YEL)   # in the space after the paragraph's last line
def notes_scroll(cv, t):
    for k, name in enumerate(("Option 1: Reduce Memory Pressure", "Option 2: Create Payload Indexes (Before Uploading)", "Option 3: Quantization to Balance Memory and Search Performance", "Option 4: Reduce Sparse Index Memory During Uploads")):
        x, y, w, h = tgt(name); at = wd(3, "different") - 0.3 + 0.18 * k; m_square(cv, x, y, w, h, t, at, 0.35, YEL, 4.5, 8, 50 + k)
        m_text(cv, str(k + 1), x + w + 30, y + h - 6, 40, t, at + 0.2, YEL)
    for k, name in enumerate(("Batch Your Uploads", "Parallelize Uploads", "Use Multiple Shards for Larger Uploads")):
        x, y, w, h = tgt(name); at = wd(3, "practices") - 0.2 + 0.15 * k; m_line(cv, [(418, y + h / 2), (430, y + h / 2 + 12), (450, y + h / 2 - 14)], t, at, 0.2, (120, 230, 140), 5, 60 + k)
def notes_vectors(cv, t):
    xs, ys, ws, hs = tgt("Dense vectors rely on HNSW>>HNSW"); m_square(cv, xs, ys + 2, ws, hs - 4, t, wd(5, "hnsw") - 0.3, 0.4, YEL, 4, 6, 70)
    xh, yh, wh, hh = tgt("Why Vector Type Matters"); m_text(cv, "a graph index", 1010, yh + 38, 40, t, wd(5, "hnsw") + 0.1, YEL)
    m_arrow(cv, 1080, yh + 54, xs + ws + 10, ys - 4, t, wd(5, "hnsw"), 0.35, YEL, 4.5, 0.25, 71)
    underline(cv, "Sparse vectors use a separate indexing approach", t, wd(6, "sparse") - 0.1, 0.9, 72)
    xp, yp, wp, hp = tgt("means sparse vector ingestion should not be treated the same way as dense HNSW indexing"); m_text(cv, "(an inverted index)", xp + wp + 18, yp + hp - 3, 30, t, wd(6, "indexing") - 0.2, YEL)
def notes_opt1(cv, t):
    x, y, w, h = tgt("memory tier"); m_square(cv, x, y + 2, w, h - 4, t, wd(9, "storing") - 0.2, 0.4, YEL, 4, 6, 80)
    underline(cv, "stores incoming vectors on disk from the start", t, wd(9, "vectors") - 0.1, 0.7, 81)
    xr, yr, wr, hr = tgt("RAM stays free"); m_square(cv, xr - 73, yr - 18, wr + 146, 80, t, wd(9, "disk") - 0.1, 0.45, YEL, 5, 8, 83)   # the diagram's own box (an SVG: its edges sit 73 / 18 px outside the label)
    m_text(cv, "<- this!", xr + wr + 70, yr + hr + 6, 32, t, wd(9, "disk") + 0.3, YEL)
def sk_vectors(cv, t):
    m_text(cv, "dense", 70, 230, 64, t, wd(4, "dense") - 0.1, INK, shadow=False); m_text(cv, "[0.12, 0.83, 0.44, 0.91, ...]", 70, 300, 40, t, wd(4, "dense") + 0.1, INK, 40, shadow=False)
    m_text(cv, "sparse", 70, 460, 64, t, wd(4, "sparse") - 0.1, (220, 36, 76), shadow=False); m_text(cv, "[0, 0, 7, 0, 0, 0, 3, ...]", 70, 530, 40, t, wd(4, "sparse") + 0.1, (220, 36, 76), 40, shadow=False)
    m_text(cv, "every value", 470, 380, 36, t, wd(4, "vectors") - 0.1, INK, shadow=False); m_line(cv, [(440, 330), (430, 360), (452, 368)], t, wd(4, "vectors") - 0.2, 0.2, INK, 5, 90)
    m_text(cv, "mostly zeros", 430, 610, 36, t, wd(4, "vectors") + 0.1, (220, 36, 76), shadow=False)
def sk_costs(cv, t):
    at = wd(7, "memory") - 0.3; m_box(cv, 80, 200, 260, 80, t, at, 0.4, INK, 6, 100)
    for k in range(5): m_box(cv, 100 + k * 48, 220, 32, 40, t, at + 0.3 + 0.04 * k, 0.1, INK, 4, 101 + k)
    for k in range(9): m_line(cv, [(95 + k * 28, 280), (95 + k * 28, 300)], t, at + 0.4, 0.1, INK, 5, 110 + k)
    m_text(cv, "memory", 210, 370, 52, t, wd(7, "memory"), INK, align="center", shadow=False)
    at = wd(7, "performance") - 0.3; cx, cy, r = 560, 270, 110
    p = skia.Path(); p.addArc(skia.Rect(cx - r, cy - r, cx + r, cy + r), 180, 180); draw_on(cv, p, ease(ramp(t, at, 0.4)), INK, 7, False)
    ang = math.radians(180 + 40 + 30 * math.sin(t * 3)); m_line(cv, [(cx, cy), (cx + 85 * math.cos(ang), cy + 85 * math.sin(ang))], t, at + 0.35, 0.15, (220, 36, 76), 7, 120)
    m_text(cv, "performance", 560, 370, 52, t, wd(7, "performance"), INK, align="center", shadow=False)
    m_line(cv, [(80, 430), (700, 432)], t, wd(7, "bulk") - 0.2, 0.4, (220, 36, 76), 7, 121); m_text(cv, "...during BULK uploads", 90, 510, 50, t, wd(7, "bulk"), (220, 36, 76), shadow=False)

EDIT = [  # (start, kind, payload)
    (0.0, "talk", sk_upload), (L[1], "term", (LOG, notes_term)), (L[2], "browser", notes_choose), (L[3], "browser", notes_scroll), (L[4], "talk", sk_vectors),
    (L[5], "browser", notes_vectors), (L[7], "talk", sk_costs), (L[8], "talk", None), (L[9], "browser", notes_opt1)]
STRIPS = [(wd(8, "first") - 0.2, "OPTION 1:", "Store dense vectors on disk", 46.0)]

def frame(t, face_im, hide):
    s = skia.Surface(W, H); cv = s.getCanvas(); i = max(j for j, e in enumerate(EDIT) if t >= e[0]); t0, kind, pay = EDIT[i]
    hidden = lambda tt: any(a <= tt < b for a, b in hide)
    if kind == "talk" and hidden(t):                               # a look-away on a talk shot: hold the screen that came before
        j = max((k for k in range(i) if EDIT[k][1] != "talk"), default=None)
        if j is not None: t0, kind, pay = EDIT[j]
    if kind == "talk":
        cv.drawImage(talk_face(face_im, t, t0), 0, 0)
        if pay: pay(cv, t)
    else:
        (browser(cv, t, pay) if kind == "browser" else terminal(cv, t, pay[0], pay[1]))
        show = 1.0
        for a, b in hide:
            if a - TR <= t < b + TR: show = min(show, 1 - min(ease(ramp(t, a - TR, TR)), 1 - ease(ramp(t, b, TR))))
        face_cam(cv, face_im, t, show)
    for at, a_txt, b_txt, until in STRIPS: strip(cv, t, at, a_txt, b_txt, until)
    return Image.fromarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGBA")

def plan(p, t0, t1):
    hide = E.hidden_spans(p.look); cuts = sorted({t0, t1} | {x for a, b in hide for x in (a, b) if t0 < x < t1}); S_ = []
    for a, b in zip(cuts, cuts[1:]):
        on = not any(x < b and y > a for x, y in hide)
        S_.append(dict(t0=a, t1=b, kind="graphic", shows_face=on, draw=lambda lt, dur, ctx: frame(ctx["t"], ctx["face"], hide), tr="cut", _hidden=False))
    sfx = [(e[0] - 0.03, E.tone(0.03, 700, 500, 0.02, noise=0.5)) for e in EDIT[1:] if t0 <= e[0] < t1]
    return S_, sfx

if __name__ == "__main__":
    a = sys.argv[1:]; p = SF.project()
    if a[:1] == ["stills"]:
        ts = [float(x) for x in a[1:]]; S_, sfx = plan(p, 0, max(ts) + 2); r = E.Renderer(p, S_, 0, p.dur, OUT, sfx, (16, 18, 27)); print(r.stills(ts, OUT.replace(".mp4", "_sheet.png"), cols=4))
    else:
        t0, t1 = (float(a[0]), float(a[1])) if len(a) >= 2 else (0.0, p.dur)
        S_, sfx = plan(p, t0, t1); E.Renderer(p, S_, t0, t1, OUT if (t0, t1) == (0.0, p.dur) else OUT.replace(".mp4", f"_{int(t0)}-{int(t1)}.mp4"), sfx, (16, 18, 27)).render()
