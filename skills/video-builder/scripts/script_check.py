#!/usr/bin/env python
"""script_check.py: the script, checked against its form before anything is built, so a mistake shows in seconds with its
line and its fix, not an hour into a build.

  python script_check.py SCRIPT.md        -> one line per finding; exit 1 if anything is to fix
  python script_check.py --selftest       -> every mistake below planted in a made-up script, each caught

The build runs it before its first stage and stops on a fix. Every check is a mistake that has cost a build (start-here's
references/script-form.md says how each one went wrong):

  fix    a B-roll marker in bold ([**B-ROLL: ...]): the recorder does not see it, so nothing is recorded (the chain test's
         demo script, 2026-10-26)
  fix    a B-roll marker without name:, so the clip never reaches the video (laptop test build, 2026-10-20)
  fix    a B-roll marker with fewer than two fields after the address, or an address that is not a web link
  fix    a B-roll marker under a later line than the one it quotes: the clip lands on the quoted line and the next card
         covers it (Bulk Uploads preview, 2026-10-21)
  fix    plain text before the first section: a note read as a spoken line, then reported missing from the cut
  fix    a <!-- or a [ never closed: everything after it stops being read
  fix    no docs page: no <!-- Source page: URL --> and no B-roll address
  fix    no name card ([**Lower third:** NAME | TITLE | 5 s]): the build stops and asks for one (--name/--role add it)
  check  a camera call without **Transition:**, a section heading without its planned times
"""
if __name__ == "__main__":                                   # run on the suite's own Python (.venv, made by setup.py), whichever python started it
    import os as _o, sys as _s, subprocess as _sp
    _v = _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), "..", "..", "..", ".venv", *(("Scripts", "python.exe") if _o.name == "nt" else ("bin", "python")))
    if _o.path.exists(_v) and _o.path.normcase(_o.path.realpath(_s.prefix)) != _o.path.normcase(_o.path.realpath(_o.path.dirname(_o.path.dirname(_v)))):
        _s.exit(_sp.call([_v, _o.path.realpath(__file__)] + _s.argv[1:]))
import argparse, difflib, re, sys

def norm(s): return re.sub(r"[^a-z0-9 ]", "", s.lower().replace("’", "'")).strip()

def check(path):
    L = open(path, encoding="utf-8").read().splitlines(); F = []
    add = lambda sev, n, msg: F.append((sev, n, msg))
    note, open_at, section, spoken = False, None, False, []                # spoken: (line number, text) since the last marker
    has_src, has_url, has_lower = False, False, False
    for n, raw in enumerate(L, 1):
        s = raw.strip()
        if note:
            if "-->" in s: note = False
            continue
        if s.startswith("<!--"):
            has_src |= bool(re.search(r"Source page:\s*https?://", s, re.I))
            if "-->" not in s: note, open_at = True, n
            continue
        if not s: continue
        if s.startswith("# ") and not s.startswith("##"): continue
        if s.startswith("##"):
            section = True; spoken = []
            if s.lower().lstrip("# ").strip() != "count" and not re.search(r"\d+:\d{2}\s+to\s+\d+:\d{2}", s):
                add("check", n, f'section "{s.lstrip("# ")}" has no planned times ("## Name   0:00 to 0:30"); fine, but the plan reads easier with them')
            continue
        if s.lower().lstrip("# ") == "count": section = False; continue
        if s.startswith("["):
            if not s.endswith("]"): add("fix", n, "a [ ... direction never closed on its line: close it with ] (everything after reads as spoken)"); continue
            if re.match(r"\[\*\*\s*B-ROLL", s, re.I):
                add("fix", n, "B-roll marker in bold: the recorder does not see [**B-ROLL: ...]. Write [B-ROLL: ...]"); s = re.sub(r"^\[\*\*\s*B-ROLL\s*:?\s*(?:\*\*)?\s*:?", "[B-ROLL:", s, flags=re.I)
            if re.match(r"\[B-ROLL", s, re.I):
                has_url |= bool(re.search(r"https?://", s))
                parts = [p.strip() for p in s.strip("[]").split(":", 1)[1].split("|")] if ":" in s else []
                url = parts[0] if parts else ""
                if not re.match(r"https?://", url): add("fix", n, f'B-roll marker: "{url[:50]}" is not a web address (https://...)')
                if len(parts) < 3: add("fix", n, "B-roll marker needs at least: URL | the spoken line | ... (section, length, name)")
                if not any(p.lower().startswith("name:") for p in parts): add("fix", n, "B-roll marker without name: the clip will never reach the video. Add | name: short_name")
                if len(parts) >= 2 and spoken:
                    quote = norm(parts[1]); score = [difflib.SequenceMatcher(None, quote, norm(t)).ratio() + (1 if quote and quote in norm(t) else 0) for _, t in spoken]
                    best = max(range(len(spoken)), key=lambda i: score[i])
                    if best != len(spoken) - 1 and score[best] > score[-1] + 0.15:
                        add("fix", n, f"B-roll marker quotes the line at {spoken[best][0]}, but sits under line {spoken[-1][0]}: move it directly under the line it quotes")
                spoken = []
            if re.match(r"\[\*\*Lower third:\*\*", s, re.I): has_lower = True
            if re.match(r"\[\*\*Camera:\*\*", s, re.I) and "transition" not in s.lower():
                add("check", n, "camera call without **Transition:** (every camera call names one)")
            continue
        if s.startswith(("|", ">", "---", "```")): continue
        if not section: add("fix", n, f'plain text before the first section is read as a spoken line: "{s[:60]}". Put a note in <!-- ... -->')
        else: spoken.append((n, s))
    if note: add("fix", open_at, "a <!-- comment never closed: everything after it is ignored. Close it with -->")
    if not (has_src or has_url): add("fix", 1, "no docs page: add <!-- Source page: https://... --> at the top, or a [B-ROLL: https://... | ...] marker")
    if not has_lower: add("fix", 1, "no name card: add [**Lower third:** NAME | TITLE | 5 s] after the first line (or build with --name and --role)")
    return sorted(F, key=lambda f: (f[0] != "fix", f[1]))

PLANTED = """Edited from the Zoom take, a note left as plain text.

# A test script

## Intro   0:00 to 0:20

First spoken line about collections.

[**Lower third:** Test Presenter | Engineer | 5 s]

Dense vectors use HNSW while sparse vectors use an inverted index.
Because they differ, memory use differs during uploads.

[B-ROLL: https://qdrant.tech/documentation/ | dense vectors use HNSW while sparse vectors use an inverted index | section: X | 5s | name: dense]

[**B-ROLL: https://qdrant.tech/documentation/ | because they differ | 5s]

## Upload

Upload in batches.

[B-ROLL: qdrant.tech/documentation | upload in batches | 5s | name: batches]
[B-ROLL: https://qdrant.tech/documentation/ | upload in batches]

[**Camera:** FULL, centred.]

<!-- an unclosed note
"""
WANT = [("plain text before", 1), ("under line", 14), ("in bold", 16), ("without name", 16), ("not a web address", 22),
        ("needs at least", 23), ("without name", 23), ("never closed", 27)]

def selftest():
    import os, tempfile
    p = os.path.join(tempfile.mkdtemp(), "planted.md"); open(p, "w", encoding="utf-8").write(PLANTED); F = check(p); ok = True
    for needle, n in WANT:
        hit = any(sev == "fix" and ln == n and needle in msg for sev, ln, msg in F); print(f"  {'caught' if hit else 'MISSED'}  line {n}: {needle}"); ok &= hit
    hit = any(sev == "check" and "Transition" in msg for sev, _, msg in F); print(f"  {'caught' if hit else 'MISSED'}  a camera call without a transition (check)"); ok &= hit
    hit = any("planned times" in msg for _, _, msg in F); print(f"  {'caught' if hit else 'MISSED'}  a section without planned times (check)"); ok &= hit
    extra = [f for f in F if f[0] == "fix" and not any(nd in f[2] and f[1] == n for nd, n in WANT)]
    for f in extra: print(f"  INVENTED  line {f[1]}: {f[2][:80]}")
    good = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "demos", "bulk-uploads-first30", "script-with-camera-and-transitions.md")
    G = [f for f in check(good) if f[0] == "fix"] if os.path.exists(good) else []
    for f in G: print(f"  INVENTED  the demo script, line {f[1]}: {f[2][:80]}")
    print("SELF-TEST PASSED" if ok and not extra and not G else "SELF-TEST FAILED"); return 0 if ok and not extra and not G else 1

def main():
    if "--selftest" in sys.argv: return selftest()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument("script"); a = ap.parse_args()
    F = check(a.script)
    for sev, n, msg in F: print(f"{sev:5s} line {n}: {msg}")
    nf = sum(1 for f in F if f[0] == "fix"); print(f"script check: {nf} to fix, {len(F) - nf} to check")
    return 1 if nf else 0

if __name__ == "__main__":
    sys.exit(main())
