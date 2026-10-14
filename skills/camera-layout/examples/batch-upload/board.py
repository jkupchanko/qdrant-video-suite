"""Layout board for the batch-upload script: one tile per camera line, in script order. Each tile shows the
time, the call, the frame it makes (John's footage by the framing rule over a mock of what the Show line
names), and the reason. Output: batch_upload_board.png (and tiles/)."""
import os, textwrap
from PIL import Image, ImageDraw, ImageFont
HERE = r"C:\Users\ADMIN\camera_audit\john_video"
W, H = 1920, 1080; BG = (245, 244, 240); DARK = (11, 15, 25); INK = (30, 30, 30); RED = (220, 36, 76); MUTED = (120, 120, 120)
def font(n, s):
    for d in [os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts")]:
        p = os.path.join(d, n)
        if os.path.exists(p): return ImageFont.truetype(p, s)
    return ImageFont.load_default()
MONO = font("consola.ttf", 34); SANS = font("segoeui.ttf", 34); SANS_B = font("segoeuib.ttf", 36); SERIF = font("georgia.ttf", 84); T = font("segoeui.ttf", 24); TB = font("segoeuib.ttf", 26); CALL = font("consola.ttf", 22)
full = Image.open(os.path.join(HERE, "take_full2_fullcrop.png")).convert("RGB"); p43 = Image.open(os.path.join(HERE, "take_full2_43.png")).convert("RGB")
docs = Image.open(os.path.join(HERE, "docs_points_page.png")).convert("RGB")

def rounded(im, r=22):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, im.size[0] - 1, im.size[1] - 1], radius=r, fill=255); return m

def card(kind, w, h):
    im = Image.new("RGB", (w, h), DARK); d = ImageDraw.Draw(im)
    if kind == "checklist":
        for i, l in enumerate(["1  a collection, vector size = your embeddings", "2  points: id, vector, payload", "3  the Python client, connected"]): d.text((70, 90 + i * 80), l, font=SANS, fill=(230, 230, 230))
    elif kind == "loop":
        code = ["for point in points:", "    client.upsert(", '        collection_name="my_collection",', "        points=[point],", "    )"]
        for i, l in enumerate(code): d.text((70, 70 + i * 56), l, font=MONO, fill=(230, 230, 230))
        d.rectangle([56, 70 + 56 - 8, w - 56, 70 + 4 * 56], outline=RED, width=3)
    elif kind == "upload":
        code = ["client.upload_points(", '    collection_name="my_collection",', "    points=points,", "    batch_size=256,", ")"]
        for i, l in enumerate(code): d.text((70, 70 + i * 56), l, font=MONO, fill=(230, 230, 230))
        d.rectangle([56, 70 + 3 * 56 - 8, w - 56, 70 + 4 * 56], outline=RED, width=3)
    elif kind == "terminal":
        im = Image.new("RGB", (w, h), (18, 18, 18)); d = ImageDraw.Draw(im)
        for i, l in enumerate(["$ python upload_loop.py", "uploaded 100000 points", "elapsed: <your time>", "", "$ python upload_batched.py", "uploaded 100000 points in 391 batches", "elapsed: <your time>"]): d.text((60, 60 + i * 50), l, font=MONO, fill=(120, 230, 150) if l.startswith("elapsed") else (220, 220, 220))
    elif kind == "dashboard":
        d.rectangle([0, 0, w, 90], fill=(20, 24, 36)); d.text((40, 26), "my_collection", font=SANS_B, fill=(240, 240, 240)); d.text((w - 420, 26), "Points: 100000", font=SANS_B, fill=(120, 230, 150))
        d.text((70, 150), "status            green", font=MONO, fill=(220, 220, 220)); d.text((70, 206), "points count      100000", font=MONO, fill=(220, 220, 220)); d.text((70, 262), "len(points)       100000", font=MONO, fill=(120, 230, 150))
        d.text((70, 360), "batch_size=256   # halve it on request size errors", font=MONO, fill=(180, 180, 180))
    elif kind == "practice":
        for i, l in enumerate(["swap the loop for one upload_points call", "read the elapsed time", "read the point count"]): d.text((70, 90 + i * 80), f"{i + 1}  {l}", font=SANS, fill=(230, 230, 230))
    elif kind == "docs":
        return docs.resize((w, h), Image.LANCZOS)
    return im

def frame(layout, kind, corner="top-right", hook=False):
    im = Image.new("RGB", (W, H), BG)
    if layout == "full":
        im.paste(full.resize((W, H)), (0, 0))
        if hook:
            d = ImageDraw.Draw(im); d.rounded_rectangle([1180, 80, 1860, 300], radius=24, fill=(245, 244, 240)); d.text((1520, 190), "One call.\nAll your points.", font=font("georgia.ttf", 56), fill=INK, anchor="mm", align="center")
        return im
    cw = int(W * 0.80); ch = int(cw * 9 / 16); x0, y0 = (W - cw) // 2, (H - ch) // 2
    c = card(kind, cw, ch); im.paste(c, (x0, y0), rounded(c))
    if layout == "small":
        pw = int(W * 0.20); ph = int(pw * 3 / 4); p = p43.resize((pw, ph), Image.LANCZOS)
        px = x0 + cw - pw - 24 if "right" in corner else x0 + 24; py = y0 + 24
        im.paste(p, (px, py), rounded(p, 16)); ImageDraw.Draw(im).rounded_rectangle([px - 3, py - 3, px + pw + 3, py + ph + 3], radius=18, outline=(245, 244, 240), width=4)
    return im

CALLS = [
 ("0:00", "Hook", "FULL, centred", "full", None, True, "First passage; a question to the viewer; nothing to read yet. Holds 15 s."),
 ("0:15", "Before you change it", "SMALL, top right, 20%", "small", "checklist", False, "Three short lines on screen, not dense; you keep talking, so presence stays. Corner clear."),
 ("0:40", "The change", "SMALL, top right, 20% (unchanged)", "small", "loop", False, "Section boundary; code gets the small window by house rule; code card clear top right."),
 ("1:03", "The change", "(holds) same window", "small", "upload", False, "Show changes to the upload_points call, batch_size highlighted; the camera does not change."),
 ("1:20", "The change", "FULL", "full", None, False, "'Nothing about your points changes' is the explanation; face has been small 65 s."),
 ("1:30", "The change", "NONE (B-roll insert)", "none", "docs", False, "Docs page insert: looked at, and its sidebar sits top right; no window."),
 ("1:41", "The change", "NONE", "none", "terminal", False, "Terminal output runs the full width; the two times are the point of focus; no corner clear."),
 ("1:52", "The change", "FULL", "full", None, False, "'The batched one is the one to keep' is the verdict: the person's line."),
 ("2:00", "How you know it worked", "SMALL, top left, 20%", "small", "dashboard", False, "Dashboard header sits top right (points count), so the check moves the window top left for this section."),
 ("2:40", "Try it on yours", "SMALL, top right, 20%", "small", "practice", False, "New section, back to the house corner; the card is clear there."),
 ("2:52", "Try it on yours", "FULL", "full", None, False, "Last passage: close on the person."),
]
os.makedirs(os.path.join(HERE, "tiles"), exist_ok=True)
tiles = []
for i, (t, sec, call, lay, kind, hook, why) in enumerate(CALLS):
    corner = "top-left" if "top left" in call else "top-right"
    fr = frame(lay, kind, corner, hook).resize((640, 360), Image.LANCZOS)
    tile = Image.new("RGB", (640, 520), (255, 255, 255)); tile.paste(fr, (0, 0)); d = ImageDraw.Draw(tile)
    d.text((16, 372), f"{t}  {sec}", font=TB, fill=INK)
    d.rectangle([16, 404, 624, 436], fill=BG); d.text((24, 409), f"[**Camera:** {call}]", font=CALL, fill=RED)
    y = 444
    for wl in textwrap.wrap(why, 58)[:3]: d.text((16, y), wl, font=T, fill=MUTED); y += 26
    tile.save(os.path.join(HERE, "tiles", f"t{i:02d}.png")); tiles.append(tile)
cols = 3; rows = (len(tiles) + cols - 1) // cols
board = Image.new("RGB", (cols * 640 + (cols + 1) * 20, rows * 520 + (rows + 1) * 20 + 60), BG); d = ImageDraw.Draw(board)
d.text((20, 14), "Stop Uploading Points One at a Time: the camera, in script order", font=font("georgia.ttf", 34), fill=INK)
for i, tl in enumerate(tiles): board.paste(tl, (20 + (i % cols) * 660, 80 + (i // cols) * 540))
board.save(os.path.join(HERE, "batch_upload_board.png")); print("board", board.size)
