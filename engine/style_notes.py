"""NOTES: Tina Huang's look ("Google's 9 Hour AI Prompt Engineering Course In 20 Minutes", 2.2M views;
"AI Agents Fundamentals", 1.6M), copied from the frame audit.

What the audit shows
  - the presenter large, in a dark room with a lit shelf behind; the frame darkens behind graphics
  - illustrated app tiles: a rounded square on a pale blue, a label under it on a white strip in bold black
    ("Prompts for emailing"); three or four pop in across the top as the list is said
  - a ChatGPT / notes window on screen: dark theme, a markdown list typing itself, the input bar at the
    bottom; a web page with one row lifted and the rest dimmed
  - a big bottom caption whose first letters are coloured to spell an acronym
  - 15 hard cuts and 24 changes a minute
Fonts: Inter 700 for labels, Inter 400 for the document.
"""
import os, math
from PIL import Image, ImageDraw, ImageFilter
import engine as E
from engine import W, H, k, ease, back, rgba
from beats import cues
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\notes_0-41.mp4"; BG = (16, 16, 20)
WHITE = (255, 255, 255); INK = (18, 18, 20); TILE = (208, 222, 250); ICON = (60, 90, 170); DOC = (33, 33, 36); DOC_TXT = (236, 236, 240); DOC_DIM = (150, 150, 160); ACC = [(255, 80, 80), (255, 170, 40), (80, 200, 120), (80, 160, 255), (200, 100, 255)]
ICONS = r"C:\Users\ADMIN\camera_audit\popular\icons"; BROLL = r"C:\Users\ADMIN\camera_audit\full\broll"; EDIT_BR = r"C:\Users\ADMIN\camera_audit\edit\broll"
INSET = ("inset", (W - 60 - 420, H - 60 - 315, 420, 315), 18)

def tile(icon, label, prog):
    if prog <= 0: return None
    im = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.rounded_rectangle([40, 10, 260, 200], radius=28, fill=rgba(TILE))
    ic = E.svg_image(os.path.join(ICONS, icon), 110, "#3c5aaa"); E.paste_center(im, ic, 150, 105)
    f = E.font("Inter[opsz,wght].ttf", 30, 700); t = E.text_image(label, f, INK, pad=6); strip = Image.new("RGBA", (t.width + 20, t.height + 8), (255, 255, 255, 255)); strip.alpha_composite(t, (10, 4)); E.paste_center(im, strip, 150, 245)
    s = 0.7 + 0.3 * back(prog); im = im.resize((int(300 * s), int(300 * s)), Image.BILINEAR); im.putalpha(im.getchannel("A").point(lambda a: int(a * min(1, prog * 3)))); return im
def dim(face_im, amount=0.55): return Image.blend(face_im, E.blank(BG), amount)
def doc_window(lines, n_chars, w=1180, h=820, title="Notes"):
    """a dark document window; lines = [(text, kind)] kind: h (heading) | b (bullet) | p; typed to n_chars"""
    im = Image.new("RGBA", (w, h), rgba(DOC)); d = ImageDraw.Draw(im); d.rounded_rectangle([0, 0, w - 1, h - 1], radius=16, fill=rgba(DOC), outline=(70, 70, 76, 255), width=2)
    d.text((28, 22), title, font=E.font("Inter[opsz,wght].ttf", 22, 600), fill=rgba(DOC_DIM)); y = 80; shown = 0
    for text, kind in lines:
        vis = text[:max(0, n_chars - shown)]; shown += len(text) + 1
        if not vis: break
        if kind == "h": d.text((40, y), vis, font=E.font("Inter[opsz,wght].ttf", 34, 700), fill=rgba(DOC_TXT)); y += 56
        elif kind == "b": d.ellipse([52, y + 14, 60, y + 22], fill=rgba(DOC_TXT)); d.text((78, y), vis, font=E.font("Inter[opsz,wght].ttf", 28, 400), fill=rgba(DOC_TXT)); y += 44
        else: d.text((40, y), vis, font=E.font("Inter[opsz,wght].ttf", 26, 400), fill=rgba(DOC_DIM)); y += 40
    d.rounded_rectangle([28, h - 76, w - 28, h - 24], radius=14, fill=(48, 48, 52, 255)); d.text((48, h - 60), "Message", font=E.font("Inter[opsz,wght].ttf", 22, 400), fill=rgba(DOC_DIM)); d.ellipse([w - 72, h - 66, w - 40, h - 34], fill=rgba(WHITE))
    return E.shadowed(im, 24, (0, 16), 160)
def acronym_caption(words, colors, prog):
    """bottom caption on one baseline, each word's first letter in a colour"""
    if prog <= 0: return None
    f = E.font("Inter[opsz,wght].ttf", 50, 700); text = " ".join(words); w = int(E.TD.textlength(text, font=f)) + 40; im = Image.new("RGBA", (w, 90), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 20
    for w_, c in zip(words, colors):
        d.text((x, 62), w_[0], font=f, fill=rgba(c), anchor="ls", stroke_width=3, stroke_fill=(0, 0, 0, 255)); x += d.textlength(w_[0], font=f)
        d.text((x, 62), w_[1:] + " ", font=f, fill=rgba(WHITE), anchor="ls", stroke_width=3, stroke_fill=(0, 0, 0, 255)); x += d.textlength(w_[1:] + " ", font=f)
    im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog)))); return im
def spotlight(frame, box, prog):
    """a page with one box lifted: the rest dims, the box gets a white edge and a shadow"""
    fr = E.cover(frame, W, H); dimmed = Image.blend(fr, E.blank((0, 0, 0)), 0.6 * ease(prog)); x0, y0, x1, y1 = box; crop = fr.crop(box)
    card = Image.new("RGBA", (x1 - x0 + 16, y1 - y0 + 16), (255, 255, 255, 255)); card.alpha_composite(crop, (8, 8)); card = E.shadowed(card, 24, (0, 12), 180); dimmed.alpha_composite(card, (x0 - 8 - 72, y0 - 8 - 72)); return dimmed

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []
    vt = E.clip(os.path.join(EDIT_BR, "vector_type_shot.mp4")); s1 = E.clip(os.path.join(BROLL, "s1_shot.mp4"))
    def face(a, b, draw=None): S.append(dict(t0=a, t1=b, kind="face", draw=draw, tr="cut"))
    def g(a, b, draw, face_=INSET): S.append(dict(t0=a, t1=b, kind="graphic", draw=draw, tr="cut", face=face_, face_border=(WHITE, 3)))
    def pops(*ts):
        for t in ts: sfx.append((t, E.pop(0.06)))
    # 0-1 hook and list: the face, tiles popping across the top on each word
    tiles = [("lucide_layers.svg", "Vectors", c["list_t0"] + 0.2), ("lucide_file-json.svg", "Payloads", c["payloads"]), ("lucide_git-branch.svg", "Indexes", c["indexes"]), ("lucide_cpu.svg", "+ more", c["much"])]
    def ov_hook(t, dur, ctx):
        T = t0 + t; ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if c["large"] <= T < c["just"]:
            cap = acronym_caption(["A", "LOT", "of", "data"], [ACC[0], ACC[1], WHITE, ACC[3]], k(T, c["large"], 0.3)); ov.alpha_composite(cap, (W // 2 - cap.width // 2, H - 180)) if cap else None
        for i, (ic, lab, at) in enumerate(tiles):
            tl = tile(ic, lab, k(T, at, 0.4))
            if tl: E.paste_center(ov, tl, (230, 230, 1690, 1690)[i], (240, 560, 240, 560)[i])
        if T >= c["just"] and T < c["list_t0"]:
            cap = acronym_caption(["Not", "just", "storing", "vectors"], [ACC[0], ACC[1], ACC[2], ACC[3]], k(T, c["just"], 0.3)); ov.alpha_composite(cap, (W // 2 - cap.width // 2, H - 180)) if cap else None
        return ov
    def ov_hook_dim(t, dur, ctx):
        """the face dims behind the tiles once they are up"""
        return ov_hook(t, dur, ctx)
    face(c["hook_t0"], c["cfg_t0"], ov_hook); pops(c["large"], c["just"], *[at for _, _, at in tiles])
    # 2 one config? the notes window types the three workloads, the inset face
    LINES = [("One configuration for every workload?", "h"), ("RAG app: small, filtered, latency matters", "b"), ("100M points: huge, dense, memory matters", "b"), ("Multi-tenant: many small collections", "b"), ("", "p"), ("There is no single answer.", "p")]
    def g_cfg(t, dur, ctx):
        fr = E.blank(BG); T = c["cfg_t0"] + t; n = int(max(0, T - c["single"] + 0.4) * 40); fr.alpha_composite(doc_window(LINES, n, title="ChatGPT"), (120 - 72, 110 - 72)); return fr
    g(c["cfg_t0"], c["plan_t0"], g_cfg); sfx.append((c["cfg_t0"], E.whoosh(0.05)))
    # 3 the plan: face with two tiles
    def ov_plan(t, dur, ctx):
        T = c["plan_t0"] + t; ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); tl = tile("lucide_list-checks.svg", "4 options", k(T, c["options"], 0.4)); E.paste_center(ov, tl, 230, 240) if tl else None
        tl2 = tile("lucide_zap.svg", "3 best practices", k(T, c["best"], 0.4)); E.paste_center(ov, tl2, 1690, 240) if tl2 else None; return ov
    face(c["plan_t0"], c["ds_t0"], ov_plan); pops(c["options"], c["best"])
    # 4-6 dense and sparse: the docs page with the paragraph spotlit, then the notes window with the two index lines
    def g_ds(t, dur, ctx):
        T = c["ds_t0"] + t
        if T < c["hnsw"] - 0.3: fr = spotlight(vt.frame(t), (560, 300, 1420, 620), k(T, c["dense"], 0.5)); return fr
        LN = [("Two kinds of vectors", "h"), ("Dense: every dimension has a value -> HNSW graph index", "b"), ("Sparse: mostly zeros -> a separate sparse (inverted) index", "b"), ("", "p"), ("Indexed completely differently.", "p")]
        n = 20 + int(max(0, T - c["hnsw"] + 0.3) * 38); fr = E.blank(BG); fr.alpha_composite(doc_window(LN, n), (120 - 72, 110 - 72)); return fr
    g(c["ds_t0"], c["mp_t0"], g_ds); sfx.append((c["hnsw"] - 0.3, E.whoosh(0.05)))
    # 7 memory and performance: face with the acronym caption and two tiles
    def ov_mp(t, dur, ctx):
        T = c["mp_t0"] + t; ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        tl = tile("lucide_memory-stick.svg", "Memory", k(T, c["memory"], 0.4)); E.paste_center(ov, tl, 230, 240) if tl else None; tl2 = tile("lucide_gauge.svg", "Performance", k(T, c["perf"], 0.4)); E.paste_center(ov, tl2, 1690, 240) if tl2 else None
        cap = acronym_caption(["During", "Bulk", "Uploads"], [ACC[0], ACC[1], ACC[3]], k(T, c["bulk"], 0.3)); ov.alpha_composite(cap, (W // 2 - cap.width // 2, H - 180)) if cap else None; return ov
    face(c["mp_t0"], c["ch_face_end"], ov_mp); pops(c["memory"], c["perf"], c["bulk"])
    # 8-9 chapter and option 1: the Option 1 docs page spotlit, inset face; the caption on "disk"
    def g_o1(t, dur, ctx):
        T = c["ch_face_end"] + t; fr = spotlight(s1.frame(t), (560, 330, 1420, 700), k(T, c["storing"], 0.5)); cap = acronym_caption(["Option", "1:", "on", "disk"], [ACC[0], WHITE, WHITE, ACC[3]], k(T, c["disk"] - 0.2, 0.3))
        if cap: fr.alpha_composite(cap, (W // 2 - cap.width // 2 - 200, H - 180))
        return fr
    g(c["ch_face_end"], t1, g_o1, None if True else INSET); S[-1]["face"] = None
    S.append(dict(t0=c["o1_t0"] + 0.2, t1=t1, kind="graphic", draw=g_o1, tr="cut", face=INSET, face_border=(WHITE, 3))); S[-2]["t1"] = c["o1_t0"] + 0.2
    sfx += [(c["ch_face_end"], E.whoosh(0.05)), (c["disk"], E.pop(0.06))]
    return S, sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
