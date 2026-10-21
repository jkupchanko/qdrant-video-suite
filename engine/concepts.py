"""Six concept frames for completely new editing directions, one still each, at the same moment of Bulk Uploads
(5 s: "Qdrant doesn't just store vectors... payloads, indexes"). Writes out/concepts/<name>.png and a board."""
import os, math, numpy as np, cv2, skia
from PIL import Image, ImageDraw, ImageFont
import engine as E
W, H = E.W, E.H; FONTS = r"C:\Users\ADMIN\camera_audit\fonts"; OUT = r"C:\Users\ADMIN\camera_audit\styles\out\concepts"; os.makedirs(OUT, exist_ok=True)
CUT = r"C:\Users\ADMIN\camera_audit\edit\full_edit\bulk_uploads_full_edit_v2.mp4"; MATTE = r"C:\Users\ADMIN\camera_audit\edit\full_edit\matte_v2_0-41.mp4"; LOGO = r"C:\Users\ADMIN\camera_audit\assets\qdrant-brandmark-red.png"
def grab(path, t):
    c = cv2.VideoCapture(path); c.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = c.read(); return f
F0 = grab(CUT, 5.2); FACE = Image.fromarray(cv2.cvtColor(F0, cv2.COLOR_BGR2RGB)).convert("RGBA")
MT = cv2.cvtColor(grab(MATTE, 5.2), cv2.COLOR_BGR2GRAY)
CUTOUT = FACE.copy(); CUTOUT.putalpha(Image.fromarray(MT))
_tf = {}
def font(name, size):
    if name not in _tf: _tf[name] = skia.Typeface.MakeFromFile(os.path.join(FONTS, name))
    return skia.Font(_tf[name], size)
def col(c, a=1.0): return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(255 * max(0, min(1, a))))
def paint(c, a=1.0, stroke=0, blur=0):
    p = skia.Paint(AntiAlias=True, Color=col(c, a))
    if stroke: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke); p.setStrokeCap(skia.Paint.kRound_Cap)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p
def text(cv, s, x, y, size, c, name="MonaSans-SemiBold.ttf", a=1.0, align="left"):
    f = font(name, size); w = f.measureText(s); x = x - w / 2 if align == "center" else (x - w if align == "right" else x); cv.drawString(s, x, y, f, paint(c, a)); return w
def skimg(im): return skia.Image.fromarray(np.ascontiguousarray(np.asarray(im.convert("RGBA"))), colorType=skia.kRGBA_8888_ColorType)
def save(surf, name): Image.fromarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGB").save(os.path.join(OUT, name + ".png")); print(name)
def quad(cv, img, pts, a=1.0):
    m = skia.Matrix(); w, h = img.width(), img.height(); m.setPolyToPoly([skia.Point(0, 0), skia.Point(w, 0), skia.Point(w, h), skia.Point(0, h)], [skia.Point(*p) for p in pts])
    cv.save(); cv.concat(m); cv.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), paint((255, 255, 255), a)); cv.restore()
def panel_img(w, h, draw, edge=(79, 209, 197)):
    s = skia.Surface(w, h); c = s.getCanvas(); c.clear(skia.Color(0, 0, 0, 0))
    c.drawRoundRect(skia.Rect(0, 0, w, h), 24, 24, paint((20, 40, 60), 0.55)); c.drawRoundRect(skia.Rect(2, 2, w - 2, h - 2), 24, 24, paint(edge, 0.9, 3)); draw(c, w, h); return s.makeImageSnapshot()

# A. HOLOGRAM STAGE: the presenter cut out, standing in a dark space among floating holographic panels
def hologram():
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col((4, 8, 16)))
    cv.drawCircle(W / 2, -200, 900, paint((40, 90, 140), 0.35, blur=200))
    vx, vy = W / 2, 470
    for k in range(-16, 17): cv.drawLine(vx + k * 40, vy, vx + k * 260, H, paint((79, 209, 197), 0.18, 1.5))
    for k in range(12): y = vy + (H - vy) * (k / 12) ** 1.8; cv.drawLine(0, y, W, y, paint((79, 209, 197), 0.12 + 0.01 * k, 1.5))
    def p1(c, w, h): text(c, "POINTS UPLOADED", 40, 70, 30, (150, 220, 230), "GeistMono-Regular.ttf"); text(c, "1,000,000", 40, 200, 120, (240, 250, 255), "MonaSans-Bold.ttf")
    def p2(c, w, h):
        text(c, "PAYLOADS", 40, 70, 30, (150, 220, 230), "GeistMono-Regular.ttf")
        for k, l in enumerate(('{"category": "news",', ' "lang": "en",', ' "year": 2024}')): text(c, l, 40, 140 + k * 54, 40, (255, 200, 120), "GeistMono-Regular.ttf")
    def p3(c, w, h):
        text(c, "HNSW INDEX", 40, 70, 30, (150, 220, 230), "GeistMono-Regular.ttf"); rd = np.random.default_rng(2); pts = [(rd.uniform(60, w - 60), rd.uniform(110, h - 40)) for _ in range(16)]
        for i in range(16):
            for j in range(i + 1, 16):
                if math.dist(pts[i], pts[j]) < 150: c.drawLine(*pts[i], *pts[j], paint((150, 140, 255), 0.8, 3))
        for p in pts: c.drawCircle(*p, 8, paint((240, 250, 255)))
    for img, pts in ((panel_img(640, 300, p1), [(90, 150), (640, 210), (640, 520), (90, 560)]), (panel_img(620, 340, p2), [(1300, 230), (1850, 150), (1850, 560), (1300, 590)]),
                     (panel_img(560, 420, p3), [(1380, 620), (1820, 600), (1820, 960), (1380, 920)])):
        quad(cv, img, pts, 0.92)
        ref = [(x, 2 * 1000 - y) for x, y in pts]; quad(cv, img, [ref[3], ref[2], ref[1], ref[0]], 0.08)
    co = CUTOUT.resize((int(W * 0.9), int(H * 0.9))); cv.drawImage(skimg(co), (W - co.width) // 2 - 40, H - co.height + 20)
    cv.drawOval(skia.Rect(W / 2 - 420, 1020, W / 2 + 300, 1070), paint((79, 209, 197), 0.25, blur=30))
    save(s, "A_hologram_stage")

# B. TERMINAL: the whole video is a terminal UI, box-drawn panes, phosphor amber, scanlines
def terminal():
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col((10, 8, 4))); A_, D_ = (255, 176, 46), (130, 88, 22); f = "GeistMono-Regular.ttf"
    def box(x, y, w, h, title):
        cv.drawRect(skia.Rect(x, y, x + w, y + h), paint(A_, 0.9, 2)); cv.drawRect(skia.Rect(x + 20, y - 14, x + 40 + font(f, 26).measureText(title), y + 14), paint((10, 8, 4))); text(cv, title, x + 30, y + 9, 26, A_, f)
    text(cv, "qdrant-bulk-upload  v1.15        collection: docs        00:05.2        ● LIVE", 40, 50, 28, A_, f)
    box(40, 100, 1100, 420, " upload ");
    for k, (lab, v) in enumerate((("points ", 0.48), ("batches", 0.47), ("vectors", 0.48))):
        y = 180 + k * 70; text(cv, lab, 80, y, 32, A_, f); n = int(40 * v); text(cv, "█" * n + "░" * (40 - n), 260, y, 32, A_, f); text(cv, f"{int(v * 100):3d}%", 1000, y, 32, A_, f)
    text(cv, "482,000 / 1,000,000 points   ·   14,212 pts/s   ·   eta 0:36", 80, 420, 30, D_, f)
    box(40, 560, 1100, 480, " what qdrant does in the background ")
    for k, l in enumerate(("> payloads   storing 3 fields per point ............ ok", "> indexes    building HNSW  m=16  ef=100 .......... 37%", "> optimizer  merging segments 4 -> 2 ................ run",
                          "> wal        flushed 41.2 MB ........................ ok", "> memory     RAM 6.8 / 8.0 GiB  [|||||||||||||||||||    ]")): text(cv, l, 80, 640 + k * 76, 30, A_ if k != 4 else (255, 110, 80), f)
    box(1180, 100, 700, 600, " cam ")
    fc = E.face_crop(FACE, 660, 560, 1.15).convert("L").convert("RGB"); arr = np.asarray(fc).astype(np.float32) / 255
    tint = (arr[:, :, :1] * np.array([1.0, 0.69, 0.18]) * 255).astype(np.uint8); cv.drawImage(skimg(Image.fromarray(tint)), 1200, 120)
    box(1180, 740, 700, 300, " hnsw ")
    for k, l in enumerate(("  L2   o-------o", "  L1   o---o---o---o", "  L0   o-o-o-o-o-o-o-o-o")): text(cv, l, 1210, 820 + k * 70, 32, A_, f)
    for y in range(0, H, 4): cv.drawLine(0, y, W, y, paint((0, 0, 0), 0.28, 1.5))
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), W * 0.7, [col((0, 0, 0), 0), col((0, 0, 0), 0.7)], [0.6, 1.0])); cv.drawRect(skia.Rect(0, 0, W, H), p)
    save(s, "B_terminal")

# C. BLUEPRINT: an engineering drawing of the system, white line work on blueprint blue, a title block
def blueprint():
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col((22, 70, 140))); Wt = (235, 242, 255)
    for x in range(0, W, 30): cv.drawLine(x, 0, x, H, paint(Wt, 0.06 if x % 150 else 0.14, 1))
    for y in range(0, H, 30): cv.drawLine(0, y, W, y, paint(Wt, 0.06 if y % 150 else 0.14, 1))
    cv.drawRect(skia.Rect(30, 30, W - 30, H - 30), paint(Wt, 0.9, 3))
    def iso(x, y, z): return 760 + (x - y) * 0.866, 560 + (x + y) * 0.5 - z
    def ibox(x, y, z, w, d, h, a=1.0):
        P = lambda *q: skia.Point(*iso(*q)); top = [P(x, y, z + h), P(x + w, y, z + h), P(x + w, y + d, z + h), P(x, y + d, z + h)]
        for f_ in (top, [P(x + w, y, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x + w, y, z + h)], [P(x, y + d, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x, y + d, z + h)]):
            pth = skia.Path(); pth.addPoly(f_, True); cv.drawPath(pth, paint(Wt, 0.95 * a, 2.5))
    ibox(0, 0, 0, 520, 360, 50); ibox(30, 30, 50, 90, 50, 25); ibox(220, 130, 50, 110, 110, 20)
    for k in range(5): ibox(380 + k * 22, 80, 50, 10, 200, 55)
    ibox(60, 250, 50, 170, 80, 22); ibox(0, 0, 230, 520, 360, 10, 0.6)
    def lead(px, py, tx, ty, tag, lab):
        cv.drawCircle(px, py, 6, paint(Wt)); cv.drawLine(px, py, tx, ty, paint(Wt, 0.9, 2)); cv.drawLine(tx, ty, tx + (180 if tx > px else -180), ty, paint(Wt, 0.9, 2))
        x0 = tx + 10 if tx > px else tx - 180; cv.drawCircle(x0 + 16, ty - 24, 18, paint(Wt, 0.9, 2)); text(cv, tag, x0 + 16, ty - 15, 24, Wt, "GeistMono-Regular.ttf", align="center"); text(cv, lab, x0 + 44, ty - 14, 24, Wt, "GeistMono-Regular.ttf")
    lead(*iso(75, 55, 75), 330, 250, "A", "NIC"); lead(*iso(275, 185, 70), 980, 230, "B", "CPU"); lead(*iso(430, 180, 105), 1180, 420, "C", "RAM"); lead(*iso(145, 290, 72), 360, 780, "D", "SSD")
    x1, y1 = iso(0, 360, 0); x2, y2 = iso(520, 360, 0); cv.drawLine(x1, y1 + 60, x2, y2 + 60, paint(Wt, 0.9, 2)); text(cv, "1,000,000 pts  ->", (x1 + x2) / 2 - 140, (y1 + y2) / 2 + 100, 28, Wt, "GeistMono-Regular.ttf")
    cv.drawCircle(1560, 330, 200, paint(Wt, 0.95, 4)); fc = E.face_crop(FACE, 384, 384, 1.25); m = Image.new("L", (384, 384), 0); ImageDraw.Draw(m).ellipse([0, 0, 383, 383], fill=255); fc.putalpha(m)
    cv.drawImage(skimg(fc), 1368, 138); text(cv, "DETAIL A  ·  PRESENTER", 1560, 570, 26, Wt, "GeistMono-Regular.ttf", align="center")
    tb = (1330, 760, 560, 290); cv.drawRect(skia.Rect(tb[0], tb[1], tb[0] + tb[2], tb[1] + tb[3]), paint(Wt, 0.95, 3))
    for k, (a_, b_) in enumerate((("TITLE", "BULK UPLOADS"), ("DRG NO.", "QD-01 / PAYLOADS + INDEXES"), ("SCALE", "1 : 1,000,000"), ("DRAWN", "J. KUPCHANKO"))):
        y = tb[1] + 60 + k * 62; cv.drawLine(tb[0], y + 18, tb[0] + tb[2], y + 18, paint(Wt, 0.6, 1.5)); text(cv, a_, tb[0] + 20, y, 20, Wt, "GeistMono-Regular.ttf"); text(cv, b_, tb[0] + 170, y, 26, Wt, "GeistMono-Regular.ttf")
    save(s, "C_blueprint")

# D. SWISS DATA-INK: an editorial grid, one huge number, hairlines, black on paper, a single red accent
def swiss():
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col((242, 240, 235))); K = (17, 17, 17); R = (220, 36, 76)
    for x in (80, 560, 1040, 1520): cv.drawLine(x, 60, x, H - 60, paint(K, 0.10, 1))
    cv.drawLine(80, 150, W - 80, 150, paint(K, 1, 3)); text(cv, "01", 80, 120, 40, K, "MonaSans-Bold.ttf"); text(cv, "Bulk uploads", 180, 120, 40, K, "MonaSans-SemiBold.ttf"); text(cv, "Qdrant · 2026", W - 80, 120, 28, K, "MonaSans-SemiBold.ttf", align="right")
    text(cv, "1,000,000", 70, 560, 330, K, "MonaSansCondensed-Black.ttf"); cv.drawCircle(1435, 300, 26, paint(R))
    text(cv, "points uploaded. Qdrant stores each vector,", 80, 650, 40, K, "MonaSans-SemiBold.ttf"); text(cv, "its payload, and the index around it.", 80, 702, 40, K, "MonaSans-SemiBold.ttf")
    for k, (lab, v) in enumerate((("vectors", 1.0), ("payloads", 0.42), ("index", 0.66))):
        y = 820 + k * 70; text(cv, lab, 80, y + 26, 28, K, "MonaSans-SemiBold.ttf"); cv.drawRect(skia.Rect(260, y, 260 + 760 * v, y + 34), paint(R if k == 2 else K)); text(cv, f"{int(v * 100)}", 280 + 760 * v, y + 28, 28, K, "MonaSans-Bold.ttf")
    fc = E.face_crop(FACE, 420, 560, 1.1); cv.drawImage(skimg(fc), 1420, 320); cv.drawRect(skia.Rect(1420, 320, 1840, 880), paint(K, 1, 2))
    text(cv, "John Kupchanko", 1420, 920, 28, K, "MonaSans-Bold.ttf"); text(cv, "Developer Relations", 1420, 958, 26, K, "MonaSans-SemiBold.ttf", 0.6)
    save(s, "D_swiss_data_ink")

# E. PARTICLE FIELD: the points are particles; a million of them stream in and settle into the collection
def particles():
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col((3, 4, 10))); rd = np.random.default_rng(1)
    for k in range(9000):
        z = rd.uniform(0.2, 1.0); r_ = abs(rd.normal(0, 1)) * 230 + 20; th = rd.uniform(0, 2 * math.pi); x = 1180 + math.cos(th) * r_ * 1.4 + rd.normal(0, 18); y = 520 + math.sin(th) * r_ * 0.8 + rd.normal(0, 18)
        c = (96, 71, 255) if k % 7 else ((79, 209, 197) if k % 2 else (220, 36, 76)); cv.drawCircle(x, y, 1.0 + 2.6 * z * z, paint(c, 0.15 + 0.7 * z, blur=(1 - z) * 4))
    for k in range(900):
        u = rd.uniform(0, 1); x = -50 + u * 1000; y = 540 + math.sin(u * 3 + k) * 80 * (1 - u) + rd.normal(0, 30); cv.drawCircle(x, y, 1.5 + 2 * u, paint((180, 168, 255), 0.25 + 0.6 * u, blur=1))
    cv.drawCircle(1180, 520, 420, paint((96, 71, 255), 0.12, blur=140))
    text(cv, "1,000,000 points", 1180, 930, 64, (240, 243, 250), "MonaSans-Bold.ttf", align="center"); text(cv, "vectors · payloads · indexes", 1180, 985, 30, (150, 156, 180), "GeistMono-Regular.ttf", align="center")
    fc = E.face_crop(FACE, 380, 380, 1.25); m = Image.new("L", (380, 380), 0); ImageDraw.Draw(m).ellipse([0, 0, 379, 379], fill=255); fc.putalpha(m)
    cv.drawCircle(290, 290, 205, paint((180, 168, 255), 0.4, blur=20)); cv.drawImage(skimg(fc), 100, 100)
    save(s, "E_particle_field")

# F. NEWSROOM: a broadcast package; studio window, lower third, live data wall, a ticker
def newsroom():
    s = skia.Surface(W, H); cv = s.getCanvas(); p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(W, H)], [col((8, 20, 52)), col((30, 10, 40))])); cv.drawRect(skia.Rect(0, 0, W, H), p)
    for k in range(0, W, 120): cv.drawLine(k, 0, k - 400, H, paint((255, 255, 255), 0.03, 30))
    fc = E.face_crop(FACE, 1100, 860, 1.0); cv.drawImage(skimg(fc), 60, 60); cv.drawRect(skia.Rect(60, 60, 1160, 920), paint((255, 255, 255), 0.9, 3))
    cv.drawRect(skia.Rect(60, 760, 900, 830), paint((220, 36, 76))); text(cv, "JOHN KUPCHANKO", 90, 808, 38, (255, 255, 255), "MonaSans-Bold.ttf")
    cv.drawRect(skia.Rect(60, 830, 1000, 880), paint((255, 255, 255))); text(cv, "Developer Relations, Qdrant  ·  on bulk uploads", 90, 866, 28, (12, 20, 40), "MonaSans-SemiBold.ttf")
    cv.drawRect(skia.Rect(90, 90, 200, 136), paint((220, 36, 76))); text(cv, "LIVE", 112, 124, 30, (255, 255, 255), "MonaSans-Bold.ttf")
    for k, (lab, val, c) in enumerate((("POINTS UPLOADED", "1,000,000", (255, 255, 255)), ("PAYLOAD FIELDS", "3 / point", (79, 209, 197)), ("INDEX", "HNSW · m=16", (180, 168, 255)), ("RAM", "6.8 GB", (255, 135, 146)))):
        y = 60 + k * 215; cv.drawRect(skia.Rect(1200, y, 1860, y + 195), paint((255, 255, 255), 0.07)); cv.drawRect(skia.Rect(1200, y, 1210, y + 195), paint(c))
        text(cv, lab, 1240, y + 60, 26, (180, 190, 210), "GeistMono-Regular.ttf"); text(cv, val, 1240, y + 150, 70, c, "MonaSans-Bold.ttf")
    cv.drawRect(skia.Rect(0, 970, W, 1040), paint((255, 255, 255))); cv.drawRect(skia.Rect(0, 970, 260, 1040), paint((220, 36, 76))); text(cv, "QDRANT", 40, 1018, 34, (255, 255, 255), "MonaSans-Bold.ttf")
    text(cv, "BULK UPLOADS  ·  4 OPTIONS, 3 BEST PRACTICES  ·  ON_DISK CUTS RAM 69%  ·  BATCH 64-256 POINTS  ·  PARALLEL WORKERS  ·", 290, 1017, 32, (12, 20, 40), "MonaSans-SemiBold.ttf")
    save(s, "F_newsroom")

if __name__ == "__main__":
  for fn in (hologram, terminal, blueprint, swiss, particles, newsroom): fn()
  names = sorted(os.listdir(OUT)); names = [n for n in names if n[0] in "ABCDEF" and n.endswith(".png")]
  board = Image.new("RGB", (1920, 1620), (20, 20, 24)); d = ImageDraw.Draw(board); fnt = ImageFont.truetype(os.path.join(FONTS, "MonaSans-Bold.ttf"), 34)
  for i, n in enumerate(names):
      im = Image.open(os.path.join(OUT, n)).resize((960, 540)); board.paste(im, ((i % 2) * 960, (i // 2) * 540))
      lab = n[:-4].replace("_", " ").upper(); d.rectangle([(i % 2) * 960, (i // 2) * 540, (i % 2) * 960 + 30 + d.textlength(lab, font=fnt), (i // 2) * 540 + 54], fill=(0, 0, 0)); d.text(((i % 2) * 960 + 14, (i // 2) * 540 + 8), lab, font=fnt, fill=(255, 255, 255))
  board.save(os.path.join(OUT, "concept_board.png")); print("board")
