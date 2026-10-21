"""DOCUMENTARY: the cinematic look of "Species | Documenting AGI" (15M views on "MIT Explains the 12 Possible
Endings for AI"), copied from the frame audit.

What the audit shows
  - archival and stock footage, letterboxed, slow push-ins, film grain, a warm desaturated grade, a vignette
  - a sentence in a white serif over dark footage, revealed word by word as it is spoken (the unread words
    sit dim on the frame)
  - "headline cards": off-white paper, a source label top left, a serif headline, and a dark-red marker swipe
    across the key word that turns it white
  - dark diagram cards: a dark shape with circled roman numerals, thin leader lines, small-caps labels
  - dark maroon charts drawn in thin lines with serif axis labels, a yellow-highlighted sentence and a
    hand-drawn arrow pointing at the thing to look at
  - a big white serif title in capitals over foggy dark footage at a chapter
  - the presenter at a desk, full frame, between sequences
  - pace: 13 hard cuts a minute, 35 visible changes a minute, most of them slow moves and word reveals;
    footage joins dissolve, cards cut, a low boom under the title
Fonts: Playfair Display for all headlines and sentences, Inter for small labels.
Footage: Prelinger Archives (public domain): "Electronic Computers Improve Management Control" (1957) and
"The Information Machine" (1958, IBM / Eames Office).
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter
import engine as E
from engine import W, H, k, ease, inout, rgba
from beats import cues, spoken
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\doc_0-41.mp4"
BG = (10, 6, 8); PAPER = (239, 233, 220); INK = (28, 24, 22); MAROON = (42, 15, 28); DRED = (110, 16, 34); YEL = (245, 211, 74); WHITE = (255, 255, 255); DIM = (255, 255, 255)
ARCH = r"C:\Users\ADMIN\camera_audit\popular\archive"
EC = os.path.join(ARCH, "electronic_computers_1957.mp4"); IM = os.path.join(ARCH, "information_machine_1958.mp4")
SERIF = "PlayfairDisplay[wght].ttf"; SANS = "Inter[opsz,wght].ttf"

def grade(fr):
    """warm, slightly desaturated, darker: the documentary grade"""
    import numpy as np
    a = np.asarray(fr.convert("RGB")).astype(np.float32); g = a.mean(axis=2, keepdims=True); a = a * 0.65 + g * 0.35
    a[..., 0] *= 1.06; a[..., 1] *= 0.97; a[..., 2] *= 0.86; a = a * 0.9
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
def footage(path, src_t0, t, dur, seed=1):
    fr = E.clip(path).frame(src_t0 + t); fr = E.cover(fr, W, H, 1.0 + 0.09 * (t / max(dur, 0.1)), 0.5, 0.45)
    fr = grade(fr); fr = E.vignette(fr, 0.75); fr = E.grain(fr, 9, int(t * 30) + seed); return E.letterbox(fr, 132)
def smallcaps(text, size=24, color=(220, 214, 200), tracking=5):
    f = E.font(SANS, size, 600); t = text.upper(); w = int(sum(E.TD.textlength(ch, font=f) + tracking for ch in t)) + 10
    im = Image.new("RGBA", (w, int(size * 1.5)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 5
    for ch in t: d.text((x, size * 1.15), ch, font=f, fill=rgba(color), anchor="ls"); x += d.textlength(ch, font=f) + tracking
    return im
def reveal(words, t, size=58, width=1500, color=WHITE, dim=0.3, swipe=None):
    """words = [(word, time)] in local time; the said words are bright, the rest dim. swipe = (word_index, t_start): a
    dark-red marker bar sweeps across that word and its text turns white"""
    f = E.font(SERIF, size, 500); lines = [[]]
    for i, (w_, tw) in enumerate(words):
        trial = " ".join(x[0] for x in lines[-1] + [(w_, tw, i)])
        if lines[-1] and E.TD.textlength(trial, font=f) > width: lines.append([])
        lines[-1].append((w_, tw, i))
    lh = int(size * 1.35); im = Image.new("RGBA", (width + 80, lh * len(lines) + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for li, ln in enumerate(lines):
        tw_ = E.TD.textlength(" ".join(x[0] for x in ln), font=f); x = (im.width - tw_) / 2; y = 20 + li * lh + size
        for w_, tw, i in ln:
            a = 1.0 if t >= tw - 0.05 else dim; ww = d.textlength(w_, font=f)
            if swipe and swipe[0] == i and t >= swipe[1]:
                p = inout((t - swipe[1]) / 0.35); d.rectangle([x - 6, y - size * 0.95, x - 6 + (ww + 12) * p, y + size * 0.3], fill=rgba(DRED))
            d.text((x, y), w_, font=f, fill=rgba(color, 255 * a), anchor="ls"); x += ww + d.textlength(" ", font=f)
    return im
def paper():
    key = "doc_paper"
    if key not in E._fc:
        import numpy as np
        rng = np.random.default_rng(7); n = rng.normal(0, 6, (H, W, 1)); base = np.array(PAPER, np.float32)[None, None, :] + n
        y = np.linspace(0, 1, H)[:, None, None]; base = base - 14 * y
        E._fc[key] = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
    return E.vignette(E._fc[key].copy(), 0.35)
def headline_card(source, text, t, swipe_word=None, swipe_at=None, size=66):
    """the news-headline card: paper, source label, serif headline; the marker swipe on one word"""
    fr = paper(); fr.alpha_composite(smallcaps(source, 26, (70, 64, 60), 6), (260, 250))
    f = E.font(SERIF, size, 600); lines = E.wrap(text, f, 1380); y = 360; d = ImageDraw.Draw(fr)
    for ln in lines:
        x = 260
        for w_ in ln.split(" "):
            ww = d.textlength(w_, font=f); col = INK
            if swipe_word and w_.strip(",.") .lower() == swipe_word.lower() and swipe_at is not None and t >= swipe_at:
                p = inout((t - swipe_at) / 0.4); d.rectangle([x - 8, y - size * 0.9, x - 8 + (ww + 16) * p, y + size * 0.3], fill=rgba(DRED))
                if p > 0.5: col = WHITE
            d.text((x, y), w_, font=f, fill=rgba(col), anchor="ls"); x += ww + d.textlength(" ", font=f)
        y += int(size * 1.4)
    date = smallcaps("qdrant.tech  /  documentation", 22, (120, 112, 104), 4); fr.alpha_composite(date, (260, y + 30))
    fr = E.grain(fr, 4, int(t * 30)); return fr
def rock(prog):
    """a dark faceted shape (the floating rock of the reference) with a red glow at its heart"""
    key = ("doc_rock", round(prog, 2))
    if key in E._fc: return E._fc[key]
    im = Image.new("RGBA", (1100, 900), (0, 0, 0, 0)); d = ImageDraw.Draw(im); rng = random.Random(3)
    pts = [(550 + 420 * math.cos(a) * (0.85 + 0.25 * rng.random()), 450 + 400 * math.sin(a) * (0.85 + 0.25 * rng.random())) for a in [i * 2 * math.pi / 14 for i in range(14)]]
    d.polygon(pts, fill=(22, 12, 18, 255))
    for i in range(14):   # facets
        a, b = pts[i], pts[(i + 1) % 14]; c = (550 + rng.randrange(-80, 80), 450 + rng.randrange(-80, 80)); v = 18 + rng.randrange(0, 22)
        d.polygon([a, b, c], fill=(v + 10, v - 4, v + 2, 255))
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse([430, 330, 670, 570], fill=(160, 30, 60, 160)); glow = glow.filter(ImageFilter.GaussianBlur(90))
    im.alpha_composite(glow); im.putalpha(im.getchannel("A").point(lambda a: int(a * prog))); E._fc[key] = im; return im
def marker(d, fr, x, y, numeral, label, prog, side=1, sub=None, color=(230, 40, 80)):
    """circled roman numeral with a leader line and a small-caps label"""
    if prog <= 0: return
    r = 26; a = int(255 * min(1, prog * 2)); d.ellipse([x - r, y - r, x + r, y + r], outline=rgba(color, a), width=3, fill=(30, 10, 18, a))
    d.text((x, y), numeral, font=E.font(SERIF, 26, 600), fill=rgba(WHITE, a), anchor="mm")
    L = 150 * ease(prog); d.line([(x + side * (r + 6), y), (x + side * (r + 6 + L), y)], fill=rgba(WHITE, a), width=2)
    if prog > 0.5:
        lab = smallcaps(label, 24, WHITE, 5); lab.putalpha(lab.getchannel("A").point(lambda v: int(v * ease((prog - 0.5) * 2)))); fr.alpha_composite(lab, (int(x + side * (r + 160) - (0 if side > 0 else lab.width)), y - 44))
        if sub:
            s = smallcaps(sub, 20, (200, 190, 180), 4); s.putalpha(s.getchannel("A").point(lambda v: int(v * ease((prog - 0.5) * 2)))); fr.alpha_composite(s, (int(x + side * (r + 160) - (0 if side > 0 else s.width)), y + 4))
def arrow_hand(d, p0, p1, prog, color=WHITE):
    """a hand-drawn curved arrow, drawing on"""
    if prog <= 0: return
    n = 40; pts = []
    for i in range(int(n * min(1, prog)) + 1):
        u = i / n; cx = (p0[0] + p1[0]) / 2 + 90; cy = min(p0[1], p1[1]) - 60
        x = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * cx + u ** 2 * p1[0]; y = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * cy + u ** 2 * p1[1]
        pts.append((x + 2 * math.sin(u * 40), y + 2 * math.cos(u * 37)))
    if len(pts) > 1: d.line(pts, fill=rgba(color), width=4, joint="curve")
    if prog >= 0.98:
        ang = math.atan2(p1[1] - pts[-3][1], p1[0] - pts[-3][0])
        for s in (-0.5, 0.5): d.line([p1, (p1[0] - 26 * math.cos(ang + s), p1[1] - 26 * math.sin(ang + s))], fill=rgba(color), width=4)
def chart_card(t, c0, c1, c2):
    """maroon chart: two lines draw on; the highlighted sentence and the hand-drawn arrow follow"""
    fr = E.blank(MAROON); d = ImageDraw.Draw(fr); fr.alpha_composite(smallcaps("memory during a bulk upload", 24, (210, 190, 196), 5), (220, 150))
    ax0, ay0, ax1, ay1 = 260, 820, 1660, 260
    for i, v in enumerate(["0", "25", "50", "75", "100 %"]):
        y = ay0 - (ay0 - ay1) * i / 4; d.line([(ax0, y), (ax1, y)], fill=(80, 40, 56, 255), width=1); d.text((ax0 - 20, y), v, font=E.font(SERIF, 22, 400), fill=(200, 180, 186), anchor="rm")
    for name, col, pts_, at in [("dense", (230, 60, 90), [0.1, 0.3, 0.55, 0.7, 0.82, 0.9, 0.95], c0), ("sparse", (110, 170, 255), [0.1, 0.2, 0.28, 0.35, 0.42, 0.5, 0.55], c1)]:
        p = ease((t - at) / 1.2)
        if p <= 0: continue
        xy = [(ax0 + (ax1 - ax0) * i / 6, ay0 - (ay0 - ay1) * v) for i, v in enumerate(pts_)]; n = int(len(xy) * p)
        if n >= 2: d.line(xy[:n], fill=rgba(col), width=4, joint="curve")
        if p >= 1: lab = smallcaps(name, 22, col, 4); fr.alpha_composite(lab, (int(xy[-1][0]) + 14, int(xy[-1][1]) - 16))
    ph = k(t, c2, 0.4)
    if ph > 0:
        f = E.font(SERIF, 44, 500); txt = "different memory and performance considerations"; tw = E.TD.textlength(txt, font=f); x, y = 420, 150 + 80
        d.rectangle([x - 16, y - 10, x - 16 + (tw + 32) * inout((t - c2) / 0.5), y + 58], fill=rgba(YEL)); d.text((x, y), txt, font=f, fill=rgba(INK, 255 * min(1, ph * 2)), anchor="lt")
        arrow_hand(d, (x + tw * 0.55, y + 80), (ax0 + (ax1 - ax0) * 0.62, ay0 - (ay0 - ay1) * 0.72 + 30), k(t, c2 + 0.5, 0.6))
    return E.grain(fr, 4, int(t * 30))
def big_title(fr, text, prog):
    f = E.font(SERIF, 150, 600); im = Image.new("RGBA", (W, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im); t = text.upper(); tr = 14
    tw = sum(d.textlength(ch, font=f) + tr for ch in t); x = (W - tw) / 2
    for ch in t: d.text((x, 200), ch, font=f, fill=rgba(WHITE), anchor="ls"); x += d.textlength(ch, font=f) + tr
    im = E.glow(im, 30, 0.6); im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog)))); fr.alpha_composite(im, (0, H // 2 - 150)); return fr

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []
    raw = lambda i: spoken(p, i)
    def face(a, b): S.append(dict(t0=a, t1=b, kind="face", tr="cut"))
    def g(a, b, draw, tr="cut"): S.append(dict(t0=a, t1=b, kind="graphic", draw=draw, tr=tr, face=None))
    # 0 hook: face, then punch cards feeding with the sentence revealing; "just" gets the marker swipe
    face(c["hook_t0"], c["large"]); w0 = raw(0); j = next(i for i, (w_, _) in enumerate(w0) if w_.lower().startswith("just"))
    def g_hook(t, dur, ctx):
        T = c["large"] + t; fr = footage(IM, 299.0, t, dur, 1) if T < c["just"] - 0.2 else footage(EC, 524.0, t, dur, 2)
        fr.alpha_composite(reveal([(w_, tw - c["large"]) for w_, tw in w0], t, 58, 1500, swipe=(j, c["just"] - c["large"] + 0.05)), ((W - 1580) // 2, H - 132 - 230)); return fr
    g(c["large"], c["list_t0"], g_hook, "dissolve"); sfx.append((c["just"], E.paper(0.05)))
    # 1 the headline card from the docs; "more" gets the swipe
    def g_card(t, dur, ctx): return headline_card("qdrant documentation", "Qdrant also handles indexing, payloads, and much more in the background.", t, "more", c["much"] - c["list_t0"] + 0.15)
    g(c["list_t0"], c["cfg_t0"], g_card, "cut"); sfx += [(c["list_t0"], E.paper(0.07)), (c["much"] + 0.15, E.paper(0.05))]
    # 2 no single configuration: the rock with three markers
    def g_rock(t, dur, ctx):
        fr = E.blank(BG); fr = E.vignette(fr, 0.3); E.paste_center(fr, rock(k(t, 0, 0.6)), W / 2, H / 2 + 40 + 10 * math.sin(t)); d = ImageDraw.Draw(fr)
        for i, (num, lab, at, x, y, side) in enumerate([("X", "RAG app", c["single"], 760, 330, -1), ("XI", "100M points", c["works"], 1180, 560, 1), ("XII", "multi-tenant", c["all"], 820, 760, -1)]):
            marker(d, fr, x, y, num, lab, k(t, at - c["cfg_t0"], 0.5), side)
        fr.alpha_composite(reveal([(w_, tw - c["cfg_t0"]) for w_, tw in raw(2)], t, 44, 1400, dim=0.3), ((W - 1480) // 2, H - 170)); return E.grain(fr, 5, int(t * 30))
    g(c["cfg_t0"], c["plan_t0"], g_rock, "dip"); sfx.append((c["cfg_t0"], E.boom(0.08)))
    for key in ("single", "works", "all"): sfx.append((c[key], E.click(0.04)))
    # 3 the plan: the presenter at the desk
    face(c["plan_t0"], c["ds_t0"])
    # 4-6 dense and sparse: a second diagram, markers I and II gain their index labels on the cue words
    def g_ds(t, dur, ctx):
        T = c["ds_t0"] + t; fr = E.blank(BG); fr = E.vignette(fr, 0.3); E.paste_center(fr, rock(k(t, 0, 0.6)), W / 2 + 200, H / 2 + 60 + 10 * math.sin(t)); d = ImageDraw.Draw(fr)
        marker(d, fr, 960, 380, "I", "dense vectors", k(T, c["dense"], 0.5), -1, "hnsw graph" if T >= c["hnsw"] else None)
        marker(d, fr, 1060, 700, "II", "sparse vectors", k(T, c["sparse"], 0.5), -1, "sparse index" if T >= c["indexing"] else None)
        lab = smallcaps("two kinds of vectors", 26, (220, 214, 200), 6); fr.alpha_composite(lab, (160, 150))
        return E.grain(fr, 5, int(t * 30))
    g(c["ds_t0"], c["mp_t0"], g_ds, "dissolve"); sfx += [(c["dense"], E.click(0.04)), (c["sparse"], E.click(0.04)), (c["hnsw"], E.click(0.04)), (c["indexing"], E.click(0.04))]
    # 7 memory and performance: the maroon chart
    g(c["mp_t0"], c["ch_t0"], lambda t, dur, ctx: chart_card(t, c["memory"] - c["mp_t0"] - 1.4, c["memory"] - c["mp_t0"] - 0.6, c["perf"] - c["mp_t0"]), "cut")
    sfx += [(c["mp_t0"], E.paper(0.06)), (c["perf"], E.click(0.05))]
    # 8 chapter: the presenter, then the big serif title over the dark machine room
    face(c["ch_t0"], c["ch_face_end"])
    def g_title(t, dur, ctx): return big_title(footage(EC, 448.0, t, dur + 1.0, 3), "option one", k(t, 0.1, 0.8))
    g(c["ch_face_end"], c["storing"] - 0.1, g_title, "dip"); sfx.append((c["ch_face_end"], E.boom(0.14)))
    # 9 option 1: the 1957 disk storage unit with the sentence revealing; "disk" gets the swipe
    w9 = raw(9); jd = next(i for i, (w_, _) in enumerate(w9) if w_.lower().startswith("disk"))
    def g_disk(t, dur, ctx):
        fr = footage(EC, 484.0, t, dur, 4)
        fr.alpha_composite(reveal([(w_, tw - (c["storing"] - 0.1)) for w_, tw in w9], t, 54, 1500, swipe=(jd, c["disk"] - (c["storing"] - 0.1) + 0.05)), ((W - 1580) // 2, H - 132 - 230)); return fr
    g(c["storing"] - 0.1, t1, g_disk, "dissolve"); sfx.append((c["disk"], E.paper(0.05)))
    return S, sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
