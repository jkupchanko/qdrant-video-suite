"""KINETIC TYPE: a talking head and words, nothing else. No diagrams, no boards, no layouts that morph.

While the presenter is on the lens, his face fills the frame. It punches in or out at every new line, with a
slow push inside the line. The key words of the line stack as heavy slabs on one side, over a soft shadow,
each one landing on its spoken word. While he looks away, the frame is a full-bleed colour field holding the
spoken sentence, set as large as the frame allows in condensed black type. The whole sentence is ghosted
from the start, so the frame is never empty, and each word lights up as it is said. Key terms come in an
accent colour with a scale slam. Sentences leave with a whip: a fast horizontal move with motion blur.

  python style_kinetic.py 0 41            sample -> out/kinetic_0-41.mp4
  python style_kinetic.py stills 3 9 20   contact sheet
"""
import os, sys, json, re, numpy as np
from PIL import Image, ImageDraw
import engine as E
import style_full as SF                                    # the v2 cut, its look-aways and the word times
W, H = E.W, E.H; TR = E.TR
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\kinetic.mp4"
WORDS = json.load(open(r"C:\Users\ADMIN\camera_audit\styles\out\v2_words.json"))["pieces"]
NAVY, WHITE, RED, VIOLET, TEAL, INK = (11, 15, 25), (245, 247, 250), (220, 36, 76), (96, 71, 255), (0, 150, 136), (14, 18, 30)
HEAVY = "MonaSansDisplayCondensed-Black.ttf"
FIELDS = [dict(bg=NAVY, fg=WHITE, key=RED), dict(bg=WHITE, fg=INK, key=RED), dict(bg=RED, fg=WHITE, key=INK), dict(bg=VIOLET, fg=WHITE, key=INK)]
STOP = set("a an the of to and or is are be it it's its that this these those for with in on at by so we will you can i our your as from into just there there's isn't don't also than then only may more much".split())
WEAK = set("when while before because going gonna start started through bunch different they they're we're let's let what which here really actually things thing get got".split())
KEY = set("qdrant vectors vector data indexing index indexes payloads payload configuration workload options practices dense sparse hnsw memory performance disk ram "
          "quantization shards shard workers batch batches upload uploads uploading latency search compressed overhead parallel".split())

def clean(w): return re.sub(r"[^\w'\-]", "", w)
def lines():
    out = []
    for i, p in enumerate(WORDS):
        ws = p["words"]; items = []
        for k, (w, t) in enumerate(ws):
            t_end = ws[k + 1][1] if k + 1 < len(ws) else p["t1"]
            items.append(dict(w=clean(w), t=t, e=t_end, key=clean(w).lower() in KEY, stop=clean(w).lower() in STOP))
        out.append(dict(i=i, t0=p["t0"], t1=p["t1"], words=[x for x in items if x["w"]]))
    return out

_tc = {}
def word_img(text, size, color):
    k = (text, size, color)
    if k not in _tc:
        f = E.font(HEAVY, size); bb = f.getbbox(text); im = Image.new("RGBA", (bb[2] - bb[0] + 4, int(size * 1.05)), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((-bb[0] + 2, int(size * 0.02)), text, font=f, fill=color + (255,)); _tc[k] = im
    return _tc[k]
def width(text, size): bb = E.font(HEAVY, size).getbbox(text); return bb[2] - bb[0] + 4

def layout(ws, box=(110, 80, W - 220, H - 160), smax=320):
    """break the words into lines and pick the largest size at which the block fills the box: for each line
    count, the breaks that make the widest line narrowest (an exact search), then the size that fits both ways"""
    texts = [x["w"].upper() for x in ws]; n_w = len(texts); wd = [width(t, 100) for t in texts]; sp = 30
    def row_w(i, j): return sum(wd[i:j]) + sp * (j - i - 1)
    best = None
    for n in range(1, min(7, n_w) + 1):
        INF = float("inf"); dp = [[INF] * (n_w + 1) for _ in range(n + 1)]; cut = [[0] * (n_w + 1) for _ in range(n + 1)]; dp[0][0] = 0
        for r in range(1, n + 1):
            for j in range(r, n_w + 1):
                for i in range(r - 1, j):
                    v = max(dp[r - 1][i], row_w(i, j))
                    if v < dp[r][j]: dp[r][j], cut[r][j] = v, i
        rows, j = [], n_w
        for r in range(n, 0, -1): i = cut[r][j]; rows.append(list(range(i, j))); j = i
        rows.reverse(); maxw = dp[n][n_w]
        s_ = min(box[2] / maxw * 100, box[3] / (n * 0.98), smax)
        if best is None or s_ > best[0]: best = (s_, rows)
    s, rows = best; s = int(s); lh = int(s * 0.98); y0 = box[1] + (box[3] - lh * len(rows)) // 2; pos = {}
    for r_i, r in enumerate(rows):
        x = box[0]
        for k in r: pos[k] = (x, y0 + r_i * lh); x += width(texts[k], s) + int(s * 0.28)
    return s, pos, texts

def paste(fr, im, x, y, alpha=1.0, scale=1.0):
    if alpha <= 0.01: return
    if abs(scale - 1) > 0.01: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR); x -= (im.width - im.width / scale) / 2; y -= (im.height - im.height / scale) / 2
    if alpha < 0.99: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda a: int(a * alpha)))
    fr.alpha_composite(im, (int(x), int(y))) if x >= 0 and y >= 0 else fr.paste(im, (int(x), int(y)), im)

def card(line, field):
    """the spoken sentence, ghosted, each word lighting up on its word; key terms slam in"""
    s, pos, texts = layout(line["words"])
    def draw(lt, dur, ctx):
        t = ctx["t"]; fr = Image.new("RGBA", (W, H), field["bg"] + (255,))
        for k, x in enumerate(line["words"]):
            px, py = pos[k]; col = field["key"] if x["key"] else field["fg"]
            a = (t - x["t"] + 0.12) / 0.22                                         # lands a hair before the word
            if a <= 0: paste(fr, word_img(texts[k], s, field["fg"]), px, py, 0.13); continue
            a = min(1, a); e = E.ease(a)
            if x["key"]: paste(fr, word_img(texts[k], s, col), px, py, e, 1.35 - 0.35 * E.back(a))
            else: paste(fr, word_img(texts[k], s, col), px, py + (1 - e) * s * 0.35, 0.13 + 0.87 * e)
        return fr
    return draw

def face_shot(line, zoom0, side):
    """the face full frame, punched to zoom0 and pushing slowly; key words stack as slabs on one side"""
    slabs = [x for x in line["words"] if x["key"] or (not x["stop"] and len(x["w"]) >= 5 and x["w"].lower() not in WEAK and not x["w"].lower().endswith("ly"))][:3]
    size = 128; xs = 90 if side == "left" else None
    scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = np.zeros((H, W), np.float32)
    ramp = np.clip(1 - np.arange(W) / 820, 0, 1) ** 1.4
    g[:] = ramp if side == "left" else ramp[::-1]; scrim.putalpha(Image.fromarray((g * 170).astype(np.uint8))); scrim_rgb = Image.new("RGBA", (W, H), NAVY + (255,)); scrim_rgb.putalpha(scrim.getchannel("A"))
    def draw(lt, dur, ctx):
        t = ctx["t"]; z = zoom0 * (1 + 0.035 * min(1, max(0, (t - line["t0"]) / max(0.1, line["t1"] - line["t0"]))))
        fr = E.face_crop(ctx["face"], W, H, z).convert("RGBA")
        shown = [x for x in slabs if t >= x["t"] - 0.12]
        if not shown: return fr
        fr.alpha_composite(scrim_rgb)
        y = (H - len(slabs) * int(size * 1.02)) // 2
        for k, x in enumerate(slabs):
            if x not in shown: y += int(size * 1.02); continue
            txt = x["w"].upper(); s = min(size, int(size * 500 / max(1, width(txt, size))))         # clear of the face, however long the word
            a = min(1, (t - x["t"] + 0.12) / 0.22); e = E.ease(a)
            im = word_img(txt, s, RED if x["key"] else WHITE); px = 90 if side == "left" else W - 90 - im.width
            paste(fr, im, px + (1 - e) * (-80 if side == "left" else 80), y, e, 1.25 - 0.25 * E.back(a) if x["key"] else 1.0); y += int(size * 1.02)
        return fr
    return draw

def plan(p, t0, t1):
    hide = E.hidden_spans(p.look); S = []; fi = 0; zi = 0; sfx = []
    def on(a, b): return not any(x < b and y > a for x, y in hide)
    mode, run = {}, []                                                            # face or type card per line, so the two alternate
    for line in lines():
        m = "card" if sum(x["key"] for x in line["words"]) >= 2 else "face"
        if len(run) >= 2 and run[-1] == run[-2] == m: m = "face" if m == "card" else "card"
        mode[line["i"]] = m; run.append(m)
    for line in lines():
        if line["t1"] <= t0 or line["t0"] >= t1: continue
        cuts = sorted({line["t0"], line["t1"]} | {x for a, b in hide for x in (a, b) if line["t0"] < x < line["t1"]})
        field = FIELDS[fi % len(FIELDS)]; fi += 1; side = "left" if zi % 2 == 0 else "right"
        for a, b in zip(cuts, cuts[1:]):
            if b - a < 0.05: continue
            if mode[line["i"]] == "face" and on(a, b) and b - a >= 1.5:
                S.append(dict(t0=a, t1=b, kind="graphic", shows_face=True, draw=face_shot(line, 1.0 if zi % 2 == 0 else 1.14, side), tr="whip", _line=line["i"])); zi += 1
            else:
                S.append(dict(t0=a, t1=b, kind="graphic", draw=card(line, field), tr="whip", _line=line["i"]))
    for k in range(1, len(S)):                                                   # a new line on the face is a punch cut; the same line keeps its frame
        same_line = S[k]["_line"] == S[k - 1]["_line"]
        if S[k].get("shows_face") and S[k - 1].get("shows_face"): S[k]["tr"] = "cut"
        elif same_line and not S[k].get("shows_face") and not S[k - 1].get("shows_face"): S[k]["tr"] = "cut"
    S[0]["tr"] = "cut"
    for sh in S:
        if sh["tr"] == "whip": sfx.append((sh["t0"] - 0.05, E.whoosh(0.035, 0.35)))
    for line in lines():
        for x in line["words"]:
            if x["key"] and t0 <= x["t"] < t1: sfx.append((x["t"] - 0.1, E.tone(0.05, 1500, 900, 0.025)))
    for sh in S: sh["_hidden"] = False                                          # this style places the face itself, from the same look-aways
    return S, sfx

if __name__ == "__main__":
    a = sys.argv[1:]; p = SF.project()
    if a[:1] == ["stills"]:
        ts = [float(x) for x in a[1:]]; S, sfx = plan(p, 0, max(ts) + 2); r = E.Renderer(p, S, 0, p.dur, OUT, sfx, NAVY); print(r.stills(ts, OUT.replace(".mp4", "_sheet.png"), cols=4))
    else:
        t0, t1 = (float(a[0]), float(a[1])) if len(a) >= 2 else (0.0, p.dur)
        S, sfx = plan(p, t0, t1); E.Renderer(p, S, t0, t1, OUT if (t0, t1) == (0.0, p.dur) else OUT.replace(".mp4", f"_{int(t0)}-{int(t1)}.mp4"), sfx, NAVY).render()
