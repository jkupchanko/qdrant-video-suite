#!/usr/bin/env python
"""chapters.py: YouTube chapters for a cut, from the script's sections and where the cut actually says them.

  python chapters.py SCRIPT.md CUTLIST.md [--offset 0] [--min 10] [--out chapters.txt]   -> "0:00 Intro" lines

A section starts at the first cut list row that says one of its lines (the planned times in the script's headings are a
plan; the cut is what plays). The heading is the chapter's title, without its times.

YouTube shows chapters only when the first is at 0:00, there are at least three, and each lasts 10 s or more. 41 of the
49 audited videos have chapters (references/research.md). The script's sections are the chapters: its author chose them.
A section the cut leaves under 10 s (--min) joins the next one and both titles are kept ("Console and Collections"), so
no topic disappears from the list; a section the cut does not say at all has no chapter.
--offset: seconds before the cut starts in the finished video (an intro card), added to every chapter after the first.
"""
import argparse, difflib, re, sys

def norm(s): return re.sub(r"[^a-z0-9 ]", "", s.lower().replace("’", "'")).strip()

def sections(script):
    """[(title, [spoken lines])]: ## headings; spoken lines are the plain ones, not [directions] or <!-- notes -->"""
    out, note = [], False
    for ln in open(script, encoding="utf-8"):
        s = ln.strip()
        if note or s.startswith("<!--"):
            note = "-->" not in s; continue
        m = re.match(r"^##\s+(.+?)(\s+\d+:\d{2}\s+to\s+\d+:\d{2})?\s*$", s)
        if m: out.append((m.group(1).strip(), [])); continue
        if out and s and not s.startswith(("[", "#", "|", ">", "---")) and s.lower() != "count": out[-1][1].append(s)
    return [(t, L) for t, L in out if L and t.lower() != "count"]

def rows(cutlist):
    return [(float(t), line.strip()) for t, line in re.findall(r"^\|\s*([\d.]+)\s*\|\s*[\d.]+-[\d.]+\s*\|[^|]*\|\s*(.*?)\s*\|", open(cutlist, encoding="utf-8").read(), flags=re.M)]

def ts(t): t = int(round(t)); return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"

def chapters(script, cutlist, offset=0.0, min_s=10.0):
    S, R = sections(script), rows(cutlist)
    starts, k_seen = [], set()
    for title, lines in S:
        want = [norm(l) for l in lines]
        hit = [t for t, line in R if line and not line.startswith("(") and any(norm(line) == w or difflib.SequenceMatcher(None, norm(line), w).ratio() >= 0.85 for w in want)]
        if hit: starts.append([title, min(hit)])
    starts.sort(key=lambda c: c[1])
    if not starts: return []
    starts[0][1] = 0.0                                                    # YouTube's rule: the first chapter is at 0:00
    for c in starts[1:]: c[1] += offset
    end = R[-1][0] + 5 if R else starts[-1][1] + 60
    merged, carry = [], None
    for i, (title, t) in enumerate(starts):
        nxt = starts[i + 1][1] if i + 1 < len(starts) else end
        if carry: title, t = f"{carry[0]} and {title}", carry[1]; carry = None
        if nxt - t < min_s and i + 1 < len(starts): carry = (title, t); continue   # too short: it joins the next, titles kept
        merged.append([title, t])
    if len(merged) > 1 and end - merged[-1][1] < min_s:                   # a short last one joins the one before
        last = merged.pop(); merged[-1][0] += f" and {last[0]}"
    return merged if len(merged) >= 3 else []

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script"); ap.add_argument("cutlist"); ap.add_argument("--offset", type=float, default=0.0); ap.add_argument("--min", type=float, default=10.0)
    ap.add_argument("--out"); a = ap.parse_args()
    C = chapters(a.script, a.cutlist, a.offset, a.min)
    if not C: sys.exit("fewer than three chapters of 10 s or more: YouTube would not show them")
    text = "\n".join(f"{ts(t)} {title}" for title, t in C)
    print(text)
    if a.out: open(a.out, "w", encoding="utf-8").write(text + "\n")

if __name__ == "__main__":
    main()
