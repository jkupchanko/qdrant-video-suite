#!/usr/bin/env python
"""fix_cut.py: look at one moment of a raw edit, or fix what the raw edit check found, without working out source times by hand.

  python fix_cut.py CUT_DIR RAW.mp4 --at 2:33              what is at 2:33: the pieces, the words, the pauses, the eyes, findings
  python fix_cut.py CUT_DIR RAW.mp4 --apply                fix every fix the raw edit check and the join check report
  python fix_cut.py CUT_DIR RAW.mp4 --apply --at 2:33      fix only what is within 6 s of 2:33
  python fix_cut.py CUT_DIR RAW.mp4 --notes review_notes.json   what a person marked on review.html (video-review's
                                                           review_page.py): fix the moments marked Fix, show each added one

A person says "at 2:33 it gets cut off and I look away". Before this, fixing that meant reading the cut list, the transcript
and the loudness to find a source time in a pause, then running respan.py. Now --at shows the moment, and --apply takes each
finding's own fix (video-review/raw_edit_checks.py: new source spans for the pieces it touches, every cut point in this
take's own quiet), applies the ones that do not touch the same piece, rebuilds the cut with respan.py, checks again, and
repeats (up to --rounds times) until nothing is left to fix. The cut before is kept as cut_before_respan.mp4.

The literal words and the eyes on the take are found next to the cut (CUT_DIR/words_literal.json, raw_gaze.json, as the
build writes them) or one or two folders up; mirror and bars come from CUT_DIR/cut_settings.json when the build wrote it.
"""
import argparse, json, os, re, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); RV = os.path.join(HERE, "..", "..", "video-review", "scripts"); sys.path.insert(0, RV)
import raw_edit_checks as RE, join_checks as JC

def find(cut_dir, name):
    for d in (cut_dir, os.path.join(cut_dir, ".."), os.path.join(cut_dir, "..", "..")):
        if os.path.exists(os.path.join(d, name)): return os.path.abspath(os.path.join(d, name))

def secs(t): return sum(float(x) * 60 ** k for k, x in enumerate(reversed(t.split(":"))))

def join_fixes(J, R):
    """the join check's fixes that name a pause to cut in at, as new spans"""
    out = []
    for j in J:
        m = re.search(r"pause to cut in at source ([\d.]+)", j["msg"])
        if j["sev"] == "fix" and m:
            k = min(range(len(R)), key=lambda k: abs(R[k][1] - j["src"]))
            out.append(dict(t=j["t"], kind="join", sev="fix", msg=j["msg"], edit={f"{R[k][0]:.2f}": [(float(m.group(1)), R[k][2])]}))
    return out

def show(at, R, W, G, S, F, env, quiet):
    ts = RE.ts; print(f"around {ts(at)} (edit time):")
    Z = None
    if G:
        fr = [f for f in G["frames"] if f.get("face")]; T = np.array([f["t"] for f in fr])
        Z = (T, np.sqrt(sum(((np.array([f[k] for f in fr]) - S[k][0]) / S[k][1]) ** 2 for k in ("h", "v"))))
    for t, a, b, line in R:
        if t + (b - a) < at - 6 or t > at + 6: continue
        words = []
        for w in W:
            if not RE.inside(w, a, b): continue
            eyes = ""
            if Z is not None:
                m = (Z[0] >= w["s"]) & (Z[0] <= w["e"] + 0.04)
                if m.any() and Z[1][m].max() > 3: eyes = "~"                      # eyes off their resting place over this word
            words.append(w["w"] + eyes)
        here = " <-" if t <= at <= t + (b - a) else ""
        print(f"  {ts(t)}  source {a:.2f}-{b:.2f}  {' '.join(words)}{here}")
        nxt = [r for r in R if r[0] > t][:1]
        if nxt:
            between = [w["w"] for w in W if b < w["s"] < nxt[0][1] and nxt[0][1] - b < 30]
            if between: print(f"           not in the cut, said before the next piece: {' '.join(between)[:110]}")
    near = [f for f in F if abs(f["t"] - at) <= 6]
    print("findings here: " + ("none" if not near else ""))
    for f in near: print(f"  {ts(f['t'])} {f['sev']} {f['kind']}: {f['msg'][:120]}")
    print("(~ = the eyes leave their resting place on that word)")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cut_dir"); ap.add_argument("raw"); ap.add_argument("--at", help="edit time, 2:33 or 153.2"); ap.add_argument("--apply", action="store_true")
    ap.add_argument("--notes", help="review_notes.json saved from review.html"); ap.add_argument("--near", type=float, default=6.0); ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--literal"); ap.add_argument("--gaze"); ap.add_argument("--mirror", action="store_true"); ap.add_argument("--bars", type=int)
    a = ap.parse_args()
    cl = os.path.join(a.cut_dir, "cutlist.md")
    lit = a.literal or find(a.cut_dir, "words_literal.json"); gz = a.gaze or find(a.cut_dir, "raw_gaze.json")
    if not lit: sys.exit("no words_literal.json next to the cut: run editing/scripts/transcribe_literal.py RAW --out CUT_DIR/words_literal.json")
    st = json.load(open(os.path.join(a.cut_dir, "cut_settings.json"))) if os.path.exists(os.path.join(a.cut_dir, "cut_settings.json")) else {}
    mirror = a.mirror or st.get("mirror", False); bars = a.bars if a.bars is not None else st.get("bars", 0)
    W = json.load(open(lit, encoding="utf-8")); G = json.load(open(gz, encoding="utf-8")) if gz else None
    E = JC.envelope(a.raw); at = secs(a.at) if a.at else None
    def check():
        R = JC.rows(cl); F, S = RE.checks(E, cl, W, G); return R, F + join_fixes(JC.joins(a.raw, cl), R), S
    R, F, S = check(); marked = None
    if a.notes:
        N = json.load(open(a.notes, encoding="utf-8"))["items"]
        marked = [i["t"] for i in N if i["decision"] == "fix"]
        for i in N:
            if i["decision"] == "look": print(f"\nyour moment at {RE.ts(i['t'])}: {i['note'] or '(no note)'}"); show(i["t"], R, W, G, S, F, E[0], E[1])
        a.apply = bool(marked)
        if not marked: print("\nnothing marked Fix"); return
    if not a.apply:
        if at is None: sys.exit("give --at TIME to look at a moment, or --apply to fix")
        show(at, R, W, G, S, F, E[0], E[1]); return
    done = 0
    for rnd in range(a.rounds):
        todo = [f for f in F if f.get("edit") and (f["sev"] == "fix" or marked) and (at is None or abs(f["t"] - at) <= a.near)
                and (marked is None or any(abs(f["t"] - m) < 1.0 for m in marked))]          # with notes: only what was marked Fix
        if not todo: break
        used, args = set(), []
        for f in todo:                                                             # one fix per piece a round; the rest next round
            if used & set(f["edit"]): continue
            used |= set(f["edit"]); print(f"  {RE.ts(f['t'])} {f['kind']}: {f['msg'][:90]}")
            for k, spans in f["edit"].items():
                args += ["--drop", k] if spans is None else ["--piece", f"{k}=" + ",".join(f"{x:.2f}-{y:.2f}" for x, y in spans)]
            done += 1
        cmd = [sys.executable, os.path.join(HERE, "respan.py"), a.cut_dir, a.raw, "--bars", str(bars)] + (["--mirror"] if mirror else []) + args
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode: sys.exit(f"respan.py failed: {r.stdout[-400:]}{r.stderr[-400:]}")
        R, F, S = check()
    left = [f for f in F if f["sev"] == "fix" and (at is None or abs(f["t"] - at) <= a.near)]
    print(f"fixed {done}; left to fix {len(left)}" + "".join(f"\n  {RE.ts(f['t'])} {f['kind']}: {f['msg'][:100]}" for f in left) + f"\n-> {os.path.join(a.cut_dir, 'cut.mp4')}")

if __name__ == "__main__":
    main()
