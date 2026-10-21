"""STICK: CGP Grey's look ("AI Doesn't Know Anything. It Just Passes Tests.", 12.6M views), copied from
the frame audit.

What the audit shows
  - a light grey paper background with a faint texture; nothing else behind the characters
  - stick figures: a white circle head with a thick black outline, dot eyes, a mouth that changes, stick
    limbs; glasses for the lecturer; a small white robot with a red light for the machine
  - props drawn flat with black outlines: a desk and monitor, a dark green chalkboard with white chalk
    diagrams, a pull-down projector screen with photos pasted on it, boxes, a waste basket
  - a red rubber stamp ("CLASSIFIED") slammed over a diagram
  - a scene per idea, cut to cut: 15 hard cuts and 33 changes a minute; inside a scene things slide
    in from the sides and the figures gesture
Fonts: Nunito 800 for the few labels (round, friendly), Anton for the stamp.
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import engine as E
from engine import W, H, k, ease, inout, back, rgba
from beats import cues
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\stick_0-41.mp4"; BG = (232, 232, 230)
INK = (20, 20, 20); WHITE = (255, 255, 255); BOARD = (34, 78, 56); CHALK = (240, 240, 235); RED = (205, 30, 30); BLUE = (80, 140, 220); WOOD = (150, 100, 60); ROBOT_EYE = (120, 170, 220)
MEMES = r"C:\Users\ADMIN\camera_audit\style\memes"

def paper():
    key = "stick_paper"
    if key not in E._fc:
        rng = np.random.default_rng(3); n = rng.normal(0, 3, (H, W, 1)); a = np.array(BG, np.float32)[None, None, :] + n
        E._fc[key] = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    return E._fc[key].copy()
def figure(d, x, y, scale=1.0, mood="calm", pose="stand", glasses=False, arm=0.0, lean=0.0):
    """a stick figure standing at (x, y) = feet; mood: calm | happy | sad | worried; arm: 0..1 raises the right arm"""
    s = scale; hr = 30 * s; hy = y - 200 * s; hx = x + lean * 30 * s
    d.line([(hx, hy + hr), (x, y - 70 * s)], fill=rgba(INK), width=int(6 * s))                                   # spine
    d.line([(x, y - 70 * s), (x - 32 * s, y)], fill=rgba(INK), width=int(6 * s)); d.line([(x, y - 70 * s), (x + 32 * s, y)], fill=rgba(INK), width=int(6 * s))   # legs
    sh = (hx * 0.3 + x * 0.7, hy + hr + 30 * s)
    d.line([sh, (x - 50 * s, y - 95 * s)], fill=rgba(INK), width=int(6 * s))                                     # left arm
    ax, ay = x + 55 * s, (y - 95 * s) * (1 - arm) + (hy - 10 * s) * arm; d.line([sh, (ax, ay)], fill=rgba(INK), width=int(6 * s))   # right arm (raised with `arm`)
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=rgba(WHITE), outline=rgba(INK), width=int(5 * s))
    d.ellipse([hx - 11 * s, hy - 6 * s, hx - 5 * s, hy], fill=rgba(INK)); d.ellipse([hx + 5 * s, hy - 6 * s, hx + 11 * s, hy], fill=rgba(INK))
    if glasses: d.ellipse([hx - 20 * s, hy - 12 * s, hx - 1 * s, hy + 6 * s], outline=rgba(INK), width=int(3 * s)); d.ellipse([hx + 1 * s, hy - 12 * s, hx + 20 * s, hy + 6 * s], outline=rgba(INK), width=int(3 * s))
    if mood == "happy": d.arc([hx - 14 * s, hy + 2 * s, hx + 14 * s, hy + 20 * s], 10, 170, fill=rgba(INK), width=int(3 * s))
    elif mood == "sad": d.arc([hx - 14 * s, hy + 10 * s, hx + 14 * s, hy + 26 * s], 190, 350, fill=rgba(INK), width=int(3 * s))
    elif mood == "worried": d.line([(hx - 12 * s, hy + 14 * s), (hx + 12 * s, hy + 12 * s)], fill=rgba(INK), width=int(3 * s)); d.line([(hx - 16 * s, hy - 18 * s), (hx - 4 * s, hy - 14 * s)], fill=rgba(INK), width=int(3 * s))
    else: d.line([(hx - 10 * s, hy + 14 * s), (hx + 10 * s, hy + 14 * s)], fill=rgba(INK), width=int(3 * s))
def robot(d, x, y, scale=1.0, t=0.0, mood="calm", carry=None):
    """the little white robot: rounded body, dark visor with two eyes, a red light, stub arms; bobs a little"""
    s = scale; y = y + 4 * math.sin(t * 3); bw, bh = 90 * s, 110 * s
    d.rounded_rectangle([x - bw / 2, y - bh, x + bw / 2, y], radius=int(28 * s), fill=rgba(WHITE), outline=rgba(INK), width=int(5 * s))
    d.rounded_rectangle([x - bw / 2 + 12 * s, y - bh + 16 * s, x + bw / 2 - 12 * s, y - bh + 52 * s], radius=int(12 * s), fill=rgba((40, 44, 52)))
    for ex in (-18, 18): d.ellipse([x + ex * s - 8 * s, y - bh + 26 * s, x + ex * s + 8 * s, y - bh + 42 * s], fill=rgba(ROBOT_EYE if mood != "worried" else (230, 120, 90)))
    d.line([(x, y - bh), (x, y - bh - 14 * s)], fill=rgba(INK), width=int(4 * s)); d.ellipse([x - 7 * s, y - bh - 26 * s, x + 7 * s, y - bh - 12 * s], fill=rgba(RED))
    d.line([(x - bw / 2, y - 60 * s), (x - bw / 2 - 26 * s, y - 40 * s)], fill=rgba(INK), width=int(6 * s)); d.line([(x + bw / 2, y - 60 * s), (x + bw / 2 + 26 * s, y - 40 * s)], fill=rgba(INK), width=int(6 * s))
    d.line([(x - 22 * s, y), (x - 22 * s, y + 14 * s)], fill=rgba(INK), width=int(6 * s)); d.line([(x + 22 * s, y), (x + 22 * s, y + 14 * s)], fill=rgba(INK), width=int(6 * s))
    if carry: box(d, x - 50 * s, y - bh - 30 * s - 70 * s, 100 * s, 70 * s, carry, 1.0)
def box(d, x, y, w, h, label=None, prog=1.0, fill=(250, 240, 210)):
    if prog <= 0: return
    s = 0.7 + 0.3 * back(prog); cx, cy = x + w / 2, y + h / 2; w2, h2 = w * s, h * s
    d.rectangle([cx - w2 / 2, cy - h2 / 2, cx + w2 / 2, cy + h2 / 2], fill=rgba(fill), outline=rgba(INK), width=4); d.line([(cx - w2 / 2, cy - h2 / 2 + 12), (cx + w2 / 2, cy - h2 / 2 + 12)], fill=rgba(INK), width=3)
    if label: d.text((cx, cy + 6), label, font=E.font("Nunito[wght].ttf", int(26 * s), 800), fill=rgba(INK), anchor="mm")
def desk(d, x, y, w=320):
    d.rectangle([x, y - 20, x + w, y], fill=rgba(WOOD), outline=rgba(INK), width=4); d.rectangle([x + 16, y, x + 36, y + 110], fill=rgba(WOOD), outline=rgba(INK), width=4); d.rectangle([x + w - 36, y, x + w - 16, y + 110], fill=rgba(WOOD), outline=rgba(INK), width=4)
def monitor(d, x, y, prog=1.0):
    d.rectangle([x, y - 110, x + 150, y - 20], fill=rgba((40, 44, 52)), outline=rgba(INK), width=4); d.rectangle([x + 60, y - 20, x + 90, y], fill=rgba(INK)); d.rectangle([x + 40, y, x + 110, y + 8], fill=rgba(INK))
    if prog > 0: d.rectangle([x + 8, y - 102, x + 8 + 134 * prog, y - 28], fill=rgba(BLUE))
def chalkboard(d, x, y, w, h):
    d.rectangle([x - 12, y - 12, x + w + 12, y + h + 12], fill=rgba((120, 85, 50)), outline=rgba(INK), width=4); d.rectangle([x, y, x + w, y + h], fill=rgba(BOARD)); d.rectangle([x, y + h + 2, x + 60, y + h + 10], fill=rgba(CHALK))
def chalk_text(d, x, y, text, prog, size=34, color=CHALK):
    if prog <= 0: return
    f = E.font("Caveat[wght].ttf", size, 600); d.text((x, y), text[:int(len(text) * min(1, prog) + 0.999)], font=f, fill=rgba(color))
def screen(d, x, y, w, h, prog=1.0):
    """the pull-down projector screen: it unrolls with `prog`"""
    d.rectangle([x - 10, y - 16, x + w + 10, y], fill=rgba((40, 40, 40))); hh = h * ease(prog); d.rectangle([x, y, x + w, y + hh], fill=rgba((250, 250, 248)), outline=rgba(INK), width=3)
    d.line([(x + w / 2, y + hh), (x + w / 2, y + hh + 24)], fill=rgba(INK), width=3); d.ellipse([x + w / 2 - 8, y + hh + 24, x + w / 2 + 8, y + hh + 40], outline=rgba(INK), width=3)
def stamp(fr, text, cx, cy, prog, angle=-14):
    if prog <= 0: return
    f = E.font("Anton-Regular.ttf", 110); t = E.text_image(text, f, RED, pad=26); d = ImageDraw.Draw(t); d.rectangle([8, 8, t.width - 9, t.height - 9], outline=rgba(RED), width=10)
    rng = np.random.default_rng(2); a = np.asarray(t).copy(); a[:, :, 3] = (a[:, :, 3] * (0.55 + 0.45 * rng.random((t.height, t.width)))).astype(np.uint8); t = Image.fromarray(a).rotate(angle, resample=Image.BICUBIC, expand=True)
    s = 1.6 - 0.6 * ease(prog); t = t.resize((int(t.width * s), int(t.height * s)), Image.BILINEAR); t.putalpha(t.getchannel("A").point(lambda v: int(v * min(1, prog * 2)))); E.paste_center(fr, t, cx, cy)
def label(fr, text, x, y, prog, size=36):
    if prog <= 0: return
    im = E.text_image(text, E.font("Nunito[wght].ttf", size, 800), INK, pad=4); im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog)))); fr.alpha_composite(im, (int(x), int(y + 10 * (1 - ease(prog)))))
def photo(name, w):
    im = Image.open(os.path.join(MEMES, name)).convert("RGBA"); im = E.fit(im, w, int(w * 0.7)); out = Image.new("RGBA", (im.width + 16, im.height + 16), (255, 255, 255, 255)); ImageDraw.Draw(out).rectangle([0, 0, out.width - 1, out.height - 1], outline=rgba(INK), width=3); out.alpha_composite(im, (8, 8)); return out

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []
    def face(a, b): S.append(dict(t0=a, t1=b, kind="face", tr="cut"))
    def g(a, b, draw): S.append(dict(t0=a, t1=b, kind="graphic", draw=draw, tr="cut", face=None))
    def pops(*ts):
        for t in ts: sfx.append((t, E.pop(0.06)))
    # 0 hook: the figure at a desk shoves a pile of data at the robot (Qdrant); on "just" the robot shows it holds more than vectors
    def g_hook(t, dur, ctx):
        fr = paper(); d = ImageDraw.Draw(fr); T = c["large"] + t; desk(d, 300, 760); monitor(d, 380, 740, min(1, t / 1.5)); figure(d, 250, 880, 1.4, "calm", arm=0.6 * inout(t / 0.6))
        n = int(40 * ease(t / 1.6)); rng = random.Random(1)
        for i in range(n):
            x = 620 + i * 14 + rng.randrange(-6, 6); y = 700 - (i % 7) * 26 - rng.randrange(0, 10); d.rectangle([x, y, x + 20, y + 20], fill=rgba(BLUE), outline=rgba(INK), width=2)
        label(fr, "a LOT of data", 640, 440, k(t, 0.3, 0.4)); robot(d, 1420, 880, 1.7, t, carry="vectors" if T < c["just"] else None)
        if T >= c["just"]:
            for i, nm in enumerate(["vectors", "payloads", "indexes"]): box(d, 1345 + (i - 1) * 165, 560 - abs(i - 1) * 30, 150, 70, nm, k(T, c["just"] + 0.1 * i, 0.4))
            label(fr, "not just vectors", 1270, 440, k(T, c["just"] + 0.3, 0.4))
        return fr
    face(c["hook_t0"], c["large"]); g(c["large"], c["list_t0"], g_hook); pops(c["large"] + 0.3, c["just"])
    # 1 the robot stacks a box per thing named
    items = [("vectors", c["list_t0"] + 0.3), ("payloads", c["payloads"]), ("indexes", c["indexes"]), ("+ more", c["much"])]
    def g_stack(t, dur, ctx):
        fr = paper(); d = ImageDraw.Draw(fr); T = c["list_t0"] + t; robot(d, 640, 880, 1.8, t, "calm"); figure(d, 1500, 880, 1.4, "happy", arm=0.3)
        for i, (nm, at) in enumerate(items): box(d, 900, 800 - i * 76, 220, 70, nm, k(T, at, 0.4), (250, 240, 210) if i < 3 else (255, 220, 160))
        label(fr, "what Qdrant handles on upload", 560, 200, k(t, 0.2, 0.4), 40); label(fr, "in the background", 1200, 300, k(T, c["background"], 0.4), 30); return fr
    g(c["list_t0"], c["cfg_t0"], g_stack); pops(*[at for _, at in items[1:]])
    # 2 one config: the projector screen with "one config", three figures with signs, the red stamp
    def g_cfg(t, dur, ctx):
        fr = paper(); d = ImageDraw.Draw(fr); T = c["cfg_t0"] + t; screen(d, 560, 140, 800, 440, k(t, 0, 0.6)); label(fr, "one config.yaml", 760, 300, k(T, c["single"] - 0.2, 0.4), 48)
        for i, (nm, at) in enumerate([("RAG app", c["works"]), ("100M points", c["works"] + 0.3), ("multi-tenant", c["works"] + 0.6)]):
            pr = k(T, at, 0.5)
            if pr > 0: x = 380 + i * 560 + 200 * (1 - ease(pr)) * (1 if i == 2 else -1); figure(d, x, 930, 1.3, ["calm", "worried", "sad"][i], arm=0.5); box(d, x + 30, 600, 190, 60, nm, pr, WHITE)
        robot(d, 1740, 920, 1.4, t, "worried" if T >= c["all"] else "calm"); stamp(fr, "ONE SIZE?", 960, 360, k(T, c["all"], 0.35)); return fr
    g(c["cfg_t0"], c["plan_t0"], g_cfg); pops(c["works"], c["works"] + 0.3, c["works"] + 0.6); sfx.append((c["all"], E.boom(0.12)))
    # 3 the plan: the presenter
    face(c["plan_t0"], c["ds_t0"])
    # 4-6 the chalkboard: the lecturer draws dense and sparse, then the graph and the index
    def g_board(t, dur, ctx):
        fr = paper(); d = ImageDraw.Draw(fr); T = c["ds_t0"] + t; chalkboard(d, 180, 120, 1180, 720); figure(d, 1620, 920, 1.4, "calm", glasses=True, arm=0.9 if (T - c["dense"]) % 2 < 1 else 0.6, lean=-0.3)
        chalk_text(d, 220, 150, "two kinds of vectors", k(t, 0.3, 0.8), 44)
        pd = k(T, c["dense"], 0.5); chalk_text(d, 220, 240, "dense", pd, 40)
        for i in range(14):
            pr = k(T, c["dense"] + 0.05 * i, 0.2)
            if pr > 0: d.rectangle([380 + i * 44, 250, 410 + i * 44, 280], fill=rgba(CHALK), outline=rgba(CHALK), width=2)
        ps = k(T, c["sparse"], 0.5); chalk_text(d, 220, 330, "sparse", ps, 40)
        for i in range(14):
            pr = k(T, c["sparse"] + 0.05 * i, 0.2)
            if pr > 0: d.rectangle([380 + i * 44, 340, 410 + i * 44, 370], fill=rgba(CHALK) if i in (2, 7, 11) else None, outline=rgba(CHALK), width=2)
        pg = k(T, c["hnsw"], 1.0)
        if pg > 0:
            pts = [(300, 520), (420, 470), (560, 540), (700, 480), (820, 580), (480, 640), (660, 680)]; ed = [(0, 1), (1, 2), (2, 3), (3, 4), (1, 5), (5, 6), (6, 2), (3, 6)]
            for j, (a, b) in enumerate(ed):
                pr = min(1, pg * 8 - j)
                if pr > 0: e = ease(pr); d.line([pts[a], (pts[a][0] + (pts[b][0] - pts[a][0]) * e, pts[a][1] + (pts[b][1] - pts[a][1]) * e)], fill=rgba(CHALK), width=3)
            for x, y in pts: d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=rgba(CHALK), width=3)
            chalk_text(d, 300, 720, "HNSW graph", k(T, c["hnsw"] + 0.5, 0.5), 36)
        pi = k(T, c["indexing"], 1.0)
        if pi > 0:
            for j in range(4): d.line([(960, 480 + j * 52), (960 + 360 * min(1, pi * 4 - j), 480 + j * 52)], fill=rgba(CHALK), width=3)
            d.line([(1080, 470), (1080, 640)], fill=rgba(CHALK), width=3)
            for j, (a, b) in enumerate([("term 3", "doc 4, 9"), ("term 7", "doc 4, 12"), ("term 10", "doc 9, 18")]): chalk_text(d, 970, 482 + j * 52, a, min(1, pi * 3 - j), 28); chalk_text(d, 1100, 482 + j * 52, b, min(1, pi * 3 - j), 28)
            chalk_text(d, 960, 720, "sparse index", k(T, c["indexing"] + 0.5, 0.5), 36)
        return fr
    g(c["ds_t0"], c["mp_t0"], g_board); pops(c["dense"], c["sparse"], c["hnsw"], c["indexing"])
    # 7 memory and performance: the robot staggers under RAM boxes, a figure runs with a stopwatch
    def g_mp(t, dur, ctx):
        fr = paper(); d = ImageDraw.Draw(fr); T = c["mp_t0"] + t; pm = k(T, c["memory"], 0.6); pp = k(T, c["perf"], 0.6)
        robot(d, 560, 900, 1.7, t, "worried" if pm > 0.5 else "calm"); top = 900 - 136 * 1.7
        for i in range(int(5 * pm)): box(d, 480, top - 60 - i * 60, 160, 56, "RAM" if i == 2 else None, 1.0, (255, 200, 190))
        label(fr, "memory", 480, 240, pm, 40)
        if pp > 0:
            figure(d, 1300 + 200 * (1 - ease(pp)), 900, 1.3, "worried", arm=0.9, lean=0.5); d.ellipse([1390, 600, 1450, 660], fill=rgba(WHITE), outline=rgba(INK), width=4); d.line([(1420, 630), (1420 + 22 * math.cos(t * 6), 630 + 22 * math.sin(t * 6))], fill=rgba(INK), width=3)
            label(fr, "performance", 1240, 330, pp, 40)
        label(fr, "...during bulk uploads", 700, 520, k(T, c["bulk"], 0.5), 36); return fr
    g(c["mp_t0"], c["ch_t0"], g_mp); pops(c["memory"], c["perf"], c["bulk"])
    # 8 chapter: presenter, then the screen pulls down with "Option 1"
    face(c["ch_t0"], c["ch_face_end"])
    def g_ch(t, dur, ctx):
        fr = paper(); d = ImageDraw.Draw(fr); screen(d, 460, 120, 1000, 560, k(t, 0, 0.7)); label(fr, "Option 1", 760, 300, k(t, 0.6, 0.4), 96); label(fr, "store dense vectors on disk", 640, 440, k(t, 0.9, 0.4), 40)
        figure(d, 1700, 930, 1.3, "happy", glasses=True, arm=0.9, lean=-0.3); return fr
    g(c["ch_face_end"], c["o1_t0"] + 0.3, g_ch); sfx.append((c["ch_face_end"], E.whoosh(0.06)))
    # 9 option 1: the robot carries boxes from the RAM shelf into the disk cylinder
    def g_disk(t, dur, ctx):
        fr = paper(); d = ImageDraw.Draw(fr); T = c["o1_t0"] + 0.3 + t
        d.rectangle([300, 520, 700, 540], fill=rgba(WOOD), outline=rgba(INK), width=4); label(fr, "RAM", 460, 370, 1.0, 36)
        d.ellipse([1300, 560, 1700, 660], fill=rgba((200, 210, 230)), outline=rgba(INK), width=4); d.rectangle([1300, 610, 1700, 860], fill=rgba((200, 210, 230))); d.line([(1300, 610), (1300, 860)], fill=rgba(INK), width=4); d.line([(1700, 610), (1700, 860)], fill=rgba(INK), width=4); d.arc([1300, 810, 1700, 910], 0, 180, fill=rgba(INK), width=4)
        label(fr, "disk", 1460, 700, 1.0, 36); mv = inout((T - c["storing"]) / 1.6)
        for i in range(4):
            f = min(1, max(0, mv * 1.6 - i * 0.2)); x = 320 + i * 95 + (1050 - i * 60) * f; y = 450 + (200 if f > 0.98 else 0) - 120 * math.sin(math.pi * min(1, f)); box(d, x, y, 80, 60, None, 1.0, (210, 225, 250))
        robot(d, 960, 900, 1.6, t, "calm"); figure(d, 200, 920, 1.3, "happy", arm=0.9 if T >= c["disk"] else 0.2); label(fr, "on_disk = True", 800, 220, k(T, c["disk"], 0.4), 44); return fr
    g(c["o1_t0"] + 0.3, t1, g_disk); pops(c["storing"], c["disk"])
    return S, sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
