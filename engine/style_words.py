"""WORDS: the look of Basics Explained, H3Vtux ("Why Do Computers Use 1s and 0s?", 5.1M views), copied from
the frame audit.

What the audit shows
  - pure white; nothing but very large bold black words (a Calibri-like humanist sans) and the odd prop:
    a photo of apples, tally marks, a grid of digits, red arrows, a red circle around the thing to see
  - secondary words in a bright blue; a word slides a little as the next one arrives beside it
  - photos pasted in a loose pile with a white edge
  - 4.2 hard cuts and 25 changes a minute: the words change constantly, the layout barely does
Fonts: Nunito 800 (the closest open humanist bold).
"""
import os, math
from PIL import Image, ImageDraw
import engine as E
from engine import W, H, k, ease, inout, rgba
from beats import cues
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\words_0-41.mp4"; BG = (255, 255, 255)
INK = (16, 16, 16); BLUE = (30, 144, 255); RED = (225, 30, 30); MEMES = r"C:\Users\ADMIN\camera_audit\style\memes"; SANS = "Nunito[wght].ttf"

def word(fr, text, cx, cy, size, prog, color=INK, slide=(0, 0)):
    if prog <= 0: return
    im = E.text_image(text, E.font(SANS, size, 800), color, pad=8); e = ease(prog); im.putalpha(im.getchannel("A").point(lambda a: int(a * min(1, prog * 3)))); E.paste_center(fr, im, cx + slide[0] * (1 - e), cy + slide[1] * (1 - e))
def red_arrow(d, a, b, prog):
    if prog <= 0: return
    e = ease(prog); x, y = a[0] + (b[0] - a[0]) * e, a[1] + (b[1] - a[1]) * e; d.line([a, (x, y)], fill=rgba(RED), width=10)
    if prog > 0.9:
        ang = math.atan2(b[1] - a[1], b[0] - a[0]); d.polygon([b, (b[0] - 34 * math.cos(ang - 0.5), b[1] - 34 * math.sin(ang - 0.5)), (b[0] - 34 * math.cos(ang + 0.5), b[1] - 34 * math.sin(ang + 0.5))], fill=rgba(RED))
def red_circle(d, cx, cy, rx, ry, prog):
    if prog <= 0: return
    pts = [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a))) for a in range(-90, -90 + int(370 * min(1, prog)))]
    if len(pts) > 1: d.line(pts, fill=rgba(RED), width=7)
def photo(name, w, tilt=0):
    im = E.fit(Image.open(os.path.join(MEMES, name)).convert("RGBA"), w, int(w * 0.75)); out = Image.new("RGBA", (im.width + 20, im.height + 20), (255, 255, 255, 255)); ImageDraw.Draw(out).rectangle([0, 0, out.width - 1, out.height - 1], outline=(200, 200, 200, 255), width=2); out.alpha_composite(im, (10, 10)); out = E.shadowed(out, 12, (0, 6), 70)
    return out.rotate(tilt, resample=Image.BICUBIC, expand=True) if tilt else out
def grid(d, x0, y0, cols, rows, cell, prog, filled=None):
    for r in range(rows):
        for c_ in range(cols):
            i = r * cols + c_; pr = min(1, max(0, prog * cols * rows - i))
            if pr <= 0: continue
            d.rectangle([x0 + c_ * cell, y0 + r * cell, x0 + (c_ + 1) * cell, y0 + (r + 1) * cell], outline=rgba(INK), width=3, fill=rgba(BLUE) if (filled and filled(i)) else None)

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []
    def face(a, b): S.append(dict(t0=a, t1=b, kind="face", tr="cut"))
    def g(a, b, draw): S.append(dict(t0=a, t1=b, kind="graphic", draw=draw, tr="cut", face=None))
    def clicks(*ts):
        for t in ts: sfx.append((t, E.click(0.03)))
    dc = photo("datacenter.jpg", 520, -4); ramp = photo("ram.jpg", 460, 5); traffic = photo("traffic.jpg", 480, -3)
    # 0 hook: "A LOT of data" huge, a photo pile; then "Just store vectors?" with a red strike
    face(c["hook_t0"], c["large"])
    def g_hook(t, dur, ctx):
        fr = E.blank(BG); d = ImageDraw.Draw(fr); T = c["large"] + t
        word(fr, "A LOT", 640, 300, 190, k(t, 0, 0.3)); word(fr, "of data", 640, 480, 120, k(t, 0.3, 0.3), BLUE)
        for i, (im, x, y) in enumerate([(dc, 1180, 160), (traffic, 1300, 420), (ramp, 1120, 620)]):
            pr = k(t, 0.5 + 0.2 * i, 0.3)
            if pr > 0: im2 = im.copy(); im2.putalpha(im2.getchannel("A").point(lambda a: int(a * pr))); fr.alpha_composite(im2, (x, y))
        pj = k(T, c["just"], 0.3); word(fr, "just store vectors?", 640, 760, 80, pj)
        ps = k(T, c["store"] + 0.5, 0.3)
        if ps > 0: d.line([(240, 770), (240 + 800 * ease(ps), 760)], fill=rgba(RED), width=12)
        return fr
    g(c["large"], c["list_t0"], g_hook); clicks(c["large"], c["just"])
    # 1 the list: one big word after another, the earlier ones slide up and shrink
    items = [("Vectors", c["list_t0"] + 0.2), ("Payloads", c["payloads"]), ("Indexes", c["indexes"]), ("+ more", c["much"])]
    def g_list(t, dur, ctx):
        fr = E.blank(BG); T = c["list_t0"] + t; n = sum(1 for _, at in items if T >= at)
        for i, (nm, at) in enumerate(items):
            if T < at: continue
            pos = n - 1 - i; size = 150 if pos == 0 else 90; y = 540 if pos == 0 else 540 - 200 - (pos - 1) * 110
            word(fr, nm, 640, y, size, k(T, at, 0.3), INK if pos == 0 else BLUE, (0, 40))
        word(fr, "in the background", 1360, 540, 64, k(T, c["background"], 0.3), BLUE); return fr
    g(c["list_t0"], c["cfg_t0"], g_list); clicks(*[at for _, at in items])
    # 2 one config? the word, three words under it, a red circle and an arrow to "No"
    def g_cfg(t, dur, ctx):
        fr = E.blank(BG); d = ImageDraw.Draw(fr); T = c["cfg_t0"] + t; word(fr, "One config?", 960, 220, 150, k(T, c["single"] - 0.2, 0.3))
        for i, (nm, at) in enumerate([("RAG app", c["works"]), ("100M points", c["works"] + 0.25), ("multi-tenant", c["works"] + 0.5)]): word(fr, nm, 400 + i * 560, 520, 64, k(T, at, 0.3), BLUE, (0, 30))
        red_circle(d, 960, 220, 480, 110, k(T, c["all"] - 0.3, 0.5)); red_arrow(d, (960, 600), (960, 760), k(T, c["all"], 0.3)); word(fr, "No.", 960, 860, 120, k(T, c["all"] + 0.2, 0.3), RED); return fr
    g(c["cfg_t0"], c["plan_t0"], g_cfg); clicks(c["single"], c["works"], c["all"])
    # 3 the plan: presenter
    face(c["plan_t0"], c["ds_t0"])
    # 4-6 dense vs sparse: two grids of cells, filled vs mostly empty, their index words
    def g_ds(t, dur, ctx):
        fr = E.blank(BG); d = ImageDraw.Draw(fr); T = c["ds_t0"] + t; word(fr, "Dense", 500, 160, 110, k(T, c["dense"], 0.3)); word(fr, "Sparse", 1420, 160, 110, k(T, c["sparse"], 0.3), BLUE)
        grid(d, 260, 260, 8, 4, 60, k(T, c["dense"] + 0.1, 0.8), lambda i: True); grid(d, 1180, 260, 8, 4, 60, k(T, c["sparse"] + 0.1, 0.8), lambda i: i in (3, 13, 22, 29))
        word(fr, "HNSW", 500, 640, 100, k(T, c["hnsw"], 0.3)); word(fr, "graph index", 500, 740, 54, k(T, c["hnsw"] + 0.3, 0.3), BLUE)
        word(fr, "Sparse index", 1420, 640, 90, k(T, c["indexing"], 0.3)); word(fr, "a different structure", 1420, 740, 54, k(T, c["indexing"] + 0.3, 0.3), BLUE)
        red_arrow(d, (840, 900), (1080, 900), k(T, c["indexing"] + 0.8, 0.3)); word(fr, "different", 960, 980, 64, k(T, c["indexing"] + 1.0, 0.3), RED); return fr
    g(c["ds_t0"], c["mp_t0"], g_ds); clicks(c["dense"], c["sparse"], c["hnsw"], c["indexing"])
    # 7 memory and performance
    def g_mp(t, dur, ctx):
        fr = E.blank(BG); d = ImageDraw.Draw(fr); T = c["mp_t0"] + t; word(fr, "Memory", 520, 360, 130, k(T, c["memory"], 0.3)); word(fr, "Performance", 1360, 360, 110, k(T, c["perf"], 0.3), BLUE)
        pr = k(T, c["memory"] + 0.4, 0.5)
        if pr > 0: ramp2 = ramp.copy(); ramp2.putalpha(ramp2.getchannel("A").point(lambda a: int(a * pr))); fr.alpha_composite(ramp2, (300, 460))
        red_arrow(d, (1360, 460), (1360, 700), k(T, c["perf"] + 0.4, 0.3)); word(fr, "?", 1360, 800, 150, k(T, c["perf"] + 0.7, 0.3), RED)
        word(fr, "during bulk uploads", 960, 980, 64, k(T, c["bulk"], 0.3), BLUE); return fr
    g(c["mp_t0"], c["ch_t0"], g_mp); clicks(c["memory"], c["perf"], c["bulk"])
    # 8 chapter: presenter, then the words
    face(c["ch_t0"], c["ch_face_end"])
    def g_ch(t, dur, ctx):
        fr = E.blank(BG); word(fr, "Option 1", 960, 420, 190, k(t, 0, 0.3)); word(fr, "dense vectors on disk", 960, 620, 80, k(t, 0.5, 0.3), BLUE); return fr
    g(c["ch_face_end"], c["o1_t0"] + 0.3, g_ch); clicks(c["ch_face_end"])
    # 9 option 1: RAM -> disk in words and a red arrow
    def g_disk(t, dur, ctx):
        fr = E.blank(BG); d = ImageDraw.Draw(fr); T = c["o1_t0"] + 0.3 + t; word(fr, "RAM", 440, 480, 170, k(t, 0, 0.3)); red_arrow(d, (700, 480), (1120, 480), k(T, c["storing"], 0.4)); word(fr, "Disk", 1440, 480, 170, k(T, c["storing"] + 0.3, 0.3), BLUE)
        word(fr, "on_disk = True", 960, 760, 90, k(T, c["disk"], 0.3)); red_circle(d, 960, 760, 420, 90, k(T, c["disk"] + 0.3, 0.5)); return fr
    g(c["o1_t0"] + 0.3, t1, g_disk); clicks(c["storing"], c["disk"])
    return S, sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
