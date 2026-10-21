"""LIGHTBOARD: IBM Technology's look (3.7M, 2.0M, 1.8M, 1.7M views on its AI explainers), copied from the
frame audit of "AI, Machine Learning, Deep Learning and Generative AI Explained".

What the audit shows
  - the presenter stands on pure black, centre-right, mid-shot; a white lower-third name card at the start
  - everything else is marker handwriting on the glass in front of him: purple for the main ideas, green
    for checks and the second level, orange for the third level, white for emphasis; all caps, uneven
  - the drawing builds as he talks and never clears: lists with checkboxes, nested boxes, a timeline arrow,
    doodles (a laptop, a brain, a smiley) beside the words; strokes glow a little on the glass
  - no cuts at all (0 hard cuts a minute, 1.2 changes a minute); the whole video is one shot
Here: the presenter is cut out of his webcam background (matte.py), scaled down and set centre-right on
black; the handwriting draws itself in Permanent Marker on the spoken words. The one look-away is covered
by a board-only beat (the camera pushes into the drawing) because the reference never cuts away.
"""
import os, math
from PIL import Image, ImageDraw, ImageFilter
import numpy as np, cv2
import engine as E
from engine import W, H, k, ease, rgba
from beats import cues
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\lightboard_0-41.mp4"; BG = (0, 0, 0)
MATTE = r"C:\Users\ADMIN\camera_audit\edit\full_edit\matte_0-40.mp4"
PURPLE = (205, 110, 255); GREEN = (165, 255, 105); ORANGE = (255, 175, 80); WHITE = (255, 255, 255)
MARKER = "PermanentMarker.ttf"
PRES_SCALE, PRES_DX, PRES_DY = 0.82, 330, 140      # the presenter, smaller and set centre-right

def presenter(face_im, t):
    """the presenter matted onto black, scaled and shifted; the matte is read at the same edit time"""
    m = E.clip(MATTE).frame(t).convert("L"); fr = face_im.convert("RGBA").copy(); fr.putalpha(m)
    w, h = int(W * PRES_SCALE), int(H * PRES_SCALE); fr = fr.resize((w, h), Image.BILINEAR)
    out = E.blank(BG); out.alpha_composite(fr, (int((W - w) / 2 + PRES_DX), int(H - h + PRES_DY))); return out
def hand(text, size=52, color=PURPLE, prog=1.0, wobble=1):
    """marker handwriting that writes itself: characters appear in order, each slightly off the line"""
    if prog <= 0: return None
    f = E.font(MARKER, size); n = max(0, int(len(text) * min(1, prog) + 0.999)); w = int(E.TD.textlength(text, font=f)) + 40; im = Image.new("RGBA", (w, int(size * 1.7)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 10
    for i, ch in enumerate(text[:n]):
        dy = 2 * wobble * math.sin(i * 1.7 + len(text)); d.text((x, size * 1.15 + dy), ch, font=f, fill=rgba(color), anchor="ls"); x += d.textlength(ch, font=f)
    return E.glow(im, 10, 0.55)
def stroke_box(d, x0, y0, x1, y1, prog, color=PURPLE, width=5):
    """a box drawn by hand: the perimeter appears clockwise from the top left"""
    if prog <= 0: return
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]; L = 2 * ((x1 - x0) + (y1 - y0)); todo = L * ease(prog); path = []
    for a, b in zip(pts, pts[1:]):
        seg = abs(b[0] - a[0]) + abs(b[1] - a[1])
        if todo <= 0: break
        f = min(1, todo / seg); path.append((a, (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))); todo -= seg
    for a, b in path: d.line([(a[0] + 2 * math.sin(a[1] / 40), a[1]), (b[0] + 2 * math.sin(b[1] / 40), b[1])], fill=rgba(color), width=width)
def stroke_line(d, a, b, prog, color=PURPLE, width=5, arrow=False):
    if prog <= 0: return
    e = ease(prog); x, y = a[0] + (b[0] - a[0]) * e, a[1] + (b[1] - a[1]) * e; d.line([a, (x, y)], fill=rgba(color), width=width)
    if arrow and prog >= 0.95:
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for s in (-0.5, 0.5): d.line([b, (b[0] - 22 * math.cos(ang + s), b[1] - 22 * math.sin(ang + s))], fill=rgba(color), width=width)
def checkbox(d, x, y, prog, checked, color=PURPLE):
    stroke_box(d, x, y, x + 22, y + 22, min(1, prog * 2), color, 3)
    if checked > 0: stroke_line(d, (x + 4, y + 12), (x + 10, y + 20), min(1, checked * 2), GREEN, 4); stroke_line(d, (x + 10, y + 20), (x + 22, y + 2), max(0, checked * 2 - 1), GREEN, 4)
def lower_third(prog):
    if prog <= 0: return None
    im = Image.new("RGBA", (520, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((0, 0), "John Kupchanko", font=E.font("Inter[opsz,wght].ttf", 34, 700), fill=rgba(WHITE)); d.text((0, 48), "Developer Relations", font=E.font("Inter[opsz,wght].ttf", 26, 400), fill=rgba(WHITE)); d.text((0, 82), "Qdrant", font=E.font("Inter[opsz,wght].ttf", 26, 400), fill=rgba(WHITE))
    im.putalpha(im.getchannel("A").point(lambda a: int(a * ease(prog)))); return im

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []
    def board(fr, T):
        """everything written so far, at edit time T (the board never clears)"""
        d = ImageDraw.Draw(fr); gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(gl)
        def put(im, x, y):
            if im is not None: fr.alpha_composite(im, (x, y))
        # top left: the title and the "not just store" line
        put(hand("BULK UPLOADS", 64, PURPLE, k(T, c["large"], 1.0)), 60, 40)
        put(hand("= JUST STORE?", 44, WHITE, k(T, c["just"] - 0.1, 0.8)), 60, 150)
        stroke_line(g, (60, 200), (420, 180), k(T, c["store"] + 0.6, 0.3), ORANGE, 6)                      # the strike
        # the list, with checkboxes ticked as each is named
        items = [("VECTORS", c["list_t0"] + 0.2), ("PAYLOADS", c["payloads"]), ("INDEXES", c["indexes"]), ("+ MORE", c["much"])]
        for i, (name, at) in enumerate(items):
            y = 290 + i * 70; checkbox(g, 70, y + 10, k(T, at, 0.4), k(T, at + 0.3, 0.4)); put(hand(name, 44, PURPLE, k(T, at, 0.7)), 110, y - 20)
        # one config? a box with three arrows and an X, lower left
        put(hand("ONE CONFIG?", 44, PURPLE, k(T, c["single"] - 0.2, 0.8)), 60, 600)
        for i, (name, at) in enumerate([("RAG", c["works"]), ("100M", c["works"] + 0.3), ("TENANTS", c["works"] + 0.6)]):
            stroke_line(g, (160, 690), (90 + i * 150, 780), k(T, at, 0.4), PURPLE, 4, arrow=True); put(hand(name, 32, GREEN, k(T, at + 0.2, 0.5)), 50 + i * 150, 790)
        px = k(T, c["all"], 0.4); stroke_line(g, (60, 640), (330, 700), px, ORANGE, 7); stroke_line(g, (330, 640), (60, 700), max(0, px * 2 - 1), ORANGE, 7)
        # the timeline arrow along the bottom: options in purple, best practices in green
        stroke_line(g, (520, 990), (1860, 990), k(T, c["options"] - 0.3, 0.8), PURPLE, 4, arrow=True)
        for i in range(4):
            at = c["options"] + 0.12 * i; x = 560 + i * 170; stroke_line(g, (x, 975), (x, 1005), k(T, at, 0.2), PURPLE, 4); put(hand(f"OPT {i + 1}", 26, PURPLE, k(T, at, 0.4)), x - 30, 1010)
        for i in range(3):
            at = c["best"] + 0.12 * i; x = 1320 + i * 170; stroke_line(g, (x, 975), (x, 1005), k(T, at, 0.2), GREEN, 4); put(hand(f"BP {i + 1}", 26, GREEN, k(T, at, 0.4)), x - 26, 1010)
        # top right: dense and sparse, each with its index doodle
        stroke_box(g, 1380, 60, 1880, 460, k(T, c["ds_t0"] + 0.3, 1.0), PURPLE, 5)
        put(hand("DENSE", 40, PURPLE, k(T, c["dense"], 0.6)), 1400, 70); put(hand("SPARSE", 40, PURPLE, k(T, c["sparse"], 0.6)), 1400, 260)
        pg = k(T, c["hnsw"], 0.9)
        if pg > 0:                                                              # a little graph doodle
            pts = [(1600, 110), (1680, 140), (1760, 100), (1820, 160), (1700, 200), (1620, 190)]; ed = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (1, 4)]
            for j, (a, b) in enumerate(ed): stroke_line(g, pts[a], pts[b], min(1, pg * 7 - j), GREEN, 3)
            for x, y in pts:
                if pg > 0.3: g.ellipse([x - 6, y - 6, x + 6, y + 6], fill=rgba(GREEN))
            put(hand("HNSW", 30, GREEN, k(T, c["hnsw"] + 0.4, 0.5)), 1400, 150)
        pi = k(T, c["indexing"], 0.9)
        if pi > 0:                                                              # a little table doodle
            for j in range(3): stroke_line(g, (1600, 300 + j * 40), (1840, 300 + j * 40), min(1, pi * 3 - j), GREEN, 3)
            stroke_line(g, (1680, 290), (1680, 400), pi, GREEN, 3); put(hand("INDEX", 30, GREEN, k(T, c["indexing"] + 0.4, 0.5)), 1400, 340)
        put(hand("MEMORY", 34, ORANGE, k(T, c["memory"], 0.6)), 1400, 470); put(hand("PERF", 34, ORANGE, k(T, c["perf"], 0.6)), 1660, 470)
        put(hand("BULK UPLOAD =", 30, WHITE, k(T, c["bulk"], 0.6)), 1400, 540); put(hand("DIFFERENT", 30, WHITE, k(T, c["bulk"] + 0.4, 0.6)), 1400, 590)
        # option 1: RAM -> disk doodle, bottom right
        put(hand("OPTION 1", 40, WHITE, k(T, c["ch_face_end"], 0.7)), 1400, 680)
        stroke_box(g, 1400, 760, 1540, 860, k(T, c["storing"] - 0.3, 0.5), ORANGE, 4); put(hand("RAM", 28, ORANGE, k(T, c["storing"] - 0.1, 0.4)), 1430, 790)
        stroke_line(g, (1560, 810), (1680, 810), k(T, c["storing"] + 0.2, 0.4), ORANGE, 4, arrow=True)
        pd = k(T, c["storing"] + 0.5, 0.6)
        if pd > 0:
            g.ellipse([1700, 770, 1860, 810], outline=rgba(ORANGE), width=4); stroke_line(g, (1700, 790), (1700, 850), pd, ORANGE, 4); stroke_line(g, (1860, 790), (1860, 850), pd, ORANGE, 4)
            if pd > 0.8: g.arc([1700, 830, 1860, 870], 0, 180, fill=rgba(ORANGE), width=4)
            put(hand("DISK", 28, ORANGE, k(T, c["storing"] + 0.9, 0.4)), 1735, 790)
        put(hand("on_disk = True", 30, GREEN, k(T, c["disk"], 0.6)), 1400, 890)
        fr.alpha_composite(E.glow(gl, 8, 0.5)); return fr
    def g_main(t, dur, ctx):
        T = t0 + t; fr = presenter(ctx["face"], T); fr = board(fr, T); lt = lower_third(min(k(T, 0.3, 0.5), 1 - k(T, 5.0, 0.5)))
        if lt is not None: fr.alpha_composite(lt, (80, H - 200))
        return fr
    S.append(dict(t0=t0, t1=c["ch_face_end"], kind="graphic", draw=g_main, tr="cut", face=None, shows_face=True))
    # the look-away: push into the board (presenter off) for the chapter beat, then back
    def g_board_only(t, dur, ctx):
        T = c["ch_face_end"] + t; fr = board(E.blank(BG), T); z = 1.0 + 0.3 * ease(t / 0.8); cx, cy = 1560, 560      # push into the right panel
        big = fr.resize((int(W * z), int(H * z)), Image.BILINEAR); out = E.blank(BG); out.alpha_composite(big, (int(W / 2 - cx * z), int(H / 2 - cy * z))); return out
    S.append(dict(t0=c["ch_face_end"], t1=c["o1_t0"] + 0.1, kind="graphic", draw=g_board_only, tr="dissolve", face=None))
    S.append(dict(t0=c["o1_t0"] + 0.1, t1=t1, kind="graphic", draw=lambda t, dur, ctx: g_main(t + (c["o1_t0"] + 0.1 - t0), dur, ctx), tr="dissolve", face=None, shows_face=True))
    for key in ("large", "just", "payloads", "indexes", "much", "single", "works", "all", "options", "best", "dense", "sparse", "hnsw", "indexing", "memory", "perf", "bulk", "storing", "disk"):
        sfx.append((c[key], E.tone(0.25, 1800, 900, 0.02, noise=0.9, decay=3)))     # a faint marker squeak per word written
    return S, sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
