"""CODE REPORT: copied from Fireship's Code Report ("The 'vibe coding' mind virus explained", 2M views; audit in
report_style/, storyboard sheets in ref_Tw18/sheets). Real things, not drawn graphics, a new visual every ~2 s:

  docs       a real Qdrant docs paragraph (captured from qdrant.tech) as a card on near-black; a red highlight
             sweeps across each phrase as it is said and the view pushes in on it (his tweet highlight)
  photo      a free-licence stock photo, slow push, heavy white caption with a black outline
  meme       a meme still, same caption treatment, contained on near-black when its shape is not 16:9
  logo       a real logo popping in big on near-black
  stack      words slamming in at staggered positions on near-black (his INGENUITY / CREATIVITY / INSTINCTS)
  rule       a red box title card with a white subtitle (his RULE 1 / choose the right stack)
  face       the presenter full frame, hard cut, alternating punch-in, sometimes captioned

Hard cuts between everything. The face is used only between inserts while the presenter is on the lens; inside a
look-away the insert before it holds.

  python style_report.py 0 41            sample -> out/report_0-41.mp4
  python style_report.py stills 2 6 20   contact sheet
"""
import os, sys, json, math, numpy as np, skia
from PIL import Image
import engine as E
import style_full as SF
import style_launch as LN
W, H = E.W, E.H
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\report.mp4"
DOCS = r"C:\Users\ADMIN\camera_audit\report_style\docs"; MEMES = r"C:\Users\ADMIN\camera_audit\style\memes"; ASSETS = r"C:\Users\ADMIN\camera_audit\assets"
BG = (17, 18, 24); RED = (237, 69, 93); WHITE = (255, 255, 255); BLACK = (0, 0, 0)
CAP = "Poppins-Bold.ttf"; HEAVY = "MonaSansCondensed-Black.ttf"
font, col, ramp, ease, back, lerp = LN.font, LN.col, LN.ramp, E.ease, E.back, LN.lerp
T, L, wd = LN.T, LN.L, LN.wd
def paint(c, a=1.0, w=0.0, blur=0.0):
    p = skia.Paint(AntiAlias=True, Color=col(c, a))
    if w: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(w); p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p
_img = {}
def img(path):
    if path not in _img: _img[path] = skia.Image.open(path)
    return _img[path]
def caption(cv, s, y, t, at, size=96, c=WHITE, x=W / 2, max_w=W - 160):
    """the Fireship caption: heavy, all caps, white with a thick black outline, popping in"""
    if t < at - 0.05 or not s: return
    k = back(ramp(t, at - 0.05, 0.22)); size = LN.fitsize(CAP, s, max_w, size); f = font(CAP, size); w = f.measureText(s)
    cv.save(); cv.translate(x, y); sc = 0.6 + 0.4 * min(1.2, k); cv.scale(sc, sc)
    cv.drawString(s, -w / 2, 0, f, paint(BLACK, 1, size * 0.22)); cv.drawString(s, -w / 2, 0, f, paint(c)); cv.restore()
def plain(cv, s, cx, cy, t, at, size, max_w):
    """black text written into a white meme panel (Drake, Expanding Brain, Gru's plan), wrapped to fit"""
    if t < at - 0.05: return
    k = ease(ramp(t, at - 0.05, 0.15)); f = font(CAP, size); words = s.split(); lines, cur = [], ""
    for wd_ in words:
        if f.measureText((cur + " " + wd_).strip()) > max_w and cur: lines.append(cur); cur = wd_
        else: cur = (cur + " " + wd_).strip()
    lines.append(cur); lh = size * 1.15; y0 = cy - lh * (len(lines) - 1) / 2 + size * 0.35
    for j, l in enumerate(lines): cv.drawString(l, cx - f.measureText(l) / 2, y0 + j * lh, f, paint(BLACK, k))
def captions(cv, t, lines):
    for s, y, at, *rest in lines: caption(cv, s, y, t, at, *(rest or []))

# ---------------------------------------------------------------- inserts: each returns draw(cv, t, t_start, t_end)
def photo(path, lines, push=0.10, focus=(0.5, 0.5)):
    def d(cv, t, a, b):
        im = img(path); k = (t - a) / max(0.1, b - a); z = 1.0 + push * k; s = max(W / im.width(), H / im.height()) * z
        w, h = im.width() * s, im.height() * s; x = (W - w) * focus[0]; y = (H - h) * focus[1]
        cv.drawImageRect(im, skia.Rect.MakeXYWH(x, y, w, h), skia.SamplingOptions(skia.FilterMode.kLinear)); captions(cv, t, lines)
    return d
def meme(path, lines, push=0.06, labels=()):
    """contained on near-black when its shape is far from 16:9; labels = [(text, fx, fy, at)] placed on the image"""
    def d(cv, t, a, b):
        im = img(path); ar = im.width() / im.height(); k = (t - a) / max(0.1, b - a); z = 1.0 + push * k
        s = (max(W / im.width(), H / im.height()) if abs(ar - 16 / 9) < 0.35 else min((W - 120) / im.width(), (H - 80) / im.height())) * z
        w, h = im.width() * s, im.height() * s; x, y = (W - w) / 2, (H - h) / 2
        cv.drawImageRect(im, skia.Rect.MakeXYWH(x, y, w, h), skia.SamplingOptions(skia.FilterMode.kLinear))
        for lab in labels:
            txt, fx, fy, at = lab[:4]; size = lab[4] if len(lab) > 4 else 110; c = lab[5] if len(lab) > 5 else WHITE; mw = lab[6] if len(lab) > 6 else 0.45
            if c == BLACK: plain(cv, txt, x + w * fx, y + h * fy, t, at, size, w * mw)
            else: caption(cv, txt, y + h * fy, t, at, size, c, x + w * fx, w * mw)
        captions(cv, t, lines)
    return d
def logo(path, at, h_px=260):
    def d(cv, t, a, b):
        im = img(path); k = back(ramp(t, at, 0.3)); s = h_px / im.height() * (0.5 + 0.5 * min(1.15, k)) * (1 + 0.04 * (t - a))
        w, h = im.width() * s, im.height() * s; cv.drawImageRect(im, skia.Rect.MakeXYWH((W - w) / 2, (H - h) / 2, w, h), skia.SamplingOptions(skia.FilterMode.kLinear), paint(WHITE, min(1, k * 2)))
    return d
def stack(words):
    """words = [(text, x_frac, y, at, colour)] slamming in"""
    def d(cv, t, a, b):
        for s, fx, y, at, c in words:
            if t < at - 0.08: continue
            k = ease(ramp(t, at - 0.08, 0.16)); f = font(HEAVY, 150); w = f.measureText(s); x = min(max(70, W * fx - w / 2), W - 70 - w)
            cv.save(); cv.translate(x + w / 2, y); sc = 1.35 - 0.35 * k; cv.scale(sc, sc); cv.drawString(s, -w / 2, 0, f, paint(c, k)); cv.restore()
    return d
def rule(title, sub_text, at_title, at_sub):
    def d(cv, t, a, b):
        k = back(ramp(t, at_title - 0.1, 0.28)); f = font(HEAVY, 170); w = f.measureText(title); bw, bh = w + 120, 230; y0 = 300 if sub_text else 425
        cv.save(); cv.translate(W / 2, y0 + bh / 2); sc = 0.5 + 0.5 * min(1.12, k); cv.scale(sc, sc)
        cv.drawRect(skia.Rect(-bw / 2, -bh / 2, bw / 2, bh / 2), paint(RED)); cv.drawString(title, -w / 2, 62, f, paint(WHITE)); cv.restore()
        if sub_text and t >= at_sub - 0.1:
            n = max(1, min(len(sub_text), int((t - at_sub + 0.1) * 40))); s = sub_text[:n]; fs = font(CAP, 76); cv.drawString(s, W / 2 - fs.measureText(sub_text) / 2, 690, fs, paint(WHITE))
    return d

_docs_meta = json.load(open(os.path.join(DOCS, "shots.json"))); _mask = {}
TRIM = 44                                                                      # the capture's padding catches neighbour lines; trim it
def docs(name, hls, zoom=1.32):
    """a real docs paragraph; hls = [(phrase, t_start, t_end)] the red highlight sweeps across each phrase in turn"""
    meta = _docs_meta[name]; path = os.path.join(DOCS, name + ".png")
    def text_mask(phrase):
        key = (name, phrase)
        if key not in _mask:
            src = np.asarray(Image.open(path).convert("RGB")).astype(np.float32); lum = src.mean(axis=2); a = np.clip((lum - 95) / 70, 0, 1)
            rgba = np.zeros(src.shape[:2] + (4,), np.uint8); rgba[..., :3] = 255; rgba[..., 3] = (a * 255).astype(np.uint8)
            _mask[key] = skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType)
        return _mask[key]
    def d(cv, t, a, b):
        im = img(path); iw, ih = im.width(), im.height() - 2 * TRIM; bs = min(1640 / iw, 860 / ih)
        cur = None
        for ph, h0, h1 in hls:
            if t >= h0 - 0.35: cur = (ph, h0)
        z, fx, fy = 1.0, iw / 2, ih / 2
        if cur:
            rects = meta["phrases"][cur[0]]; xs = [r[0] for r in rects] + [r[0] + r[2] for r in rects]; ys = [r[1] - TRIM for r in rects] + [r[1] - TRIM + r[3] for r in rects]
            k = E.inout(ramp(t, cur[1] - 0.35, 0.7)); z = lerp(1.0, min(zoom, 1820 / (iw * bs)), k); fy = lerp(ih / 2, (min(ys) + max(ys)) / 2, k * 0.6)   # push in, centred, the whole line stays in frame
        s = bs * z * (1 + 0.015 * (t - a)); ox, oy = W / 2 - fx * s, H / 2 - fy * s
        cv.save(); cv.translate(ox, oy); cv.scale(s, s)
        cv.drawRoundRect(skia.Rect(-30, 14, iw + 30, ih + 74), 26, 26, paint(BLACK, 0.6, blur=30)); cv.drawRoundRect(skia.Rect(-30, -30, iw + 30, ih + 30), 26, 26, paint((14, 20, 32)))
        cv.save(); cv.clipRect(skia.Rect(0, 0, iw, ih)); cv.drawImage(im, 0, -TRIM, skia.SamplingOptions(skia.FilterMode.kLinear))
        for ph, h0, h1 in hls:                                                  # the highlight sweeps across the phrase, line by line
            if t < h0: continue
            p = min(1.0, (t - h0) / max(0.15, h1 - h0)); rects = meta["phrases"][ph]; tot = sum(r[2] for r in rects); left = p * tot; mk = text_mask(ph)
            for x, y, w, h in rects:
                if left <= 0: break
                ww = min(w, left); left -= w; r = skia.Rect.MakeXYWH(x - 4, y - TRIM - 2, ww + 8, h + 4)
                cv.drawRect(r, paint(RED, 0.95)); cv.save(); cv.clipRect(r); cv.drawImage(mk, 0, -TRIM); cv.restore()
        cv.restore(); cv.restore()
    return d

def face_draw(zoom, lines=()):
    def d(cv, t, a, b, face_im):
        fc = E.face_crop(face_im, W, H, zoom).convert("RGBA"); sk = skia.Image.fromarray(np.ascontiguousarray(np.asarray(fc)), colorType=skia.kRGBA_8888_ColorType)
        cv.drawImage(sk, 0, 0); captions(cv, t, lines)
    return d

# ---------------------------------------------------------------- the edit: (start, kind, content); each runs until the next starts
M = lambda f: os.path.join(MEMES, f)
EDIT = [
    (0.00, "face", face_draw(1.0)),
    (1.10, "insert", photo(M("datacenter.jpg"), [("LARGE AMOUNTS OF DATA", 930, T["large"])], 0.12, (0.5, 0.45))),
    (wd(0, "qdrant") - 0.12, "insert", logo(os.path.join(ASSETS, "qdrant-logo-red-white.png"), wd(0, "qdrant") - 0.12)),
    (wd(0, "doesn't") - 0.1, "face", face_draw(1.12, [("DOESN'T JUST STORE VECTORS", 960, wd(0, "doesn't") + 0.1)])),
    (L[1] + 0.55, "insert", stack([("PAYLOADS", 0.30, 330, wd(1, "payloads"), WHITE), ("INDEXES", 0.62, 560, wd(1, "indexes"), WHITE), ("& MUCH MORE", 0.42, 800, wd(1, "much"), RED)])),
    (wd(1, "background") - 0.6, "insert", meme(M("charlie_conspiracy.jpg"), [("WHAT QDRANT DOES IN THE BACKGROUND", 960, wd(1, "background") - 0.3, 80)])),
    (L[2] + 0.05, "insert", docs("no_single", [("there is no single configuration that works best for every bulk upload", wd(2, "no") - 0.05, wd(2, "works") + 0.1)], 1.35)),
    (wd(2, "for") - 0.05, "insert", meme(M("one_does_not_simply.jpg"), [("USE ONE CONFIG FOR EVERY WORKLOAD", 950, wd(2, "for") + 0.05, 84)])),
    (L[3] + 0.05, "face", face_draw(1.0)),
    (wd(3, "bunch") - 0.05, "insert", meme(M("x_everywhere.jpg"), [("OPTIONS. OPTIONS EVERYWHERE.", 960, wd(3, "different"), 92)])),
    (wd(3, "options") + 0.35, "insert", rule("4 OPTIONS", "+ 3 best practices", wd(3, "options") + 0.35, wd(3, "best") - 0.05)),
    (L[4] + 0.05, "face", face_draw(1.12)),
    (wd(4, "difference") - 0.1, "insert", meme(M("spiderman_pointing.jpg"), [], 0.05, [("DENSE", 0.26, 0.30, wd(4, "dense")), ("SPARSE", 0.74, 0.30, wd(4, "sparse"))])),
    (L[5], "insert", docs("vector_type", [("Dense vectors rely on HNSW", wd(5, "dense"), wd(5, "hnsw") + 0.2), ("Sparse vectors use a separate indexing approach", wd(6, "sparse") - 0.1, wd(6, "indexing") + 0.2)], 1.38)),
    (L[7] + 0.05, "face", face_draw(1.0)),
    (wd(7, "memory") - 0.1, "insert", photo(M("ram.jpg"), [("MEMORY", 880, wd(7, "memory"), 140)], 0.10)),
    (wd(7, "performance") - 0.08, "insert", photo(M("traffic.jpg"), [("PERFORMANCE", 880, wd(7, "performance"), 140)], 0.10, (0.5, 0.6))),
    (wd(7, "considerations") + 0.3, "insert", meme(M("this_is_fine.jpg"), [("YOUR SERVER DURING A BULK UPLOAD", 990, wd(7, "during") - 0.2, 74)])),
    (L[8] + 0.1, "face", face_draw(1.12)),
    (wd(8, "first") - 0.15, "insert", rule("OPTION 1", "dense vectors on disk", wd(8, "first") - 0.15, wd(8, "dense") - 0.1)),
    (L[9] + 0.05, "face", face_draw(1.0)),
    (wd(9, "storing") - 0.2, "insert", docs("option1", [("stores incoming vectors on disk from the start", wd(9, "storing"), wd(9, "disk") - 0.2)], 1.4)),
    (wd(9, "disk") - 0.15, "insert", docs("option1_code", [("memory=models.Memory.COLD", wd(9, "disk"), wd(9, "disk") + 0.8)], 1.55)),
    # line 10-12: raw vectors eat RAM; on disk keeps RAM low; search leans on disk
    (L[10] + 0.3, "insert", docs("option1", [("the raw vector data alone can take up a large amount of RAM", wd(10, "raw"), wd(10, "consume") + 0.2)], 1.4)),
    (wd(10, "a") - 0.1, "insert", meme(M("pikachu.jpg"), [], 0.05, [("RAM AFTER 1,000,000 RAW VECTORS", 0.5, 0.22, wd(10, "lot") - 0.2, 66, BLACK, 0.9)])),
    (L[11] + 0.15, "face", face_draw(1.12, [("LESS RAM AS IT GROWS", 960, wd(11, "reduce"))])),
    (wd(11, "grow") - 0.2, "insert", docs("option1_watch", [("Search performance may depend more on disk access", wd(12, "search"), wd(12, "access") + 0.3)], 1.35)),
    (wd(12, "potentially") - 0.1, "insert", meme(M("waiting_skeleton.jpg"), [("WAITING ON DISK ACCESS", 960, wd(12, "increasing"), 92)])),
    # 13-16: option 2, payload indexes first
    (wd(13, "the"), "insert", rule("OPTION 2", "payload indexes first", wd(13, "second") - 0.05, wd(13, "payload") - 0.1)),
    (wd(13, "before") + 0.05, "face", face_draw(1.0, [("BEFORE YOU UPLOAD", 960, wd(13, "before"))])),
    (L[14], "insert", docs("option2", [("Create payload indexes before uploading points", L[14] + 0.05, wd(14, "which")), ("which fields will be used for filtering", wd(14, "which"), wd(14, "on") + 0.2)], 1.3)),
    (wd(14, "such") - 0.1, "insert", stack([("CATEGORY", 0.28, 330, wd(14, "categories"), WHITE), ("TENANT ID", 0.66, 560, wd(14, "tenant"), WHITE), ("SOURCE", 0.40, 800, wd(14, "sources"), RED)])),
    (wd(14, "you", 2) - 0.1, "insert", docs("option2_code", [('field_name="category"', wd(14, "create") - 0.1, wd(14, "first") + 0.3)], 1.5)),
    (L[15] + 0.05, "insert", docs("option2", [("If those indexes are created after a large dataset has already been uploaded", wd(15, "avoids"), wd(15, "everything") + 0.2)], 1.3)),
    (wd(15, "everything") + 0.45, "insert", meme(M("harold.jpg"), [("REBUILDING THE INDEX AFTER 10M POINTS", 1000, wd(15, "everything") + 0.5, 70)])),
    (L[16] + 0.05, "insert", meme(M("drake.jpg"), [], 0.04, [("INDEX EVERY FIELD", 0.75, 0.25, wd(16, "index"), 64, BLACK, 0.44), ("INDEX ONLY WHAT YOU FILTER ON", 0.75, 0.75, wd(16, "plan") - 0.2, 64, BLACK, 0.44)])),
    # 17-21: option 3, quantization
    (L[17] + 0.05, "insert", rule("OPTION 3", "quantization", wd(17, "final") - 0.05, wd(17, "quantization") - 0.1)),
    (L[18] + 0.05, "insert", docs("option3", [("the original vectors stay on disk", wd(18, "original") - 0.1, wd(18, "disk") + 0.3)], 1.35)),
    (wd(18, "while") + 0.2, "insert", stack([("SMALLER", 0.30, 330, wd(18, "smaller"), WHITE), ("COMPRESSED", 0.62, 560, wd(18, "compressed"), RED), ("FOR SEARCH", 0.42, 800, wd(18, "for"), WHITE)])),
    (L[19] + 0.25, "face", face_draw(1.12, [("SIGNIFICANTLY LESS MEMORY", 960, wd(19, "significantly"))])),
    (L[20], "insert", docs("option3_watch", [("lower memory usage while still keeping search performance practical", wd(20, "while"), wd(20, "practical") + 0.3)], 1.4)),
    (L[21] + 0.05, "insert", meme(M("monkey_puppet.jpg"), [], 0.04, [("WHEN COMPRESSION QUIETLY HURTS YOUR SEARCH QUALITY", 0.5, 0.12, wd(21, "affect"), 52, BLACK, 0.92)])),
    (wd(21, "so") - 0.15, "insert", docs("option3_watch", [("search quality and latency should be tested with real data", wd(21, "test") - 0.1, wd(21, "data") + 0.3)], 1.4)),
    # 22-29: wrap dense, then sparse: option 4
    (L[22] + 0.25, "face", face_draw(1.0)),
    (wd(22, "all") - 0.15, "insert", stack([("ON DISK", 0.28, 330, wd(22, "all"), WHITE), ("PAYLOAD INDEXES", 0.62, 560, wd(22, "three"), WHITE), ("QUANTIZATION", 0.40, 800, wd(22, "options"), RED)])),
    (L[23], "face", face_draw(1.12)),
    (wd(23, "sparse") - 0.15, "insert", rule("SPARSE VECTORS", "", wd(23, "sparse") - 0.15, 0)),
    (L[24] + 0.05, "face", face_draw(1.0)),
    (wd(24, "can") - 0.1, "insert", rule("OPTION 4", "sparse index on disk", wd(24, "can") - 0.1, wd(24, "put") - 0.1)),
    (wd(24, "our") - 0.1, "face", face_draw(1.12)),
    (wd(25, "index") - 0.25, "insert", docs("option4", [("store the sparse vector index on disk", wd(25, "index") - 0.1, wd(25, "disk") + 0.3), ("reduce memory usage when the index becomes large", wd(26, "large") - 0.1, wd(26, "start") + 0.1)], 1.35)),
    (wd(26, "consume") - 0.15, "insert", meme(M("disaster_girl.jpg"), [("YOUR SPARSE INDEX vs YOUR RAM", 960, wd(26, "consume"), 84)])),
    (L[27] + 0.1, "face", face_draw(1.0, [("REDUCES RAM USAGE", 960, wd(27, "reduces"))])),
    (L[28] + 0.05, "insert", photo(M("catalog.jpg"), [("AS YOUR SPARSE INDEX GROWS", 900, wd(28, "sparse"), 90)], 0.10)),
    (L[29] - 0.1, "insert", docs("option4_watch", [("may slow down search because queries can depend more on disk access", wd(29, "searches"), wd(29, "performance") + 0.4)], 1.35)),
    # 30-38: the best practices; 1 batching
    (L[30] + 0.25, "face", face_draw(1.12)),
    (wd(30, "best") - 0.1, "insert", meme(M("leo_cheers.jpg"), [("4 OPTIONS DOWN", 950, wd(30, "options"), 110)])),
    (L[31] + 0.05, "face", face_draw(1.0)),
    (wd(31, "best") - 0.1, "insert", rule("BEST PRACTICES", "for dense and sparse", wd(31, "best") - 0.1, wd(31, "for") - 0.1)),
    (wd(32, "first") - 0.1, "insert", rule("PRACTICE 1", "batch your uploads", wd(32, "first") - 0.1, wd(32, "batching") - 0.1)),
    (L[33] - 0.2, "insert", docs("batch", [("uploading points one at a time is slow", wd(33, "upload"), wd(35, "a") + 0.3)], 1.35)),
    (wd(35, "one") - 0.2, "insert", photo(M("traffic.jpg"), [("ONE. AT. A. TIME.", 880, wd(35, "one"), 130)], 0.10, (0.5, 0.6))),
    (wd(36, "creates") - 0.1, "insert", stack([("NETWORK", 0.30, 330, wd(36, "network"), WHITE), ("PROCESSING", 0.62, 560, wd(36, "processing"), WHITE), ("OVERHEAD", 0.42, 800, wd(36, "overhead"), RED)])),
    (L[37] + 0.25, "face", face_draw(1.12)),
    (wd(37, "64") - 0.2, "insert", rule("64-256", "points per batch", wd(37, "64") - 0.2, wd(37, "is") - 0.1)),
    (wd(37, "good") - 0.05, "insert", docs("batch_code", [("batch_size=256", wd(37, "good"), wd(37, "point") + 0.3)], 1.6)),
    (L[38] - 0.6, "insert", docs("batch_watch", [("increase memory usage and make retries more expensive if a request fails", wd(38, "large"), wd(38, "retry") + 0.2)], 1.35)),
    (wd(38, "more", 1) - 0.1, "insert", meme(M("gru_plan.jpg"), [], 0.03, [("HUGE BATCHES", 0.37, 0.24, wd(38, "more", 1), 34, BLACK, 0.16), ("FAST UPLOAD", 0.87, 0.24, wd(38, "expensive"), 34, BLACK, 0.16),
                                                                 ("ONE REQUEST FAILS", 0.37, 0.74, wd(38, "retry"), 34, BLACK, 0.16), ("RETRY ALL 10,000 POINTS", 0.87, 0.74, wd(38, "fail") - 0.1, 30, BLACK, 0.16)])),
    # 39-43: 2 parallel workers
    (L[39], "insert", rule("PRACTICE 2", "multiple upload workers", wd(39, "second") - 0.05, wd(39, "multiple") - 0.1)),
    (L[40], "insert", photo(M("lanes.jpg"), [("SEVERAL BATCHES AT THE SAME TIME", 900, wd(40, "batches"), 84)], 0.12)),
    (wd(40, "instead") - 0.1, "insert", docs("parallel", [("Two to four workers, each sending its own stream of batches", wd(40, "instead"), wd(40, "stream") + 0.3)], 1.35)),
    (L[41] - 0.05, "insert", docs("parallel_watch", [("Start with two to four workers", L[41] + 0.05, wd(42, "workers") + 0.2)], 1.4)),
    (wd(42, "then") - 0.15, "insert", docs("parallel_code", [("parallel=4", wd(42, "slowly"), wd(42, "increase") + 0.4)], 1.6)),
    (L[43] + 0.05, "insert", docs("parallel_watch", [("Too much parallelism can create extra pressure on CPU, memory, disk I/O, and network resources", wd(43, "too"), wd(43, "overwhelm") + 0.4)], 1.35)),
    (wd(43, "the") - 0.05, "insert", stack([("CPU", 0.24, 300, wd(43, "cpu"), WHITE), ("MEMORY", 0.60, 470, wd(43, "memory"), WHITE), ("DISK", 0.30, 650, wd(43, "disk"), WHITE), ("NETWORK", 0.62, 830, wd(43, "network"), RED)])),
    # 44-47: 3 shards
    (L[44] + 0.3, "face", face_draw(1.0)),
    (wd(44, "consider") - 0.15, "insert", rule("PRACTICE 3", "multiple shards", wd(44, "consider") - 0.15, wd(44, "multiple") - 0.1)),
    (L[45], "insert", docs("shards", [("Each shard has its own write-ahead log and update worker", wd(45, "each"), wd(45, "path") + 0.3), ("process writes in parallel", wd(45, "ingestion"), wd(45, "parallel") + 0.3)], 1.35)),
    (L[46] - 0.25, "insert", docs("shards_watch", [("especially when paired with parallel upload workers", wd(46, "especially"), wd(46, "workers") + 0.3)], 1.35)),
    (wd(46, "parallel") - 0.1, "insert", meme(M("roll_safe.jpg"), [("SHARDS + PARALLEL WORKERS", 950, wd(46, "parallel"), 92)])),
    (L[47] + 0.05, "insert", docs("shards_watch", [("Each shard adds overhead", wd(47, "every"), wd(47, "overhead") + 0.2), ("More shards are not always better", wd(47, "more"), wd(47, "better") + 0.2)], 1.35)),
    (wd(47, "more") - 0.1, "insert", meme(M("expanding_brain.jpg"), [], 0.03, [("2 SHARDS", 0.25, 0.125, wd(47, "more"), 44, BLACK, 0.42), ("8 SHARDS", 0.25, 0.375, wd(47, "shards", 1), 44, BLACK, 0.42),
                                                                        ("64 SHARDS", 0.25, 0.625, wd(47, "not"), 44, BLACK, 0.42), ("1,024 SHARDS", 0.25, 0.875, wd(47, "always"), 44, BLACK, 0.42)])),
    # 48-52: the wrap
    (L[48] + 0.25, "face", face_draw(1.12)),
    (wd(48, "right") - 0.15, "insert", docs("wrap", [("choose the right strategy for the workload", wd(48, "right"), wd(48, "workload") + 0.3)], 1.35)),
    (L[49] + 0.3, "face", face_draw(1.0, [("WHAT ARE YOU OPTIMIZING FOR?", 960, wd(49, "prioritizing"))])),
    (wd(49, "memory") - 0.15, "insert", stack([("MEMORY", 0.28, 300, wd(49, "memory"), WHITE), ("INGESTION SPEED", 0.62, 480, wd(50, "ingestion"), WHITE), ("SEARCH PERFORMANCE", 0.44, 660, wd(50, "search"), WHITE), ("OR A BALANCE", 0.50, 860, wd(50, "balance"), RED)])),
    (wd(51, "between") - 0.2, "face", face_draw(1.12)),
    (wd(52, "thank") - 0.05, "face", face_draw(1.0, [("THANKS FOR WATCHING", 960, wd(52, "thank"))])),
    (wd(52, "watching") + 0.45, "insert", logo(os.path.join(ASSETS, "qdrant-logo-red-white.png"), wd(52, "watching") + 0.45)),
]

def plan(p, t0, t1):
    hide = E.hidden_spans(p.look); segs = []
    for k, (a, kind, fn) in enumerate(EDIT):
        b = EDIT[k + 1][0] if k + 1 < len(EDIT) else p.dur
        if b <= t0 or a >= t1: continue
        segs.append([max(a, t0), min(b, t1), kind, fn, a, b])
    shots = []
    for i, (a, b, kind, fn, a0, b0) in enumerate(segs):
        if kind != "face":
            shots.append(dict(t0=a, t1=b, kind="graphic", shows_face=False, draw=(lambda fn_, a_, b_: lambda lt, dur, ctx: _frame(fn_, ctx["t"], a_, b_))(fn, a0, b0), tr="cut", _hidden=False)); continue
        cuts = sorted({a, b} | {x for p_, q in hide for x in (p_, q) if a < x < b})
        prev = next((s for s in reversed(segs[:i]) if s[2] != "face"), None) or next((s for s in segs[i + 1:] if s[2] != "face"), None)
        for c0, c1 in zip(cuts, cuts[1:]):
            on = not any(p_ < c1 and q > c0 for p_, q in hide)
            if on: shots.append(dict(t0=c0, t1=c1, kind="graphic", shows_face=True, draw=(lambda fn_, a_, b_: lambda lt, dur, ctx: _frame_face(fn_, ctx["t"], a_, b_, ctx["face"]))(fn, a0, b0), tr="cut", _hidden=False))
            else: shots.append(dict(t0=c0, t1=c1, kind="graphic", shows_face=False, draw=(lambda s_: lambda lt, dur, ctx: _frame(s_[3], ctx["t"], s_[4], s_[5] + (c1 - s_[5])))(prev), tr="cut", _hidden=False))
    sfx = [(s["t0"], E.tone(0.035, 900, 600, 0.02, noise=0.4)) for s in shots[1:] if not s["shows_face"]]
    return shots, sfx
def _frame(fn, t, a, b):
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col(BG)); fn(cv, t, a, b); return Image.fromarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGBA")
def _frame_face(fn, t, a, b, face_im):
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col(BG)); fn(cv, t, a, b, face_im); return Image.fromarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGBA")

if __name__ == "__main__":
    a = sys.argv[1:]; p = SF.project()
    if a[:1] == ["stills"]:
        ts = [float(x) for x in a[1:]]; S_, sfx = plan(p, 0, max(ts) + 2); r = E.Renderer(p, S_, 0, p.dur, OUT, sfx, BG); print(r.stills(ts, OUT.replace(".mp4", "_sheet.png"), cols=4))
    else:
        t0, t1 = (float(a[0]), float(a[1])) if len(a) >= 2 else (0.0, p.dur)
        S_, sfx = plan(p, t0, t1); E.Renderer(p, S_, t0, t1, OUT if (t0, t1) == (0.0, p.dur) else OUT.replace(".mp4", f"_{int(t0)}-{int(t1)}.mp4"), sfx, BG).render()
