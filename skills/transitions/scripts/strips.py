#!/usr/bin/env python
"""strips.py: a strip of frames around each transition so the label can be checked by eye.

  python strips.py VIDEO.mp4 REPORT.json --out strips.png [--per-kind 3] [--kinds cut,dissolve,...]

For up to --per-kind events of each kind: 8 frames from 0.3 s before to 0.3 s after the boundary, with the
time, the kind and the context written on the strip.
"""
if __name__ == "__main__":                                   # run on the suite's own Python (.venv, made by setup.py), whichever python started it
    import os as _o, sys as _s, subprocess as _sp
    _v = _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), "..", "..", "..", ".venv", *(("Scripts", "python.exe") if _o.name == "nt" else ("bin", "python")))
    if _o.path.exists(_v) and _o.path.normcase(_o.path.realpath(_s.prefix)) != _o.path.normcase(_o.path.realpath(_o.path.dirname(_o.path.dirname(_v)))):
        _s.exit(_sp.call([_v, _o.path.realpath(__file__)] + _s.argv[1:]))
import argparse, json, os
import cv2, numpy as np

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video"); ap.add_argument("report"); ap.add_argument("--out", required=True); ap.add_argument("--per-kind", type=int, default=3); ap.add_argument("--kinds")
    a = ap.parse_args()
    r = json.load(open(a.report)); fps = r["fps"]
    kinds = a.kinds.split(",") if a.kinds else sorted(set(e["kind"] for e in r["events"]))
    picks = []
    for k in kinds:
        evs = [e for e in r["events"] if e["kind"] == k]
        step = max(1, len(evs) // a.per_kind)
        picks += evs[::step][:a.per_kind]
    cap = cv2.VideoCapture(a.video); rows = []
    for e in picks:
        t0 = e["t"] - 0.3; tiles = []
        for i in range(8):
            cap.set(cv2.CAP_PROP_POS_MSEC, max(0, (t0 + i * 0.6 / 7) * 1000)); ok, f = cap.read()
            if not ok: f = np.zeros((180, 320, 3), np.uint8)
            tiles.append(cv2.resize(f, (320, 180)))
        row = np.hstack(tiles); cv2.rectangle(row, (0, 0), (row.shape[1], 26), (0, 0, 0), -1)
        cv2.putText(row, f"{e['t']:.2f}s  {e['kind']}  {e['frames']} f  {e['context'] or ''}", (8, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
        rows.append(row)
    cap.release()
    cv2.imwrite(a.out, np.vstack(rows)); print(f"-> {a.out}  ({len(rows)} strips)")

if __name__ == "__main__":
    main()
