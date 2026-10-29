#!/usr/bin/env python
"""camera_plan.py: turn a script into a camera plan (which layout, how big, where, for how long).

  python camera_plan.py SCRIPT.md [--out plan.md] [--style cut|window] [--corner bottom-right]

Reads a script in the suite's layout (## Section   m:ss to m:ss, passages, [**Camera:** ...] [**Show:** ...]
[**B roll:** ...] directions) or a plain script with headings and paragraphs. For every passage it decides one
of five layouts (full, half, inset, small, none), then checks the whole plan against the corpus habits:
hold the opening about 20 s, keep at least three layouts in anything over three minutes, bring the face back
to full within about 40 s of leaving it, never leave the viewer without a face for more than about 50 s, hide
the face whenever something must be read, keep the same window corner through a section, and change at
section boundaries or when the material changes rather than on a timer.

Output: a markdown table (time, section, what is said, layout, size and position, hold, why), followed by the
checks and any conflicts with Camera directions already in the script.
"""
if __name__ == "__main__":                                   # run on the suite's own Python (.venv, made by setup.py), whichever python started it
    import os as _o, sys as _s, subprocess as _sp
    _v = _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), "..", "..", "..", ".venv", *(("Scripts", "python.exe") if _o.name == "nt" else ("bin", "python")))
    if _o.path.exists(_v) and _o.path.normcase(_o.path.realpath(_s.prefix)) != _o.path.normcase(_o.path.realpath(_o.path.dirname(_o.path.dirname(_v)))):
        _s.exit(_sp.call([_v, _o.path.realpath(__file__)] + _s.argv[1:]))
import argparse, re, sys

LAYOUTS = ("full", "half", "inset", "small", "none")
SIZE = {"full": "head and shoulders, centred", "half": "full-height panel, 40% width, presenter side", "inset": "window 28% width, corner", "small": "window 20% width, corner", "none": "screen only"}

READ = r"\b(code|terminal|output|result|results|returns?|response|diagram|illustration|config|configuration|snippet|function|command|query|vector|json|table|screenshot|logs?|error)\b"
WALK = r"\b(click|open|run|type|scroll|go to|navigate|select|paste|install|let's (build|write|add)|we (add|write|create|set))\b"
TALK = r"\b(why|because|think|idea|means|matter|important|honestly|opinion|i (think|believe|like)|the point|in short|so what|recap|summary|to sum|that's it|thanks|subscribe|comment|next video|link)\b"
COMPARE = r"\b(versus|vs\.?|compared (to|with)|comparison|side by side)\b"
READ_HARD = r"\b(highlight|highlighted|readable|inspect|read|code|calls?|config|configuration|diagram|illustration|results?|output|ranked?|table)\b"
CODE = r"\b(code|calls?|snippet|config|configuration|function|command|terminal)\b"
LOOK_ONLY = r"\b(diagram|illustration|results?|table|ranked?)\b"
HOOK_RESULT = r"\b(look at this|here's what|watch this|this is what happens|the result)\b"

def mmss(s):
    m = re.match(r"(\d+):(\d\d)", s); return int(m[1]) * 60 + int(m[2]) if m else None

def parse(text):
    """sections -> passages. A passage is a run of spoken lines; directions in [**...**] attach to the passage before them."""
    sections = []; cur = None
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)              # notes and code-on-screen comments are never spoken
    for raw in text.splitlines():
        line = raw.rstrip()
        h = re.match(r"^##\s+(.*?)(?:\s{2,}|\s+)?(\d+:\d\d)?\s*(?:to|-|–)?\s*(\d+:\d\d)?\s*$", line)
        if line.startswith("## ") and h:
            cur = {"title": h[1].strip(), "start": mmss(h[2] or ""), "end": mmss(h[3] or ""), "passages": [], "raw": []}
            sections.append(cur); continue
        if line.startswith("# "): continue                         # the video's title
        if cur is None:
            if not line.strip(): continue
            cur = {"title": "Opening", "start": 0, "end": None, "passages": [], "raw": []}; sections.append(cur)
        cur["raw"].append(line)
    for s in sections:
        passages = []; buf = []; last_dir = [0]
        def flush():
            if buf: passages.append({"text": " ".join(buf).strip(), "camera": None, "show": None, "broll": False})
            buf.clear()
        for line in s["raw"]:
            if not line.strip():
                flush(); continue
            if line.startswith("[**") or re.match(r"^\[B-ROLL:", line):
                flush()
                cam = re.search(r"\*\*Camera:\*\*\s*(.*?)(?=\s*\*\*Show|\s*\*\*Transition|\]$)", line); sh = re.search(r"\*\*Show:\*\*\s*(.*?)(?=\s*\*\*Transition|\]$)", line)
                br = bool(re.search(r"B[ -]?roll", line, re.I))
                for q in passages[last_dir[0]:]:          # a direction covers every paragraph since the previous one
                    if cam: q["camera"] = cam[1].strip()
                    if sh: q["show"] = sh[1].strip()
                    if br: q["broll"] = True
                last_dir[0] = len(passages)
                continue
            if line.startswith("**") and line.endswith("**"): continue       # labels like **Verbal hook**
            if line.startswith("**Written hook:**"): continue
            buf.append(re.sub(r"\[B-ROLL:[^\]]*\]", "", line).strip())
        flush()
        s["passages"] = passages
    return sections

def words(t): return len(re.findall(r"[A-Za-z0-9']+", t))

def choose(p, idx, n_in_section, section_title, is_first):
    t = p["text"].lower(); cam = (p.get("camera") or "").lower(); show = (p.get("show") or "").lower()
    if p.get("broll"): return "none", "B-roll insert: the viewer looks at the asset"
    if is_first:
        if re.search(HOOK_RESULT, t): return "none", "hook lands on a result the viewer sees"
        return "full", "hook: the person asks the question"
    if re.search(COMPARE, t) and re.search(READ, t + " " + show): return "half", "comparison: person and content carry equal weight"
    if re.search(CODE, show + " " + t) and not re.search(LOOK_ONLY, show):
        return "small", "code on screen: house rule, small window top right so the person stays while they read"
    if re.search(READ_HARD, show): return "none", "the viewer must read what is on screen"
    if re.search(WALK, t): return "small", "walkthrough: presence while the viewer follows the cursor"
    if show and not re.search(TALK, t): return "small", "something is on screen but not dense: presence, small"
    if re.search(READ, t) and not re.search(TALK, t): return "none", "names code or a result: show it, hide the face"
    if re.search(TALK, t): return "full", "opinion, reason or summary: the person carries it"
    if re.search(READ, t): return "small", "talks about on-screen material: keep presence, keep the screen"
    return "full", "explanation with nothing to read: the person carries it"

def plan(sections, style="cut", corner="top-right"):
    rows = []; t = 0.0; first = True; wpm = 150.0
    for si, s in enumerate(sections):
        if s["start"] is not None: t = float(s["start"])
        dur_section = (s["end"] - s["start"]) if (s["start"] is not None and s["end"] is not None) else None
        total_words = sum(words(p["text"]) for p in s["passages"]) or 1
        for pi, p in enumerate(s["passages"]):
            w = words(p["text"]); hold = (dur_section * w / total_words) if dur_section else w / wpm * 60
            layout, why = choose(p, pi, len(s["passages"]), s["title"], first)
            rows.append({"t": t, "section": s["title"], "text": p["text"], "layout": layout, "why": why, "hold": hold, "script_camera": p.get("camera")})
            t += hold; first = False
    # closing: the corpus closes on the person (14 of 32) unless the last thing is a result worth looking at
    if rows and rows[-1]["layout"] != "full" and not re.search(READ_HARD, (rows[-1]["text"]).lower()):
        rows[-1]["layout"] = "full"; rows[-1]["why"] = "close on the person: the last line is the take-away"
    if style == "window":
        # window family: replace "full" inside sections with inset; keep full only for the opening and the close
        for i, r in enumerate(rows[1:-1], 1):
            if r["layout"] == "full": r["layout"] = "inset"; r["why"] += " (window style: stay in the inset)"
    # checks and repairs
    notes = []
    # 1. opening hold ~20 s: merge a change that would come inside the first 12 s
    if len(rows) > 1 and rows[1]["t"] < 12 and rows[1]["layout"] != rows[0]["layout"]:
        notes.append(f"opening: the first change came at {rows[1]['t']:.0f} s; held the opening layout ({rows[0]['layout']}) through it (corpus holds the opening ~20 s)")
        rows[1]["layout"] = rows[0]["layout"]
    # 2. face back within ~40 s; no face at all for more than ~50 s
    away = 0.0; noface = 0.0
    for r in rows:
        if r["layout"] == "full": away = 0.0
        else: away += r["hold"]
        if r["layout"] == "none": noface += r["hold"]
        else: noface = 0.0
        if noface > 50 and r["layout"] == "none":
            r["layout"] = "small"; r["why"] += " (no face for over 50 s: bring in a small window)"; noface = 0.0
        elif away > 40 and r["layout"] in ("small", "inset") and not re.search(READ, r["text"].lower()):
            r["layout"] = "full"; r["why"] += " (away from full for over 40 s: come back)"; away = 0.0
    # 3. merge same-layout neighbours for the table, count layouts
    total = sum(r["hold"] for r in rows)
    used = {k: sum(r["hold"] for r in rows if r["layout"] == k) for k in LAYOUTS}
    n_used = sum(1 for k in LAYOUTS if used[k] >= 0.05 * total)
    if total > 180 and n_used < 3:
        notes.append(f"variety: only {n_used} layouts carry 5%+ of a {total / 60:.0f} min video; the corpus median is 3. Candidates: turn one long 'small' walkthrough into 'inset', or one 'none' read into 'small'.")
    changes = sum(1 for a, b in zip(rows, rows[1:]) if a["layout"] != b["layout"])
    cpm = changes / (total / 60) if total else 0
    if cpm < 1.2: notes.append(f"pace: {cpm:.1f} changes a minute; the corpus median is 2.4 (cut style) or under 1 (window style). Fine for window style, slow for cut style.")
    if cpm > 5: notes.append(f"pace: {cpm:.1f} changes a minute is above everything in the corpus (max 6.1); merge some.")
    # 4. corner consistency and window size per section
    for r in rows:
        if r["layout"] in ("small", "inset"): r["pos"] = f"{SIZE[r['layout']]} ({corner})"
        else: r["pos"] = SIZE[r["layout"]]
    # 5. conflicts with the script's own camera directions
    conflicts = []
    for r in rows:
        sc = (r.get("script_camera") or "").lower()
        if not sc: continue
        hits = []                                   # the earliest keyword in the note is the layout it opens with
        for lay, pat in (("none", r"hide|hidden|no face|face off|screen only"), ("small", r"small"), ("inset", r"large|big|inset|picture"), ("half", r"split|half|beside|side by side"), ("full", r"medium|centred|centered|full|wide|close")):
            m = re.search(pat, sc)
            if m: hits.append((m.start(), lay))
        want = min(hits)[1] if hits else None
        if want and want != r["layout"]:
            conflicts.append(f"{round(r['t']) // 60}:{round(r['t']) % 60:02d} script says '{r['script_camera'][:60]}' ({want}); plan says {r['layout']} because {r['why']}")
    return rows, notes, conflicts, used, total, cpm, n_used

def render(rows, notes, conflicts, used, total, cpm, n_used, title):
    L = [f"# Camera plan: {title}", "", f"{total / 60:.1f} min, {cpm:.1f} changes a minute, {n_used} layouts carrying 5%+ of the time. Shares: " + ", ".join(f"{k} {100 * used[k] / total:.0f}%" for k in LAYOUTS if used[k]) + ".", ""]
    L += ["| time | section | says | layout | size and position | hold | why |", "|---|---|---|---|---|---|---|"]
    merged = []
    for r in rows:
        if merged and merged[-1]["layout"] == r["layout"] and merged[-1]["section"] == r["section"]:
            merged[-1]["hold"] += r["hold"]; continue
        merged.append(dict(r))
    for r in merged:
        L.append(f"| {round(r['t']) // 60}:{round(r['t']) % 60:02d} | {r['section'][:28]} | {r['text'][:70]}{'...' if len(r['text']) > 70 else ''} | **{r['layout']}** | {r['pos']} | {r['hold']:.0f} s | {r['why']} |")
    if notes: L += ["", "## Checks", ""] + [f"- {n}" for n in notes]
    else: L += ["", "## Checks", "", "- opening hold, return-to-face, no-face stretch, variety and pace are all inside the corpus habits"]
    if conflicts: L += ["", "## Where this differs from the script's own Camera notes", ""] + [f"- {c}" for c in conflicts]
    return "\n".join(L) + "\n"

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script"); ap.add_argument("--out"); ap.add_argument("--style", default="cut", choices=["cut", "window"]); ap.add_argument("--corner", default="top-right")
    ap.add_argument("--annotate", help="also write the script with a [**Camera:** ...] call under each passage where the camera changes")
    ap.add_argument("--json", help="also write the rows as json (for building previews)")
    a = ap.parse_args()
    text = open(a.script, encoding="utf-8").read()
    title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), a.script)
    sections = parse(text)
    if not any(s["passages"] for s in sections): raise SystemExit("no spoken passages found; is this a script?")
    result = plan(sections, a.style, a.corner); rows = result[0]
    out = render(*result, title)
    if a.out: open(a.out, "w", encoding="utf-8").write(out); print(f"-> {a.out}")
    else: print(out)
    if a.json:
        import json; json.dump(rows, open(a.json, "w", encoding="utf-8"), indent=1); print(f"-> {a.json}")
    if a.annotate:
        # write a [**Camera:** ...] call in the script's own form under each passage where the camera CHANGES
        lines = text.splitlines(); out_lines = []; ri = 0; buf = []; prev_layout = None
        def key(t): return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()[:40]
        rk = [key(r["text"]) for r in rows]
        def call(r):
            lay = r["layout"]; pos = ""
            if lay in ("small", "inset"):
                corner = a.corner.replace("-", " "); pos = f", {corner}, {'20' if lay == 'small' else '28'}% width"
            elif lay == "half": pos = ", right, 40%"
            why = r["why"].split(" (")[0]
            return f"[**Camera:** {lay.upper()}{pos}. **Why:** {why}.]"
        for line in lines + [""]:
            if line.strip() and not line.startswith(("[**", "## ", "# ", "**", "[B-ROLL")):
                buf.append(line); out_lines.append(line); continue
            if buf:
                k = key(" ".join(l.strip() for l in buf))
                for j in range(ri, len(rows)):
                    if rk[j] and (k.startswith(rk[j][:25]) or rk[j].startswith(k[:25])):
                        r = rows[j]; ri = j + 1
                        if r["layout"] != prev_layout:
                            out_lines.append(call(r)); prev_layout = r["layout"]
                        break
                buf = []
            out_lines.append(line)
        open(a.annotate, "w", encoding="utf-8").write("\n".join(out_lines)); print(f"-> {a.annotate}")

if __name__ == "__main__":
    main()
