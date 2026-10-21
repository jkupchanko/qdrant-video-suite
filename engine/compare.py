"""Side-by-side sheet of every style: one row per style, the same edit times across.
  python compare.py"""
import os, cv2
from PIL import Image, ImageDraw, ImageFont
OUT = r"C:\Users\ADMIN\camera_audit\styles\out"
STYLES = [("MATH  (3Blue1Brown)", "math_0-41.mp4"), ("CARTOON  (Kurzgesagt)", "cartoon_0-41.mp4"), ("DOCUMENTARY  (Species)", "doc_0-41.mp4"), ("BRIGHT  (Cleo Abram)", "bright_0-41.mp4"), ("STICK  (CGP Grey)", "stick_0-41.mp4"), ("SKETCH  (Karpathy)", "sketch_0-41.mp4"),
          ("STUDIO  (Jeff Su)", "studio_0-41.mp4"), ("LIGHTBOARD  (IBM)", "lightboard_0-41.mp4"), ("CODE  (CodeAesthetic)", "code_0-41.mp4"), ("ANNOTATED  (NetworkChuck)", "annotated_0-41.mp4"), ("FAST  (Fireship)", "fast_0-41.mp4"), ("EDITORIAL  (Vox)", "editorial_0-41.mp4"), ("FLOWCHART  (StatQuest)", "flowchart_0-41.mp4"), ("WORDS  (H3Vtux)", "words_0-41.mp4"), ("NOTES  (Tina Huang)", "notes_0-41.mp4"), ("GLOSSY  (Dan Martell)", "glossy_0-41.mp4"), ("ARCHIVE  (ColdFusion)", "archive_0-41.mp4"), ("CAPTIONS  (Hormozi)", "captions_0-41.mp4"), ("WHITEBOARD  (After Skool)", "whiteboard_0-41.mp4")]
TS = [2.2, 7.2, 12.6, 21.9, 24.6, 31.5, 37.0, 40.5]
tw, th = 320, 180; f = ImageFont.truetype(r"C:\Users\ADMIN\camera_audit\fonts\Inter[opsz,wght].ttf", 24)
rows = [s for s in STYLES if os.path.exists(os.path.join(OUT, s[1]))]
sheet = Image.new("RGB", (tw * len(TS), (th + 40) * rows.__len__()), (20, 20, 24)); d = ImageDraw.Draw(sheet)
for r, (name, fn) in enumerate(rows):
    cap = cv2.VideoCapture(os.path.join(OUT, fn)); y0 = r * (th + 40); d.text((10, y0 + 8), name, font=f, fill=(240, 240, 240))
    for i, t in enumerate(TS):
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, fr = cap.read()
        if not ok: continue
        sheet.paste(Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).resize((tw - 4, th - 4)), (i * tw + 2, y0 + 40))
for i, t in enumerate(TS): d.text((i * tw + tw - 60, 8), f"{t:.0f}s", font=f, fill=(255, 220, 0))
sheet.save(os.path.join(OUT, "all_styles_sheet.png")); print(os.path.join(OUT, "all_styles_sheet.png"), len(rows), "styles")
