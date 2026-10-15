"""Explanatory boards for the transitions skill and the B-roll key-term rule, in the same style as the camera boards."""
import os, subprocess, textwrap, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
BG = (245, 244, 240); INK = (30, 30, 30); MUTED = (120, 120, 120); RED = (220, 36, 76); DARK = (11, 15, 25)
def font(n, s):
    p = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", n)
    return ImageFont.truetype(p, s) if os.path.exists(p) else ImageFont.load_default()
H1 = font("georgia.ttf", 40); H2 = font("segoeuib.ttf", 28); T = font("segoeui.ttf", 24); S = font("segoeui.ttf", 20); M = font("consola.ttf", 22)
OUT_T = r"C:\Users\ADMIN\.claude\skills\transitions\assets"; OUT_B = r"C:\Users\ADMIN\.claude\skills\broll-recorder\assets"
os.makedirs(OUT_T, exist_ok=True); os.makedirs(OUT_B, exist_ok=True)
SEEN = r"C:\Users\ADMIN\camera_audit\john_video\seen"

def frames_across(path, t_join, n=6, span=0.9, size=(224, 126)):
    cap = cv2.VideoCapture(path); out = []
    for i in range(n):
        t = t_join - span / 2 + i * span / (n - 1)
        cap.set(cv2.CAP_PROP_POS_MSEC, max(0, t * 1000)); ok, f = cap.read()
        if not ok: f = np.zeros((144, 256, 3), np.uint8)
        f = cv2.cvtColor(cv2.resize(f, size), cv2.COLOR_BGR2RGB); out.append(Image.fromarray(f))
    cap.release(); return out

# ---------- A. vocabulary board: the four things the model videos do, each as frames across a real join on John's footage
rows = [
 ("Cut", f"{SEEN}/01_face_to_card/cut.mp4", 3.0, "At every camera call. 138 of 185 face-to-screen joins in the eight model videos.", "Default. Lands on the sentence turn the camera call already sits on."),
 ("Push, 0.3 s", f"{SEEN}/01_face_to_card/slideleft.mp4", 3.0, "When a card arrives over the presenter. 7 of 185 (Futurepedia, Aishwarya, NetworkChuck).", "One direction for the whole video. Cards leave on a cut, never a reverse push."),
 ("White flash, 0.3 s", f"{SEEN}/04_chapter/fadewhite.mp4", 3.0, "At a chapter boundary. 5 of 185 (Jeff Su, Futurepedia).", "A few per video at most; never inside a demonstration."),
 ("Element entrance", r"C:\Users\ADMIN\Desktop\Qdrant Videos\Bulk Uploads\Bulk Uploads_FinalCleanUps.mp4", 32.8, "A label or card appears over a shot that stays. 62% of all visible motion in the corpus.", "Graphics work, not a transition: one entrance style for the whole video."),
]
W = 1920; row_h = 230; board = Image.new("RGB", (W, 120 + row_h * len(rows) + 90), BG); d = ImageDraw.Draw(board)
d.text((40, 30), "Transitions: the whole vocabulary, measured from 50 videos", font=H1, fill=INK)
d.text((40, 82), "Nothing else is used. Dissolves, black fades, punch-ins and wipes were not seen at the joins of the model videos.", font=T, fill=MUTED)
y = 120
for name, path, tj, when, rule in rows:
    fr = frames_across(path, tj)
    for i, im in enumerate(fr): board.paste(im, (40 + i * 230, y + 12))
    d.line([(40 + 3 * 230 - 3, y + 8), (40 + 3 * 230 - 3, y + 142)], fill=RED, width=3)
    tx = 40 + 6 * 230 + 30
    d.text((tx, y + 10), name, font=H2, fill=INK)
    for k, wl in enumerate(textwrap.wrap(when, 44)): d.text((tx, y + 50 + k * 28), wl, font=T, fill=INK)
    yy = y + 50 + 28 * len(textwrap.wrap(when, 44)) + 6
    for k, wl in enumerate(textwrap.wrap(rule, 52)): d.text((tx, yy + k * 24), wl, font=S, fill=MUTED)
    d.text((40, y + 146), "0.45 s before the join                       the join                       0.45 s after", font=S, fill=MUTED)
    y += row_h
d.text((40, y + 10), "Frames are from the Bulk Uploads footage rendered by render_transitions.py; the counts are from references/models.md.", font=S, fill=MUTED)
board.save(os.path.join(OUT_T, "vocabulary-board.png")); print("A ok")

# ---------- B. where the transitions go in a script: the batch-upload camera plan as a timeline
calls = [(0, "FULL", "cut"), (15, "SMALL top right", "push 0.3 s: the checklist arrives"), (40, "SMALL stays", "cut"), (80, "FULL", "cut"), (90, "NONE: docs insert", "cut"), (101, "NONE: terminal", "cut"), (112, "FULL", "cut"), (120, "SMALL top left", "cut"), (160, "SMALL top right", "cut"), (172, "FULL", "cut to end card")]
total = 180; W2 = 1920; board = Image.new("RGB", (W2, 600), BG); d = ImageDraw.Draw(board)
d.text((40, 30), "Where a transition goes: the script's camera calls are the joins", font=H1, fill=INK)
d.text((40, 82), "Stop Uploading Points One at a Time (3:00). Every camera call is a cut unless a rule says otherwise. One push in the video, where the first card arrives.", font=T, fill=MUTED)
x0, x1, yb = 60, W2 - 60, 290
d.line([(x0, yb), (x1, yb)], fill=INK, width=3)
for s in range(0, total + 1, 30):
    x = x0 + (x1 - x0) * s / total; d.line([(x, yb - 8), (x, yb + 8)], fill=INK, width=2); d.text((x - 16, yb + 14), f"{s // 60}:{s % 60:02d}", font=S, fill=MUTED)
col = {"FULL": (30, 30, 30), "SMALL": (40, 120, 200), "NONE": (160, 160, 160)}
for i, (t, lay, tr) in enumerate(calls):
    x = x0 + (x1 - x0) * t / total; key = lay.split()[0].rstrip(":")
    push = tr.startswith("push")
    d.ellipse([x - 9, yb - 9, x + 9, yb + 9], fill=RED if push else col.get(key, INK))
    up = (i % 2 == 0)
    ty = yb - 70 - (26 if up else -0) if up else yb + 50
    d.line([(x, yb - 10 if up else yb + 10), (x, ty + (40 if up else 0))], fill=(190, 190, 190), width=1)
    d.text((x - 10, ty - 24 if up else ty + 4), lay, font=S, fill=col.get(key, INK))
    d.text((x - 10, ty if up else ty + 28), tr, font=S, fill=RED if push else MUTED)
d.text((40, 470), "Black dot: FULL. Blue: SMALL window. Grey: NONE. Red: the one soft move, a 0.3 s push as a card arrives over the presenter.", font=T, fill=INK)
d.text((40, 506), "Dissolves and fades do not appear because the model videos do not use them at these joins. Chapter flashes would sit at section headings, a few per video at most.", font=S, fill=MUTED)
board.save(os.path.join(OUT_T, "where-in-the-script.png")); print("B ok")

# ---------- C. the numbers as a board with proportional bars
data = [("cut", 65.3), ("animated card moves (other)", 20.1), ("slide / push", 5.9), ("dissolve", 3.7), ("fade to white", 2.3), ("fade to black", 1.9), ("punch-in / out", 0.5), ("zoom", 0.2)]
models = [("cut", 138), ("animated card entrance", 31), ("push / slide", 7), ("white flash", 5), ("dissolve", 4), ("fade to black", 0), ("punch-in", 0)]
board = Image.new("RGB", (1920, 700), BG); d = ImageDraw.Draw(board)
d.text((40, 30), "What the watched videos do at a shot change", font=H1, fill=INK)
d.text((40, 100), "All 50 videos, share of real shot changes (3,290)", font=H2, fill=INK)
for i, (k, v) in enumerate(data):
    y = 150 + i * 44; d.text((40, y), k, font=T, fill=INK); d.rectangle([420, y + 6, 420 + int(v * 7), y + 30], fill=RED if k == "cut" else (120, 120, 120)); d.text((430 + int(v * 7), y + 2), f"{v:.1f}%", font=T, fill=INK)
d.text((1040, 100), "The eight model videos, joins between face and screen (185)", font=H2, fill=INK)
for i, (k, v) in enumerate(models):
    y = 150 + i * 44; d.text((1040, y), k, font=T, fill=INK); d.rectangle([1400, y + 6, 1400 + int(v * 3), y + 30], fill=RED if k == "cut" else (120, 120, 120)); d.text((1410 + int(v * 3), y + 2), str(v), font=T, fill=INK)
d.text((40, 540), "62% of everything that moves on screen is not a shot change at all: a label, caption or card appearing over a shot that stays.", font=T, fill=INK)
d.text((40, 576), "Soft moves, where used, last a median 0.27 s. Median pace: 2.6 shot changes a minute, 11.7 visible changes a minute with elements counted.", font=T, fill=INK)
d.text((40, 630), "From references/tendencies.md and references/models.md. 360p copies were audited; very fast moves can register as 'animated'.", font=S, fill=MUTED)
board.save(os.path.join(OUT_T, "numbers-board.png")); print("C ok")

# ---------- D. B-roll by key term
ex = [
 ("So we will go over a few different options and best practices you can try.", "none", "", "none: general talk, the person carries it"),
 ("The second dense-vector option is creating your payload indexes before uploading.", "payload indexes", "Option 2: Create Payload Indexes (Before Uploading)", "B-ROLL: a named thing, and the page has a section about it"),
 ("If you already know which fields you'll filter on, such as category, tenant ID...", "filter, tenant", "Option 2 (same section)", "hold: same section is already up, no new insert"),
 ("This avoids creating those indexes after a large dataset is already populated.", "indexes", "", "none: a consequence line (This...), the person's; generic word only"),
 ("The first best practice is to batch your uploads.", "batch", "Batch Your Uploads", "B-ROLL: first mention of a named thing"),
 ("Thanks for watching!", "", "", "none"),
]
board = Image.new("RGB", (1920, 160 + 100 * len(ex) + 80), BG); d = ImageDraw.Draw(board)
d.text((40, 30), "B-roll by key term: which lines earn an insert", font=H1, fill=INK)
d.text((40, 82), "A line names something specific -> the page section about it. General talk, transitions and consequences stay on the person. One insert per section.", font=T, fill=MUTED)
d.text((40, 130), "script line", font=H2, fill=INK); d.text((900, 130), "key terms", font=H2, fill=INK); d.text((1180, 130), "page section", font=H2, fill=INK); d.text((1560, 130), "call", font=H2, fill=INK)
for i, (l, terms, sec, call) in enumerate(ex):
    y = 170 + i * 100; c = RED if call.startswith("B-ROLL") else (MUTED if call.startswith("none") else (40, 120, 200))
    for k, wl in enumerate(textwrap.wrap(l, 60)[:2]): d.text((40, y + k * 26), wl, font=T, fill=INK)
    d.text((900, y), terms or "-", font=M, fill=INK)
    for k, wl in enumerate(textwrap.wrap(sec or "-", 28)[:2]): d.text((1180, y + k * 26), wl, font=T, fill=INK)
    for k, wl in enumerate(textwrap.wrap(call, 30)[:3]): d.text((1560, y + k * 24), wl, font=S, fill=c)
    d.line([(40, y + 84), (1880, y + 84)], fill=(215, 215, 210), width=1)
d.text((40, 170 + 100 * len(ex) + 10), "scripts/keyterms.py SCRIPT.md URL prints this for every line and writes the B-ROLL markers the recorder reads.", font=S, fill=MUTED)
board.save(os.path.join(OUT_B, "keyterm-board.png")); print("D ok")
