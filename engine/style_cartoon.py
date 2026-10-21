"""CARTOON: the flat illustrated look of Kurzgesagt (19.9M and 12.7M views on its two AI explainers), copied
from the frame audit of "AI Just Crossed the Terrifying Line".

What the audit shows
  - deep navy-purple scenes with a lighter glow on the floor, bright saturated flat shapes (violet, magenta,
    cyan, green, orange), every shape shaded with one darker flat tone, every light source glowing
  - characters: a purple one-eyed blob with tentacle arms (their "AI"), a laptop with a glowing screen, a
    rock with a face, pink hands; speech bubbles and chat pills in white
  - labels are chips: a rectangle with a small pointed tab, bold white text (green, magenta, violet, orange)
  - diagrams: a timeline line with diamond markers and chips, a neural web of cyan nodes with curved pink
    and cyan edges and green centre nodes, abstract code as coloured bars, glowing particle streams
  - titles in tracked small caps
  - pace: 6.8 hard cuts and 22 changes a minute; scenes hold 3 to 6 seconds while the camera drifts and
    things bounce in with a small overshoot
  - voice-over, no presenter; here the presenter lives inside the cartoon laptop screen
Fonts: Montserrat 700 for chips, Montserrat 600 tracked caps for titles.
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter
import engine as E
from engine import W, H, k, ease, inout, back, rgba
from beats import cues
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\cartoon_0-41.mp4"
BG = (14, 9, 34); NAVY = (24, 14, 58); VIOLET = (128, 48, 255); VIOLET_D = (82, 22, 180); MAG = (236, 46, 160); MAG_D = (160, 20, 110); CYAN = (46, 230, 255); CYAN_D = (20, 150, 190)
GREEN = (72, 230, 110); GREEN_D = (30, 150, 70); ORANGE = (255, 150, 40); ORANGE_D = (200, 90, 20); WHITE = (255, 255, 255); INK = (30, 20, 60); S = 2
LAPTOP_SCREEN = (610, 170, 700, 440)      # where the face sits (engine face card), in 1x frame units
LAPTOP_LEFT = (150, 250, 620, 390)        # the laptop parked left when a diagram shares the scene

def big_canvas(top=NAVY, bottom=BG, floor=None):
    """vertical gradient scene with an optional floor glow colour"""
    key = ("cartoon_bg", top, bottom, floor)
    if key not in E._fc:
        import numpy as np
        y = np.linspace(0, 1, H * S)[:, None, None]; a = np.array(top, np.float32) * (1 - y) + np.array(bottom, np.float32) * y
        im = Image.fromarray(np.clip(np.repeat(a, W * S, axis=1), 0, 255).astype(np.uint8)).convert("RGBA")
        if floor:
            g = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([-200 * S, 820 * S, (W + 200) * S, 1400 * S], fill=rgba(floor, 110)); im.alpha_composite(g.filter(ImageFilter.GaussianBlur(70 * S)))
        E._fc[key] = im
    return E._fc[key].copy()
def down(im, zoom=1.0):
    if zoom != 1.0: im = E.cover(im, W * S, H * S, zoom)
    return im.resize((W, H), Image.LANCZOS)
def glowlayer(im, blur, strength=1.0):
    g = im.filter(ImageFilter.GaussianBlur(blur * S)); g.putalpha(g.getchannel("A").point(lambda v: min(255, int(v * strength)))); return g
def shaded_circle(d, cx, cy, r, color, dark, light_from=(-0.4, -0.5)):
    """flat disc with a darker crescent on the side away from the light"""
    d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=rgba(dark))
    ox, oy = -light_from[0] * r * 0.28, -light_from[1] * r * 0.28
    d.ellipse([(cx - r * 0.92 - ox) * S, (cy - r * 0.92 - oy) * S, (cx + r * 0.92 - ox) * S, (cy + r * 0.92 - oy) * S], fill=rgba(color))
def chip(text, color, dark, prog=1.0, size=40, tab="down"):
    """rectangle label with a small pointed tab; pops with overshoot"""
    if prog <= 0: return None
    f = E.font("Montserrat[wght].ttf", size * S, 700); t = E.text_image(text, f, WHITE, pad=6 * S)
    w, h = t.width + 44 * S, t.height + 20 * S; im = Image.new("RGBA", (w, h + 24 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=rgba(color)); d.rectangle([0, h - 6 * S, w, h], fill=rgba(dark))
    if tab == "down": d.polygon([(w / 2 - 16 * S, h), (w / 2 + 16 * S, h), (w / 2, h + 22 * S)], fill=rgba(dark))
    im.alpha_composite(t, (22 * S, 10 * S)); s = 0.6 + 0.4 * back(prog)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR); im.putalpha(im.getchannel("A").point(lambda a: int(a * min(1, prog * 3)))); return im
def caps(text, size=34, color=(210, 200, 255), tracking=9):
    f = E.font("Montserrat[wght].ttf", size * S, 600); t = text.upper(); w = int(sum(E.TD.textlength(ch, font=f) + tracking * S for ch in t)) + 10 * S
    im = Image.new("RGBA", (w, int(size * 1.6) * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 5 * S
    for ch in t: d.text((x, size * 1.2 * S), ch, font=f, fill=rgba(color), anchor="ls"); x += d.textlength(ch, font=f) + tracking * S
    return im
def blob(t, prog=1.0, look=(0, 0), size=1.0, mood="calm"):
    """the one-eyed purple blob with tentacle arms; breathes, blinks, looks toward `look`"""
    if prog <= 0: return None
    w, h = int(700 * size), int(700 * size); im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); cx, cy = w / 2, h * 0.5
    br = 150 * size * (1 + 0.02 * math.sin(t * 2.2)); rng = random.Random(2)
    for i in range(5):     # tentacles
        a = math.pi * (0.55 + 0.9 * i / 4) + 0.2 * math.sin(t * 1.5 + i); pts = []
        for j in range(12):
            u = j / 11; L = br * (1.3 + 0.5 * (i % 2)) * u; ang = a + 0.9 * u * math.sin(t * 2 + i * 1.3 + u * 3)
            pts.append(((cx + math.cos(ang) * (br * 0.5 + L)) * S, (cy + math.sin(ang) * (br * 0.5 + L)) * S))
        for j in range(len(pts) - 1): d.line([pts[j], pts[j + 1]], fill=rgba(VIOLET_D if j > 8 else VIOLET), width=int((34 - 2.2 * j) * size * S))
    shaded_circle(d, cx, cy, br, VIOLET, VIOLET_D)
    for i in range(3):     # finger bumps on top
        a = -math.pi / 2 + (i - 1) * 0.55; d.ellipse([(cx + math.cos(a) * br * 0.95 - 34 * size) * S, (cy + math.sin(a) * br * 0.95 - 34 * size) * S, (cx + math.cos(a) * br * 0.95 + 34 * size) * S, (cy + math.sin(a) * br * 0.95 + 34 * size) * S], fill=rgba(VIOLET))
    er = br * 0.42; ex, ey = cx + look[0] * 10, cy + look[1] * 8; blink = (t % 3.7) < 0.12
    d.ellipse([(ex - er) * S, (ey - er) * S, (ex + er) * S, (ey + er) * S], fill=rgba((12, 8, 24)))
    if not blink:
        pr = er * 0.5; px, py = ex + look[0] * er * 0.35, ey + look[1] * er * 0.35
        d.ellipse([(px - pr) * S, (py - pr) * S, (px + pr) * S, (py + pr) * S], fill=rgba(WHITE))
    else: d.line([((ex - er) * S, ey * S), ((ex + er) * S, ey * S)], fill=rgba(VIOLET_D), width=8 * S)
    if mood == "worried": d.line([((ex - er * 0.9) * S, (ey - er * 1.25) * S), ((ex + er * 0.9) * S, (ey - er * 1.05) * S)], fill=rgba(VIOLET_D), width=14 * S)
    out = glowlayer(im, 26, 0.5); out.alpha_composite(im); s = 0.7 + 0.3 * back(prog)
    out = out.resize((max(1, int(out.width * s)), max(1, int(out.height * s))), Image.BILINEAR); return out
def particle_stream(t, n=140, x0=-100, x1=1100, y0=380, y1=760, cols=(CYAN, MAG, GREEN, VIOLET), speed=380, seed=1, size=18):
    im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); rng = random.Random(seed)
    for i in range(n):
        ph = rng.random(); y = y0 + rng.random() * (y1 - y0); sp = 0.6 + rng.random(); c = cols[i % len(cols)]
        x = x0 + ((t * speed * sp + ph * (x1 - x0)) % (x1 - x0)); yy = y + 26 * math.sin(x / 120 + i)
        d.rounded_rectangle([(x - size / 2) * S, (yy - size / 2) * S, (x + size / 2) * S, (yy + size / 2) * S], radius=4 * S, fill=rgba(c))
    out = glowlayer(im, 14, 0.9); out.alpha_composite(im); return out
def core(t, cx=1380, cy=540, r=230):
    """the Qdrant core: a red-violet planet with a glowing ring"""
    im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([(cx - r * 1.35) * S, (cy - r * 1.35) * S, (cx + r * 1.35) * S, (cy + r * 1.35) * S], outline=rgba(MAG), width=10 * S)
    shaded_circle(d, cx, cy, r, (220, 36, 76), (150, 18, 60), (-0.5, -0.4))
    mk = E.fit(Image.open(r"C:\Users\ADMIN\camera_audit\assets\qdrant-brandmark-white.png").convert("RGBA"), int(r * 0.9) * S, int(r * 0.9) * S); E.paste_center(im, mk, cx * S, cy * S)
    out = glowlayer(im, 40, 0.8); out.alpha_composite(im); return out
def laptop(fr_s, prog=1.0, rect=None):
    """the cartoon laptop drawn around the face card rect (2x canvas)"""
    x, y, w, h = rect or LAPTOP_SCREEN; d = ImageDraw.Draw(fr_s); a = int(255 * prog)
    g = Image.new("RGBA", fr_s.size, (0, 0, 0, 0)); ImageDraw.Draw(g).rectangle([(x - 60) * S, (y - 60) * S, (x + w + 60) * S, (y + h + 60) * S], fill=rgba(CYAN, 150)); fr_s.alpha_composite(g.filter(ImageFilter.GaussianBlur(60 * S)))
    d.rounded_rectangle([(x - 26) * S, (y - 26) * S, (x + w + 26) * S, (y + h + 26) * S], radius=22 * S, fill=rgba((40, 170, 150), a)); d.rounded_rectangle([(x - 18) * S, (y - 18) * S, (x + w + 18) * S, (y + h + 18) * S], radius=16 * S, fill=rgba((22, 110, 100), a))
    bx0, bx1, by = x - 120, x + w + 120, y + h + 26
    d.polygon([((bx0 + 40) * S, by * S), ((bx1 - 40) * S, by * S), (bx1 * S, (by + 70) * S), (bx0 * S, (by + 70) * S)], fill=rgba((60, 210, 185), a)); d.rectangle([bx0 * S, (by + 70) * S, bx1 * S, (by + 84) * S], fill=rgba((30, 130, 115), a))
    for r in range(3):
        for c_ in range(16): d.rounded_rectangle([((bx0 + 110 + c_ * 42) * S), ((by + 14 + r * 18) * S), ((bx0 + 140 + c_ * 42) * S), ((by + 26 + r * 18) * S)], radius=3 * S, fill=rgba((24, 120, 108), a))
def web(prog, t, cx=960, cy=540):
    """neural web: cyan nodes, curved pink/cyan edges, green centre nodes"""
    im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); rng = random.Random(9)
    nodes = [(cx + (-1) ** i * 120 * (1 + i // 2 * 0), cy + (-1) ** (i // 2) * 70) for i in range(4)]
    outer = [(cx + math.cos(a) * r * (1 + 0.05 * math.sin(t + a * 3)), cy + math.sin(a) * r * 0.8) for a, r in [(i * 2 * math.pi / 14 + 0.2, 330 + 70 * (i % 3)) for i in range(14)]]
    ring = [(cx + math.cos(a) * 190, cy + math.sin(a) * 150) for a in [i * 2 * math.pi / 7 + 0.5 for i in range(7)]]
    edges = []
    for i, o in enumerate(outer): edges.append((o, ring[i % 7], MAG if i % 2 else CYAN))
    for i, r_ in enumerate(ring): edges.append((r_, nodes[i % 4], CYAN if i % 2 else MAG))
    n = int(len(edges) * min(1, prog))
    for a, b, col in edges[:n]:
        mx, my = (a[0] + b[0]) / 2 + 40 * math.sin(a[1]), (a[1] + b[1]) / 2 + 40 * math.cos(a[0]); pts = []
        for j in range(16):
            u = j / 15; pts.append((((1 - u) ** 2 * a[0] + 2 * (1 - u) * u * mx + u ** 2 * b[0]) * S, ((1 - u) ** 2 * a[1] + 2 * (1 - u) * u * my + u ** 2 * b[1]) * S))
        d.line(pts, fill=rgba(col), width=9 * S, joint="curve")
    for pts_, r, col, dark in [(outer, 18, CYAN, CYAN_D), (ring, 22, CYAN, CYAN_D), (nodes, 30, GREEN, GREEN_D)]:
        for (x, y) in pts_:
            if prog > 0.05: shaded_circle(d, x, y, r, col, dark)
    out = glowlayer(im, 22, 0.8); out.alpha_composite(im); return out
def bars_index(prog, t):
    """abstract code as coloured bars: an inverted index building row by row"""
    im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); rng = random.Random(5); cols = [MAG, GREEN, ORANGE, CYAN, VIOLET]
    for r in range(6):
        pr = min(1, max(0, prog * 7 - r)); y = 300 + r * 92; x = 420
        segs = [(70, cols[r % 5]), (24, WHITE), (110 + rng.randrange(0, 120), cols[(r + 2) % 5]), (24, WHITE), (90 + rng.randrange(0, 160), cols[(r + 3) % 5])]
        for w_, c in segs:
            ww = w_ * ease(pr)
            if ww > 2: d.rounded_rectangle([x * S, y * S, (x + ww) * S, (y + 40) * S], radius=6 * S, fill=rgba(c))
            x += w_ + 16
    out = glowlayer(im, 16, 0.6); out.alpha_composite(im); return out
def disk(d, cx, cy, prog=1.0):
    """a stack of cyan platters"""
    for i in range(4):
        y = cy + 60 - i * 46 * ease(prog); d.ellipse([(cx - 200) * S, (y - 40) * S, (cx + 200) * S, (y + 40) * S], fill=rgba(CYAN_D)); d.rectangle([(cx - 200) * S, (y - 46) * S, (cx + 200) * S, y * S], fill=rgba(CYAN_D))
        d.ellipse([(cx - 200) * S, (y - 86) * S, (cx + 200) * S, (y - 6) * S], fill=rgba(CYAN)); d.ellipse([(cx - 50) * S, (y - 58) * S, (cx + 50) * S, (y - 34) * S], fill=rgba(CYAN_D))

def plan(p, t0, t1):
    c = cues(p); S_ = []; sfx = []
    FACE = ("card", LAPTOP_SCREEN, 14)
    def g(a, b, draw, tr="cut", face=None): S_.append(dict(t0=a, t1=b, kind="graphic", draw=draw, tr=tr, face=face))
    def pops(*ts):
        for t in ts: sfx.append((t, E.pop(0.07)))
    def laptop_scene(t, dur, ctx, extra=None, rect=None):
        fr = big_canvas(NAVY, BG, (30, 120, 110)); laptop(fr, 1.0, rect); fr = down(fr, 1.0 if rect else 1.0 + 0.03 * t / max(dur, 1))
        if extra: extra(fr, t)
        return fr
    # 0 the laptop with the presenter, then the core with the data stream
    g(c["hook_t0"], c["large"], laptop_scene, "cut", FACE)
    def g_core(t, dur, ctx):
        fr = big_canvas(NAVY, BG, (90, 20, 120)); fr.alpha_composite(core(t)); fr.alpha_composite(particle_stream(t, 160 if t > 0.3 else 60))
        ch = chip("a LOT of data", CYAN, CYAN_D, k(t, 0.2, 0.5), 44); fr.alpha_composite(ch, (int(300 * S), int(230 * S))) if ch else None
        pb = k(t, c["just"] - c["large"] - 0.3, 0.5); b = blob(t, pb, (1, -0.3), 0.8)
        if b is not None: fr.alpha_composite(b, (int(120 * S - b.width * 0.1), int(560 * S)))
        ch2 = chip("not just a vector store", MAG, MAG_D, k(t, c["just"] - c["large"], 0.5), 40); fr.alpha_composite(ch2, (int(560 * S), int(720 * S))) if ch2 else None
        return down(fr, 1.0 + 0.04 * t / dur)
    g(c["large"], c["list_t0"], g_core, "cut"); pops(c["large"] + 0.2, c["just"])
    # 1 the blob with four chips popping around it
    items = [("vectors", VIOLET, VIOLET_D, 0.0, (1180, 250)), ("payloads", GREEN, GREEN_D, c["payloads"] - c["list_t0"], (1400, 420)), ("indexes", CYAN, CYAN_D, c["indexes"] - c["list_t0"], (1350, 640)), ("...and much more", ORANGE, ORANGE_D, c["much"] - c["list_t0"], (1100, 820))]
    def g_list(t, dur, ctx):
        fr = big_canvas(NAVY, BG, (60, 20, 140)); b = blob(t, 1.0, (0.8, 0.1), 1.1); fr.alpha_composite(b, (int(230 * S), int(130 * S)))
        for name, col, dk, at, (x, y) in items:
            ch = chip(name, col, dk, k(t, at, 0.5), 44)
            if ch: E.paste_center(fr, ch, x * S, y * S)
        fr.alpha_composite(caps("what qdrant does on upload", 30), (120 * S, 90 * S)); return down(fr, 1.0 + 0.03 * t / dur)
    g(c["list_t0"], c["cfg_t0"], g_list, "cut"); pops(*[c["list_t0"] + it[3] for it in items])
    # 2 one config for everything? the chat pill, three workload planets, a magenta X
    def g_cfg(t, dur, ctx):
        fr = big_canvas((20, 110, 200), (10, 60, 150), (60, 220, 255)); d = ImageDraw.Draw(fr)
        pw = 980; d.rounded_rectangle([(470) * S, 300 * S, (470 + pw) * S, 420 * S], radius=60 * S, fill=rgba(WHITE)); d.rounded_rectangle([(470) * S, 404 * S, (470 + pw) * S, 420 * S], radius=8 * S, fill=rgba((200, 200, 230)))
        txt = "one config for everything"[:int(max(0, t - (c["single"] - c["cfg_t0"]) + 0.2) * 16)]; f = E.font("Montserrat[wght].ttf", 44 * S, 600); d.text((520 * S, 360 * S), txt, font=f, fill=rgba(VIOLET_D), anchor="lm")
        cur = 520 + d.textlength(txt, font=f) / S + 6; d.rectangle([cur * S, 338 * S, (cur + 16) * S, 382 * S], fill=rgba(VIOLET))
        shaded_circle(d, 1560, 360, 50, ORANGE, ORANGE_D); d.text((1560 * S, 360 * S), "\u21b5", font=E.font("Inter[opsz,wght].ttf", 44 * S, 700), fill=rgba(WHITE), anchor="mm")
        for i, (name, col, dk, at) in enumerate([("RAG app", GREEN, GREEN_D, c["works"]), ("100M points", MAG, MAG_D, c["works"] + 0.25), ("multi-tenant", ORANGE, ORANGE_D, c["works"] + 0.5)]):
            pr = k(t, at - c["cfg_t0"], 0.5); x = 560 + i * 400
            if pr > 0:
                shaded_circle(d, x, 680, 70 * back(pr), col, dk); ch = chip(name, col, dk, pr, 34, tab=None)
                if ch: E.paste_center(fr, ch, x * S, 820 * S)
        px = k(t, c["all"] - c["cfg_t0"], 0.4)
        if px > 0:
            xm = Image.new("RGBA", fr.size, (0, 0, 0, 0)); dx = ImageDraw.Draw(xm); r = 110 * back(px)
            dx.line([((960 - r) * S, (360 - r) * S), ((960 + r) * S, (360 + r) * S)], fill=rgba(MAG), width=28 * S); dx.line([((960 + r) * S, (360 - r) * S), ((960 - r) * S, (360 + r) * S)], fill=rgba(MAG), width=28 * S)
            fr.alpha_composite(glowlayer(xm, 30, 1.0)); fr.alpha_composite(xm)
        b = blob(t, 1.0, (0.4, -0.5), 0.55, "worried"); fr.alpha_composite(b, (int(60 * S), int(620 * S))); return down(fr, 1.0 + 0.03 * t / dur)
    g(c["cfg_t0"], c["plan_t0"], g_cfg, "cut"); pops(c["works"], c["works"] + 0.25, c["works"] + 0.5, c["all"])
    # 3 the plan: the presenter in the laptop, the timeline beside it
    def g_plan(t, dur, ctx):
        def extra(fr, t):
            d = ImageDraw.Draw(fr); cp = caps("the plan", 30); fr.alpha_composite(cp.resize((cp.width // S, cp.height // S), Image.LANCZOS), (900, 200))
            for row, (n, col, dk, at, lab) in enumerate([(4, GREEN, GREEN_D, c["options"] - c["plan_t0"], "options"), (3, MAG, MAG_D, c["best"] - c["plan_t0"], "best practices")]):
                y = 420 + row * 250; pl = k(t, at, 0.4); d.line([(900, y), (900 + 860 * ease(pl), y)], fill=rgba((120, 100, 220)), width=4)
                for i in range(n):
                    pr = k(t, at + 0.12 * i, 0.35); x = 940 + i * 780 / max(1, n - 1)
                    if pr > 0:
                        r = 14 * back(pr); d.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], fill=rgba(col))
                        ch = chip(str(i + 1), col, dk, pr, 30); ch = ch.resize((ch.width // S, ch.height // S), Image.LANCZOS); E.paste_center(fr, ch, x, y - 62)
                lab_im = caps(lab, 24, (210, 200, 255), 6); lab_im = lab_im.resize((lab_im.width // S, lab_im.height // S), Image.LANCZOS); pl2 = k(t, at + 0.5, 0.4)
                if pl2 > 0: lab_im.putalpha(lab_im.getchannel("A").point(lambda a: int(a * pl2))); fr.alpha_composite(lab_im, (900, y + 30))
        return laptop_scene(t, dur, ctx, extra, LAPTOP_LEFT)
    g(c["plan_t0"], c["ds_t0"], g_plan, "cut", ("card", LAPTOP_LEFT, 14)); pops(c["options"], c["best"])
    # 4 dense and sparse: a dense cloud and a sparse cloud with their chips
    def g_ds(t, dur, ctx):
        fr = big_canvas(NAVY, BG, (40, 30, 140)); d = ImageDraw.Draw(fr); rng = random.Random(4); T = c["ds_t0"] + t
        for side, (cx, n, col, dk, at, name) in enumerate([(560, 120, CYAN, CYAN_D, c["dense"], "dense"), (1360, 9, MAG, MAG_D, c["sparse"], "sparse")]):
            pr = k(T, at, 0.6); lay = Image.new("RGBA", fr.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            for i in range(n):
                a = rng.random() * 2 * math.pi; r = 240 * math.sqrt(rng.random()) * (1 + 0.05 * math.sin(t * 1.5 + i)); pp = min(1, max(0, pr * 1.4 - i / n * 0.4))
                if pp > 0: rr = (14 if n > 20 else 30) * back(pp); x, y = cx + r * math.cos(a), 520 + r * math.sin(a) * 0.9; dl.ellipse([(x - rr) * S, (y - rr) * S, (x + rr) * S, (y + rr) * S], fill=rgba(col))
            fr.alpha_composite(glowlayer(lay, 18, 0.9)); fr.alpha_composite(lay); ch = chip(name, col, dk, pr, 48)
            if ch: E.paste_center(fr, ch, cx * S, 860 * S)
        fr.alpha_composite(caps("two kinds of vectors", 30), (120 * S, 90 * S)); b = blob(t, 1.0, (0.3, -0.7), 0.5); fr.alpha_composite(b, (int(40 * S), int(640 * S))); return down(fr, 1.0 + 0.03 * t / dur)
    g(c["ds_t0"], c["hnsw_t0"] + 0.3, g_ds, "cut"); pops(c["dense"], c["sparse"])
    # 5 HNSW: the neural web
    def g_web(t, dur, ctx):
        fr = big_canvas(BG, (6, 4, 20)); fr.alpha_composite(web(k(t, 0.1, 1.6), t)); ch = chip("HNSW", GREEN, GREEN_D, k(t, c["hnsw"] - c["hnsw_t0"] - 0.3, 0.5), 54)
        if ch: E.paste_center(fr, ch, 960 * S, 940 * S)
        return down(fr, 1.0 + 0.05 * t / dur)
    g(c["hnsw_t0"] + 0.3, c["sparse2"] + 0.2, g_web, "cut"); pops(c["hnsw"])
    # 6 sparse index: coloured bars
    def g_bars(t, dur, ctx):
        fr = big_canvas(BG, (6, 4, 20)); fr.alpha_composite(bars_index(k(t, 0.1, 2.0), t)); ch = chip("sparse index", CYAN, CYAN_D, k(t, c["indexing"] - c["sparse2"] - 0.2, 0.5), 48)
        if ch: E.paste_center(fr, ch, 960 * S, 940 * S)
        b = blob(t, 1.0, (-0.6, -0.2), 0.5); fr.alpha_composite(b, (int(1380 * S), int(560 * S))); return down(fr, 1.0 + 0.03 * t / dur)
    g(c["sparse2"] + 0.2, c["mp_t0"], g_bars, "cut"); pops(c["indexing"])
    # 7 memory and performance: two chips with bars filling, the blob worried
    def g_mp(t, dur, ctx):
        fr = big_canvas(NAVY, BG, (140, 40, 20)); d = ImageDraw.Draw(fr)
        for i, (name, col, dk, at, v) in enumerate([("memory", ORANGE, ORANGE_D, c["memory"] - c["mp_t0"], 0.85), ("performance", GREEN, GREEN_D, c["perf"] - c["mp_t0"], 0.55)]):
            pr = k(t, at, 0.5); x = 760 + i * 520
            ch = chip(name, col, dk, pr, 44)
            if ch: E.paste_center(fr, ch, x * S, 330 * S)
            if pr > 0:
                d.rounded_rectangle([(x - 180) * S, 440 * S, (x + 180) * S, 490 * S], radius=25 * S, fill=rgba((40, 30, 80)))
                lay = Image.new("RGBA", fr.size, (0, 0, 0, 0)); ImageDraw.Draw(lay).rounded_rectangle([(x - 180) * S, 440 * S, (x - 180 + 360 * v * ease((t - at) / 1.2)) * S, 490 * S], radius=25 * S, fill=rgba(col)); fr.alpha_composite(glowlayer(lay, 16, 0.8)); fr.alpha_composite(lay)
        b = blob(t, 1.0, (0.5, -0.6), 0.9, "worried" if t > c["bulk"] - c["mp_t0"] else "calm"); fr.alpha_composite(b, (int(180 * S), int(380 * S)))
        cp = caps("during bulk uploads", 34, (255, 200, 120)); pc = k(t, c["bulk"] - c["mp_t0"], 0.4)
        if pc > 0: cp.putalpha(cp.getchannel("A").point(lambda a: int(a * pc))); E.paste_center(fr, cp, 1020 * S, 760 * S)
        return down(fr, 1.0 + 0.03 * t / dur)
    g(c["mp_t0"], c["ch_t0"], g_mp, "cut"); pops(c["memory"], c["perf"], c["bulk"])
    # 8 chapter: presenter in the laptop, then the Option 1 chip with the blob
    g(c["ch_t0"], c["ch_face_end"], laptop_scene, "cut", FACE)
    def g_ch(t, dur, ctx):
        fr = big_canvas(NAVY, BG, (90, 20, 120)); ch = chip("Option 1", MAG, MAG_D, k(t, 0.1, 0.5), 80, tab=None); E.paste_center(fr, ch, 960 * S, 420 * S) if ch else None
        cp = caps("store dense vectors on disk", 34); pc = k(t, 0.5, 0.4)
        if pc > 0: cp.putalpha(cp.getchannel("A").point(lambda a: int(a * pc))); E.paste_center(fr, cp, 960 * S, 560 * S)
        b = blob(t, k(t, 0.3, 0.5), (0, -0.8), 0.6); fr.alpha_composite(b, (int(760 * S), int(640 * S))) if b is not None else None; return down(fr, 1.0 + 0.03 * t / dur)
    g(c["ch_face_end"], c["storing"] - 0.2, g_ch, "cut"); pops(c["ch_face_end"] + 0.1)
    # 9 on disk: cubes fly from the RAM chip into the platters
    def g_disk(t, dur, ctx):
        fr = big_canvas(NAVY, BG, (20, 90, 140)); d = ImageDraw.Draw(fr)
        d.rounded_rectangle([300 * S, 380 * S, 640 * S, 620 * S], radius=18 * S, fill=rgba(GREEN_D)); d.rounded_rectangle([300 * S, 380 * S, 640 * S, 596 * S], radius=18 * S, fill=rgba(GREEN))
        for i in range(8): d.rectangle([(318 + i * 40) * S, 622 * S, (338 + i * 40) * S, 660 * S], fill=rgba(GREEN_D))
        d.text((470 * S, 490 * S), "RAM", font=E.font("Montserrat[wght].ttf", 56 * S, 700), fill=rgba(INK), anchor="mm")
        disk(d, 1380, 520, k(t, 0.1, 0.6)); pm = k(t, c["storing"] - (c["storing"] - 0.2), 0.3)
        if pm > 0: fr.alpha_composite(particle_stream(t, 60, 660, 1180, 440, 560, (CYAN, GREEN, VIOLET), 420, 3, 22))
        ch = chip("on disk", CYAN, CYAN_D, k(t, c["disk"] - (c["storing"] - 0.2), 0.5), 48); E.paste_center(fr, ch, 1380 * S, 300 * S) if ch else None
        return down(fr, 1.0 + 0.03 * t / dur)
    g(c["storing"] - 0.2, t1, g_disk, "cut"); pops(c["storing"], c["disk"])
    return S_, sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
