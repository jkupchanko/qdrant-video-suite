#!/usr/bin/env python
"""tendencies.py: roll per-video audits up into the habits the corpus shares.

  python tendencies.py --audit audit/ [--meta meta.txt] [--out tendencies.md]

Reads every <id>.json written by audit.py and reports, across the corpus and split by video kind
(short explainer < 7 min, tutorial 7-25 min, long 25+ min):
  share of time in each layout, how often the camera changes, typical run length of each layout,
  what each layout is most often followed by, where in the timeline switches cluster, how videos open and
  close, which corner the window lives in, and what the window sits over (editor / page / other).
"""
import argparse, json, os
from collections import Counter, defaultdict
import numpy as np

LAYOUTS = ("full", "half", "inset", "small", "none")

def kind(dur):
    return "short (<7 min)" if dur < 420 else ("tutorial (7-25 min)" if dur < 1500 else "long (25+ min)")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audit", required=True); ap.add_argument("--meta"); ap.add_argument("--out", default="tendencies.md")
    a = ap.parse_args()
    meta = {}
    if a.meta and os.path.exists(a.meta):
        for l in open(a.meta, encoding="utf-8", errors="ignore"):
            p = l.strip().split("|")
            if len(p) >= 5: meta[p[0]] = {"views": int(p[2] or 0), "channel": p[3], "title": p[4]}
    reps = []
    for fn in sorted(os.listdir(a.audit)):
        if fn.endswith(".json"):
            r = json.load(open(os.path.join(a.audit, fn))); r["id"] = fn[:-5]; r["kind"] = kind(r["duration"]); reps.append(r)
    groups = defaultdict(list)
    for r in reps: groups[r["kind"]].append(r)
    groups["all"] = reps
    L = []
    L.append(f"# Camera layout tendencies ({len(reps)} videos)\n")
    L.append("Layouts: full = talking head; half = presenter in a split beside content; inset = large picture-in-picture; small = small picture-in-picture; none = screen only.\n")
    for g in ("all", "short (<7 min)", "tutorial (7-25 min)", "long (25+ min)"):
        rs = groups.get(g)
        if not rs: continue
        L.append(f"\n## {g}  ({len(rs)} videos)\n")
        share = {k: np.mean([r["share"][k] for r in rs]) for k in LAYOUTS}
        used = {k: sum(1 for r in rs if r["share"][k] >= 0.05) for k in LAYOUTS}
        L.append("| layout | share of time (mean) | videos using it (>=5% of time) | typical run (median s) |")
        L.append("|---|---|---|---|")
        for k in LAYOUTS:
            runs = [r["avg_segment_s"][k] for r in rs if k in r["avg_segment_s"]]
            L.append(f"| {k} | {100 * share[k]:.0f}% | {used[k]}/{len(rs)} | {np.median(runs):.0f} |" if runs else f"| {k} | {100 * share[k]:.0f}% | {used[k]}/{len(rs)} | - |")
        n_layouts = [sum(1 for k in LAYOUTS if r["share"][k] >= 0.05) for r in rs]
        L.append(f"\nLayouts per video (used >= 5% of the time): median {np.median(n_layouts):.0f}; {sum(1 for n in n_layouts if n >= 3)}/{len(rs)} videos use three or more.")
        longest = {k: np.median([max((sg["end"] - sg["start"]) for sg in r["segments"] if sg["layout"] == k) for r in rs if any(sg["layout"] == k for sg in r["segments"])]) for k in LAYOUTS if any(any(sg["layout"] == k for sg in r["segments"]) for r in rs)}
        L.append("Longest single run of each layout (median across videos): " + ", ".join(f"{k} {v:.0f} s" for k, v in longest.items()) + ".")
        spm = [r["switches_per_min"] for r in rs]
        L.append(f"\nCamera changes per minute: median {np.median(spm):.1f} (range {min(spm):.1f} to {max(spm):.1f}).")
        first_sw = [r["segments"][1]["start"] for r in rs if len(r["segments"]) > 1]
        open_len = [r["segments"][0]["end"] - r["segments"][0]["start"] for r in rs]
        L.append(f"Opening shot holds for a median {np.median(open_len):.0f} s before the first change (range {min(open_len):.0f} to {max(open_len):.0f}).")
        opens = Counter(r["opens_with"] for r in rs); closes = Counter(r["closes_with"] for r in rs)
        L.append(f"Opens with: {', '.join(f'{k} {v}' for k, v in opens.most_common())}. Closes with: {', '.join(f'{k} {v}' for k, v in closes.most_common())}.")
        thirds = np.sum([r["switches_by_third"] for r in rs], axis=0); tot = thirds.sum() or 1
        L.append(f"Where switches fall: first third {100 * thirds[0] / tot:.0f}%, middle {100 * thirds[1] / tot:.0f}%, last third {100 * thirds[2] / tot:.0f}%.")
        corners = Counter(r["small_corner"] for r in rs if r["small_corner"])
        if corners: L.append(f"Window corner: {', '.join(f'{k} {v}' for k, v in corners.most_common())}.")
        over = Counter()
        for r in rs:
            for k, v in r["small_over"].items(): over[k] += v
        if over:
            t = sum(over.values()); L.append(f"What the window sits over: {', '.join(f'{k} {100 * v // t}%' for k, v in over.most_common())}.")
        trans = Counter()
        for r in rs:
            for k, v in r["transitions"].items(): trans[k] += v
        if trans:
            L.append("\nMost common changes (from -> to):\n")
            t = sum(trans.values())
            for k, v in trans.most_common(8): L.append(f"- {k}: {100 * v / t:.0f}%")
        # pattern label per video
        L.append("\nPer video:\n")
        L.append("| id | channel | min | pattern | full | half | inset | small | none | sw/min | corner |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for r in sorted(rs, key=lambda r: -meta.get(r["id"], {}).get("views", 0)):
            s = r["share"]; dom = max(LAYOUTS, key=lambda k: s[k])
            if s["none"] > 0.85: pat = "screen only (voiceover)"
            elif s["full"] > 0.85: pat = "talking head only"
            elif s["full"] >= 0.3 and s["none"] >= 0.3: pat = "cuts between face and screen"
            elif s["inset"] + s["small"] >= 0.4: pat = "window over screen most of the time"
            elif s["half"] >= 0.3: pat = "split screen"
            else: pat = f"mixed, mostly {dom}"
            m = meta.get(r["id"], {})
            L.append(f"| {r['id']} | {m.get('channel', '')[:18]} | {r['duration'] / 60:.0f} | {pat} | {100 * s['full']:.0f} | {100 * s['half']:.0f} | {100 * s['inset']:.0f} | {100 * s['small']:.0f} | {100 * s['none']:.0f} | {r['switches_per_min']:.1f} | {r['small_corner'] or ''} |")
    open(a.out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"-> {a.out}")

if __name__ == "__main__":
    main()
