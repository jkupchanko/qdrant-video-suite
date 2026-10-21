"""GLOSSY: Dan Martell's look ("You're Not Behind (Yet): How to Build Your First AI Agent", 0.8M; "How to
learn AI in 18 minutes", 3.1M), copied from the frame audit.

What the audit shows
  - the presenter in a warm wood studio, large; graphics appear beside him or take the frame on near-black
  - a title in a white italic serif ("How to Build an AI Agent"); a tree of dark glass boxes with a cyan
    rim-light glow and numbered nodes, which builds and then zooms to the branch in play
  - big dark glass letter cards with a glowing letter ("D A T A"), one per word of an acronym
  - a flow panel: a black card with rounded outlined steps, icons, a red end box
  - lists as dark rounded bars: a cyan number, white bold text, the first letter in cyan
  - 17 hard cuts and 21 changes a minute
Fonts: Playfair Display Italic for titles, Inter 700 for the rest.
"""
import os, math
from PIL import Image, ImageDraw, ImageFilter
import engine as E
from engine import W, H, k, ease, back, rgba
from beats import cues
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\glossy_0-41.mp4"; BG = (6, 8, 14)
WHITE = (255, 255, 255); CYAN = (80, 210, 255); GLASS = (14, 22, 40); GLASS_EDGE = (40, 90, 150); RED = (170, 20, 40); ICONS = r"C:\Users\ADMIN\camera_audit\popular\icons"
SERIF_I = "PlayfairDisplay-Italic[wght].ttf"

def _serif_italic():
    p = os.path.join(E.FONTS, SERIF_I)
    if not os.path.exists(p):
        import urllib.request; urllib.request.urlretrieve("https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/PlayfairDisplay-Italic%5Bwght%5D.ttf", p)
    return SERIF_I
def title(text, prog, size=64):
    if prog <= 0: return None
    im = E.text_image(text, E.font(_serif_italic(), size, 500), WHITE, pad=10); im = E.glow(im, 14, 0.5); im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog)))); return im
def glass(w, h, prog=1.0, glow=True):
    """a dark glass card with a cyan rim glow"""
    pad = 40; im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if glow: g = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle([pad, pad, pad + w, pad + h], radius=14, outline=rgba(CYAN, 200), width=6); im.alpha_composite(g.filter(ImageFilter.GaussianBlur(14)))
    d.rounded_rectangle([pad, pad, pad + w, pad + h], radius=14, fill=rgba(GLASS, 235), outline=rgba(GLASS_EDGE), width=2); d.line([(pad + 14, pad + 1), (pad + w - 14, pad + 1)], fill=rgba(CYAN, 160), width=2)
    if prog < 1: im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog))))
    return im
def node(fr, cx, cy, text, prog, w=260, h=70, num=None):
    if prog <= 0: return
    im = glass(w, h, prog); d = ImageDraw.Draw(im); f = E.font("Inter[opsz,wght].ttf", 26, 700)
    if num: d.rounded_rectangle([40 + 10, 40 + 12, 40 + 56, 40 + h - 12], radius=8, fill=rgba(WHITE)); d.text((40 + 33, 40 + h / 2), str(num), font=f, fill=rgba(GLASS), anchor="mm"); d.text((40 + 72, 40 + h / 2), text, font=f, fill=rgba(WHITE), anchor="lm")
    else: d.text((40 + w / 2, 40 + h / 2), text, font=f, fill=rgba(WHITE), anchor="mm")
    E.paste_center(fr, im, cx, cy)
def link(d, a, b, prog):
    if prog <= 0: return
    e = ease(prog); d.line([a, (a[0], a[1] + (b[1] - a[1]) * 0.5 * e)], fill=rgba(CYAN, 180), width=3)
    if e > 0.5: d.line([(a[0], (a[1] + b[1]) / 2), (b[0], (a[1] + b[1]) / 2)], fill=rgba(CYAN, 180), width=3); d.line([(b[0], (a[1] + b[1]) / 2), (b[0], (a[1] + b[1]) / 2 + (b[1] - (a[1] + b[1]) / 2) * (e - 0.5) * 2)], fill=rgba(CYAN, 180), width=3)
def letter_card(ch, label, prog, size=240):
    if prog <= 0: return None
    im = glass(size, size, 1.0, True); d = ImageDraw.Draw(im); t = E.text_image(ch, E.font("Inter[opsz,wght].ttf", 150, 700), CYAN, pad=4); t = E.glow(t, 18, 0.9); E.paste_center(im, t, 40 + size / 2, 40 + size / 2)
    if label:
        l = E.text_image(label, E.font("Inter[opsz,wght].ttf", 26, 700), WHITE, pad=2); out = Image.new("RGBA", (im.width, im.height + 50), (0, 0, 0, 0)); out.alpha_composite(im, (0, 0)); E.paste_center(out, l, im.width / 2, im.height + 20); im = out
    s = 0.85 + 0.15 * ease(prog); im = im.resize((int(im.width * s), int(im.height * s)), Image.BILINEAR); im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog)))); return im
def list_bar(text, num, prog, w=700):
    if prog <= 0: return None
    im = glass(w, 90, 1.0, False); d = ImageDraw.Draw(im); f = E.font("Inter[opsz,wght].ttf", 40, 700); d.text((40 + 36, 40 + 45), str(num), font=f, fill=rgba(CYAN), anchor="lm"); d.line([(40 + 90, 40 + 22), (40 + 90, 40 + 68)], fill=rgba(GLASS_EDGE), width=2)
    x = 40 + 112; d.text((x, 40 + 45), text[0], font=f, fill=rgba(CYAN), anchor="lm"); x += d.textlength(text[0], font=f); d.text((x, 40 + 45), text[1:], font=f, fill=rgba(WHITE), anchor="lm")
    im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog)))); return im
def flow_panel(steps, prog, cur, w=560):
    """the black panel with outlined steps; the last step is red"""
    if prog <= 0: return None
    h = 110 + 90 * len(steps); im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.rounded_rectangle([0, 0, w - 1, h - 1], radius=12, fill=(10, 10, 14, 245), outline=(120, 120, 130, 255), width=2)
    d.text((w / 2, 46), "UPLOAD", font=E.font("Inter[opsz,wght].ttf", 34, 700), fill=rgba(WHITE), anchor="mm")
    for i, (icon, text) in enumerate(steps):
        y = 100 + i * 90; on = i <= cur; col = RED if i == len(steps) - 1 and on else ((30, 30, 36) if on else (18, 18, 22))
        d.rounded_rectangle([70, y, w - 70, y + 64], radius=8, fill=rgba(col), outline=rgba((200, 200, 210) if on else (70, 70, 80)), width=2)
        ic = E.svg_image(os.path.join(ICONS, icon), 34, "#ffffff" if on else "#555566"); im.alpha_composite(ic, (96, y + 15)); d.text((150, y + 32), text, font=E.font("Inter[opsz,wght].ttf", 26, 600), fill=rgba(WHITE if on else (90, 90, 100)), anchor="lm")
        if i < len(steps) - 1: d.line([(w / 2, y + 66), (w / 2, y + 88)], fill=rgba((200, 200, 210) if on else (70, 70, 80)), width=2)
    im = E.shadowed(im, 20, (0, 10), 180); im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog)))); return im
def dark(face_im, amount=0.75): return Image.blend(face_im, E.blank(BG), amount)

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []
    def face(a, b, draw=None): S.append(dict(t0=a, t1=b, kind="face", draw=draw, tr="cut"))
    def g(a, b, draw, tr="dissolve"): S.append(dict(t0=a, t1=b, kind="graphic", draw=draw, tr=tr, face=None))
    def pops(*ts):
        for t in ts: sfx.append((t, E.click(0.05)))
    # 0 hook: face, then the title and the first glass nodes
    def ov_hook(t, dur, ctx):
        T = t0 + t; ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ti = title("Bulk Uploads to Qdrant", k(T, c["large"] - 0.2, 0.5), 72); ov.alpha_composite(ti, (W // 2 - ti.width // 2, 96)) if ti else None; return ov
    face(c["hook_t0"], c["just"] - 0.2, ov_hook)
    # 1 the tree: a root and four numbered nodes, one per word
    def g_tree(t, dur, ctx):
        fr = E.blank(BG); d = ImageDraw.Draw(fr); T = c["just"] - 0.2 + t; ti = title("What happens on upload", k(t, 0, 0.5)); fr.alpha_composite(ti, (W // 2 - ti.width // 2, 70)) if ti else None
        node(fr, 960, 260, "NOT JUST VECTORS", k(T, c["just"], 0.4), 420, 80)
        for i, (nm, at) in enumerate([("Vectors", c["list_t0"] + 0.2), ("Payloads", c["payloads"]), ("Indexes", c["indexes"]), ("Much more", c["much"])]):
            x = 420 + i * 360; pr = k(T, at, 0.4); link(d, (960, 300), (x, 440), pr); node(fr, x, 480, nm, pr, 300, 76, i + 1)
        pb = k(T, c["background"], 0.4)
        if pb > 0: l = E.text_image("...in the background", E.font("Inter[opsz,wght].ttf", 30, 600), CYAN, pad=4); l.putalpha(l.getchannel("A").point(lambda a: int(a * pb))); E.paste_center(fr, l, 960, 640)
        return fr
    g(c["just"] - 0.2, c["cfg_t0"], g_tree); pops(c["just"], c["payloads"], c["indexes"], c["much"])
    # 2 one config? three letter cards W-H-Y? Better: the flow panel beside the face: one config -> three workloads -> END (red)
    STEPS = [("lucide_file-json.svg", "one configuration"), ("lucide_layers.svg", "RAG app"), ("lucide_database.svg", "100M points"), ("lucide_network.svg", "multi-tenant"), ("lucide_x.svg", "does not fit")]
    def ov_cfg(t, dur, ctx):
        T = c["cfg_t0"] + t; ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cur = sum(1 for at in (c["single"], c["works"], c["works"] + 0.3, c["works"] + 0.6, c["all"]) if T >= at) - 1
        pn = flow_panel(STEPS, k(T, c["single"] - 0.3, 0.5), cur); ov.alpha_composite(pn, (1240, 120)) if pn else None; return ov
    face(c["cfg_t0"], c["plan_t0"], ov_cfg); pops(c["single"], c["works"], c["all"])
    # 3 the plan: the list bars
    def g_plan(t, dur, ctx):
        fr = E.blank(BG); T = c["plan_t0"] + t; ti = title("The Plan", k(t, 0.2, 0.5)); fr.alpha_composite(ti, (W // 2 - ti.width // 2, 80)) if ti else None
        for i, (txt, at) in enumerate([("Four options", c["options"]), ("Three best practices", c["best"])]):
            b = list_bar(txt, i + 1, k(T, at, 0.4), 820)
            if b: E.paste_center(fr, b, 960, 300 + i * 130)
        return fr
    g(c["plan_t0"], c["ds_t0"], g_plan); pops(c["options"], c["best"])
    # 4-6 dense and sparse: two big letter cards, their index labels arrive on the cue words
    def g_ds(t, dur, ctx):
        fr = E.blank(BG); T = c["ds_t0"] + t; ti = title("The Anatomy of a Vector", k(t, 0.3, 0.5)); fr.alpha_composite(ti, (W // 2 - ti.width // 2, 70)) if ti else None
        a = letter_card("D", "DENSE" + ("  -  HNSW graph" if T >= c["hnsw"] else ""), k(T, c["dense"], 0.5)); E.paste_center(fr, a, 640, 520) if a else None
        b = letter_card("S", "SPARSE" + ("  -  sparse index" if T >= c["indexing"] else ""), k(T, c["sparse"], 0.5)); E.paste_center(fr, b, 1280, 520) if b else None
        pr = k(T, c["indexing"] + 0.5, 0.4)
        if pr > 0: l = E.text_image("indexed completely differently", E.font("Inter[opsz,wght].ttf", 32, 600), CYAN, pad=4); l.putalpha(l.getchannel("A").point(lambda a_: int(a_ * pr))); E.paste_center(fr, l, 960, 860)
        return fr
    g(c["ds_t0"], c["mp_t0"], g_ds); pops(c["dense"], c["sparse"], c["hnsw"], c["indexing"])
    # 7 memory and performance: face with two list bars beside it
    def ov_mp(t, dur, ctx):
        T = c["mp_t0"] + t; ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for i, (txt, at) in enumerate([("Memory", c["memory"]), ("Performance", c["perf"])]):
            b = list_bar(txt, i + 1, k(T, at, 0.4), 520)
            if b: ov.alpha_composite(b, (1300, 200 + i * 130))
        pb = k(T, c["bulk"], 0.4)
        if pb > 0: ti = title("during bulk uploads", pb, 40); ov.alpha_composite(ti, (1340, 480))
        return ov
    face(c["mp_t0"], c["ch_face_end"], ov_mp); pops(c["memory"], c["perf"], c["bulk"])
    # 8-9 chapter and option 1: the title, the tree zooms to branch 1, the node for on_disk
    def g_o1(t, dur, ctx):
        fr = E.blank(BG); d = ImageDraw.Draw(fr); T = c["ch_face_end"] + t; ti = title("Option 1", k(t, 0.1, 0.5), 96); fr.alpha_composite(ti, (W // 2 - ti.width // 2, 120)) if ti else None
        node(fr, 960, 360, "Store dense vectors on disk", k(t, 0.6, 0.5), 620, 80, 1)
        pr = k(T, c["storing"], 0.5); link(d, (960, 400), (640, 540), pr); link(d, (960, 400), (1280, 540), pr); node(fr, 640, 580, "RAM: search structures", pr, 440, 76); node(fr, 1280, 580, "Disk: original vectors", pr, 440, 76)
        pd = k(T, c["disk"], 0.4)
        if pd > 0: b = list_bar("on_disk = True", 1, pd, 520); E.paste_center(fr, b, 960, 780)
        return fr
    g(c["ch_face_end"], t1, g_o1, "cut"); sfx += [(c["ch_face_end"], E.whoosh(0.05)), (c["storing"], E.click(0.05)), (c["disk"], E.click(0.05))]
    return S, sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
