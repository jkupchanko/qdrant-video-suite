#!/usr/bin/env python
"""shot.py: the B-roll suite with house defaults. One shot type, one command, matching output every time.

  python shot.py docs    URL --says "line"  --out DIR [--name n] [--zoom-speed slow|normal|fast|snap]
  python shot.py article URL --says "line"  --out DIR            (section gets a highlight box)
  python shot.py look    URL --says "line"  --out DIR [--mark box|underline|circle] [--target block|heading] [--hold 2.5]
                                            (scroll, stop, push in, draw the mark, hold, one swoop back out)
  python shot.py site    URL                --out DIR [--duration 10]   (slow top-to-bottom glide)
  python shot.py code    FILE               --out DIR [--static] [--lines 13-19] [--run "cmd" --run-output "..."]
  python shot.py title   "Headline text"    --out DIR [--sub "smaller line"] [--duration 3]
  python shot.py flow    (see SKILL.md: needs the real browser; this prints the steps)

Every shot: 1920x1080, 60 fps, off-white background rgb(245,244,240), the page or editor in a rounded card with a
soft shadow, pushes in slow and swoops out in one move, hard-cut safe (no slides, no fades to black).
"""
if __name__ == "__main__":                                   # run on the suite's own Python (.venv, made by setup.py), whichever python started it
    import os as _o, sys as _s, subprocess as _sp
    _v = _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), "..", "..", "..", ".venv", *(("Scripts", "python.exe") if _o.name == "nt" else ("bin", "python")))
    if _o.path.exists(_v) and _o.path.normcase(_o.path.realpath(_s.prefix)) != _o.path.normcase(_o.path.realpath(_o.path.dirname(_o.path.dirname(_v)))):
        _s.exit(_sp.call([_v, _o.path.realpath(__file__)] + _s.argv[1:]))
import argparse, json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
BG = "#F5F4F0"

def run(args):
    r = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    for l in (r.stdout + r.stderr).splitlines():
        if l.startswith(("plan", "recorded", "review", "manifest", "composed", "code clip", "WARNING")) or "FAIL" in l or "rror" in l: print("  " + l)
    if r.returncode != 0: raise SystemExit("step failed")

def section_focus(plan_path):
    """where the matched section sits in the composed card: push target in output px"""
    p = json.load(open(plan_path)); s = p.get("section")
    # the recorder parks the heading at 28% of the viewport; the card is 80% wide and centred
    cw = 1920 * 0.80; ch = cw * 9 / 16; px, py = (1920 - cw) / 2, (1080 - ch) / 2
    y_vp = 0.28 * 1080 + (140 if (s and s.get("has_code")) else 90)
    x_vp = ((s["left"] + min(s["width"], 900) / 2) if s else 960)
    return round(px + x_vp * cw / 1920), round(py + y_vp * ch / 1080)

def shot_docs(a, highlight=False):
    name = a.name or re.sub(r"[^a-z0-9]+", "_", (a.says or a.url)[:36].lower()).strip("_")
    style = "highlight" if highlight else "reveal"
    dur = a.duration or 7
    run([PY, f"{HERE}/broll.py", "auto", a.url, "--match", a.says or "", "--duration", dur, "--style", style, "--out", a.out, "--name", name] + (["--section", a.section] if getattr(a, "section", None) else []))
    cx, cy = section_focus(os.path.join(a.out, name + "_plan.json"))
    t_in = 2.2; t_out = dur - 1.3
    run([PY, f"{HERE}/compose.py", os.path.join(a.out, name + ".mp4"), "--style", "clean", "--card-bg", BG,
         "--focus", f"{t_in}:{cx},{cy},1.5:{a.zoom_speed}", "--focus", f"{t_out}:out", "--out", os.path.join(a.out, name + "_shot.mp4")])
    print(f"-> {os.path.join(a.out, name + '_shot.mp4')}")

def section_rect(plan_path):
    """the matched heading + first lines, as a box in output px (pre-zoom): x, y, w, h"""
    p = json.load(open(plan_path)); s = p.get("section")
    cw = 1920 * 0.80; ch = cw * 9 / 16; px, py = (1920 - cw) / 2, (1080 - ch) / 2
    k = cw / 1920
    x_vp = s["left"] if s else 300; w_vp = min(s["width"], 900) if s else 900
    y_vp = 0.28 * 1080 - 12; h_vp = 150 if not (s and s.get("has_code")) else 240
    return round(px + x_vp * k - 14), round(py + y_vp * k), round(w_vp * k + 28), round(h_vp * k)

def shot_look(a):
    """the stop-and-look shot: scroll to the section, settle, push in, frame the element, hold, swoop out the same way"""
    name = a.name or re.sub(r"[^a-z0-9]+", "_", (a.says or a.url)[:36].lower()).strip("_")
    hold = a.hold if a.hold is not None else 2.5
    spd = {"slow": 1.4, "normal": 0.7, "fast": 0.3, "snap": 0.12}[a.zoom_speed]
    t_zoom = 3.6            # the scroll lands at 2.9 s and the cursor settles on the heading by 3.5 s; a beat of stillness first
    t_mark = t_zoom + spd + 0.4
    t_out = t_mark + hold
    need = round(t_out + spd + 0.9, 1)
    dur = a.duration or need
    if dur < need: print(f"  note: --duration {dur} is too short for the sequence; using {need}s"); dur = need
    run([PY, f"{HERE}/broll.py", "auto", a.url, "--match", a.says or "", "--duration", dur, "--style", "look", "--out", a.out, "--name", name] + (["--section", a.section] if getattr(a, "section", None) else []))
    man = json.load(open(os.path.join(a.out, name + "_manifest.json")))
    box = (man.get("section_box") or {}).get(a.target)
    cw = 1920 * 0.80; ch = cw * 9 / 16; px, py = (1920 - cw) / 2, (1080 - ch) / 2; k = cw / 1920
    if box:
        # the element as it really sat on screen, mapped into the card, with a small even margin
        m = 14
        x, y, w, h = px + box["x"] * k - m, py + box["y"] * k - m, box["w"] * k + 2 * m, box["h"] * k + 2 * m
    else:
        print("  WARNING: the section box could not be measured; falling back to the plan estimate")
        x, y, w, h = section_rect(os.path.join(a.out, name + "_plan.json"))
    x, y, w, h = round(x), round(y), round(w), round(h)
    cx, cy = x + w / 2, y + h / 2
    # push just far enough that the framed element fills the view with air around it (never past --zoom)
    zoom = a.zoom or min(1.6, 1920 / (w + 240), 1080 / (h + 160))
    zoom = max(1.15, round(zoom, 2))
    if a.mark == "box": mark = f"box@{t_mark}={x},{y},{w},{h}"
    elif a.mark == "circle": mark = f"circle@{t_mark}={cx},{cy},{round(max(w, h) / 2 + 6)}"
    elif a.mark == "underline": mark = f"underline@{t_mark}={x + 14},{y + h},{w - 28}"
    else: mark = ""
    beats = f"zoom@{t_zoom}={cx},{cy},{zoom}:{a.zoom_speed} {mark}{':until=' + str(round(t_out - 0.1, 2)) if mark else ''} out@{t_out}:{a.zoom_speed}"
    run([PY, f"{HERE}/compose.py", os.path.join(a.out, name + ".mp4"), "--style", "clean", "--card-bg", BG, "--beats", beats,
         "--mark-color", a.mark_color, "--out", os.path.join(a.out, name + "_shot.mp4")])
    print(f"   beats: {beats}")
    print(f"-> {os.path.join(a.out, name + '_shot.mp4')}")

def shot_site(a):
    name = a.name or re.sub(r"[^a-z0-9]+", "_", re.sub(r"https?://", "", a.url)[:30].lower()).strip("_")
    dur = a.duration or 10
    run([PY, f"{HERE}/broll.py", "auto", a.url, "--match", "", "--style", "readthrough", "--duration", dur, "--out", a.out, "--name", name])
    run([PY, f"{HERE}/compose.py", os.path.join(a.out, name + ".mp4"), "--style", "clean", "--card-bg", BG, "--out", os.path.join(a.out, name + "_shot.mp4")])
    print(f"-> {os.path.join(a.out, name + '_shot.mp4')}")

def shot_code(a):
    name = a.name or os.path.splitext(os.path.basename(a.file))[0]
    cmd = [PY, f"{HERE}/code_broll.py", a.file, "--out", os.path.join(a.out, name + "_shot.mp4"), "--card", "--theme", "qdrant", "--bg", BG, "--zoom-speed", a.zoom_speed]
    if a.static: cmd += ["--reveal", "static", "--duration", a.duration or 6]
    if a.lines: cmd += ["--focus-lines", a.lines, "--zoom-out"]
    if a.run: cmd += ["--run", a.run] + (["--run-output", a.run_output] if a.run_output else [])
    run(cmd); print(f"-> {os.path.join(a.out, name + '_shot.mp4')}")

def shot_title(a):
    from PIL import Image, ImageDraw, ImageFont
    import imageio_ffmpeg
    name = a.name or re.sub(r"[^a-z0-9]+", "_", a.text[:30].lower()).strip("_")
    dur = a.duration or 3.0; fps = 60; W, H = 1920, 1080
    def font(names, size):
        for d in [os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts"), os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"), "/Library/Fonts", "/System/Library/Fonts", "/usr/share/fonts"]:
            for n in names:
                p = os.path.join(d, n)
                if os.path.exists(p): return ImageFont.truetype(p, size)
        return ImageFont.load_default()
    serif = font(["georgia.ttf", "Georgia.ttf", "times.ttf", "PlayfairDisplay-Regular.ttf", "DejaVuSerif.ttf"], 96)
    sans = font(["MonaSans-Medium.ttf", "segoeui.ttf", "DejaVuSans.ttf"], 36)
    bg = tuple(int(BG.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)); ink = (30, 30, 30)
    # wrap the headline to ~22 chars per line
    words = a.text.split(); lines = [""]
    for w in words:
        if len(lines[-1] + " " + w) > 24 and lines[-1]: lines.append(w)
        else: lines[-1] = (lines[-1] + " " + w).strip()
    tmp = tempfile.mkdtemp(prefix="title_")
    n = int(dur * fps)
    for f in range(n):
        t = f / fps
        k = min(1, max(0, t / 0.6)); e = k * k * (3 - 2 * k)
        im = Image.new("RGB", (W, H), bg); d = ImageDraw.Draw(im)
        total_h = len(lines) * 110 + (60 if a.sub else 0)
        y = H / 2 - total_h / 2 + 40
        for ln in lines:
            d.text((W / 2, y + 24 * (1 - e)), ln, font=serif, fill=ink + (int(255 * e),) if False else ink, anchor="mm"); y += 110
        if a.sub: d.text((W / 2, y + 10), a.sub, font=sans, fill=(110, 110, 110), anchor="mm")
        if e < 1:   # fade the text in over the background
            base = Image.new("RGB", (W, H), bg); im = Image.blend(base, im, e)
        im.save(os.path.join(tmp, f"f_{f:05d}.png"))
    out = os.path.join(a.out, name + "_shot.mp4")
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "f_%05d.png"), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=True)
    import shutil; shutil.rmtree(tmp, ignore_errors=True)
    print(f"-> {out}")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="kind", required=True)
    for k in ("docs", "article", "site", "look"):
        s = sub.add_parser(k); s.add_argument("url"); s.add_argument("--says", default=""); s.add_argument("--section", help="pin the page section by its heading; the spoken line alone can match the wrong section when several sections share words"); s.add_argument("--out", required=True); s.add_argument("--name"); s.add_argument("--duration", type=float); s.add_argument("--zoom-speed", default="slow", choices=["slow", "normal", "fast", "snap"])
        if k == "look":
            s.add_argument("--mark", default="box", choices=["box", "underline", "circle", "none"]); s.add_argument("--target", default="block", choices=["block", "heading"], help="frame the heading plus its text/code (block) or just the heading"); s.add_argument("--hold", type=float, help="seconds to sit on the marked spot before the swoop out (default 2.5)")
            s.add_argument("--zoom", type=float, help="push amount (default 1.6)"); s.add_argument("--mark-color", default="#DC244C")
    s = sub.add_parser("code"); s.add_argument("file"); s.add_argument("--out", required=True); s.add_argument("--name"); s.add_argument("--static", action="store_true"); s.add_argument("--lines"); s.add_argument("--run"); s.add_argument("--run-output"); s.add_argument("--duration", type=float); s.add_argument("--zoom-speed", default="slow")
    s = sub.add_parser("title"); s.add_argument("text"); s.add_argument("--out", required=True); s.add_argument("--name"); s.add_argument("--sub"); s.add_argument("--duration", type=float)
    s = sub.add_parser("flow")
    a = ap.parse_args()
    os.makedirs(getattr(a, "out", "."), exist_ok=True)
    if a.kind == "docs": shot_docs(a)
    elif a.kind == "article": shot_docs(a, highlight=True)
    elif a.kind == "look": shot_look(a)
    elif a.kind == "site": shot_site(a)
    elif a.kind == "code": shot_code(a)
    elif a.kind == "title": shot_title(a)
    else: print("flow: record the person's real browser. Steps are in SKILL.md under 'Pages behind a login'; the pieces are osmouse.py (real cursor) and cut_marks.py (tighten the capture).")

if __name__ == "__main__":
    main()
