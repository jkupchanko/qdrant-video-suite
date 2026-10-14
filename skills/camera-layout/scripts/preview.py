"""Build a short preview video: one card per camera-plan row, showing the layout with a presenter still
over a mock of what is on screen, and a label bar with the time, section, layout and the spoken line."""
import json, os, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
BG = (245, 244, 240); DARK = (11, 15, 25); INK = (30, 30, 30); MUTED = (110, 110, 110); RED = (220, 36, 76)
rows = json.load(open(os.path.join(HERE, "plan.json")))
full = Image.open(os.path.join(HERE, "presenter_full.png")).convert("RGB")
p43 = Image.open(os.path.join(HERE, "presenter_43.png")).convert("RGB")
art = {"home": Image.open(os.path.join(HERE, "article_home_casa.png")).convert("RGB"), "bat": Image.open(os.path.join(HERE, "article_bat.png")).convert("RGB")}

def font(names, size):
    for d in [os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts")]:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()
SANS = font(["segoeui.ttf"], 30); SANS_B = font(["segoeuib.ttf", "segoeui.ttf"], 34); MONO = font(["consola.ttf", "cour.ttf"], 30); SERIF = font(["georgia.ttf"], 64); SMALL = font(["segoeui.ttf"], 24)

def card(w, h, kind, section, text):
    """mock of what is on screen for this passage"""
    im = Image.new("RGB", (w, h), DARK); d = ImageDraw.Draw(im)
    s = section.lower()
    if "article" in kind:
        src = art["bat"] if "limit" in s else art["home"]
        return src.resize((w, h), Image.LANCZOS)
    if "hook" in s:
        d.text((w / 2, h / 2 - 40), "Spanish question.", font=SERIF, fill=(245, 244, 240), anchor="mm")
        d.text((w / 2, h / 2 + 50), "English answer.", font=SERIF, fill=RED, anchor="mm")
    elif "set up" in s:
        lines = ["query:  perro corriendo en el parque", "", "1  A dog ran through the park after a red ball.   <- intended", "2  This soup uses onion, garlic and fresh tomato.", "3  Astronomers found a new star in a distant galaxy."]
        for i, l in enumerate(lines): d.text((60, 70 + i * 60), l, font=MONO, fill=(230, 230, 230) if i else (150, 200, 255))
    elif "connection" in s:
        d.text((w / 2, h * 0.35), "perro        dog", font=SERIF, fill=(245, 244, 240), anchor="mm")
        d.text((w / 2, h * 0.55), "shared concept", font=SANS, fill=RED, anchor="mm")
        d.text((w / 2, h * 0.72), "casa  <->  home", font=SANS, fill=(180, 180, 180), anchor="mm")
    elif "code" in s:
        code = ['passage = "A dog ran through the park after a red ball."', 'question = "perro corriendo en el parque"', "", 'document_values = encoder.encode_sparse(passage, lang="en")', 'query_values = encoder.encode_sparse(', '    question, lang="es", is_query=True', ")", "", 'sparse_vectors_config={"minicoil": models.SparseVectorParams(', "    modifier=models.Modifier.IDF)}"]
        for i, l in enumerate(code): d.text((60, 60 + i * 52), l, font=MONO, fill=(230, 230, 230))
        d.rectangle([48, 60 + 4 * 52 - 8, w - 48, 60 + 7 * 52], outline=RED, width=3)
    elif "run" in s:
        rowsr = [("rank", "passage", "score"), ("1", "A dog ran through the park after a red ball.", "0.83"), ("2", "Astronomers found a new star in a distant galaxy.", "0.12"), ("3", "This soup uses onion, garlic and fresh tomato.", "0.09")]
        for i, (a, b, c) in enumerate(rowsr):
            col = (150, 200, 255) if i == 0 else (230, 230, 230)
            d.text((60, 70 + i * 70), a, font=MONO, fill=col); d.text((180, 70 + i * 70), b, font=MONO, fill=col); d.text((w - 160, 70 + i * 70), c, font=MONO, fill=col)
        d.rectangle([48, 70 + 70 - 10, w - 48, 70 + 70 + 44], outline=RED, width=3)
    elif "limit" in s:
        d.text((w / 2, h * 0.4), "bat", font=SERIF, fill=(245, 244, 240), anchor="mm")
        d.text((w / 2, h * 0.62), "animal        or        sports equipment", font=SANS, fill=(180, 180, 180), anchor="mm")
    else:
        for i, l in enumerate(["1  Write three questions in Spanish.", "2  Run each against your passages.", "3  Record the rank of the intended answer."]): d.text((60, 90 + i * 70), l, font=SANS, fill=(230, 230, 230))
    return im

def rounded(im, r=22):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, im.size[0] - 1, im.size[1] - 1], radius=r, fill=255); return m

def frame(row, kind):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    lay = row["layout"]; sec = row["section"]
    content_h = 880
    if lay == "full":
        im.paste(full.resize((W, H)), (0, 0)); d = ImageDraw.Draw(im)
    elif lay == "half":
        cw = int(W * 0.58); ch = int(cw * 9 / 16); c = card(cw, ch, kind, sec, row["text"]); im.paste(c, (60, (content_h - ch) // 2 + 40), rounded(c))
        pw = W - cw - 180; ph = int(pw * 4 / 3); p = p43.resize((pw, ph)); im.paste(p, (cw + 120, (content_h - ph) // 2 + 40), rounded(p))
    else:
        cw = int(W * 0.80); ch = int(cw * 9 / 16); c = card(cw, ch, kind, sec, row["text"]); x0, y0 = (W - cw) // 2, (content_h - ch) // 2 + 40
        im.paste(c, (x0, y0), rounded(c))
        if lay in ("small", "inset"):
            pw = int(W * (0.18 if lay == "small" else 0.28)); ph = int(pw * 3 / 4); p = p43.resize((pw, ph))
            corner = row.get("pos", "")
            px = x0 + cw - pw - 24 if "right" in corner else x0 + 24; py = y0 + ch - ph - 24 if "bottom" in corner else y0 + 24
            im.paste(p, (px, py), rounded(p, 16)); d = ImageDraw.Draw(im); d.rounded_rectangle([px - 3, py - 3, px + pw + 3, py + ph + 3], radius=18, outline=(245, 244, 240), width=4)
    # label bar
    d = ImageDraw.Draw(im); d.rectangle([0, H - 150, W, H], fill=(28, 28, 28))
    t = row["t"]; label = f"{int(t // 60)}:{int(t % 60):02d}  ·  {sec}  ·  {row['layout'].upper()}"
    if lay in ("small", "inset", "half"): label += "  " + ("(18% window)" if lay == "small" else "(28% window)" if lay == "inset" else "(40% panel)")
    d.text((60, H - 128), label, font=SANS_B, fill=(245, 244, 240))
    says = textwrap.shorten(row["text"], 150); d.text((60, H - 80), "\u201c" + says + "\u201d", font=SANS, fill=(200, 200, 200))
    d.text((60, H - 42), row["why"], font=SMALL, fill=(150, 150, 150))
    return im

# merge same-layout neighbours within a section, as the plan table does
merged = []
for r in rows:
    if merged and merged[-1]["layout"] == r["layout"] and merged[-1]["section"] == r["section"]: merged[-1]["hold"] += r["hold"]; continue
    merged.append(dict(r))
os.makedirs(os.path.join(HERE, "frames"), exist_ok=True)
lst = []
for i, r in enumerate(merged):
    kind = "article" if "B-roll" in r["why"] else "card"
    f = frame(r, kind); p = os.path.join(HERE, "frames", f"f{i:02d}.png"); f.save(p)
    lst.append(f"file 'frames/f{i:02d}.png'\nduration {max(3.0, min(6.0, r['hold'] / 3)):.1f}")
lst.append(f"file 'frames/f{len(merged) - 1:02d}.png'")
open(os.path.join(HERE, "frames.txt"), "w").write("\n".join(lst))
out = os.path.join(HERE, "miniCOIL_camera_preview.mp4")
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(HERE, "frames.txt"), "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "18", "-movflags", "+faststart", out], check=True, cwd=HERE)
print("->", out, len(merged), "cards")
