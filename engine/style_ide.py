"""IDE WALKTHROUGH: the whole video happens in the editor, the way the top coding channels show it
(Nick Chapsas, Tech With Tim, CodeAesthetic; see coding_audit/report.md).

A VS Code window fills the frame. The real Qdrant Python is typed as the presenter talks. The line he is
discussing gets selected, and the view zooms in on it the way screen-recording tutorials do. Hover docs pop
up over the call he names. The terminal shows the upload running, the optimizer's log and memory use. The
explorer gains the option files as he lists them. His face sits in a small round cam top right (the house
rule for code), hidden whenever he looks away.

  python style_ide.py 0 41             sample -> out/ide_0-41.mp4
  python style_ide.py stills 2 6 20    contact sheet
"""
import os, sys, json, math, re, numpy as np, skia
from PIL import Image, ImageDraw
import engine as E
import style_full as SF
W, H, SS = E.W, E.H, 2                                                          # the IDE is drawn at 2x, so zooming stays sharp
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\ide.mp4"
FONTS = r"C:\Users\ADMIN\camera_audit\fonts"
C = dict(bg=(0x1E, 0x1E, 0x1E), side=(0x25, 0x25, 0x26), act=(0x33, 0x33, 0x33), title=(0x32, 0x32, 0x33), tab=(0x2D, 0x2D, 0x2D), tabon=(0x1E, 0x1E, 0x1E),
         line=(0x85, 0x85, 0x85), txt=(0xD4, 0xD4, 0xD4), kw=(0xC5, 0x86, 0xC0), fn=(0xDC, 0xDC, 0xAA), st=(0xCE, 0x91, 0x78), num=(0xB5, 0xCE, 0xA8),
         com=(0x6A, 0x99, 0x55), cls=(0x4E, 0xC9, 0xB0), arg=(0x9C, 0xDC, 0xFE), sel=(0x26, 0x4F, 0x78), status=(0x00, 0x7A, 0xCC), term=(0x18, 0x18, 0x18),
         ok=(0x89, 0xD1, 0x85), warn=(0xF1, 0x4C, 0x4C), border=(0x45, 0x45, 0x45), hover=(0x25, 0x25, 0x26))
_tf = {}
def font(name, size):
    if name not in _tf: _tf[name] = skia.Typeface.MakeFromFile(os.path.join(FONTS, name))
    return skia.Font(_tf[name], size)
MONO = "FiraCode[wght].ttf"; UI = "Inter[opsz,wght].ttf"
def col(c, a=1.0): return skia.Color(c[0], c[1], c[2], int(255 * max(0, min(1, a))))
def paint(c, a=1.0, stroke=0):
    p = skia.Paint(AntiAlias=True, Color=col(c, a))
    if stroke: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
    return p
def rect(cv, x, y, w, h, c, a=1.0, r=0): cv.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), r, r, paint(c, a)) if r else cv.drawRect(skia.Rect.MakeXYWH(x, y, w, h), paint(c, a))
def text(cv, s, x, y, size, c, name=UI, a=1.0): cv.drawString(s, x, y, font(name, size), paint(c, a))
def ramp(t, a, d=0.5): return max(0.0, min(1.0, (t - a) / d))
ease, inout = E.ease, E.inout
WORDS = json.load(open(r"C:\Users\ADMIN\camera_audit\styles\out\v2_words.json"))["pieces"]
def wd(i, w, nth=0):
    hits = [t for x, t in WORDS[i]["words"] if x.lower().strip(",.?!").startswith(w.lower())]; return hits[min(nth, len(hits) - 1)]
T = dict(up=wd(0, "uploading"), large=wd(0, "large"), qd=wd(0, "qdrant"), store=wd(0, "store"), pay=wd(1, "payloads"), idx=wd(1, "indexes"), bg=wd(1, "much"),
         conf=wd(2, "configuration"), opt=wd(3, "options"), best=wd(3, "best"), d0=WORDS[4]["t0"], dense=wd(4, "dense"), sparse=wd(4, "sparse"), hnsw=wd(5, "hnsw"),
         sidx=wd(6, "completely"), mem=wd(7, "memory"), perf=wd(7, "performance"), first=wd(8, "first"), l9=WORDS[9]["t0"], storing=wd(9, "storing"), disk=wd(9, "disk"))

# ---------------------------------------------------------------- the code, typed on the spoken words
CPS = 42                                                                        # typing speed, characters a second
HEAD = [('"""Bulk upload 1,000,000 points into Qdrant."""', None), ("import json", None), ("from qdrant_client import QdrantClient, models", None), ("", None),
        ('client = QdrantClient(url="http://localhost:6333")', None), ("", None), ("def load_points(path):", None), ("    with open(path) as f:", None),
        ("        for i, line in enumerate(f):", None), ("            rec = json.loads(line)", None),
        ('            yield models.PointStruct(id=i, vector=rec["vector"], payload=rec["payload"])', None), ("", None)]
OFF = len(HEAD) - 4                                                              # the file opens with real code in it; typed lines follow
MAIN = HEAD + [  # (text, time typing starts); None = there from the start
    ('points = load_points("data.jsonl")  # 1,000,000 points', T["large"] - 0.3), ('client.upload_points("docs", points=points, batch_size=256)', T["qd"] - 0.1), ("", T["qd"] + 1.2),
    ("# no single configuration fits every workload", T["conf"] - 0.6), ("client.create_collection(", T["d0"] + 0.1), ('    "docs",', T["d0"] + 0.5),
    ("    vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),", T["dense"] - 1.0),
    ("    hnsw_config=models.HnswConfigDiff(m=16, ef_construct=100),", T["hnsw"] - 0.9),
    ("    sparse_vectors_config={", T["sparse"] - 0.4), ('        "text": models.SparseVectorParams(index=models.SparseIndexParams()),', T["sparse"] - 0.1),
    ("    },", T["sparse"] + 1.6), (")", T["sparse"] + 1.7)]
OPT1 = [("from qdrant_client import QdrantClient, models", None), ("", None), ('client = QdrantClient(url="http://localhost:6333")', None), ("", None),
        ("client.create_collection(", None), ('    "docs",', None), ("    vectors_config=models.VectorParams(", None), ("        size=768,", None),
        ("        distance=models.Distance.COSINE,", None), ("        on_disk=True,", T["disk"] - 0.55), ("    ),", None), (")", None)]
T_TAB = T["first"] - 0.1                                                        # the option file opens on "first option"
SEL = [  # (doc, line, substring, start, end): the selection that follows the words
    ("main", 4 + OFF, "1,000,000 points", T["large"] + 0.4, T["qd"] - 0.2), ("main", 5 + OFF, "upload_points", T["qd"] + 0.6, T["pay"] - 0.3), ("main", 7 + OFF, "no single configuration", T["conf"] - 0.1, WORDS[3]["t0"]),
    ("main", 10 + OFF, "VectorParams", T["dense"] - 0.1, T["sparse"] - 0.3), ("main", 13 + OFF, "SparseVectorParams", T["sparse"] + 0.2, T["hnsw"] - 1.0), ("main", 11 + OFF, "HnswConfigDiff", T["hnsw"] - 0.2, WORDS[6]["t0"]),
    ("main", 13 + OFF, "SparseIndexParams", T["sidx"] - 0.3, WORDS[7]["t0"]), ("opt1", 9, "on_disk=True", T["disk"] + 0.05, 99)]
HOVERS = [  # (doc, line, anchor substring, start, end, lines of the tooltip)
    ("main", 4 + OFF, "points", T["pay"] - 0.3, T["idx"] - 0.2, ["points: list[PointStruct]", "PointStruct(id=1, vector=[0.12, -0.08, ...],", '            payload={"category": "news", "lang": "en"})']),
    ("main", 13 + OFF, "SparseIndexParams", T["sidx"] + 0.2, WORDS[7]["t0"] + 0.4, ["class SparseIndexParams", "Configuration for the sparse inverted index.", "on_disk: bool | None  (store the index on disk)"]),
    ("opt1", 9, "on_disk", T["disk"] + 0.4, 99, ["on_disk: bool | None", "If true, vectors are served from disk, not RAM,", "which keeps RAM low as the collection grows."])]
TERM = [  # (time, line) appended to the terminal; "{pct}" and "{mem}" update live
    (T["qd"] + 0.9, "$ python bulk_upload.py"), (T["qd"] + 1.3, "Uploading points  {bar}  {pct}%  {n}/1,000,000"),
    (T["idx"] - 0.1, "INFO  optimizer: building HNSW index, segment 2 of 8"), (T["bg"] - 0.1, "INFO  wal: flushed 4.1 MB"), (T["bg"] + 0.4, "INFO  optimizer: merging 3 segments"),
    (T["mem"] - 0.6, "$ docker stats qdrant --no-stream"), (T["mem"] - 0.3, "NAME      CPU %     MEM USAGE / LIMIT"), (T["mem"] - 0.2, "qdrant    {cpu}%     {mem} GiB / 8 GiB")]
EXPLORER = [("bulk_upload.py", None, 0), ("data.jsonl", None, 0), ("docker-compose.yml", None, 0), ("options/", T["opt"] - 0.4, 0), ("1_on_disk.py", T["opt"] - 0.3, 1),
            ("2_payload_index.py", T["opt"] - 0.2, 1), ("3_quantization.py", T["opt"] - 0.1, 1), ("4_sparse_on_disk.py", T["opt"], 1), ("best_practices/", T["best"] - 0.3, 0),
            ("batching.py", T["best"] - 0.2, 1), ("workers.py", T["best"] - 0.1, 1), ("shards.py", T["best"], 1)]

KW = set("from import as def return class if else for in while with True False None".split())
def tokens(s):
    """a small Python highlighter: comments, strings, numbers, keywords, classes, calls, keyword args, attributes"""
    out = []
    for m in re.finditer(r'(#.*$)|("[^"]*"?)|(\b\d[\d_,.]*\b)|(\w+)(?=\s*=(?!=))|(\w+)(?=\()|(\b[A-Z]\w*)|(\w+)|(\s+)|(.)', s):
        g = m.lastindex; v = m.group(0)
        c = {1: C["com"], 2: C["st"], 3: C["num"], 4: C["arg"], 5: C["fn"], 6: C["cls"], 7: C["kw"] if v in KW else C["txt"]}.get(g, C["txt"])
        out.append((v, c))
    return out

# ---------------------------------------------------------------- the IDE, drawn in its own (2x) coordinates
IW, IH = W * SS, H * SS
LAY = dict(title=38 * SS, act=52 * SS, side=270 * SS, tabs=38 * SS, status=26 * SS, term_h=330 * SS, gutter=70 * SS)
FS = 25 * SS; LH = int(FS * 1.55); CW = None                                # code set large, as coding channels do
def char_w():
    global CW
    if CW is None: CW = font(MONO, FS).measureText("M")
    return CW
def code_xy(doc_lines, li):
    x0 = LAY["act"] + LAY["side"] + LAY["gutter"] + 16 * SS; y0 = LAY["title"] + LAY["tabs"] + 18 * SS; return x0, y0 + li * LH
FIT = int((IH - LAY["status"] - LAY["term_h"] - LAY["title"] - LAY["tabs"] - 30 * SS) / LH) - 1
def visible(doc, t):
    """lines shown at t, with how much of each is typed, a smooth slide as lines are inserted, and a smooth
    scroll once they no longer fit above the terminal"""
    rows, y, apps = [], 0.0, []
    for k, (s, ts) in enumerate(doc):
        if ts is None: n, grow = len(s), 1.0
        else:
            if t < ts: continue
            n, grow = min(len(s), int((t - ts) * CPS)), ease(ramp(t, ts, 0.15)); apps.append(ts)
        rows.append((k, s, n, y)); y += grow
    over = len(rows) - FIT; scroll = sum(ease(ramp(t, ts, 0.3)) for ts in sorted(apps)[max(0, len(apps) - over):]) if over > 0 else 0.0
    return [(k, s, n, yy - scroll) for (k, s, n, yy) in rows if yy - scroll > -1]

def draw_ide(cv, t):
    doc_name = "opt1" if t >= T_TAB else "main"; doc = OPT1 if doc_name == "opt1" else MAIN
    rect(cv, 0, 0, IW, IH, C["bg"])
    rect(cv, 0, 0, IW, LAY["title"], C["title"])                                # title bar
    for k, c in enumerate(((0xFF, 0x5F, 0x57), (0xFE, 0xBC, 0x2E), (0x28, 0xC8, 0x40))): cv.drawCircle((22 + k * 22) * SS, LAY["title"] / 2, 6.5 * SS, paint(c))
    ttl = f"{'1_on_disk.py' if doc_name == 'opt1' else 'bulk_upload.py'} — qdrant-bulk-uploads"; f = font(UI, 14 * SS); cv.drawString(ttl, (IW - f.measureText(ttl)) / 2, LAY["title"] * 0.68, f, paint(C["line"]))
    rect(cv, 0, LAY["title"], LAY["act"], IH, C["act"])                       # activity bar
    for k in range(5): rect(cv, 14 * SS, LAY["title"] + (18 + k * 50) * SS, 24 * SS, 24 * SS, (0x85, 0x85, 0x85) if k else (0xFF, 0xFF, 0xFF), 0.9, 4 * SS)
    sx = LAY["act"]; rect(cv, sx, LAY["title"], LAY["side"], IH, C["side"])     # explorer
    text(cv, "EXPLORER", sx + 20 * SS, LAY["title"] + 26 * SS, 12 * SS, C["line"]); text(cv, "QDRANT-BULK-UPLOADS", sx + 20 * SS, LAY["title"] + 58 * SS, 12.5 * SS, C["txt"])
    y = LAY["title"] + 90 * SS
    for name, ts, ind in EXPLORER:
        if ts is not None and t < ts: continue
        a = ease(ramp(t, ts, 0.25)) if ts is not None else 1.0; active = (name == "1_on_disk.py" and t >= T_TAB) or (name == "bulk_upload.py" and t < T_TAB)
        if active: rect(cv, sx, y - 20 * SS, LAY["side"], 28 * SS, (0x37, 0x37, 0x3D), a)
        if name == "1_on_disk.py" and T_TAB - 0.6 < t < T_TAB + 0.3: rect(cv, sx, y - 20 * SS, LAY["side"], 28 * SS, C["status"], 0.45 * a)
        ic = (0x4B, 0x8B, 0xBE) if name.endswith(".py") else ((0xE3, 0xB3, 0x41) if name.endswith("/") else (0xA0, 0xA0, 0xA0))
        rect(cv, sx + (24 + ind * 18) * SS, y - 13 * SS, 11 * SS, 11 * SS, ic, a, 2 * SS); text(cv, name, sx + (44 + ind * 18) * SS, y - 2 * SS, 14 * SS, C["txt"], UI, a); y += 30 * SS
    ex = LAY["act"] + LAY["side"]; ty = LAY["title"]; rect(cv, ex, ty, IW - ex, LAY["tabs"], C["tab"])   # tabs
    tabs = ["bulk_upload.py"] + (["1_on_disk.py"] if t >= T_TAB else [])
    for k, name in enumerate(tabs):
        on = (k == len(tabs) - 1); w = 200 * SS; rect(cv, ex + k * w, ty, w, LAY["tabs"], C["tabon"] if on else C["tab"])
        if on: rect(cv, ex + k * w, ty, w, 2 * SS, C["status"])
        text(cv, name, ex + k * w + 22 * SS, ty + 25 * SS, 14 * SS, C["txt"] if on else C["line"])
    rows = visible(doc, t); f = font(MONO, FS); cw = char_w()
    term_top = IH - LAY["status"] - LAY["term_h"]
    for (k, s, n, yy) in rows:                                                   # gutter and code
        x0, _ = code_xy(doc, 0); y0 = LAY["title"] + LAY["tabs"] + 18 * SS + (yy + 1) * LH
        if y0 > term_top - LH * 0.3: break
        for (d_, li, sub, a0, a1) in SEL:                                        # the selection that follows the words
            if d_ == doc_name and li == k and a0 <= t < a1 and sub in s[:n]:
                i = s.index(sub); rect(cv, x0 + i * cw, y0 - FS * 0.95, len(sub) * cw, LH * 0.92, C["sel"], ease(ramp(t, a0, 0.15)))
        fs_n = font(MONO, FS * 0.9); ln = str(k + 1); cv.drawString(ln, x0 - 16 * SS - fs_n.measureText(ln) - 10 * SS, y0, fs_n, paint(C["line"]))
        x = x0; shown = 0
        for v, c_ in tokens(s):
            if shown >= n: break
            part = v[: max(0, n - shown)]; cv.drawString(part, x, y0, f, paint(c_)); x += len(part) * cw; shown += len(v)
        if n < len(s) or (k == rows[-1][0] and (t * 2) % 2 < 1.3):               # the cursor at the end of the typing
            if n < len(s) or k == rows[-1][0]: rect(cv, x0 + n * cw, y0 - FS * 0.95, 2.5 * SS, LH * 0.9, C["txt"])
    for (d_, li, sub, a0, a1, lines_) in HOVERS:                                 # hover docs
        if d_ != doc_name or not (a0 <= t < a1): continue
        row = next((r for r in rows if r[0] == li), None)
        if not row or sub not in row[1]: continue
        x0, _ = code_xy(doc, 0); y0 = LAY["title"] + LAY["tabs"] + 18 * SS + (row[3] + 1) * LH; i = row[1].index(sub); hx, hy = x0 + i * cw, y0 + LH * 0.55
        a = ease(ramp(t, a0, 0.2)); fh = font(MONO, FS * 0.86); wmax = max(fh.measureText(s_) for s_ in lines_) + 40 * SS
        rect(cv, hx, hy, wmax, len(lines_) * LH * 0.9 + 26 * SS, C["hover"], a, 6 * SS); cv.drawRoundRect(skia.Rect.MakeXYWH(hx, hy, wmax, len(lines_) * LH * 0.9 + 26 * SS), 6 * SS, 6 * SS, paint(C["border"], a, 1.5 * SS))
        for q, s_ in enumerate(lines_):
            colr = C["cls"] if q == 0 else (C["txt"] if q == 1 else C["arg"])
            if "payload" in s_ and q == 2: colr = C["st"]
            cv.drawString(s_, hx + 20 * SS, hy + 34 * SS + q * LH * 0.9, fh, paint(colr, a))
    rect(cv, ex, term_top, IW - ex, LAY["term_h"], C["term"]); rect(cv, ex, term_top, IW - ex, 1.5 * SS, C["border"])   # terminal
    text(cv, "TERMINAL", ex + 20 * SS, term_top + 26 * SS, 12 * SS, C["txt"]); rect(cv, ex + 20 * SS, term_top + 33 * SS, 62 * SS, 1.5 * SS, C["txt"])
    lines_t = [(ts, s) for ts, s in TERM if t >= ts]; ft = font(MONO, FS * 0.86); yt = term_top + 70 * SS
    pct = int(100 * ease(ramp(t, T["qd"] + 1.3, 7.0))); mem = 3.1 + 3.7 * ease(ramp(t, T["mem"] - 0.2, 2.2)); cpu = 120 + int(60 * abs(math.sin(t * 1.3)))
    for ts, s in lines_t[-7:]:
        bar = "━" * (pct // 5) + "╺" + "─" * (20 - pct // 5)
        s2 = s.replace("{bar}", bar).replace("{pct}", f"{pct:3d}").replace("{n}", f"{pct * 10000:,}").replace("{mem}", f"{mem:.1f}").replace("{cpu}", str(cpu))
        c_ = C["ok"] if s.startswith("$") else (C["warn"] if "{mem}" in s and mem > 6 else (C["arg"] if s.startswith("INFO") else C["txt"]))
        if "{bar}" in s:
            pre = s2.split(bar)[0]; cv.drawString(pre, ex + 24 * SS, yt, ft, paint(C["txt"])); xb = ex + 24 * SS + ft.measureText(pre)
            cv.drawString(bar[: pct // 5], xb, yt, ft, paint(C["ok"])); cv.drawString(bar[pct // 5:], xb + ft.measureText(bar[: pct // 5]), yt, ft, paint(C["line"])); cv.drawString(s2.split(bar)[1], xb + ft.measureText(bar), yt, ft, paint(C["txt"]))
        else: cv.drawString(s2, ex + 24 * SS, yt, ft, paint(c_))
        yt += LH * 0.9
    rect(cv, 0, IH - LAY["status"], IW, LAY["status"], C["status"])             # status bar
    text(cv, "main   Python 3.12   qdrant-client 1.15", 14 * SS, IH - 8 * SS, 13 * SS, (0xFF, 0xFF, 0xFF))
    return rows, doc_name

# ---------------------------------------------------------------- the camera: zooms in on what is being said, like a screen-recording tutorial
def line_center(doc, li, t):
    rows = visible(doc, t); row = next((r for r in rows if r[0] == li), None); yy = row[3] if row else li
    x0, _ = code_xy(doc, 0); return (x0 + 360 * SS, LAY["title"] + LAY["tabs"] + 18 * SS + (yy + 1) * LH)
TERM_C = (LAY["act"] + LAY["side"] + 420 * SS, IH - LAY["status"] - LAY["term_h"] + 150 * SS)      # the output lines, not the empty panel
EXPL_C = (LAY["act"] + LAY["side"] / 2 + 260 * SS, LAY["title"] + 260 * SS)
def cam_keys(t):
    return [(0.0, ("main", 6), 1.45), (T["large"] - 0.2, ("main", 4 + OFF), 1.6), (T["qd"] + 1.0, TERM_C, 1.55), (T["pay"] - 0.4, ("main", 5 + OFF), 1.5), (T["idx"] - 0.3, TERM_C, 1.55),
            (WORDS[2]["t0"], ("main", 7 + OFF), 1.55), (T["opt"] - 0.6, EXPL_C, 1.6), (T["d0"], ("main", 10 + OFF), 1.4), (T["hnsw"] - 0.6, ("main", 11 + OFF), 1.5),
            (T["sidx"] - 0.4, ("main", 13 + OFF), 1.45), (T["mem"] - 0.8, TERM_C, 1.55), (T["first"] - 0.7, EXPL_C, 1.55), (T_TAB + 0.6, ("opt1", 7), 1.75), (T["disk"] - 0.7, ("opt1", 9), 1.75)]
def camera(t):
    ks = cam_keys(t); cur = ks[0]
    def pos(k):
        if k[1] is None: return (IW / 2, IH / 2)
        if isinstance(k[1][0], str): return line_center(OPT1 if k[1][0] == "opt1" else MAIN, k[1][1], t)
        return k[1]
    i = max(j for j, k in enumerate(ks) if t >= k[0]); a = ks[i]; b = ks[i - 1] if i else ks[0]; e = inout(ramp(t, a[0], 0.8))
    pa, pb = pos(a), pos(b); z = b[2] + (a[2] - b[2]) * e; x = pb[0] + (pa[0] - pb[0]) * e; y = pb[1] + (pa[1] - pb[1]) * e
    vw, vh = IW / z, IH / z; left, top = x - 0.40 * vw, y - 0.60 * vh                     # the line being said sits left of centre, clear of the face cam
    left = min(max(left, 0), IW - vw); top = min(max(top, 0), IH - vh); return left, top, vw, vh

CAM_R = 130; CAM_C = (W - 50 - CAM_R, 50 + CAM_R)                                  # the presenter's round cam, top right
def frame(t, face_im, show_face):
    surf = skia.Surface(IW, IH); cv = surf.getCanvas(); draw_ide(cv, t)
    x, y, w, h = camera(t); img = surf.makeImageSnapshot()
    out = skia.Surface(W, H); oc = out.getCanvas(); oc.drawImageRect(img, skia.Rect.MakeXYWH(x, y, w, h), skia.Rect.MakeWH(W, H), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
    fr = Image.fromarray(out.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGBA")
    if show_face:
        d = 2 * CAM_R; f = E.face_crop(face_im, d, d, 1.3); m = Image.new("L", (d, d), 0); ImageDraw.Draw(m).ellipse([0, 0, d - 1, d - 1], fill=255); f.putalpha(m)
        ring = Image.new("RGBA", (d + 12, d + 12), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse([0, 0, d + 11, d + 11], fill=(0x00, 0x7A, 0xCC, 255))
        fr.alpha_composite(ring, (CAM_C[0] - CAM_R - 6, CAM_C[1] - CAM_R - 6)); fr.paste(f, (CAM_C[0] - CAM_R, CAM_C[1] - CAM_R), f)
    return fr

def plan(p, t0, t1):
    hide = E.hidden_spans(p.look); cuts = sorted({t0, t1} | {x for a, b in hide for x in (a, b) if t0 < x < t1}); S_ = []
    for a, b in zip(cuts, cuts[1:]):
        on = not any(x < b and y > a for x, y in hide)
        S_.append(dict(t0=a, t1=b, kind="graphic", shows_face=on, draw=(lambda on_: lambda lt, dur, ctx: frame(ctx["t"], ctx["face"], on_))(on), tr="cut", _hidden=False))
    keys = [s for s, ts in MAIN + OPT1 if ts is not None]; sfx = []
    for doc in (MAIN, OPT1):                                                     # soft key clicks while typing
        for s, ts in doc:
            if ts is None or not (t0 <= ts < t1): continue
            for k in range(0, len(s), 3): sfx.append((ts + k / CPS, E.tone(0.012, 2400, 1800, 0.012, noise=0.6)))
    return S_, sfx

if __name__ == "__main__":
    a = sys.argv[1:]; p = SF.project()
    if a[:1] == ["stills"]:
        ts = [float(x) for x in a[1:]]; S_, sfx = plan(p, 0, max(ts) + 2); r = E.Renderer(p, S_, 0, p.dur, OUT, sfx, C["bg"]); print(r.stills(ts, OUT.replace(".mp4", "_sheet.png"), cols=4))
    else:
        t0, t1 = (float(a[0]), float(a[1])) if len(a) >= 2 else (0.0, p.dur)
        S_, sfx = plan(p, t0, t1); E.Renderer(p, S_, t0, t1, OUT if (t0, t1) == (0.0, p.dur) else OUT.replace(".mp4", f"_{int(t0)}-{int(t1)}.mp4"), sfx, C["bg"]).render()
