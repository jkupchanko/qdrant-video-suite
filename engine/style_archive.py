"""ARCHIVE: ColdFusion's look ("What is Artificial Intelligence Exactly?", 2.2M views), copied from the
frame audit.

What the audit shows
  - black; archival photographs and footage, often black and white, with a slow drift; a soft grade
  - captions and lists in a classic white book serif ("The Original 7 Aspects of A.I. (1955)", then a
    numbered list, each item on its own line, appearing one by one)
  - white document cards: a grid of portraits with names under them in a black serif
  - code on a dark editor with green annotations beside the lines
  - small tracked condensed capitals for a kicker ("THIS WAS THE SCREENPLAY IT WROTE:")
  - 10 hard cuts and 38 changes a minute: the words keep arriving while the picture holds
Fonts: Computer Modern (the book serif), Bebas Neue for the kicker, Fira Code for code.
"""
import os, math
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import engine as E
from engine import W, H, k, ease, inout, rgba
from beats import cues, spoken
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\archive_0-41.mp4"; BG = (0, 0, 0)
WHITE = (240, 238, 232); GREEN = (120, 220, 120); INK = (20, 20, 20); SERIF = "cmunrm.otf"; KICK = "BebasNeue-Regular.ttf"
ARCH = r"C:\Users\ADMIN\camera_audit\popular\archive"; EC = os.path.join(ARCH, "electronic_computers_1957.mp4"); IM = os.path.join(ARCH, "information_machine_1958.mp4"); MEMES = r"C:\Users\ADMIN\camera_audit\style\memes"

def bw(fr):
    a = np.asarray(fr.convert("RGB")).astype(np.float32); g = a.mean(axis=2, keepdims=True); a = g * np.array([1.0, 0.98, 0.94])[None, None, :] * 0.85
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
def footage(path, src_t0, t, dur, seed=1, darken=0.3):
    fr = E.clip(path).frame(src_t0 + t); fr = E.cover(fr, W, H, 1.0 + 0.06 * (t / max(dur, 0.1)), 0.5, 0.45); fr = bw(fr); fr = Image.blend(fr, E.blank(BG), darken); fr = E.vignette(fr, 0.6); return E.grain(fr, 7, int(t * 30) + seed)
def serif(text, size=48, color=WHITE): return E.text_image(text, E.font(SERIF, size), color, pad=8)
def kicker(text, size=34, color=WHITE, tracking=6):
    f = E.font(KICK, size); t = text.upper(); w = int(sum(E.TD.textlength(ch, font=f) + tracking for ch in t)) + 10; im = Image.new("RGBA", (w, int(size * 1.4)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 5
    for ch in t: d.text((x, size * 1.1), ch, font=f, fill=rgba(color), anchor="ls"); x += d.textlength(ch, font=f) + tracking
    return im
def fade(im, prog):
    if prog <= 0 or im is None: return None
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog)))); return im
def numbered_list(fr, title, items, cues_, T, x=120, y=200):
    ti = fade(serif(title, 62), k(T, cues_[0] - 0.5, 0.5)); fr.alpha_composite(ti, (x, y)) if ti else None
    for i, (txt, at) in enumerate(zip(items, cues_)):
        im = fade(serif(f"{i + 1}  {txt}", 40), k(T, at, 0.5)); fr.alpha_composite(im, (x + 10, y + 110 + i * 64)) if im else None
def document_card(entries, prog, title=None):
    """white card: a row of photos with serif names under them"""
    if prog <= 0: return None
    cw, pw, ph_ = 300, 250, 280; w = cw * len(entries) + 100; h = 60 + ph_ + 90 + (90 if title else 0); im = Image.new("RGBA", (w, h), (255, 255, 255, 255)); d = ImageDraw.Draw(im); y0 = 50 + (90 if title else 0)
    if title: d.text((w / 2, 56), title, font=E.font(SERIF, 44), fill=rgba(INK), anchor="mm"); d.line([(50, 98), (w - 50, 98)], fill=rgba(INK), width=2)
    for i, (name, img) in enumerate(entries):
        x = 50 + i * cw + (cw - pw) // 2; ph = bw(E.cover(img, pw, ph_)); im.alpha_composite(ph, (x, y0)); d.rectangle([x, y0, x + pw, y0 + ph_], outline=rgba(INK), width=2)
        d.text((x + pw / 2, y0 + ph_ + 44), name, font=E.font(SERIF, 34), fill=rgba(INK), anchor="mm")
    im = E.grain(im, 3, 1); im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog)))); return im
def code_panel(lines, annos, prog):
    """dark editor with line numbers; annos = {line_index: text} in green beside the line"""
    if prog <= 0: return None
    f = E.font("FiraCode[wght].ttf", 36, 450); w, h = 1500, 70 + 62 * len(lines); im = Image.new("RGBA", (w, h), (24, 26, 30, 255)); d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        y = 30 + i * 62; d.text((30, y), str(i + 1), font=E.font("FiraCode[wght].ttf", 28, 400), fill=(90, 95, 105)); d.text((90, y), ln, font=f, fill=(225, 225, 230))
        if i in annos and annos[i]: tw = d.textlength(ln, font=f); d.line([(100 + tw + 20, y + 22), (100 + tw + 60, y + 22)], fill=rgba(GREEN), width=2); d.text((100 + tw + 72, y), annos[i], font=E.font(SERIF, 34), fill=rgba(GREEN))
    im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog)))); return im

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []
    photos = {n: Image.open(os.path.join(MEMES, n)).convert("RGBA") for n in ("datacenter.jpg", "ram.jpg", "traffic.jpg", "catalog.jpg", "lanes.jpg")}
    def face(a, b): S.append(dict(t0=a, t1=b, kind="face", tr="cut"))
    def g(a, b, draw, tr="dip"): S.append(dict(t0=a, t1=b, kind="graphic", draw=draw, tr=tr, face=None))
    # 0 hook: punch-card footage, the serif title, the kicker on "just"
    face(c["hook_t0"], c["large"])
    def g_hook(t, dur, ctx):
        fr = footage(IM, 299.0, t, dur, 1); T = c["large"] + t; ti = fade(serif("Bulk Uploads", 110), k(t, 0.1, 0.6)); E.paste_center(fr, ti, W / 2, 400) if ti else None
        kk = fade(kicker("A LOT of data, into Qdrant", 40), k(t, 0.5, 0.5)); E.paste_center(fr, kk, W / 2, 520) if kk else None
        kj = fade(kicker("it does not just store vectors", 40), k(T, c["just"], 0.5)); E.paste_center(fr, kj, W / 2, 600) if kj else None; return fr
    g(c["large"], c["list_t0"], g_hook); sfx.append((c["large"], E.boom(0.06)))
    # 1 the numbered list over dark machine-room footage
    def g_list(t, dur, ctx):
        fr = footage(EC, 448.0, t, dur, 2, 0.6); T = c["list_t0"] + t; numbered_list(fr, "What Qdrant does on every upload", ["Stores the vectors.", "Stores and indexes the payloads.", "Builds the vector indexes.", "Optimises, merges, writes the log... and much more."], [c["list_t0"] + 0.3, c["payloads"], c["indexes"], c["much"]], T); return fr
    g(c["list_t0"], c["cfg_t0"], g_list)
    for at in (c["payloads"], c["indexes"], c["much"]): sfx.append((at, E.click(0.03)))
    # 2 one configuration? the document card with three workloads, the kicker
    def g_cfg(t, dur, ctx):
        fr = E.blank(BG); T = c["cfg_t0"] + t; ti = fade(serif("One configuration for every workload?", 54), k(T, c["single"] - 0.3, 0.5)); E.paste_center(fr, ti, W / 2, 150) if ti else None
        card = document_card([("RAG app", photos["catalog.jpg"]), ("100M points", photos["datacenter.jpg"]), ("multi-tenant", photos["lanes.jpg"])], k(T, c["works"], 0.6), "Three workloads"); E.paste_center(fr, card, W / 2, 520) if card else None
        kk = fade(kicker("there is no single answer", 44), k(T, c["all"], 0.5)); E.paste_center(fr, kk, W / 2, 900) if kk else None; return fr
    g(c["cfg_t0"], c["plan_t0"], g_cfg); sfx.append((c["works"], E.paper(0.05)))
    # 3 the plan: the presenter
    face(c["plan_t0"], c["ds_t0"])
    # 4-6 dense and sparse: the code panel with green annotations arriving on the cue words
    LINES = ["vectors_config = VectorParams(", "    size=768,", "    hnsw_config=HnswConfig(m=16),", ")", "sparse_vectors_config = SparseVectorParams(", "    index=SparseIndexParams(),", ")"]
    def g_ds(t, dur, ctx):
        fr = E.blank(BG); T = c["ds_t0"] + t; annos = {}
        if T >= c["dense"]: annos[0] = "the dense vector"
        if T >= c["hnsw"]: annos[2] = "its HNSW graph"
        if T >= c["sparse"]: annos[4] = "the sparse vector"
        if T >= c["indexing"]: annos[5] = "a separate sparse index"
        pn = code_panel(LINES, annos, k(t, 0.2, 0.5)); fr.alpha_composite(pn, (210, 220)) if pn else None
        kk = fade(kicker("indexed completely differently", 40), k(T, c["indexing"] + 0.5, 0.5)); E.paste_center(fr, kk, W / 2, 860) if kk else None; return fr
    g(c["ds_t0"], c["mp_t0"], g_ds)
    for at in (c["dense"], c["hnsw"], c["sparse"], c["indexing"]): sfx.append((at, E.click(0.03)))
    # 7 memory and performance: the sentence revealing over footage of the tape drives
    w7 = spoken(p, 7)
    def g_mp(t, dur, ctx):
        fr = footage(EC, 484.0, t, dur, 3, 0.45); T = c["mp_t0"] + t; said = " ".join(w_ for w_, tw in w7 if tw <= T + 0.05)
        f = E.font(SERIF, 46); lines = E.wrap(said, f, 1400)
        for i, ln in enumerate(lines[-4:]): im = serif(ln, 46); E.paste_center(fr, im, W / 2, 700 + i * 64)
        kk = fade(kicker("memory  /  performance", 36), k(T, c["memory"], 0.5)); E.paste_center(fr, kk, W / 2, 200) if kk else None; return fr
    g(c["mp_t0"], c["ch_t0"], g_mp)
    # 8-9 chapter and option 1: serif title over the disk unit, the kicker on "disk"
    face(c["ch_t0"], c["ch_face_end"])
    def g_o1(t, dur, ctx):
        fr = footage(EC, 524.0, t, dur, 4, 0.4); T = c["ch_face_end"] + t; ti = fade(serif("Option 1", 120), k(t, 0.1, 0.6)); E.paste_center(fr, ti, W / 2, 360) if ti else None
        sub = fade(serif("Store the original dense vectors on disk.", 48), k(T, c["storing"], 0.5)); E.paste_center(fr, sub, W / 2, 500) if sub else None
        kk = fade(kicker("on_disk = true", 44), k(T, c["disk"], 0.5)); E.paste_center(fr, kk, W / 2, 620) if kk else None; return fr
    g(c["ch_face_end"], t1, g_o1); sfx.append((c["ch_face_end"], E.boom(0.08)))
    return S, sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
