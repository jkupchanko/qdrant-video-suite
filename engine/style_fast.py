"""FAST: Fireship's look (Code Report; 1.1M to 3M views a video), copied from the frame audit of
"Vector databases are so hot right now. WTF are they?"

What the audit shows
  - a flat near-black background (15, 13, 23); no grid, no texture
  - one big thing per frame, centred: a logo with its wordmark, a line of heavy rounded uppercase text with
    a dark outline and shadow, a screenshot, an emoji used as a prop, a point cloud, a code editor
  - bright green chips with black text for numbers and verdicts ("28M", "REKTOR")
  - arrays and values in a monospace font with the numbers in yellow
  - a pointing-hand emoji next to the line of code that matters
  - pop-culture stills and meme photos as reactions
  - 13 hard cuts and 31 visible changes a minute: something new every two seconds, nothing fades
  - no presenter on screen (voice-over); here the face is kept only for the opening second and the
    "let's get started" beat so the video is still recognisably John's
Fonts: Fredoka 700 (the rounded heavy sans) for all headings, Fira Code for arrays and code.
"""
import os, math, random
from PIL import Image, ImageDraw
import engine as E
from engine import W, H, k, ease, back, rgba
from beats import cues
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\fast_0-41.mp4"
BG = (15, 13, 23); GREEN = (118, 255, 128); YEL = (255, 222, 89); WHITE = (255, 255, 255); INK = (12, 12, 16)
EMO = r"C:\Users\ADMIN\camera_audit\popular\emoji"; MEMES = r"C:\Users\ADMIN\camera_audit\style\memes"; EDIT_BR = r"C:\Users\ADMIN\camera_audit\edit\broll"
LOGO = r"C:\Users\ADMIN\camera_audit\assets\qdrant-logo-red-white.png"

def big(text, size=96, color=WHITE):
    return E.text_image(text.upper(), E.font("Fredoka[wdth,wght].ttf", size, 700), color, outline=max(3, size // 22), outline_color=INK, shadow=(6, 0, 10, 200), pad=24)
def chip(text, size=72, color=GREEN):
    t = E.text_image(text.upper(), E.font("Fredoka[wdth,wght].ttf", size, 700), INK, pad=10)
    im = Image.new("RGBA", (t.width + 40, t.height + 18), (0, 0, 0, 0)); ImageDraw.Draw(im).rectangle([0, 0, im.width - 1, im.height - 1], fill=rgba(color)); im.alpha_composite(t, (20, 9)); return im
def mono(text, size=54, numbers=YEL):
    """monospace text with digits in yellow, drawn on one baseline"""
    f = E.font("FiraCode[wght].ttf", size, 500); w = int(E.TD.textlength(text, font=f)) + 20; im = Image.new("RGBA", (w, int(size * 1.5)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 10
    for ch in text:
        d.text((x, size * 1.1), ch, font=f, fill=rgba(numbers if ch.isdigit() or ch in ".-" else WHITE), anchor="ls"); x += d.textlength(ch, font=f)
    return im
def emoji(code, size): return E.svg_image(os.path.join(EMO, code + ".svg"), size)
def snap(im, prog, cx, cy, fr):
    """a hard pop: 0.9 -> 1 scale over 0.12 s, no fade"""
    if prog <= 0: return
    s = 0.9 + 0.1 * min(1, prog / 0.12 * 0.12 / 0.12) if prog < 0.12 else 1.0
    if s != 1.0: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
    E.paste_center(fr, im, cx, cy)
def shot(im, prog): return im if prog > 0 else None
def point_cloud(seed=1, n=420):
    """coloured digit tiles in a blob, like the MNIST embedding frame"""
    key = ("cloud", seed)
    if key in E._fc: return E._fc[key]
    rng = random.Random(seed); im = Image.new("RGBA", (900, 700), (0, 0, 0, 0)); d = ImageDraw.Draw(im); f = E.font("FiraCode[wght].ttf", 22, 700)
    cols = [(255, 95, 180), (80, 190, 255), (90, 230, 200), (255, 180, 70), (170, 120, 255), (200, 200, 210)]
    for i in range(n):
        a = rng.random() * 2 * math.pi; r = 300 * math.sqrt(rng.random()); g = rng.randrange(6)
        cx = 450 + r * math.cos(a) * 1.3 + 70 * math.cos(g * 1.1); cy = 350 + r * math.sin(a) * 0.9 + 60 * math.sin(g * 1.7)
        d.rectangle([cx - 13, cy - 13, cx + 13, cy + 13], fill=rgba(cols[g])); d.text((cx, cy), str(g), font=f, fill=INK, anchor="mm")
    E._fc[key] = im; return im
def graph(prog, seed=4):
    """an HNSW-looking graph: white nodes, coloured edges drawing on"""
    rng = random.Random(seed); pts = [(rng.randrange(80, 1120), rng.randrange(60, 560)) for _ in range(22)]
    im = Image.new("RGBA", (1200, 620), (0, 0, 0, 0)); d = ImageDraw.Draw(im); edges = []
    for i, a in enumerate(pts):
        for j in sorted(range(22), key=lambda j: (pts[j][0] - a[0]) ** 2 + (pts[j][1] - a[1]) ** 2)[1:3]: edges.append((i, j))
    n_show = int(len(edges) * min(1, prog * 1.3))
    for e, (i, j) in enumerate(edges[:n_show]): d.line([pts[i], pts[j]], fill=rgba((80, 190, 255) if e % 3 else (255, 95, 180)), width=6)
    for i, (x, y) in enumerate(pts):
        if prog > i / 30: d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=(255, 255, 255, 255), outline=rgba(INK), width=4)
    return im
def screenshot(frame, w=1500, prog=1.0):
    im = E.cover(frame, w, int(w * 9 / 16)); im.putalpha(E.rounded_mask(im.width, im.height, 14)); return E.shadowed(im, 24, (0, 16), 200)
CODE = "vectors_config=models.VectorParams(\n    size=768,\n    distance=models.Distance.COSINE,\n    on_disk=True,\n)"
def code_card(n_chars, hand=False):
    """a VS Code-like editor card; the hand points at on_disk=True"""
    cw, ch = 1500, 720; im = Image.new("RGBA", (cw, ch), (30, 30, 36, 255)); d = ImageDraw.Draw(im); f = E.font("FiraCode[wght].ttf", 40, 500)
    d.rectangle([0, 0, cw, 56], fill=(40, 40, 48, 255)); d.text((28, 16), "JS  upload.py", font=E.font("Inter[opsz,wght].ttf", 24, 600), fill=(170, 170, 180))
    shown = 0; y = 110
    for i, ln in enumerate(CODE.split("\n")):
        vis = ln[:max(0, n_chars - shown)]; shown += len(ln) + 1; x = 60; d.text((x - 30, y), str(i + 1), font=E.font("FiraCode[wght].ttf", 26, 400), fill=(90, 90, 100), anchor="rm")
        for tok in __import__("re").findall(r"\s+|[A-Za-z_][A-Za-z_0-9]*|\d+|.", vis):
            col = (230, 230, 240)
            if tok.isdigit(): col = (255, 222, 89)
            elif tok in ("True", "False"): col = (255, 120, 170)
            elif tok[:1].isupper(): col = (120, 220, 255)
            elif tok in "=(),.": col = (170, 178, 190)
            d.text((x, y), tok, font=f, fill=col); x += d.textlength(tok, font=f)
        y += 72
    im.putalpha(E.rounded_mask(cw, ch, 14)); im = E.shadowed(im, 24, (0, 16), 200)
    if hand:
        line_y = 110 + 3 * 72; hnd = emoji("1f449", 150).transpose(Image.FLIP_LEFT_RIGHT)   # points left, at the on_disk line
        im.alpha_composite(hnd, (72 + 540, 72 + int(line_y - 50)))
    return im

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []; logo = Image.open(LOGO).convert("RGBA"); logo = E.fit(logo, 900, 260)
    def face(a, b): S.append(dict(t0=a, t1=b, kind="face", tr="cut"))
    def g(a, b, draw): S.append(dict(t0=a, t1=b, kind="graphic", draw=draw, tr="cut", face=None)); sfx.append((a, E.pop(0.10)))
    def pops(*ts):
        for t in ts: sfx.append((t, E.pop(0.08)))
    # 0 hook
    face(c["hook_t0"], c["large"])
    def g_logo(t, dur, ctx):
        fr = E.blank(BG); snap(logo, 1, W / 2, 420, fr); ch = chip("1,000,000+ points"); snap(ch, k(t, 0.9, 0.12), W / 2, 640, fr); return fr
    g(c["large"], c["just"], g_logo); pops(c["large"] + 0.9)
    def g_just(t, dur, ctx):
        fr = E.blank(BG); snap(emoji("1f914", 300), 1, 560, H / 2, fr); snap(big("just storing vectors?", 84), 1, 1180, H / 2, fr); return fr
    g(c["just"], c["list_t0"], g_just)
    # 1 payloads, indexes, much more: a new centred element on each word
    def g_payload(t, dur, ctx):
        fr = E.blank(BG); snap(big("payloads", 110), 1, W / 2, 380, fr); snap(mono('{"color": "red", "price": 9.99}', 54), k(t, 0.25, 0.12), W / 2, 580, fr); return fr
    def g_index(t, dur, ctx):
        fr = E.blank(BG); snap(point_cloud(), 1, 1200, 560, fr); snap(big("indexes", 110), 1, 520, 440, fr); return fr
    def g_more(t, dur, ctx):
        fr = E.blank(BG); snap(big("...and much more", 96), 1, W / 2, 460, fr); snap(emoji("1f525", 200), k(t, 0.3, 0.12), W / 2, 700, fr); return fr
    g(c["list_t0"], c["payloads"], lambda t, d, x: E.blank(BG)) if False else None
    g(c["list_t0"], c["indexes"], g_payload); g(c["indexes"], c["much"], g_index); g(c["much"], c["cfg_t0"], g_more); pops(c["list_t0"] + 0.25, c["much"] + 0.3)
    # 2 no single config
    def g_one(t, dur, ctx):
        fr = E.blank(BG); snap(big("one config", 120), 1, W / 2, 440, fr); snap(chip("for everything?", 64), k(t, 0.5, 0.12), W / 2, 640, fr); return fr
    def g_nope(t, dur, ctx):
        fr = E.blank(BG); snap(emoji("274c", 260), 1, 620, H / 2, fr); snap(big("nope.", 160), 1, 1180, H / 2, fr); return fr
    g(c["cfg_t0"], c["all"], g_one); g(c["all"], c["plan_t0"], g_nope); pops(c["cfg_t0"] + 0.5)
    # 3 the plan: face, then two lines stacking
    face(c["plan_t0"], c["options"] - 0.1)
    def g_plan(t, dur, ctx):
        fr = E.blank(BG); snap(big("4 options", 120), 1, W / 2, 400, fr); snap(big("3 best practices", 96, GREEN), k(t, c["best"] - c["options"] + 0.1, 0.12), W / 2, 600, fr)
        snap(emoji("1f680", 160), k(t, 2.0, 0.12), W / 2, 820, fr); return fr
    g(c["options"] - 0.1, c["ds_t0"], g_plan); pops(c["best"], c["options"] + 1.9)
    # 4-6 dense vs sparse, then HNSW, then the sparse index
    def g_ds(t, dur, ctx):
        fr = E.blank(BG); snap(big("dense vector", 84), 1, W / 2, 250, fr); snap(mono("[0.12, -0.87, 0.33, 0.91, 0.04, ...]", 50), 1, W / 2, 380, fr)
        ps = k(t, c["sparse"] - c["dense"], 0.12); snap(big("sparse vector", 84), ps, W / 2, 640, fr); snap(mono("{12: 0.9, 77: 0.6, 301: 0.8}", 50), ps, W / 2, 770, fr); return fr
    g(c["ds_t0"], c["dense"], lambda t, d, x: __import__("PIL.Image").Image.new("RGBA", (W, H), rgba(BG))) if False else None
    face(c["ds_t0"], c["dense"]); g(c["dense"], c["hnsw_t0"] + 0.4, g_ds); pops(c["sparse"])
    def g_hnsw(t, dur, ctx):
        fr = E.blank(BG); snap(graph(k(t, c["hnsw"] - c["hnsw_t0"] - 0.4, 1.0)), 1, W / 2, 400, fr)
        snap(big("HNSW", 150), k(t, c["hnsw"] - c["hnsw_t0"] - 0.4, 0.12), W / 2, 800, fr); snap(chip("blazingly fast", 56), k(t, c["hnsw"] - c["hnsw_t0"] + 0.4, 0.12), W / 2, 940, fr); return fr
    g(c["hnsw_t0"] + 0.4, c["sparse2"], g_hnsw); pops(c["hnsw"], c["hnsw"] + 0.8)
    rows = ["term 12  -> doc 4, doc 9, doc 31", "term 77  -> doc 4, doc 12", "term 301 -> doc 9, doc 18, doc 77"]
    def g_sparse(t, dur, ctx):
        fr = E.blank(BG); snap(big("sparse index", 110), 1, W / 2, 300, fr)
        for i, r in enumerate(rows): snap(mono(r, 48), k(t, c["indexing"] - c["sparse2"] + 0.25 * i, 0.12), W / 2, 480 + i * 90, fr)
        return fr
    g(c["sparse2"], c["mp_t0"], g_sparse); pops(c["indexing"], c["indexing"] + 0.25, c["indexing"] + 0.5)
    # 7 memory and performance: docs screenshot, chips, then the meme
    vt = os.path.join(EDIT_BR, "vector_type_shot.mp4")
    def g_docs(t, dur, ctx):
        fr = E.blank(BG); fr.alpha_composite(screenshot(E.clip(vt).frame(0.0), 1400), ((W - 1400) // 2 - 72, 40 - 72))
        snap(chip("memory", 64), k(t, c["memory"] - c["mp_t0"], 0.12), 620, 950, fr); snap(chip("performance", 64), k(t, c["perf"] - c["mp_t0"], 0.12), 1250, 950, fr); return fr
    g(c["mp_t0"], c["bulk"], g_docs); pops(c["memory"], c["perf"])
    meme = Image.open(os.path.join(MEMES, "this_is_fine.jpg")).convert("RGBA")
    def g_meme(t, dur, ctx):
        fr = E.blank(BG); im = E.fit(meme, 1300, 760); im.putalpha(E.rounded_mask(im.width, im.height, 10)); E.paste_center(fr, im, W / 2, 440)
        snap(big("your RAM during a bulk upload", 64), 1, W / 2, 900, fr); return fr
    g(c["bulk"], c["ch_t0"], g_meme)
    # 8 chapter: face, then a "1 WEEK AGO..."-style card typing itself
    face(c["ch_t0"], c["ch_face_end"])
    def g_ch(t, dur, ctx):
        fr = E.blank(BG); txt = "option 1..."[:int(t * 14) + 1]; snap(big(txt, 150), 1, W / 2, H / 2, fr); return fr
    g(c["ch_face_end"], c["o1_t0"] + 0.1, g_ch)
    # 9 option 1: the editor types the config; the hand points at on_disk=True on "disk"
    def g_code(t, dur, ctx):
        fr = E.blank(BG); n = int(len(CODE) * min(1, t / 1.1)); fr.alpha_composite(code_card(n, hand=t >= c["disk"] - c["o1_t0"] - 0.1), ((W - 1500) // 2 - 72, 120 - 72))
        snap(big("on_disk=true", 80, GREEN), k(t, c["disk"] - c["o1_t0"] - 0.1, 0.12), W / 2, 980, fr); return fr
    g(c["o1_t0"] + 0.1, t1, g_code); pops(c["disk"])
    return [s for s in S if s is not None], sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
