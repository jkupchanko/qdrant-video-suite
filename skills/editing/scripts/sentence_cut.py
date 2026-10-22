#!/usr/bin/env python
"""sentence_cut.py: cut a raw take to a script by whole sentences, never mid-thought.

  python sentence_cut.py RAW.mp4 SCRIPT.md --words WORDS.json --gaze GAZE.json --out DIR [--mirror] [--bars 72]

John, 2026-10-21, on the first Get Started cut: "you stopped in the center of my talking and then kept it going",
"it doesn't matter if the script is one-to-one... it needs to make sense and be very similar to the script", and
"my eyes go to a bunch of different things". cut_takes.py matches words and splices pieces of takes together, which
left half sentences and false starts in. This cuts differently:

  1. the take's words (source times, from cut_takes' words.json) become sentences: a full stop or a pause over 0.9 s
  2. every script line is scored against every sentence, and against pairs of sentences said back to back: how many
     of the line's content words are said (spelling-tolerant), plus how alike the two read. Wording may differ.
  3. for each line, in script order, the candidates after the last chosen one: the latest that scores close to the
     best (the last good take), preferring one with the eyes on the lens (GAZE.json, run on the raw take)
  4. a sentence that covers two lines is used once; a line with no candidate is listed as NO TAKE FOUND
  5. each sentence is kept whole, from the silence before its first word to the silence after its last; only pauses
     over 1.2 s inside it are taken out, at silence

The output is cut.mp4 and cutlist.md in cut_takes' format (mirror, held push, bars, assemble.py), so the build goes on.
"""
import argparse, json, os, re, sys, difflib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from assemble import assemble

STOP = set("a an the and or but so to of in on at for with from by as is are was were be been it its this that these those we you i "
           "our your my they them their can will just going gonna actually really also then now let's lets here there what which "
           "do does did have has had not no yes if when while into out up about like get got".split())
ALIAS = {"quadrant": "qdrant", "quadrants": "qdrant", "hem": "helm", "kubernetes": "kubernetes", "api's": "api"}
norm_w = lambda w: ALIAS.get(re.sub(r"[^a-z0-9']", "", w.lower()), re.sub(r"[^a-z0-9']", "", w.lower()))

def sentences(words, gap=0.9):
    out, cur = [], []
    for k, w in enumerate(words):
        if cur and (w["s"] - cur[-1]["e"] > gap): out.append(cur); cur = []
        cur.append(w)
        if re.search(r"[.?!]$", w["w"]): out.append(cur); cur = []
    if cur: out.append(cur)
    return [dict(words=s, s=s[0]["s"], e=s[-1]["e"], text=" ".join(x["w"] for x in s)) for s in out if s]

def content(text): return [t for t in (norm_w(w) for w in text.split()) if t and t not in STOP]

def score(line, said):
    """how well a take says a line: the line's content words said (recall), the take's words belonging to the line
    (precision: a take that runs on into the next line loses), and how alike the two read"""
    a, b = content(line), content(said)
    if not a or not b: return 0.0
    same = lambda x, y: x == y or (len(x) > 3 and difflib.SequenceMatcher(None, x, y).ratio() > 0.8)
    recall = sum(1 for x in a if any(same(x, y) for y in b)) / len(a)
    precision = sum(1 for y in b if any(same(x, y) for x in a)) / len(b)
    ratio = difflib.SequenceMatcher(None, " ".join(a), " ".join(b)).ratio()
    return 0.55 * recall + 0.25 * precision + 0.2 * ratio

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("raw"); ap.add_argument("script"); ap.add_argument("--words", required=True); ap.add_argument("--gaze")
    ap.add_argument("--out", required=True); ap.add_argument("--mirror", action="store_true"); ap.add_argument("--bars", type=int, default=0)
    ap.add_argument("--push", type=float, default=1.04); ap.add_argument("--push-blocks", type=int, default=3); ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--min-score", type=float, default=0.38); ap.add_argument("--debug", action="append", default=[], help="print the top candidates of lines containing this text");
    ap.add_argument("--window", type=float, default=150.0, help="seconds after the last chosen take to look for the next line")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "..", "video-review", "scripts")); sys.path.insert(0, os.path.expanduser("~/.claude/skills/video-review/scripts"))
    import script_checks as SC, join_checks as JC
    lines = [l if isinstance(l, str) else l.get("text", "") for l in SC.parse(a.script)["lines"]]
    W = [w for w in json.load(open(a.words, encoding="utf-8")) if w.get("w")]
    S = sentences(W); env, quiet, loud = JC.envelope(a.raw)
    G = json.load(open(a.gaze)) if a.gaze else None
    gt = np.array([f["t"] for f in G["frames"]]) if G else None; goff = np.array([bool(f.get("off")) for f in G["frames"]]) if G else None
    def eyes(x0, x1, words=None):                          # over the words kept, not the pauses between phrases
        if G is None: return 1.0
        m = np.zeros(len(gt), bool)
        for w in (words or [dict(s=x0, e=x1)]): m |= (gt >= w["s"] - 0.1) & (gt <= w["e"] + 0.1)
        return float(1 - goff[m].mean()) if m.any() else 1.0
    # John records in short phrases with pauses, and restarts a phrase when he stumbles. A candidate is a run of phrases
    # (up to 6, pauses under 6 s) read as one attempt: a phrase that restarts an earlier one (same opening words, or the
    # same thing said again) replaces it and everything after it; a candidate must finish its thought (a full stop, or
    # the line's last content words said), so a half sentence is never taken.
    def opening(u): return [norm_w(w["w"]) for w in u["words"]][:3]
    def stutter_free(words):                              # "give it a name, give it a name, give it a recognizable name"
        ws = list(words); changed = True
        while changed:
            changed = False; n = [norm_w(w["w"]) for w in ws]
            for i in range(len(ws)):
                for j in range(i + 2, min(len(ws), i + 12)):
                    if n[i:i + 3] == n[j:j + 3] and len(n[i:i + 3]) == 3: ws = ws[:i] + ws[j:]; changed = True; break
                if changed: break
                for k in (2, 3, 4):                           # the same few words again, reordered ("load data samples, load sample data")
                    a_, b_ = n[i:i + k], n[i + k:i + 2 * k]
                    if len(b_) == k and a_[0] == b_[0] and len(set(map(lambda w: w.rstrip("s"), a_)) & set(map(lambda w: w.rstrip("s"), b_))) >= k - 0 * 1 and k >= 2:
                        ws = ws[:i] + ws[i + k:]; changed = True; break
                if changed: break
        return ws
    def restarts(u, kept):                                # "storage, / storage and any other", "load data samples, / load sample data"
        stem = lambda w: re.sub(r"s$", "", norm_w(w))                 # dataset / datasets
        un = [stem(w["w"]) for w in u["words"]]
        for j in range(len(kept) - 1, -1, -1):                   # the latest phrase it restarts, one phrase at a time
            k = kept[j]
            kn = [stem(w["w"]) for w in k["words"]]
            if un[:1] == kn[:1] and len(un) <= 5 and len(kn) <= 5 and score(u["text"], k["text"]) > 0.3: return j
            if (un[:3] == kn[:3]) or (len(un) > 1 and len(kn) > 1 and un[:2] == kn[:2]) or (kn and un[:len(kn)] == kn) or                (len(kn) <= 2 and kn[:1] == un[:1]) or score(u["text"], k["text"]) > 0.7: return j   # "The logs page helps us inspect" /
                                                                                                    # "The backups page helps us create" is not a restart
        return None
    def has_head(line, words):                           # the take begins where the line begins ("You can also visit...")
        head = [norm_w(w) for w in line.split()][:3]; said = "".join(norm_w(w["w"]) for w in words[:10])   # "WebUI" says "Web UI"
        return sum(1 for h in head if h and h in said) >= min(2, len(head))
    def complete(line, words):                           # the line's last content words are said (a full stop alone is not enough:
        tail = content(line)[-2:]; said = [norm_w(w["w"]) for w in words]
        return bool(tail) and any(any(t == x or difflib.SequenceMatcher(None, t, x).ratio() > 0.8 for x in said[-8:]) for t in tail)
    cands = []
    for i in range(len(S)):
        kept = []; mine = []                                   # this start's candidates, with how many phrases each kept
        for n in range(8):
            if i + n >= len(S): break
            u = S[i + n]
            if kept and (u["s"] - kept[-1]["e"] > 15.0 or u["e"] - kept[0]["s"] > 75): break
            j = restarts(u, kept) if kept else None
            if j:                                                 # a restart inside the attempt: the part it replaces is abandoned, so the
                for c_, k_ in mine:                               # candidates that ended inside it are dropped
                    if k_ > j and c_ in cands: cands.remove(c_)
            if j == 0: break                                   # a restart of the very first phrase: that is the next attempt
            kept = (kept[:j] if j is not None else kept) + [u]
            words = stutter_free([w for k in kept for w in k["words"]])
            c_ = (i, i + n, dict(s=words[0]["s"], e=words[-1]["e"], text=" ".join(w["w"] for w in words), words=words)); cands.append(c_); mine.append((c_, len(kept)))
    # the whole video at once: each line gets one take (or none), the takes in the order they were said and never
    # overlapping, so that the total of (match + how it starts and ends + eyes) is as high as it can be, less a cost for
    # every line left out. One take that swallows several lines loses to a take for each, since it scores against one.
    import bisect
    SKIP = 0.30
    def value(line, c):
        raw = score(line, c["text"])
        if raw < a.min_score: return None
        e = eyes(c["s"], c["e"], c["words"])
        first = "".join(norm_w(w["w"]) for w in c["words"][:3]); head3 = [norm_w(w) for w in line.split()][:3]
        starts_on_head = sum(1 for h in head3 if h and h in first) >= min(2, len(head3))   # not "responsible. / This gives you..."
        return (raw + (0.08 if complete(line, c["words"]) else -0.2) + (0.05 if has_head(line, c["words"]) else -0.25)
                + (0.04 if starts_on_head else 0.0) + (0.04 if re.search(r"[.?!]$", c["words"][-1]["w"]) else 0.0)
                + (0.03 if c["words"][0]["w"][:1].isupper() else 0.0)        # a take that starts a sentence ("You can also...", not "can also...")
                + (0.02 if e >= 0.8 else -0.03) + 1e-5 * c["s"])             # eyes only break ties (reading is fine); a later take wins a tie
    C = [c for _, _, c in cands]; starts = np.array([c["s"] for c in C])
    for dbg in a.debug:
        for line in [l for l in lines if dbg.lower() in l.lower()]:
            top = sorted(((value(line, c), score(line, c["text"]), c) for c in C if value(line, c) is not None), key=lambda x: -x[0])[:6]
            print(f"DEBUG {line[:60]}"); [print(f"   {v:.2f} raw {r:.2f} @{c['s']:.1f}-{c['e']:.1f} {c['text'][:90]}") for v, r, c in top]
    if a.debug: return
    entries = [(0.0, 0.0, -1, -1)]            # (end time, dp + SKIP * line, line, candidate): the start, before any line
    back = {}
    for li, line in enumerate(lines):
        ends = sorted(entries); ev = [x[0] for x in ends]; pm, best_i = [], -1
        for k, x in enumerate(ends):
            if best_i < 0 or x[1] > ends[best_i][1]: best_i = k
            pm.append(best_i)
        new_entries = []
        for ci, c in enumerate(C):
            v = value(line, c)
            if v is None: continue
            k = bisect.bisect_right(ev, c["s"] + 0.01) - 1
            if k < 0: continue
            prev = ends[pm[k]]; tot = prev[1] - SKIP * (li - 1) + v       # prev[1] holds dp + SKIP*line of the line before
            new_entries.append((c["e"], tot + SKIP * li, li, ci)); back[(li, ci)] = (prev[2], prev[3])
        entries += new_entries
    end_best = max(entries, key=lambda x: x[1] - SKIP * (len(lines) - 1 - x[2]))
    pick, cur = {}, (end_best[2], end_best[3])
    while cur[0] >= 0: pick[cur[0]] = cur[1]; cur = back[cur]
    chosen = []
    for li, line in enumerate(lines):
        if li in pick:
            c = C[pick[li]]; sc = score(line, c["text"]); e = eyes(c["s"], c["e"], c["words"])
            chosen.append((line, c, f"take at {c['s']:.1f}s, match {sc:.2f}, eyes on lens {int(e * 100)}%" + ("" if e >= 0.8 else "  <- CHECK")))
        else:
            prev = next((x for x in reversed(chosen) if x[1]), None)
            chosen.append((line, None, "said with the line before" if prev and score(line, prev[1]["text"]) >= a.min_score * 0.8 else "NO TAKE FOUND: not said on the recording, or said too differently"))
    # whole sentences: from the silence before the first word to the silence after the last; long pauses inside come out
    def q_before(x):
        i = int(round(x * 100)); return next((k / 100 for k in range(i, max(0, i - 40), -1) if env[k] < quiet), x - 0.08)
    def q_after(x):
        i = int(round(x * 100)); return next(((k + 2) / 100 for k in range(i, min(len(env) - 2, i + 60)) if env[k] < quiet and env[k + 1] < quiet), x + 0.15)
    pieces = []                                                                       # (x0, x1, line, said, note)
    for line, c, note in chosen:
        if not c: pieces.append((None, None, line, "", note)); continue
        ws = c["words"]; seg = [ws[0]]; first = True
        for w in ws[1:]:
            if w["s"] - seg[-1]["e"] > 0.6:
                pieces.append((q_before(seg[0]["s"]), q_after(seg[-1]["e"]), line if first else "(same line, after a pause)", " ".join(x["w"] for x in seg), note if first else "pause inside the take removed")); first = False; seg = []
            seg.append(w)
        pieces.append((q_before(seg[0]["s"]), q_after(seg[-1]["e"]), line if first else "(same line, after a pause)", " ".join(x["w"] for x in seg), note if first else "pause inside the take removed"))
    real = [p for p in pieces if p[0] is not None]
    for k in range(len(real) - 1):                                                     # never overlap the next piece in the source
        if real[k + 1][0] < real[k][1] and real[k + 1][0] > real[k][0]: real[k] = (real[k][0], real[k + 1][0], *real[k][2:])
    durs = [p[1] - p[0] for p in real]; starts = np.cumsum([0.0] + durs[:-1]); total = sum(durs)
    flips = sorted({int(np.argmin(np.abs(starts - total * jx / a.push_blocks))) for jx in range(1, a.push_blocks)}) if a.push_blocks > 1 else []
    push = [a.push if sum(1 for f in flips if f <= k) % 2 == 1 else 1.0 for k in range(len(real))]
    import cv2
    W_, H_ = (int(v) for v in a.size.split("x")); cap = cv2.VideoCapture(a.raw); sw, sh = int(cap.get(3)), int(cap.get(4)); cap.release()
    def vf(k):
        cw, ch = int(sw / push[k]), int(sh / push[k]); cx, cy = (sw - cw) // 2, (sh - ch) // 2
        return ("hflip," if a.mirror else "") + f"crop={cw}:{ch}:{cx}:{cy},scale={W_}:{H_}:flags=lanczos" + \
               (f",drawbox=x=0:y=0:w={W_}:h={a.bars}:color=black:t=fill,drawbox=x=0:y={H_ - a.bars}:w={W_}:h={a.bars}:color=black:t=fill" if a.bars else "")
    times = assemble(a.raw, [(p[0], p[1]) for p in real], os.path.join(a.out, "cut.mp4"), vf_for=vf)
    rows, k = [], 0
    for p in pieces:
        if p[0] is None: rows.append(f"|  |  |  | {p[2]} |  | {p[4]} |"); continue
        rows.append(f"| {times[k]:.2f} | {p[0]:.2f}-{p[1]:.2f} | x{push[k]:.2f} | {p[2]} | {p[3]} | {p[4]} |"); k += 1
    end = times[-1] + durs[-1]
    with open(os.path.join(a.out, "cutlist.md"), "w", encoding="utf-8") as fh:
        fh.write(f"# Cut list: {os.path.basename(a.raw)} (whole sentences)\n\n| edit time | source | push | script line | said | take and eyes |\n|---|---|---|---|---|---|\n" + "\n".join(rows) +
                 f"\n\nTotal {end:.1f} s, {len(real)} cuts. " + ("Mirrored. " if a.mirror else "") + (f"Bars {a.bars} px top and bottom. " if a.bars else "") +
                 f"Push x{a.push:.2f} held in stretch 2 of {a.push_blocks}, changing at {len(flips)} cuts. Whole sentences; 20 ms audio fades at every join.\n")
    json.dump(W, open(os.path.join(a.out, "words.json"), "w"))
    missing = sum(1 for p in pieces if p[0] is None and p[4].startswith("NO TAKE")); covered = sum(1 for p in pieces if p[0] is None and not p[4].startswith("NO TAKE"))
    print(f"{len(lines)} lines: {len(lines) - missing - covered} cut, {covered} said with the line before, {missing} not found; {len(real)} pieces, {end:.1f} s -> {a.out}")

if __name__ == "__main__":
    main()
