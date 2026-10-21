"""Six more concept frames for new directions (round 2), same moment as round 1. Writes out/concepts/G..L and board2."""
import os, math, numpy as np, cv2, skia
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from concepts import FACE, CUTOUT, font, col, paint, text, skimg, save, OUT, FONTS, W, H, E

# G. SPLIT-FLAP BOARD: the facts arrive on an airport departures board, letters flipping into place
def splitflap():
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col((14, 14, 16))); Y = (255, 214, 10); f = "GeistMono-Bold.ttf"
    rows = [("BULK UPLOAD", "1,000,000 PTS", "ON TIME"), ("PAYLOADS", "3 FIELDS", "STORED"), ("INDEXES", "HNSW M=16", "BUILDING"), ("BACKGROUND", "OPTIMIZER", "RUNNING"), ("RAM", "6.8 / 8 GB", "WARNING")]
    text(cv, "QDRANT  ·  DEPARTURES", 80, 110, 44, Y, "MonaSans-Bold.ttf"); text(cv, "00:05", 1180, 110, 44, (240, 240, 240), f, align="right")
    for r_, row in enumerate(rows):
        y = 170 + r_ * 160; x = 80
        for c_, (txt_, n) in enumerate(zip(row, (11, 13, 8))):
            for k in range(n):
                ch = txt_[k] if k < len(txt_) else " "; cx = x + k * 50
                cv.drawRoundRect(skia.Rect(cx, y, cx + 46, y + 130), 6, 6, paint((34, 34, 38))); cv.drawLine(cx, y + 65, cx + 46, y + 65, paint((0, 0, 0), 0.9, 2))
                if ch != " ": text(cv, ch, cx + 23, y + 92, 64, (240, 240, 240) if not (r_ == 4 and c_ == 2) else (255, 90, 80), f, align="center")
            x += n * 50 + 30
    fc = E.face_crop(FACE, 540, 720, 1.05); cv.drawImage(skimg(fc), W - 80 - 540, 180); cv.drawRect(skia.Rect(W - 620, 180, W - 80, 900), paint(Y, 1, 4))
    cv.drawRect(skia.Rect(W - 620, 900, W - 80, 960), paint(Y)); text(cv, "GATE 1  ·  JOHN KUPCHANKO", W - 600, 942, 30, (14, 14, 16), "MonaSans-Bold.ttf")
    save(s, "G_split_flap")

# H. METRO MAP: the upload's journey as a transit map; each line is a data path, each station a component
def metro():
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col((246, 244, 238))); K = (25, 25, 25)
    lines = [((220, 36, 76), [(120, 540), (520, 540), (700, 360), (1100, 360)], "vectors"), ((0, 150, 136), [(120, 600), (560, 600), (760, 800), (1100, 800)], "payloads"),
             ((96, 71, 255), [(120, 660), (500, 660), (640, 520), (980, 520), (1100, 400)], "indexes")]
    for c, pts, _ in lines:
        pth = skia.Path(); pth.moveTo(*pts[0])
        for p in pts[1:]: pth.lineTo(*p)
        cv.drawPath(pth, paint(c, 1, 26))
    for (x, y, name, big) in ((120, 600, "Your app", True), (520, 560, "Batch", False), (760, 520, "Qdrant API", True), (1100, 360, "Vectors", False), (1100, 800, "Payload store", False), (1100, 420, "HNSW", False)):
        r = 30 if big else 20; cv.drawCircle(x, y, r, paint((255, 255, 255))); cv.drawCircle(x, y, r, paint(K, 1, 8)); text(cv, name, x, y - 50, 34, K, "MonaSans-Bold.ttf", align="center")
    text(cv, "THE UPLOAD LINE", 120, 160, 70, K, "MonaSans-Bold.ttf"); text(cv, "1,000,000 points  ·  3 lines  ·  every 256 points a train", 120, 220, 32, K, "MonaSans-SemiBold.ttf", 0.7)
    for k, (c, _, lab) in enumerate(lines): cv.drawRect(skia.Rect(120 + k * 260, 920, 180 + k * 260, 950), paint(c)); text(cv, lab, 195 + k * 260, 945, 30, K, "MonaSans-SemiBold.ttf")
    fc = E.face_crop(FACE, 480, 480, 1.2); m = Image.new("L", (480, 480), 0); ImageDraw.Draw(m).ellipse([0, 0, 479, 479], fill=255); fc.putalpha(m)
    cv.drawCircle(1580, 560, 254, paint(K)); cv.drawImage(skimg(fc), 1340, 320); text(cv, "You are here", 1580, 880, 32, K, "MonaSans-Bold.ttf", align="center")
    save(s, "H_metro_map")

# I. RISOGRAPH PRINT: a two-colour printed poster, halftone photo, misregistered pink and blue, bold type
def riso():
    pink, blue, paper = np.array([255, 72, 176]), np.array([0, 120, 191]), np.array([244, 239, 228])
    g = np.asarray(E.face_crop(FACE, 900, 1080, 1.0).convert("L")).astype(np.float32) / 255; h, w = g.shape; yy, xx = np.mgrid[0:h, 0:w]
    cell = 9; cx = (xx % cell) - cell / 2; cy = (yy % cell) - cell / 2; rad = np.sqrt(cx ** 2 + cy ** 2); dots = rad < (1 - g) * cell * 0.72
    canvas = np.ones((H, W, 3)) * paper; inkb = np.zeros((H, W)); inkb[:, 1000:1000 + w] = dots; inkp = np.zeros((H, W)); inkp[8:, 1014:1014 + w - 14] = dots[:-8, :-14] * 0.0
    img = canvas * (1 - inkb[..., None] * 0.85) + blue * inkb[..., None] * 0.85
    im = Image.fromarray(img.clip(0, 255).astype(np.uint8)).convert("RGBA"); d = ImageDraw.Draw(im); fb = ImageFont.truetype(os.path.join(FONTS, "MonaSansCondensed-Black.ttf"), 250); fs = ImageFont.truetype(os.path.join(FONTS, "MonaSans-Bold.ttf"), 48)
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0)); do = ImageDraw.Draw(over)
    do.text((70, 60), "1,000,000", font=fb, fill=tuple(pink) + (225,)); do.text((70, 330), "POINTS", font=fb, fill=tuple(pink) + (225,)); do.ellipse([700, 640, 960, 900], fill=tuple(pink) + (200,))
    im.alpha_composite(over); d = ImageDraw.Draw(im); d.text((86, 640), "Qdrant doesn't just", font=fs, fill=tuple(blue)); d.text((86, 700), "store vectors.", font=fs, fill=tuple(blue)); d.text((86, 800), "payloads · indexes · background", font=ImageFont.truetype(os.path.join(FONTS, "GeistMono-Regular.ttf"), 34), fill=tuple(blue))
    n = (np.random.default_rng(1).random((H, W)) * 26 - 13); a = np.asarray(im.convert("RGB")).astype(np.float32) + n[..., None]
    Image.fromarray(a.clip(0, 255).astype(np.uint8)).save(os.path.join(OUT, "I_risograph.png")); print("I_risograph")

# J. NOTEBOOK: a live Jupyter notebook; cells run as he talks and their charts render inline
def notebook():
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col((255, 255, 255))); K = (40, 40, 40); f = "GeistMono-Regular.ttf"
    cv.drawRect(skia.Rect(0, 0, W, 70), paint((245, 245, 245))); text(cv, "bulk_uploads.ipynb", 40, 46, 28, K, "MonaSans-SemiBold.ttf"); cv.drawCircle(1260, 35, 9, paint((61, 180, 100)))
    def cell(y, n, code, h):
        text(cv, f"[{n}]:", 40, y + 42, 24, (48, 63, 159), f); cv.drawRect(skia.Rect(130, y, 1300, y + h), paint((247, 247, 247))); cv.drawRect(skia.Rect(130, y, 1300, y + h), paint((224, 224, 224), 1, 1.5))
        for k, l in enumerate(code): text(cv, l, 150, y + 42 + k * 38, 26, K, f)
    cell(110, 1, ["client.upload_points('docs', points, batch_size=256)"], 64); text(cv, "Uploaded 1,000,000 points in 70.4 s (14,204 pts/s)", 150, 230, 26, K, f)
    cell(270, 2, ["info = client.get_collection('docs')", "plot_memory(info)"], 104)
    for k, (lab, v, c) in enumerate((("vectors", 0.62, (31, 119, 180)), ("payloads", 0.12, (255, 127, 14)), ("HNSW index", 0.26, (44, 160, 44)))):
        y = 420 + k * 90; text(cv, lab, 150, y + 40, 26, K, f); cv.drawRect(skia.Rect(380, y + 10, 380 + 800 * v, y + 60), paint(c)); text(cv, f"{v * 6.8:.1f} GB", 390 + 800 * v, y + 46, 26, K, f)
    cell(720, 3, ["client.update_collection('docs', vectors_config={'': {'on_disk': True}})"], 64); text(cv, "▶ running...", 150, 840, 26, (200, 80, 0), f)
    fc = E.face_crop(FACE, 520, 520, 1.15); cv.drawImage(skimg(fc), 1360, 110); cv.drawRect(skia.Rect(1360, 110, 1880, 630), paint((224, 224, 224), 1, 2)); text(cv, "presenter.mp4", 1360, 670, 24, (120, 120, 120), f)
    save(s, "J_notebook")

# K. MISSION CONTROL: a bank of console screens, telemetry, a countdown, a radar sweep over the cluster
def mission():
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col((6, 10, 14))); G = (90, 255, 160); f = "GeistMono-Regular.ttf"
    def scr(x, y, w, h, title): cv.drawRoundRect(skia.Rect(x, y, x + w, y + h), 14, 14, paint((12, 22, 26))); cv.drawRoundRect(skia.Rect(x, y, x + w, y + h), 14, 14, paint(G, 0.5, 2)); text(cv, title, x + 20, y + 36, 24, G, f, 0.8)
    scr(40, 40, 1180, 140, "UPLOAD  T+00:05"); text(cv, "1,000,000 POINTS  ·  NOMINAL", 70, 150, 64, G, "MonaSans-Bold.ttf")
    scr(40, 210, 580, 520, "CLUSTER RADAR"); cx, cy, r = 330, 490, 210
    for k in (1, 2, 3): cv.drawCircle(cx, cy, r * k / 3, paint(G, 0.35, 1.5))
    ang = math.radians(-50); p = skia.Path(); p.moveTo(cx, cy); p.arcTo(skia.Rect(cx - r, cy - r, cx + r, cy + r), -90, 40, False); p.close(); cv.drawPath(p, paint(G, 0.25)); cv.drawLine(cx, cy, cx + r * math.cos(ang), cy + r * math.sin(ang), paint(G, 1, 3))
    for (dx, dy, n) in ((60, -80, "node-1"), (-110, 40, "node-2"), (120, 90, "node-3")): cv.drawCircle(cx + dx, cy + dy, 8, paint(G)); text(cv, n, cx + dx + 14, cy + dy + 8, 20, G, f)
    scr(640, 210, 580, 520, "TELEMETRY")
    for k, (lab, base, c) in enumerate((("RAM", 0.7, (255, 120, 90)), ("CPU", 0.5, G), ("DISK IO", 0.3, (120, 200, 255)))):
        y0 = 290 + k * 150; text(cv, lab, 660, y0, 22, c, f); pth = skia.Path()
        for i in range(60): v = base + 0.15 * math.sin(i * 0.4 + k) + 0.05 * math.sin(i * 1.7); x = 660 + i * 9; y = y0 + 110 - v * 100; (pth.moveTo if i == 0 else pth.lineTo)(x, y)
        cv.drawPath(pth, paint(c, 1, 3))
    scr(40, 760, 1180, 280, "EVENT LOG")
    for k, l in enumerate(("05.21  payloads   stored, 3 fields", "05.48  indexes    HNSW build started", "06.12  optimizer  merging segments 4 -> 2", "06.60  wal        flushed 41.2 MB")): text(cv, l, 70, 830 + k * 50, 28, G, f)
    scr(1250, 40, 630, 1000, "CAPCOM"); fc = E.face_crop(FACE, 590, 900, 1.05); cv.drawImage(skimg(fc), 1270, 100)
    for y in range(0, H, 3): cv.drawLine(0, y, W, y, paint((0, 0, 0), 0.18, 1))
    save(s, "K_mission_control")

# L. PAPER DIORAMA: layered paper cut-outs with real depth and shadows; the scene builds layer by layer
def diorama():
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col((238, 232, 222)))
    layers = [((222, 214, 200), 760, 0.0), ((210, 98, 120), 830, 1.0), ((96, 92, 200), 900, 2.0), ((40, 50, 80), 980, 3.0)]
    for c, y0, k in layers:
        p = skia.Path(); p.moveTo(0, H)
        for x in range(0, W + 1, 30): p.lineTo(x, y0 - 60 * math.sin(x / (200 + k * 60) + k) - 30 * math.sin(x / 90 + k * 2))
        p.lineTo(W, H); p.close(); cv.save(); cv.translate(0, 14); cv.drawPath(p, paint((0, 0, 0), 0.25, blur=12)); cv.restore(); cv.drawPath(p, paint(c))
    for k, (x, y, w, h, c, lab) in enumerate(((180, 300, 380, 240, (255, 255, 255), "vectors"), (700, 220, 380, 240, (255, 255, 255), "payloads"), (1220, 300, 380, 240, (255, 255, 255), "indexes"))):
        cv.save(); cv.translate(0, 16); cv.drawRoundRect(skia.Rect(x, y, x + w, y + h), 6, 6, paint((0, 0, 0), 0.3, blur=14)); cv.restore(); cv.drawRoundRect(skia.Rect(x, y, x + w, y + h), 6, 6, paint(c))
        text(cv, lab, x + w / 2, y + h / 2 + 22, 64, (40, 50, 80), "MonaSans-Bold.ttf", align="center"); cv.drawLine(x + w / 2, y, x + w / 2, 0, paint((60, 60, 60), 0.6, 2))
    fc = E.face_crop(FACE, 420, 420, 1.2); m = Image.new("L", (420, 420), 0); ImageDraw.Draw(m).ellipse([0, 0, 419, 419], fill=255); fc.putalpha(m)
    cv.save(); cv.translate(0, 16); cv.drawCircle(1660, 760, 220, paint((0, 0, 0), 0.3, blur=16)); cv.restore(); cv.drawCircle(1660, 760, 220, paint((255, 255, 255))); cv.drawImage(skimg(fc), 1450, 550)
    text(cv, "1,000,000 points", 640, 640, 70, (40, 50, 80), "MonaSans-Bold.ttf", align="center")
    save(s, "L_paper_diorama")

for fn in (splitflap, metro, riso, notebook, mission, diorama): fn()
names = [n for n in sorted(os.listdir(OUT)) if n[0] in "GHIJKL" and n.endswith(".png")]
board = Image.new("RGB", (1920, 1620), (20, 20, 24)); d = ImageDraw.Draw(board); fnt = ImageFont.truetype(os.path.join(FONTS, "MonaSans-Bold.ttf"), 34)
for i, n in enumerate(names):
    im = Image.open(os.path.join(OUT, n)).resize((960, 540)); board.paste(im, ((i % 2) * 960, (i // 2) * 540))
    lab = n[:-4].replace("_", " ").upper(); d.rectangle([(i % 2) * 960, (i // 2) * 540, (i % 2) * 960 + 30 + d.textlength(lab, font=fnt), (i // 2) * 540 + 54], fill=(0, 0, 0)); d.text(((i % 2) * 960 + 14, (i // 2) * 540 + 8), lab, font=fnt, fill=(255, 255, 255))
board.save(os.path.join(OUT, "concept_board_2.png")); print("board2")
