"""Save full-size frames of the animated-board style in the current look (BOARD_THEME) at given edit times.
  BOARD_THEME=paper python dump_frames.py 3.5 16.5 29 39   -> out/gallery/paper_3.5.png ..."""
import os, sys, cv2
from PIL import Image
import engine as E, style_full as F
ts = [float(x) for x in sys.argv[1:]]; p = F.project(); S, sfx = F.plan(p, 0, max(ts) + 2); r = E.Renderer(p, S, 0, p.dur, F.OUT, sfx, F.BG)
os.makedirs(r"out\gallery", exist_ok=True); cap = cv2.VideoCapture(p.base)
for t in ts:
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read(); fi = Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)).convert("RGBA")
    s = r.shot_at(t); prev = r.prev_shot(s); pl = r.base_frame(prev, prev["t1"] - 0.01, fi)[0] if prev and prev["kind"] != "face" else None
    fr, shows = r.compose(t, fi, pl); fr.convert("RGB").save(rf"out\gallery\{F.THEME}_{t}.png"); print(F.THEME, t, "face" if shows else "no face")
