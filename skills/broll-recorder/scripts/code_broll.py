#!/usr/bin/env python
"""code_broll.py: a code snippet typing itself into an IDE-style window, as B-roll (no IDE, no editor needed).

The window looks like VS Code / a dark editor: title bar with traffic lights and a file tab, line numbers,
syntax colours, a blinking cursor. The code appears character by character at a natural, slightly uneven pace,
pauses at line ends, and the view scrolls to keep the cursor in sight. Optionally a terminal line "runs" at the end.

usage: python code_broll.py SNIPPET.py --out clip.mp4 [--lang python] [--cps 28] [--filename upload.py]
       [--theme dark|light] [--width 1920 --height 1080] [--card] [--bg "#F5F4F0"] [--focus-lines 12-18]
       [--reveal all|typed] [--hold 1.5] [--run "python upload.py" --run-output "Uploaded 1,000,000 points in 41s"]

--card        put the editor in the clean cream card (rounded, shadow) instead of filling the frame
--reveal      typed (default): characters type in; all: the full snippet is shown from the start (for pushes only)
--focus-lines after typing, push into these lines (1-based) and hold
"""
import argparse, math, os, re, subprocess, sys, tempfile, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def find_font(names, fallback_size=20):
    dirs = [os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts"), os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
            "/Library/Fonts", "/System/Library/Fonts", os.path.expanduser("~/Library/Fonts"), "/usr/share/fonts", "/usr/share/fonts/truetype/dejavu"]
    for n in names:
        for d in dirs:
            p = os.path.join(d, n)
            if os.path.exists(p): return p
    return None

MONO = find_font(["CascadiaCode.ttf", "CascadiaMono.ttf", "GeistMono-Regular.ttf", "JetBrainsMono-Regular.ttf", "FiraCode-Regular.ttf", "consola.ttf", "Menlo.ttc", "DejaVuSansMono.ttf"])
UI = find_font(["MonaSans-Medium.ttf", "Inter-Medium.ttf", "segoeui.ttf", "Helvetica.ttc", "DejaVuSans.ttf"])

THEMES = {
    "dark": {"bg": (30, 30, 30), "bar": (40, 40, 40), "tab": (30, 30, 30), "tabtext": (220, 220, 220), "gutter": (133, 133, 133), "text": (212, 212, 212),
             "kw": (197, 134, 192), "kw2": (86, 156, 214), "str": (206, 145, 120), "num": (181, 206, 168), "com": (106, 153, 85), "fn": (220, 220, 170), "cls": (78, 201, 176), "cursor": (212, 212, 212), "line": (40, 40, 40)},
    "qdrant": {"bg": (11, 15, 25), "bar": (17, 24, 36), "tab": (11, 15, 25), "tabtext": (240, 243, 250), "gutter": (101, 107, 127), "text": (240, 243, 250),
               "kw": (199, 146, 234), "kw2": (130, 170, 255), "str": (255, 177, 140), "num": (181, 206, 168), "com": (101, 107, 127), "fn": (255, 220, 150), "cls": (120, 220, 200), "cursor": (240, 243, 250), "line": (20, 26, 42)},
    "light": {"bg": (255, 255, 255), "bar": (243, 243, 243), "tab": (255, 255, 255), "tabtext": (60, 60, 60), "gutter": (170, 170, 170), "text": (36, 41, 46),
              "kw": (175, 0, 219), "kw2": (0, 0, 255), "str": (163, 21, 21), "num": (9, 134, 88), "com": (0, 128, 0), "fn": (121, 94, 38), "cls": (38, 127, 153), "cursor": (36, 41, 46), "line": (245, 245, 245)},
}
KEYWORDS = {
    "python": "def class return import from as if else elif for while in not and or with try except finally raise yield lambda pass break continue True False None async await".split(),
    "javascript": "const let var function return import from export default if else for while in of not new class extends async await try catch finally throw true false null undefined this".split(),
    "typescript": "const let var function return import from export default if else for while in of new class extends async await try catch finally throw true false null undefined this interface type implements".split(),
    "rust": "fn let mut use pub struct impl enum match if else for while loop return async await Some None Ok Err true false self crate mod".split(),
    "go": "func package import return if else for range var const type struct interface map go defer nil true false".split(),
    "bash": "if then else fi for do done echo export cd ls cat curl pip python docker".split(),
    "json": [],
}
def tokenize(line, lang):
    """very small highlighter: comments, strings, numbers, keywords, function calls, Capitalised names"""
    out = []; i = 0; kws = set(KEYWORDS.get(lang, KEYWORDS["python"]))
    cstart = "#" if lang in ("python", "bash") else "//"
    while i < len(line):
        c = line[i]
        if line.startswith(cstart, i):
            out.append((line[i:], "com")); break
        if c in "\"'`":
            j = i + 1
            while j < len(line) and line[j] != c: j += 1 if line[j] != "\\" else 2
            out.append((line[i:j + 1], "str")); i = j + 1; continue
        m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", line[i:])
        if m:
            w = m.group(0); nxt = line[i + len(w):i + len(w) + 1]
            kind = "kw" if w in kws else ("fn" if nxt == "(" else ("cls" if w[:1].isupper() else "text"))
            if lang == "json": kind = "text"
            out.append((w, kind)); i += len(w); continue
        m = re.match(r"\d+(\.\d+)?", line[i:])
        if m: out.append((m.group(0), "num")); i += len(m.group(0)); continue
        out.append((c, "text")); i += 1
    return out

def render_frame(lines_shown, cursor_pos, theme, W, H, font, ui, filename, scroll_line, line_h, pad, run_text, run_out, cursor_on):
    T = THEMES[theme]
    im = Image.new("RGB", (W, H), T["bg"]); d = ImageDraw.Draw(im)
    bar = 44
    d.rectangle([0, 0, W, bar], fill=T["bar"])
    for k, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([18 + k * 22, bar // 2 - 6, 30 + k * 22, bar // 2 + 6], fill=col)
    tw = d.textlength(filename, font=ui)
    d.rectangle([100, 8, 100 + tw + 36, bar], fill=T["tab"])
    d.text((118, bar // 2), filename, font=ui, fill=T["tabtext"], anchor="lm")
    gutter_w = 64
    y0 = bar + pad
    visible = max(1, (H - y0 - pad) // line_h)
    for row in range(visible):
        li = scroll_line + row
        if li >= len(lines_shown): break
        y = y0 + row * line_h
        if cursor_pos and cursor_pos[0] == li: d.rectangle([gutter_w, y - 2, W, y + line_h - 2], fill=T["line"])
        d.text((gutter_w - 16, y + line_h // 2), str(li + 1), font=font, fill=T["gutter"], anchor="rm")
        x = gutter_w + 12
        for tok, kind in tokenize(lines_shown[li], "python" if "lang" not in globals() else LANG):
            d.text((x, y + line_h // 2), tok, font=font, fill=T[kind], anchor="lm"); x += d.textlength(tok, font=font)
        if cursor_pos and cursor_pos[0] == li and cursor_on:
            cx = gutter_w + 12 + d.textlength(lines_shown[li][:cursor_pos[1]], font=font)
            d.rectangle([cx, y + 2, cx + 2, y + line_h - 4], fill=T["cursor"])
    if run_text:
        th = line_h * (2 if run_out else 1) + pad * 2
        d.rectangle([0, H - th, W, H], fill=T["bar"]); d.line([0, H - th, W, H - th], fill=T["gutter"], width=1)
        d.text((gutter_w - 40, H - th + pad + line_h // 2), "$ " + run_text, font=font, fill=T["text"], anchor="lm")
        if run_out: d.text((gutter_w - 40, H - th + pad + line_h + line_h // 2), run_out, font=font, fill=T["num"], anchor="lm")
    return im

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("snippet"); ap.add_argument("--out", required=True); ap.add_argument("--lang"); ap.add_argument("--cps", type=float, default=28)
    ap.add_argument("--filename"); ap.add_argument("--theme", default="qdrant", choices=list(THEMES)); ap.add_argument("--fontsize", type=int, default=30)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080); ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--card", action="store_true"); ap.add_argument("--bg", default="#F5F4F0"); ap.add_argument("--card-width", type=float, default=0.78)
    ap.add_argument("--reveal", default="typed", choices=["typed", "all", "static"], help="typed: types in; all: shown finished, no cursor; static: shown finished with a blinking cursor at the end, as if waiting for you")
    ap.add_argument("--hold", type=float, default=1.5); ap.add_argument("--lead", type=float, default=0.6)
    ap.add_argument("--duration", type=float, help="for --reveal all/static: total clip length (default 6s)")
    ap.add_argument("--focus-lines", help="e.g. 12-18: push into these lines after typing"); ap.add_argument("--zoom", type=float, default=1.45)
    ap.add_argument("--zoom-speed", default="slow", choices=["slow", "normal", "fast", "snap"], help="push-in speed (1.4 / 0.7 / 0.3 / 0.12 s)")
    ap.add_argument("--zoom-out", action="store_true", help="after the push, swoop back out to the full view before the end")
    ap.add_argument("--cursor-line", type=int, help="static mode: line (1-based) where the cursor blinks; default last line")
    ap.add_argument("--run"); ap.add_argument("--run-output"); ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    global LANG
    code = open(a.snippet, encoding="utf-8").read().rstrip("\n")
    ext = os.path.splitext(a.snippet)[1].lower()
    LANG = a.lang or {".py": "python", ".js": "javascript", ".ts": "typescript", ".rs": "rust", ".go": "go", ".sh": "bash", ".json": "json"}.get(ext, "python")
    filename = a.filename or os.path.basename(a.snippet)
    lines = code.split("\n")
    random.seed(a.seed)
    # editor canvas size: full frame, or the card
    if a.card:
        EW = int(a.width * a.card_width); EH = int(EW * 9 / 16)
    else:
        EW, EH = a.width, a.height
    # shrink the font (down to 20 px) until the whole snippet fits the window, so static shots never scroll
    pad = 28; fs = a.fontsize
    while fs > 20 and len(lines) * int(fs * 1.55) > EH - 44 - 2 * pad: fs -= 1
    font = ImageFont.truetype(MONO, fs) if MONO else ImageFont.load_default()
    ui = ImageFont.truetype(UI, 18) if UI else ImageFont.load_default()
    line_h = int(fs * 1.55)
    visible = max(1, (EH - 44 - 2 * pad) // line_h)
    # typing schedule: time at which each character of each line has appeared
    events = []  # (t, line_index, chars_shown)
    t = a.lead
    if a.reveal in ("all", "static"):
        for li, ln in enumerate(lines): events.append((0.0, li, len(ln)))
        t = (a.duration or 6.0) - a.hold - (1.4 if a.run else 0)
    else:
        for li, ln in enumerate(lines):
            if ln.strip() == "":
                events.append((t, li, 0)); t += 0.12; continue
            indent = len(ln) - len(ln.lstrip())
            events.append((t, li, indent)); t += 0.04
            for ci in range(indent + 1, len(ln) + 1):
                ch = ln[ci - 1]
                dt = 1.0 / a.cps * random.uniform(0.6, 1.5)
                if ch in ",;:(" : dt *= 1.6
                if ch == " ": dt *= 0.8
                t += dt; events.append((t, li, ci))
            t += random.uniform(0.18, 0.42)        # breath at the end of a line
    t_typed = t
    run_at = t_typed + 0.5 if a.run else None
    t_end = (run_at + 0.9 if run_at else t_typed) + a.hold
    SPEED = {"slow": 1.4, "normal": 0.7, "fast": 0.3, "snap": 0.12}
    if a.focus_lines: t_end += SPEED[a.zoom_speed] + 1.2 + (0.6 if a.zoom_out else 0)
    n_frames = int(math.ceil(t_end * a.fps))
    tmp = tempfile.mkdtemp(prefix="code_")
    # background card pieces
    if a.card:
        from PIL import ImageDraw as _D
        r = 22
        mask = Image.new("L", (EW, EH), 0); _D.Draw(mask).rounded_rectangle([0, 0, EW - 1, EH - 1], radius=r, fill=255)
        pad_s = 90
        sh = Image.new("RGBA", (EW + 2 * pad_s, EH + 2 * pad_s), (0, 0, 0, 0)); _D.Draw(sh).rounded_rectangle([pad_s, pad_s, pad_s + EW - 1, pad_s + EH - 1], radius=r, fill=(0, 0, 0, 110)); sh = sh.filter(ImageFilter.GaussianBlur(40))
        bg_col = tuple(int(a.bg.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        px, py = (a.width - EW) // 2, (a.height - EH) // 2
    ev_i = 0; shown = [""] * len(lines); cursor = (0, 0); scroll = 0
    for f in range(n_frames):
        tf = f / a.fps
        while ev_i < len(events) and events[ev_i][0] <= tf:
            _, li, n = events[ev_i]; shown[li] = lines[li][:n]; cursor = (li, n); ev_i += 1
        lines_shown = shown[:max(cursor[0] + 1, 1)] if a.reveal == "typed" else lines
        if a.reveal == "static":
            cl = (a.cursor_line or len(lines)) - 1; cursor = (cl, len(lines[cl]))
        if len(lines) > visible and cursor[0] >= scroll + visible - 2: scroll = min(len(lines) - visible, cursor[0] - visible + 3)
        run_text = a.run if (run_at and tf >= run_at) else None
        run_out = a.run_output if (run_at and tf >= run_at + 0.9) else None
        cursor_on = (int(tf * 2.2) % 2 == 0) or (a.reveal == "typed" and tf < t_typed)
        im = render_frame(lines_shown, cursor if a.reveal in ("typed", "static") else None, a.theme, EW, EH, font, ui, filename, scroll, line_h, pad, run_text, run_out, cursor_on)
        if a.card:
            frame = Image.new("RGBA", (a.width, a.height), bg_col + (255,))
            frame.alpha_composite(sh, (px - pad_s, py - pad_s + 24))
            card = im.convert("RGBA"); card.putalpha(mask)
            frame.alpha_composite(card, (px, py)); im = frame.convert("RGB")
        im.save(os.path.join(tmp, f"f_{f:05d}.png"))
    # optional push into focus lines (ease over 1.0 s, hold)
    vf = ""
    if a.focus_lines:
        l0, l1 = [int(v) for v in a.focus_lines.split("-")]
        row = (l0 + l1) / 2 - 1 - scroll
        cy = (py if a.card else 0) + 44 + pad + row * line_h; cx = (px if a.card else 0) + EW * 0.45
        t0 = (run_at + 0.9 if run_at else t_typed) + 0.3; d_in = SPEED[a.zoom_speed]
        e_in = f"(st(1,min(1,max(0,(on/{a.fps}-{t0})/{d_in})))*0+ld(1)*ld(1)*(3-2*ld(1)))"
        Z = f"(1+({a.zoom}-1)*{e_in})"
        if a.zoom_out:   # one clean swoop back: sharp ease-out over 0.3 s
            t_out = t_end - a.hold - 0.3
            e_out = f"(st(2,min(1,max(0,(on/{a.fps}-{t_out})/0.3)))*0+1-(1-ld(2))*(1-ld(2))*(1-ld(2)))"
            Z = f"(1+({a.zoom}-1)*{e_in}*(1-{e_out}))"
        X = f"(2*({cx})-iw/{Z}/2)"; Y = f"(2*({cy})-ih/{Z}/2)"
        vf = f"scale={a.width * 2}:{a.height * 2}:flags=lanczos,zoompan=z='{Z}':x='min(max(0,{X}),iw-iw/zoom)':y='min(max(0,{Y}),ih-ih/zoom)':d=1:s={a.width}x{a.height}:fps={a.fps},"
    subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(a.fps), "-i", os.path.join(tmp, "f_%05d.png"), "-vf", vf + "format=yuv420p",
                    "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-movflags", "+faststart", a.out], check=True)
    import shutil; shutil.rmtree(tmp, ignore_errors=True)
    print(f"code clip -> {a.out}  {t_end:.1f}s  {len(lines)} lines typed at ~{a.cps:.0f} cps  theme {a.theme}{' in card' if a.card else ''}")

if __name__ == "__main__":
    main()
