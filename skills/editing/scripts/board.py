"""How-it-works board for the editing skill, from the Bulk Uploads take."""
import os, textwrap, json, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
BG = (245, 244, 240); INK = (30, 30, 30); MUTED = (120, 120, 120); RED = (220, 36, 76)
def font(n, s):
    p = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", n); return ImageFont.truetype(p, s) if os.path.exists(p) else ImageFont.load_default()
H1 = font("georgia.ttf", 40); H2 = font("segoeuib.ttf", 28); T = font("segoeui.ttf", 23); S = font("segoeui.ttf", 20); M = font("consola.ttf", 21)
E = r"C:\Users\ADMIN\camera_audit\edit"
def frame(path, t, size):
    cap = cv2.VideoCapture(path); cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read(); cap.release()
    return Image.fromarray(cv2.cvtColor(cv2.resize(f, size), cv2.COLOR_BGR2RGB)) if ok else Image.new("RGB", size, (0, 0, 0))
W = 1920; board = Image.new("RGB", (W, 1340), BG); d = ImageDraw.Draw(board)
d.text((40, 30), "Editing: a raw take and the script in, a clean cut out", font=H1, fill=INK)
d.text((40, 84), "Six steps, shown on the Bulk Uploads Zoom take. Every decision is written to the cut list so a person can change it.", font=T, fill=MUTED)
col_w = 600; gap = 40; x0 = 40; y0 = 140; tile = (560, 315)
steps = [
 ("1  Transcribe", "Word timestamps for the whole recording.", [("transcript", None)]),
 ("2  Find the takes", "Five starts of the same line; the last complete one is kept. Stumbles and ad-libs go.", [("takes", None)]),
 ("3  Check the eyes", "Every chosen take, frame by frame: face frontal, eyes near centre. Under 80% is flagged, never swapped quietly.", [("gaze", None)]),
 ("4  Cut on the word", "0.08 s before the first word, 0.3 s after the last. Never on a breath.", [("cutword", None)]),
 ("5  Fix the picture", "Mirror the webcam image, bar over the recording tag with a matching bar on top, alternate a slight push between cuts.", [("fix", None)]),
 ("6  Write it down", "cut.mp4, the cut list (which take, what was said, eyes score) and the eye sheet.", [("cutlist", None)]),
]
raw = os.path.join(E, "raw.mp4"); cut = os.path.join(E, "cut.mp4")
for i, (title, text, _) in enumerate(steps):
    cx = x0 + (i % 3) * (col_w + gap); cy = y0 + (i // 3) * 600
    im = Image.new("RGB", tile, (235, 234, 230)); dd = ImageDraw.Draw(im)
    key = ["transcript", "takes", "gaze", "cutword", "fix", "cutlist"][i]
    if key == "transcript":
        words = json.load(open(os.path.join(E, "transcript.json")))[:3]
        y = 16
        for s in words:
            dd.text((14, y), f"{s['start']:6.2f}  {s['text'][:48]}", font=M, fill=INK); y += 30
            dd.text((14, y), "  " + " ".join(f"{w['w']}({w['s']:.1f})" for w in s["words"][:6]) + " ...", font=S, fill=MUTED); y += 34
    elif key == "takes":
        rows = [("25.1", "So we're gonna go through a few different options that you can", "stumble"), ("29.3", "So we're gonna go through a few different. So we're...", "restart"), ("35.9", "...options and best practices that you can try at home", "ad-lib"), ("44.2", "So we're gonna go through a bunch of different prep", "stumble"), ("47.3", "So we're gonna go through a bunch of different options and best practices that you can try", "KEEP")]
        y = 16
        for t, txt, tag in rows:
            dd.text((14, y), t, font=M, fill=INK); dd.text((80, y), txt[:40], font=S, fill=INK if tag == "KEEP" else MUTED); dd.text((470, y), tag, font=H2 if tag == "KEEP" else S, fill=RED if tag == "KEEP" else MUTED); y += 58
    elif key == "gaze":
        g = Image.open(os.path.join(E, "gaze_sheet.png")).convert("RGB"); im = g.crop((0, 0, 2400, 320)).resize(tile)
        dd = ImageDraw.Draw(im); dd.rectangle([0, tile[1] - 30, tile[0], tile[1]], fill=(0, 0, 0)); dd.text((10, tile[1] - 27), "56 samples across the chosen takes: all on the lens; one blink at the very first frame, so the in-point moved", font=S, fill=(255, 255, 255))
    elif key == "cutword":
        im = frame(raw, 47.3, tile); dd = ImageDraw.Draw(im)
        dd.rectangle([0, tile[1] - 92, tile[0], tile[1]], fill=(0, 0, 0))
        dd.text((12, tile[1] - 86), "So(47.28) we're(47.78) gonna(48.08) ... can(50.94) try(51.10)", font=M, fill=(255, 255, 255))
        dd.text((12, tile[1] - 54), "in 47.22   out 51.42", font=H2, fill=(220, 36, 76)); dd.text((300, tile[1] - 50), "0.08 s before 'So', 0.3 s after 'try'", font=S, fill=(230, 230, 230))
    elif key == "fix":
        a = frame(raw, 20, (280, 158)); b = frame(cut, 5.5, (280, 158)); im.paste(a, (0, 60)); im.paste(b, (280, 60))
        dd.text((14, 16), "raw: mirrored, tag bottom left", font=S, fill=INK); dd.text((294, 16), "cut: flipped, bars, push 1.06", font=S, fill=INK)
        dd.text((14, 236), "the bar hides the Zoom tag; its twin on top makes it a frame, not a patch", font=S, fill=MUTED)
        dd.text((14, 266), "push alternates 1.00 / 1.06 so each jump reads as a cut", font=S, fill=MUTED)
    elif key == "cutlist":
        lines = open(os.path.join(E, "cutlist.md"), encoding="utf-8").read().splitlines()[4:9]
        y = 14
        for l in lines:
            cells = [c.strip() for c in l.strip("|").split("|")]
            dd.text((14, y), f"{cells[0]:>6}  {cells[1]:<13} {cells[2]:<6} {cells[3][:34]}", font=M, fill=INK); y += 30
            dd.text((14, y), "      " + cells[4][:70], font=S, fill=MUTED); y += 30
    board.paste(im, (cx, cy + 50))
    d.text((cx, cy), title, font=H2, fill=INK)
    for k, wl in enumerate(textwrap.wrap(text, 52)): d.text((cx, cy + 50 + tile[1] + 12 + k * 26), wl, font=T, fill=INK)
d.text((40, 1300), "Spoken wording wins over the script; the cut list shows every difference. Nothing is added: labels, B-roll and transitions are other skills laid on afterwards.", font=S, fill=MUTED)
os.makedirs(r"C:\Users\ADMIN\.claude\skills\editing\assets", exist_ok=True)
board.save(r"C:\Users\ADMIN\.claude\skills\editing\assets\how-it-works.png"); print("board ok")
