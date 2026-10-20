"""Map look-aways in the raw take onto the cut: which edit-time stretches show the presenter off the lens.
Writes lookaways.json next to the cut list: [{edit_start, edit_end, len, why, source, line}]."""
import json, re, sys
gaze, cutlist, out = sys.argv[1], sys.argv[2], sys.argv[3]
st = json.load(open(gaze))["lookaways"]; res = []
for r in open(cutlist, encoding="utf-8"):
    m = re.match(r"^\| (\d+):([\d.]+) \| ([\d.]+)-([\d.]+) \| (.*?) \|", r)
    if not m: continue
    e0 = int(m[1]) * 60 + float(m[2]); a, b, line = float(m[3]), float(m[4]), m[5]
    for s in st:
        if s["end"] > a and s["start"] < b:
            x0, x1 = max(a, s["start"]), min(b, s["end"])
            if x1 - x0 >= 0.3: res.append({"edit_start": round(e0 + x0 - a, 2), "edit_end": round(e0 + x1 - a, 2), "len": round(x1 - x0, 2), "why": s["why"], "source": round(x0, 2), "line": line})
json.dump(res, open(out, "w"), indent=1)
for x in res: print(f"  edit {x['edit_start']:7.2f}-{x['edit_end']:7.2f}  {x['len']:.1f} s  {x['why']:28s} | {x['line'][:55]}")
print(f"{len(res)} stretches -> {out}")
