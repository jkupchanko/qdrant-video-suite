"""SKETCH: Andrej Karpathy's look ("Deep Dive into LLMs like ChatGPT", 10M views; "Intro to Large Language
Models", 4.2M), copied from the frame audit.

What the audit shows
  - the whole video is his screen: a browser window with an Excalidraw canvas, white, and web pages he
    pastes onto it or opens beside it; his face in a small rounded window bottom-left (about 14% wide)
  - the canvas holds one huge hand-drawn diagram: Excalifont text in near-black, blue text for
    sub-headings, sketchy rectangles with pastel fills (pink, blue, green, yellow), sketchy arrows
  - he pans and zooms the canvas as he talks; nothing cuts (0 hard cuts, 3 changes a minute)
  - web pages appear as pasted screenshots with a thin border and he scrolls them
Here: a 2x world canvas is drawn in full, the view eases between keyframes per line, docs pages are
pasted from the B-roll shots, and the face window is hidden during the look-away (the code rule).
Font: Excalifont (Excalidraw's own, OFL).
"""
import os, math, random
from PIL import Image, ImageDraw
import engine as E
from engine import W, H, k, ease, inout, rgba
from beats import cues
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\sketch_0-41.mp4"; BG = (236, 238, 242)
INK = (30, 30, 30); BLUE = (25, 113, 194); RED = (224, 49, 49); PINK = (255, 201, 201); LBLUE = (165, 216, 255); GREEN = (178, 242, 187); YELLOW = (255, 236, 153); GREY = (120, 120, 128)
CW, CH = 3840, 2160                           # the world canvas
BROLL = r"C:\Users\ADMIN\camera_audit\full\broll"; EDIT_BR = r"C:\Users\ADMIN\camera_audit\edit\broll"
FACE = ("inset", (24, H - 24 - 200, 270, 200), 14)

def wob(x, y, i=0): return (x + 2.2 * math.sin(0.11 * y + i), y + 2.2 * math.cos(0.09 * x + i))
def srect(d, x0, y0, x1, y1, prog, fill=None, color=INK):
    """a sketchy rectangle: two slightly different passes, drawn on"""
    if prog <= 0: return
    if fill and prog > 0.5: d.rectangle([x0 + 3, y0 + 3, x1 - 3, y1 - 3], fill=rgba(fill, 255 * min(1, (prog - 0.5) * 3)))
    for p in (0, 1):
        pts = [wob(x0, y0, p), wob(x1, y0, p + 2), wob(x1, y1, p + 4), wob(x0, y1, p + 6), wob(x0, y0, p)]; L = 2 * (x1 - x0 + y1 - y0); todo = L * ease(prog)
        for a, b in zip(pts, pts[1:]):
            seg = math.hypot(b[0] - a[0], b[1] - a[1])
            if todo <= 0: break
            f = min(1, todo / seg); d.line([a, (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)], fill=rgba(color), width=3); todo -= seg
def sarrow(d, a, b, prog, color=INK):
    if prog <= 0: return
    e = ease(prog); x, y = a[0] + (b[0] - a[0]) * e, a[1] + (b[1] - a[1]) * e
    mid = ((a[0] + x) / 2 + 6, (a[1] + y) / 2 - 6); d.line([a, mid, (x, y)], fill=rgba(color), width=3, joint="curve")
    if prog >= 0.95:
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for s_ in (-0.5, 0.5): d.line([b, (b[0] - 18 * math.cos(ang + s_), b[1] - 18 * math.sin(ang + s_))], fill=rgba(color), width=3)
def stext(d, x, y, text, prog, size=40, color=INK):
    if prog <= 0: return
    f = E.font("Excalifont-Regular.ttf", size); n = int(len(text) * min(1, prog) + 0.999); d.text((x, y), text[:n], font=f, fill=rgba(color))
def paste_page(canvas, frame, x, y, w, prog):
    if prog <= 0: return
    im = E.cover(frame, w, int(w * 9 / 16)); im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog)))); canvas.alpha_composite(im, (x, y)); ImageDraw.Draw(canvas).rectangle([x, y, x + w, y + im.height], outline=rgba(GREY), width=2)
def chrome(fr):
    """a browser window around the canvas: tab strip and address bar"""
    d = ImageDraw.Draw(fr); d.rectangle([0, 0, W, 92], fill=(222, 225, 230, 255)); d.rounded_rectangle([130, 10, 420, 46], radius=10, fill=(245, 246, 248, 255)); d.text((150, 18), "Excalidraw", font=E.font("Inter[opsz,wght].ttf", 20, 500), fill=(60, 60, 70))
    d.rounded_rectangle([430, 10, 700, 46], radius=10, fill=(205, 208, 214, 255)); d.text((450, 18), "Bulk Upload Vectors to Qdrant", font=E.font("Inter[opsz,wght].ttf", 20, 500), fill=(60, 60, 70))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]): d.ellipse([20 + 26 * i, 18, 38 + 26 * i, 36], fill=c + (255,))
    d.rounded_rectangle([130, 54, W - 130, 86], radius=14, fill=(245, 246, 248, 255)); d.text((160, 61), "excalidraw.com", font=E.font("Inter[opsz,wght].ttf", 20, 400), fill=(90, 90, 100))
    d.rectangle([0, 92, W, H], fill=(255, 255, 255, 255)); return fr

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []
    vt = E.clip(os.path.join(EDIT_BR, "vector_type_shot.mp4")); s1 = E.clip(os.path.join(BROLL, "s1_shot.mp4"))
    def world(T):
        """the whole diagram at edit time T, on the 2x canvas"""
        cv = Image.new("RGBA", (CW, CH), (255, 255, 255, 255)); d = ImageDraw.Draw(cv)
        # region A (top left): title, the flow into Qdrant, the "not just" line
        stext(d, 200, 160, "BULK UPLOADS", k(T, 0.2, 0.8), 72); stext(d, 200, 250, "step 1: a LOT of data goes in", k(T, c["large"], 1.0), 40, BLUE)
        for i in range(5): srect(d, 220 + i * 30, 340 + i * 12, 360 + i * 30, 440 + i * 12, k(T, c["large"] + 0.1 * i, 0.5), YELLOW)
        sarrow(d, (560, 400), (760, 400), k(T, c["large"] + 0.6, 0.5)); srect(d, 780, 330, 1080, 470, k(T, c["large"] + 0.8, 0.6), PINK); stext(d, 830, 375, "Qdrant", k(T, c["large"] + 1.1, 0.5), 48)
        stext(d, 200, 520, "not just storing vectors!", k(T, c["just"], 0.8), 40); d.line([(200, 540), (200 + 520 * k(T, c["store"] + 0.5, 0.4), 536)], fill=rgba(RED), width=4) if k(T, c["store"] + 0.5, 0.4) > 0 else None
        # region B (under A): what happens on upload
        stext(d, 440, 640, "what happens on upload:", k(T, c["list_t0"], 0.8), 40, BLUE)
        for i, (name, at, fill) in enumerate([("vectors", c["list_t0"] + 0.4, LBLUE), ("payloads", c["payloads"], GREEN), ("indexes (HNSW + payload)", c["indexes"], YELLOW), ("+ optimizer, segments, WAL ...", c["much"], PINK)]):
            y = 710 + i * 90; srect(d, 460, y, 500, y + 40, k(T, at, 0.4), fill); stext(d, 530, y - 4, name, k(T, at + 0.1, 0.6), 38)
        # region C (right of A): one config?
        stext(d, 1400, 160, "one config for all?", k(T, c["single"] - 0.2, 0.8), 44); srect(d, 1400, 240, 1900, 330, k(T, c["single"], 0.6), LBLUE); stext(d, 1440, 262, "config.yaml", k(T, c["single"] + 0.3, 0.5), 36)
        for i, (name, at) in enumerate([("RAG app", c["works"]), ("100M points", c["works"] + 0.3), ("multi-tenant", c["works"] + 0.6)]):
            x = 1300 + i * 330; sarrow(d, (1650, 340), (x + 120, 450), k(T, at, 0.4)); srect(d, x, 460, x + 260, 540, k(T, at + 0.2, 0.5), GREEN); stext(d, x + 20, 480, name, k(T, at + 0.3, 0.5), 32)
        px = k(T, c["all"], 0.4)
        if px > 0: d.line([(1380, 230), (1380 + 540 * px, 230 + 110 * px)], fill=rgba(RED), width=8); d.line([(1920, 230), (1920 - 540 * px, 230 + 110 * px)], fill=rgba(RED), width=8)
        # region D (under C): the plan
        stext(d, 1400, 620, "the plan:", k(T, c["plan_t0"] + 0.3, 0.6), 44, BLUE)
        for i, name in enumerate(["dense on disk", "payload indexes first", "quantization", "sparse index on disk"]): stext(d, 1440, 690 + i * 60, f"{i + 1}. {name}", k(T, c["options"] + 0.15 * i, 0.5), 34)
        for i, name in enumerate(["batch", "parallel workers", "shards"]): stext(d, 1440, 960 + i * 60, f"best practice {i + 1}: {name}", k(T, c["best"] + 0.15 * i, 0.5), 34, GREY)
        # region E (right half, upper): dense vs sparse with their indexes
        stext(d, 2200, 160, "two kinds of vectors", k(T, c["ds_t0"] + 0.3, 0.8), 48, BLUE)
        srect(d, 2200, 240, 2900, 420, k(T, c["dense"], 0.6), LBLUE); stext(d, 2230, 260, "dense", k(T, c["dense"] + 0.2, 0.5), 40); stext(d, 2230, 330, "[0.12, -0.87, 0.33, 0.91, ...]", k(T, c["dense"] + 0.4, 0.6), 32)
        srect(d, 2960, 240, 3660, 420, k(T, c["sparse"], 0.6), YELLOW); stext(d, 2990, 260, "sparse", k(T, c["sparse"] + 0.2, 0.5), 40); stext(d, 2990, 330, "{12: 0.9, 77: 0.6, 301: 0.8}", k(T, c["sparse"] + 0.4, 0.6), 32)
        pg = k(T, c["hnsw"], 1.0)
        if pg > 0:
            pts = [(2300, 520), (2420, 480), (2560, 540), (2700, 500), (2820, 580), (2480, 640), (2640, 660)]; ed = [(0, 1), (1, 2), (2, 3), (3, 4), (1, 5), (5, 6), (6, 2), (3, 6)]
            for j, (a, b) in enumerate(ed):
                pr = min(1, pg * 8 - j)
                if pr > 0: e = ease(pr); d.line([pts[a], (pts[a][0] + (pts[b][0] - pts[a][0]) * e, pts[a][1] + (pts[b][1] - pts[a][1]) * e)], fill=rgba(INK), width=3)
            for x, y in pts: d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=rgba(BLUE))
            stext(d, 2300, 700, "HNSW graph (in RAM)", k(T, c["hnsw"] + 0.6, 0.6), 34, BLUE)
        pi = k(T, c["indexing"], 1.0)
        if pi > 0:
            for j in range(4): d.line([(3000, 500 + j * 46), (3000 + 600 * min(1, pi * 4 - j), 500 + j * 46)], fill=rgba(INK), width=3)
            d.line([(3180, 500), (3180, 638)], fill=rgba(INK), width=3)
            for j, (a, b) in enumerate([("term 12", "doc 4, 9, 31"), ("term 77", "doc 4, 12"), ("term 301", "doc 9, 18, 77")]): stext(d, 3010, 504 + j * 46, a, min(1, pi * 3 - j), 28); stext(d, 3200, 504 + j * 46, b, min(1, pi * 3 - j), 28)
            stext(d, 3000, 700, "sparse (inverted) index", k(T, c["indexing"] + 0.6, 0.6), 34, BLUE)
        # region F (right half, lower): the docs page pasted, memory / performance
        paste_page(cv, vt.frame(max(0, T - c["mp_t0"])), 2200, 820, 900, k(T, c["mp_t0"] + 0.2, 0.6))
        stext(d, 3160, 860, "memory", k(T, c["memory"], 0.5), 40); sarrow(d, (3160, 900), (3160, 960), k(T, c["memory"] + 0.3, 0.3), RED); stext(d, 3200, 915, "up", k(T, c["memory"] + 0.4, 0.3), 32, RED)
        stext(d, 3160, 1010, "performance", k(T, c["perf"], 0.5), 40); sarrow(d, (3160, 1050), (3160, 1110), k(T, c["perf"] + 0.3, 0.3), RED); stext(d, 3200, 1065, "depends", k(T, c["perf"] + 0.4, 0.3), 32, RED)
        stext(d, 3160, 1180, "during bulk uploads!", k(T, c["bulk"], 0.6), 36, BLUE)
        # region G (bottom): option 1
        stext(d, 200, 1380, "Option 1: dense vectors on disk", k(T, c["ch_face_end"], 0.9), 56)
        srect(d, 200, 1500, 560, 1700, k(T, c["storing"] - 0.3, 0.5), PINK); stext(d, 240, 1520, "RAM", k(T, c["storing"] - 0.1, 0.4), 40); sarrow(d, (580, 1600), (820, 1600), k(T, c["storing"] + 0.2, 0.4))
        srect(d, 840, 1500, 1200, 1700, k(T, c["storing"] + 0.4, 0.5), LBLUE); stext(d, 880, 1520, "disk", k(T, c["storing"] + 0.6, 0.4), 40)
        for i in range(12):
            pr = inout((T - c["storing"] - 0.3 - 0.05 * i) / 0.8); x = 240 + (i % 4) * 70 + (640 if pr > 0 else 0) * pr; y = 1580 + (i // 4) * 36
            d.rectangle([x, y, x + 40, y + 24], fill=rgba(BLUE if pr < 1 else LBLUE), outline=rgba(INK))
        srect(d, 1260, 1540, 1700, 1640, k(T, c["disk"], 0.5), YELLOW); stext(d, 1290, 1565, "on_disk = True", k(T, c["disk"] + 0.2, 0.5), 36)
        paste_page(cv, s1.frame(max(0, T - c["o1_t0"])), 1760, 1300, 760, k(T, c["o1_t0"] + 0.3, 0.6))
        return cv
    # the view: (centre x, centre y, zoom) keyframes in world units; eased between them
    KEYS = [(0.0, (900, 520, 0.95)), (c["cfg_t0"], (1650, 420, 0.95)), (c["plan_t0"], (1650, 820, 0.95)), (c["ds_t0"], (2930, 480, 0.85)), (c["mp_t0"], (2800, 1000, 0.85)), (c["ch_face_end"], (900, 1540, 0.95)), (c["o1_t0"] + 1.5, (1250, 1540, 0.85))]
    def view(T):
        cur = KEYS[0][1]; prev_t = KEYS[0][0]
        for kt, kv in KEYS[1:]:
            if T >= kt - 0.8:
                e = inout((T - (kt - 0.8)) / 1.2); cur = tuple(a + (b - a) * e for a, b in zip(cur, kv))
        return cur
    def g_main(t, dur, ctx):
        T = t0 + t; cv = world(T); cx, cy, z = view(T); vw, vh = W / z, (H - 92) / z
        x0, y0 = int(min(max(0, cx - vw / 2), CW - vw)), int(min(max(0, cy - vh / 2), CH - vh)); crop = cv.crop((x0, y0, int(x0 + vw), int(y0 + vh))).resize((W, H - 92), Image.BILINEAR)
        fr = chrome(E.blank(BG)); fr.alpha_composite(crop, (0, 92))
        if not ctx["project"].looking_away(T): E.place_face(fr, ctx["face"], FACE, ((60, 60, 70), 2))
        return fr
    S.append(dict(t0=t0, t1=t1, kind="graphic", draw=g_main, tr="cut", face=None, shows_face=False))
    for key in ("large", "just", "payloads", "indexes", "much", "single", "works", "all", "options", "best", "dense", "sparse", "hnsw", "indexing", "memory", "perf", "bulk", "storing", "disk"): sfx.append((c[key], E.click(0.02)))
    return S, sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
