"""TERMINAL: the whole video is a live terminal, tmux-style, in amber phosphor.

Panes split and resize between sections (a tiling window manager is the motion vocabulary): commands type
themselves, progress bars fill, the Qdrant log streams on the spoken words, a config diff shows the workloads,
`tree` lists the options, ASCII vectors and an ASCII HNSW graph explain dense vs sparse, htop-style bars show
memory. The presenter is a camera pane (amber duotone) that zooms to full screen on key lines and is replaced
by NO SIGNAL in a look-away while the other panes take its space. CRT finish: scanlines, bloom, vignette.

  python style_term.py 0 41             sample -> out/term_0-41.mp4
  python style_term.py stills 2 6 20    contact sheet
"""
import os, sys, math, numpy as np, skia
from PIL import Image
import engine as E
import style_full as SF
import style_launch as LN
W, H = E.W, E.H
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\term.mp4"
font, col, paint, text, ramp, ease, inout, lerp, lerpr = LN.font, LN.col, LN.paint, LN.text, LN.ramp, E.ease, E.inout, LN.lerp, LN.lerpr
T, L, wd = LN.T, LN.L, LN.wd
BG, A, A2, D, RED, GRN = (12, 9, 4), (255, 176, 46), (255, 214, 140), (125, 84, 22), (255, 110, 80), (190, 230, 90)
MONO, MONO_B = "GeistMono-Regular.ttf", "GeistMono-Bold.ttf"; FS = 34; LH = 50     # set large, so the panes fill
def typed(s, t, ts, cps=55): return "" if t < ts else s[: int((t - ts) * cps)]
def bar(v, n=30, full="█", empty="░"): k = int(round(v * n)); return full * k + empty * (n - k)

# ---------------------------------------------------------------- layouts: pane name -> rect, keyed in time
TOP = 56
LAYOUTS = {
    "zoom":   {"cam": (20, TOP, W - 40, H - TOP - 20)},
    "s1a":    {"upload": (20, TOP, 1150, 470), "log": (20, 540, 1150, 520), "cam": (1190, TOP, 710, 560), "stats": (1190, 630, 710, 430)},
    "s1b":    {"upload": (20, TOP, 1150, 330), "log": (20, 400, 1150, 660), "cam": (1190, TOP, 710, 560), "stats": (1190, 630, 710, 430)},
    "s2":     {"default": (20, TOP, 1300, 420), "rag": (20, 490, 425, 570), "analytics": (455, 490, 425, 570), "saas": (890, 490, 430, 570), "cam": (1340, TOP, 560, 500), "summary": (1340, 570, 560, 490)},
    "s3":     {"tree": (20, TOP, 1180, H - TOP - 20), "cam": (1220, TOP, 680, 520), "notes": (1220, 590, 680, 470)},
    "s4":     {"dense": (20, TOP, 930, 520), "sparse": (970, TOP, 930, 520), "hnsw": (20, 590, 620, 470), "invidx": (660, 590, 610, 470), "cam": (1290, 590, 610, 470)},
    "s4c":    {"dense": (20, TOP, 930, 520), "sparse": (970, TOP, 930, 520), "htop": (20, 590, 1250, 470), "cam": (1290, 590, 610, 470)},
    "s5":     {"cmd": (20, TOP, 1150, 500), "mem": (20, 570, 1150, 490), "cam": (1190, TOP, 710, 560), "olog": (1190, 630, 710, 430)},
    "s5_nocam": {"cmd": (20, TOP, W - 40, 500), "mem": (20, 570, 940, 490), "olog": (980, 570, 920, 490)},
}
KEYS = [(0.0, "zoom"), (0.75, "s1a"), (L[1], "s1b"), (L[2], "s2"), (L[3], "zoom"), (wd(3, "different") - 0.2, "s3"), (L[4], "s4"), (L[7], "s4c"), (L[8], "zoom"), (L[9], "s5")]
ACTIVE = [(0.75, "upload"), (T["qd"] + 0.2, "log"), (L[2], "default"), (T["conf"], "rag"), (T["conf"] + 0.22, "analytics"), (T["conf"] + 0.44, "saas"), (L[3], "tree"),
          (L[4], "dense"), (T["sparse"] - 0.2, "sparse"), (T["hnsw"] - 0.3, "hnsw"), (T["sidx"] - 0.3, "invidx"), (L[7], "htop"), (L[9], "cmd"), (T["disk"], "mem")]
def layout_keys(hide):
    keys = []
    for k, (t0, lay) in enumerate(KEYS):
        t1 = KEYS[k + 1][0] if k + 1 < len(KEYS) else 1e9; cur = t0
        for a, b in hide:
            if b <= cur or a >= t1: continue
            if a > cur: keys.append((cur, lay))
            keys.append((max(a, cur), lay + "_nocam" if lay + "_nocam" in LAYOUTS else lay)); cur = min(b, t1)
        if cur < t1: keys.append((cur, lay))
    return keys
def panes_at(keys, t):
    i = max(j for j, k in enumerate(keys) if t >= k[0]); cur = LAYOUTS[keys[i][1]]; prev = LAYOUTS[keys[i - 1][1]] if i else cur; e = inout(ramp(t, keys[i][0], 0.35))
    out = {}
    for name in set(cur) | set(prev):
        if name in cur and name in prev: out[name] = (lerpr(prev[name], cur[name], e), 1.0)
        elif name in cur: out[name] = (cur[name], e)                                # a new pane opens as the split happens
        else: out[name] = (prev[name], 1 - e)
    return out, keys[i][1]

# ---------------------------------------------------------------- pane contents
def lines(cv, x, y, w, rows, a=1.0):
    f = font(MONO, FS)
    for k, item in enumerate(rows):
        s, c = (item, A) if isinstance(item, str) else item
        if not s: continue
        if c == "inv": cv.drawRect(skia.Rect(x - 6, y + k * LH - FS, x + min(w - 20, f.measureText(s) + 12), y + k * LH + 9), paint(A, a)); cv.drawString(s, x, y + k * LH, f, paint(BG, a)); continue
        while f.measureText(s) > w - 20 and len(s) > 4: s = s[:-2]
        cv.drawString(s, x, y + k * LH, f, paint(c, a))
N_PTS = lambda t: 1_000_000 * ease(ramp(t, T["large"], 6.5))
LOG = [(T["qd"], "qdrant  | collection 'docs' ready"), (T["store"], "storage | vectors: 768 dims, Cosine"), (T["pay"], "payload | storing 3 fields per point"),
       (T["idx"], "index   | building HNSW  m=16  ef=100"), (T["bg"], "optimiz | merging segments 4 -> 2"), (T["bg"] + 0.45, "wal     | flushed 41.2 MB"), (T["bg"] + 0.9, "optimiz | vacuum: 0 deleted points")]
def p_upload(cv, x, y, w, h, t):
    v = N_PTS(t) / 1e6; rows = [typed("$ python bulk_upload.py --batch 256", t, T["up"] - 0.5, 70), ""]
    if t > T["large"] - 0.2:
        rows += [f"points   {bar(v, 20)} {int(v * 100):3d}%", f"batches  {bar(v, 20)} {int(v * 3907):,}/3,907", f"vectors  {bar(v * 0.98, 20)} {int(v * 98):3d}%", "",
                 (f"{int(N_PTS(t)):,} pts   {int(14100 + 400 * math.sin(t * 3)):,}/s", A2)]
    lines(cv, x, y, w, rows)
def p_log(cv, x, y, w, h, t):
    shown = [(ts, s) for ts, s in LOG if t >= ts - 0.2]; rows = []
    for ts, s in shown[-int((h - 40) / LH):]: rows.append((s, "inv") if t - ts < 0.6 else (s, A))
    lines(cv, x, y, w, rows)
SPARK = "▁▂▃▄▅▆▇█"
def p_stats(cv, x, y, w, h, t):
    n = int((w - 40) / font(MONO, FS).measureText('M')); sp = "".join(SPARK[int(4 + 3 * math.sin((t - (n - k) * 0.12) * 2.1) * 0.9)] for k in range(n)) if t > T["large"] else ""
    ram = 0.2 + 0.65 * N_PTS(t) / 1e6
    lines(cv, x, y, w, ["throughput (pts/s)", (sp, A2), "", f"RAM [{bar(ram, 12, '|', ' ')}] {ram * 8:.1f}G", ("", A), ("watch -n1 qdrant-stats", D)])
CFG = {"default": ("default.yaml", ["vectors:", "  size: 768", "  on_disk: false", "hnsw: { m: 16 }", "shards: 1"]),
       "rag": ("rag.yaml", ["10M vectors, low latency", "", "- on_disk: false", "+ on_disk: false", "+ hnsw: { m: 32 }"]),
       "analytics": ("analytics.yaml", ["heavy payload filters", "", "- (no payload index)", "+ payload_index:", "+   category: keyword"]),
       "saas": ("saas.yaml", ["thousands of tenants", "", "- shards: 1", "+ shards: 6", "+ is_tenant: true"])}
def p_cfg(name):
    def draw(cv, x, y, w, h, t):
        title, body = CFG[name]
        if name == "default":
            rows = [typed(f"$ cat {title}", t, T["single"] - 0.4)] + ([(l, A) for l in body] if t > T["single"] else [])
            if t > T["works"]: rows.append(("applies to every workload?", "inv"))
            return lines(cv, x, y, w, rows)
        k = ["rag", "analytics", "saas"].index(name); at = T["conf"] + 0.22 * k; rows = [typed(f"$ diff {title}", t, at - 0.3, 60)]
        if t > at: rows.append((body[0], A2)); rows.append("")
        if t > T["works"] + 0.15 * k: rows.append((body[2], RED))
        if t > T["wf"] + 0.2 + 0.15 * k: rows += [(body[3], GRN), (body[4], GRN)]
        lines(cv, x, y, w, rows)
    return draw
def p_summary(cv, x, y, w, h, t): lines(cv, x, y, w, [typed("3 workloads", t, T["works"]), typed("3 different configs", t, T["wf"] + 0.3), "", (typed("no one-size-fits-all", t, T["wf"] + 0.9), "inv") if t > T["wf"] + 0.9 else ""])
TREE = [("bulk-uploads/", None), ("├── options/            # dense or sparse", T["opt"] - 0.2), ("│   ├── 1_vectors_on_disk.py", T["opt"]), ("│   ├── 2_payload_index_first.py", T["opt"] + 0.12),
        ("│   ├── 3_quantization.py", T["opt"] + 0.24), ("│   └── 4_sparse_index_on_disk.py", T["opt"] + 0.36), ("└── best_practices/     # both", T["best"] - 0.2),
        ("    ├── 5_batch_uploads.py", T["best"]), ("    ├── 6_parallel_workers.py", T["best"] + 0.12), ("    └── 7_multiple_shards.py", T["best"] + 0.24)]
def p_tree(cv, x, y, w, h, t):
    t0 = wd(3, "different"); rows = [typed("$ tree bulk-uploads/", t, t0 - 0.4)]
    for s, ts in TREE:
        if t >= (ts if ts is not None else t0): rows.append((s, "inv") if ts and t - ts < 0.4 else (s, A2 if "py" in s else A))
    lines(cv, x, y, w, rows)
def p_notes(cv, x, y, w, h, t):
    f = font(MONO_B, 150); a1 = ease(ramp(t, T["opt"], 0.3)); a2 = ease(ramp(t, T["best"], 0.3))
    if a1 > 0: cv.drawString("4", x + 40, y + 150, f, paint(A, a1)); text(cv, "options", x + 150, y + 150, 34, A, a1, MONO)
    if a2 > 0: cv.drawString("3", x + 40, y + 330, f, paint(GRN, a2)); text(cv, "best practices", x + 150, y + 330, 34, GRN, a2, MONO)
def p_dense(cv, x, y, w, h, t):
    n = int((w - 40) / font(MONO, FS).measureText('M')); rows = [typed("$ inspect dense[0]   # 768 dims", t, T["dense"] - 0.6, 60), ""]
    if t > T["dense"]:
        for r in range(4): rows.append(("".join(SPARK[int(3.5 + 3.4 * math.sin(k * 1.7 + r * 2.3 + t * 1.4) * math.cos(k * 0.6 - t))] for k in range(n)), A2))
        rows += ["", ("every value set", A)]
    lines(cv, x, y, w, rows)
def p_sparse(cv, x, y, w, h, t):
    n = int((w - 40) / font(MONO, FS).measureText('M')); rows = [typed("$ inspect sparse[0]  # 30,000 dims", t, T["sparse"] - 0.6, 60), ""]
    if t > T["sparse"]:
        for r in range(4): rows.append(("".join("█" if (k * 7 + r * 13) % 37 == 0 else "·" for k in range(n)), A2))
        rows += ["", ("~0.1% of values set", A)]
    lines(cv, x, y, w, rows)
HN = ["L2   o-----------------o", "L1   o-----o-----o-----o", "L0   o--o--o--o--o--o--o--o"]
def p_hnsw(cv, x, y, w, h, t):
    k = ease(ramp(t, T["hnsw"], 1.2)); rows = [typed("$ index dense --type hnsw", t, T["hnsw"] - 0.6, 60), ""]
    total = sum(len(s) for s in HN); n = int(total * k)
    for s in HN: rows.append((s[: max(0, n)], A2)); n -= len(s); rows.append("")
    lines(cv, x, y, w, rows)
def p_inv(cv, x, y, w, h, t):
    rows = [typed("$ index sparse --type inverted", t, T["sidx"] - 0.6, 60), ""]
    for k, l in enumerate(("t12   -> [4, 9, 31]", "t77   -> [4, 12]", "t301  -> [9, 18, 77]", "t5    -> [2]")):
        if t > T["sidx"] + 0.15 * k: rows.append((l, A2))
    lines(cv, x, y, w, rows)
def p_htop(cv, x, y, w, h, t):
    m1, m2 = 0.78 * ease(ramp(t, T["mem"], 1.2)), 0.31 * ease(ramp(t, T["mem"] + 0.2, 1.2)); rows = ["$ htop --qdrant", ""]
    if t > T["mem"] - 0.2: rows += [(f"dense + HNSW  Mem[{bar(m1, 22, '|', ' ')}] {int(m1 * 100):2d}%", RED if m1 > 0.7 else A2), (f"sparse index  Mem[{bar(m2, 22, '|', ' ')}] {int(m2 * 100):2d}%", A2)]
    if t > T["perf"] - 0.2: rows += ["", ("search  dense/RAM 2.1 ms   dense/disk 4.8 ms", A)]
    if t > T["bulk"] - 0.2: rows += ["", ("during bulk uploads, both grow together", "inv")]
    lines(cv, x, y, w, rows)
CODE5 = [("client.update_collection(", T["storing"] - 0.2), ('    "docs",', T["storing"]), ("    vectors_config={", T["storing"] + 0.2), ('        "": models.VectorParamsDiff(', T["storing"] + 0.5), ("            on_disk=True,", T["disk"] - 0.5), ("        )", T["storing"] + 1.0), ("    },", T["storing"] + 1.1), (")", T["storing"] + 1.2)]
def p_cmd(cv, x, y, w, h, t):
    rows = [("# option 01: store dense vectors on disk", D), ">>> "] ; rows = rows[:1]
    for s, ts in CODE5: rows.append((typed(s, t, ts, 65), "inv") if "on_disk" in s and t > T["disk"] else (typed(s, t, ts, 65), A2))
    lines(cv, x, y, w, rows)
def p_mem(cv, x, y, w, h, t):
    k = ease(ramp(t, T["disk"] + 0.2, 1.4)); ram, dsk = lerp(0.85, 0.26, k), lerp(0.05, 0.62, k)
    lines(cv, x, y, w, ["$ watch free -h", "", (f"RAM  [{bar(ram, 22, '|', ' ')}] {ram * 8:.1f}G", RED if ram > 0.7 else GRN), "", (f"DISK [{bar(dsk, 22, '|', ' ')}] {dsk * 64:.0f}G", A2)])
def p_olog(cv, x, y, w, h, t):
    ev = [(T["storing"], "collection docs: config update"), (T["disk"] + 0.1, "vectors: moving to disk (mmap)"), (T["disk"] + 0.5, "segment 1/8 flushed"), (T["disk"] + 0.8, "segment 2/8 flushed")]
    lines(cv, x, y, w, [((s, "inv") if t - ts < 0.5 else (s, A)) for ts, s in ev if t >= ts])
DRAW = dict(upload=p_upload, log=p_log, stats=p_stats, default=p_cfg("default"), rag=p_cfg("rag"), analytics=p_cfg("analytics"), saas=p_cfg("saas"), summary=p_summary,
            tree=p_tree, notes=p_notes, dense=p_dense, sparse=p_sparse, hnsw=p_hnsw, invidx=p_inv, htop=p_htop, cmd=p_cmd, mem=p_mem, olog=p_olog)
TITLE = dict(upload="upload", log="qdrant: logs", stats="stats", default="default.yaml", rag="rag.yaml", analytics="analytics.yaml", saas="saas.yaml", summary="summary", tree="tree",
             notes="notes", dense="dense", sparse="sparse", hnsw="hnsw", invidx="inverted index", htop="htop", cmd="python", mem="memory", olog="qdrant: logs", cam="cam0 · john@qdrant")

# ---------------------------------------------------------------- frame
def amber(im):
    g = np.asarray(im.convert("L")).astype(np.float32) / 255; g = np.clip((g - 0.08) * 1.25, 0, 1)
    out = np.array(BG) * (1 - g[..., None]) + np.array(A2) * g[..., None]; return Image.fromarray(out.astype(np.uint8))
def frame(t, face_im, keys, hide):
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(col(BG)); panes, lay = panes_at(keys, t)
    act = max((a for a in ACTIVE if t >= a[0]), key=lambda a: a[0], default=(0, ""))[1]
    secs = int(t); f = font(MONO, 26); cv.drawRect(skia.Rect(0, 0, W, 44), paint(A, 0.12))
    cv.drawString(f"qdrant-bulk-upload v1.15   [0] {lay.split('_')[0]}   collection: docs", 20, 31, f, paint(A))
    clock = f"00:{secs:02d}.{int((t % 1) * 10)}   ● LIVE"; cv.drawString(clock, W - 20 - f.measureText(clock), 31, f, paint(RED if int(t * 2) % 2 else A))
    for name, ((x, y, w, h), a) in sorted(panes.items(), key=lambda kv: kv[0] == "cam"):
        if a <= 0.02 or w < 30 or h < 30: continue
        on = name == act; cv.drawRect(skia.Rect(x, y, x + w, y + h), paint(A if on else D, a, 3 if on else 2))
        ttl = f" {TITLE.get(name, name)} "; ft = font(MONO, 22); cv.drawRect(skia.Rect(x + 18, y - 13, x + 26 + ft.measureText(ttl), y + 13), paint(BG)); cv.drawString(ttl, x + 22, y + 8, ft, paint(A if on else D, a))
        cv.save(); cv.clipRect(skia.Rect(x + 3, y + 3, x + w - 3, y + h - 3))
        if name == "cam":
            hidden = any(p <= t < q for p, q in hide)
            if not hidden:
                im = amber(E.face_crop(face_im, int(w - 12), int(h - 12), 1.0 if lay == "zoom" else 1.1)).convert("RGBA")
                cv.drawImage(skia.Image.fromarray(np.ascontiguousarray(np.asarray(im)), colorType=skia.kRGBA_8888_ColorType), x + 6, y + 6, skia.SamplingOptions(skia.FilterMode.kLinear), paint((255, 255, 255), a))
            else:
                rd = np.random.default_rng(int(t * 30)); nz = (rd.random(((int(h) - 12) // 4, (int(w) - 12) // 4)) * 90).astype(np.uint8); im = Image.fromarray(nz).resize((int(w - 12), int(h - 12))).convert("RGBA")
                cv.drawImage(skia.Image.fromarray(np.ascontiguousarray(np.asarray(im)), colorType=skia.kRGBA_8888_ColorType), x + 6, y + 6); text(cv, "NO SIGNAL", x + w / 2, y + h / 2, 48, A, 1, MONO_B, align="center")
        else: DRAW[name](cv, x + 26, y + 56, w - 40, h, t)
        cv.restore()
    if lay == "zoom" and T["first"] - 0.3 < t < L[9]:                                 # the chapter banner over the zoomed cam
        k = ease(ramp(t, T["first"] - 0.3, 0.3)); s_ = "OPTION 01 :: STORE DENSE VECTORS ON DISK"[: int(44 * k)]; fb = font(MONO_B, 52)
        cv.drawRect(skia.Rect(60, H - 200, 80 + fb.measureText(s_) + 40, H - 110), paint(A)); cv.drawString(s_, 90, H - 138, fb, paint(BG))
    img = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3].astype(np.float32)
    small = np.asarray(Image.fromarray(img.astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR).resize((W, H), Image.BILINEAR)).astype(np.float32)
    img = 255 - (255 - img) * (255 - small * 0.55) / 255                             # bloom
    img[::3] *= 0.82                                                                  # scanlines
    yy, xx = np.mgrid[0:H:8, 0:W:8]; v = 1 - 0.45 * ((((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2); v = np.asarray(Image.fromarray((v * 255).clip(0, 255).astype(np.uint8)).resize((W, H))).astype(np.float32) / 255
    img *= v[..., None] * (0.97 + 0.03 * math.sin(t * 50))
    return Image.fromarray(img.clip(0, 255).astype(np.uint8)).convert("RGBA")

def plan(p, t0, t1):
    hide = E.hidden_spans(p.look); keys = layout_keys(hide); cuts = sorted({t0, t1} | {x for a, b in hide for x in (a, b) if t0 < x < t1}); S_ = []
    for a, b in zip(cuts, cuts[1:]):
        on = not any(x < b and y > a for x, y in hide)
        S_.append(dict(t0=a, t1=b, kind="graphic", shows_face=on, draw=lambda lt, dur, ctx: frame(ctx["t"], ctx["face"], keys, hide), tr="cut", _hidden=False))
    sfx = [(k[0] - 0.03, E.tone(0.04, 300, 200, 0.03, noise=0.8)) for k in keys[1:] if t0 <= k[0] < t1]
    for ts, s in LOG + [(x, "") for x in (T["single"], T["opt"], T["best"], T["dense"], T["sparse"], T["hnsw"], T["sidx"], T["mem"], T["disk"])]:
        if t0 <= ts < t1: sfx.append((ts - 0.05, E.tone(0.03, 2200, 1800, 0.018, noise=0.5)))
    return S_, sfx

if __name__ == "__main__":
    a = sys.argv[1:]; p = SF.project()
    if a[:1] == ["stills"]:
        ts = [float(x) for x in a[1:]]; S_, sfx = plan(p, 0, max(ts) + 2); r = E.Renderer(p, S_, 0, p.dur, OUT, sfx, BG); print(r.stills(ts, OUT.replace(".mp4", "_sheet.png"), cols=4))
    else:
        t0, t1 = (float(a[0]), float(a[1])) if len(a) >= 2 else (0.0, p.dur)
        S_, sfx = plan(p, t0, t1); E.Renderer(p, S_, t0, t1, OUT if (t0, t1) == (0.0, p.dur) else OUT.replace(".mp4", f"_{int(t0)}-{int(t1)}.mp4"), sfx, BG).render()
