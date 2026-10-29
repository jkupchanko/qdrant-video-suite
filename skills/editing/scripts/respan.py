#!/usr/bin/env python
"""respan.py: a small fix to an approved cut, without cutting it again: change the source span of chosen pieces (or split
one into several), then rebuild cut.mp4 and cutlist.md the same way cut_takes.py does (mirror, push, bars, 20 ms fades,
picture and voice locked by assemble.py). Everything not named stays exactly as it was.

  python respan.py CUT_DIR RAW.mp4 --piece "EDIT_TIME=A-B[,A-B...]" [--piece ...] [--drop EDIT_TIME] [--mirror] [--bars 72]

  EDIT_TIME  the piece's edit time as the cut list prints it (e.g. 136.57)
  A-B        new source span(s) in seconds; several spans split the piece (a pause or a false start taken out)

Bulk Uploads, 2026-10-21: at 2:21 "A ... batch size starting ... from 64 to 256" lost its pause and its first "starting"
(--piece 136.57=405.80-406.08 --piece 137.40=407.05-408.12,409.30-412.45), and at 2:23 a piece that began on the tail of
"that" was moved to start on "large" (--piece 143.30=430.36-434.68). The old cut is kept as cut_before_respan.mp4.
"""
if __name__ == "__main__":                                   # run on the suite's own Python (.venv, made by setup.py), whichever python started it
    import os as _o, sys as _s, subprocess as _sp
    _v = _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), "..", "..", "..", ".venv", *(("Scripts", "python.exe") if _o.name == "nt" else ("bin", "python")))
    if _o.path.exists(_v) and _o.path.normcase(_o.path.realpath(_s.prefix)) != _o.path.normcase(_o.path.realpath(_o.path.dirname(_o.path.dirname(_v)))):
        _s.exit(_sp.call([_v, _o.path.realpath(__file__)] + _s.argv[1:]))
import argparse, os, re, shutil, sys
import cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from assemble import assemble

ROW = re.compile(r"^\| ([\d.]+) \| ([\d.]+)-([\d.]+) \| x([\d.]+) \| (.*?) \| (.*?) \| (.*?) \|$")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cut_dir"); ap.add_argument("raw")
    ap.add_argument("--piece", action="append", default=[], help="EDIT_TIME=A-B[,A-B...]"); ap.add_argument("--drop", action="append", default=[])
    ap.add_argument("--mirror", action="store_true"); ap.add_argument("--bars", type=int, default=0); ap.add_argument("--size", default="1920x1080")
    a = ap.parse_args()
    cl = os.path.join(a.cut_dir, "cutlist.md"); L = open(cl, encoding="utf-8").read().splitlines()
    new = {k.split("=")[0].strip(): [tuple(float(x) for x in s.split("-")) for s in k.split("=")[1].split(",")] for k in a.piece}
    drop = {d.strip() for d in a.drop}
    rows = [(i, ROW.match(l)) for i, l in enumerate(L) if ROW.match(l)]
    missing = (set(new) | drop) - {m.group(1) for _, m in rows}
    if missing: sys.exit(f"no piece at edit time {', '.join(sorted(missing))} in {cl}")
    pieces = []                                                                  # (x0, x1, push, line, said, note)
    for _, m in rows:
        t, x0, x1, push, line, said, note = m.groups()
        if t in drop: continue
        for k, (y0, y1) in enumerate(new.get(t, [(float(x0), float(x1))])):
            pieces.append((y0, y1, float(push), line if k == 0 else "(same line, after a pause)", said if k == 0 else "",
                           (note + "; respanned by hand") if t in new else note))
    W, H = (int(v) for v in a.size.split("x")); c = cv2.VideoCapture(a.raw); sw, sh = int(c.get(3)), int(c.get(4)); c.release()
    def vf(k):
        push = pieces[k][2]; cw, ch = int(sw / push), int(sh / push); cx, cy = (sw - cw) // 2, (sh - ch) // 2
        return ("hflip," if a.mirror else "") + f"crop={cw}:{ch}:{cx}:{cy},scale={W}:{H}:flags=lanczos" + \
               (f",drawbox=x=0:y=0:w={W}:h={a.bars}:color=black:t=fill,drawbox=x=0:y={H - a.bars}:w={W}:h={a.bars}:color=black:t=fill" if a.bars else "")
    out = os.path.join(a.cut_dir, "cut.mp4"); shutil.copy(out, os.path.join(a.cut_dir, "cut_before_respan.mp4"))
    tmp = os.path.join(a.cut_dir, "cut_respan.mp4")
    times = assemble(a.raw, [(p[0], p[1]) for p in pieces], tmp, vf_for=vf); os.replace(tmp, out)
    head = L[:rows[0][0]]; tail = L[rows[-1][0] + 1:]
    body = [f"| {t:.2f} | {p[0]:.2f}-{p[1]:.2f} | x{p[2]:.2f} | {p[3]} | {p[4]} | {p[5]} |" for t, p in zip(times, pieces)]
    total = times[-1] + pieces[-1][1] - pieces[-1][0]
    tail = [re.sub(r"Total [\d.]+ s, \d+ cuts", f"Total {total:.1f} s, {len(pieces)} cuts", l) for l in tail]
    open(cl, "w", encoding="utf-8").write("\n".join(head + body + tail) + "\n")
    print(f"respanned {len(new)} piece(s), dropped {len(drop)}: {len(pieces)} pieces, {total:.1f} s -> {out}")

if __name__ == "__main__":
    main()
