"""FLOWCHART: StatQuest's look ("A Gentle Introduction to Machine Learning", 1.7M views; his neural network
series, 1.4M), copied from the frame audit.

What the audit shows
  - pure white; a plain sans (Helvetica-like) in black, bold for the emphasised words
  - decision trees: blue rounded boxes with white text, black arrows between them with "Yes" / "No" beside
    the arrow, green boxes for the good outcome, red for the bad; branches not in play fade to pale
  - a sentence beside the diagram explains what was just drawn
  - charts drawn with thick blue axes, red dots, a dotted black fit line, green dashed arrows and a red X
  - a big "BAM!!!" (or "Double BAM!!!") when the point lands
  - everything appears in place, no motion: 0.8 hard cuts and 1.8 changes a minute
Fonts: Inter (the closest open sans), 400 and 700.
"""
import os, math
from PIL import Image, ImageDraw
import engine as E
from engine import W, H, k, ease, rgba
from beats import cues
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\flowchart_0-41.mp4"; BG = (255, 255, 255)
BLUE = (30, 150, 240); BLUE_PALE = (190, 222, 250); GREEN = (90, 210, 60); GREEN_PALE = (205, 240, 195); RED = (235, 55, 55); RED_PALE = (250, 205, 205); INK = (20, 20, 20); GREY = (170, 170, 170); DOT = (60, 60, 60)
SANS = "Inter[opsz,wght].ttf"

def node(d, cx, cy, text, prog, color=BLUE, pale=None, w=None, dim=False):
    """a rounded box with white text, appearing in place (StatQuest does not animate them)"""
    if prog <= 0: return
    f = E.font(SANS, 30, 700); lines = text.split("\n"); tw = max(E.TD.textlength(l, font=f) for l in lines); w = w or int(tw + 50); h = 30 + 36 * len(lines)
    col = (pale or {BLUE: BLUE_PALE, GREEN: GREEN_PALE, RED: RED_PALE}.get(color, BLUE_PALE)) if dim else color
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=8, fill=rgba(col))
    for i, l in enumerate(lines): d.text((cx, cy - h / 2 + 15 + 18 + i * 36), l, font=f, fill=rgba((255, 255, 255) if not dim else (255, 255, 255)), anchor="mm")
def arrow(d, a, b, prog, label=None, side=-1, dim=False):
    if prog <= 0: return
    col = GREY if dim else INK; e = ease(prog); x, y = a[0] + (b[0] - a[0]) * e, a[1] + (b[1] - a[1]) * e; d.line([a, (x, y)], fill=rgba(col), width=5)
    if prog >= 0.95:
        ang = math.atan2(b[1] - a[1], b[0] - a[0]); d.polygon([b, (b[0] - 22 * math.cos(ang - 0.45), b[1] - 22 * math.sin(ang - 0.45)), (b[0] - 22 * math.cos(ang + 0.45), b[1] - 22 * math.sin(ang + 0.45))], fill=rgba(col))
    if label and prog > 0.5: d.text(((a[0] + b[0]) / 2 + side * 40, (a[1] + b[1]) / 2 - 10), label, font=E.font(SANS, 26, 400), fill=rgba(col), anchor="mm")
def sentence(d, x, y, parts, prog, size=30, width=560, align="l"):
    """wrapped sentence with bold spans: parts = [(text, bold)]"""
    if prog <= 0: return
    words = []
    for t, b in parts:
        for w_ in t.split(" "):
            if w_: words.append((w_, b))
    f_r, f_b = E.font(SANS, size, 400), E.font(SANS, size, 700); lines = [[]]; cur = 0
    for w_, b in words:
        ww = E.TD.textlength(w_ + " ", font=f_b if b else f_r)
        if cur + ww > width and lines[-1]: lines.append([]); cur = 0
        lines[-1].append((w_, b, ww)); cur += ww
    for i, ln in enumerate(lines):
        tw = sum(ww for _, _, ww in ln); xx = x - tw / 2 if align == "c" else x
        for w_, b, ww in ln: d.text((xx, y + i * int(size * 1.4)), w_, font=f_b if b else f_r, fill=rgba(INK)); xx += ww
def bam(fr, text, cx, cy, prog):
    if prog <= 0: return
    f = E.font(SANS, 110, 700); im = E.text_image(text, f, INK, pad=10); s = 0.6 + 0.4 * min(1, prog * 3); im = im.resize((int(im.width * s), int(im.height * s)), Image.BILINEAR); E.paste_center(fr, im, cx, cy)
def axes(d, x0, y0, w, h, xl, yl, prog):
    if prog <= 0: return
    d.line([(x0, y0), (x0, y0 - h * ease(prog))], fill=rgba(BLUE), width=7); d.line([(x0, y0), (x0 + w * ease(prog), y0)], fill=rgba(BLUE), width=7)
    for i in range(1, 4): d.line([(x0 - 12, y0 - h * i / 4), (x0 + 12, y0 - h * i / 4)], fill=rgba(BLUE), width=5); d.line([(x0 + w * i / 4, y0 - 12), (x0 + w * i / 4, y0 + 12)], fill=rgba(BLUE), width=5)
    if prog > 0.8: d.text((x0 + w / 2, y0 + 44), xl, font=E.font(SANS, 26, 400), fill=rgba(INK), anchor="mm"); d.text((x0 - 24, y0 - h / 2), yl, font=E.font(SANS, 26, 400), fill=rgba(INK), anchor="rm")

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []
    def face(a, b): S.append(dict(t0=a, t1=b, kind="face", tr="cut"))
    def g(a, b, draw): S.append(dict(t0=a, t1=b, kind="graphic", draw=draw, tr="cut", face=None))
    # 0 title, then the first node and the "just storing?" branch
    face(c["hook_t0"], c["large"])
    def g_tree1(t, dur, ctx):
        fr = E.blank(BG); d = ImageDraw.Draw(fr); T = c["large"] + t
        d.text((W / 2, 140), "A Gentle Introduction\nto\nBulk Uploads", font=E.font(SANS, 54, 700), fill=rgba(INK), anchor="ma", align="center") if T < c["just"] - 0.3 else None
        if T >= c["just"] - 0.3:
            node(d, 960, 180, "A LOT of data", 1.0); arrow(d, (960, 215), (960, 300), k(T, c["just"] - 0.1, 0.4), "into Qdrant", 1)
            node(d, 960, 340, "Just store\nvectors?", k(T, c["just"], 0.3)); sentence(d, 1200, 320, [("Qdrant ", False), ("doesn't", True), (" just store vectors...", False)], k(T, c["store"], 0.3), 30, 520)
        return fr
    g(c["large"], c["list_t0"], g_tree1); sfx.append((c["just"], E.click(0.04)))
    # 1 the tree grows one node per word; the sentence beside it updates
    def g_tree2(t, dur, ctx):
        fr = E.blank(BG); d = ImageDraw.Draw(fr); T = c["list_t0"] + t
        node(d, 960, 120, "A LOT of data", 1.0); arrow(d, (960, 155), (960, 230), 1.0, "into Qdrant", 1); node(d, 960, 270, "Just store\nvectors?", 1.0)
        arrow(d, (900, 325), (640, 420), 1.0, "No", -1); items = [("vectors", c["list_t0"] + 0.2), ("payloads", c["payloads"]), ("indexes", c["indexes"]), ("+ more", c["much"])]
        for i, (nm, at) in enumerate(items):
            x = 400 + i * 300; pr = k(T, at, 0.3)
            if pr > 0:
                node(d, x, 480, nm, 1.0, GREEN if i < 3 else BLUE)
                if i > 0: arrow(d, (x - 160, 480), (x - 80, 480), 1.0)
        sentence(d, 960, 620, [("If you upload points, Qdrant stores the ", False), ("vectors", True), (", stores and indexes the ", False), ("payloads", True), (", builds the ", False), ("indexes", True), (" and ", False), ("much more", True), (" in the background.", False)], k(T, c["background"], 0.3), 30, 900, "c")
        return fr
    g(c["list_t0"], c["cfg_t0"], g_tree2)
    for _, at in [("payloads", c["payloads"]), ("indexes", c["indexes"]), ("much", c["much"])]: sfx.append((at, E.click(0.04)))
    # 2 one config? a tree with three workloads under it, the config box goes red, sentence
    def g_cfg(t, dur, ctx):
        fr = E.blank(BG); d = ImageDraw.Draw(fr); T = c["cfg_t0"] + t; pr0 = k(T, c["single"] - 0.2, 0.3)
        node(d, 960, 160, "One configuration?", pr0, BLUE if T < c["all"] else RED)
        for i, (nm, at) in enumerate([("RAG app", c["works"]), ("100M points", c["works"] + 0.25), ("multi-tenant", c["works"] + 0.5)]):
            x = 560 + i * 400; pr = k(T, at, 0.3)
            if pr > 0: arrow(d, (960, 195), (x, 330), 1.0, ["Yes", "Yes", "Yes"][i] if T < c["all"] else "No", (-1, 1, 1)[i]); node(d, x, 380, nm, 1.0, GREEN if T < c["all"] else BLUE, dim=T >= c["all"] and False)
        if T >= c["all"]: node(d, 960, 560, ":(", 1.0, RED, w=140)
        sentence(d, 960, 680, [("There's ", False), ("no single configuration", True), (" that works for every workload. What's right depends on what you optimise for.", False)], k(T, c["all"], 0.3), 30, 900, "c")
        return fr
    g(c["cfg_t0"], c["plan_t0"], g_cfg); sfx.append((c["all"], E.click(0.05)))
    # 3 the plan: the presenter
    face(c["plan_t0"], c["ds_t0"])
    # 4-6 dense vs sparse: the tree splits, each branch gets its index node on the cue word; the other dims
    def g_ds(t, dur, ctx):
        fr = E.blank(BG); d = ImageDraw.Draw(fr); T = c["ds_t0"] + t; node(d, 960, 120, "What kind of vector?", k(t, 0.3, 0.3))
        pd, ps = k(T, c["dense"], 0.3), k(T, c["sparse"], 0.3); dim_d = T >= c["indexing"]; dim_s = c["hnsw"] <= T < c["indexing"] - 0.2
        if pd > 0: arrow(d, (900, 155), (620, 280), 1.0, "Dense", -1, dim=dim_d); node(d, 560, 330, "Dense vector", 1.0, BLUE, dim=dim_d)
        if ps > 0: arrow(d, (1020, 155), (1300, 280), 1.0, "Sparse", 1, dim=dim_s); node(d, 1360, 330, "Sparse vector", 1.0, BLUE, dim=dim_s)
        ph = k(T, c["hnsw"], 0.3)
        if ph > 0: arrow(d, (560, 365), (560, 480), 1.0, dim=dim_d); node(d, 560, 530, "HNSW index", 1.0, GREEN, dim=dim_d)
        pi = k(T, c["indexing"], 0.3)
        if pi > 0: arrow(d, (1360, 365), (1360, 480), 1.0); node(d, 1360, 530, "Sparse index", 1.0, GREEN)
        sentence(d, 960, 700, [("Dense vectors are indexed with ", False), ("HNSW", True), ("; sparse vectors use a ", False), ("completely different", True), (" index.", False)], k(T, c["indexing"] + 0.4, 0.3), 30, 900, "c")
        return fr
    g(c["ds_t0"], c["mp_t0"], g_ds); sfx += [(c["hnsw"], E.click(0.04)), (c["indexing"], E.click(0.04))]
    # 7 memory and performance: the chart with dots and the fit line, red X on the axes
    def g_chart(t, dur, ctx):
        fr = E.blank(BG); d = ImageDraw.Draw(fr); T = c["mp_t0"] + t; x0, y0, w, h = 420, 820, 760, 560; axes(d, x0, y0, w, h, "Points uploaded", "Memory", k(t, 0.2, 0.6))
        pts = [(0.15, 0.2), (0.3, 0.32), (0.45, 0.5), (0.6, 0.58), (0.75, 0.78), (0.9, 0.88)]
        for i, (u, v) in enumerate(pts):
            if k(T, c["memory"] + 0.1 * i, 0.2) > 0: d.ellipse([x0 + w * u - 12, y0 - h * v - 12, x0 + w * u + 12, y0 - h * v + 12], fill=rgba(RED))
        pl = k(T, c["memory"] + 0.8, 0.6)
        if pl > 0:
            for s_ in range(int(60 * pl)): u = 0.08 + s_ / 60 * 0.85; d.ellipse([x0 + w * u - 3, y0 - h * (u * 1.0) - 3, x0 + w * u + 3, y0 - h * (u * 1.0) + 3], fill=rgba(DOT))
        pp = k(T, c["perf"], 0.4)
        if pp > 0:
            for s_ in range(int(14 * pp)): u = 0.62; d.line([(x0 + w * u, y0 - 20 - s_ * 30), (x0 + w * u, y0 - 36 - s_ * 30)], fill=rgba(GREEN), width=5)
            d.text((x0 + w * 0.62, y0 + 6), "X", font=E.font(SANS, 44, 700), fill=rgba(RED), anchor="mm"); d.text((x0 - 6, y0 - h * 0.62), "X", font=E.font(SANS, 44, 700), fill=rgba(RED), anchor="mm")
        sentence(d, 1260, 320, [("During a ", False), ("bulk upload", True), (", memory grows with every point, and search ", False), ("performance", True), (" depends on how you set things up.", False)], k(T, c["bulk"], 0.3), 30, 560)
        return fr
    g(c["mp_t0"], c["ch_t0"], g_chart); sfx += [(c["memory"], E.click(0.04)), (c["perf"], E.click(0.04))]
    # 8 chapter: presenter, then BAM
    face(c["ch_t0"], c["ch_face_end"])
    def g_bam(t, dur, ctx):
        fr = E.blank(BG); d = ImageDraw.Draw(fr); bam(fr, "Option 1!!!", W / 2, 420, k(t, 0.1, 0.3)); sentence(d, 960, 560, [("Store the ", False), ("original dense vectors on disk", True), (".", False)], k(t, 0.7, 0.3), 34, 900, "c"); return fr
    g(c["ch_face_end"], c["o1_t0"] + 0.3, g_bam); sfx.append((c["ch_face_end"] + 0.1, E.pop(0.1)))
    # 9 option 1: a small tree: RAM -> disk, green box on "disk"
    def g_disk(t, dur, ctx):
        fr = E.blank(BG); d = ImageDraw.Draw(fr); T = c["o1_t0"] + 0.3 + t; node(d, 560, 400, "Original vectors\nin RAM", 1.0, RED); arrow(d, (700, 400), (1180, 400), k(T, c["storing"], 0.5), "on_disk = True", -1)
        node(d, 1360, 400, "Original vectors\non disk", k(T, c["disk"], 0.3), GREEN); sentence(d, 960, 600, [("Option 1: put the ", False), ("original vectors on disk", True), (" and keep only what search needs in memory.", False)], k(T, c["disk"] + 0.3, 0.3), 30, 900, "c")
        return fr
    g(c["o1_t0"] + 0.3, t1, g_disk); sfx.append((c["disk"], E.click(0.05)))
    return S, sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
