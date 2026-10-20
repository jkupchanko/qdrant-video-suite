"""Rebuild a face cut from its cut list with sound and picture locked (editing skill's assemble.py).
  python rebuild_locked.py full_edit/cutlist_v2.md full_edit/bulk_uploads_full_edit_v2_locked.mp4"""
import re, sys
sys.path.insert(0, r"C:\Users\ADMIN\.claude\skills\editing\scripts")
from assemble import assemble
SRC = "raw.mp4"; W, H, BAR = 1920, 1080, 72
cl, out = sys.argv[1], sys.argv[2]; spans, times = [], []
for r in open(cl, encoding="utf-8"):
    m = re.match(r"^\| (\d+):([\d.]+) \| ([\d.]+)-([\d.]+) \|", r)
    if m: times.append(int(m[1]) * 60 + float(m[2])); spans.append((float(m[3]), float(m[4])))
def vf(k):
    push = 1.0 if k % 2 == 0 else 1.06; cw, ch = int(1280 / push), int(720 / push); cx, cy = (1280 - cw) // 2, (720 - ch) // 2
    return (f"hflip,crop={cw}:{ch}:{cx}:{cy},scale={W}:{H}:flags=lanczos,drawbox=x=0:y=0:w={W}:h={BAR}:color=black:t=fill,"
            f"drawbox=x=0:y={H - BAR}:w={W}:h={BAR}:color=black:t=fill")
assemble(SRC, spans, out, vf_for=vf, times=times, crf=15)
