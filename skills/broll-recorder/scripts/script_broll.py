#!/usr/bin/env python
"""script_broll.py: read a video script, find every B-roll marker, record each one, and list what goes where.

Marker forms the parser understands (case-insensitive, anywhere in the text):

  [B-ROLL: https://qdrant.tech/documentation/concepts/indexing/]
  [B-ROLL: https://qdrant.tech/documentation/concepts/indexing/ | create the payload index before you upload]
  [B-ROLL: https://qdrant.tech/pricing/ | there is a free tier | 5s | hover]
  [BROLL https://qdrant.tech/]      (B-ROLL, BROLL, B ROLL, CUTAWAY, SCREEN all work; colon optional)
  {{b-roll: URL | line}}            (curly form, for docs/templates)
  **B-roll:** URL                   (markdown bold label, line = the sentence before it)
  <!-- b-roll: URL | line -->       (HTML comment, invisible in the rendered script)

Fields after the URL, in any order, separated by |:  a spoken line (text), a duration ("5s" or "5"), a style
(reveal / hover / highlight / readthrough), a section ("section: Free Tier"), a name ("name: free_tier").
If no spoken line is given, the sentence just before the marker is used, so a bare [B-ROLL: URL] after a line
of narration already knows what it is illustrating.

usage: python script_broll.py SCRIPT.md --out DIR [--default-duration 6] [--dry-run] [--compose fullscreen]
Writes one clip per marker plus DIR/shotlist.md and DIR/shotlist.json (marker text, line, section matched, clip
path, caption suggestion, and where in the script it sits), and DIR/script.annotated.md with each marker
followed by the clip's file name.
"""
import argparse, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LABEL = r"(?:b[\s\-_]*roll|cutaway|screen(?:\s*cap(?:ture)?)?)"
PATTERNS = [
    re.compile(r"\[\s*" + LABEL + r"\s*:?\s*(?P<body>[^\]]+?)\s*\]", re.I),
    re.compile(r"\{\{\s*" + LABEL + r"\s*:?\s*(?P<body>[^}]+?)\s*\}\}", re.I),
    re.compile(r"<!--\s*" + LABEL + r"\s*:?\s*(?P<body>.+?)\s*-->", re.I | re.S),
    re.compile(r"\*\*\s*" + LABEL + r"\s*:?\s*\*\*\s*(?P<body>[^\n]+)", re.I),
    re.compile(r"(?m)^\s*" + LABEL + r"\s*:\s*(?P<body>https?://[^\n]+)$", re.I),
]
URL = re.compile(r"https?://[^\s|\]\}>\"']+")
STYLES = {"reveal", "hover", "highlight", "readthrough", "look", "arrive"}
ARRIVE_LEAD = 1.5   # the click-through plays this long before its line, then the marker's seconds hold the section (John, 2026-10-21)

def prev_sentence(text, pos):
    before = text[:pos]
    before = re.sub(r"\[[^\]]*\]|\{\{[^}]*\}\}|<!--.*?-->", " ", before, flags=re.S)
    parts = re.split(r"(?<=[.!?])\s+|\n{2,}", before.strip())
    parts = [p.strip() for p in parts if p.strip()]
    if not parts: return ""
    s = parts[-1]
    s = re.sub(r"^\s*(?:[A-Z][A-Za-z ]{0,20}:)\s*", "", s)          # drop a "JOHN:" speaker label
    s = re.sub(r"^[#>*\-\s]+", "", s)
    return s.strip()[-220:]

def parse(text, default_duration):
    jobs, seen = [], set()
    for pat in PATTERNS:
        for m in pat.finditer(text):
            if any(a <= m.start() < b for a, b in seen): continue
            seen.add((m.start(), m.end()))
            body = m.group("body").strip()
            u = URL.search(body)
            if not u: continue
            url = u.group(0).rstrip(".,;)")
            rest = [f.strip() for f in (body[:u.start()] + " " + body[u.end():]).split("|") if f.strip()]
            job = {"url": url, "match": "", "duration": default_duration, "style": None, "section": None, "name": None,
                   "marker": m.group(0).strip(), "pos": m.start(), "line_no": text.count("\n", 0, m.start()) + 1}
            for f in rest:
                fl = f.lower()
                if re.fullmatch(r"\d+(\.\d+)?\s*s?", fl): job["duration"] = float(re.sub(r"[^\d.]", "", fl))
                elif fl in STYLES: job["style"] = fl
                elif fl.startswith("section:"): job["section"] = f.split(":", 1)[1].strip()
                elif fl.startswith("name:"): job["name"] = re.sub(r"[^a-z0-9]+", "_", f.split(":", 1)[1].strip().lower()).strip("_")
                elif fl.startswith("style:"): job["style"] = f.split(":", 1)[1].strip().lower()
                else: job["match"] = f
            if not job["match"]: job["match"] = prev_sentence(text, m.start())
            if not job["style"]:
                job["style"] = "readthrough" if re.sub(r"https?://[^/]+", "", url).strip("/") == "" else "reveal"
            if not job["name"]:
                # name from the content words of the line (or the URL path), not the whole sentence
                stop = set("the a an and or of to in on for with is are be this that it its as at by from you your we our can will into over about what when how which there if rather not run anything yourself just much more".split())
                words = [w for w in re.findall(r"[a-z0-9]+", (job["match"] or "").lower()) if w not in stop and len(w) > 2][:4]
                if len(words) < 2:
                    words = [w for w in re.findall(r"[a-z0-9]+", re.sub(r"https?://[^/]+", "", url).lower()) if w not in ("documentation", "docs", "concepts", "articles", "blog")][-3:]
                job["name"] = "_".join(words) or "clip"
            jobs.append(job)
    jobs.sort(key=lambda j: j["pos"])
    # unique names
    used = {}
    for j in jobs:
        n = j["name"]; k = used.get(n, 0); used[n] = k + 1
        if k: j["name"] = f"{n}_{k + 1}"
    return jobs

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script"); ap.add_argument("--out", required=True); ap.add_argument("--default-duration", type=float, default=6)
    ap.add_argument("--dry-run", action="store_true", help="parse and print the shot list, record nothing")
    ap.add_argument("--compose", choices=["fullscreen", "fullscreen-pip", "evidence-card", "window"], help="also bake each clip in this style")
    ap.add_argument("--presenter", help="presenter video for --compose fullscreen-pip"); ap.add_argument("--light", action="store_true")
    ap.add_argument("--raw", action="store_true", help="record only; skip the house-style finishing (shot.py)")
    ap.add_argument("--style", choices=["reveal", "hover", "highlight", "readthrough", "look", "arrive"], help="one recording style for every marker (readthrough: opens on the section and reads down it)")
    ap.add_argument("--arrive-first", action="store_true", help="the first marker of each page arrives on it (page top, the article clicked in the docs menu, the title, the section clicked in On this page); the rest use --style")
    ap.add_argument("--zoom", type=float, help="CSS page zoom for every recording (1.4 = docs text readable on a phone)")
    ap.add_argument("--lead-in", type=float, default=ARRIVE_LEAD, help="seconds the click-through plays before its line (the style sheet's broll.lead_in_seconds)")
    a = ap.parse_args()
    text = open(a.script, encoding="utf-8").read()
    jobs = parse(text, a.default_duration)
    if not jobs:
        print("no B-roll markers found. Use e.g. [B-ROLL: https://site/page | what is being said]"); sys.exit(2)
    print(f"{len(jobs)} marker(s):")
    for i, j in enumerate(jobs, 1):
        print(f"  {i}. line {j['line_no']:4d}  {j['name']:28s} {j['duration']:>4}s {j['style']:11s} {j['url']}\n       says: {j['match'][:90]}")
    if a.dry_run: return
    os.makedirs(a.out, exist_ok=True)
    results = []
    seen_pages = set()
    for j in jobs:
        if a.style and not j["style"]: j["style"] = a.style                                     # a marker's own style wins over the default
        page_key = j["url"].split("#")[0].rstrip("/")
        if a.arrive_first and page_key not in seen_pages: j["style"] = "arrive"             # the viewer is shown where this page is, once
        if j["style"] == "arrive": j["duration"] = float(j["duration"]) + a.lead_in         # the click before the line, then the section on it
        seen_pages.add(page_key)
        cmd = [sys.executable, os.path.join(HERE, "broll.py"), "auto", j["url"], "--match", j["match"], "--duration", str(j["duration"]), "--style", j["style"], "--out", a.out, "--name", j["name"]]
        if j["section"]: cmd += ["--section", j["section"]]
        if a.light: cmd.append("--light")
        if a.zoom: cmd += ["--zoom", str(a.zoom)]
        if a.compose: cmd += ["--compose", a.compose] + (["--presenter", a.presenter] if a.presenter else [])
        elif not getattr(a, "raw", False):
            # house default: finish each clip as a suite shot (clean card, push in, swoop out)
            kind = {"highlight": "article", "readthrough": "site", "look": "look"}.get(j["style"], "docs")
            cmd = [sys.executable, os.path.join(HERE, "shot.py"), kind, j["url"], "--out", a.out, "--name", j["name"], "--duration", str(j["duration"])] + (["--says", j["match"]] if kind != "site" else []) + (["--section", j["section"]] if j["section"] and kind != "site" else [])   # keep the pin: it was dropped here before
        print(f"\n=== {j['name']}: {j['url']}")
        r = subprocess.run(cmd, capture_output=True, text=True)
        tail = "\n".join(l for l in (r.stdout + r.stderr).splitlines() if l.strip().startswith(("plan", "recorded", "review", "manifest", "composed", "->", "WARNING")) or "FAIL" in l)
        print(tail)
        mp = os.path.join(a.out, j["name"] + "_manifest.json")
        man = json.load(open(mp)) if os.path.exists(mp) else {"error": r.stderr[-400:]}
        results.append({**j, "manifest": man})
    # shot list
    lines = ["# B-roll shot list", "", f"Script: {os.path.abspath(a.script)}", ""]
    lines.append("| # | script line | says | page | section matched | clip | caption | note |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(results, 1):
        m = r["manifest"]
        if "error" in m:
            lines.append(f"| {i} | {r['line_no']} | {r['match'][:60]} | {r['url']} | FAILED | | | {m['error'][:80]} |"); continue
        sc = m.get("match_score", 0) or 0
        note = ("match weak, check the sheet or add section:" if sc < 0.35 and not r["section"] else ("matched on body text, worth a glance" if sc < 1.0 and not r["section"] else "")) + (" " + m["notes"] if m.get("notes") else "")
        lines.append(f"| {i} | {r['line_no']} | {r['match'][:60]} | {r['url']} | {m.get('section') or 'top of page'} | {os.path.basename(m['clip'])} ({m['duration']}s) | {m.get('caption_suggestion', '')[:60]} | {note.strip()} |")
    open(os.path.join(a.out, "shotlist.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    json.dump(results, open(os.path.join(a.out, "shotlist.json"), "w"), indent=1)
    # annotated script: each marker followed by the clip file name
    ann = text
    for r in sorted(results, key=lambda r: -r["pos"]):
        clip = os.path.basename(r["manifest"]["clip"]) if "clip" in r["manifest"] else "FAILED"
        ann = ann[:r["pos"] + len(r["marker"])] + f"  -> {clip}" + ann[r["pos"] + len(r["marker"]):]
    open(os.path.join(a.out, "script.annotated.md"), "w", encoding="utf-8").write(ann)
    print(f"\nshot list -> {os.path.join(a.out, 'shotlist.md')}")

if __name__ == "__main__":
    main()
