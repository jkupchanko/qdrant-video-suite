"""LISTED SECTIONS: the video as a numbered list, built by itself from the script, the docs page and the cut.

Copied from the most-watched list videos (camera_audit/peers/peer_list_layouts.jpg):
  ByteByteGo  a MASTER LIST of every item (number, picture, name, one line), shown whole at the start and coming
              back with the current item lit before each one; the presenter in a framed window
  Fireship    a numbered card per item, then the TRADEOFF: green BEST FOR and red WATCH FOR chips, with evidence
  NeetCode    a group card when the list turns to a new kind of item

Nothing is drawn by hand for a video. The list is the script's B-roll sections whose docs section has a "Best fit"
line (page_assets.py); the groups are the page's own tags ("Dense vectors", "Sparse vectors", "Dense & sparse
vectors"); the pictures are the page's own figures and code, captured sharp; every word on a chip is the page's own
("Best fit:", "Watch for:"). Each script line gets one beat, in order:
  the hook        the title over the face, then the master list building row by row on its last line
  an item         announcement lines: the list with its row lit; the B-roll line: the list (0.8 s), zooming through
                  the lit row into the page; then the docs figure, the docs code (face small top right, house rule),
                  and on the caveat line the TRADEOFF card (best fit / watch for)
  a group line    the group card (the list, that group lit)
  the wrap-up     the list again, every item ticked off; the last line ends on the logo
  [**Lower third:** NAME | TITLE | 5 s]   the Qdrant name lower third (brand-consistency skill), sliding in from the bottom
                  left on the line above the directive, holding, sliding out; moved to a stretch with the eyes on the lens
Code is typed live: the docs code, character by character with syntax colours, the key line lit once it is all there.
Lines with no beat are the face. The engine then applies eye contact (protect_eyes), the face layouts on every
graphic while the eyes are on the lens (direct_face; B-roll stays faceless), and no empty screen (hold_over_empty).
Transitions come from the script's own values: push in (zoom, 0.5 s) on a card arriving, a white flash where a
camera call says so.

  python style_list.py CONFIG.json            render (CONFIG from video-builder: cut, cutlist, words, lookaways,
  python style_list.py CONFIG.json 0 60       script, assets, broll, out)
  python style_list.py CONFIG.json stills 3 30 60
"""
import os, sys, json, re, math, argparse
import numpy as np, skia
from PIL import Image
import engine as E
import broll_layer as BL
sys.path.insert(0, os.path.expanduser(r"~/.claude/skills/brand-consistency/scripts")); from lower_third import LowerThird
sys.path.insert(0, os.path.expanduser(r"~/.claude/skills/video-review/scripts")); import script_checks as SC

W, H = E.W, E.H
E.TR = 0.8          # transitions 0.8 s, soft (John's boss: "how quick we are transitioning"; 0.5 s zoom-cuts read as abrupt). The eye
                    # rules use the same TR, so the face is still hidden a whole transition before a look-away
SOFT = "soft_zoom"  # a card arriving: the new frame fades in while it settles; leaving a card for the face: a dissolve
CODE_CPS = 65.0     # live code types this fast, then holds at least 3 s with the key line lit
READ_WPS = 3.8      # words a second a viewer reads on a card (with the presenter saying much the same over it)
FONTS = r"C:\Users\ADMIN\camera_audit\fonts"; ASSETS = r"C:\Users\ADMIN\camera_audit\assets"
from brand import C as BC, GROUPS, SYNTAX, LOGO_DIR                                     # every colour from the Qdrant brand skill
BG, CARD, CARD2, BORDER, TXT, MUTED = BC.BG, BC.CARD, BC.CARD2, BC.BORDER, BC.TEXT, BC.MUTED
RED, VIOLET, VIOLET_L, TEAL, TEAL_L, ORANGE = BC.RED, BC.VIOLET, BC.VIOLET_LIGHT, BC.TEAL, BC.CYAN, BC.ORANGE
GROUP_COL = GROUPS[:4]                                                                  # the brand's chart order: red, violet, teal, light blue
F_HEAD = "MonaSansCondensed-Black.ttf"; F_LABEL = "MonaSansCondensed-BlackItalic.ttf"; F_BOLD = "MonaSans-Bold.ttf"; F_REG = "MonaSans-Medium.ttf"
F_MONO = "GeistMono-Regular.ttf"; F_MONO_B = "GeistMono-Medium.ttf"

# ---------------------------------------------------------------- drawing
_tf, _im = {}, {}
def font(name, size):
    if name not in _tf: _tf[name] = skia.Typeface.MakeFromFile(os.path.join(FONTS, name))
    return skia.Font(_tf[name], size)
def col(c, a=1.0): return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(255 * max(0.0, min(1.0, a))))
def paint(c, a=1.0, stroke=0.0, blur=0.0):
    p = skia.Paint(AntiAlias=True, Color=col(c, a))
    if stroke: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p
def ramp(t, t0, d): return max(0.0, min(1.0, (t - t0) / max(1e-6, d)))
def ease(x): return E.ease(max(0.0, min(1.0, x)))
def img(path):
    if path not in _im: _im[path] = skia.Image.open(path)
    return _im[path]
def text(cv, s, x, y, f, c, a=1.0, align="left"):
    w = f.measureText(s); x = x - w / 2 if align == "center" else (x - w if align == "right" else x)
    cv.drawString(s, x, y, f, paint(c, a)); return w
def wrap(s, f, max_w, max_lines=3):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        if f.measureText((cur + " " + w_).strip()) > max_w and cur: lines.append(cur); cur = w_
        else: cur = (cur + " " + w_).strip()
    if cur: lines.append(cur)
    return lines[:max_lines], len(lines) > max_lines
def fit_lines(s, name, size, min_size, max_w, max_lines):
    """the largest size from `size` down to `min_size` at which s fits in max_lines; at min_size it is cut at a sentence end"""
    for sz in range(size, min_size - 1, -2):
        lines, over = wrap(s, font(name, sz), max_w, max_lines)
        if not over: return lines, sz
    first = re.split(r"(?<=[.;])\s", s)[0]                                            # a sentence, never "..."
    return wrap(first, font(name, min_size), max_w, max_lines)[0], min_size
def rrect(cv, x, y, w, h, r, fill=None, a=1.0, stroke=None, sw=2.0, shadow=False):
    R = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)
    if shadow: cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y + 14, w, h), r, r), paint((0, 0, 0), 0.55 * a, blur=26))
    if fill is not None: cv.drawRRect(R, paint(fill, a))
    if stroke is not None: cv.drawRRect(R, paint(stroke, a, sw))
def picture(cv, path, x, y, w, h, a=1.0, mode="contain", focus=(0.5, 0.5), radius=14):
    """an image fitted into the box: contain (all of it) or cover (fill, cropped round focus)"""
    im = img(path); iw, ih = im.width(), im.height(); s = (min if mode == "contain" else max)(w / iw, h / ih)
    dw, dh = iw * s, ih * s; dx, dy = x + (w - dw) * (0.5 if mode == "contain" else focus[0]), y + (h - dh) * (0.5 if mode == "contain" else focus[1])
    cv.save(); cv.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), radius, radius), doAntiAlias=True)
    cv.drawImageRect(im, skia.Rect.MakeXYWH(dx, dy, dw, dh), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), paint((255, 255, 255), a)); cv.restore()
    return (dx, dy, dw, dh) if mode == "contain" else (x, y, w, h)
_thumb = {}
def thumb(path):
    """a row's picture: the figure softened (its 13 px diagram text is picture, not reading: sharp, OCR and viewers try to read it)"""
    if path not in _thumb:
        from PIL import ImageFilter, ImageEnhance
        im = Image.open(path).convert("RGB"); im = im.resize((im.width // 3, im.height // 3), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.6))
        out = path.replace(".png", "_thumb.png"); ImageEnhance.Contrast(im).enhance(0.9).save(out); _thumb[path] = out
    return _thumb[path]

_trim = {}
def trimmed(path, pad=36):
    """a code block captured full width with its code in the left half: crop to the text (plus a margin), cached as a png"""
    if path in _trim: return _trim[path]
    im = Image.open(path).convert("RGB"); a = np.asarray(im).astype(np.int16); bgc = np.median(a.reshape(-1, 3), axis=0)
    ink = (np.abs(a - bgc).max(axis=2) > 40); ink[:, int(a.shape[1] * 0.93):] = False                   # not the copy button at the far right
    ys, xs = np.where(ink)
    if len(xs) == 0: _trim[path] = path; return path
    box = (max(0, xs.min() - pad), max(0, ys.min() - pad), min(a.shape[1], xs.max() + pad), min(a.shape[0], ys.max() + pad))
    out = path.replace(".png", "_trim.png"); im.crop(box).save(out); _trim[path] = out; return out

def surface():
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col(BG)); return s, cv
def to_pil(s): return Image.fromarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGBA")
def chip(cv, s, x, y, c, size=26, a=1.0, fill_a=1.0):
    f = font(F_BOLD, size); w = f.measureText(s); rrect(cv, x, y, w + 28, size + 18, 10, c, a * fill_a); text(cv, s, x + 14, y + size + 3, f, (255, 255, 255), a); return w + 28
def number_chip(cv, n, x, y, s, c, a=1.0):
    rrect(cv, x, y, s, s, s * 0.22, c, a); f = font(F_HEAD, s * 0.62); text(cv, str(n), x + s / 2, y + s * 0.73, f, (255, 255, 255), a, "center")
def tick(cv, x, y, s, c, k):
    if k <= 0: return
    p = skia.Path(); p.moveTo(x, y + s * 0.55); p.lineTo(x + s * 0.4, y + s * 0.92); p.lineTo(x + s, y + s * 0.1)
    meas = skia.PathMeasure(p, False); seg = skia.Path(); meas.getSegment(0, meas.getLength() * min(1, k), seg, True)
    pt = paint(c, 1.0, s * 0.16); pt.setStrokeCap(skia.Paint.kRound_Cap); pt.setStrokeJoin(skia.Paint.kRound_Join); cv.drawPath(seg, pt)

# ---------------------------------------------------------------- the plan's data
class Build:
    def __init__(self, cfg):
        self.cfg = cfg; self.p = E.Project(base=cfg["cut"], cutlist=cfg["cutlist"], lookaways=cfg["lookaways"], words=cfg["raw_words"])
        self.pcs = SC.pieces(cfg["words"]); A = json.load(open(cfg["assets"], encoding="utf-8")); self.page = A
        here = os.path.dirname(os.path.abspath(cfg["assets"]))                         # a relative picture path is next to assets.json
        for sec in A["sections"]:
            for f in sec.get("figures", []) + sec.get("code", []):
                if not os.path.isabs(f["png"]): f["png"] = os.path.join(here, os.path.basename(f["png"]))
        self.title = cfg.get("title") or re.sub(r"\s*[-|]\s*Qdrant.*$", "", A.get("title", "")).strip()
        self.sections = self.script_sections(cfg["script"]); self.items, self.groups = self.list_items()
        self.windows = {w["name"]: w for w in BL.windows(cfg["script"], cfg["broll"], words=cfg["words"], cut=cfg["cut"])}
    def script_sections(self, path):
        """[{heading, lines: [{text, t0, t1, piece}], markers: [...], calls: [...]}] with every line placed in the cut"""
        text_ = re.sub(r"<!--.*?-->", "", open(path, encoding="utf-8").read(), flags=re.S); secs = []; cur = None; self.unplaced = []; self.last_t = None
        for raw in text_.splitlines():
            s = raw.strip()
            if s.startswith("## "):
                head = re.sub(r"\s+\d+:\d{2}.*$", "", s[3:]).strip(); cur = None
                if head.lower().startswith(("count", "notes", "sources")): continue
                cur = dict(heading=head, lines=[], markers=[], calls=[], lowers=[]); secs.append(cur); continue
            if cur is None or not s or s.startswith(("#", "|")): continue
            for m in SC.MARK.finditer(s):
                f = {}
                for part in [x.strip() for x in m.group(3).split("|") if x.strip()]:
                    if ":" in part: k, v = part.split(":", 1); f[k.strip()] = v.strip()
                cur["markers"].append(dict(line=m.group(2).strip(), section=f.get("section", ""), name=f.get("name", ""), after=len(cur["lines"])))
            for m in SC.CALL.finditer(s): cur["calls"].append(dict(text=m.group(0), after=len(cur["lines"])))
            for lw in SC.lower_thirds_in(s): cur["lowers"].append(dict(lw, after=len(cur["lines"])))
            if s.startswith("["): continue
            i, t0, r = SC.line_time(s, self.pcs, self.cfg["cut"])
            if i is None: continue
            if r < 0.38 and SC.recall(s, self.pcs, i) < 0.5: self.unplaced.append(s); continue          # not in the cut: no beat for it
            if self.last_t is not None and t0 < self.last_t - 0.5: self.unplaced.append(s); continue    # out of order: a match elsewhere
            self.last_t = t0
            cur["lines"].append(dict(text=s, piece=i, t0=round(t0, 2), t1=round(self.pcs[i][1], 2), match=round(r, 2)))
        for sec in secs:
            for m in sec["markers"]:
                m["line_index"] = next((k for k, l in enumerate(sec["lines"]) if SC._norm_words(l["text"]) == SC._norm_words(m["line"])), max(0, m["after"] - 1))
        return [s_ for s_ in secs if s_["lines"]]
    def page_section(self, heading):
        n = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
        return next((s for s in self.page["sections"] if n(s["heading"]).startswith(n(heading)[:24])), None)
    def list_items(self):
        items, groups = [], []
        for si, sec in enumerate(self.sections):
            for m in sec["markers"]:
                ps = self.page_section(m["section"]) if m["section"] else None
                if not ps or not ps.get("best_fit") or not ps.get("figures"): continue
                tag = ps.get("tag") or "More"
                if tag not in groups: groups.append(tag)
                title = re.sub(r"^(option|step|tip)\s*\d+\s*[:.-]\s*", "", sec["heading"], flags=re.I).strip()
                sub = re.sub(r"^(option|step|tip)\s*\d+\s*[:.-]\s*", "", ps["heading"], flags=re.I).strip()
                items.append(dict(n=len(items) + 1, title=title, sub=sub if sub.lower() != title.lower() else "", group=tag, gi=groups.index(tag), section=si, marker=m, page=ps,
                                  figure=ps["figures"][0]["png"], code=(ps["code"][0]["png"] if ps.get("code") else None), best=ps["best_fit"], watch=ps.get("watch_for", "")))
        return items, groups

# ---------------------------------------------------------------- devices: each a draw(lt, dur, ctx) -> RGBA frame
def group_word(g): return "both" if "&" in g or " and " in g.lower() else g.split()[0].lower()
def counts(B): return " · ".join(f"{sum(1 for it in B.items if it['group'] == g)} for {group_word(g)}" for g in B.groups)

def list_layout(B):
    """where each row sits: two columns, the groups in order, balanced"""
    rows = []; half = math.ceil(len(B.items) / 2)
    col_items = [[], []]; k = 0                                                       # whole groups per column, the first holding about half
    for gi, g in enumerate(B.groups):
        its = [it for it in B.items if it["group"] == g]
        if k == 0 and len(col_items[0]) + len(its) > half and col_items[0]: k = 1
        col_items[k].extend(its)
    x0s = (60, 790); cw = 700; y_top = 190; rh = 178; gap = 18                          # x 1490..1920 stays free: the presenter's window
    for c, its in enumerate(col_items):
        y = y_top; last_g = None
        for it in its:
            if it["group"] != last_g: rows.append(dict(kind="group", group=it["group"], gi=it["gi"], x=x0s[c], y=y, w=cw)); y += 50; last_g = it["group"]
            rows.append(dict(kind="item", item=it, x=x0s[c], y=y, w=cw, h=rh)); y += rh + gap
    return rows

def draw_list(cv, B, t, lit=None, lit_group=None, build=None, ticks=None, a_all=1.0):
    """the master list. lit: the item number lit (others dimmed); lit_group: a whole group lit; build: {n: t_in}; ticks: {n: t}"""
    bm = img(os.path.join(LOGO_DIR, "png", "Qdrant-Brandmark-Red.png")); cv.drawImageRect(bm, skia.Rect.MakeXYWH(60, 68, 60, 60 * bm.height() / bm.width()), skia.SamplingOptions(skia.FilterMode.kLinear), paint((255, 255, 255), a_all))
    lines, sz = fit_lines(B.title.upper(), F_HEAD, 64, 44, 1330, 1); text(cv, lines[0], 140, 120, font(F_HEAD, sz), TXT, a_all)
    text(cv, counts(B), 142, 162, font(F_REG, 28), MUTED, a_all)
    for r in list_layout(B):
        if r["kind"] == "group":
            c = GROUP_COL[r["gi"] % len(GROUP_COL)]; on = lit_group is None or lit_group == r["group"]
            a = a_all * (1.0 if on else 0.35)
            if build is not None:
                first = min((build.get(it["n"], 1e9) for it in B.items if it["group"] == r["group"]), default=0); a *= ease(ramp(t, first - 0.1, 0.3))
            text(cv, r["group"].upper(), r["x"] + 4, r["y"] + 34, font(F_LABEL, 30), c, a); continue
        it = r["item"]; c = GROUP_COL[it["gi"] % len(GROUP_COL)]; x, y, w, h = r["x"], r["y"], r["w"], r["h"]
        on = (lit is None and lit_group is None) or lit == it["n"] or lit_group == it["group"]; a = a_all * (1.0 if on else 0.32); dy = 0.0
        if build is not None:
            k = ease(ramp(t, build.get(it["n"], 0), 0.35)); a *= k; dy = 30 * (1 - k)
        if a <= 0.01: continue
        cv.save(); cv.translate(0, dy)
        hot = lit == it["n"]
        if hot: rrect(cv, x - 6, y - 6, w + 12, h + 12, 22, None, a, c, 5)
        rrect(cv, x, y, w, h, 18, CARD, a, BORDER if not hot else c, 2 if not hot else 3, shadow=hot)
        done = ticks and it["n"] in ticks and t >= ticks[it["n"]]
        if done:                                                                          # ticked off: the check takes the number's place
            rrect(cv, x + 22, y + (h - 84) / 2, 84, 84, 84 * 0.22, TEAL, a); tick(cv, x + 22 + 20, y + (h - 84) / 2 + 22, 44, (255, 255, 255), ease(ramp(t, ticks[it["n"]], 0.35)))
        else: number_chip(cv, it["n"], x + 22, y + (h - 84) / 2, 84, c, a)
        picture(cv, thumb(it["figure"]), x + 124, y + 20, 238, h - 40, a, mode="cover", focus=(0.5, 0.3), radius=10)
        tx = x + 384; tw = w - 384 - 24
        lines, sz = fit_lines(it["title"], F_BOLD, 38, 30, tw, 2); block = [(ln, F_BOLD, sz, TXT) for ln in lines]
        if it["sub"]:
            room = 2 if len(lines) == 1 else 1                                        # never more than the row holds
            sl, over = wrap(it["sub"], font(F_REG, 24), tw, room)
            if not over: block += [(ln, F_REG, 24, MUTED) for ln in sl]
        hh = sum(b[2] * 1.2 for b in block); ty = y + (h - hh) / 2
        for ln, fn, fs, c_ in block: ty += fs * 1.2; text(cv, ln, tx, ty - fs * 0.25, font(fn, fs), c_, a)
        cv.restore()

def row_rect(B, n):
    r = next(r for r in list_layout(B) if r["kind"] == "item" and r["item"]["n"] == n); return (r["x"], r["y"], r["w"], r["h"])

def d_list(B, **kw):
    def d(lt, dur, ctx):
        s, cv = surface(); draw_list(cv, B, ctx["t"], **kw); return to_pil(s)
    return d

def d_title_over_face(B, t_in, t_out):
    """over the face: the video's title, low and big, gone before it can cover a look away"""
    def d(lt, dur, ctx):
        t = ctx["t"]; k = ease(ramp(t, t_in, 0.4)) * (1 - ease(ramp(t, t_out - 0.4, 0.4)))
        s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(skia.Color(0, 0, 0, 0))
        if k > 0:
            sh = skia.Paint(Shader=skia.GradientShader.MakeLinear([(0, H * 0.55), (0, H)], [col((0, 0, 0), 0), col((0, 0, 0), 0.82 * k)])); cv.drawRect(skia.Rect(0, H * 0.55, W, H), sh)
            f = font(F_HEAD, 104); lines, _ = wrap(B.title.upper(), f, W - 200, 2); y = H - 150 - 100 * (len(lines) - 1) + 40 * (1 - k)
            for ln in lines: text(cv, ln, 100, y, f, TXT, k); y += 100
            chip(cv, counts(B), 102, H - 118 + 30 * (1 - k), RED, 30, k)
        return to_pil(s)
    return d

def d_broll_badge(B, it, w, lead=0.0):
    """the B-roll page full frame, the item's badge over the page's left navigation (never over the docs column)"""
    def d(lt, dur, ctx):
        t = ctx["t"] - w["t0"] - lead; fr = BL.frame(w, max(0.0, t)).convert("RGBA")
        k = ease(ramp(t, 0.15, 0.35)) * (1 - ease(ramp(t, (w["t1"] - w["t0"]) - 0.6, 0.4)))
        if k > 0 and it is not None:
            s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(skia.Color(0, 0, 0, 0)); c = GROUP_COL[it["gi"] % len(GROUP_COL)]
            x, y, bw, bh = 24, H - 330, 330, 290; rrect(cv, x, y, bw, bh, 18, BG, 0.94 * k, c, 3, shadow=True)
            number_chip(cv, it["n"], x + 22, y + 22, 70, c, k); text(cv, it["group"].upper(), x + 108, y + 66, font(F_LABEL, 24), c, k)
            lines, sz = fit_lines(it["title"], F_BOLD, 38, 28, bw - 44, 3); ty = y + 140
            for ln in lines: text(cv, ln, x + 22, ty, font(F_BOLD, sz), TXT, k); ty += sz * 1.18
            fr.alpha_composite(to_pil(s))
        return fr
    return d

def d_list_into_broll(B, it, w, lead=0.8, pre=0.4):
    """the list with this item lit, then a zoom through its row's picture into the page: the B-roll still lands on its line.
    The picture is 16:9 like the page, so the page grows out of it without being stretched."""
    page = d_broll_badge(B, it, w, lead - pre)
    def d(lt, dur, ctx):
        t = ctx["t"] - (w["t0"] - pre)
        if t >= lead: return page(lt, dur, ctx)
        s_, cv = surface(); draw_list(cv, B, ctx["t"], lit=it["n"]); im = to_pil(s_)
        k = ease(ramp(t, lead - 0.42, 0.42))
        if k <= 0: return im
        x, y, rw, rh = row_rect(B, it["n"]); px, py, pw, ph = x + 124, y + 20, 238, rh - 40          # the row's picture
        tw = pw + (W - pw) * k; z = tw / pw; tx, ty = px + (0 - px) * k, py + (0 - py) * k            # its rect now, growing to the frame
        sx0, sy0 = px - tx / z, py - ty / z                                                         # the part of the list still in view
        crop = im.crop((int(sx0), int(sy0), int(sx0 + W / z), int(sy0 + H / z))).resize((W, H), Image.BILINEAR)
        pg = page(lt, dur, dict(ctx, t=w["t0"] - pre + lead)).resize((max(2, int(tw)), max(2, int(tw * H / W))), Image.BILINEAR)
        pg.putalpha(pg.getchannel("A").point(lambda v: int(v * min(1.0, k * 1.6)))); crop.alpha_composite(pg, (int(tx), int(ty))); return crop
    return d

def item_header(cv, it, label, a=1.0, right=W - 60):
    c = GROUP_COL[it["gi"] % len(GROUP_COL)]; number_chip(cv, it["n"], 60, 46, 76, c, a)
    lab_w = font(F_LABEL, 34).measureText(label); lines, sz = fit_lines(it["title"], F_HEAD, 62, 44, right - 156 - lab_w - 60, 1)
    text(cv, lines[0].upper(), 156, 104, font(F_HEAD, sz), TXT, a); text(cv, label, right, 100, font(F_LABEL, 34), c, a, "right")

def d_figure(B, it, t_in):
    """the docs figure, large, panning slowly across it (a still card for 5 s reads as frozen: the review's static check)"""
    def d(lt, dur, ctx):
        t = ctx["t"]; s_, cv = surface(); item_header(cv, it, "FROM THE DOCS")
        im = img(it["figure"]); bw = W - 200; bh = bw * im.height() / im.width()
        if bh > H - 280: bh = H - 280; bw = bh * im.width() / im.height()
        x, y = (W - bw) / 2, 175 + (H - 230 - bh) / 2
        rrect(cv, x - 30, y - 30, bw + 60, bh + 60, 24, CARD, 1.0, BORDER, 2, shadow=True)
        picture(cv, it["figure"], x, y, bw, bh, 1.0)                                    # whole: a pan or a push would cut its words at the card's edge
        # the movement is a focus box going from the figure's upper half to its lower half (docs figures read top to bottom: the
        # default, then the option), the rest dimmed a little
        c = GROUP_COL[it["gi"] % len(GROUP_COL)]; k = E.inout(ramp(t, t_in + max(1.0, dur * 0.45), 0.8)); a_in = ease(ramp(t, t_in + 0.4, 0.4))
        fy = y + (bh / 2) * k; fh = bh / 2
        if a_in > 0:
            dim = paint(BG, 0.45 * a_in); cv.drawRect(skia.Rect(x, y, x + bw, fy - 6), dim); cv.drawRect(skia.Rect(x, fy + fh + 6, x + bw, y + bh), dim)
            rrect(cv, x - 10, fy - 6, bw + 20, fh + 12, 14, None, a_in, c, 4)
        return to_pil(s_)
    return d

def code_of(it):
    """the docs code as written: the page capture doubles every line break (a blank line after each line); one blank line
    where the docs had a real gap"""
    raw = it["page"]["code"][0]["text"].splitlines() if it["page"].get("code") else []
    out, blank = [], 0
    for ln in raw:
        if ln.strip(): (out.append("") if blank >= 2 and out else None); out.append(ln.rstrip()); blank = 0
        else: blank += 1
    return out

def key_line(it, B):
    """which line of the code is the point: the script's own `backticks` for that section if one is in the code, else the line
    sharing most words with the item's title and its docs heading"""
    code = code_of(it)
    if not code: return None, 0
    ticks = [m for c in B.sections[it["section"]]["calls"] for m in re.findall(r"`([^`]+)`", c["text"])]
    for tk in ticks:
        core = re.split(r"[=(]", tk)[0].strip()
        for k, ln in enumerate(code):
            if core and core in ln: return k, len(code)
    tw = set(re.findall(r"[a-z]{4,}", it["title"].lower())); hw = set(re.findall(r"[a-z]{4,}", it["page"]["heading"].lower())) - tw
    best = max(range(len(code)), key=lambda k: 3 * sum(1 for w in tw if w[:5] in code[k].lower()) + sum(1 for w in hw if w[:5] in code[k].lower()))   # the title counts most
    return best, len(code)

SYN = SYNTAX
def tokens(line):
    """[(text, colour key)] for one line of Python: keyword arguments, calls, strings, numbers, comments, the rest"""
    from pygments.lexers import PythonLexer; from pygments.token import Keyword, String, Number, Comment, Operator, Punctuation, Name
    tk = [(ty, v) for ty, v in PythonLexer().get_tokens(line) if v != "\n"]; out = []
    for k, (ty, v) in enumerate(tk):
        nxt = next((v2 for _, v2 in tk[k + 1:] if v2.strip()), "")
        if ty in Keyword or ty in Name.Builtin.Pseudo: c = "kw"
        elif ty in String: c = "str"
        elif ty in Number: c = "num"
        elif ty in Comment: c = "comment"
        elif ty in Operator or ty in Punctuation: c = "punct"
        elif ty in Name and nxt == "=": c = "arg"
        elif ty in Name and nxt == "(": c = "call"
        else: c = "name"
        out.append((v, c))
    return out

def chip_block(cv, label, body, c, x, y, w, size, a):
    """a TRADEOFF chip: its label, then the page's own words in a tinted card; -> its height"""
    lines, _ = wrap(body, font(F_BOLD, size), w - 48, 9); h = 58 + len(lines) * size * 1.3 + 30
    text(cv, label, x, y + 38, font(F_LABEL, 40), c, a); rrect(cv, x, y + 58, w, h - 58, 18, c, 0.15 * a, c, 3 * a)
    ty = y + 58 + 22 + size
    for ln in lines: text(cv, ln, x + 24, ty, font(F_BOLD, size), TXT, a); ty += size * 1.3
    return h

def d_code(B, it, t_in, t_end=None, chips=None):
    """live code: the docs code typed out in the card, character by character with syntax colours (indentation arrives
    with the line, as an editor puts it there), a cursor at the typing point; once it is all there the key line is lit.
    The top right stays clear for the presenter (house rule)"""
    code = code_of(it); kl, nl = key_line(it, B); toks = [tokens(ln) for ln in code]
    t_end = t_end if t_end is not None else t_in + 6.0
    longest = max((len(ln) for ln in code), default=10); x0, y0, cw, ch = 80, 190, (W - 560) if not chips else 1080, H - 300
    if chips:                                                                          # the right column under the presenter's corner: Best for, Watch for
        col_x, col_w, col_y = 1220, W - 1220 - 56, 410; csz = 30
        while csz > 24 and sum(58 + len(wrap(b_, font(F_BOLD, csz), col_w - 48, 9)[0]) * csz * 1.3 + 30 for b_ in (it["best"], chips["watch"]) if b_) + 24 > H - 60 - col_y: csz -= 2
    size = max(24, min(46, (cw - 150) / (0.6 * longest), (ch - 110) / (1.55 * max(1, len(code)))))       # short code reads big on a phone
    fm, lh = font(F_MONO, size), size * 1.55; adv = fm.measureText("M")
    cw = min(cw, max(1000, 28 + adv * 3.4 + adv * longest + 70))                       # the card hugs the code
    typed = [len(ln) - len(ln.lstrip()) for ln in code]                                # the indentation of each line: no time
    n_chars = sum(len(ln) - t_ for ln, t_ in zip(code, typed)); t_type = t_in + 0.45
    rate = max(CODE_CPS, n_chars / max(0.8, (t_end - t_type) - 3.0))                    # done with at least 3 s left to read it, never slow
    if chips: rate = max(rate, CODE_CPS * 1.15)                                        # beside the tradeoff: typed briskly, the card stays up
    t_done = t_type + n_chars / rate
    card_h = min(ch, 92 + lh * len(code) + 30); cy = y0 + max(0, (ch - card_h) / 2 - 20)
    def d(lt, dur, ctx):
        t = ctx["t"]; s_, cv = surface(); item_header(cv, it, "IN CODE", right=W - 420)
        rrect(cv, x0, cy, cw, card_h, 16, CARD, 1.0, BORDER, 2, shadow=True)               # the brand's code snippet: surface, header bar, tab
        rrect(cv, x0, cy, cw, 64, 16, CARD2, 1.0); cv.drawRect(skia.Rect(x0, cy + 48, x0 + cw, cy + 64), paint(CARD2))
        rrect(cv, x0 + 20, cy + 12, 150, 52, 10, CARD, 1.0); text(cv, "Python", x0 + 95, cy + 47, font(F_REG, 24), TXT, 1.0, "center")      # the brand's language tab
        cv.drawRect(skia.Rect(x0 + 20, cy + 60, x0 + 170, cy + 63), paint(RED))
        left = int((t - t_type) * rate) if t >= t_type else 0; gx, tx = x0 + 28, x0 + 28 + adv * 3.4; y = cy + 92 + size
        cur = None; c = GROUP_COL[it["gi"] % len(GROUP_COL)]
        if kl is not None and t >= t_done + 0.25:                                          # the point of it, once it is all there
            k = ease(ramp(t, t_done + 0.25, 0.45)); ly = cy + 92 + kl * lh - lh * 0.12
            rrect(cv, x0 + 12, ly, (cw - 24) * k, lh * 1.04, 8, c, 0.2 * k); rrect(cv, x0 + 12, ly, 6, lh * 1.04, 3, c, k)
        for n, (ln, tk) in enumerate(zip(code, toks)):
            body = len(ln) - typed[n]
            if left <= 0 and n > 0: break
            text(cv, f"{n + 1:>2}", gx, y, fm, SYN["comment"], 1.0)
            show = typed[n] + min(body, max(0, left)); left -= body; x = tx; done = 0
            for v, kind in tk:
                if done >= show: break
                part = v[:show - done]; cv.drawString(part, x, y, fm, paint(SYN[kind])); x += fm.measureText(part); done += len(part)
            if left <= 0 and cur is None: cur = (x, y)
            y += lh
        if cur is None and code: cur = (tx + fm.measureText(code[-1]), y - lh)
        if cur and (t < t_done or int((t - t_done) * 2.2) % 2 == 0):                        # the cursor: steady while typing, then blinking
            cv.drawRect(skia.Rect(cur[0] + 2, cur[1] - size * 0.85, cur[0] + 5, cur[1] + size * 0.2), paint(RED))
        if chips:                                                                      # then the tradeoff arrives beside the code, and stays
            yy = col_y
            for lab, body, c_, at in (("BEST FOR", it["best"], TEAL, chips["t_best"]), ("WATCH FOR", chips["watch"], RED, chips["t_watch"])):
                k = ease(ramp(t, at, 0.5))
                if body and k > 0:
                    cv.save(); cv.translate(40 * (1 - k), 0); hh = chip_block(cv, lab, body, c_, col_x, yy, col_w, csz, k); cv.restore(); yy += hh + 24
                elif body: yy += 58 + len(wrap(body, font(F_BOLD, csz), col_w - 48, 9)[0]) * csz * 1.3 + 30 + 24
        return to_pil(s_)
    return d

def sentences(s): return [x.strip() for x in re.split(r"(?<=[.!?])\s+", s or "") if x.strip()]
def fit_watch(it, seconds):
    """the page's own Watch for, whole sentences only, as many as can be read in `seconds` after the Best for (at least one)"""
    room = (seconds - 1.0) * READ_WPS - len(it["best"].split()); out = []
    for x in sentences(it["watch"]):
        if out and len(" ".join(out + [x]).split()) > room: break
        out.append(x)
    return " ".join(out)

def d_tradeoff(B, it, t_in, t_watch, watch=None):
    """Fireship's TRADEOFF, side by side: the page's own 'Best fit' (teal) and 'Watch for' (red); the figure under them as evidence"""
    watch = it["watch"] if watch is None else watch
    def d(lt, dur, ctx):
        t = ctx["t"]; s, cv = surface(); item_header(cv, it, "TRADEOFF")
        pairs = [(lab, body, c, at) for lab, body, c, at in (("BEST FOR", it["best"], TEAL, t_in), ("WATCH FOR", watch, RED, t_watch)) if body]
        cw = (W - 160 - 40 * (len(pairs) - 1)) / max(1, len(pairs))
        one = min((fit_lines(body, F_BOLD, 54, 36, cw - 70, 8)[1] for _, body, _, _ in pairs), default=54)   # one size for both sides
        for j, (lab, body, c, at) in enumerate(pairs):
            kk = 1.0 if j == 0 else ease(ramp(t, at, 0.35)); x, y = 80 + j * (cw + 40), 230 + 30 * (1 - kk)
            text(cv, lab, x, y + 66, font(F_LABEL, 72), c, kk); rrect(cv, x, y + 100, cw, 620, 24, c, kk * 0.16, c, 3)
            lines, sz = fit_lines(body, F_BOLD, one, one, cw - 70, 8); ty = y + 100 + (620 - len(lines) * sz * 1.25) / 2 + sz * 0.9
            for ln in lines: text(cv, ln, x + 35, ty, font(F_BOLD, sz), TXT, kk); ty += sz * 1.25
        return to_pil(s)
    return d

def d_end(B, t_in):
    def d(lt, dur, ctx):
        t = ctx["t"]; k = ease(ramp(t, t_in, 0.5)); s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(skia.Color(0, 0, 0, 0))
        if k > 0:
            lg = img(os.path.join(LOGO_DIR, "png", "Qdrant-Logo-Red-White.png")); lw = 420 * (0.9 + 0.1 * k); lh = lw * lg.height() / lg.width()
            rrect(cv, W - lw - 120, H - lh - 110, lw + 60, lh + 60, 20, BG, 0.85 * k)
            cv.drawImageRect(lg, skia.Rect.MakeXYWH(W - lw - 90, H - lh - 80, lw, lh), skia.SamplingOptions(skia.FilterMode.kLinear), paint((255, 255, 255), k))
        return to_pil(s)
    return d

def d_where(B, si, t_in, t_out):
    """on the full face: a small chip, top left over the wall, saying where we are: the item's number and name and a dot per
    item (done ones filled, this one lit), or the section's name between items. It slides in from the left and back out, and
    never covers the face. (John: "when I'm full screen... a little animation to help guide the direction of what I'm doing")"""
    sec = B.sections[si]; its = [it for it in B.items if it["section"] == si]; it = its[0] if its else None
    done = {x["n"] for x in B.items if x["section"] < si}
    label = (it["title"] if it else re.sub(r"^(option|step|tip)\s*\d+\s*[:.-]\s*", "", sec["heading"], flags=re.I)).strip()
    f = font(F_BOLD, 30); lines, sz = fit_lines(label, F_BOLD, 30, 24, 470, 1); tw = font(F_BOLD, sz).measureText(lines[0])
    w = (76 if it else 0) + 24 + max(tw, 22 * len(B.items)) + 32; h = 104; x0, y0 = 44, 96
    def d(lt, dur, ctx):
        t = ctx["t"]; k = ease(ramp(t, t_in, 0.5)) * (1 - ease(ramp(t, t_out - 0.45, 0.45)))
        if k <= 0: return None
        s_ = skia.Surface(W, H); cv = s_.getCanvas(); cv.clear(skia.Color(0, 0, 0, 0)); x = x0 - (w + 60) * (1 - k)
        rrect(cv, x, y0, w, h, 16, CARD, 0.9 * k, BORDER, 2, shadow=True); tx = x + 22
        if it:
            c = GROUP_COL[it["gi"] % len(GROUP_COL)]; number_chip(cv, it["n"], x + 18, y0 + (h - 60) / 2, 60, c, k); tx = x + 96
        text(cv, lines[0], tx, y0 + 44, font(F_BOLD, sz), TXT, k)
        for j, x_ in enumerate(B.items):                                             # the list so far, and where this is in it
            cx, cy = tx + 8 + 22 * j, y0 + 74; c = GROUP_COL[x_["gi"] % len(GROUP_COL)]
            if it and x_["n"] == it["n"]: cv.drawCircle(cx, cy, 8, paint(c, k)); cv.drawCircle(cx, cy, 11, paint(c, 0.6 * k, stroke=2))
            elif x_["n"] in done: cv.drawCircle(cx, cy, 6, paint(c, 0.85 * k))
            else: cv.drawCircle(cx, cy, 6, paint(BORDER, k))
        return to_pil(s_)
    return d

def where_chips(B, S):
    """the chip on every full-face stretch of 2.5 s or more between the hook and the wrap-up"""
    starts = [sec["lines"][0]["t0"] for sec in B.sections]
    for s_ in S:
        if s_["kind"] != "face" or s_.get("draw") or s_["t1"] - s_["t0"] < 2.5: continue
        si = max((k for k, t in enumerate(starts) if t <= s_["t0"] + 0.1), default=0)
        if si == 0 or si == len(B.sections) - 1: continue
        dr = d_where(B, si, s_["t0"] + 0.5, s_["t1"] - 0.2)
        s_["draw"] = (lambda d_: lambda lt, du, ctx: d_(lt, du, ctx))(dr)
    return S

# ---------------------------------------------------------------- the plan
def item_devices(B, it, t0, t1, cav_t=None):
    """what an item shows after its B-roll, and for how long, so every card can be read ("I can't actually sit there and
    look at it... it instantly is already gone"). An item with code gets ONE card that stays up for the item's time: the
    code typed out on the left, its key line lit, then the page's Best for and Watch for arriving beside it (Watch for on
    the caveat line), whole sentences only, as many as can be read. Without code, the tradeoff card alone. The docs figure
    comes first only when the item has 4.5 s to spare beyond a comfortable card. -> [(name, t_start, t_end, extra)]"""
    span = t1 - t0
    if span < 3.5: return []
    best_w = len(it["best"].split()); code = code_of(it) if it["code"] else []; n_chars = sum(len(l.strip()) for l in code)
    t_typed = 0.45 + n_chars / (CODE_CPS * 1.15) + 0.3
    def comfortable(watch_words): return (t_typed if code else 0.0) + best_w / READ_WPS + 0.5 + watch_words / READ_WPS + 1.0
    out, t = [], t0
    if span - comfortable(len(it["watch"].split())) >= 4.5:                            # time to spare: the figure first
        fig = min(6.0, span - comfortable(len(it["watch"].split()))); out.append(("figure", t, t + fig, {})); t += fig
    te = t1; d = te - t; ex = {}
    room = (d - (t_typed if code else 0.0) - 1.0) * READ_WPS - best_w; keep = []
    for x in sentences(it["watch"]):                                                  # Watch for: whole sentences that can be read
        if keep and len(" ".join(keep + [x]).split()) > room: break
        keep.append(x)
    ex["watch"] = " ".join(keep); watch_w = len(ex["watch"].split())
    ex["t_best"] = t + (t_typed if code else 0.3)
    want = cav_t if cav_t is not None else ex["t_best"] + best_w / READ_WPS + 0.5
    ex["t_watch"] = max(ex["t_best"] + min(2.0, best_w / READ_WPS), min(want, te - watch_w / READ_WPS - 0.8))
    out.append(("code" if code else "tradeoff", t, te, ex))
    return out

CAVEAT = re.compile(r"\b(may|might|can affect|more expensive|too much|overhead|not always|depend|careful|only)\b", re.I)
def lower_third_at(B, lw, line, graphics):
    """when the name card comes in: on its line, on the face with the eyes on the lens for the whole card; moved later (never
    past the section's next graphic) when a look-away is in the way, the hold shortened to fit, never under 3 s"""
    p = B.p; hold = lw["secs"]; t = line["t0"] + 0.2; nxt = min((g for g in graphics if g > t + 0.5), default=p.dur)
    clear = lambda a, b: not any(p.looking_away(a + k * 0.1) for k in range(int((b - a) / 0.1) + 1))
    span = lambda h: 0.75 + h + 0.6
    while t + span(3.0) <= nxt:
        h = min(hold, nxt - 0.2 - t - span(0))
        if clear(t, t + span(h)): return t, h
        t += 0.2
    return line["t0"] + 0.2, max(3.0, min(hold, nxt - 0.2 - line["t0"] - 0.2 - span(0)))

def plan(B, t0=0.0, t1=None):
    p = B.p; beats = []                                                               # (t, kind, draw, tr, extra)
    lw = next(((sec, l_) for sec in B.sections for l_ in sec.get("lowers", [])), None)
    if lw is None and B.cfg.get("name"):                                             # no directive but a name from the build: the hook's second line
        lw = (B.sections[0], dict(name=B.cfg["name"], title=B.cfg.get("role", ""), secs=5.0, after=min(2, len(B.sections[0]["lines"]))))
    graphic_t = []                                                                    # filled once the beats are known
    lt_line = lw[0]["lines"][max(0, min(lw[1]["after"], len(lw[0]["lines"])) - 1)] if lw else None
    flash_at = []
    for sec in B.sections:
        for c in sec["calls"]:
            if "white flash" in c["text"].lower():
                k = min(c["after"], len(sec["lines"])) - 1; flash_at.append(sec["lines"][max(0, k)]["t0"])
    items_by_sec = {}
    for it in B.items: items_by_sec.setdefault(it["section"], []).append(it)
    group_of_sec = {}
    for si, sec in enumerate(B.sections):                                            # a section with no item that names a group: the group card
        if si in items_by_sec: continue
        nxt = next((B.items[k] for k in range(len(B.items)) if B.items[k]["section"] > si), None)
        if nxt and si > B.items[0]["section"] and any(w_ in " ".join(l["text"] for l in sec["lines"]).lower() for w_ in ("both", "best practice", nxt["group"].split()[0].lower())):
            group_of_sec[si] = nxt["group"]                                          # only between items: the intro is not a group turn
    for si, sec in enumerate(B.sections):
        L = sec["lines"]
        if si == 0:                                                                   # the hook: title over the face, then the list builds
            if lt_line and lw[0] is sec and lt_line is L[0]:                         # the name card first (John: "your name first"), then the title
                lt_end = L[0]["t0"] + 0.2 + 0.75 + lw[1]["secs"] + 0.6
                beats.append((L[0]["t0"], "face", d_title_over_face(B, lt_end + 0.3, max(lt_end + 3.3, L[-1]["t0"] - 0.1)), "cut", {}))
            else:
                t_title = min(L[0]["t1"] + 2.5, L[-1]["t0"]) if not (lt_line and lw[0] is sec) else min(L[0]["t1"] + 2.5, L[-1]["t0"], lt_line["t0"] + 0.1)
                beats.append((L[0]["t0"], "face", d_title_over_face(B, L[0]["t0"] + 0.3, t_title), "cut", {}))
            last = L[-1]; n = len(B.items); build = {it["n"]: last["t0"] + 0.3 + (last["t1"] - last["t0"] - 0.8) * k / max(1, n) for k, it in enumerate(B.items)}
            beats.append((last["t0"], "graphic", d_list(B, build=build), SOFT, dict(scene="list", corner_only=True)))
            continue
        its = items_by_sec.get(si, [])
        if si == len(B.sections) - 1 and not its:                                    # the wrap-up: every item ticked off, then the logo
            ticks = {it["n"]: L[0]["t0"] + 0.5 + 0.35 * k for k, it in enumerate(B.items)}
            beats.append((L[0]["t0"], "graphic", d_list(B, ticks=ticks), SOFT, dict(scene="list", corner_only=True)))
            if len(L) > 1: beats.append((L[-1]["t0"], "face", d_end(B, L[-1]["t0"] + 0.2), "cut", {}))
            continue
        if not its:
            for m in sec["markers"]:                                                  # B-roll that is not a list item (context)
                w = B.windows.get(m["name"])
                if w: beats.append((w["t0"], "broll", d_broll_badge(B, None, w), SOFT, dict(window=w)))
            if si in group_of_sec:
                k = next((k for k, l in enumerate(L) if any(w_ in l["text"].lower() for w_ in ("both", "best practice", "let's cover"))), len(L) - 1)
                beats.append((L[k]["t0"], "graphic", d_list(B, lit_group=group_of_sec[si]), SOFT, dict(scene="list", corner_only=True)))
            continue
        it = its[0]; w = B.windows.get(it["marker"]["name"]); mk = it["marker"]["line_index"]
        if mk > 0: beats.append((L[0]["t0"], "graphic", d_list(B, lit=it["n"]), SOFT, dict(scene="list", corner_only=True)))     # announcement: the row lit
        if w:
            if mk == 0: beats.append((w["t0"] - 0.4, "broll", d_list_into_broll(B, it, w), "cut", dict(window=w, lead=0.4)))
            else: beats.append((w["t0"], "broll", d_broll_badge(B, it, w), SOFT, dict(window=w)))
        after = L[mk + 1:]; t_free = (w["t1"] + (0.4 if mk == 0 else 0.0)) if w else L[mk]["t1"]
        t_stop = B.sections[si + 1]["lines"][0]["t0"] if si + 1 < len(B.sections) else p.dur
        cav_t = max((l["t0"] for l in after if CAVEAT.search(l["text"])), default=None)
        for name, ts, te, ex in item_devices(B, it, t_free, t_stop, cav_t):
            if name == "figure": draw = d_figure(B, it, ts)
            elif name == "code": draw = d_code(B, it, ts, te, chips=ex)
            else: draw = d_tradeoff(B, it, ts, ex["t_watch"], ex["watch"])
            beats.append((ts, "graphic", draw, SOFT, dict(scene=f"item{it['n']}", corner_only=(name == "code"))))
    beats.sort(key=lambda b: b[0])
    # beats to shots: each runs to the next; B-roll runs its window; a line with no beat is the face
    S = []; dur = p.dur if t1 is None else min(p.dur, t1)
    starts = [b[0] for b in beats] + [p.dur]
    cur_t = 0.0
    for k, (ts, kind, draw, tr, ex) in enumerate(beats):
        if ts > cur_t + 0.05 and not S:                                             # before the first beat: the face
            S.append(dict(t0=cur_t, t1=ts, kind="face", tr="cut"))
        end = starts[k + 1]
        if kind == "broll":
            w = ex["window"]; bend = w["t1"] + ex.get("lead", 0.0)
            if S and S[-1]["t1"] > ts: S[-1]["t1"] = ts
            S.append(dict(t0=ts, t1=min(end, bend) if end > ts else bend, kind="graphic", draw=draw, tr=tr, face=None, no_face=True, shows_face=False, scene="broll:" + w["name"]))
            if end > bend + 0.05: S.append(dict(t0=bend, t1=end, kind="face", tr="cut"))
            continue
        if S and S[-1]["t1"] > ts: S[-1]["t1"] = ts
        if kind == "face": S.append(dict(t0=ts, t1=end, kind="face", draw=draw, tr=tr))
        else: S.append(dict(t0=ts, t1=end, kind="graphic", draw=(lambda d_: lambda lt, du, ctx: d_(lt, du, ctx))(draw), tr=tr, face=None, scene=ex.get("scene"),
                            corner_only=bool(ex.get("corner_only"))))
        cur_t = S[-1]["t1"]
    S = [s_ for s_ in S if s_["t1"] - s_["t0"] > 0.02]
    for k_, s_ in enumerate(S):                                                        # the face back after a card: a dissolve, not a cut
        if k_ and s_["kind"] == "face" and s_.get("tr") == "cut" and S[k_ - 1]["kind"] == "graphic": s_["tr"] = "dissolve"
    for s_ in S:                                                                       # the script's chapter flashes
        if any(abs(s_["t0"] - fa) < 0.6 for fa in flash_at): s_["tr"] = "flash"
    if t1 is not None: S = [s_ for s_ in S if s_["t0"] < t1]
    S = E.protect_eyes(S, p.look, board_at=E.nearest_graphic(S), recenter_px=0, bg=BG)
    S = E.direct_face(S, p.look, project=p, bg=BG, border=(BORDER, 3))              # figures and tradeoffs: the face layouts
    S = E.invite_face(S, p.look, project=p, bg=BG, border=(BORDER, 3))              # lists and code: a window over the free corner
    S = E.hold_over_empty(S, p, BG)
    B.overlays, B.overlay_info = [], []
    if lw:
        t_lt, hold = lower_third_at(B, lw[1], lt_line, [s_["t0"] for s_ in S if s_["kind"] == "graphic"])
        L3 = LowerThird(lw[1]["name"], lw[1]["title"], t_lt, hold); B.overlays.append(L3)
        B.overlay_info.append(dict(kind="lower_third", name=lw[1]["name"], title=lw[1]["title"], t_in=round(t_lt, 2), t_out=round(L3.t_out, 2), hold=round(hold, 2), box=L3.box))
    S = where_chips(B, S)                                                              # on the full face: where we are
    sfx = [(s_["t0"] - 0.05, E.whoosh(0.025, 0.6)) for s_ in S if s_.get("tr") in ("zoom", SOFT, "push_up", "morph")]
    sfx += [(o["t_in"], E.whoosh(0.025, 0.35)) for o in B.overlay_info]
    sfx += [(s_["t0"], E.tone(0.6, 1200, 1800, 0.05, noise=0.3, decay=6)) for s_ in S if s_.get("tr") == "flash"]
    return S, sfx

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("config"); ap.add_argument("rest", nargs="*"); a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8")); B = Build(cfg); out = cfg["out"]
    print(f"{len(B.items)} items in {len(B.groups)} groups: " + "; ".join(f"{it['n']}. {it['title']} ({it['group']})" for it in B.items))
    if a.rest[:1] == ["stills"]:
        ts = [float(x) for x in a.rest[1:]]; S, sfx = plan(B, 0, max(ts) + 3); r = E.Renderer(B.p, S, 0, B.p.dur, out, sfx, BG, B.overlays); print(r.stills(ts, out.replace(".mp4", "_sheet.png"), cols=4)); return
    t0, t1 = (float(a.rest[0]), float(a.rest[1])) if len(a.rest) >= 2 else (0.0, B.p.dur)
    S, sfx = plan(B, t0, t1 if (t0, t1) != (0.0, B.p.dur) else None)
    json.dump([dict(t0=round(s_["t0"], 2), t1=round(s_["t1"], 2), kind=s_["kind"], tr=s_.get("tr"), scene=s_.get("scene"), face=(s_.get("face") or [None])[0]) for s_ in S], open(out.replace(".mp4", "_shots.json"), "w"), indent=0)
    json.dump(B.overlay_info, open(out.replace(".mp4", "_overlays.json"), "w"), indent=1)
    if B.overlay_info: print("lower third: " + ", ".join(f'{o["name"]} | {o["title"]} {o["t_in"]:.2f}-{o["t_out"]:.2f} s' for o in B.overlay_info))
    else: print("lower third: none (no [**Lower third:** ...] in the script, no name in the config)")
    E.Renderer(B.p, S, t0, t1, out if (t0, t1) == (0.0, B.p.dur) else out.replace(".mp4", f"_{int(t0)}-{int(t1)}.mp4"), sfx, BG, B.overlays).render()

if __name__ == "__main__":
    main()
