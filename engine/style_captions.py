"""CAPTIONS: the caption-led talking-head format of Alex Hormozi (1.7M on the audited video, tens of
millions across Shorts), Iman Gadzhi (8.1M) and the short-form editors who copy them.

What the format is (from the frames and the CapCut tutorials that teach it)
  - the presenter full frame, nothing else; punch-ins on emphasis
  - three to five words at a time, centred low in the frame, in a heavy geometric sans (Montserrat
    ExtraBold / "The Bold Font"), white with a thick black stroke, in capitals
  - the word being said is highlighted: yellow (or green), slightly larger, with a pop as it lands
  - an emoji drops in beside a word that has one; a key word gets a colour of its own
  - sound: a soft tick on each word group; a whoosh on a punch-in
  - no graphics at all: the captions are the edit
Fonts: Montserrat 800.
"""
import os, math
from PIL import Image, ImageDraw
import engine as E
from engine import W, H, k, ease, back, rgba
from beats import cues, spoken
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\captions_0-41.mp4"; BG = (0, 0, 0)
WHITE = (255, 255, 255); YEL = (255, 222, 0); GREEN = (80, 230, 90); INK = (0, 0, 0); EMO = r"C:\Users\ADMIN\camera_audit\popular\emoji"
EMOJI = {"data": "1f4e6", "qdrant": None, "vectors": None, "background": None, "memory": "1f9e0", "performance": "26a1", "disk": "1f4be", "hnsw": "1f5c4", "sparse": None, "bulk": "1f680", "no": "274c", "single": None}
KEY = {"large": YEL, "just": GREEN, "payloads": YEL, "indexes": YEL, "more": GREEN, "single": GREEN, "all": YEL, "options": YEL, "best": YEL, "dense": YEL, "sparse": GREEN, "hnsw": YEL, "indexing": GREEN, "memory": YEL, "performance": GREEN, "bulk": YEL, "first": YEL, "storing": YEL, "disk": GREEN}
PUNCH = {"large", "just", "all", "hnsw", "bulk", "disk"}

def groups(words, n=4, max_gap=0.9):
    """split the spoken words into caption groups of up to n words; a long pause starts a new group"""
    out = []; cur = []
    for w_, t in words:
        if cur and (len(cur) >= n or t - cur[-1][1] > max_gap): out.append(cur); cur = []
        cur.append((w_, t))
    if cur: out.append(cur)
    return out
def caption(group, T, next_t):
    """the group on one baseline; the current word in colour and a little bigger"""
    f = E.font("Montserrat[wght].ttf", 66, 800); fb = E.font("Montserrat[wght].ttf", 74, 800); texts = [w_.strip(" ,.?!").upper() for w_, _ in group]
    cur = max(i for i, (_, t) in enumerate(group) if T >= t - 0.02) if any(T >= t - 0.02 for _, t in group) else -1
    widths = [E.TD.textlength(t + " ", font=fb if i == cur else f) for i, t in enumerate(texts)]; tw = sum(widths); im = Image.new("RGBA", (int(tw) + 160, 230), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 80
    for i, (t, wd) in enumerate(zip(texts, widths)):
        key = group[i][0].strip(" ,.?!").lower(); col = KEY.get(key, WHITE) if i == cur else (KEY.get(key, WHITE) if i < cur and key in KEY else WHITE)
        if i == cur: col = KEY.get(key, YEL)
        font = fb if i == cur else f; s = 1.0
        if i == cur: s = 0.9 + 0.1 * back(min(1, (T - group[i][1] + 0.02) / 0.12))
        d.text((x + wd / 2, 180), t, font=font, fill=rgba(col), anchor="ms", stroke_width=7, stroke_fill=rgba(INK))
        if i == cur and EMOJI.get(key):
            em = E.svg_image(os.path.join(EMO, EMOJI[key] + ".svg"), 70); pe = back(min(1, (T - group[i][1] + 0.02) / 0.2)); em = em.resize((max(1, int(70 * pe)), max(1, int(70 * pe)))); im.alpha_composite(em, (int(x + wd / 2 - em.width / 2), 0))
        x += wd
    return im

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []
    words = []
    for i in range(10): words += spoken(p, i)
    gs = groups(words); starts = [g[0][1] for g in gs]
    def ov(t, dur, ctx):
        T = ctx["t"]; ovl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for gi, g in enumerate(gs):
            g_end = starts[gi + 1] if gi + 1 < len(gs) else g[-1][1] + 1.2
            if g[0][1] - 0.05 <= T < g_end:
                cap = caption(g, T, g_end); E.paste_center(ovl, cap, W / 2, H - 230); break
        return ovl
    # the face carries the whole thing; a punch-in on the emphasis words; the look-away is covered by a black card with the words only
    for a, b in [(t0, c["ch_face_end"]), (c["o1_t0"] + 0.1, t1)]: S.append(dict(t0=a, t1=b, kind="face", draw=ov, tr="cut"))
    def g_black(t, dur, ctx):
        fr = E.blank(BG); fr.alpha_composite(ov(t, dur, ctx)); return fr
    S.append(dict(t0=c["ch_face_end"], t1=c["o1_t0"] + 0.1, kind="graphic", draw=g_black, tr="cut", face=None))
    for g in gs: sfx.append((g[0][1], E.click(0.025)))
    for w_, t in words:
        if w_.strip(" ,.?!").lower() in PUNCH: sfx.append((t, E.whoosh(0.03, 0.25)))
    return S, sfx

# punch-ins: the engine has no zoom-on-face primitive, so the face shot draws its own crop through `draw`
# (the overlay above is composited after); done here by wrapping the renderer's face frame
_orig_base = E.Renderer.base_frame
def _base(self, s, t, face_im):
    if s["kind"] == "face" and getattr(self, "_punch", None):
        z = 1.0
        for pt in self._punch:
            if 0 <= t - pt < 1.0: z = 1.0 + 0.1 * (1 - (t - pt) / 1.0) ** 0.5
        if z > 1.001:
            cw, ch = int(W / z), int(H / z); x0, y0 = (W - cw) // 2, int((H - ch) * 0.45); face_im = face_im.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR)
    return _orig_base(self, s, t, face_im)
E.Renderer.base_frame = _base

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__))
    _p = E.Project(); _words = []
    for i in range(10): _words += spoken(_p, i)
    E.Renderer._punch = [t for w_, t in _words if w_.strip(" ,.?!").lower() in PUNCH]
    E.main(sys.modules[__name__])
