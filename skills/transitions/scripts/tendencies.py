#!/usr/bin/env python
"""tendencies.py: roll per-video transition audits into the habits the corpus shares.

  python tendencies.py --audit transitions/ [--meta meta.txt] [--out transitions.md]
"""
if __name__ == "__main__":                                   # run on the suite's own Python (.venv, made by setup.py), whichever python started it
    import os as _o, sys as _s, subprocess as _sp
    _v = _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), "..", "..", "..", ".venv", *(("Scripts", "python.exe") if _o.name == "nt" else ("bin", "python")))
    if _o.path.exists(_v) and _o.path.normcase(_o.path.realpath(_s.prefix)) != _o.path.normcase(_o.path.realpath(_o.path.dirname(_o.path.dirname(_v)))):
        _s.exit(_sp.call([_v, _o.path.realpath(__file__)] + _s.argv[1:]))
import argparse, json, os
from collections import Counter, defaultdict
import numpy as np

KINDS = ["cut", "punch-in", "punch-out", "dissolve", "fade-black", "fade-white", "slide", "zoom", "other", "element-in", "element-anim"]

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audit", required=True); ap.add_argument("--meta"); ap.add_argument("--out", default="transitions.md")
    a = ap.parse_args()
    meta = {}
    if a.meta and os.path.exists(a.meta):
        for l in open(a.meta, encoding="utf-8", errors="ignore"):
            p = l.strip().split("|")
            if len(p) >= 5: meta[p[0]] = {"views": int(p[2] or 0), "channel": p[3], "title": p[4]}
    reps = [json.load(open(os.path.join(a.audit, f))) | {"id": f[:-5]} for f in sorted(os.listdir(a.audit)) if f.endswith(".json")]
    L = [f"# Transition tendencies ({len(reps)} videos)\n", "Kinds: cut (one frame to the next), punch-in/out (a cut to the same shot tighter or wider), dissolve (blend), fade-black/white, slide (content moves across), zoom (content scales as a move), other (a whole-frame change that is none of those), element-in/element-anim (a label, card or caption appears over a shot that stays; not a shot change).\n"]
    tot = Counter(); n_ev = 0
    for r in reps:
        for k, v in r["counts"].items(): tot[k] += v; n_ev += v
    L.append("## Across the corpus\n")
    L.append("| kind | share of all changes | videos using it (3+ times) |"); L.append("|---|---|---|")
    for k in KINDS:
        users = sum(1 for r in reps if r["counts"].get(k, 0) >= 3)
        L.append(f"| {k} | {100 * tot[k] / n_ev:.1f}% | {users}/{len(reps)} |")
    shot_kinds = [k for k in KINDS if not k.startswith("element")]
    n_shot = sum(tot[k] for k in shot_kinds)
    L.append(f"\nElements (labels, captions, cards appearing over a shot that stays) are {100 * (n_ev - n_shot) / n_ev:.0f}% of all visible changes. Among SHOT changes only ({n_shot}):\n")
    L.append("| kind | share of shot changes |"); L.append("|---|---|")
    for k in shot_kinds: L.append(f"| {k} | {100 * tot[k] / n_shot:.1f}% |")
    shot_pm = [sum(v for k, v in r["counts"].items() if not k.startswith("element")) / (r["duration"] / 60) for r in reps if r["duration"]]
    L.append(f"\nShot changes per minute: median {np.median(shot_pm):.1f} (range {min(shot_pm):.1f} to {max(shot_pm):.1f}).")
    pm = [r["per_min"] for r in reps]
    L.append(f"\nVisible changes per minute: median {np.median(pm):.1f} (range {min(pm):.1f} to {max(pm):.1f}).")
    soft = [r["soft_median_s"] for r in reps if r["soft_median_s"]]
    L.append(f"Length of a soft transition (dissolve, fade, slide, zoom) where used: median {np.median(soft):.2f} s.")
    hard_share = [100 * (r["counts"].get("cut", 0) + r["counts"].get("punch-in", 0) + r["counts"].get("punch-out", 0)) / max(1, r["n"]) for r in reps]
    L.append(f"Share of changes that are hard (cut or punch): median video {np.median(hard_share):.0f}%; {sum(1 for h in hard_share if h >= 80)}/{len(reps)} videos are 80%+ hard.")
    # by context
    ctx = defaultdict(Counter)
    for r in reps:
        for c, d in r.get("by_context", {}).items():
            if c and "None" not in c:
                for k, v in d.items(): ctx[c][k] += v
    L.append("\n## By what changes\n")
    L.append("| from -> to | changes | cut | punch | dissolve | fade | slide | zoom | other |"); L.append("|---|---|---|---|---|---|---|---|---|")
    for c, d in sorted(ctx.items(), key=lambda kv: -sum(kv[1].values())):
        n = sum(d.values())
        def pct(*ks): return f"{100 * sum(d.get(k, 0) for k in ks) / n:.0f}%"
        L.append(f"| {c} | {n} | {pct('cut')} | {pct('punch-in', 'punch-out')} | {pct('dissolve')} | {pct('fade-black', 'fade-white')} | {pct('slide')} | {pct('zoom')} | {pct('other')} |")
    L.append("\n## Per video\n")
    L.append("| id | channel | min | changes/min | hard % | cut | punch | dissolve | fade | slide | zoom | other |"); L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in sorted(reps, key=lambda r: -meta.get(r["id"], {}).get("views", 0)):
        c = r["counts"]; m = meta.get(r["id"], {}); hard = 100 * (c.get("cut", 0) + c.get("punch-in", 0) + c.get("punch-out", 0)) / max(1, r["n"])
        L.append(f"| {r['id']} | {m.get('channel', '')[:18]} | {r['duration'] / 60:.0f} | {r['per_min']:.1f} | {hard:.0f} | {c.get('cut', 0)} | {c.get('punch-in', 0) + c.get('punch-out', 0)} | {c.get('dissolve', 0)} | {c.get('fade-black', 0) + c.get('fade-white', 0)} | {c.get('slide', 0)} | {c.get('zoom', 0)} | {c.get('other', 0)} |")
    open(a.out, "w", encoding="utf-8").write("\n".join(L) + "\n"); print(f"-> {a.out}")

if __name__ == "__main__":
    main()
