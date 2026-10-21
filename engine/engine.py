"""Shared engine for the editing styles. A style module gives it a list of shots; the engine reads the cut,
the look-away list and the spoken words, composites each frame, runs the transitions, writes the sound, and
checks that the presenter's face is never on screen while the eyes are off the lens.

Shot: dict(t0, t1, kind, draw, tr, face)
  kind  "face"     the cut as it is; draw(t_local, dur, ctx) may return an RGBA overlay or None
        "graphic"  draw(t_local, dur, ctx) returns a full RGBA frame; `face` places the presenter on it:
                   None | ("inset", (x, y, w, h), radius) | ("card", (x, y, w, h), radius)
  tr    how the shot arrives: cut | push_left | push_up | dissolve | flash | dip | shrink | grow | slide_card | card_out | pip_in | pip_out | morph | whip | zoom
ctx: dict(face=<RGBA face frame>, t=<edit time>, project=<Project>)
Transitions take TR seconds (0.5: the first test was judged a little fast at 0.3).
"""
import os, re, sys, json, math, wave, subprocess, numpy as np, cv2, imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1920, 1080, 30
TR = 0.5
FONTS = r"C:\Users\ADMIN\camera_audit\fonts"
EDIT = r"C:\Users\ADMIN\camera_audit\edit"

# ---------------------------------------------------------------- fonts, easing, drawing helpers
_fc = {}
def font(name, size, weight=None):
    """a font by file name; `weight` picks the instance of a variable font ([wght] or [opsz,wght])"""
    key = (name, size, weight)
    if key in _fc: return _fc[key]
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if weight is not None and "[" in name:
        try:
            axes = f.get_variation_axes(); vals = []
            for a in axes:
                nm = a["name"].decode() if isinstance(a["name"], bytes) else a["name"]
                vals.append(weight if "eight" in nm or nm == "wght" else (min(max(a["minimum"], 32), a["maximum"]) if "ptical" in nm or nm == "opsz" else a["default"]))
            f.set_variation_by_axes(vals)
        except Exception: pass
    _fc[key] = f; return f
def ease(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3
def inout(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def back(x, s=1.7):           # overshoot, for bouncy pops
    x = min(1, max(0, x)); x -= 1; return 1 + x * x * ((s + 1) * x + s)
def k(t, t0, d=0.45, fn=ease): return fn((t - t0) / d)
def rgba(c, a=255): return tuple(c[:3]) + (int(a),)

def blank(color=(0, 0, 0), alpha=255): return Image.new("RGBA", (W, H), rgba(color, alpha))
def rounded_mask(w, h, r):
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255); return m
def cover(im, w, h, zoom=1.0, cx=0.5, cy=0.5):
    """scale an image to cover w x h (optionally zoomed) and crop around (cx, cy)"""
    s = max(w / im.width, h / im.height) * zoom; big = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.BILINEAR)
    x = int((big.width - w) * cx); y = int((big.height - h) * cy); return big.crop((x, y, x + w, y + h))
def fit(im, w, h):
    s = min(w / im.width, h / im.height); return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
def paste_center(fr, im, cx, cy): fr.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
def shadowed(im, blur=18, offset=(0, 14), alpha=150):
    pad = blur * 3; out = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, alpha)); sh.putalpha(im.getchannel("A").point(lambda a: a * alpha // 255))
    out.alpha_composite(sh, (pad + offset[0], pad + offset[1])); out = out.filter(ImageFilter.GaussianBlur(blur)); out.alpha_composite(im, (pad, pad)); return out
def glow(im, blur=24, strength=1.0):
    g = im.filter(ImageFilter.GaussianBlur(blur)); a = g.getchannel("A").point(lambda v: min(255, int(v * strength))); g.putalpha(a)
    out = g.copy(); out.alpha_composite(im); return out
def grain(fr, amount=10, seed=0):
    rng = np.random.default_rng(seed); a = np.asarray(fr.convert("RGB")).astype(np.int16); h, w = a.shape[:2]
    n = rng.integers(-amount, amount + 1, ((h + 1) // 2, (w + 1) // 2, 1), dtype=np.int16); n = np.repeat(np.repeat(n, 2, 0), 2, 1)[:h, :w]
    out = Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8)).convert("RGBA")
    if fr.mode == "RGBA": out.putalpha(fr.getchannel("A"))
    return out
def vignette(fr, strength=0.55):
    key = ("vig", strength)
    if key not in _fc:
        y, x = np.ogrid[:H, :W]; d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
        m = np.clip(1 - strength * np.clip(d - 0.45, 0, 1) ** 1.5 * 1.6, 0, 1); _fc[key] = Image.fromarray((m * 255).astype(np.uint8))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 255)); dark.putalpha(_fc[key].point(lambda v: 255 - v)); out = fr.copy(); out.alpha_composite(dark); return out
def letterbox(fr, bar=132):
    d = ImageDraw.Draw(fr); d.rectangle([0, 0, W, bar], fill=(0, 0, 0, 255)); d.rectangle([0, H - bar, W, H], fill=(0, 0, 0, 255)); return fr

TD = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
def text_image(t, f, color=(255, 255, 255), outline=0, outline_color=(0, 0, 0), shadow=None, pad=8):
    """a text as an RGBA image; outline in px; shadow = (blur, dx, dy, alpha)"""
    l, tp, r, b = TD.textbbox((0, 0), t, font=f, stroke_width=outline); w, h = r - l + pad * 2, b - tp + pad * 2
    ex = (shadow[0] * 3 + abs(shadow[1])) if shadow else 0; ey = (shadow[0] * 3 + abs(shadow[2])) if shadow else 0
    im = Image.new("RGBA", (w + 2 * ex, h + 2 * ey), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((ex + pad - l + shadow[1], ey + pad - tp + shadow[2]), t, font=f, fill=(0, 0, 0, shadow[3]), stroke_width=outline, stroke_fill=(0, 0, 0, shadow[3]))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(shadow[0])))
    ImageDraw.Draw(im).text((ex + pad - l, ey + pad - tp), t, font=f, fill=rgba(color), stroke_width=outline, stroke_fill=rgba(outline_color)); return im
def wrap(t, f, width):
    lines = []
    for w_ in t.split():
        if lines and TD.textlength(lines[-1] + " " + w_, font=f) <= width: lines[-1] += " " + w_
        else: lines.append(w_)
    return lines

_svg = {}
def svg_image(path, size, color=None):
    """an SVG rendered through skia at `size` px (longest side); color overrides fill/stroke (hex string)"""
    import skia
    key = (path, size, color)
    if key in _svg: return _svg[key]
    src = open(path, encoding="utf-8").read(); src = src[src.index("<svg"):]
    mw = re.search(r'<svg[^>]*\swidth="([\d.]+)(px)?"', src); mh = re.search(r'<svg[^>]*\sheight="([\d.]+)(px)?"', src)
    if "viewBox" not in src.split(">", 1)[0] and mw and mh: src = src.replace("<svg", f'<svg viewBox="0 0 {mw[1]} {mh[1]}"', 1)
    head, rest = src.split(">", 1); head = re.sub(r'\s(width|height)="[^"]*"', "", head); src = head + ">" + rest   # size comes from the container
    if color:
        src = re.sub(r'fill="(?!none)[^"]*"', f'fill="{color}"', src); src = re.sub(r'stroke="(?!none)[^"]*"', f'stroke="{color}"', src)
        if 'fill="' not in src and 'stroke="' not in src: src = src.replace("<svg", f'<svg fill="{color}"', 1)
    dom = skia.SVGDOM.MakeFromStream(skia.MemoryStream(src.encode("utf-8")))
    surface = skia.Surface(size, size); c = surface.getCanvas(); c.clear(skia.ColorTRANSPARENT); dom.setContainerSize(skia.Size(size, size)); dom.render(c)
    im = Image.fromarray(surface.makeImageSnapshot().toarray()[:, :, [2, 1, 0, 3]]).convert("RGBA"); _svg[key] = im; return im

# ---------------------------------------------------------------- the project: cut, look-aways, words
class Project:
    def __init__(self, base=os.path.join(EDIT, "full_edit", "bulk_uploads_full_edit.mp4"), cutlist=os.path.join(EDIT, "full_edit", "cutlist.md"),
                 lookaways=os.path.join(EDIT, "full_edit", "lookaways.json"), words=os.path.join(EDIT, "full", "words.json")):
        self.base = base; self.pieces = []
        for r in open(cutlist, encoding="utf-8"):
            m = re.match(r"^\| (\d+):([\d.]+) \| ([\d.]+)-([\d.]+) \| (.*?) \|", r)                    # hand-kept list: m:ss | src | line
            if m: self.pieces.append((int(m[1]) * 60 + float(m[2]), float(m[3]), float(m[4]), m[5])); continue
            m = re.match(r"^\| ([\d.]+) \| ([\d.]+)-([\d.]+) \| x[\d.]+ \| (.*?) \|", r)                  # the editing skill's: s | src | push | line
            if m: self.pieces.append((float(m[1]), float(m[2]), float(m[3]), m[4]))
        self.look = json.load(open(lookaways)); self.words = json.load(open(words))
        self.dur = self.pieces[-1][0] + self.pieces[-1][2] - self.pieces[-1][1]
    def L(self, i): return self.pieces[i][0]
    def end(self, i): e0, a, b, _ = self.pieces[i]; return e0 + b - a
    def line(self, i): return self.pieces[i][3]
    def E(self, src):
        for e0, a, b, _ in self.pieces:
            if a - 0.05 <= src <= b + 0.05: return e0 + max(0, src - a)
        raise ValueError(src)
    def words_in(self, i):
        e0, a, b, _ = self.pieces[i]; return [(w["w"].strip(" ,.?!").lower(), e0 + w["s"] - a) for w in self.words if a - 0.05 <= w["s"] <= b]
    def cue(self, i, word, nth=0):
        """edit time at which `word` is spoken in piece i (prefix match, nth occurrence)"""
        hits = [t for w, t in self.words_in(i) if w.startswith(word.lower())]
        if not hits: raise KeyError(f"'{word}' not in piece {i}: {self.line(i)}")
        return hits[min(nth, len(hits) - 1)]
    def looking_away(self, t): return any(x["edit_start"] - 0.05 <= t < x["edit_end"] + 0.05 for x in self.look)

# ---------------------------------------------------------------- face placement
FACE_C = (960, 500)      # where the face sits in the mirrored, barred cut
FACE_SAFE = (0, 72, W, H - 72)  # the cut's black bars (over the recording tag) stay out of every face window and the full-frame face
def face_crop(face_im, w, h, zoom=1.0):
    """crop of the cut around the face at the aspect w:h, as large as the safe area allows / zoom"""
    sx0, sy0, sx1, sy1 = FACE_SAFE; aspect = w / h; cw = min(sx1 - sx0, (sy1 - sy0) * aspect) / zoom; ch = cw / aspect
    x0 = min(max(sx0, FACE_C[0] - cw / 2), sx1 - cw); y0 = min(max(sy0, FACE_C[1] - ch / 2), sy1 - ch)
    return face_im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((int(w), int(h)), Image.BILINEAR)
def full_face(face_im): return face_crop(face_im, W, H)     # the face full frame, without the bars
FACE_ZOOM = {"inset": 1.0}                     # the whole head in every window, the small corner one too (the review cut 8-15% of the head at 1.25)
def place_face(fr, face_im, spec, border=None, shadow=False, zoom=None):
    kind, (x, y, w, h), r = spec; x, y, w, h = int(x), int(y), max(2, int(w)), max(2, int(h)); r = int(r)
    im = face_crop(face_im, w, h, zoom if zoom is not None else FACE_ZOOM.get(kind, 1.0)); im.putalpha(rounded_mask(w, h, r))
    if kind in ("half", "full"): border = None
    if border: ImageDraw.Draw(fr).rounded_rectangle([x - border[1], y - border[1], x + w + border[1] - 1, y + h + border[1] - 1], radius=r + border[1], fill=rgba(border[0]))
    if shadow: im = shadowed(im); fr.alpha_composite(im, (x - 54, y - 54))
    else: fr.paste(im, (x, y), im)                 # paste, not alpha_composite: a window sliding off the edge has a negative x
    return fr

IDENT = ((0, 0, W, H), (0, 0, W, H))
BOARD_FX = None                                # a look's effect on the board layer (e.g. glow), applied after placement, under the face
def glow(im, strength=0.85, radius=12):
    """a soft bloom: a blurred copy screened over the board, so bright strokes glow on a dark ground"""
    rgb = im.convert("RGB"); b = rgb.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(radius / 2)).resize((W, H), Image.BILINEAR)
    a = np.asarray(rgb, np.float32) / 255; g = np.asarray(b, np.float32) / 255 * strength
    return Image.fromarray(((1 - (1 - a) * (1 - g)) * 255).astype(np.uint8)).convert("RGBA")
def place_board(fr, place, bg=(0, 0, 0)):
    out = _place_board(fr, place, bg); return BOARD_FX(out) if BOARD_FX else out
def _place_board(fr, place, bg=(0, 0, 0)):
    """the graphic's frame, cropped to place[0] and drawn into place[1]: how a layout zooms or slides the board.
    Coordinates are in output pixels; a graphic drawn larger (a 4K board) is cropped at its own resolution,
    so enlarging it stays sharp."""
    if place is None or place == IDENT: return fr if fr.size == (W, H) else fr.resize((W, H), Image.LANCZOS)
    (cx, cy, cw, ch), (dx, dy, dw, dh) = place; out = Image.new("RGBA", (W, H), rgba(bg)); k = fr.width / W
    im = fr.crop((int(cx * k), int(cy * k), int((cx + cw) * k), int((cy + ch) * k)))
    if (int(dw), int(dh)) != im.size: im = im.resize((max(1, int(dw)), max(1, int(dh))), Image.LANCZOS)
    out.paste(im, (int(dx), int(dy)), im); return out          # by its alpha: a view past the board's edge shows the background
def _lerp(a, b, k): return tuple(u + (v - u) * k for u, v in zip(a, b))

# ---------------------------------------------------------------- clips (B-roll, archival footage)
class Clip:
    def __init__(self, path): self.cap = cv2.VideoCapture(path); self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30; self.n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)); self.last_i = -2; self.last = None
    def frame(self, t):
        i = max(0, min(self.n - 1, int(t * self.fps)))
        if i == self.last_i: return self.last.copy()
        if i != self.last_i + 1: self.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, f = self.cap.read()
        if ok: self.last = Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)).convert("RGBA")
        self.last_i = i; return self.last.copy()        # a copy: callers draw on it (the face card), and a second read of the frame must come back clean
_clips = {}
def clip(path):
    if path not in _clips: _clips[path] = Clip(path)
    return _clips[path]

# ---------------------------------------------------------------- sound synthesis
SR = 48000
def tone(dur, f0, f1, vol, noise=0.0, decay=4.0):
    n = int(dur * SR); tt = np.arange(n) / SR; fq = np.linspace(f0, f1, n)
    x = np.sin(2 * np.pi * np.cumsum(fq) / SR) * (1 - noise) + noise * np.random.uniform(-1, 1, n); return (x * np.exp(-tt / (dur / decay)) * vol).astype(np.float32)
def pop(vol=0.12): return tone(0.07, 900, 400, vol)
def click(vol=0.06): return tone(0.03, 2500, 1500, vol, noise=0.5)
def whoosh(vol=0.07, dur=0.35): return tone(dur, 200, 1400, vol, noise=0.8, decay=2.5)
def boom(vol=0.14): return tone(0.9, 70, 40, vol, noise=0.15, decay=1.8)
def paper(vol=0.07): return tone(0.18, 3000, 800, vol, noise=0.95, decay=2.0)
def riser(vol=0.05, dur=0.6): return tone(dur, 300, 2000, vol, noise=0.6, decay=100)

# ---------------------------------------------------------------- rendering
def hidden_spans(look, min_face=2.0, lead=0.1):
    """where the face must be off screen: each look-away widened by a leaving transition before it and
    `lead` after it, joined when the face could not stay at least min_face between two of them"""
    merged = []
    for a, b in sorted([max(0.0, x["edit_start"] - TR - lead), x["edit_end"] + lead] for x in look):
        if merged and a - merged[-1][1] < min_face + TR: merged[-1][1] = max(merged[-1][1], b)
        else: merged.append([a, b])
    return merged

# ---------------------------------------------------------------- eye contact: plan the face around the look-aways
def protect_eyes(shots, look, board_at=None, recenter_px=0, bg=(0, 0, 0), min_face=2.0, lead=0.1, quiet=False):
    """Rewrite a shot list so the presenter is never on screen while the eyes are off the lens.

    A style writes the shots it wants (face, card beside a board, full board); this enforces eye contact
    on top of them, from the look-aways measured on the cut (gaze.py --lookaways). For each look-away
    [a, b] the face is hidden over [a - TR - lead, b + lead]: a leaving transition takes TR with the face
    still showing, so it has to start a TR early, and an arriving one starts only once the eyes are back.
    Hidden stretches closer than min_face + TR are joined, so the face never pops in for a moment.
      card shot  -> the card slides out (card_out) and back (slide_card); while it is out the board glides
                    `recenter_px` to the left so it sits in the middle of the frame, not beside an empty space
      face shot  -> board_at(t0, t1) gives the draw of a full-frame graphic for that stretch (the board that
                    is running then); without one the stretch is reported and left, and the render check fails
    Splits keep each piece's draw on the original shot's clock, so a split board plays on without a jump."""
    merged = hidden_spans(look, min_face, lead)
    def on_clock(sh):
        d, t0, dur = sh["draw"], sh["t0"], sh["t1"] - sh["t0"]
        return lambda lt, _dur, ctx: d(ctx["t"] - t0, dur, ctx)
    out = []; unfixed = []
    for sh in shots:
        has_face = sh["kind"] == "face" or bool(sh.get("face"))
        cuts = [(max(a, sh["t0"]), min(b, sh["t1"])) for a, b in merged if b > sh["t0"] and a < sh["t1"]] if has_face else []
        if not cuts: out.append(dict(sh, _card=bool(sh.get("face")), _hidden=sh.get("tr") == "card_out")); continue
        pieces, t = [], sh["t0"]                                                     # (t0, t1, hidden)
        for a, b in cuts:
            if a > t: pieces.append([t, a, False])
            pieces.append([a, b, True]); t = b
        if t < sh["t1"]: pieces.append([t, sh["t1"], False])
        for pc in pieces:                                                            # a face piece too short to settle is hidden too
            if not pc[2] and pc[1] - pc[0] < min_face: pc[2] = True
        for i, (a, b, hidden) in enumerate(pieces):
            first = i == 0
            if not hidden:
                tr = sh["tr"] if first else ("slide_card" if sh.get("face") else "dissolve")
                out.append(dict(sh, t0=a, t1=b, tr=tr, draw=on_clock(sh) if sh.get("draw") else None, _card=bool(sh.get("face")), _hidden=False)); continue
            if sh["kind"] == "face":
                d = board_at(a, b) if board_at else None
                if d is None: unfixed.append((a, b)); out.append(dict(sh, t0=a, t1=b, tr=sh["tr"] if first else "cut", _card=False, _hidden=False)); continue
                out.append(dict(t0=a, t1=b, kind="graphic", draw=d, face=None, tr=sh["tr"] if first and sh["tr"] in ("cut", "push_up", "push_left", "dissolve") else "push_up", _card=False, _hidden=False)); continue
            # a card shot with the card out: the same board, no face
            tr = ("cut" if sh["tr"] == "slide_card" else sh["tr"] if sh["tr"] in ("cut", "push_up", "push_left", "dissolve") else "push_up") if first else "card_out"
            out.append(dict(sh, t0=a, t1=b, tr=tr, face=None, draw=on_clock(sh), _card=False, _hidden=True))
    for i in range(1, len(out)):                                                     # arrivals that assumed a card or a face before them
        prev, cur = out[i - 1], out[i]
        if cur["tr"] == "grow" and not prev.get("face"): cur["tr"] = "dissolve"
        if cur["tr"] == "card_out" and not prev.get("face"): cur["tr"] = "cut"
        if cur["tr"] == "slide_card" and prev["kind"] == "face": cur["tr"] = "shrink"
    if recenter_px:                                                                  # the board glides to the centre while the card is out
        keys = []; v = 0.0
        for sh in out:
            target = -recenter_px if sh["_hidden"] and sh["t1"] - sh["t0"] >= 1.0 else (0.0 if sh["_card"] or sh["kind"] == "face" or not sh["_hidden"] else v)
            keys.append((sh["t0"], v, target)); v = target
        def off(t):
            k = max((k for k in keys if k[0] <= t), key=lambda k: k[0], default=(0, 0, 0))
            return k[1] + (k[2] - k[1]) * inout((t - k[0]) / TR)
        def shifted(d):
            def draw(lt, dur, ctx):
                im = d(lt, dur, ctx); dx = int(round(off(ctx["t"])))
                if dx == 0: return im
                fr = Image.new("RGBA", im.size, rgba(bg, 255)); fr.paste(im, (dx, 0)); return fr
            return draw
        for sh in out:
            if sh["kind"] == "graphic" and (sh["_hidden"] or sh["_card"]): sh["draw"] = shifted(sh["draw"])
    if not quiet:
        moved = [(round(sh["t0"], 2), round(sh["t1"], 2)) for sh in out if sh["_hidden"]]
        print(f"eye contact: face hidden over {len(merged)} stretches; board-only pieces {moved}")
        for a, b in unfixed: print(f"  NOT FIXED {a:.2f}-{b:.2f}: a face shot inside a look-away and no board to show; give board_at() one")
    return out

def nearest_graphic(shots):
    """the fallback for a face shot inside a look-away when the style named no board: hold the graphic shot
    that ends just before it on its last frame, or else the one that starts just after it on its first"""
    gs = [g for g in shots if g["kind"] == "graphic" and g.get("draw")]
    def board_at(a, b):
        before = [g for g in gs if g["t1"] <= a + 1e-6]; after = [g for g in gs if g["t0"] >= b - 1e-6]
        g = max(before, key=lambda g: g["t1"]) if before else (min(after, key=lambda g: g["t0"]) if after else None)
        if g is None: return None
        d, dur = g["draw"], g["t1"] - g["t0"]; lt = dur - 0.01 if before else 0.0; t_at = g["t0"] + lt
        return lambda _lt, _dur, ctx: d(lt, dur, dict(ctx, t=t_at))
    return board_at

CORNER_ORDER = ("tr", "br", "bl", "tl")       # top right first: the house spot for the presenter over code
def corner_rect(c, size=(310, 360), margin=40):
    w, h = size; x = W - margin - w if c[1] == "r" else margin; y = margin if c[0] == "t" else H - margin - h; return (x, y, w, h)

def invite_face(shots, look, project=None, size=(310, 360), margin=40, min_on=2.0, min_face=2.0, lead=0.1, bg=(0, 0, 0), border=None, tol=0.002, step=0.25, quiet=False):
    """The other half of eye contact: whenever the presenter IS on the lens over a full-frame graphic, bring
    the face back in a small corner window, so the viewer keeps a person to follow between the boards.
    Run it after protect_eyes. One shape for the whole video (the side card's shape at half size, same
    border). The corner is chosen by looking at the graphic's own frames every `step` s: the window takes
    the longest stretch in which a corner stays empty, and leaves a full transition before anything is drawn
    there, so it never covers the diagram. The corner used last is preferred, then top right, so the window
    does not hop around. It stays within the eyes-on stretches (hidden_spans), starts a moment after the
    shot's own arrival, pops in and fades out in TR (pip_in / pip_out), and only appears when it can stay at
    least min_on seconds. If a side card arrives while it is up, the window grows into the card."""
    hide = hidden_spans(look, min_face, lead); out = []; last = None; added = []
    def on_clock(sh):
        d, t0, dur = sh["draw"], sh["t0"], sh["t1"] - sh["t0"]
        return lambda lt, _dur, ctx: d(ctx["t"] - t0, dur, ctx)
    def best_run(sh, rect, a, b):
        x, y, w, h = rect; pad = 20; e = min(b + TR, sh["t1"]); ts = list(np.arange(a, e, step)) + [e - 0.01]; free = []    # through the fade-out too
        for t in ts:
            im = sh["draw"](t - sh["t0"], sh["t1"] - sh["t0"], {"face": blank(), "t": t, "project": project})
            box = np.asarray(im.convert("RGB").crop((max(0, x - pad), max(0, y - pad), min(W, x + w + pad), min(H, y + h + pad)))).astype(np.int16)
            free.append((np.abs(box - np.array(bg[:3], np.int16)).max(axis=2) > 24).mean() <= tol)
        runs, start = [], None
        for i, (t, f) in enumerate(zip(ts, free)):
            if f and start is None: start = t
            if not f and start is not None: runs.append((start, ts[i - 1] - TR)); start = None    # gone a transition before the content lands
        if start is not None: runs.append((start, b))
        runs = [(r0, min(r1, b)) for r0, r1 in runs if min(r1, b) > r0]
        return max(runs, key=lambda r: r[1] - r[0], default=None)
    for sh in shots:
        if sh["kind"] != "graphic" or sh.get("face") or sh.get("shows_face") or sh.get("no_face") or not sh.get("draw"): out.append(sh); continue
        wins, t = [], sh["t0"]                                                       # eyes-on stretches inside this shot
        for a, b in hide:
            if b <= sh["t0"] or a >= sh["t1"]: continue
            if a > t: wins.append([t, a])
            t = max(t, b)
        if t < sh["t1"]: wins.append([t, sh["t1"]])
        pieces = []
        for a, b in wins:
            if a <= sh["t0"] + 1e-6: a = sh["t0"] + TR + 0.3                           # let the shot arrive first
            if b - a < min_on: continue
            cands = []
            for rank, c in enumerate(([last] if last else []) + [c for c in CORNER_ORDER if c != last]):
                r = best_run(sh, corner_rect(c, size, margin), a, b)
                if r and r[1] - r[0] >= min_on: cands.append((r[1] - r[0] - 1.5 * rank, r, c))
            if cands:
                _, (r0, r1), c = max(cands); pieces.append((r0, r1, c)); last = c
        if not pieces: out.append(sh); continue
        t = sh["t0"]; base = dict(sh, draw=on_clock(sh))
        for i, (a, b, c) in enumerate(pieces):
            if a > t: out.append(dict(base, t0=t, t1=a, tr=sh["tr"] if t == sh["t0"] else "pip_out"))
            out.append(dict(base, t0=a, t1=b, tr="pip_in" if a > sh["t0"] else sh["tr"], face=("inset", corner_rect(c, size, margin), 18), face_border=border or sh.get("face_border")))
            added.append((round(a, 2), round(b, 2), c)); t = b
        if t < sh["t1"]: out.append(dict(base, t0=t, t1=sh["t1"], tr="pip_out"))
    for i in range(1, len(out)):                                                     # a window that ends on a hard cut fades out instead
        if out[i - 1].get("face") and out[i - 1]["face"][0] == "inset" and not out[i].get("face") and out[i]["kind"] == "graphic" and out[i]["tr"] == "cut": out[i]["tr"] = "pip_out"
    if not quiet: print(f"face in a corner window while on the lens: {len(added)} stretches {[(float(a), float(b), c) for a, b, c in added]}")
    return out

# ---------------------------------------------------------------- face layouts: a few, changed every few seconds while on the lens
CARD_RECT = (90, 180, 620, 720)
HALF_RECT = (0, 0, W // 2, H)                                  # the face fills the left half, edge to edge
MARGIN = 60
HALF_BOARD = (W // 2 + 50, MARGIN, W // 2 - 50 - MARGIN, H - 2 * MARGIN)
LAYOUTS = ("half", "card", "full", "corner")

def _on_clock(sh):
    d, t0, dur = sh["draw"], sh["t0"], sh["t1"] - sh["t0"]
    return lambda lt, _dur, ctx: d(ctx["t"] - t0, dur, ctx)

def free_regions(layout, rect=None):
    """the space the face leaves for the board in a layout; the board's content is fitted into the best one"""
    if layout in ("none", "full"): return [(MARGIN, MARGIN, W - 2 * MARGIN, H - 2 * MARGIN)]
    if layout == "half": return [HALF_BOARD]
    if layout == "card":
        x0 = CARD_RECT[0] + CARD_RECT[2] + 50; return [(x0, MARGIN, W - x0 - MARGIN, H - 2 * MARGIN)]
    x, y, w, h = rect; gap = 40; out = []                          # a corner window: beside it, or above / below it
    out.append((MARGIN, MARGIN, x - gap - MARGIN, H - 2 * MARGIN) if x + w / 2 > W / 2 else (x + w + gap, MARGIN, W - (x + w + gap) - MARGIN, H - 2 * MARGIN))
    out.append((MARGIN, MARGIN, W - 2 * MARGIN, y - gap - MARGIN) if y + h / 2 > H / 2 else (MARGIN, y + h + gap, W - 2 * MARGIN, H - (y + h + gap) - MARGIN))
    return out

def fit_place(bb, regions, smax):
    """scale and centre the content box bb into the region that lets it be largest; returns (scale, place)"""
    if not bb: return 1.0, None
    bw, bh = bb[2] - bb[0], bb[3] - bb[1]; best = None
    for rx, ry, rw, rh in regions:
        if rw <= 0 or rh <= 0: continue
        s = min(rw / bw, rh / bh, smax)
        if best is None or s > best[0]: best = (s, ((bb[0], bb[1], bw, bh), (rx + (rw - bw * s) / 2, ry + (rh - bh * s) / 2, bw * s, bh * s)))
    return best or (0.0, None)

def direct_face(shots, look, project=None, bg=(0, 0, 0), border=None, min_face=2.0, lead=0.1, target=6.5, min_len=2.0,
                min_scale=0.7, smax=2.0, full_change=0.015, full_target=4.5, full_gap=20.0, step=0.25, order=LAYOUTS, quiet=False):
    """Direct where the presenter is while they talk to the lens: a small set of layouts, changed every few
    seconds, so there is more movement than not and the viewer always has the person and the idea in view.
    No dead space: in every layout the board's content is scaled (up to smax) and centred into the space the
    face leaves (free_regions), so the screen is always full; boards drawn at 4K stay sharp when enlarged.

      half    the face fills the left half; the content fills the right half
      card    the face in the side card; the content fills the space right of it
      full    the face full frame, for a few seconds where the board changes least (under full_change of the
              frame in all: a label being written, not a new structure, so nothing that matters is missed)
      corner  a small window in a corner; the content fills the space beside or above it
      none    no face (inside every look-away, or where nothing fits); the content fills the frame

    Each on-lens stretch over a graphic is walked from its start. At each moment, every layout is checked for
    how long it stays possible, read from the graphic's own frames every `step` s and through the layout's
    exit as well. Possible means the content box over that time still fits its free region at min_scale or
    more, or, for full, that the board barely changes. The next layout in `order` that is not the one before
    it and can hold at least `min_len` s takes about `target` s (it runs to the end of the stretch rather than
    leave a sliver), and a full-frame moment is placed whenever `full_gap` s have passed without one. Inside
    one scene every change of layout is a `morph` (TR): the face window and the board move together. A
    face shot next to a graphic morphs too. Pushes between scenes stay pushes. Run it after
    protect_eyes(recenter_px=0), and give graphic shots a "scene" key so that pieces of one board are known
    to be one board."""
    hide = hidden_spans(look, min_face, lead); q = 4; bgv = np.array(bg[:3], np.int16); m = int(np.ceil(TR / step))
    def sample(draw, t0, ref0, ref1, t1):
        ims = []
        for t in np.arange(t0, t1, step):
            im = draw(t - ref0, ref1 - ref0, {"face": blank(), "t": t, "project": project})
            ims.append(np.asarray(im.convert("RGB").resize((W // q, H // q), Image.BILINEAR)).astype(np.int16))
        return ims
    def bbox_of(u):
        if u is None or not u.any(): return None
        ys, xs = np.where(u); pad = 24
        return (max(0, xs.min() * q - pad), max(0, ys.min() * q - pad), min(W, (xs.max() + 1) * q + pad), min(H, (ys.max() + 1) * q + pad))
    def regs(L):
        if L.startswith("corner:"): return free_regions("corner", corner_rect(L[7:]))
        return free_regions(L)
    pieces, chosen = [], []; last, rot, corner_last, last_full = None, 0, None, -1e9
    for sh in shots:
        if sh["kind"] != "graphic" or not sh.get("draw") or sh.get("shows_face") or sh.get("no_face") or sh.get("corner_only"):   # no_face: B-roll;
            # corner_only: a graphic laid out with a free corner (a list, code), left to invite_face, which never scales it
            pieces.append(dict(sh, _role="keep"))
            if sh["kind"] == "face": last, last_full = "full", sh["t1"]
            continue
        segs, t = [], sh["t0"]
        for a, b in hide:
            if b <= sh["t0"] or a >= sh["t1"]: continue
            if a > t: segs.append([t, a, True])
            segs.append([max(a, sh["t0"]), min(b, sh["t1"]), False]); t = min(b, sh["t1"])
        if t < sh["t1"]: segs.append([t, sh["t1"], True])
        clk = _on_clock(sh)
        for a, b, on in segs:
            if b - a < 1e-3: continue
            if not on or b - a < min_len: pieces.append(dict(sh, t0=a, t1=b, draw=clk, _layout="none")); continue
            ims = sample(clk, a, a, b, min(b + TR, sh["t1"]) + 1e-6); n = len(ims); n_in = int(round((b - a) / step))
            masks = [(np.abs(x - bgv).max(axis=2) > 24) for x in ims]
            chg = [np.zeros_like(masks[0])] + [(np.abs(ims[i] - ims[i - 1]).max(axis=2) > 24) for i in range(1, n)]
            def run(L, i):                                                       # samples from i for which L stays possible
                j = i; u = np.zeros_like(masks[0]); uc = np.zeros_like(masks[0])
                while j < n:
                    if L == "full":
                        if j > i:
                            uc = uc | chg[j]
                            if uc.mean() > full_change: break
                    else:
                        u2 = u | masks[j]; bb = bbox_of(u2)
                        if bb and fit_place(bb, regs(L), smax)[0] < min_scale: break
                        u = u2
                    j += 1
                return j - i
            i, none_from = 0, None
            while i < n_in:
                best = None
                own = sh.get("layouts")                                                  # a shot may allow only some layouts (code: the corner)
                cands = list(own) if own else [order[(rot + k) % len(order)] for k in range(len(order))]
                if not own and a + i * step - last_full >= full_gap: cands = ["full"] + [c for c in cands if c != "full"]   # a full-frame moment when one is due
                for L in cands:
                    if L == last and not own: continue
                    keys = [f"corner:{c}" for c in ([corner_last] if corner_last else []) + [c for c in CORNER_ORDER if c != corner_last]] if L == "corner" else [L]
                    for key in keys:
                        r = run(key, i); reach_end = i + r >= n
                        dur = (n_in - i) * step if reach_end else (r - m) * step     # leave room for the exit unless it holds to the end
                        if dur >= min_len: best = (L, key, dur); break
                    if best: break
                if not best:
                    if none_from is None: none_from = i
                    i += 1; continue
                if none_from is not None:
                    pieces.append(dict(sh, t0=a + none_from * step, t1=a + i * step, draw=clk, _layout="none")); none_from = None
                L, key, dur = best; left = (n_in - i) * step; tg = full_target if L == "full" else target
                take = left if (dur >= left and left - min(dur, tg) < min_len) else min(dur, tg)
                k = max(1, int(round(take / step))); t0p, t1p = a + i * step, (b if i + k >= n_in else a + (i + k) * step)
                u = np.zeros_like(masks[0])
                for mk in masks[i:min(n, i + k + m)]: u |= mk
                pc = dict(sh, t0=t0p, t1=t1p, draw=clk, _layout=L, _bb=bbox_of(u))
                if L == "half": pc["face"] = ("half", HALF_RECT, 0)
                elif L == "card": pc["face"] = ("card", CARD_RECT, 16)
                elif L == "full": pc["face"] = ("full", (0, 0, W, H), 0)
                else: corner_last = key[7:]; pc["face"] = ("inset", corner_rect(corner_last), 18); pc["_regs"] = regs(key)
                pc["face_border"] = border if L in ("card", "corner") else None
                pieces.append(pc); chosen.append((round(float(t0p), 2), round(float(t1p), 2), L)); last = L; rot += 1; i += k
                if L == "full": last_full = t1p
            if none_from is not None: pieces.append(dict(sh, t0=a + none_from * step, t1=b, draw=clk, _layout="none"))
    din, dout = np.log(1.08) * step, np.log(1.5) * step                             # zoom in at most 8 %/s; zoom out up to 50 %/s, ahead of time
    def camera(pc, rlist):
        """a view that keeps the content filling the free region: at each moment the content now and in the
        next 0.75 s is fitted, the zoom-out comes before a piece lands, the zoom-in comes slowly afterwards"""
        ts = np.arange(pc["t0"], max(pc["t1"], pc["t0"] + step) + TR, step)
        ims = sample(pc["draw"], ts[0], pc["t0"], pc["t1"], ts[-1] + 1e-6); n = len(ims)
        if not n: return None
        masks = [(np.abs(x - bgv).max(axis=2) > 24) for x in ims]; u_all = np.zeros_like(masks[0])
        for mk in masks: u_all |= mk
        if not u_all.any(): return None
        R = max(rlist, key=lambda r: fit_place(bbox_of(u_all), [r], smax)[0])
        boxes = []
        for k in range(n):
            u = np.zeros_like(masks[0])
            for mk in masks[max(0, k - 1): k + 4]: u |= mk
            boxes.append(bbox_of(u))
        for k in range(1, n):                                                       # empty moments hold the neighbouring view
            if boxes[k] is None: boxes[k] = boxes[k - 1]
        for k in range(n - 2, -1, -1):
            if boxes[k] is None: boxes[k] = boxes[k + 1]
        rw, rh = R[2], R[3]
        ls = np.array([np.log(min(rw / (b[2] - b[0]), rh / (b[3] - b[1]), smax)) for b in boxes])
        f = ls.copy()
        for k in range(1, n): f[k] = min(ls[k], f[k - 1] + din)
        for k in range(n - 2, -1, -1): f[k] = min(f[k], f[k + 1] + dout)
        sc = np.exp(f); cx = np.array([(b[0] + b[2]) / 2 for b in boxes]); cy = np.array([(b[1] + b[3]) / 2 for b in boxes])
        for arr in (cx, cy):                                                       # smooth the pan both ways (no lag), then keep the content in view
            for k in range(1, n): arr[k] = arr[k - 1] + 0.35 * (arr[k] - arr[k - 1])
            for k in range(n - 2, -1, -1): arr[k] = arr[k + 1] + 0.35 * (arr[k] - arr[k + 1])
        views = []
        for k in range(n):
            b = boxes[k]; hw, hh = rw / 2 / sc[k], rh / 2 / sc[k]
            x = min(max(cx[k], b[2] - hw), b[0] + hw) if b[2] - b[0] <= 2 * hw else (b[0] + b[2]) / 2
            y = min(max(cy[k], b[3] - hh), b[1] + hh) if b[3] - b[1] <= 2 * hh else (b[1] + b[3]) / 2
            views.append((x - hw, y - hh, 2 * hw, 2 * hh))
        t0s = ts[0]
        def path(t):
            u = (t - t0s) / step; k = int(np.clip(np.floor(u), 0, n - 1)); k2 = min(n - 1, k + 1); a = float(np.clip(u - k, 0, 1))
            return (_lerp(views[k], views[k2], a), R)
        return path
    for pc in pieces:                                                                # where the board goes: a camera filling the free space
        if pc.get("_role") == "keep": continue
        L = pc["_layout"]
        if L == "none": pc["face"] = None
        pc["place"] = camera(pc, pc.get("_regs") or free_regions(L))
    out = []
    for i, pc in enumerate(pieces):                                                  # how each piece arrives
        if i and not pc.get("no_face"):                                              # B-roll keeps its own arrival
            prev = out[-1]; same = pc["kind"] == "graphic" and prev["kind"] == "graphic" and pc.get("scene") is not None and pc.get("scene") == prev.get("scene")
            face_edge = (pc["kind"] == "face") != (prev["kind"] == "face")
            if same: pc["tr"] = "morph" if (pc.get("face") != prev.get("face") or (pc.get("place") or IDENT) != (prev.get("place") or IDENT)) else "cut"
            elif face_edge and pc["tr"] not in ("push_up", "push_left"): pc["tr"] = "morph"
            elif pc["tr"] in ("slide_card", "card_out", "pip_in", "pip_out", "shrink", "grow", "dissolve"): pc["tr"] = "morph"
        out.append(pc)
    if not quiet:
        from collections import Counter
        on_t = Counter()
        for a, b, L in chosen: on_t[L] += b - a
        print("face layouts while on the lens: " + ", ".join(f"{L} {on_t[L]:.0f} s" for L in on_t))
        print("  " + "  ".join(f"{a:.1f}-{b:.1f} {L}" for a, b, L in chosen))
    return out

def hold_over_empty(shots, project=None, bg=(0, 0, 0), step=0.05, look=0.9, quiet=False):
    """No empty screen: where a graphic shot with no face on it shows nothing (a board cleared before the next one has drawn
    anything, while the eyes keep the face off), hold the last full frame of the board before it, from before its fade-out, until
    something new lands. The video-review skill found three such flashes (0.17-0.27 s) in the Animated Board.
    Run it last, after protect_eyes and direct_face. Graphic shots are sampled every `step` s; 'empty' is a board that does not
    differ from the background; the hold starts at the most visible moment in the `look` s before the empty stretch."""
    bgv = np.array(bg[:3], np.float32)
    def energy(sh, t):
        im = sh["draw"](t - sh["t0"], sh["t1"] - sh["t0"], {"face": blank(), "t": t, "project": project})
        a = np.asarray(im.convert("RGB").resize((192, 108), Image.BILINEAR), np.float32); return float(np.abs(a - bgv).mean())
    cand = lambda sh: sh["kind"] == "graphic" and sh.get("draw") and not sh.get("face") and not sh.get("shows_face") and not sh.get("no_face")
    samples = []                                                                     # (t, shot index, energy) over the faceless graphics
    for k, sh in enumerate(shots):
        if not cand(sh): continue
        for t in np.arange(sh["t0"], sh["t1"] - 1e-6, step): samples.append((float(t), k, energy(sh, t)))
    runs, cur = [], []
    for s_ in samples:
        if s_[2] < 0.6 and (not cur or s_[0] - cur[-1][0] <= step * 1.5): cur.append(s_); continue
        if cur: runs.append(cur)
        cur = [s_] if s_[2] < 0.6 else []
    if cur: runs.append(cur)
    holds = []
    for run in runs:
        a, b = run[0][0], run[-1][0] + step
        before = [s_ for s_ in samples if a - look <= s_[0] < a]
        if not before: continue
        t_full, k_src, e = max(before, key=lambda s_: s_[2])
        if e < 3.0: continue                                                          # nothing worth holding before it
        src = shots[k_src]; holds.append((t_full, b, src))
    if not holds:
        if not quiet: print("no empty screens"); return shots
        return shots
    out = []
    for sh in shots:                                                                  # cut the hold stretches out of the shots
        pieces = [[sh["t0"], sh["t1"]]]
        for h0, h1, _ in holds:
            nxt = []
            for p0, p1 in pieces:
                if h1 <= p0 or h0 >= p1: nxt.append([p0, p1]); continue
                if h0 - p0 > 1e-3: nxt.append([p0, h0])
                if p1 - h1 > 1e-3: nxt.append([h1, p1])
            pieces = nxt
        for p0, p1 in pieces: out.append(dict(sh, t0=p0, t1=p1, tr=sh["tr"] if abs(p0 - sh["t0"]) < 1e-6 else "cut"))
    for h0, h1, src in holds:
        frozen = src["draw"](h0 - src["t0"], src["t1"] - src["t0"], {"face": blank(), "t": h0, "project": project})
        pl = src.get("place"); pl = pl(h0) if callable(pl) else pl
        out.append(dict(t0=h0, t1=h1, kind="graphic", draw=(lambda im: lambda lt, dur, ctx: im.copy())(frozen), place=pl, face=None, tr="cut", scene=src.get("scene"), _hold=True,
                        _hidden=src.get("_hidden", False), _card=False))
    out.sort(key=lambda s_: s_["t0"])
    if not quiet: print("held over empty screens: " + ", ".join(f"{a:.2f}-{b:.2f}" for a, b, _ in holds))
    return out

class Renderer:
    def __init__(self, project, shots, t0, t1, out, sfx=(), bg=(0, 0, 0), overlays=()):
        """overlays: functions t -> RGBA frame or None, laid over the finished frame, whatever the shot or its transition
        (the name lower third: it belongs to the video, not to a shot)"""
        shots = sorted(shots, key=lambda s: s["t0"]); self.overlays = list(overlays)
        if not any("_hidden" in s for s in shots):                                  # every style gets the eye-contact pass, asked for or not
            shots = protect_eyes(shots, project.look, board_at=nearest_graphic(shots), bg=bg)
        self.p = project; self.shots = shots; self.t0, self.t1, self.out = t0, t1, out; self.sfx = list(sfx); self.bg = bg
    def shot_at(self, t):
        for s in self.shots:
            if s["t0"] <= t < s["t1"]: return s
        return self.shots[-1]
    def prev_shot(self, s):
        i = self.shots.index(s); return self.shots[i - 1] if i > 0 else None
    def base_frame(self, s, t, face_im):
        ctx = {"face": face_im, "t": t, "project": self.p}; lt = t - s["t0"]; dur = s["t1"] - s["t0"]
        if s["kind"] == "face":
            fr = full_face(face_im); ov = s["draw"](lt, dur, ctx) if s.get("draw") else None
            if ov is not None: fr.alpha_composite(ov)
            return fr, True
        pl = s.get("place"); pl = pl(t) if callable(pl) else pl                  # a camera path follows the content over time
        fr = place_board(s["draw"](lt, dur, ctx), pl, self.bg)
        if s.get("face"): place_face(fr, face_im, s["face"], s.get("face_border"), s.get("face_shadow", False)); return fr, True
        return fr, bool(s.get("shows_face"))      # a graphic that composes the presenter itself declares it
    def compose(self, t, face_im, prev_last):
        s = self.shot_at(t); lt = t - s["t0"]; tr = s.get("tr", "cut"); e = inout(lt / TR)
        fr, shows = self.base_frame(s, t, face_im)
        if lt >= TR or tr == "cut": return fr, shows
        prev = self.prev_shot(s)
        if prev is None: return fr, shows
        pf = prev_last if prev["kind"] != "face" else full_face(face_im)  # a face keeps talking while it is pushed out
        pshows = prev["kind"] == "face" or bool(prev.get("face")) or bool(prev.get("shows_face"))
        if tr in ("push_left", "push_up"):
            comp = blank(self.bg)
            if tr == "push_left": comp.alpha_composite(pf, (int(-e * W * 0.35), 0)); comp.alpha_composite(fr, (int(W * (1 - e)), 0))
            else: comp.alpha_composite(pf, (0, int(-e * H * 0.35))); comp.alpha_composite(fr, (0, int(H * (1 - e))))
            return comp, shows or pshows
        if tr == "whip":                                               # both frames fly left, blurred along the move by its speed
            k = inout(lt / TR); off = int(k * W); comp = blank(self.bg); comp.paste(pf, (-off, 0)); comp.paste(fr, (W - off, 0))
            b = int(6 * k * (1 - k) * 140) | 1
            if b > 1: comp = Image.fromarray(cv2.blur(np.asarray(comp), (b, 1)))
            return comp, (shows and off > 0) or (pshows and off < W)
        if tr == "dissolve": return Image.blend(pf, fr, e), shows or pshows
        if tr == "dip":
            if lt < TR / 2: return Image.blend(pf, blank(self.bg), inout(lt / (TR / 2))), pshows
            return Image.blend(blank(self.bg), fr, inout((lt - TR / 2) / (TR / 2))), shows
        if tr == "glitch":                                             # RGB split + sliced displacement + noise, 0.3 s
            g = min(1, lt / 0.3); a = np.asarray(fr.convert("RGB")).copy(); rng = np.random.default_rng(int(lt * 1000)); amp = int(40 * (1 - g))
            if amp > 0:
                a[:, :, 0] = np.roll(a[:, :, 0], amp, axis=1); a[:, :, 2] = np.roll(a[:, :, 2], -amp, axis=1)
                for _ in range(8):
                    y0 = rng.integers(0, H - 40); h = rng.integers(8, 60); a[y0:y0 + h] = np.roll(a[y0:y0 + h], rng.integers(-120, 120), axis=1)
                a = np.clip(a.astype(np.int16) + rng.integers(-30, 30, (H, W, 1), dtype=np.int16) * (1 - g), 0, 255).astype(np.uint8)
            return Image.fromarray(a).convert("RGBA"), shows
        if tr == "flash":
            kf = 1 - lt / (TR * 0.6); return (Image.blend(fr, blank((255, 255, 255)), min(1, kf) * 0.9) if kf > 0 else fr), shows
        if tr == "soft_zoom":                                          # the new frame fades in over TR while it settles from slightly small;
            k = inout(lt / TR); z0, z1 = 1.0 + 0.03 * k, 0.94 + 0.06 * ease(lt / TR)     # the old one drifts forward underneath (no hard change)
            base = blank(self.bg); paste_center(base, pf.resize((int(W * z0), int(H * z0)), Image.BILINEAR), W / 2, H / 2)
            top = blank(self.bg); paste_center(top, fr.resize((int(W * z1), int(H * z1)), Image.BILINEAR), W / 2, H / 2)
            return Image.blend(base, top, k), shows or pshows
        if tr == "zoom":                                               # a hard cut; the new frame settles in from slightly small
            z = 0.92 + 0.08 * ease(lt / TR); sm = fr.resize((int(W * z), int(H * z)), Image.BILINEAR); comp = blank(self.bg); paste_center(comp, sm, W / 2, H / 2); return comp, shows
        if tr == "shrink" and s.get("face") and s["face"][0] == "card":      # the full face shrinks into its card over the new graphic
            kind, (x, y, w, h), r = s["face"]; ee = inout(lt / TR); comp = s["draw"](lt, s["t1"] - s["t0"], {"face": face_im, "t": t, "project": self.p})
            cw, ch = W + (w - W) * ee, H + (h - H) * ee; cx, cy = (x + w / 2) * ee + W / 2 * (1 - ee), (y + h / 2) * ee + H / 2 * (1 - ee)
            im = face_crop(face_im, int(cw), int(ch)); im.putalpha(rounded_mask(im.width, im.height, int(r * ee)))
            paste_center(comp, im, cx, cy); return comp, True
        if tr == "morph":                                                    # one layout into the next: face window and board both move
            return self._morph(s, prev, lt, t, face_im)
        if tr == "pip_in" and s.get("face"):                                 # the corner window fades and grows in over the graphic
            return self._fading_face(s["draw"](lt, s["t1"] - s["t0"], {"face": face_im, "t": t, "project": self.p}), face_im, s, ease(lt / TR)), True
        if tr == "pip_out" and prev.get("face"):                             # and fades out, gone before the eyes leave
            return self._fading_face(fr.copy(), face_im, prev, 1 - inout(lt / TR)), True
        if tr == "grow" and prev.get("face") and prev["face"][0] in ("card", "inset"):  # out of a card shot: the card grows back to the full face
            kind, (x, y, w, h), r = prev["face"]; ee = 1 - inout(lt / TR); comp = prev["draw"](prev["t1"] - prev["t0"] - 0.01, prev["t1"] - prev["t0"], {"face": face_im, "t": t, "project": self.p})
            cw, ch = W + (w - W) * ee, H + (h - H) * ee; cx, cy = (x + w / 2) * ee + W / 2 * (1 - ee), (y + h / 2) * ee + H / 2 * (1 - ee)
            im = face_crop(face_im, int(cw), int(ch)); im.putalpha(rounded_mask(im.width, im.height, int(r * ee))); paste_center(comp, im, cx, cy); return comp, True
        if tr == "card_out" and prev.get("face") and prev["face"][0] == "card":     # the face card slides out to the left over the new frame
            kind, (x, y, w, h), r = prev["face"]; comp = fr.copy()
            place_face(comp, face_im, (kind, (int(x - (x + w + 60) * e), y, w, h), r), prev.get("face_border"), prev.get("face_shadow", False)); return comp, True
        if tr == "slide_card" and s.get("face") and prev.get("face") and prev["face"][0] == "inset":   # the corner window grows into the side card
            (x0, y0, w0, h0), r0 = prev["face"][1], prev["face"][2]; (x1, y1, w1, h1), r1 = s["face"][1], s["face"][2]; k = inout(lt / TR)
            comp = s["draw"](lt, s["t1"] - s["t0"], {"face": face_im, "t": t, "project": self.p}); lerp = lambda u, v: int(u + (v - u) * k)
            place_face(comp, face_im, ("card" if k > 0.5 else "inset", (lerp(x0, x1), lerp(y0, y1), lerp(w0, w1), lerp(h0, h1)), lerp(r0, r1)), s.get("face_border")); return comp, True
        if tr == "slide_card" and s.get("face"):
            kind, (x, y, w, h), r = s["face"]; comp = s["draw"](lt, s["t1"] - s["t0"], {"face": face_im, "t": t, "project": self.p})
            place_face(comp, face_im, (kind, (int(x - (x + w + 60) * (1 - e)), y, w, h), r), s.get("face_border"), s.get("face_shadow", False)); return comp, True
        return fr, shows
    def overlay(self, fr, t):
        for ov in self.overlays:
            o = ov(t)
            if o is not None: fr = fr.copy() if fr is not None else fr; fr.alpha_composite(o)
        return fr
    def _layout(self, sh):
        if sh["kind"] == "face": return ("full", (0, 0, W, H), 0), None
        return sh.get("face"), sh.get("place")
    def _morph(self, s, prev, lt, t, face_im):
        f0, p0 = self._layout(prev); f1, p1 = self._layout(s); k = inout(lt / TR); ctx = {"face": face_im, "t": t, "project": self.p}
        if s["kind"] == "graphic": b = s["draw"](lt, s["t1"] - s["t0"], ctx)
        elif prev.get("draw") and prev["kind"] == "graphic": b = prev["draw"](t - prev["t0"], prev["t1"] - prev["t0"], ctx)
        else: b = blank(self.bg)
        p0 = p0(t) if callable(p0) else p0; p1 = p1(t) if callable(p1) else p1
        P0, P1 = p0 or IDENT, p1 or IDENT
        comp = place_board(b, (_lerp(P0[0], P1[0], k), _lerp(P0[1], P1[1], k)), self.bg) if (P0 != IDENT or P1 != IDENT) else place_board(b, None, self.bg)
        off = lambda r: ((-r[2] - 60) if r[0] + r[2] / 2 < W / 2 else W + 60, r[1], r[2], r[3])
        z = lambda f: FACE_ZOOM.get(f[0], 1.0)
        if f0 and f1: spec, zm = ((f1 if k >= 0.5 else f0)[0], _lerp(f0[1], f1[1], k), f0[2] + (f1[2] - f0[2]) * k), z(f0) + (z(f1) - z(f0)) * k
        elif f0: spec, zm = (f0[0], _lerp(f0[1], off(f0[1]), k), f0[2]), z(f0)
        elif f1: spec, zm = (f1[0], _lerp(off(f1[1]), f1[1], k), f1[2]), z(f1)
        else: return comp, False
        bd = (s if k >= 0.5 else prev).get("face_border") or s.get("face_border") or prev.get("face_border")
        place_face(comp, face_im, spec, bd if spec[0] in ("card", "inset") else None, zoom=zm); return comp, True
    def _fading_face(self, comp, face_im, sh, k):
        if k <= 0.01: return comp
        kind, (x, y, w, h), r = sh["face"]; sc = 0.88 + 0.12 * k; nw, nh = int(w * sc), int(h * sc)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); place_face(layer, face_im, (kind, (int(x + (w - nw) / 2), int(y + (h - nh) / 2), nw, nh), int(r * sc)), sh.get("face_border"))
        if k < 0.99: layer.putalpha(layer.getchannel("A").point(lambda a: int(a * k)))
        comp.alpha_composite(layer); return comp
    def stills(self, ts, out, cols=3):
        cap = cv2.VideoCapture(self.p.base); tiles = []
        for t in ts:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read(); fi = Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)).convert("RGBA")
            s = self.shot_at(t); prev = self.prev_shot(s); pl = None
            if prev and prev["kind"] != "face": pl, _ = self.base_frame(prev, prev["t1"] - 0.01, fi)
            fr, shows = self.compose(t, fi, pl); fr = self.overlay(fr, t); im = fr.convert("RGB").resize((640, 360))
            ImageDraw.Draw(im).text((8, 6), f"{t:.2f} {s['kind']}{' FACE+LOOKAWAY' if shows and self.p.looking_away(t) else ''}", fill=(255, 255, 0)); tiles.append(im)
        sheet = Image.new("RGB", (640 * cols, 360 * ((len(tiles) + cols - 1) // cols)))
        for i, im in enumerate(tiles): sheet.paste(im, ((i % cols) * 640, (i // cols) * 360))
        sheet.save(out); return out
    def render(self, make_720=True, mix=0.9):
        p, t0, t1 = self.p, self.t0, self.t1; dur = t1 - t0; sfx = np.zeros(int(dur * SR) + SR, np.float32)
        for t, snd in self.sfx:
            i = int((t - t0) * SR)
            if 0 <= i < len(sfx): sfx[i:i + len(snd)] += snd[:len(sfx) - i]
        sp = self.out.replace(".mp4", "_sfx.wav")
        with wave.open(sp, "w") as w_: w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(SR); w_.writeframes((np.clip(sfx, -1, 1) * 32767).astype(np.int16).tobytes())
        base = cv2.VideoCapture(p.base); base.set(cv2.CAP_PROP_POS_MSEC, t0 * 1000)
        cmd = [FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-ss", f"{t0:.3f}", "-i", p.base, "-i", sp,
               "-filter_complex", f"[1:a][2:a]amix=inputs=2:duration=first:weights=1 {mix}[a]", "-map", "0:v", "-map", "[a]", "-t", f"{dur:.3f}",
               "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", self.out]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE); bad = []; prev_last = None; last = None; n = int(dur * FPS); cur = None
        for i in range(n):
            t = t0 + i / FPS; ok, f = base.read()
            if not ok: f = last
            last = f; face_im = Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)).convert("RGBA")
            s = self.shot_at(t)
            if cur is not None and s is not cur: prev_last = cur_fr
            cur = s
            fr, shows = self.compose(t, face_im, prev_last); cur_fr = fr; fr = self.overlay(fr, t)
            if shows and p.looking_away(t): bad.append(round(t, 2))
            proc.stdin.write(fr.convert("RGB").tobytes())
            if i % 300 == 0: print(f"  {t:6.1f}s", flush=True)
        proc.stdin.close(); proc.wait()
        if make_720: subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i", self.out, "-vf", "scale=1280:720,format=yuv420p", "-c:v", "libx264", "-profile:v", "main", "-crf", "23", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", self.out.replace(".mp4", "_720.mp4")], check=True)
        print("->", self.out, f"{dur:.1f} s; face frames shown while looking away: {len(bad)}", bad[:20]); return bad

def run(style_module, t0=0.0, t1=40.94, stills=None):
    """python <style>.py            renders t0..t1
       python <style>.py stills 1 2 3   contact sheet at those times"""
    p = Project(); shots, sfx = style_module.plan(p, t0, t1)
    r = Renderer(p, shots, t0, t1, style_module.OUT, sfx, getattr(style_module, "BG", (0, 0, 0)))
    if stills: print(r.stills(stills, style_module.OUT.replace(".mp4", "_sheet.png")))
    else: r.render()
def main(style_module):
    a = sys.argv[1:]
    if a[:1] == ["stills"]: run(style_module, stills=[float(x) for x in a[1:]])
    elif len(a) >= 2: run(style_module, float(a[0]), float(a[1]))
    else: run(style_module)
