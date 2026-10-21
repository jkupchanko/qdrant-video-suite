"""EDITORIAL: Vox's look ("Why AI art struggles with hands", 2.8M views), copied from the frame audit.

What the audit shows
  - two worlds: a dark navy panel (#18192 2) holding a cream search box with a magnifier, where a prompt
    types itself with a blinking cursor; and cream paper (#F8F7F3) where images sit as cards with a white
    matte and a pixel-dotted border, scattered and tilted a little, sliding in one after another
  - captions in a plain sans: a word in bold, a line under it in regular
  - a grey robot with a magenta-to-blue glow behind it as the AI; the Vox mark top right
  - the presenter at a desk in a warm room, full frame; interviewees in their own rooms
  - 19 hard cuts and 30 changes a minute: a new card or a cut about every two seconds
Fonts: Inter 600 and 400; Fira Code for the prompt.
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import engine as E
from engine import W, H, k, ease, inout, rgba
from beats import cues
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\editorial_0-41.mp4"; BG = (24, 25, 34)
NAVY = (24, 25, 34); CREAM = (248, 247, 243); INK = (28, 28, 32); GREY = (120, 120, 126); BOX = (252, 251, 247); MAG = (190, 40, 120); BLUEG = (40, 90, 200); RED = (200, 40, 40)
MEMES = r"C:\Users\ADMIN\camera_audit\style\memes"; BROLL = r"C:\Users\ADMIN\camera_audit\full\broll"; EDIT_BR = r"C:\Users\ADMIN\camera_audit\edit\broll"; MARK = r"C:\Users\ADMIN\camera_audit\assets\qdrant-brandmark-red.png"

def paper():
    key = "ed_paper"
    if key not in E._fc:
        rng = np.random.default_rng(5); n = rng.normal(0, 2.5, (H, W, 1)); a = np.array(CREAM, np.float32)[None, None, :] + n; E._fc[key] = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    fr = E._fc[key].copy(); mk = E.fit(Image.open(MARK).convert("RGBA"), 44, 44); fr.alpha_composite(mk, (W - 90, 36)); return fr
def navy():
    fr = E.blank(NAVY); mk = E.fit(Image.open(MARK).convert("RGBA"), 44, 44); fr.alpha_composite(mk, (W - 90, 36)); return fr
def search_box(fr, text, t, cx=960, cy=330, w=1000):
    """the cream search box with a magnifier and a typed prompt; the cursor blinks"""
    d = ImageDraw.Draw(fr); x0, y0 = cx - w / 2, cy - 60; d.rectangle([x0, y0, x0 + w, y0 + 120], fill=rgba(BOX)); d.rectangle([x0 - 10, y0 + 10, x0, y0 + 110], fill=rgba(BOX)); d.rectangle([x0 + w, y0 + 10, x0 + w + 10, y0 + 110], fill=rgba(BOX))
    d.ellipse([x0 + 40, cy - 22, x0 + 72, cy + 10], outline=rgba(BLUEG), width=5); d.line([(x0 + 68, cy + 6), (x0 + 86, cy + 24)], fill=rgba(BLUEG), width=6)
    f = E.font("FiraCode[wght].ttf", 30, 450); d.text((x0 + 110, cy), text, font=f, fill=rgba(INK), anchor="lm")
    if int(t * 2.5) % 2 == 0: cx2 = x0 + 110 + d.textlength(text, font=f) + 6; d.line([(cx2, cy - 22), (cx2, cy + 22)], fill=rgba(INK), width=3)
def dotted(d, x0, y0, x1, y1, color=(140, 150, 170), step=10):
    for x in range(int(x0), int(x1), step): d.rectangle([x, y0, x + 4, y0 + 4], fill=rgba(color)); d.rectangle([x, y1 - 4, x + 4, y1], fill=rgba(color))
    for y in range(int(y0), int(y1), step): d.rectangle([x0, y, x0 + 4, y + 4], fill=rgba(color)); d.rectangle([x1 - 4, y, x1, y + 4], fill=rgba(color))
def card(im, w, tilt=0.0, caption=None, sub=None):
    """an image on a white matte with the pixel-dotted border; optional caption lines under it"""
    im = E.cover(im, w, int(w * 0.68)); pad = 18; ch = (70 if caption else 0) + (34 if sub else 0); out = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2 + ch), (0, 0, 0, 0)); d = ImageDraw.Draw(out)
    d.rectangle([0, 0, out.width - 1, out.height - 1], fill=(255, 255, 255, 255)); out.alpha_composite(im, (pad, pad)); dotted(d, 4, 4, out.width - 4, out.height - 4)
    if caption: d.text((pad, im.height + pad + 14), caption, font=E.font("Inter[opsz,wght].ttf", 34, 600), fill=rgba(INK))
    if sub: d.text((pad, im.height + pad + 60), sub, font=E.font("Inter[opsz,wght].ttf", 24, 400), fill=rgba(GREY))
    out = E.shadowed(out, 14, (0, 8), 70)
    if tilt: out = out.rotate(tilt, resample=Image.BICUBIC, expand=True)
    return out
def text_card(lines, w=460, tilt=0.0):
    f = E.font("FiraCode[wght].ttf", 26, 450); h = 40 + 38 * len(lines); out = Image.new("RGBA", (w, h), (255, 255, 255, 255)); d = ImageDraw.Draw(out)
    for i, ln in enumerate(lines): d.text((24, 22 + i * 38), ln, font=f, fill=rgba(INK))
    dotted(d, 4, 4, w - 4, h - 4); out = E.shadowed(out, 14, (0, 8), 70)
    if tilt: out = out.rotate(tilt, resample=Image.BICUBIC, expand=True)
    return out
def slide(fr, im, x, y, prog, frm="right"):
    if prog <= 0: return
    e = ease(prog); dx = {"right": 300 * (1 - e), "left": -300 * (1 - e), "up": 0}[frm]; dy = 80 * (1 - e) if frm == "up" else 0
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda a: int(a * e))); fr.alpha_composite(im, (int(x + dx), int(y + dy)))
def caption(fr, bold, regular, x, y, prog):
    if prog <= 0: return
    b = E.text_image(bold, E.font("Inter[opsz,wght].ttf", 48, 600), INK, pad=4); r = E.text_image(regular, E.font("Inter[opsz,wght].ttf", 28, 400), GREY, pad=4)
    for im, dy in ((b, 0), (r, 60)): im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog)))); fr.alpha_composite(im, (int(x), int(y + dy + 10 * (1 - ease(prog)))))
def glow_mark(fr, cx, cy, size, t):
    g = Image.new("RGBA", (size * 3, size * 3), (0, 0, 0, 0)); d = ImageDraw.Draw(g); d.ellipse([size * 0.6, size * 0.6, size * 2.4, size * 2.4], fill=rgba(MAG, 160)); d.ellipse([size * 1.0, size * 0.9, size * 2.6, size * 2.5], fill=rgba(BLUEG, 160)); g = g.filter(ImageFilter.GaussianBlur(size * 0.25))
    E.paste_center(fr, g, cx + 10 * math.sin(t), cy); mk = E.fit(Image.open(MARK).convert("RGBA"), size, size); E.paste_center(fr, mk, cx, cy)

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []
    photos = {n: Image.open(os.path.join(MEMES, n)).convert("RGBA") for n in ("datacenter.jpg", "ram.jpg", "traffic.jpg", "lanes.jpg", "catalog.jpg")}
    vt = E.clip(os.path.join(EDIT_BR, "vector_type_shot.mp4")); s1 = E.clip(os.path.join(BROLL, "s1_shot.mp4")); s2 = E.clip(os.path.join(BROLL, "s2_shot.mp4")); s5 = E.clip(os.path.join(BROLL, "s5_shot.mp4"))
    def face(a, b): S.append(dict(t0=a, t1=b, kind="face", tr="cut"))
    def g(a, b, draw): S.append(dict(t0=a, t1=b, kind="graphic", draw=draw, tr="cut", face=None))
    def pops(*ts):
        for t in ts: sfx.append((t, E.paper(0.04)))
    # 0 hook: the prompt types on navy, then the cards of data scatter onto the paper
    face(c["hook_t0"], c["large"])
    def g_prompt(t, dur, ctx):
        fr = navy(); txt = "upload 1,000,000 points to Qdrant"[:int(t * 22)]; search_box(fr, txt, t); return fr
    g(c["large"], c["just"] - 0.1, g_prompt); sfx.append((c["large"], E.click(0.04)))
    cards0 = [(card(photos["datacenter.jpg"], 380, -4), 120, 140), (card(photos["catalog.jpg"], 340, 3), 540, 100), (card(photos["lanes.jpg"], 360, -2), 900, 160), (card(photos["ram.jpg"], 330, 5), 1290, 110), (card(photos["traffic.jpg"], 400, -3), 300, 560), (card(vt.frame(1.0), 420, 2), 760, 540), (card(s5.frame(1.0), 380, -5), 1240, 560)]
    def g_cards(t, dur, ctx):
        fr = paper(); T = c["just"] - 0.1 + t
        for i, (im, x, y) in enumerate(cards0): slide(fr, im, x, y, k(t, 0.08 * i, 0.4), "up")
        caption(fr, "Not just vectors.", "every point carries payloads, indexes and more", 1240, 920, k(T, c["just"] + 0.3, 0.5)); return fr
    g(c["just"] - 0.1, c["list_t0"], g_cards); pops(*[c["just"] - 0.1 + 0.08 * i for i in range(7)])
    # 1 three columns of cards: vectors (images), payloads (json), indexes (graph) on each word
    vec_cards = [card(photos["lanes.jpg"], 300, -3), card(photos["datacenter.jpg"], 300, 2)]; pay_cards = [text_card(['{"color": "red",', ' "price": 9.99,', ' "tags": ["sale"]}'], 420, 2), text_card(['{"city": "Berlin",', ' "stock": 12}'], 420, -3)]
    idx = Image.new("RGBA", (600, 400), (255, 255, 255, 255)); dd = ImageDraw.Draw(idx); rng = random.Random(2); pts = [(rng.randrange(60, 540), rng.randrange(60, 340)) for _ in range(14)]
    for i, a in enumerate(pts):
        for j in sorted(range(14), key=lambda j: (pts[j][0] - a[0]) ** 2 + (pts[j][1] - a[1]) ** 2)[1:3]: dd.line([a, pts[j]], fill=rgba(BLUEG), width=3)
    for x, y in pts: dd.ellipse([x - 7, y - 7, x + 7, y + 7], fill=rgba(INK))
    idx_card = card(idx, 360, 3); more_card = text_card(["optimizer", "segments", "WAL, snapshots ..."], 380, -2)
    def g_cols(t, dur, ctx):
        fr = paper(); T = c["list_t0"] + t
        for i, (title, at, ims) in enumerate([("vectors", c["list_t0"] + 0.3, vec_cards), ("payloads", c["payloads"], pay_cards), ("indexes", c["indexes"], [idx_card]), ("more", c["much"], [more_card])]):
            x = 100 + i * 450; pr = k(T, at, 0.5); caption(fr, title, "", x, 110, pr)
            for j, im in enumerate(ims): slide(fr, im, x, 220 + j * 300, k(T, at + 0.15 * j, 0.5), "up")
        caption(fr, "", "all of it, in the background", 100, 960, k(T, c["background"], 0.4)); return fr
    g(c["list_t0"], c["cfg_t0"], g_cols); pops(c["payloads"], c["indexes"], c["much"])
    # 2 one configuration? the prompt again, then "no results": three workload cards with a red line through the prompt
    def g_cfg(t, dur, ctx):
        fr = navy(); T = c["cfg_t0"] + t; txt = "one configuration for every workload"[:int(max(0, T - c["single"] + 0.3) * 24)]; search_box(fr, txt, t)
        for i, (nm, at) in enumerate([("RAG app", c["works"]), ("100M points", c["works"] + 0.3), ("multi-tenant", c["works"] + 0.6)]):
            pr = k(T, at, 0.4)
            if pr > 0: tc = text_card([nm], 360, (-3, 2, -2)[i]); slide(fr, tc, 400 + i * 420, 520, pr, "up")
        px = k(T, c["all"], 0.4)
        if px > 0: d = ImageDraw.Draw(fr); d.line([(460, 330), (460 + 1000 * px, 330)], fill=rgba(RED), width=8); caption(fr, "", "no single answer", 1200, 700, px) if False else None
        return fr
    g(c["cfg_t0"], c["plan_t0"], g_cfg); pops(c["works"], c["works"] + 0.3, c["works"] + 0.6); sfx.append((c["all"], E.click(0.05)))
    # 3 the plan: the presenter at the desk
    face(c["plan_t0"], c["ds_t0"])
    # 4-6 dense vs sparse: two big cards with grids, then the graph card and the index card
    def grid_img(dense):
        im = Image.new("RGBA", (600, 400), (255, 255, 255, 255)); d = ImageDraw.Draw(im); rng = random.Random(7)
        for r in range(8):
            for col in range(12):
                on = True if dense else rng.random() < 0.12; v = rng.random()
                d.rectangle([30 + col * 46, 30 + r * 44, 66 + col * 46, 66 + r * 44], fill=rgba((int(60 + 160 * v), int(90 + 100 * v), 220)) if on else (240, 240, 240, 255))
        return im
    dense_card = card(grid_img(True), 560, -2, "dense", "every dimension has a value"); sparse_card = card(grid_img(False), 560, 2, "sparse", "mostly zeros")
    tbl = text_card(["term 12  -> doc 4, 9, 31", "term 77  -> doc 4, 12", "term 301 -> doc 9, 18, 77"], 520, -2)
    def g_ds(t, dur, ctx):
        fr = paper(); T = c["ds_t0"] + t; caption(fr, "Two kinds of vectors", "", 100, 90, k(t, 0.3, 0.5))
        slide(fr, dense_card, 120, 200, k(T, c["dense"], 0.5), "left"); slide(fr, sparse_card, 760, 200, k(T, c["sparse"], 0.5), "right")
        slide(fr, idx_card, 1420, 180, k(T, c["hnsw"], 0.5), "up"); caption(fr, "", "HNSW graph", 1440, 560, k(T, c["hnsw"] + 0.4, 0.4))
        slide(fr, tbl, 1380, 640, k(T, c["indexing"], 0.5), "up"); caption(fr, "", "sparse index", 1400, 860, k(T, c["indexing"] + 0.4, 0.4)); return fr
    g(c["ds_t0"], c["mp_t0"], g_ds); pops(c["dense"], c["sparse"], c["hnsw"], c["indexing"])
    # 7 memory and performance: the docs page as a big card with two captions
    def g_mp(t, dur, ctx):
        fr = paper(); T = c["mp_t0"] + t; dc = card(vt.frame(t), 1100, 0, "Why vector type matters", "qdrant.tech / documentation"); slide(fr, dc, 80, 100, k(t, 0, 0.5), "up")
        caption(fr, "memory", "", 1340, 300, k(T, c["memory"], 0.4)); caption(fr, "performance", "", 1340, 420, k(T, c["perf"], 0.4)); caption(fr, "", "both change during bulk uploads", 1340, 560, k(T, c["bulk"], 0.4)); glow_mark(fr, 1560, 820, 120, t); return fr
    g(c["mp_t0"], c["ch_t0"], g_mp); pops(c["memory"], c["perf"], c["bulk"])
    # 8 chapter: presenter, then the prompt types the chapter
    face(c["ch_t0"], c["ch_face_end"])
    g(c["ch_face_end"], c["storing"] - 0.2, lambda t, dur, ctx: (lambda fr: (search_box(fr, "option 1: store dense vectors on disk"[:int(t * 26)], t), fr)[1])(navy())); sfx.append((c["ch_face_end"], E.click(0.04)))
    # 9 option 1: RAM card, arrow, disk card, the docs page card
    ram_card = card(photos["ram.jpg"], 420, -3, "RAM", "fast, limited"); disk = Image.new("RGBA", (600, 400), (255, 255, 255, 255)); dd = ImageDraw.Draw(disk); dd.ellipse([150, 60, 450, 140], fill=rgba((200, 210, 230)), outline=rgba(INK), width=4); dd.rectangle([150, 100, 450, 320], fill=rgba((200, 210, 230))); dd.line([(150, 100), (150, 320)], fill=rgba(INK), width=4); dd.line([(450, 100), (450, 320)], fill=rgba(INK), width=4); dd.arc([150, 280, 450, 360], 0, 180, fill=rgba(INK), width=4)
    disk_card = card(disk, 420, 3, "disk", "the original vectors live here")
    def g_disk(t, dur, ctx):
        fr = paper(); T = c["storing"] - 0.2 + t; slide(fr, ram_card, 120, 200, k(t, 0, 0.5), "left"); slide(fr, disk_card, 760, 200, k(T, c["storing"] + 0.3, 0.5), "right")
        pa = k(T, c["storing"] + 0.1, 0.4)
        if pa > 0: d = ImageDraw.Draw(fr); d.line([(600, 420), (600 + 140 * pa, 420)], fill=rgba(INK), width=6); d.polygon([(740, 420), (716, 404), (716, 436)], fill=rgba(INK)) if pa > 0.95 else None
        slide(fr, card(s1.frame(max(0, T - c["o1_t0"])), 480, 2, "Option 1", "Reduce memory pressure"), 1360, 160, k(T, c["o1_t0"] + 0.5, 0.5), "up"); caption(fr, "on_disk = True", "", 160, 760, k(T, c["disk"], 0.4)); return fr
    g(c["storing"] - 0.2, t1, g_disk); pops(c["storing"] + 0.3, c["disk"])
    return S, sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
