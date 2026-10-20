"""build.py: one request, the whole video. Raw take + three-layer script -> finished, mastered, reviewed video.

  python build.py --take RAW.mp4 --script SCRIPT.md --out BUILD_DIR [--url DOCS_URL] [--style list]
                  [--name "NAME" --role "TITLE"] [--no-mirror] [--bars 72] [--from STAGE] [--only STAGE] [--redo STAGE,...]

The script runs the video. Before the first stage the build checks it has what only a person can give (INTAKE below):
the presenter's name and title for the Qdrant name lower third come from the script's [**Lower third:** NAME | TITLE | 5 s];
without one, --name and --role add it (to a copy, BUILD_DIR/script.md, on the hook's second line; the script you gave is
never edited), and with neither the build stops and asks (exit 2).

Stages, each one a skill of the suite (outputs in BUILD_DIR/<stage>; a stage whose outputs exist is skipped unless --redo):
  cut      editing          the take cut to the script: last complete take per line, eyes on the lens, word-boundary cuts,
                            mirrored, Zoom tag covered, voice locked to the lips          -> cut/cut.mp4, cutlist.md, words.json
  words    (glue)           the cut's words at cut time, one piece per line                -> words.json
  gaze     editing/gaze     where the eyes are, frame by frame; the look-aways on the cut  -> gaze.json, lookaways.json
  camera   camera-layout    the camera plan from the script, checked against the corpus    -> camera_plan.md
  keyterms broll-recorder   which lines earn B-roll, by key term (checked against the script's markers) -> keyterms.md
  broll    broll-recorder   every [B-ROLL] marker recorded: readthrough, 1.4x page zoom, its section pinned -> broll/
  assets   broll-recorder   the docs page's figures and code, sharp, with its Best fit / Watch for lines -> page_assets/
  style    editing-style    the styled video (style 'list': the listed-sections style, built from all of the above)
  master   (editing-style)  loudness to about -14 LUFS, true peak -1.5 dBTP, picture untouched
  review   video-review     the audit: every problem with its time and frame               -> review/report.md
Writes BUILD_DIR/BUILD.md (what each stage did, how long it took, what the review found) and build.json.
"""
import os, sys, re, json, time, glob, argparse, subprocess, shutil
SK = os.path.expanduser("~/.claude/skills"); STYLES = r"C:\Users\ADMIN\camera_audit\styles"; PY = sys.executable
STAGES = ["cut", "words", "gaze", "camera", "keyterms", "broll", "assets", "style", "master", "review"]

def run(cmd, log, cwd=None):
    with open(log, "w", encoding="utf-8") as f:
        r = subprocess.run([str(c) for c in cmd], stdout=f, stderr=subprocess.STDOUT, cwd=cwd)
    tail = open(log, encoding="utf-8", errors="replace").read().splitlines()[-12:]
    if r.returncode != 0: raise RuntimeError(f"{os.path.basename(str(cmd[1]))} failed ({r.returncode}); last lines of {log}:\n  " + "\n  ".join(tail))
    return tail

INTAKE = """Before building, the video needs answers only the presenter has:
  1. Your name, as it should read on the name card (lower third)?
  2. Your title under it (e.g. Developer Relations Engineer)?
Give them with --name "..." --role "...", or put this line in the script after the line it should come in on:
  [**Lower third:** NAME | TITLE | 5 s]"""
LOWER = re.compile(r"\[\*\*Lower third:\*\*", re.I)

def with_lower_third(script, out_dir, name, role):
    """a copy of the script with the name card on the hook's second spoken line (or its first, if it has one line)"""
    L = open(script, encoding="utf-8").read().splitlines(); seen_head = False; spoken = []
    in_comment = False
    for k, ln in enumerate(L):
        s_ = ln.strip()
        if "<!--" in s_: in_comment = "-->" not in s_; continue
        if in_comment: in_comment = "-->" not in s_; continue
        if s_.startswith("## "):
            if seen_head: break
            seen_head = True; continue
        if seen_head and s_ and not s_.startswith(("[", "#", "|")): spoken.append(k)
    at = spoken[min(1, len(spoken) - 1)] if spoken else 0
    L[at + 1:at + 1] = ["", f"[**Lower third:** {name} | {role} | 5 s]", ""]
    out = os.path.join(out_dir, "script.md"); open(out, "w", encoding="utf-8").write("\n".join(L) + "\n"); return out

def page_url(script):
    t = open(script, encoding="utf-8").read()
    m = re.search(r"Source page:\s*(https?://\S+)", t) or re.search(r"\[B-ROLL:\s*(https?://[^\s|]+)", t)
    return m.group(1) if m else None

class Build:
    def __init__(self, a):
        self.a = a; self.d = os.path.abspath(a.out); os.makedirs(self.d, exist_ok=True); self.state_p = os.path.join(self.d, "build.json")
        self.state = json.load(open(self.state_p)) if os.path.exists(self.state_p) else {}
        self.url = a.url or page_url(a.script); self.p = lambda *x: os.path.join(self.d, *x)
    def save(self): json.dump(self.state, open(self.state_p, "w"), indent=1)
    def done(self, stage, outs): return all(os.path.exists(o) for o in outs) and stage not in self.a.redo
    # ---------------------------------------------------------------- stages
    def cut(self):
        outs = [self.p("cut", "cut.mp4"), self.p("cut", "cutlist.md"), self.p("cut", "words.json")]
        if self.done("cut", outs): return outs, "kept"
        cmd = [PY, os.path.join(SK, "editing", "scripts", "cut_takes.py"), self.a.take, self.a.script, "--out", self.p("cut"), "--bars", self.a.bars]
        if self.a.mirror: cmd.append("--mirror")
        run(cmd, self.p("cut.log")); return outs, "cut from the take"
    def words(self):
        out = self.p("words.json")
        if self.done("words", [out]): return [out], "kept"
        sys.path.insert(0, STYLES); import engine as E
        pr = E.Project(base=self.p("cut", "cut.mp4"), cutlist=self.p("cut", "cutlist.md"), lookaways=self._empty_look(), words=self.p("cut", "words.json"))
        pieces = [dict(i=i, t0=round(pr.L(i), 3), t1=round(pr.end(i), 3), line=pr.line(i), words=[[w, round(t, 3)] for w, t in pr.words_in(i)]) for i in range(len(pr.pieces))]
        json.dump(dict(pieces=pieces, dur=round(pr.dur, 3)), open(out, "w"), indent=0); return [out], f"{len(pieces)} pieces, {pr.dur:.1f} s"
    def _empty_look(self):
        p = self.p("lookaways_empty.json")
        if not os.path.exists(p): json.dump([], open(p, "w"))
        return p
    def gaze(self):
        outs = [self.p("gaze.json"), self.p("lookaways.json")]
        if self.done("gaze", outs): return outs, "kept"
        run([PY, os.path.join(SK, "editing", "scripts", "gaze.py"), self.p("cut", "cut.mp4"), "--out", outs[0], "--lookaways", outs[1]], self.p("gaze.log"))
        look = json.load(open(outs[1])); return outs, f"{len(look)} look-aways, {sum(x['edit_end'] - x['edit_start'] for x in look):.1f} s"
    def camera(self):
        out = self.p("camera_plan.md")
        if self.done("camera", [out]): return [out], "kept"
        tail = run([PY, os.path.join(SK, "camera-layout", "scripts", "camera_plan.py"), self.a.script, "--out", out], self.p("camera.log"))
        return [out], "planned; the script's own camera calls lead (the plan is the check)"
    def keyterms(self):
        out = self.p("keyterms.md")
        if self.done("keyterms", [out]): return [out], "kept"
        run([PY, os.path.join(SK, "broll-recorder", "scripts", "keyterms.py"), self.a.script, self.url, "--out", out], self.p("keyterms.log"))
        picks = re.findall(r"^\| B-ROLL \| [\d.]+ \| (.*?) \| .*? \| (.*?) \|", open(out, encoding="utf-8").read(), flags=re.M)        # (line, section)
        marks = {re.sub(r"\W", "", l.lower()): sec.strip() for l, sec in re.findall(r"\[B-ROLL:[^|]+\|([^|]+)\|\s*section:\s*([^|\]]+)", open(self.a.script, encoding="utf-8").read())}
        differ = [f'"{l[:40]}": rule says {sec}, script pins {marks[k]}' for l, sec in picks for k in [re.sub(r"\W", "", l.lower())] if k in marks and sec.strip()[:24] != marks[k][:24]]
        return [out], f"key-term rule picks {len(picks)} line(s); the script carries {len(marks)} marker(s)" + (f"; they differ on {len(differ)}: " + "; ".join(differ) if differ else "")
    def broll(self):
        outs = [self.p("broll", "shotlist.md")]
        if self.done("broll", outs): return outs, "kept"
        run([PY, os.path.join(SK, "broll-recorder", "scripts", "script_broll.py"), self.a.script, "--out", self.p("broll"), "--raw", "--style", "readthrough", "--zoom", "1.4"], self.p("broll.log"))
        return outs, f"{len(glob.glob(self.p('broll', '*_manifest.json')))} clips"
    def assets(self):
        out = self.p("page_assets", "assets.json")
        if self.done("assets", [out]): return [out], "kept"
        run([PY, os.path.join(SK, "broll-recorder", "scripts", "page_assets.py"), self.url, "--out", self.p("page_assets")], self.p("assets.log"))
        A = json.load(open(out, encoding="utf-8")); return [out], f"{len(A['sections'])} sections, {sum(len(s['figures']) for s in A['sections'])} figures"
    def style(self):
        out = self.p("video.mp4")
        if self.done("style", [out]): return [out], "kept"
        cfg = dict(cut=self.p("cut", "cut.mp4"), cutlist=self.p("cut", "cutlist.md"), raw_words=self.p("cut", "words.json"), words=self.p("words.json"),
                   lookaways=self.p("lookaways.json"), script=os.path.abspath(self.a.script), assets=self.p("page_assets", "assets.json"), broll=self.p("broll"), out=out)
        json.dump(cfg, open(self.p("style_config.json"), "w"), indent=1)
        tail = run([PY, os.path.join(STYLES, f"style_{self.a.style}.py"), self.p("style_config.json")], self.p("style.log"), cwd=STYLES)
        return [out], next((l.strip() for l in tail if l.startswith("->")), "rendered")
    def master(self):
        out = self.p("video_master.mp4")
        if self.done("master", [out]): return [out], "kept"
        tail = run([PY, os.path.join(STYLES, "master_audio.py"), self.p("video.mp4"), out], self.p("master.log")); return [out], tail[-1] if tail else ""
    def review(self):
        out = self.p("review", "report.md")
        if self.done("review", [out]): return [out], "kept"
        cmd = [PY, os.path.join(SK, "video-review", "scripts", "review.py"), self.p("video_master.mp4"), "--out", self.p("review"), "--cut", self.p("cut", "cut.mp4"),
               "--script", self.a.script, "--words", self.p("words.json"), "--gaze", self.p("gaze.json"), "--lookaways", self.p("lookaways.json"), "--broll", self.p("broll"), "--label", self.a.label or "build",
               "--cutlist", self.p("cut", "cutlist.md"), "--assets", self.p("page_assets", "assets.json"), "--take", self.a.take]
        try: run(cmd, self.p("review.log"))
        except RuntimeError as e:
            if "failed (1)" not in str(e): raise                                       # exit 1 = there is something to fix: that is a result, not an error
        R = json.load(open(self.p("review", "report.json"))); from collections import Counter; c = Counter(f["sev"] for f in R["findings"])
        return [out], f"{c['fix']} to fix, {c['check']} to check, {c['note']} notes"

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--take", required=True); ap.add_argument("--script", required=True); ap.add_argument("--out", required=True); ap.add_argument("--url")
    ap.add_argument("--style", default="list"); ap.add_argument("--no-mirror", dest="mirror", action="store_false"); ap.add_argument("--bars", default="72"); ap.add_argument("--label")
    ap.add_argument("--from", dest="start"); ap.add_argument("--only"); ap.add_argument("--redo", default="")
    ap.add_argument("--name", help="the presenter's name for the lower third, when the script has no [**Lower third:** ...]"); ap.add_argument("--role", help="the title under it")
    a = ap.parse_args(); a.redo = set(filter(None, a.redo.split(",")))
    if not LOWER.search(open(a.script, encoding="utf-8").read()):
        if not (a.name and a.role): print(INTAKE); return 2
        os.makedirs(a.out, exist_ok=True); a.script = with_lower_third(a.script, os.path.abspath(a.out), a.name, a.role)
        print(f"the script has no name card: added [**Lower third:** {a.name} | {a.role} | 5 s] in {a.script}")
    B = Build(a)
    if not B.url: sys.exit("no docs URL: give --url, or put 'Source page: URL' or a [B-ROLL: URL | ...] marker in the script")
    stages = [a.only] if a.only else STAGES[STAGES.index(a.start):] if a.start else STAGES
    print(f"building {a.out} from {a.take} + {a.script} ({B.url}), style '{a.style}': {', '.join(stages)}", flush=True)
    for st in stages:
        t0 = time.time(); print(f"[{st}] ...", flush=True)
        try: outs, note = getattr(B, st)(); ok = True
        except Exception as e: outs, note, ok = [], str(e), False
        B.state[st] = dict(ok=ok, seconds=round(time.time() - t0, 1), outputs=outs, note=note, at=time.strftime("%Y-%m-%d %H:%M")); B.save()
        print(f"[{st}] {'ok' if ok else 'FAILED'} in {time.time() - t0:.0f} s: {note}", flush=True)
        if not ok: break
    L = [f"# Build: {a.label or os.path.basename(a.out)}", "", f"Take `{a.take}`, script `{a.script}`, page {B.url}, style `{a.style}`.", "", "| stage | skill | result | time |", "|---|---|---|---|"]
    skill = dict(cut="editing", words="glue", gaze="editing (gaze)", camera="camera-layout", keyterms="broll-recorder", broll="broll-recorder", assets="broll-recorder", style="editing-style", master="editing-style", review="video-review")
    for st in STAGES:
        s = B.state.get(st)
        if s: L.append(f"| {st} | {skill[st]} | {'ok' if s['ok'] else 'FAILED'}: {s['note'][:160]} | {s['seconds']:.0f} s |")
    if os.path.exists(B.p("review", "report.md")): L += ["", f"Video: `{B.p('video_master.mp4')}`", f"Review: `{B.p('review', 'report.md')}` (frames in `review/frames`, sheet `review/sheet.jpg`)"]
    open(B.p("BUILD.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("->", B.p("BUILD.md"))
    return 0 if all(B.state.get(s, {}).get("ok") for s in stages) else 1

if __name__ == "__main__":
    sys.exit(main())
