#!/usr/bin/env python
"""upload_kit.py: what YouTube asks for besides the video: the title, the description with its chapters, and the checks.

  python upload_kit.py SCRIPT.md CUTLIST.md --out DIR [--title "..."]   -> DIR/title.txt, description.txt, chapters.txt
  python upload_kit.py --check DIR                                       -> the checks again, after a person edits the files

The description is drafted from the script: the intro's own lines (what the video covers and what the viewer will have
at the end), the source page as a link in the first lines, the chapters (chapters.py), and every page the video shows,
from the script's markers and notes. The title starts as the script's own title (its # heading). Claude proposes title
options from the measured norms below and the person picks; the draft is a starting point, never the final word.

Checked against what the 49 audited videos do (references/research.md):
  title        20 to 70 characters (their middle 80% runs 28 to 67; YouTube refuses over 100: fix); no emoji (none of the
               49 has one); at most one word in capitals; the product named; and what the 19,463-title study found
               trailing on DevRel channels (titles.py): 70+ characters, a year, a part number, an event name, "live"
  description  a link in the first two lines (33 of 49); chapters valid for YouTube (the first at 0:00, three or more,
               10 s apart or more, in order: fix); no placeholder address (YOUR-CLUSTER...: fix); under 5,000 characters
"""
import argparse, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import chapters as CH
import titles as TI
PLACEHOLDER = re.compile(r"YOUR[-_]|EXAMPLE|<[^>]+>|localhost|127\.0\.0\.1", re.I)

def script_title(script):
    for ln in open(script, encoding="utf-8"):
        m = re.match(r"^#\s+(.+?)\s*$", ln)
        if m: return re.sub(r"\s+\d+:\d{2}.*$", "", m.group(1)).split(":")[0].strip()
    return ""

def links(script):
    """the source page first, then every other page the video shows, in the order the script uses them"""
    text = open(script, encoding="utf-8").read(); src = re.search(r"Source page:\s*(https?://\S+?)\s*-->", text)
    out = [src.group(1)] if src else []
    for u in re.findall(r"https?://[^\s|)>\]]+", text):
        u = u.rstrip(".,")
        if u not in out and not PLACEHOLDER.search(u): out.append(u)
    return out

def draft(script, cutlist, title=None):
    S = CH.sections(script); intro = S[0][1] if S else []
    me = lambda l: re.search(r"\bI(?:['’](?:ll|m))?\b", l)                     # "I'll show you" says nothing about the viewer
    rank = lambda l: next((k for k, pat in enumerate((r"\bby the end\b|\byou['’]ll (?:have|know|be able)", r"\byou can\b")) if re.search(pat, l, re.I)), None)
    lead = next((l for l in intro if not me(l)), "")                          # the hook's own opening, then what the viewer
    best = sorted([l for l in intro if l != lead and rank(l) is not None and not me(l)], key=rank)   # gets: "by the end" first,
    first = " ".join([x for x in (lead, best[0] if best else "") if x]).replace("’", "'")           # then "you can"
    L = links(script); C = CH.chapters(script, cutlist)
    D = [first, f"Docs: {L[0]}" if L else ""] + (["", "Chapters"] + [f"{CH.ts(t)} {name}" for name, t in C] if C else [])
    if len(L) > 1: D += ["", "Pages shown in this video"] + [f"- {u}" for u in L[1:]]
    return (title or script_title(script)), "\n".join(D).replace("\n\n\n", "\n\n").strip() + "\n", C

def check(title, description):
    F = []
    n = len(title)
    if n > 100: F.append(("fix", f"title is {n} characters; YouTube refuses over 100"))
    F += [f for f in TI.check(title) if not (n > 100 and "characters" in f[1])]    # the 19,463-title study (titles.py)
    if n < 20: F.append(("check", f"title is {n} characters; the 49 run 28 to 67: say what the viewer gets"))
    if re.search(r"[\U0001F300-\U0001FAFF☀-➿]", title): F.append(("check", "an emoji in the title; none of the 49 has one"))
    if sum(1 for w in title.split() if len(w) > 2 and w.isupper()) > 1: F.append(("check", "more than one word in capitals in the title"))
    if "qdrant" not in title.lower(): F.append(("check", "the title does not name Qdrant (or the tool the video is about)"))
    lines = description.splitlines(); first = " ".join(lines[:2])
    if not re.search(r"https?://", first): F.append(("check", "no link in the first two lines of the description (33 of the 49 put one there)"))
    ts = [(m.group(1), m.group(2)) for m in re.finditer(r"(?m)^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)$", description)]
    secs = [sum(int(x) * 60 ** k for k, x in enumerate(reversed(t.split(":")))) for t, _ in ts]
    if ts:
        if secs[0] != 0: F.append(("fix", "the first chapter is not at 0:00: YouTube will not show chapters"))
        if len(ts) < 3: F.append(("fix", "fewer than three chapters: YouTube will not show them"))
        bad = [ts[i + 1][0] for i in range(len(secs) - 1) if secs[i + 1] - secs[i] < 10]
        if bad: F.append(("fix", f"chapters under 10 s apart ({', '.join(bad)}): YouTube will not show them"))
        if secs != sorted(secs): F.append(("fix", "chapters out of order"))
    else: F.append(("check", "no chapters (41 of the 49 have them)"))
    for u in re.findall(r"https?://\S+", description):
        if PLACEHOLDER.search(u): F.append(("fix", f"a placeholder address in the description: {u}"))
    if len(description) > 5000: F.append(("fix", f"description is {len(description)} characters; YouTube's limit is 5,000"))
    return F

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", nargs="?"); ap.add_argument("cutlist", nargs="?"); ap.add_argument("--out"); ap.add_argument("--title"); ap.add_argument("--check", metavar="DIR")
    a = ap.parse_args()
    if a.check:
        T = open(os.path.join(a.check, "title.txt"), encoding="utf-8").read().strip(); D = open(os.path.join(a.check, "description.txt"), encoding="utf-8").read()
    else:
        if not (a.script and a.cutlist and a.out): ap.error("give SCRIPT CUTLIST --out DIR, or --check DIR")
        os.makedirs(a.out, exist_ok=True); T, D, C = draft(a.script, a.cutlist, a.title)
        open(os.path.join(a.out, "title.txt"), "w", encoding="utf-8").write(T + "\n"); open(os.path.join(a.out, "description.txt"), "w", encoding="utf-8").write(D)
        open(os.path.join(a.out, "chapters.txt"), "w", encoding="utf-8").write("".join(f"{CH.ts(t)} {n}\n" for n, t in C))
        print(f"TITLE: {T}\n\n{D}")
    F = check(T, D)
    for sev, msg in F: print(f"{sev:5s} {msg}")
    print(f"upload kit: {sum(1 for s, _ in F if s == 'fix')} to fix, {sum(1 for s, _ in F if s == 'check')} to check")
    return 1 if any(s == "fix" for s, _ in F) else 0

if __name__ == "__main__":
    sys.exit(main())
