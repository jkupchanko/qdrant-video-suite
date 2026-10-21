"""STUDIO: the clean professional look of Jeff Su's AI explainers (5.4M, 3.9M, 3.6M views), copied from the
frame audit of "99% of Beginners Don't Know the Basics of AI".

What the audit shows
  - graphics sit on near-black charcoal (#121212) with a faint dot grid
  - headings: condensed, bold, italic, UPPERCASE, white; one sentence under them in a regular sans with one
    phrase in blue; centred title cards ("3 TYPES OF AI TOOLS / #1") between sections
  - app-icon tiles (rounded squares holding a logo) pop in one by one into rows as each tool is named
  - screen recordings sit in a large rounded window with a soft shadow
  - the presenter stays on screen: full frame between graphics, and in a rounded rectangle at the bottom
    left (about 29% wide) while a graphic is up
  - captions on face shots: a white rounded box, black text, one phrase highlighted with a marker
  - a green stat with an arrow ("13% up") for numbers
  - pace: 7.6 hard cuts a minute, 12 visible changes a minute; a graphic holds for several seconds
Fonts: Oswald 700 (sheared 12 degrees for the italic) for headings, Inter for everything else.
"""
import os, math
from PIL import Image, ImageDraw
import engine as E
from engine import W, H, k, ease, back, rgba
from beats import cues
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\studio_0-41.mp4"
BG = (18, 18, 18); BLUE = (74, 140, 255); GREEN = (74, 222, 128); WHITE = (255, 255, 255); GREY = (160, 160, 168); MARK = (217, 249, 96)
ICONS = r"C:\Users\ADMIN\camera_audit\popular\icons"; BROLL = r"C:\Users\ADMIN\camera_audit\full\broll"; EDIT_BR = r"C:\Users\ADMIN\camera_audit\edit\broll"
INSET = ("inset", (60, H - 60 - 315, 560, 315), 24)

def heading(text, size=64):
    im = E.text_image(text.upper(), E.font("Oswald[wght].ttf", size, 700), WHITE, pad=20)
    return im.transform((im.width + int(im.height * 0.21), im.height), Image.AFFINE, (1, -0.21, 0, 0, 1, 0), Image.BICUBIC)   # italic shear
def subline(parts, size=34):
    """parts = [(text, color)] on one line"""
    f = E.font("Inter[opsz,wght].ttf", size, 500); ims = [E.text_image(t, f, c, pad=4) for t, c in parts]
    out = Image.new("RGBA", (sum(i.width for i in ims), max(i.height for i in ims)), (0, 0, 0, 0)); x = 0
    for i in ims: out.alpha_composite(i, (x, 0)); x += i.width
    return out
def canvas():
    key = "studio_bg"
    if key not in E._fc:
        im = E.blank(BG); d = ImageDraw.Draw(im)
        for x in range(40, W, 44):
            for y in range(40, H, 44): d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(44, 44, 48, 255))
        E._fc[key] = im
    return E._fc[key].copy()
def tile(icon, label, size=150, prog=1.0, fill=(255, 255, 255), icon_color="#111111", brand=False):
    """an app-style tile: rounded square with the icon, label under it; pops with overshoot"""
    if prog <= 0: return None
    s = 0.6 + 0.4 * back(prog); w = int(size * s); im = Image.new("RGBA", (size + 40, size + 90), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0, y0 = (im.width - w) // 2, (size - w) // 2 + 10; d.rounded_rectangle([x0, y0, x0 + w, y0 + w], radius=int(w * 0.22), fill=rgba(fill, 255 * min(1, prog * 2)))
    ic = E.svg_image(icon, int(w * 0.56), None if brand else icon_color); ic.putalpha(ic.getchannel("A").point(lambda a: int(a * min(1, prog * 2)))); E.paste_center(im, ic, im.width / 2, y0 + w / 2)
    if label and prog > 0.5:
        lab = E.text_image(label, E.font("Inter[opsz,wght].ttf", 26, 600), WHITE, pad=2); lab.putalpha(lab.getchannel("A").point(lambda a: int(a * ease((prog - 0.5) * 2)))); E.paste_center(im, lab, im.width / 2, size + 50)
    return im
def chip(text, prog, color=WHITE, fg=(17, 17, 17), size=40):
    if prog <= 0: return None
    f = E.font("Oswald[wght].ttf", size, 700); t = E.text_image(text, f, fg, pad=6); s = 0.7 + 0.3 * back(prog)
    im = Image.new("RGBA", (t.width + 36, t.height + 16), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=10, fill=rgba(color)); im.alpha_composite(t, (18, 8))
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR); im.putalpha(im.getchannel("A").point(lambda a: int(a * min(1, prog * 2)))); return im
def window(frame, prog=1.0, w=1500, zoom=1.0):
    """a screen recording in a rounded window with a soft shadow, slight zoom over time"""
    im = E.cover(frame, w, int(w * 9 / 16), zoom); im.putalpha(E.rounded_mask(im.width, im.height, 22)); im = E.shadowed(im, 30, (0, 20), 170)
    if prog < 1: s = 0.94 + 0.06 * ease(prog); im = im.resize((int(im.width * s), int(im.height * s)), Image.BILINEAR); im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog))))
    return im
def caption(parts, prog=1.0):
    """white rounded caption box with a marker-highlighted phrase: parts = [(text, highlighted?)]"""
    if prog <= 0: return None
    f = E.font("Inter[opsz,wght].ttf", 40, 600); ims = [(E.text_image(t, f, (16, 16, 16), pad=6), hl) for t, hl in parts]
    tw = sum(i.width for i, _ in ims); box = Image.new("RGBA", (tw + 60, ims[0][0].height + 36), (0, 0, 0, 0)); d = ImageDraw.Draw(box)
    d.rounded_rectangle([0, 0, box.width - 1, box.height - 1], radius=14, fill=(255, 255, 255, 255)); x = 30
    for im, hl in ims:
        if hl: d.rectangle([x + 2, 22, x + im.width - 2, box.height - 22], fill=rgba(MARK))
        box.alpha_composite(im, (x, 18)); x += im.width
    box.putalpha(box.getchannel("A").point(lambda a: int(a * ease(prog)))); return box
def stat(text, prog, color=GREEN):
    if prog <= 0: return None
    f = E.font("Inter[opsz,wght].ttf", 44, 700); im = E.text_image(text, f, color, pad=6); s = 0.8 + 0.2 * back(prog)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.BILINEAR); im.putalpha(im.getchannel("A").point(lambda a: int(a * min(1, prog * 2)))); return im

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []
    def face(a, b, draw=None, tr="cut"): S.append(dict(t0=a, t1=b, kind="face", draw=draw, tr=tr))
    def graphic(a, b, draw, tr="cut", face=INSET): S.append(dict(t0=a, t1=b, kind="graphic", draw=draw, tr=tr, face=face))
    # 0 hook: face, then the title with a counting stat and the "not just storing vectors" line
    face(c["hook_t0"], c["large"])
    def g_hook(t, dur, ctx):
        fr = canvas(); E.paste_center(fr, heading("Bulk uploads", 96), W / 2 + 160, 300)
        n = int(1_000_000 * ease(t / 1.4)); st = stat(f"{n:,} points", k(t, 0.05)); E.paste_center(fr, st, W / 2 + 160, 420) if st else None
        ps = k(t, c["just"] - c["large"]); sl = subline([("Qdrant isn't ", WHITE), ("just storing vectors", BLUE)], 40) if ps > 0 else None
        if sl is not None: sl.putalpha(sl.getchannel("A").point(lambda a: int(a * ps))); E.paste_center(fr, sl, W / 2 + 160, 560 + 16 * (1 - ps))
        return fr
    graphic(c["large"], c["list_t0"], g_hook, "zoom")
    # 1 what happens on upload: four tiles pop in as each thing is named
    items = [("lucide_layers.svg", "vectors", 0.0), ("lucide_file-json.svg", "payloads", c["payloads"] - c["list_t0"]), ("lucide_git-branch.svg", "indexes", c["indexes"] - c["list_t0"]), ("lucide_cpu.svg", "much more", c["much"] - c["list_t0"])]
    def g_list(t, dur, ctx):
        fr = canvas(); E.paste_center(fr, heading("What happens on upload", 64), W / 2 + 160, 230)
        for i, (ic, lab, at) in enumerate(items):
            tl = tile(os.path.join(ICONS, ic), lab, 150, k(t, at, 0.4))
            if tl is not None: E.paste_center(fr, tl, W / 2 + 160 - 330 + i * 220, 500)
        sl = subline([("all of it ", WHITE), ("in the background", BLUE)], 34); ps = k(t, c["background"] - c["list_t0"])
        if ps > 0: sl.putalpha(sl.getchannel("A").point(lambda a: int(a * ps))); E.paste_center(fr, sl, W / 2 + 160, 700)
        return fr
    graphic(c["list_t0"], c["cfg_t0"], g_list, "cut")
    for _, _, at in items[1:]: sfx.append((c["list_t0"] + at, E.pop(0.08)))
    # 2 no single config: back to the face with a caption
    def ov_cfg(t, dur, ctx):
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cp = caption([("No single configuration for ", False), ("every workload", True)], k(t, c["single"] - c["cfg_t0"] - 0.2, 0.3))
        if cp is not None: E.paste_center(ov, cp, W / 2, H - 150)
        return ov
    face(c["cfg_t0"], c["plan_t0"], ov_cfg)
    # 3 the plan: centred title card with numbered chips
    def g_plan(t, dur, ctx):
        fr = canvas(); E.paste_center(fr, heading("What we'll cover", 80), W / 2 + 160, 260)
        for row, (n, lab, at) in enumerate([(4, "options", c["options"] - c["plan_t0"]), (3, "best practices", c["best"] - c["plan_t0"])]):
            y = 450 + row * 190; x = W / 2 + 160 - 60 * n
            for i in range(n):
                ch = chip(f"#{i + 1}", k(t, at + 0.1 * i, 0.35), WHITE if row == 0 else BLUE, (17, 17, 17) if row == 0 else WHITE)
                if ch is not None: E.paste_center(fr, ch, x + i * 120, y)
            lab_im = E.text_image(lab.upper(), E.font("Inter[opsz,wght].ttf", 28, 600), GREY, pad=2); pl = k(t, at + 0.1 * n, 0.3)
            if pl > 0: lab_im.putalpha(lab_im.getchannel("A").point(lambda a: int(a * pl))); E.paste_center(fr, lab_im, W / 2 + 160, y + 80)
        return fr
    graphic(c["plan_t0"], c["ds_t0"], g_plan, "zoom")
    for i in range(4): sfx.append((c["options"] + 0.1 * i, E.click(0.05)))
    for i in range(3): sfx.append((c["best"] + 0.1 * i, E.click(0.05)))
    # 4-6 dense vs sparse: face first, then a two-tile comparison that gains its index labels on the cue words
    face(c["ds_t0"], c["dense"] - 0.3)
    def g_ds(t, dur, ctx):
        T = t + c["dense"] - 0.3; fr = canvas(); E.paste_center(fr, heading("Two kinds of vectors", 64), W / 2 + 160, 200)
        for i, (lab, at, ic, sub, sub_at) in enumerate([("dense", c["dense"], "lucide_layers.svg", "HNSW index", c["hnsw"]), ("sparse", c["sparse"], "lucide_list-checks.svg", "sparse index", c["indexing"])]):
            x = W / 2 + 160 - 260 + i * 520; tl = tile(os.path.join(ICONS, ic), lab.upper(), 190, k(T, at, 0.4), (255, 255, 255) if i == 0 else BLUE, "#111111" if i == 0 else "#ffffff")
            if tl is not None: E.paste_center(fr, tl, x, 480)
            ps = k(T, sub_at, 0.4); sl = subline([(sub, BLUE if i == 0 else WHITE)], 36)
            if ps > 0: sl.putalpha(sl.getchannel("A").point(lambda a: int(a * ps))); E.paste_center(fr, sl, x, 700 + 16 * (1 - ps))
        ps = k(T, c["indexing"] + 0.6, 0.4); sl = subline([("indexed ", WHITE), ("completely differently", BLUE)], 34)
        if ps > 0: sl.putalpha(sl.getchannel("A").point(lambda a: int(a * ps))); E.paste_center(fr, sl, W / 2 + 160, 820)
        return fr
    graphic(c["dense"] - 0.3, c["mp_t0"], g_ds, "cut")
    sfx += [(c["dense"], E.pop(0.08)), (c["sparse"], E.pop(0.08)), (c["hnsw"], E.click(0.05)), (c["indexing"], E.click(0.05))]
    # 7 memory and performance: the docs page in a window, as a screen recording, with a stat
    vt = os.path.join(EDIT_BR, "vector_type_shot.mp4")
    def g_mp(t, dur, ctx):
        fr = canvas(); fr.alpha_composite(window(E.clip(vt).frame(t), k(t, 0, 0.5), 1240, 1 + 0.04 * t / dur), (640 - 90, 70 - 90))
        for i, (txt, at) in enumerate([("memory", c["memory"]), ("performance", c["perf"])]):
            ch = chip(txt.upper(), k(t, at - c["mp_t0"], 0.35), WHITE)
            if ch is not None: E.paste_center(fr, ch, 1260 + (i - 0.5) * 320, 880)
        return fr
    graphic(c["mp_t0"], c["ch_t0"], g_mp, "cut")
    sfx += [(c["mp_t0"], E.whoosh(0.05)), (c["memory"], E.click(0.05)), (c["perf"], E.click(0.05))]
    # 8 chapter: face, then a centred title card before the look-away
    face(c["ch_t0"], c["ch_face_end"])
    def g_ch(t, dur, ctx):
        fr = canvas(); E.paste_center(fr, heading("Option 1", 110), W / 2, 440); ch = chip("#1", k(t, 0.2), BLUE, WHITE, 36)
        if ch is not None: E.paste_center(fr, ch, W / 2, 300)
        sl = subline([("Store dense vectors ", WHITE), ("on disk", BLUE)], 44); ps = k(t, 0.35)
        if ps > 0: sl.putalpha(sl.getchannel("A").point(lambda a: int(a * ps))); E.paste_center(fr, sl, W / 2, 580 + 16 * (1 - ps))
        return fr
    graphic(c["ch_face_end"], c["storing"] - 0.2, g_ch, "zoom", face=None)
    # 9 option 1: the Option 1 docs page in a window, inset face, green stat on "disk"
    s1 = os.path.join(BROLL, "s1_shot.mp4")
    def g_o1(t, dur, ctx):
        fr = canvas(); fr.alpha_composite(window(E.clip(s1).frame(t), k(t, 0, 0.5), 1240, 1 + 0.04 * t / dur), (640 - 90, 70 - 90))
        st = stat("RAM usage  down", k(t, c["disk"] - (c["storing"] - 0.2), 0.4)); E.paste_center(fr, st, 1260, 880) if st is not None else None
        return fr
    graphic(c["storing"] - 0.2, t1, g_o1, "cut")
    sfx += [(c["storing"] - 0.2, E.whoosh(0.05)), (c["disk"], E.pop(0.08))]
    return S, sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
