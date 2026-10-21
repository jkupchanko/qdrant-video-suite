"""WHITEBOARD: the whiteboard-animation format of After Skool (8.0M on the audited video) and Sprouts.

What the format is
  - white paper with a faint texture; black marker line drawings that draw themselves stroke by stroke,
    a marker tip travelling along the line; a few fills in one or two colours
  - hand-lettered words next to the drawings, written letter by letter
  - the camera drifts slowly across the board; nothing cuts; a new drawing every few seconds
  - a voice-over; the presenter is never on screen. Here the presenter is drawn in at the open, the plan
    and the chapter line as in the other voice-over styles
Fonts: Patrick Hand for the lettering. Drawings: Lucide's stroke icons, revealed along a wipe, plus
arrows and boxes drawn in code.
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import engine as E
from engine import W, H, k, ease, inout, rgba
from beats import cues
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\whiteboard_0-41.mp4"; BG = (250, 249, 245)
INK = (24, 22, 20); RED = (200, 40, 40); BLUE = (40, 90, 200); GREEN = (40, 150, 80); ICONS = r"C:\Users\ADMIN\camera_audit\popular\icons"; HAND = "PatrickHand-Regular.ttf"

def paper():
    key = "wb_paper"
    if key not in E._fc:
        rng = np.random.default_rng(9); n = rng.normal(0, 3, (H, W, 1)); a = np.array(BG, np.float32)[None, None, :] + n; E._fc[key] = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    return E._fc[key].copy()
def marker_tip(fr, x, y):
    d = ImageDraw.Draw(fr); d.polygon([(x, y), (x + 14, y - 30), (x + 30, y - 18)], fill=rgba(INK)); d.rounded_rectangle([x + 14, y - 100, x + 46, y - 22], radius=6, fill=rgba((40, 40, 46))); d.rectangle([x + 18, y - 96, x + 42, y - 70], fill=rgba((90, 90, 100)))
def icon_draw(fr, name, cx, cy, size, prog, color="#181614"):
    """a Lucide stroke icon revealed by a diagonal wipe, the marker tip at the wipe front"""
    if prog <= 0: return
    im = E.svg_image(os.path.join(ICONS, name), size, color); m = Image.new("L", im.size, 0); d = ImageDraw.Draw(m); e = ease(prog); lim = int(2 * size * e)
    d.polygon([(0, 0), (lim, 0), (0, lim)], fill=255); im = im.copy(); im.putalpha(Image.fromarray(np.minimum(np.asarray(im.getchannel("A")), np.asarray(m))))
    fr.alpha_composite(im, (int(cx - size / 2), int(cy - size / 2)))
    if prog < 1: marker_tip(fr, cx - size / 2 + lim / 2, cy - size / 2 + lim / 2)
def letter(fr, text, x, y, prog, size=54, color=INK):
    """hand lettering written letter by letter; the marker tip after the last letter"""
    if prog <= 0: return
    f = E.font(HAND, size); n = int(len(text) * min(1, prog) + 0.999); d = ImageDraw.Draw(fr); d.text((x, y), text[:n], font=f, fill=rgba(color))
    if prog < 1: marker_tip(fr, x + d.textlength(text[:n], font=f) + 4, y + size)
def stroke_path(fr, pts, prog, color=INK, width=5, arrow=False):
    if prog <= 0: return
    d = ImageDraw.Draw(fr); L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])); todo = L * ease(prog); drawn = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        if todo <= 0: break
        f = min(1, todo / seg); drawn.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)); todo -= seg
    if len(drawn) > 1: d.line([(x + 1.5 * math.sin(y / 30), y + 1.5 * math.cos(x / 30)) for x, y in drawn], fill=rgba(color), width=width, joint="curve")
    if prog < 1: marker_tip(fr, drawn[-1][0], drawn[-1][1])
    elif arrow:
        a, b = pts[-2], pts[-1]; ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for s in (-0.5, 0.5): d.line([b, (b[0] - 24 * math.cos(ang + s), b[1] - 24 * math.sin(ang + s))], fill=rgba(color), width=width)
def box(fr, x0, y0, x1, y1, prog, color=INK): stroke_path(fr, [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], prog, color, 5)
def fill_hatch(fr, x0, y0, x1, y1, prog, color=BLUE):
    if prog <= 0: return
    d = ImageDraw.Draw(fr); n = int(((x1 - x0) + (y1 - y0)) / 14 * ease(prog))
    for i in range(n):
        o = i * 14; a = (x0 + o, y0) if o < x1 - x0 else (x1, y0 + o - (x1 - x0)); b = (x0, y0 + o) if o < y1 - y0 else (x0 + o - (y1 - y0), y1); d.line([a, b], fill=rgba(color), width=3)

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []
    def face(a, b): S.append(dict(t0=a, t1=b, kind="face", tr="cut"))
    def g(a, b, draw): S.append(dict(t0=a, t1=b, kind="graphic", draw=draw, tr="cut", face=None))
    def squeaks(*ts):
        for t in ts: sfx.append((t, E.tone(0.3, 1600, 900, 0.03, noise=0.9, decay=3)))
    def board(T, cam):
        """the whole board at edit time T; cam = (dx, dy) camera offset"""
        fr = paper(); dx, dy = cam
        def P(x, y): return (x - dx, y - dy)
        # region 1: the data pile -> the database
        for i in range(5): box(fr, *P(160 + i * 26, 260 + i * 14), *P(300 + i * 26, 380 + i * 14), k(T, c["large"] + 0.12 * i, 0.4))
        letter(fr, "a LOT of data", *P(150, 150), k(T, c["large"] + 0.5, 0.8), 60)
        stroke_path(fr, [P(470, 320), P(640, 320)], k(T, c["large"] + 1.0, 0.4), INK, 5, True); icon_draw(fr, "lucide_database.svg", *P(780, 320), 220, k(T, c["large"] + 1.3, 0.8))
        letter(fr, "Qdrant", *P(700, 450), k(T, c["large"] + 1.9, 0.5), 48)
        letter(fr, "not just storing vectors!", *P(160, 540), k(T, c["just"], 1.0), 52); stroke_path(fr, [P(160, 600), P(740, 596)], k(T, c["store"] + 0.6, 0.4), RED, 6)
        # region 2: what it stores, four icons with lettering, under the first region
        for i, (ic, lab, at) in enumerate([("lucide_layers.svg", "vectors", c["list_t0"] + 0.3), ("lucide_file-json.svg", "payloads", c["payloads"]), ("lucide_git-branch.svg", "indexes", c["indexes"]), ("lucide_cpu.svg", "+ more", c["much"])]):
            x = 200 + i * 230; icon_draw(fr, ic, *P(x, 760), 150, k(T, at, 0.6)); letter(fr, lab, *P(x - 70, 850), k(T, at + 0.4, 0.5), 44)
        letter(fr, "in the background", *P(1120, 820), k(T, c["background"], 0.7), 44, BLUE)
        # region 3 (right): one config? a page icon with three arrows to three icons, a red X
        icon_draw(fr, "lucide_file-json.svg", *P(1460, 240), 180, k(T, c["single"], 0.6)); letter(fr, "one config?", *P(1340, 340), k(T, c["single"] + 0.3, 0.7), 50)
        for i, (ic, lab, at) in enumerate([("lucide_search.svg", "RAG app", c["works"]), ("lucide_server.svg", "100M points", c["works"] + 0.3), ("lucide_network.svg", "tenants", c["works"] + 0.6)]):
            x = 1240 + i * 220; stroke_path(fr, [P(1460, 330), P(x, 470)], k(T, at, 0.4), INK, 4, True); icon_draw(fr, ic, *P(x, 540), 120, k(T, at + 0.2, 0.5)); letter(fr, lab, *P(x - 60, 610), k(T, at + 0.5, 0.4), 34)
        px = k(T, c["all"], 0.4); stroke_path(fr, [P(1380, 170), P(1540, 310)], px, RED, 8); stroke_path(fr, [P(1540, 170), P(1380, 310)], max(0, px * 2 - 1), RED, 8)
        # region 4: the plan, lettered list (right, lower)
        letter(fr, "4 options", *P(1300, 700), k(T, c["options"], 0.6), 52); letter(fr, "3 best practices", *P(1300, 770), k(T, c["best"], 0.6), 52)
        # region 5 (far right, x 2000+): dense vs sparse boxes with their indexes
        letter(fr, "dense", *P(2100, 180), k(T, c["dense"], 0.5), 56); box(fr, *P(2080, 250), *P(2560, 330), k(T, c["dense"] + 0.2, 0.5)); fill_hatch(fr, *P(2084, 254), *P(2556, 326), k(T, c["dense"] + 0.6, 0.6), BLUE)
        letter(fr, "sparse", *P(2700, 180), k(T, c["sparse"], 0.5), 56); box(fr, *P(2680, 250), *P(3160, 330), k(T, c["sparse"] + 0.2, 0.5))
        for i in (2, 6, 9): fill_hatch(fr, *P(2684 + i * 48, 254), *P(2724 + i * 48, 326), k(T, c["sparse"] + 0.6, 0.4), BLUE)
        icon_draw(fr, "lucide_git-branch.svg", *P(2320, 520), 220, k(T, c["hnsw"], 0.8)); letter(fr, "HNSW graph", *P(2200, 650), k(T, c["hnsw"] + 0.5, 0.6), 46)
        icon_draw(fr, "lucide_list-checks.svg", *P(2920, 520), 220, k(T, c["indexing"], 0.8)); letter(fr, "sparse index", *P(2790, 650), k(T, c["indexing"] + 0.5, 0.6), 46)
        letter(fr, "indexed differently", *P(2380, 760), k(T, c["indexing"] + 1.0, 0.7), 46, RED)
        # region 6: memory and performance gauges
        icon_draw(fr, "lucide_memory-stick.svg", *P(2240, 960), 160, k(T, c["memory"], 0.6)); letter(fr, "memory", *P(2340, 920), k(T, c["memory"] + 0.3, 0.5), 48)
        icon_draw(fr, "lucide_gauge.svg", *P(2740, 960), 160, k(T, c["perf"], 0.6)); letter(fr, "performance", *P(2840, 920), k(T, c["perf"] + 0.3, 0.5), 48)
        letter(fr, "during bulk uploads", *P(2300, 1060), k(T, c["bulk"], 0.7), 46, BLUE)
        # region 7 (below, y 1300+): option 1: RAM box -> disk
        letter(fr, "Option 1", *P(200, 1320), k(T, c["ch_face_end"], 0.6), 80); letter(fr, "dense vectors on disk", *P(200, 1420), k(T, c["ch_face_end"] + 0.6, 0.8), 52)
        box(fr, *P(200, 1540), *P(560, 1760), k(T, c["storing"] - 0.4, 0.5)); letter(fr, "RAM", *P(330, 1770), k(T, c["storing"] - 0.1, 0.4), 44)
        for i in range(6): box(fr, *P(230 + (i % 3) * 100, 1570 + (i // 3) * 80), *P(300 + (i % 3) * 100, 1630 + (i // 3) * 80), k(T, c["storing"] - 0.3 + 0.05 * i, 0.3), BLUE)
        stroke_path(fr, [P(600, 1650), P(840, 1650)], k(T, c["storing"] + 0.2, 0.4), INK, 5, True); icon_draw(fr, "lucide_hard-drive.svg", *P(1000, 1650), 240, k(T, c["storing"] + 0.5, 0.8)); letter(fr, "disk", *P(950, 1790), k(T, c["storing"] + 1.0, 0.4), 44)
        letter(fr, "on_disk = True", *P(1240, 1620), k(T, c["disk"], 0.7), 56, GREEN)
        return fr
    KEYS = [(0.0, (0, 0)), (c["cfg_t0"], (560, 0)), (c["ds_t0"], (1700, 0)), (c["mp_t0"], (1700, 140)), (c["ch_face_end"], (0, 1100)), (c["storing"], (0, 1200))]
    def cam(T):
        cur = KEYS[0][1]
        for kt, kv in KEYS[1:]:
            if T >= kt - 0.6: e = inout((T - (kt - 0.6)) / 1.2); cur = (cur[0] + (kv[0] - cur[0]) * e, cur[1] + (kv[1] - cur[1]) * e)
        return cur
    def g_main(t, dur, ctx): T = ctx["t"]; return board(T, cam(T))
    face(c["hook_t0"], c["large"]); g(c["large"], c["plan_t0"], g_main); face(c["plan_t0"], c["options"] - 0.2); g(c["options"] - 0.2, c["ch_t0"], g_main); face(c["ch_t0"], c["ch_face_end"]); g(c["ch_face_end"], t1, g_main)
    squeaks(c["large"], c["just"], c["payloads"], c["indexes"], c["much"], c["single"], c["works"], c["all"], c["options"], c["best"], c["dense"], c["sparse"], c["hnsw"], c["indexing"], c["memory"], c["perf"], c["bulk"], c["ch_face_end"], c["storing"], c["disk"])
    return S, sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
