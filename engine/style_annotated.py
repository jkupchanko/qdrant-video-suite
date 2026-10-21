"""ANNOTATED: NetworkChuck's look (3.0M views on "you need to learn Python RIGHT NOW!!", 2.7M and 2.6M on
his AI videos), copied from the frame audit.

What the audit shows
  - the presenter full frame, big, on a dark neon-lit set; he stays on screen most of the time
  - white hand-written notes pop in beside his head as he talks: a word or two in marker capitals, a
    boxed word, a logo with a hand-drawn arrow, chains of notes joined by arrows ("Learning -> What do
    you need? -> NOTHING!!"); they stay up for the whole thought, then clear
  - a glitch (RGB split, sliced displacement, noise) into and out of screen recordings; on the screen
    the presenter sits in a large circle bottom-left and a hand-drawn circle marks the thing to click
  - a lower third: round avatar, title, episode, thin sans
  - short reaction cut-ins (a sip of coffee), a datamosh frame between sections
  - 5.6 hard cuts and 22 changes a minute: a new note every three seconds or so
Fonts: Gloria Hallelujah for the notes, Inter for the lower third.
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter
import engine as E
from engine import W, H, k, ease, back, rgba
from beats import cues
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\annotated_0-41.mp4"; BG = (8, 8, 12)
WHITE = (255, 255, 255); INK = (12, 12, 16)
HAND = "GloriaHallelujah.ttf"; BROLL = r"C:\Users\ADMIN\camera_audit\full\broll"; EDIT_BR = r"C:\Users\ADMIN\camera_audit\edit\broll"
MARK = r"C:\Users\ADMIN\camera_audit\assets\qdrant-brandmark-white.png"
CIRCLE = ("inset", (40, H - 40 - 420, 420, 420), 210)

def note(text, size=46, prog=1.0, rot=-4, boxed=False):
    """white marker handwriting with a soft shadow, slightly rotated, popping in with overshoot"""
    if prog <= 0: return None
    f = E.font(HAND, size); lines = text.split("\n"); ims = [E.text_image(ln, f, WHITE, shadow=(5, 2, 4, 170), pad=10) for ln in lines]
    w, h = max(i.width for i in ims), sum(i.height for i in ims) - 12 * (len(ims) - 1); im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); y = 20
    for i in ims: im.alpha_composite(i, (20, y)); y += i.height - 12
    if boxed:
        d = ImageDraw.Draw(im); pts = [(14, 16), (w + 26, 12), (w + 24, h + 26), (10, h + 24), (14, 16)]
        for a, b in zip(pts, pts[1:]): d.line([a, b], fill=rgba(WHITE), width=4)
    im = im.rotate(rot, resample=Image.BICUBIC, expand=True); s = 0.7 + 0.3 * back(prog)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR); im.putalpha(im.getchannel("A").point(lambda a: int(a * min(1, prog * 3)))); return im
def harrow(fr, a, b, prog, curve=40):
    """a hand-drawn white arrow from a to b, drawing on"""
    if prog <= 0: return
    d = ImageDraw.Draw(fr); n = 30; pts = []
    for i in range(int(n * min(1, prog)) + 1):
        u = i / n; mx, my = (a[0] + b[0]) / 2 + curve, (a[1] + b[1]) / 2 - curve
        x = (1 - u) ** 2 * a[0] + 2 * (1 - u) * u * mx + u ** 2 * b[0]; y = (1 - u) ** 2 * a[1] + 2 * (1 - u) * u * my + u ** 2 * b[1]; pts.append((x + 1.5 * math.sin(u * 30), y + 1.5 * math.cos(u * 28)))
    if len(pts) > 1:
        d.line([(x + 3, y + 4) for x, y in pts], fill=(0, 0, 0, 120), width=5); d.line(pts, fill=rgba(WHITE), width=5)
    if prog >= 0.97:
        ang = math.atan2(b[1] - pts[-3][1], b[0] - pts[-3][0])
        for s in (-0.55, 0.55): d.line([b, (b[0] - 26 * math.cos(ang + s), b[1] - 26 * math.sin(ang + s))], fill=rgba(WHITE), width=5)
def hcircle(fr, cx, cy, rx, ry, prog):
    """a hand-drawn ellipse around something on the screen, one and a bit turns"""
    if prog <= 0: return
    d = ImageDraw.Draw(fr); pts = []
    for i in range(int(380 * min(1, prog)) + 1):
        a = math.radians(i - 110); pts.append((cx + (rx + 6 * math.sin(i / 23)) * math.cos(a), cy + (ry + 5 * math.cos(i / 17)) * math.sin(a) + i * 0.04))
    if len(pts) > 1: d.line(pts, fill=rgba(WHITE), width=5)
def logo(size, prog):
    if prog <= 0: return None
    im = E.fit(Image.open(MARK).convert("RGBA"), size, size); im = E.shadowed(im, 10, (2, 4), 160); s = 0.7 + 0.3 * back(prog)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
def lower_third(prog):
    if prog <= 0: return None
    im = Image.new("RGBA", (700, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.ellipse([0, 0, 110, 110], outline=rgba(WHITE), width=4); mk = E.fit(Image.open(MARK).convert("RGBA"), 60, 60); E.paste_center(im, mk, 55, 55)
    d.line([(130, 20), (130, 95)], fill=rgba(WHITE), width=2); d.text((150, 18), "Bulk Uploads", font=E.font("Inter[opsz,wght].ttf", 36, 300), fill=rgba(WHITE)); d.text((150, 66), "Qdrant  //  EP 1", font=E.font("Inter[opsz,wght].ttf", 24, 300), fill=rgba((200, 200, 210)))
    im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog)))); return im
def screen(frame, fr):
    """a screen recording full frame with a dark vignette, the presenter in the circle"""
    fr.alpha_composite(E.vignette(E.cover(frame, W, H), 0.4)); return fr

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []
    def put(fr, im, x, y):
        if im is not None: fr.alpha_composite(im, (int(x), int(y)))
    def face(a, b, draw, tr="cut"): S.append(dict(t0=a, t1=b, kind="face", draw=draw, tr=tr))
    def scr(a, b, draw, tr="glitch"): S.append(dict(t0=a, t1=b, kind="graphic", draw=draw, tr=tr, face=CIRCLE, face_border=(WHITE, 5)))
    def pops(*ts):
        for t in ts: sfx.append((t, E.paper(0.05)))
    vt = E.clip(os.path.join(EDIT_BR, "vector_type_shot.mp4")); s1 = E.clip(os.path.join(BROLL, "s1_shot.mp4"))
    # 0-1 hook and the list: notes around the head, a chain on the right
    def ov_hook(t, dur, ctx):
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); T = t0 + t
        put(ov, lower_third(min(k(T, 0.4, 0.5), 1 - k(T, 5.5, 0.5))), 60, H - 170)
        put(ov, note("a LOT of\ndata!!", 52, k(T, c["large"], 0.4), -6), 80, 120); harrow(ov, (380, 260), (640, 330), k(T, c["large"] + 0.3, 0.4), 30)
        put(ov, logo(120, k(T, c["store"] - 0.4, 0.4)), 1480, 120); put(ov, note("not JUST\nstoring vectors", 42, k(T, c["just"], 0.4), 4, boxed=True), 1380, 270)
        put(ov, note("payloads", 44, k(T, c["payloads"], 0.4), -3), 1460, 520); harrow(ov, (1560, 600), (1560, 650), k(T, c["indexes"] - 0.2, 0.3), 10)
        put(ov, note("indexes", 44, k(T, c["indexes"], 0.4), 2), 1460, 650); harrow(ov, (1560, 730), (1560, 790), k(T, c["much"] - 0.2, 0.3), -10)
        put(ov, note("+ MORE!!", 50, k(T, c["much"], 0.4), -5), 1420, 790)
        pb = k(T, c["background"], 0.4); put(ov, note("in the background", 34, pb, 3), 60, 540)
        return ov
    face(c["hook_t0"], c["cfg_t0"], ov_hook); pops(c["large"], c["just"], c["payloads"], c["indexes"], c["much"], c["background"])
    # 2 one config? glitch to the docs page with the circle cam; a hand circle around the options list, a note
    def g_cfg(t, dur, ctx):
        fr = screen(s1.frame(t), E.blank(BG)); T = c["cfg_t0"] + t
        hcircle(fr, 1180, 560, 520, 200, k(T, c["single"] - 0.2, 0.8)); put(fr, note("ONE config??", 52, k(T, c["works"], 0.4), -5), 560, 120); put(fr, note("NOPE.", 70, k(T, c["all"], 0.4), 4), 1300, 110)
        return fr
    scr(c["cfg_t0"], c["plan_t0"], g_cfg); sfx.append((c["cfg_t0"], E.tone(0.3, 300, 80, 0.12, noise=0.9, decay=3))); pops(c["works"], c["all"])
    # 3 the plan: glitch back to the face, two notes
    def ov_plan(t, dur, ctx):
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); T = c["plan_t0"] + t
        put(ov, note("4 OPTIONS", 60, k(T, c["options"], 0.4), -5, boxed=True), 80, 300); put(ov, note("3 BEST\nPRACTICES", 50, k(T, c["best"], 0.4), 4, boxed=True), 1380, 280); return ov
    face(c["plan_t0"], c["ds_t0"], ov_plan, "glitch"); sfx.append((c["plan_t0"], E.tone(0.3, 300, 80, 0.12, noise=0.9, decay=3))); pops(c["options"], c["best"])
    # 4-6 dense and sparse: notes left and right with doodles
    def ov_ds(t, dur, ctx):
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); T = c["ds_t0"] + t; d = ImageDraw.Draw(ov)
        put(ov, note("DENSE", 60, k(T, c["dense"], 0.4), -4), 120, 200); put(ov, note("SPARSE", 60, k(T, c["sparse"], 0.4), 4), 1420, 200)
        pg = k(T, c["hnsw"], 0.9)
        if pg > 0:
            pts = [(160, 440), (260, 400), (380, 460), (470, 410), (300, 540), (420, 560)]; ed = [(0, 1), (1, 2), (2, 3), (1, 4), (4, 5), (5, 2)]
            for j, (a, b) in enumerate(ed):
                pr = min(1, pg * 6 - j)
                if pr > 0: e = ease(pr); d.line([pts[a], (pts[a][0] + (pts[b][0] - pts[a][0]) * e, pts[a][1] + (pts[b][1] - pts[a][1]) * e)], fill=rgba(WHITE), width=4)
            for x, y in pts: d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=rgba(WHITE))
            put(ov, note("HNSW graph", 40, k(T, c["hnsw"] + 0.5, 0.4), -3), 150, 580)
        pi = k(T, c["indexing"], 0.9)
        if pi > 0:
            for j in range(4): d.line([(1420, 420 + j * 44), (1420 + 400 * min(1, pi * 4 - j), 420 + j * 44)], fill=rgba(WHITE), width=4)
            d.line([(1560, 410), (1560, 560)], fill=rgba(WHITE), width=4); put(ov, note("its OWN index", 40, k(T, c["indexing"] + 0.5, 0.4), 3), 1400, 580)
        return ov
    face(c["ds_t0"], c["mp_t0"], ov_ds); pops(c["dense"], c["sparse"], c["hnsw"], c["indexing"])
    # 7 memory and performance: glitch to the vector-type docs page, circle cam, notes
    def g_mp(t, dur, ctx):
        fr = screen(vt.frame(t), E.blank(BG)); T = c["mp_t0"] + t
        hcircle(fr, 1150, 500, 560, 150, k(T, c["mp_t0"] + 0.4, 0.8)); put(fr, note("memory", 54, k(T, c["memory"], 0.4), -4), 560, 110); put(fr, note("performance", 54, k(T, c["perf"], 0.4), 3), 1150, 100)
        put(fr, note("during BULK uploads!!", 44, k(T, c["bulk"], 0.4), -2, boxed=True), 760, 820); return fr
    scr(c["mp_t0"], c["ch_t0"], g_mp); sfx.append((c["mp_t0"], E.tone(0.3, 300, 80, 0.12, noise=0.9, decay=3))); pops(c["memory"], c["perf"], c["bulk"])
    # 8 chapter: glitch back to the face, then the dark title frame (covers the look-away)
    face(c["ch_t0"], c["ch_face_end"], None, "glitch"); sfx.append((c["ch_t0"], E.tone(0.3, 300, 80, 0.12, noise=0.9, decay=3)))
    def g_title(t, dur, ctx):
        fr = E.blank(BG); d = ImageDraw.Draw(fr)
        for i in range(12): d.line([(140 + i * 160, 0), (60 + i * 160, H)], fill=(20, 16, 40, 255), width=3)         # faint neon lines of the set
        put(fr, logo(220, k(t, 0.1, 0.5)), 850, 200); put(fr, note("OPTION 1", 110, k(t, 0.3, 0.5), -3), 700, 470); put(fr, note("dense vectors -> on disk", 44, k(t, 0.8, 0.5), 2), 700, 680); return fr
    S.append(dict(t0=c["ch_face_end"], t1=c["o1_t0"] + 0.3, kind="graphic", draw=g_title, tr="glitch", face=None)); sfx.append((c["ch_face_end"], E.tone(0.3, 300, 80, 0.12, noise=0.9, decay=3)))
    # 9 option 1: face, RAM -> disk doodle on the left, on_disk note on the right
    def ov_disk(t, dur, ctx):
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); T = c["o1_t0"] + 0.3 + t; d = ImageDraw.Draw(ov)
        put(ov, note("RAM", 50, k(T, c["storing"] - 0.2, 0.4, ), -3, boxed=True), 100, 300); harrow(ov, (300, 360), (420, 360), k(T, c["storing"] + 0.2, 0.4), 0)
        pd = k(T, c["storing"] + 0.5, 0.5)
        if pd > 0:
            d.ellipse([430, 320, 590, 370], outline=rgba(WHITE), width=5); d.line([(430, 345), (430, 440)], fill=rgba(WHITE), width=5); d.line([(590, 345), (590, 440)], fill=rgba(WHITE), width=5); d.arc([430, 415, 590, 465], 0, 180, fill=rgba(WHITE), width=5)
            put(ov, note("disk", 40, pd, 2), 440, 470)
        put(ov, note("on_disk = True", 54, k(T, c["disk"], 0.4), -4, boxed=True), 1340, 300); return ov
    face(c["o1_t0"] + 0.3, t1, ov_disk, "glitch"); sfx.append((c["o1_t0"] + 0.3, E.tone(0.3, 300, 80, 0.12, noise=0.9, decay=3))); pops(c["storing"], c["disk"])
    return S, sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
