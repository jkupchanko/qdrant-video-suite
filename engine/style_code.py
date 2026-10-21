"""CODE: CodeAesthetic's look ("Why You Shouldn't Nest Your Code", 3.4M views), copied from the frame audit.

What the audit shows
  - a flat dark grey (#1C1D20); nothing else on screen but type, code and one small prop
  - headings in a light humanist sans: a small line above ("A confession"), a big line below with the
    key phrase in lavender ("I'm a Never Nester")
  - code in a monospace with soft colours: parameters coral, types and calls white, numbers blue; the
    block sits centred and is edited in place: lines slide, a translucent bar highlights the line
    being talked about, the rest dims
  - the "disgust-o-meter": a small outlined tube with two dots at the bottom, filling green to red
  - a chapter card: a muted purple band across the middle with the title and a wireframe solid
  - "Methods to Denest": a mono heading with the accent word, list items with stacked coloured cubes
  - almost nothing cuts (0.2 hard cuts, 0.6 changes a minute); everything slides, fades or morphs
Fonts: Inter 300 and 400 for the sans, Fira Code for code.
"""
import os, math
from PIL import Image, ImageDraw
import engine as E
from engine import W, H, k, ease, inout, rgba
from beats import cues
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\code_0-41.mp4"; BG = (28, 29, 32)
WHITE = (236, 236, 240); LAV = (186, 150, 230); CORAL = (232, 120, 110); BLUEC = (130, 180, 235); GREENC = (150, 200, 120); DIM = (110, 112, 120); PURPLE = (108, 66, 118); GREEN = (178, 196, 78); YEL = (220, 170, 70); RED = (210, 80, 80)
MONO = "FiraCode[wght].ttf"; SANS = "Inter[opsz,wght].ttf"

def sans(text, size, weight=300, color=WHITE): return E.text_image(text, E.font(SANS, size, weight), color, pad=6)
def heading(small, big, accent, prog_small, prog_big, cx=960, y=300):
    """the two-line heading: a small line, then the big line with `accent` in lavender"""
    im = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    if prog_small > 0: s = sans(small, 40, 300); s.putalpha(s.getchannel("A").point(lambda a: int(a * ease(prog_small)))); im.alpha_composite(s, (int(cx - 700), 20))
    if prog_big > 0:
        before, after = big.split("{}") if "{}" in big else (big, ""); f = E.font(SANS, 96, 300); parts = [(before, WHITE), (accent, LAV), (after, WHITE)]
        ims = [E.text_image(t, f, c, pad=4) for t, c in parts if t]; tw = sum(i.width for i in ims); x = cx - 700
        row = Image.new("RGBA", (tw + 20, max(i.height for i in ims)), (0, 0, 0, 0)); xx = 0
        for i in ims: row.alpha_composite(i, (xx, 0)); xx += i.width
        row.putalpha(row.getchannel("A").point(lambda a: int(a * ease(prog_big)))); im.alpha_composite(row, (int(x), int(90 + 18 * (1 - ease(prog_big)))))
    return im
def code_block(lines, hi=None, dim_others=False, n_chars=None, size=34, prog=1.0, slide_in=None):
    """lines = [(text, tokens)] where tokens = [(str, color)]; hi = index of the highlighted line; slide_in = {index: prog}"""
    slide_in = slide_in or {}; f = E.font(MONO, size, 450); lh = int(size * 1.7); w = 1400; im = Image.new("RGBA", (w, lh * len(lines) + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im); shown = 0
    for i, toks in enumerate(lines):
        y = 20 + i * lh; sp = slide_in.get(i, 1.0); xoff = int(60 * (1 - ease(sp))); a_line = ease(sp)
        if hi == i and sp >= 1: d.rounded_rectangle([0, y - 8, w, y + lh - 14], radius=8, fill=(255, 255, 255, 22))
        x = 40 + xoff
        for tok, col in toks:
            if n_chars is not None:
                tok = tok[:max(0, n_chars - shown)]; shown += len(tok)
            c = DIM if (dim_others and hi is not None and hi != i) else col; d.text((x, y), tok, font=f, fill=rgba(c, 255 * a_line)); x += d.textlength(tok, font=f)
        if n_chars is not None: shown += 1
    if prog < 1: im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog))))
    return im
def meter(value, prog=1.0, label="work-o-meter"):
    """the small tube: outline, fill from the bottom coloured by value, two dots, label under"""
    if prog <= 0: return None
    w, h = 90, 230; im = Image.new("RGBA", (w + 200, h + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x0 = 100
    d.rounded_rectangle([x0, 0, x0 + w, h], radius=10, outline=rgba(WHITE), width=4)
    v = max(0.03, min(1, value)); col = GREEN if v < 0.45 else (YEL if v < 0.75 else RED); fh = int((h - 16) * v)
    d.rounded_rectangle([x0 + 8, h - 8 - fh, x0 + w - 8, h - 8], radius=6, fill=rgba(col)); d.ellipse([x0 + 22, h - 38, x0 + 36, h - 24], fill=rgba(WHITE)); d.ellipse([x0 + 54, h - 38, x0 + 68, h - 24], fill=rgba(WHITE))
    l = sans(label, 22, 400, WHITE); im.alpha_composite(l, (x0 + w // 2 - l.width // 2, h + 14)); im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog)))); return im
def card(title, accent, prog, t):
    """the purple band with the title and a slowly turning wireframe tetrahedron"""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); e = ease(prog); bw = int(1280 * e); d.rectangle([W // 2 - bw // 2, 180, W // 2 + bw // 2, 900], fill=rgba(PURPLE))
    if e > 0.6:
        a = (e - 0.6) / 0.4; f = E.font(SANS, 96, 300); t1 = E.text_image(title + " ", f, WHITE, pad=4); t2 = E.text_image(accent, f, LAV, pad=4); row = Image.new("RGBA", (t1.width + t2.width, t1.height), (0, 0, 0, 0)); row.alpha_composite(t1, (0, 0)); row.alpha_composite(t2, (t1.width, 0))
        row.putalpha(row.getchannel("A").point(lambda v: int(v * a))); E.paste_center(im, row, W / 2, 460)
        ang = t * 0.6; cx, cy = W / 2 + 40, 700; r = 90
        pts3 = [(0, -1, 0), (0.94, 0.33, 0), (-0.47, 0.33, 0.82), (-0.47, 0.33, -0.82)]; proj = []
        for x, y, z in pts3:
            xr, zr = x * math.cos(ang) - z * math.sin(ang), x * math.sin(ang) + z * math.cos(ang); proj.append((cx + xr * r * 1.4, cy + y * r * 0.9 + zr * 20))
        for i in range(4):
            for j in range(i + 1, 4): d.line([proj[i], proj[j]], fill=rgba((230, 220, 240), 255 * a), width=3)
    return im
def cubes(n, colors):
    im = Image.new("RGBA", (40, 22 * n + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(n): d.rectangle([6 + (i % 2) * 8, 4 + i * 22, 26 + (i % 2) * 8, 24 + i * 22], fill=rgba(colors[i % len(colors)]))
    return im

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []
    def face(a, b): S.append(dict(t0=a, t1=b, kind="face", tr="cut"))
    def g(a, b, draw, tr="dissolve"): S.append(dict(t0=a, t1=b, kind="graphic", draw=draw, tr=tr, face=None))
    T = lambda t, a: a + t
    UP = [[("client", WHITE), (".upload_points(", WHITE)], [("    collection_name", CORAL), ("=", WHITE), ('"my_collection"', GREENC), (",", WHITE)], [("    points", CORAL), ("=", WHITE), ("points", WHITE), (",   ", WHITE), ("# 1,000,000", DIM)], [(")", WHITE)]]
    # 0 hook: heading, then the upload call typing in; "just storing vectors" accented
    face(c["hook_t0"], c["large"])
    def g_hook(t, dur, ctx):
        fr = E.blank(BG); Tt = T(t, c["large"]); fr.alpha_composite(heading("A bulk upload", "not just {}", "storing vectors", k(t, 0, 0.6), k(Tt, c["just"] - 0.2, 0.6)), (0, 160))
        n = int(sum(len(tok) for ln in UP for tok, _ in ln) * min(1, (Tt - c["large"] - 0.2) / 1.6)); fr.alpha_composite(code_block(UP, None, False, n), (260, 540)); return fr
    g(c["large"], c["list_t0"], g_hook)
    # 1 what happens on upload: lines slide in one per word, highlighted as said, the meter rises
    WORK = [[("store", WHITE), ("(", WHITE), ("vectors", CORAL), (")", WHITE)], [("store", WHITE), ("(", WHITE), ("payloads", CORAL), (")", WHITE)], [("build_index", WHITE), ("(", WHITE), ("hnsw", CORAL), (", ", WHITE), ("payload_fields", CORAL), (")", WHITE)], [("optimize_segments", WHITE), ("()", WHITE), ("   ", WHITE), ("# ...and more, in the background", DIM)]]
    ats = [c["list_t0"] + 0.3, c["payloads"], c["indexes"], c["much"]]
    def g_work(t, dur, ctx):
        fr = E.blank(BG); Tt = T(t, c["list_t0"]); fr.alpha_composite(heading("on every upload, Qdrant", "does {}", "all of this", k(t, 0, 0.6), k(t, 0.3, 0.6)), (0, 120))
        shown = [ln for ln, at in zip(WORK, ats) if Tt >= at]; sl = {i: k(Tt, ats[i], 0.5) for i in range(len(shown))}; hi = len(shown) - 1 if shown else None
        if shown: fr.alpha_composite(code_block(shown, hi, True, None, 34, 1.0, sl), (260, 480))
        m = meter(0.15 + 0.2 * len(shown) + (0.15 if Tt >= c["background"] else 0), k(t, 0.2, 0.5)); fr.alpha_composite(m, (1480, 500)) if m else None; return fr
    g(c["list_t0"], c["cfg_t0"], g_work)
    for at in ats[1:]: sfx.append((at, E.click(0.03)))
    # 2 one config for every workload? the config block, three workloads cycle through it, meter goes red
    CFG = [[("config", WHITE), (" = ", WHITE), ("VectorParams", BLUEC), ("(", WHITE)], [("    size", CORAL), ("=", WHITE), ("768", BLUEC), (",", WHITE)], [("    distance", CORAL), ("=", WHITE), ("Distance.COSINE", BLUEC), (",", WHITE)], [(")", WHITE)]]
    loads = ["RAG app", "100M points", "multi-tenant"]
    def g_cfg(t, dur, ctx):
        fr = E.blank(BG); Tt = T(t, c["cfg_t0"]); fr.alpha_composite(heading("one configuration", "for {}", "every workload?", k(Tt, c["single"] - 0.3, 0.6), k(Tt, c["single"], 0.6)), (0, 120))
        fr.alpha_composite(code_block(CFG, None, False, None, 34, k(t, 0.2, 0.5)), (260, 480))
        for i, name in enumerate(loads):
            pr = k(Tt, c["works"] + 0.3 * i, 0.4)
            if pr > 0: lab = sans(name, 34, 400, WHITE if Tt < c["all"] else DIM); lab.putalpha(lab.getchannel("A").point(lambda a: int(a * ease(pr)))); fr.alpha_composite(lab, (1420, 500 + i * 70))
        px = k(Tt, c["all"], 0.4); m = meter(0.3 + 0.65 * px, k(t, 0.2, 0.5)); fr.alpha_composite(m, (1480, 720)) if m else None
        if px > 0: ln = sans("one size does not fit all", 30, 300, LAV); ln.putalpha(ln.getchannel("A").point(lambda a: int(a * px))); fr.alpha_composite(ln, (260, 820))
        return fr
    g(c["cfg_t0"], c["plan_t0"], g_cfg)
    # 3 the plan: the presenter
    face(c["plan_t0"], c["ds_t0"])
    # 4-6 dense and sparse: two blocks side by side; the index line of each highlights on its cue word
    DENSE = [[("VectorParams", BLUEC), ("(", WHITE)], [("    size", CORAL), ("=", WHITE), ("768", BLUEC), (",", WHITE)], [("    hnsw_config", CORAL), ("=", WHITE), ("HnswConfig", BLUEC), ("(m=", WHITE), ("16", BLUEC), ("),", WHITE)], [(")", WHITE)]]
    SPARSE = [[("SparseVectorParams", BLUEC), ("(", WHITE)], [("    modifier", CORAL), ("=", WHITE), ("Modifier.IDF", BLUEC), (",", WHITE)], [("    index", CORAL), ("=", WHITE), ("SparseIndexParams", BLUEC), ("(),", WHITE)], [(")", WHITE)]]
    def g_ds(t, dur, ctx):
        fr = E.blank(BG); Tt = T(t, c["ds_t0"]); fr.alpha_composite(heading("two kinds of vectors", "{} and sparse", "dense", k(t, 0.3, 0.6), k(Tt, c["dense"] - 0.2, 0.6)), (0, 100))
        hd = 2 if Tt >= c["hnsw"] else None; hs = 2 if Tt >= c["indexing"] else None
        cb = code_block(DENSE, hd, hd is not None, None, 28, k(Tt, c["dense"], 0.5)); fr.alpha_composite(cb.crop((0, 0, 900, cb.height)), (140, 460))
        cb2 = code_block(SPARSE, hs, hs is not None, None, 28, k(Tt, c["sparse"], 0.5)); fr.alpha_composite(cb2.crop((0, 0, 900, cb2.height)), (1000, 460))
        for x, txt, at in ((190, "HNSW graph", c["hnsw"]), (1050, "sparse index", c["indexing"])):
            pr = k(Tt, at + 0.3, 0.4)
            if pr > 0: l = sans(txt, 30, 400, LAV); l.putalpha(l.getchannel("A").point(lambda a: int(a * pr))); fr.alpha_composite(l, (x, 760))
        return fr
    g(c["ds_t0"], c["mp_t0"], g_ds); sfx += [(c["hnsw"], E.click(0.03)), (c["indexing"], E.click(0.03))]
    # 7 memory and performance: the "Methods to Denest" list with cube bullets and a meter each
    def g_mp(t, dur, ctx):
        fr = E.blank(BG); Tt = T(t, c["mp_t0"]); f = E.font(MONO, 64, 450); h1 = E.text_image("Different ", f, WHITE, pad=4); h2 = E.text_image("costs", f, LAV, pad=4); pr0 = k(t, 0.2, 0.6)
        row = Image.new("RGBA", (h1.width + h2.width, h1.height), (0, 0, 0, 0)); row.alpha_composite(h1, (0, 0)); row.alpha_composite(h2, (h1.width, 0)); row.putalpha(row.getchannel("A").point(lambda a: int(a * pr0))); fr.alpha_composite(row, (420, 220))
        for i, (txt, at, val, cols) in enumerate([("memory", c["memory"], 0.85, (LAV, BLUEC)), ("performance", c["perf"], 0.55, (CORAL, GREENC))]):
            pr = k(Tt, at, 0.5)
            if pr <= 0: continue
            y = 400 + i * 150; cb = cubes(2 + i, cols); l = E.text_image(txt, E.font(MONO, 48, 450), WHITE, pad=4); l.putalpha(l.getchannel("A").point(lambda a: int(a * ease(pr)))); fr.alpha_composite(cb, (470, y)); fr.alpha_composite(l, (540, y - 8))
            m = meter(val * ease((Tt - at) / 1.0), 1.0, ""); fr.alpha_composite(m, (1180 + i * 260, 400))
        pb = k(Tt, c["bulk"], 0.5)
        if pb > 0: ln = sans("...and they change during bulk uploads", 34, 300, WHITE); ln.putalpha(ln.getchannel("A").point(lambda a: int(a * pb))); fr.alpha_composite(ln, (470, 760))
        return fr
    g(c["mp_t0"], c["ch_t0"], g_mp); sfx += [(c["memory"], E.click(0.03)), (c["perf"], E.click(0.03))]
    # 8 chapter: presenter, then the purple band
    face(c["ch_t0"], c["ch_face_end"])
    g(c["ch_face_end"], c["o1_t0"] + 0.4, lambda t, dur, ctx: (lambda fr: (fr.alpha_composite(card("Option", "1", k(t, 0, 0.7), t)), fr)[1])(E.blank(BG)), "cut")   # a cut, not a dissolve: the look-away starts 0.35 s in
    # 9 option 1: the config block; on_disk slides in and takes the highlight on "disk"; the meter drops
    DISK = CFG[:3] + [[("    on_disk", CORAL), ("=", WHITE), ("True", BLUEC), (",", WHITE)], [(")", WHITE)]]
    def g_disk(t, dur, ctx):
        fr = E.blank(BG); Tt = T(t, c["o1_t0"] + 0.4); fr.alpha_composite(heading("option 1", "store the {}", "original vectors on disk", k(t, 0, 0.6), k(Tt, c["storing"], 0.6)), (0, 120))
        ps = k(Tt, c["disk"] - 0.4, 0.5); lines = DISK if ps > 0 else CFG; sl = {3: ps} if ps > 0 else {}; hi = 3 if Tt >= c["disk"] else None
        fr.alpha_composite(code_block(lines, hi, hi is not None, None, 34, k(t, 0.1, 0.5), sl), (260, 480)); m = meter(0.85 - 0.6 * k(Tt, c["disk"], 0.8), k(t, 0.2, 0.5), "RAM"); fr.alpha_composite(m, (1480, 500)) if m else None; return fr
    g(c["o1_t0"] + 0.4, t1, g_disk); sfx.append((c["disk"], E.click(0.03)))
    return S, sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
