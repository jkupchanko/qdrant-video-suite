"""BRIGHT: Cleo Abram's "Huge If True" look (13.5M views on "What If You Just Keep Digging?"), copied from
the frame audit.

What the audit shows
  - bright flat illustration: layered, textured strata in orange, magenta, yellow and brown under a sky;
    a drill descending through them; props drawn flat with a dark outline
  - a vertical gauge on the right that stays on screen and tracks progress (a marker, a value chip)
  - titles in lime condensed capitals with a dark drop shadow ("WHAT'S REALLY GOING ON?"); a chapter
    title filled with a texture ("THE CRUST")
  - callouts: a big number, a small-caps label and a sub-label ("1,000M / KAMIOKA OBSERVATORY / JAPAN")
  - dashboards on blue: ring gauges and thermometers with small-caps labels under them
  - the presenter in a bright studio full frame, or tiny inside the illustration
  - pace: 17 hard cuts and 33 changes a minute; archival black and white footage between scenes
Here: the upload is the drill; the strata are what Qdrant writes (vectors, payloads, indexes, more); the
gauge is memory; Option 1 reaches the disk layer.
Fonts: Anton for the lime titles, Oswald 700 for numbers, Inter 700 small caps for labels.
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import engine as E
from engine import W, H, k, ease, inout, back, rgba
from beats import cues
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\bright_0-41.mp4"; BG = (14, 22, 36)
LIME = (216, 255, 60); NAVY = (14, 27, 42); SKY = (72, 170, 255); SKY2 = (150, 215, 255); GRASS = (120, 200, 60); ORANGE = (255, 122, 26); MAG = (194, 24, 126); YEL = (255, 210, 30); BROWN = (107, 58, 30); DEEP = (60, 24, 12); WHITE = (255, 255, 255); RED = (235, 50, 40); BLUE_D = (28, 70, 150)
LAYERS = [("VECTORS", ORANGE, (255, 150, 60)), ("PAYLOADS", MAG, (225, 60, 160)), ("INDEXES", YEL, (255, 230, 90)), ("MORE", BROWN, (140, 80, 40))]

def texture(color, light, seed, w=W, h=H):
    key = ("bright_tex", color, seed)
    if key not in E._fc:
        rng = np.random.default_rng(seed); n = rng.normal(0, 1, (h // 4, w // 4)); n = np.kron(n, np.ones((4, 4)))[:h, :w]
        n2 = rng.normal(0, 1, (h // 32 + 1, w // 32 + 1)); n2 = np.kron(n2, np.ones((32, 32)))[:h, :w]
        m = np.clip(0.5 + 0.18 * n + 0.22 * n2, 0, 1)[:, :, None]; a = np.array(color, np.float32) * (1 - m) + np.array(light, np.float32) * m
        E._fc[key] = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    return E._fc[key]
def title(text, size=120, color=LIME, shadow=NAVY):
    """lime condensed capitals with a hard dark shadow"""
    f = E.font("Anton-Regular.ttf", size); lines = text.upper().split("\n"); ims = []
    for ln in lines:
        t = E.text_image(ln, f, color, pad=12); sh = E.text_image(ln, f, shadow, pad=12); im = Image.new("RGBA", (t.width + 10, t.height + 10), (0, 0, 0, 0)); im.alpha_composite(sh, (8, 8)); im.alpha_composite(t, (0, 0)); ims.append(im)
    out = Image.new("RGBA", (max(i.width for i in ims), sum(i.height for i in ims) - 20 * (len(ims) - 1)), (0, 0, 0, 0)); y = 0
    for im in ims: out.alpha_composite(im, ((out.width - im.width) // 2, y)); y += im.height - 20
    return out
def smallcaps(text, size=24, color=WHITE, tracking=2):
    f = E.font("Inter[opsz,wght].ttf", size, 700); t = text.upper(); w = int(sum(E.TD.textlength(ch, font=f) + tracking for ch in t)) + 8
    im = Image.new("RGBA", (w, int(size * 1.5)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 4
    for ch in t: d.text((x, size * 1.15), ch, font=f, fill=rgba(color), anchor="ls"); x += d.textlength(ch, font=f) + tracking
    return im
def callout(number, label, sub, prog=1.0, color=WHITE):
    """big number, small-caps label, sub-label; rises in"""
    if prog <= 0: return None
    n = E.text_image(number, E.font("Oswald[wght].ttf", 56, 700), color, pad=4); l = smallcaps(label, 26, color, 3); s = smallcaps(sub, 20, (210, 210, 220), 2)
    im = Image.new("RGBA", (max(n.width, l.width, s.width) + 10, n.height + l.height + s.height), (0, 0, 0, 0)); im.alpha_composite(n, (0, 0)); im.alpha_composite(l, (0, n.height - 6)); im.alpha_composite(s, (0, n.height + l.height - 14))
    im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog)))); return im
def chip(text, prog=1.0, color=LIME, fg=NAVY, size=28):
    if prog <= 0: return None
    t = smallcaps(text, size, fg, 2); im = Image.new("RGBA", (t.width + 28, t.height + 6), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=6, fill=rgba(color)); im.alpha_composite(t, (14, 3))
    s = 0.7 + 0.3 * back(prog); im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR); return im
def gauge(fr, value, prog=1.0, label="MEMORY", x=1800):
    """the vertical gauge on the right: yellow to red, a marker at `value` (0 top .. 1 bottom), a value chip"""
    if prog <= 0: return
    d = ImageDraw.Draw(fr); y0, y1 = 120, 980; d.rounded_rectangle([x - 16, y0 - 16, x + 16, y1 + 16], radius=18, fill=rgba(NAVY)); d.rounded_rectangle([x - 10, y0, x + 10, y1], radius=10, fill=(40, 30, 30, 255))
    for i in range(0, int((y1 - y0) * ease(prog)), 4):
        u = i / (y1 - y0); col = (int(255), int(220 - 180 * u), int(40)); d.rectangle([x - 10, y0 + i, x + 10, y0 + i + 4], fill=rgba(col))
    my = y0 + (y1 - y0) * value; d.ellipse([x - 22, my - 22, x + 22, my + 22], fill=rgba(NAVY)); d.ellipse([x - 14, my - 14, x + 14, my + 14], fill=rgba(LIME))
    c = chip(f"{label} {int(value * 100)}%", 1, LIME, NAVY, 20)
    if c: fr.alpha_composite(c, (x - c.width - 34, int(my - c.height / 2)))
def strata(fr, t, depth, named):
    """sky, grass, then the four strata; `depth` 0..1 is how far the drill has gone; `named` = layers labelled so far"""
    d = ImageDraw.Draw(fr); d.rectangle([0, 0, W, 300], fill=rgba(SKY)); d.ellipse([200, 60, 420, 150], fill=rgba(SKY2)); d.ellipse([1200, 90, 1500, 180], fill=rgba(SKY2))
    d.rectangle([0, 280, W, 320], fill=rgba(GRASS)); tops = [320, 500, 680, 860]
    for i, (name, col, light) in enumerate(LAYERS):
        y = tops[i]; y2 = tops[i + 1] if i + 1 < len(tops) else H; band = texture(col, light, 11 + i).crop((0, y, W, y2)); fr.alpha_composite(band, (0, y)); d.line([(0, y), (W, y)], fill=rgba(DEEP), width=6)
        if named > i:
            lab = chip(name, min(1, named - i), LIME, NAVY, 30); fr.alpha_composite(lab, (120, y + 24))
    # the shaft and the drill head
    sx = 960; sy = 300 + (H - 360) * depth; d.rectangle([sx - 26, 300, sx + 26, sy], fill=rgba((40, 28, 24))); d.rectangle([sx - 12, 300, sx + 12, sy], fill=rgba((90, 70, 60)))
    d.rounded_rectangle([sx - 40, sy - 70, sx + 40, sy + 20], radius=18, fill=rgba(NAVY)); d.rounded_rectangle([sx - 32, sy - 62, sx + 32, sy + 12], radius=14, fill=rgba((40, 110, 230))); d.ellipse([sx - 10, sy - 40, sx + 10, sy - 20], fill=rgba(LIME))
    d.polygon([(sx - 34, sy + 12), (sx + 34, sy + 12), (sx, sy + 60)], fill=rgba((200, 200, 210)))
    # the rig on the surface
    d.polygon([(sx - 120, 300), (sx + 120, 300), (sx + 30, 110), (sx - 30, 110)], outline=rgba(NAVY), width=8, fill=(0, 0, 0, 0)); d.rectangle([sx - 140, 270, sx + 140, 300], fill=rgba(NAVY))
def panel(fr, text, prog, y=None):
    """the dark question card over a scene"""
    if prog <= 0: return
    im = title(text, 110); im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog)))); E.paste_center(fr, im, W / 2 + 140, y or H / 2)
def ring(fr, cx, cy, value, label, sub, prog, color=LIME):
    if prog <= 0: return
    d = ImageDraw.Draw(fr); r = 150; d.ellipse([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14], fill=rgba(WHITE)); d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rgba(NAVY))
    d.arc([cx - r + 24, cy - r + 24, cx + r - 24, cy + r - 24], 135, 405, fill=(70, 80, 100, 255), width=26); d.arc([cx - r + 24, cy - r + 24, cx + r - 24, cy + r - 24], 135, 135 + 270 * value * ease(prog), fill=rgba(color), width=26)
    a = math.radians(135 + 270 * value * ease(prog)); d.line([(cx, cy), (cx + (r - 50) * math.cos(a), cy + (r - 50) * math.sin(a))], fill=rgba(WHITE), width=8); d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=rgba(LIME))
    l = smallcaps(label, 34, WHITE, 3); E.paste_center(fr, l, cx, cy + r + 60); s = smallcaps(sub, 22, (200, 215, 240), 2); E.paste_center(fr, s, cx, cy + r + 100)
def thermo(fr, x, value, label, prog, color):
    if prog <= 0: return
    d = ImageDraw.Draw(fr); y0, y1 = 300, 760; d.rounded_rectangle([x - 34, y0 - 34, x + 34, y1 + 34], radius=34, fill=rgba(WHITE)); d.rounded_rectangle([x - 22, y0 - 22, x + 22, y1 + 22], radius=22, fill=rgba(NAVY))
    v = value * ease(prog); d.rounded_rectangle([x - 12, y1 - (y1 - y0) * v, x + 12, y1], radius=12, fill=rgba(color)); d.ellipse([x - 60, y1, x + 60, y1 + 120], fill=rgba(WHITE)); d.ellipse([x - 48, y1 + 12, x + 48, y1 + 108], fill=rgba(color))
    n = E.text_image(f"{int(100 * v)}%", E.font("Oswald[wght].ttf", 56, 700), WHITE, pad=4); E.paste_center(fr, n, x, y1 + 190); l = smallcaps(label, 26, WHITE, 3); E.paste_center(fr, l, x, y1 + 240)

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []
    def face(a, b): S.append(dict(t0=a, t1=b, kind="face", tr="cut"))
    def g(a, b, draw, tr="cut"): S.append(dict(t0=a, t1=b, kind="graphic", draw=draw, tr=tr, face=None))
    def pops(*ts):
        for t in ts: sfx.append((t, E.pop(0.07)))
    # 0 hook: the rig on the surface, the drill starts; "a LOT of data" chip, then the question card
    face(c["hook_t0"], c["large"])
    def g_hook(t, dur, ctx):
        fr = E.blank(BG); strata(fr, t, 0.04 * ease(t / 2), 0); gauge(fr, 0.1, k(t, 0.3, 0.6))
        ch = chip("A LOT OF DATA", k(t, 0.2, 0.5), LIME, NAVY, 36)
        if ch: fr.alpha_composite(ch, (640, 80))
        panel(fr, "not just\nstoring vectors", k(t, c["just"] - c["large"] - 0.1, 0.5), 620); return fr
    g(c["large"], c["list_t0"], g_hook, "cut"); pops(c["large"] + 0.2, c["just"])
    # 1 the drill goes down through the strata, each labelled on its word; the gauge rises
    def g_layers(t, dur, ctx):
        fr = E.blank(BG); T = c["list_t0"] + t; named = sum(k(T, at, 0.4) for at in (c["list_t0"] + 0.3, c["payloads"], c["indexes"], c["much"]))
        strata(fr, t, 0.1 + 0.75 * inout(t / (dur - 0.3)), named); gauge(fr, 0.15 + 0.45 * inout(t / dur))
        co = callout("4 LAYERS", "written on every upload", "qdrant collection", k(T, c["background"], 0.5)); fr.alpha_composite(co, (1240, 360)) if co else None; return fr
    g(c["list_t0"], c["cfg_t0"], g_layers, "cut"); pops(c["payloads"], c["indexes"], c["much"])
    # 2 one config for all? the question card, three callouts, an orange cross
    def g_cfg(t, dur, ctx):
        fr = texture(DEEP, (90, 40, 20), 3).copy(); fr = E.vignette(fr, 0.5); T = c["cfg_t0"] + t; panel(fr, "one config\nfor all?", k(T, c["single"] - 0.2, 0.5), 330)
        for i, (n, l, s, at) in enumerate([("1", "rag app", "small, filtered", c["works"]), ("2", "100M points", "huge, dense", c["works"] + 0.25), ("3", "multi-tenant", "many small collections", c["works"] + 0.5)]):
            co = callout(n, l, s, k(T, at, 0.5)); fr.alpha_composite(co, (330 + i * 520, 700)) if co else None
        px = k(T, c["all"], 0.35)
        if px > 0:
            d = ImageDraw.Draw(fr); r = 120 * back(px); cx, cy = 1560, 330; d.line([(cx - r, cy - r), (cx + r, cy + r)], fill=rgba(ORANGE), width=22); d.line([(cx + r, cy - r), (cx - r, cy + r)], fill=rgba(ORANGE), width=22)
        return fr
    g(c["cfg_t0"], c["plan_t0"], g_cfg, "cut"); pops(c["works"], c["works"] + 0.25, c["works"] + 0.5, c["all"])
    # 3 the plan: the presenter
    face(c["plan_t0"], c["ds_t0"])
    # 4-6 two kinds of vectors: the dashboard on blue with two ring gauges that gain their index labels
    def g_ds(t, dur, ctx):
        fr = texture(BLUE_D, (60, 120, 210), 5).copy(); T = c["ds_t0"] + t; tt = smallcaps("two kinds of vectors", 34, WHITE, 4); E.paste_center(fr, tt, W / 2, 110)
        ring(fr, 560, 480, 0.92, "dense", "hnsw graph" if T >= c["hnsw"] else " ", k(T, c["dense"], 0.6), LIME)
        ring(fr, 1360, 480, 0.18, "sparse", "sparse index" if T >= c["indexing"] else " ", k(T, c["sparse"], 0.6), (255, 150, 60))
        d = ImageDraw.Draw(fr); pc = k(T, c["indexing"] + 0.5, 0.4)
        if pc > 0: lab = chip("indexed completely differently", pc, LIME, NAVY, 26); E.paste_center(fr, lab, W / 2, 900)
        return fr
    g(c["ds_t0"], c["mp_t0"], g_ds, "cut"); pops(c["dense"], c["sparse"], c["hnsw"], c["indexing"])
    # 7 memory and performance: two thermometers, the question in lime
    def g_mp(t, dur, ctx):
        fr = texture(BLUE_D, (60, 120, 210), 6).copy(); T = c["mp_t0"] + t; tt = smallcaps("what it feels like during a bulk upload", 30, WHITE, 4); E.paste_center(fr, tt, W / 2, 110)
        thermo(fr, 640, 0.88, "memory", k(T, c["memory"], 1.0), (255, 90, 50)); thermo(fr, 1280, 0.42, "performance", k(T, c["perf"], 1.0), LIME)
        ch = chip("during bulk uploads", k(T, c["bulk"], 0.5), LIME, NAVY, 30); E.paste_center(fr, ch, W / 2, 1010) if ch else None; return fr
    g(c["mp_t0"], c["ch_t0"], g_mp, "cut"); pops(c["memory"], c["perf"], c["bulk"])
    # 8 chapter: presenter, then the textured big title
    face(c["ch_t0"], c["ch_face_end"])
    def g_title(t, dur, ctx):
        fr = E.blank((8, 8, 12)); f = E.font("Anton-Regular.ttf", 300); m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).text((W / 2, H / 2), "OPTION 1", font=f, fill=255, anchor="mm")
        tex = texture(ORANGE, (255, 230, 90), 9).copy(); tex.putalpha(m.point(lambda a: int(a * ease(t / 0.5)))); fr.alpha_composite(tex); return fr
    g(c["ch_face_end"], c["o1_t0"] + 0.2, g_title, "cut"); sfx.append((c["ch_face_end"], E.boom(0.1)))
    # 9 option 1: the drill reaches the disk layer; the gauge drops; the callout
    def g_disk(t, dur, ctx):
        fr = E.blank(BG); T = c["o1_t0"] + 0.2 + t; strata(fr, t, 0.88 + 0.08 * ease(t / 1.2), 4); d = ImageDraw.Draw(fr)
        d.rectangle([0, 980, W, H], fill=rgba((30, 60, 120))); lab = chip("DISK", 1, LIME, NAVY, 30); fr.alpha_composite(lab, (120, 1000))
        gauge(fr, 0.6 - 0.4 * ease((T - c["disk"]) / 0.8) if T > c["disk"] else 0.6)
        co = callout("OPTION 1", "store dense vectors on disk", "on_disk = true", k(T, c["storing"], 0.5)); fr.alpha_composite(co, (1180, 420)) if co else None; return fr
    g(c["o1_t0"] + 0.2, t1, g_disk, "cut"); pops(c["storing"], c["disk"])
    return S, sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
