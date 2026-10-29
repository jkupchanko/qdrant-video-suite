#!/usr/bin/env python
"""compose.py: bake a recorded B-roll clip into a finished, editor-agnostic video (no After Effects needed).

Styles
  fullscreen       the page fills the frame with a slow push; optional caption pill
  fullscreen-pip   as above, plus the presenter as a rounded, bordered picture-in-picture (face-cropped)
  evidence-card    the clip as a tilted card with a shadow that slides in; an OVERLAY unless --presenter is given
  window           the clip inside a browser-chrome window with a shadow; an OVERLAY unless --presenter is given

Outputs
  --presenter VIDEO --at SECONDS   use the presenter's own footage (video + audio) for that stretch: the result is a
                                   finished SECTION you drop straight into any timeline (mp4, H.264 + AAC)
  no --presenter                   fullscreen styles render over a dark background; card/window styles render a
                                   transparent OVERLAY (ProRes 4444 .mov with alpha) to place above your own footage

Examples
  python compose.py clip.mp4 --style fullscreen-pip --presenter talk.mp4 --at 72.0 --caption "create the index first" --out section.mp4
  python compose.py clip.mp4 --style evidence-card --out card_overlay.mov
  python compose.py clip.mp4 --style window --presenter talk.mp4 --at 10.5 --out section.mp4
"""
if __name__ == "__main__":                                   # run on the suite's own Python (.venv, made by setup.py), whichever python started it
    import os as _o, sys as _s, subprocess as _sp
    _v = _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), "..", "..", "..", ".venv", *(("Scripts", "python.exe") if _o.name == "nt" else ("bin", "python")))
    if _o.path.exists(_v) and _o.path.normcase(_o.path.realpath(_s.prefix)) != _o.path.normcase(_o.path.realpath(_o.path.dirname(_o.path.dirname(_v)))):
        _s.exit(_sp.call([_v, _o.path.realpath(__file__)] + _s.argv[1:]))
import argparse, json, math, os, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont

def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def probe(path):
    info = subprocess.run([ffmpeg(), "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info); dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 6.0
    r = re.search(r", (\d{3,5})x(\d{3,5})", info)
    return dur, (int(r[1]), int(r[2])) if r else (1920, 1080)

def find_font(names):
    dirs = [os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts"), os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
            "/Library/Fonts", "/System/Library/Fonts", os.path.expanduser("~/Library/Fonts"), "/usr/share/fonts", "/usr/share/fonts/truetype/dejavu"]
    for n in names:
        for d in dirs:
            p = os.path.join(d, n)
            if os.path.exists(p): return p
    return None

FONT = find_font(["MonaSans-Medium.ttf", "MonaSans-Regular.ttf", "Inter-Medium.ttf", "segoeui.ttf", "Arial.ttf", "arial.ttf", "Helvetica.ttc", "DejaVuSans.ttf"])

def caption_png(text, path, size=38, maxw=1600):
    font = ImageFont.truetype(FONT, size) if FONT else ImageFont.load_default()
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    while tmp.textlength(text, font=font) > maxw - 56 and size > 18:
        size -= 2; font = ImageFont.truetype(FONT, size) if FONT else font
    tw = int(tmp.textlength(text, font=font)); w, h = tw + 56, int(size * 1.7)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=14, fill=(8, 9, 15, 210))
    d.text((28, h / 2), text, font=font, fill=(255, 255, 255, 255), anchor="lm")
    im.save(path); return w, h

def rounded_mask(w, h, r, path):
    im = Image.new("L", (w, h), 0); ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255); im.save(path)

def border_png(w, h, r, color, width, path):
    im = Image.new("RGBA", (w + 2 * width, h + 2 * width), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w + 2 * width - 1, h + 2 * width - 1], radius=r + width, outline=tuple(color) + (255,), width=width); im.save(path)

def shadow_png(w, h, r, path, blur=28, alpha=150, pad=60):
    im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([pad, pad, pad + w - 1, pad + h - 1], radius=r, fill=(0, 0, 0, alpha))
    im.filter(ImageFilter.GaussianBlur(blur)).save(path)

def chrome_png(w, h, url, path):
    """browser title bar + edge, content area transparent; w x h is the full window (bar 44 px)"""
    S = 2; W, H, bar, rad = w * S, h * S, 44 * S, 14 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W - 1, bar + rad], radius=rad, fill=(20, 26, 42, 255)); d.rectangle([0, bar, W - 1, bar + rad], fill=(0, 0, 0, 0))
    d.rectangle([0, bar - 1, W - 1, bar - 1], fill=(78, 83, 102, 255))
    for i, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx, cy = (16 + i * 20) * S + 6 * S, bar // 2; d.ellipse([cx - 6 * S, cy - 6 * S, cx + 6 * S, cy + 6 * S], fill=col + (255,))
    pw, ph = min(360 * S, W - 200 * S), 26 * S; px, py = (W - pw) // 2, (bar - ph) // 2
    d.rounded_rectangle([px, py, px + pw, py + ph], radius=ph // 2, fill=(11, 15, 25, 255), outline=(78, 83, 102, 255), width=S)
    f = ImageFont.truetype(FONT, 13 * S) if FONT else ImageFont.load_default()
    d.text((W / 2, py + ph / 2), url[:60], font=f, fill=(240, 243, 250, 255), anchor="mm")
    edge = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(edge).rounded_rectangle([0, 0, W - 1, H - 1], radius=rad, outline=(255, 255, 255, 46), width=S)
    Image.alpha_composite(im, edge).resize((w, h), Image.LANCZOS).save(path)

def face_crop(video, at, fw, fh):
    """centre a 16:9 crop (fw x fh in source px) on the face if OpenCV finds one, else on the frame centre"""
    tmp = tempfile.mktemp(suffix=".png")
    subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-ss", str(at + 0.5), "-i", video, "-frames:v", "1", tmp], check=True)
    im = Image.open(tmp); W, H = im.size
    cx, cy = W / 2, H / 2
    try:
        import cv2, numpy as np
        g = cv2.equalizeHist(cv2.cvtColor(np.asarray(im.convert("RGB")), cv2.COLOR_RGB2GRAY))
        faces = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml").detectMultiScale(g, 1.1, 5, minSize=(int(H * 0.15), int(H * 0.15)))
        if len(faces):
            x, y, w, h = max(faces, key=lambda b: b[2] * b[3]); cx, cy = x + w / 2, y + h * 0.52
            fw = min(W, max(fw, int(w * 2.0))); fh = int(fw * 9 / 16)
    except Exception:
        pass
    os.remove(tmp)
    x0 = int(min(max(0, cx - fw / 2), W - fw)); y0 = int(min(max(0, cy - fh / 2), H - fh))
    return x0, y0, int(fw), int(fh), W, H

def smooth(t0, d):   # eased 0..1 as an ffmpeg expression in t
    return f"(st(0,min(1,max(0,(t-{t0})/{d})))*0+ld(0)*ld(0)*(3-2*ld(0)))"

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clip"); ap.add_argument("--style", default="fullscreen-pip", choices=["fullscreen", "fullscreen-pip", "evidence-card", "window", "clean"])
    ap.add_argument("--focus", action="append", default=[], help="clean style: 'T:cx,cy,zoom' or 'T:cx,cy,zoom:speed' moves the view to that point/zoom starting at T seconds. speed = slow (1.4s), normal (0.7s), fast (0.3s) or snap (0.12s); default slow for pushes in, fast for pulls out. 'T:out' returns to the full view. Between moves the view holds still.")
    ap.add_argument("--card-width", type=float, default=0.80, help="clean style: window width as a fraction of the frame")
    ap.add_argument("--mark", action="append", default=[], help="clean style annotation: 'T:circle:cx,cy,r' | 'T:box:x,y,w,h' | 'T:underline:x,y,w' drawn on at T (output px, pre-zoom, so it rides with the zoom); add ':until=T2' to remove it; colour via --mark-color")
    ap.add_argument("--mark-color", default="#DC244C")
    ap.add_argument("--beats", help="clean style shot plan in one string, e.g. 'zoom@2.0=900,470,1.5 circle@3.2=900,470,120 out@6.0' (speeds: zoom@2.0=...:snap); see styles.md")
    ap.add_argument("--card-bg", default="#F5F4F0", help="clean style: background colour (default rgb 245,244,240, the Anthropic/Claude off-white)")
    ap.add_argument("--out", required=True); ap.add_argument("--presenter"); ap.add_argument("--at", type=float, default=0.0, help="where in the presenter video this clip sits (s)")
    ap.add_argument("--duration", type=float); ap.add_argument("--caption", default=""); ap.add_argument("--push", type=float, default=1.05)
    ap.add_argument("--pip-width", type=int, default=435); ap.add_argument("--pip-corner", default="bottom-right"); ap.add_argument("--pip-border", default="255,255,255")
    ap.add_argument("--pip-crop", help="cx,cy,w,h in presenter pixels (default: auto on the face)")
    ap.add_argument("--card-scale", type=float, default=0.45); ap.add_argument("--card-pos", default="450,320"); ap.add_argument("--card-rot", type=float, default=-6)
    ap.add_argument("--window-scale", type=float, default=0.72); ap.add_argument("--window-pos", default="1180,560"); ap.add_argument("--url", default="")
    ap.add_argument("--bg", default="#0B0F19", help="background colour when there is no presenter and the style is full-screen")
    ap.add_argument("--fps", type=int, default=60); ap.add_argument("--manifest", help="manifest json from broll.py; fills --caption and --url when omitted")
    a = ap.parse_args()
    if a.manifest and os.path.exists(a.manifest):
        m = json.load(open(a.manifest)); a.caption = a.caption or m.get("caption_suggestion", ""); a.url = a.url or m.get("url", "")
    D, (cw, ch) = probe(a.clip); D = a.duration or D
    W, H = 1920, 1080
    tmp = tempfile.mkdtemp(prefix="compose_")
    inputs = ["-i", a.clip]; filt = []; n_in = 1
    overlay_mode = a.style in ("evidence-card", "window") and not a.presenter
    # --- "clean" style: cream background, rounded window with a soft shadow, eased pushes into points of interest.
    if a.style == "clean":
        # beats: a compact way to direct a shot. zoom@T=cx,cy,z[:speed]  out@T[:speed]  circle@T=cx,cy,r  box@T=x,y,w,h  underline@T=x,y,w
        if a.beats:
            for b in a.beats.split():
                kind, rest = b.split("@", 1)
                tpart, _, val = rest.partition("=")
                t, _, spd = tpart.partition(":")
                if kind == "zoom": a.focus.append(f"{t}:{val}" + (f":{spd}" if spd else ""))
                elif kind == "out": a.focus.append(f"{t}:out" + (f":{spd}" if spd else ""))
                else: a.mark.append(f"{t}:{kind}:{val}")
        kw = int(W * a.card_width); kh = int(kw * ch / cw); r = 22
        rounded_mask(kw, kh, r, f"{tmp}/mask.png"); shadow_png(kw, kh, r, f"{tmp}/shadow.png", blur=40, alpha=110, pad=90)
        px, py = (W - kw) // 2, (H - kh) // 2
        inputs += ["-loop", "1", "-t", str(D), "-i", f"{tmp}/mask.png", "-loop", "1", "-t", str(D), "-i", f"{tmp}/shadow.png"]; mk, sh = n_in, n_in + 1; n_in += 2
        filt.append(f"color=c={a.card_bg.replace('#', '0x')}:s={W}x{H}:r={a.fps}:d={D}[bg]")
        filt.append(f"[0:v]scale={kw}:{kh},format=rgba[k0];[{mk}:v]format=gray[km];[k0][km]alphamerge[card]")
        rise = f"{py}+14*(1-{smooth(0.0, 0.45)})"
        filt.append(f"[bg][{sh}:v]overlay={px - 90}:{py - 90 + 24}:format=auto[b1];[b1][card]overlay=x={px}:y='{rise}':format=auto[flat0]")
        # annotations: drawn-on marks that ride with the zoom (overlaid before zoompan)
        last_flat = "flat0"
        col = tuple(int(a.mark_color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        for mi, m in enumerate(a.mark):
            parts = m.split(":"); t0 = float(parts[0]); kind = parts[1]; vals = [float(v) for v in parts[2].split(",")]
            until = None
            for p in parts[3:]:
                if p.startswith("until="): until = float(p[6:])
            pad = 24
            if kind == "circle":
                cx, cy, r = vals; mw, mh = int(2 * r + 2 * pad), int(2 * r + 2 * pad); mx, my = int(cx - r - pad), int(cy - r - pad)
                im = Image.new("RGBA", (mw, mh), (0, 0, 0, 0)); ImageDraw.Draw(im).ellipse([pad, pad, pad + 2 * r, pad + 2 * r], outline=col + (255,), width=6)
            elif kind == "box":
                x, y, w, h = vals; mw, mh = int(w + 2 * pad), int(h + 2 * pad); mx, my = int(x - pad), int(y - pad)
                im = Image.new("RGBA", (mw, mh), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle([pad, pad, pad + w, pad + h], radius=12, outline=col + (255,), width=6)
            else:  # underline
                x, y, w = vals[:3]; mw, mh = int(w + 2 * pad), 2 * pad + 8; mx, my = int(x - pad), int(y - pad)
                im = Image.new("RGBA", (mw, mh), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle([pad, pad, pad + w, pad + 6], radius=3, fill=col + (255,))
            mp = f"{tmp}/mark{mi}.png"; im.save(mp)
            inputs += ["-loop", "1", "-t", str(D), "-i", mp]; mi_in = n_in; n_in += 1
            # pop in (scale 0.85 -> 1 with a tiny overshoot, alpha fade) over 0.35 s; optional fade out
            fade = f"fade=t=in:st={t0}:d=0.25:alpha=1" + (f",fade=t=out:st={until}:d=0.2:alpha=1" if until else "")
            filt.append(f"[{mi_in}:v]format=rgba,{fade}[mk{mi}]")
            sc_e = f"(0.85+0.15*{smooth(t0, 0.35)}+0.06*sin(min(1,max(0,(t-{t0})/0.35))*3.1416))"
            filt.append(f"[mk{mi}]scale=w='iw*{sc_e}':h='ih*{sc_e}':eval=frame[mks{mi}]")
            filt.append(f"[{last_flat}][mks{mi}]overlay=x='{mx + mw / 2}-w/2':y='{my + mh / 2}-h/2':format=auto[flat{mi + 1}]"); last_flat = f"flat{mi + 1}"
        filt.append(f"[{last_flat}]null[flat]")
        # pushes: zoom/centre as piecewise eased sums, rendered from a 2x frame so the zoom stays sharp
        SPEED = {"slow": 1.4, "normal": 0.7, "fast": 0.3, "snap": 0.12}
        segs = []
        for f in a.focus:
            parts = f.split(":")
            # legacy form 't0-t1:cx,cy,z' still accepted
            if "-" in parts[0] and len(parts) >= 2 and "," in parts[1]:
                t0, t1 = [float(v) for v in parts[0].split("-")]; cx, cy, z = [float(v) for v in parts[1].split(",")]
                segs.append((t0, t1 - t0, cx, cy, z)); continue
            t0 = float(parts[0])
            if parts[1].strip().lower() == "out":
                cx, cy, z = 960.0, 540.0, 1.0; spd = parts[2] if len(parts) > 2 else "fast"
            else:
                cx, cy, z = [float(v) for v in parts[1].split(",")]; spd = parts[2] if len(parts) > 2 else None
            segs.append((t0, spd, cx, cy, z))
        segs.sort(key=lambda s: s[0])
        zx, zy, zz = "960", "540", "1"
        pz, pcx, pcy = 1.0, 960.0, 540.0
        for t0, spd, cx, cy, z in segs:
            if isinstance(spd, (int, float)): dur = max(0.05, spd)
            else: dur = SPEED.get(spd or ("slow" if z > pz else "fast"), 0.7)
            # smoothstep for pushes in; pulls out get a sharper ease-out so the swoop lands cleanly
            if z < pz: e = f"(st(1,min(1,max(0,(on/{a.fps}-{t0})/{dur})))*0+1-(1-ld(1))*(1-ld(1))*(1-ld(1)))"
            else: e = f"(st(1,min(1,max(0,(on/{a.fps}-{t0})/{dur})))*0+ld(1)*ld(1)*(3-2*ld(1)))"
            zz += f"+({z - pz})*{e}"; zx += f"+({cx - pcx})*{e}"; zy += f"+({cy - pcy})*{e}"
            pz, pcx, pcy = z, cx, cy
        Z = f"({zz})"; X = f"(2*({zx})-iw/{Z}/2)"; Y = f"(2*({zy})-ih/{Z}/2)"
        filt.append(f"[flat]scale={W * 2}:{H * 2}:flags=lanczos,zoompan=z='{Z}':x='min(max(0,{X}),iw-iw/zoom)':y='min(max(0,{Y}),ih-ih/zoom)':d=1:s={W}x{H}:fps={a.fps}[v1]")
        last = "v1"
        if a.caption:
            cwid, chei = caption_png(a.caption, f"{tmp}/caption.png")
            inputs += ["-loop", "1", "-t", str(D), "-i", f"{tmp}/caption.png"]; cp = n_in; n_in += 1
            filt.append(f"[{cp}:v]format=rgba,fade=t=in:st=0.1:d=0.2:alpha=1,fade=t=out:st={max(0, D - 0.3):.2f}:d=0.25:alpha=1[cap];[{last}][cap]overlay={(W - cwid) // 2}:{H - 60 - chei}:format=auto[c1]"); last = "c1"
        filt.append(f"[{last}]format=yuv420p[vout]")
        out = a.out
        cmd = [ffmpeg(), "-hide_banner", "-loglevel", "error", "-y"] + inputs + ["-filter_complex", ";".join(filt), "-map", "[vout]", "-an", "-t", str(D), "-r", str(a.fps), "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
        subprocess.run(cmd, check=True)
        print(f"composed -> {out}  [clean] {D:.2f}s {W}x{H}  cream card, {len(segs)} push(es)")
        import shutil; shutil.rmtree(tmp, ignore_errors=True); return
    # --- base layer
    if a.presenter:
        inputs += ["-ss", str(a.at), "-t", str(D), "-i", a.presenter]; pres = n_in; n_in += 1
        filt.append(f"[{pres}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1[base]")
    elif overlay_mode:
        filt.append(f"color=c=black@0.0:s={W}x{H}:r={a.fps}:d={D},format=rgba[base]")
    else:
        filt.append(f"color=c={a.bg.replace('#', '0x')}:s={W}x{H}:r={a.fps}:d={D}[base]")
    last = "base"
    # --- the clip in its style
    if a.style.startswith("fullscreen"):
        frames = int(D * a.fps)
        filt.append(f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,zoompan=z='1+({a.push}-1)*on/{frames}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={a.fps},format=rgba,fade=t=in:st=0:d=0.2:alpha=1[page]")
        filt.append(f"[{last}][page]overlay=0:0:format=auto[v1]"); last = "v1"
    elif a.style == "evidence-card":
        kw = int(cw * a.card_scale); kh = int(ch * a.card_scale); r = 24
        rounded_mask(kw, kh, r, f"{tmp}/mask.png"); shadow_png(kw, kh, r, f"{tmp}/shadow.png")
        inputs += ["-loop", "1", "-t", str(D), "-i", f"{tmp}/mask.png", "-loop", "1", "-t", str(D), "-i", f"{tmp}/shadow.png"]; mk, sh = n_in, n_in + 1; n_in += 2
        px, py = [int(v) for v in a.card_pos.split(",")]
        rot = a.card_rot * math.pi / 180
        filt.append(f"[0:v]scale={kw}:{kh},format=rgba[k0];[{mk}:v]format=gray[km];[k0][km]alphamerge,rotate={rot}:ow='hypot(iw,ih)':oh='hypot(iw,ih)':c=black@0[card]")
        filt.append(f"[{sh}:v]format=rgba,rotate={rot}:ow='hypot(iw,ih)':oh='hypot(iw,ih)':c=black@0[shadow]")
        ex = f"{px}-w/2+(-{px}-w)*(1-{smooth(0.0, 0.5)})"; ey = f"{py}-h/2+(-{py}-h)*(1-{smooth(0.0, 0.5)})"
        filt.append(f"[{last}][shadow]overlay=x='({ex})+14':y='({ey})+18':format=auto[v1];[v1][card]overlay=x='{ex}':y='{ey}+6*sin(t*1.1)':format=auto[v2]"); last = "v2"
    elif a.style == "window":
        ww = int(cw * a.window_scale); wh = int(ch * a.window_scale) + 44; r = 14
        chrome_png(ww, wh, a.url or "localhost", f"{tmp}/chrome.png"); rounded_mask(ww, wh, r, f"{tmp}/mask.png"); shadow_png(ww, wh, r, f"{tmp}/shadow.png", blur=34, alpha=170, pad=80)
        inputs += ["-loop", "1", "-t", str(D), "-i", f"{tmp}/chrome.png", "-loop", "1", "-t", str(D), "-i", f"{tmp}/mask.png", "-loop", "1", "-t", str(D), "-i", f"{tmp}/shadow.png"]; cr, mk, sh = n_in, n_in + 1, n_in + 2; n_in += 3
        px, py = [int(v) for v in a.window_pos.split(",")]
        filt.append(f"[0:v]scale={ww}:{wh - 44},format=rgba,pad={ww}:{wh}:0:44:black@0[pg];[pg][{cr}:v]overlay=0:0:format=auto[win0];[{mk}:v]format=gray[wm];[win0][wm]alphamerge[win]")
        ex = f"{px}-w/2+300*(1-{smooth(0.0, 0.6)})"; ey = f"{py}-h/2"
        filt.append(f"[{last}][{sh}:v]overlay=x='({ex})-80+16':y='({ey})-80+22':format=auto[v1];[v1][win]overlay=x='{ex}':y='{ey}+8*sin(t*0.9)':format=auto,fade=t=in:st=0:d=0.25:alpha=1[v2]"); last = "v2"
    # --- PiP of the presenter
    if a.style == "fullscreen-pip" and a.presenter:
        pw = a.pip_width; ph = int(pw * 9 / 16); r = 36
        if a.pip_crop:
            cx, cy, fw, fh = [int(v) for v in a.pip_crop.split(",")]; x0, y0 = cx - fw // 2, cy - fh // 2
        else:
            x0, y0, fw, fh, _, _ = face_crop(a.presenter, a.at, 640, 360)
        rounded_mask(pw, ph, r, f"{tmp}/pmask.png"); border_png(pw, ph, r, [int(v) for v in a.pip_border.split(",")], 4, f"{tmp}/pborder.png"); shadow_png(pw, ph, r, f"{tmp}/pshadow.png", blur=22, alpha=170, pad=50)
        inputs += ["-loop", "1", "-t", str(D), "-i", f"{tmp}/pmask.png", "-loop", "1", "-t", str(D), "-i", f"{tmp}/pborder.png", "-loop", "1", "-t", str(D), "-i", f"{tmp}/pshadow.png"]; pm, pb, ps = n_in, n_in + 1, n_in + 2; n_in += 3
        m = 40
        pos = {"bottom-right": (W - m - pw, H - m - ph), "top-right": (W - m - pw, m), "bottom-left": (m, H - m - ph), "top-left": (m, m)}[a.pip_corner]
        filt.append(f"[{pres}:v]crop={fw}:{fh}:{x0}:{y0},scale={pw}:{ph},format=rgba[p0];[{pm}:v]format=gray[pmk];[p0][pmk]alphamerge,fade=t=in:st=0.15:d=0.25:alpha=1[pip]")
        filt.append(f"[{ps}:v]fade=t=in:st=0.15:d=0.25:alpha=1[psh];[{pb}:v]fade=t=in:st=0.15:d=0.25:alpha=1[pbd]")
        filt.append(f"[{last}][psh]overlay={pos[0] - 50 + 10}:{pos[1] - 50 + 14}:format=auto[q1];[q1][pip]overlay={pos[0]}:{pos[1]}:format=auto[q2];[q2][pbd]overlay={pos[0] - 4}:{pos[1] - 4}:format=auto[q3]"); last = "q3"
    # --- caption pill
    if a.caption:
        cwid, chei = caption_png(a.caption, f"{tmp}/caption.png")
        inputs += ["-loop", "1", "-t", str(D), "-i", f"{tmp}/caption.png"]; cp = n_in; n_in += 1
        filt.append(f"[{cp}:v]format=rgba,fade=t=in:st=0.1:d=0.2:alpha=1,fade=t=out:st={max(0, D - 0.3):.2f}:d=0.25:alpha=1[cap];[{last}][cap]overlay={(W - cwid) // 2}:{H - 60 - chei}:format=auto[c1]"); last = "c1"
    # --- output
    out = a.out
    if overlay_mode:
        if not out.lower().endswith(".mov"): out = os.path.splitext(out)[0] + ".mov"
        filt.append(f"[{last}]format=yuva444p10le[vout]")
        cmd = [ffmpeg(), "-hide_banner", "-loglevel", "error", "-y"] + inputs + ["-filter_complex", ";".join(filt), "-map", "[vout]", "-t", str(D), "-r", str(a.fps), "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-an", out]
    else:
        filt.append(f"[{last}]format=yuv420p[vout]")
        cmd = [ffmpeg(), "-hide_banner", "-loglevel", "error", "-y"] + inputs + ["-filter_complex", ";".join(filt), "-map", "[vout]"] + (["-map", f"{pres}:a?", "-c:a", "aac", "-b:a", "192k"] if a.presenter else ["-an"]) + ["-t", str(D), "-r", str(a.fps), "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    kind = "transparent overlay (lay it above your footage)" if overlay_mode else ("finished section with the presenter's audio" if a.presenter else "finished clip")
    print(f"composed -> {out}  [{a.style}] {D:.2f}s {W}x{H}  {kind}")
    import shutil; shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    main()
