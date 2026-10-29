#!/usr/bin/env python
"""keyterms.py: decide, line by line, whether a script line earns B-roll from a page, and which section.

  python keyterms.py SCRIPT.md URL [--out shotlist.md]

The rule: B-roll only when the line names something specific (a feature, a setting, a function, a term)
that the page has a section about. General talk ("this reduces RAM", "let's get started", "thanks for
watching") gets nothing; the person carries it. Generic words (memory, disk, vectors, uploads) never earn
B-roll on their own; a specific term (HNSW, quantization, payload index, batch, parallel, shards, on_disk,
an identifier) must appear, and the page must have a section about it. One insert per section: the first
line that names the thing gets it, later lines on the same thing hold (the card stays or the face is back). The decision is made from the line's key terms, not the
whole sentence: identifiers (on_disk, batch_size, upload_points), acronyms (HNSW, RAM), capitalised product
terms, and the page's own heading words. Each line is printed with its terms, the best section, the score
and the call (B-ROLL or none), and the B-ROLL lines are written as markers the recorder reads.
"""
if __name__ == "__main__":                                   # run on the suite's own Python (.venv, made by setup.py), whichever python started it
    import os as _o, sys as _s, subprocess as _sp
    _v = _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), "..", "..", "..", ".venv", *(("Scripts", "python.exe") if _o.name == "nt" else ("bin", "python")))
    if _o.path.exists(_v) and _o.path.normcase(_o.path.realpath(_s.prefix)) != _o.path.normcase(_o.path.realpath(_o.path.dirname(_o.path.dirname(_v)))):
        _s.exit(_sp.call([_v, _o.path.realpath(__file__)] + _s.argv[1:]))
import argparse, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GENERAL = re.compile(r"^(so|now|and|but|finally|thanks|welcome|let'?s|this|that|these|those|it|there)\b", re.I)
STOP = set("the a an of to and or for in on with is are be can you your we our it its this that these those as by at from into than then when while which what how not no more much very just also only some any all each every both few first second third final option options best practice practices".split())

def terms_in(line):
    t = set()
    for m in re.findall(r"\b[a-z]+(?:_[a-z0-9]+)+\b", line): t.add(m)                       # identifiers: on_disk, batch_size
    for m in re.findall(r"\b[A-Z]{2,}[A-Za-z0-9]*\b", line): t.add(m.lower())                 # acronyms: HNSW, RAM, IDF
    for m in re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b", line):                         # capitalised terms (not sentence starts)
        if line.strip().find(m) > 0: t.add(m.lower())
    for m in re.findall(r"\b(quantization|quantized|payload index(?:es)?|payload|shards?|sharding|parallel(?:ism|ize)?|batch(?:es|ing)?|workers?|index(?:es|ing)?|sparse|dense|vectors?|disk|memory|latency|throughput|upload(?:s|ing)?|collection|filter(?:s|ing)?|tenant|category)\b", line, re.I): t.add(m.lower())
    return {x for x in t if x not in STOP}

def sections(url):
    out = subprocess.run([sys.executable, os.path.join(HERE, "broll.py"), "inspect", url, "--out", os.path.join(HERE, "_kt_sections.json")], capture_output=True, text=True)
    p = os.path.join(HERE, "_kt_sections.json")
    if not os.path.exists(p): raise SystemExit("inspect failed: " + out.stderr[-400:])
    d = json.load(open(p, encoding="utf-8")); os.remove(p)
    return [s for s in d["sections"] if s.get("tag", "H2") in ("H1", "H2", "H3", "H4") and s["top"] > 150]

SPECIFIC = re.compile(r"\b(hnsw|quantiz\w*|payload index\w*|shards?|sharding|batch\w*|parallel\w*|workers?|on_disk|on disk|sparse index\w*|tenant|filter\w*|idf|upload_points|batch_size|shard_number)\b", re.I)

def specific_terms(line):
    return {m.lower() for m in SPECIFIC.findall(line)} | {m for m in re.findall(r"\b[a-z]+(?:_[a-z0-9]+)+\b", line)}

def score(sec, terms):
    head = set(re.findall(r"[a-z0-9_]+", sec["text"].lower())); body = set(re.findall(r"[a-z0-9_]+", (sec.get("body") or "").lower()))
    s = 0.0
    for t in terms:
        tw = set(re.findall(r"[a-z0-9_]+", t))
        if tw and tw <= head: s += 1.0
        elif tw and tw <= body: s += 0.4
        elif any(w in body for w in tw if len(w) > 3): s += 0.15
    return s

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script"); ap.add_argument("url"); ap.add_argument("--out"); ap.add_argument("--min-score", type=float, default=0.9)
    a = ap.parse_args()
    secs = sections(a.url)
    body = re.sub(r"<!--.*?-->", "", open(a.script, encoding="utf-8").read(), flags=re.S)   # notes are never spoken
    lines = [l.strip() for l in body.splitlines() if l.strip() and not l.strip().startswith(("#", "[", "**", "🎥", "🎙", "💻", "✅", "⚖", "```"))]
    rows = []; markers = []; used = set()
    secs = [x for x in secs if x.get("tag") != "H1"]          # the page title matches every general line; never a reason
    ORD = {"first": 1, "second": 2, "third": 3, "fourth": 4, "final": None, "last": None}
    def stem(w): return w[:6] if len(w) > 6 else w
    def words(t): return [stem(w) for w in re.findall(r"[a-z0-9_]+", t.lower())]
    for l in lines:
        if len(l.split()) < 4 or l.endswith(":") or l.isupper(): continue
        t = terms_in(l); sp = specific_terms(l)
        call, best, sc = "none", None, 0.0
        transition = bool(re.match(r"(now|so|let'?s|and now|but now|thanks|welcome)" + chr(92) + "b", l, re.I))
        consequence = bool(re.match(r"(this|these|only|too much|start with|larger|every|each|search may|compression|sparse searches)" + chr(92) + "b", l, re.I))
        if transition or consequence:
            # the person's line; if a section is already up it holds, otherwise the face
            prev = rows[-1][2] if rows and rows[-1][4] in ("B-ROLL", "hold") else ""
            rows.append((l, sorted(sp) if sp else sorted(t), prev, 0.0, "hold" if prev and sp else "none")); continue
        # ordinal: "the second option", "the final dense-vector option" -> the heading that starts with Option N
        m = re.search(r"\b(first|second|third|fourth|final|last)\b(?:[^.]{0,40}?)\boption\b", l, re.I)
        if m:
            n = ORD[m.group(1).lower()]; opts = [x for x in secs if re.match(r"Option\s*\d", x["text"])]
            if opts:
                pick = None
                if n: pick = next((x for x in opts if re.match(rf"Option\s*{n}\b", x["text"])), None)
                else:
                    pool = [x for x in opts if ("sparse" in x["text"].lower()) == ("sparse" in l.lower() and "dense" not in l.lower())]
                    pick = pool[-1] if pool else opts[-1]
                if pick: best, sc = pick, 9.0
        if best is None and sp:                                # only a line that names something specific can earn B-roll
            cands = []
            pool = secs
            if "dense" in l.lower() and "sparse" in l.lower(): pool = [x for x in secs if not re.match(r"Option" + chr(92) + "s*" + chr(92) + "d", x["text"])] or secs
            for x in pool:
                head = set(words(x["text"])); body = set(words(x.get("body") or ""))
                n_head = sum(1 for w in sp if set(words(w)) <= head); n_body = sum(1 for w in sp if set(words(w)) <= body)
                head_hit = any(stem(w) in head for w in t if len(w) > 3)
                if n_head or (n_body and head_hit) or n_body == len(sp) >= 1:
                    cands.append((2.0 * n_head + 1.0 * n_body + (3.0 if n_body + n_head >= len(sp) else 0) + score(x, t) * 0.5, x))
            if cands: sc, best = max(cands, key=lambda c: c[0])
        if best is not None:
            if best["text"] not in used: call = "B-ROLL"; used.add(best["text"])
            else: call = "hold"                                  # same section already on screen: no new insert
        rows.append((l, sorted(sp) if sp else sorted(t), best["text"] if best else "", round(sc, 2), call))
        if call == "B-ROLL": markers.append(f"[B-ROLL: {a.url} | {l} | section: {best['text']} | 5s]")
    w = max(len(r[0]) for r in rows) if rows else 40
    for l, t, s, sc, c in rows: print(f"{c:6s} {sc:4.1f}  {l[:70]:70s}  terms={','.join(t)[:40]:40s}  -> {s[:40]}")
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(f"# B-roll by key term: {os.path.basename(a.script)} against {a.url}\n\n| call | score | line | key terms | section |\n|---|---|---|---|---|\n")
            for l, t, s, sc, c in rows: fh.write(f"| {c} | {sc} | {l} | {', '.join(t)} | {s} |\n")
            fh.write("\n## Markers for the recorder\n\n" + "\n".join(markers) + "\n")
        print(f"-> {a.out}  ({sum(1 for r in rows if r[4] == 'B-ROLL')} B-ROLL of {len(rows)} lines)")

if __name__ == "__main__":
    main()
