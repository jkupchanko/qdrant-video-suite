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
  broll    broll-recorder   every [B-ROLL] marker recorded: the first of each page arrives on it (title, menu, a click into
                            the section), the rest read through their section and settle; 1.4x page zoom -> broll/
  assets   broll-recorder   the docs page's figures and code, sharp, with its Best fit / Watch for lines -> page_assets/
  style    editing-style    the styled video (style 'list': the listed-sections style, built from all of the above)
  master   (editing-style)  loudness to about -14 LUFS, true peak -1.5 dBTP, picture untouched
  review   video-review     the audit: every problem with its time and frame               -> review/report.md
Writes BUILD_DIR/BUILD.md (what each stage did, how long it took, what the review found) and build.json.
"""
import os, sys, re, json, time, glob, argparse, subprocess, shutil
SK = os.path.expanduser("~/.claude/skills"); STYLES = os.path.expanduser(r"~\camera_audit\styles"); PY = sys.executable
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

def preview_script(script, out_dir, secs):
    """a copy of the script cut to its first `secs` seconds: everything before the first section, then the sections that start
    before `secs` (by the heading's m:ss times, else by about 2.5 spoken words a second), so a short build shows the direction"""
    t = open(script, encoding="utf-8").read(); parts = re.split(r"(?m)^(?=## )", t); head, secs_ = parts[0], parts[1:]
    keep, words = [], 0
    for s in secs_:
        m = re.search(r"(\d+):(\d{2})\s+to\s+\d+:\d{2}", s.splitlines()[0])
        start = int(m.group(1)) * 60 + int(m.group(2)) if m else words / 2.5
        if keep and start >= secs: break
        keep.append(s); words += len(re.sub(r"(?s)<!--.*?-->|\[.*?\]|^#.*$", " ", s, flags=re.M).split())
    out = os.path.join(out_dir, "script_preview.md"); open(out, "w", encoding="utf-8").write(head + "".join(keep)); return out, len(keep)

def preview_from_cut(main, out, script):
    """a preview made from the approved cut, not a new one: its first pieces, up to the last line of the preview script,
    with the eye contact as measured on the whole cut. A short clip calibrates the lens differently (Bulk Uploads: the
    preview's own gaze pass found 4 targets instead of 3 and hid the face through the whole hook)"""
    import cv2, imageio_ffmpeg; FF = imageio_ffmpeg.get_ffmpeg_exe()
    sys.path.insert(0, os.path.join(SK, "video-review", "scripts")); import script_checks as SC
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
    want = {norm(l if isinstance(l, str) else l.get("text", "")) for l in SC.parse(script)["lines"]}
    L = open(os.path.join(main, "cut", "cutlist.md"), encoding="utf-8").read().splitlines()
    rows = [k for k, l in enumerate(L) if re.match(r"^\| [\d.]+ \| [\d.]+-[\d.]+ \|", l)]
    keep, ok = [], False
    for k in rows:
        line = L[k].strip("|").split("|")[3].strip()
        ok = ok if line.startswith("(same line") else norm(line) in want
        if not ok: break
        keep.append(k)
    c = cv2.VideoCapture(os.path.join(main, "cut", "cut.mp4")); fps = c.get(cv2.CAP_PROP_FPS) or 30; total = c.get(cv2.CAP_PROP_FRAME_COUNT) / fps; c.release()
    t_end = float(L[rows[len(keep)]].split("|")[1]) if len(keep) < len(rows) else total
    os.makedirs(os.path.join(out, "cut"), exist_ok=True)
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i", os.path.join(main, "cut", "cut.mp4"), "-frames:v", str(round(t_end * fps)), "-t", f"{t_end:.3f}",
                    "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", os.path.join(out, "cut", "cut.mp4")], check=True)
    head = L[:rows[0]]; open(os.path.join(out, "cut", "cutlist.md"), "w", encoding="utf-8").write("\n".join(head + [L[k] for k in keep] + ["", f"Total {t_end:.1f} s, {len(keep)} cuts: the first part of the approved cut in {main}."]) + "\n")
    shutil.copy(os.path.join(main, "cut", "words.json"), os.path.join(out, "cut", "words.json"))
    g = json.load(open(os.path.join(main, "gaze.json")))
    g["frames"] = [f for f in g["frames"] if f["t"] < t_end]; g["lookaways"] = [dict(w, end=min(w["end"], t_end)) for w in g["lookaways"] if w["start"] < t_end]
    json.dump(g, open(os.path.join(out, "gaze.json"), "w"), indent=0)
    lk = [dict(w, edit_end=min(w["edit_end"], t_end)) for w in json.load(open(os.path.join(main, "lookaways.json"))) if w["edit_start"] < t_end]
    json.dump(lk, open(os.path.join(out, "lookaways.json"), "w"), indent=1)
    return t_end, len(keep)

def page_url(script):
    t = open(script, encoding="utf-8").read()
    m = re.search(r"Source page:\s*(https?://\S+)", t) or re.search(r"\[B-ROLL:\s*(https?://[^\s|]+)", t)
    return m.group(1) if m else None

class Build:
    def __init__(self, a):
        self.a = a; self.d = os.path.abspath(a.out); os.makedirs(self.d, exist_ok=True); self.state_p = os.path.join(self.d, "build.json")
        self.state = json.load(open(self.state_p)) if os.path.exists(self.state_p) else {}
        self.url = a.url or page_url(a.script); self.p = lambda *x: os.path.join(self.d, *x)
        sp = os.path.join(STYLES, f"style_{a.style}.json")                              # the style sheet: the style sets the B-roll,
        self.sheet_path = sp if os.path.exists(sp) else None                             # camera, transitions and zoom
        self.sheet = json.load(open(sp, encoding="utf-8")) if self.sheet_path else {}
    def save(self): json.dump(self.state, open(self.state_p, "w"), indent=1)
    def done(self, stage, outs): return all(os.path.exists(o) for o in outs) and stage not in self.a.redo
    # ---------------------------------------------------------------- stages
    def cut(self):
        outs = [self.p("cut", "cut.mp4"), self.p("cut", "cutlist.md"), self.p("cut", "words.json")]
        if self.done("cut", outs): return outs, "kept"
        cmd = [PY, os.path.join(SK, "editing", "scripts", "cut_takes.py"), self.a.take, self.a.script, "--out", self.p("cut"), "--bars", self.a.bars]
        if self.a.mirror: cmd.append("--mirror")
        z = self.sheet.get("zoom", {})
        if z: cmd += ["--push", str(z.get("scale", 1.04)), "--push-blocks", str(z.get("stretches", 3))]
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
        b = self.sheet.get("broll", {})
        cmd = [PY, os.path.join(SK, "broll-recorder", "scripts", "script_broll.py"), self.a.script, "--out", self.p("broll"), "--raw",
               "--style", b.get("other_clips", "readthrough"), "--zoom", str(b.get("page_zoom", 1.4)), "--lead-in", str(b.get("lead_in_seconds", 1.5)),
               "--default-duration", str(b.get("default_seconds", 6))]
        if b.get("first_clip_of_a_page", "arrive") == "arrive": cmd.append("--arrive-first")
        run(cmd, self.p("broll.log"))
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
                   lookaways=self.p("lookaways.json"), script=os.path.abspath(self.a.script), assets=self.p("page_assets", "assets.json"), broll=self.p("broll"), out=out,
                   sheet=self.sheet_path)
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

def patch(B, a):
    """a small edit: re-render only [t0, t1] of a finished build with the script as it is now, splice it into video.mp4, master
    again, and cut the changed moment out to show (patch_T0-T1.mp4). Minutes, not the full render. The range grows to whole
    shots, so no transition is cut in half. The review is not re-run here: run --only review --redo review for the final check."""
    import cv2, imageio_ffmpeg; FF = imageio_ffmpeg.get_ffmpeg_exe(); fps = 30
    t0, t1 = a.patch; video = B.p("video.mp4")
    if not os.path.exists(video): sys.exit(f"--patch needs a finished build in {B.d} (no video.mp4)")
    shots = json.load(open(B.p("video_shots.json")))
    t0 = max([s["t0"] for s in shots if s["t0"] <= t0 + 1e-6] or [0.0]); t1 = min([s["t1"] for s in shots if s["t1"] >= t1 - 1e-6] or [shots[-1]["t1"]])
    print(f"patch: re-rendering {t0:.2f}-{t1:.2f} s (whole shots)", flush=True)
    cfg = json.load(open(B.p("style_config.json"))); cfg["script"] = os.path.abspath(a.script); json.dump(cfg, open(B.p("style_config.json"), "w"), indent=1)
    shots_p = B.p("video_shots.json"); shutil.copy(shots_p, shots_p + ".full")              # a range render writes its own shot list over it
    f0 = round(t0 * fps); lead = min(fps, f0); r0 = (f0 - lead) / fps                      # a second of the shot before: the transition
    run([PY, os.path.join(STYLES, f"style_{a.style}.py"), B.p("style_config.json"), f"{r0}", f"{t1}"], B.p("patch.log"), cwd=STYLES)   # into the first
    shutil.move(shots_p + ".full", shots_p)                                                  # shot needs its last frame; it is dropped below
    part = B.p(f"video_{int(r0)}-{int(t1)}.mp4"); c = cv2.VideoCapture(part); n = int(c.get(cv2.CAP_PROP_FRAME_COUNT)) - lead; c.release()
    c = cv2.VideoCapture(video); total = int(c.get(cv2.CAP_PROP_FRAME_COUNT)); c.release()
    f1 = min(total, f0 + n)
    segs = ([(0, f"trim=end_frame={f0}", f"atrim=end={f0 / fps:.4f}")] if f0 > 0 else []) + \
           [(1, f"trim=start_frame={lead}:end_frame={lead + f1 - f0}", f"atrim=start={lead / fps:.4f}:end={(lead + f1 - f0) / fps:.4f}")] + \
           ([(0, f"trim=start_frame={f1}", f"atrim=start={f1 / fps:.4f}")] if f1 < total else [])
    fc = "".join(f"[{s}:v]{vt},setpts=PTS-STARTPTS[v{k}];[{s}:a]{at},asetpts=PTS-STARTPTS[a{k}];" for k, (s, vt, at) in enumerate(segs))
    fc += "".join(f"[v{k}][a{k}]" for k in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=1[v][a]"
    tmp = B.p("video_patched.mp4")
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i", video, "-i", part, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp], check=True)
    c = cv2.VideoCapture(tmp); got = int(c.get(cv2.CAP_PROP_FRAME_COUNT)); c.release()
    if got != total: sys.exit(f"patch: the spliced video has {got} frames, the original {total}: kept the original, nothing changed")
    shutil.copy(video, B.p("video_before_patch.mp4")); os.replace(tmp, video)
    a.redo = {"master"}; outs, note = B.master()
    show = B.p(f"patch_{t0:.0f}-{t1:.0f}.mp4"); s0 = max(0.0, t0 - 1.0)
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{s0:.3f}", "-i", outs[0], "-t", f"{t1 + 1.0 - s0:.3f}", "-vf", "scale=1280:720",
                    "-c:v", "libx264", "-crf", "23", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", show], check=True)
    B.state["patch"] = dict(ok=True, range=[t0, t1], at=time.strftime("%Y-%m-%d %H:%M"), show=show)
    if "review" in B.state: B.state["review"]["stale"] = True
    B.save(); print(f"patched {t0:.2f}-{t1:.2f} s into {video}; mastered; the changed moment: {show}\nthe review is now out of date: --only review --redo review for the final check")
    return 0

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--take", required=True); ap.add_argument("--script", required=True); ap.add_argument("--out", required=True); ap.add_argument("--url")
    ap.add_argument("--style", default="list"); ap.add_argument("--no-mirror", dest="mirror", action="store_false"); ap.add_argument("--bars", default="72"); ap.add_argument("--label")
    ap.add_argument("--from", dest="start"); ap.add_argument("--only"); ap.add_argument("--redo", default="")
    ap.add_argument("--name", help="the presenter's name for the lower third, when the script has no [**Lower third:** ...]"); ap.add_argument("--role", help="the title under it")
    ap.add_argument("--cut-from", metavar="BUILD_DIR", help="with --preview: take the cut and its eye contact from this build's approved cut instead of cutting again")
    ap.add_argument("--take-is-edited", action="store_true", help="build from a take that is already cut (a test); normally refused, it gets cut twice")
    ap.add_argument("--patch", type=float, nargs=2, metavar=("T0", "T1"), help="a small edit to a finished build: re-render only T0-T1 s (grown to whole shots) with the script as it is now, splice it in and master; minutes, not hours")
    ap.add_argument("--preview", type=float, metavar="SECONDS", help="build only the sections that start in the first SECONDS (try 30): minutes instead of hours, to check the direction first")
    a = ap.parse_args(); a.redo = set(filter(None, a.redo.split(",")))
    if not LOWER.search(open(a.script, encoding="utf-8").read()):
        if not (a.name and a.role): print(INTAKE); return 2
        os.makedirs(a.out, exist_ok=True); a.script = with_lower_third(a.script, os.path.abspath(a.out), a.name, a.role)
        print(f"the script has no name card: added [**Lower third:** {a.name} | {a.role} | 5 s] in {a.script}")
    if not a.take_is_edited and not a.patch:                                            # a raw take with retakes runs well over its script;
        import cv2; sys.path.insert(0, os.path.join(SK, "video-review", "scripts")); import script_checks as SC   # an edit is about as long
        c = cv2.VideoCapture(a.take); take_s = c.get(cv2.CAP_PROP_FRAME_COUNT) / (c.get(cv2.CAP_PROP_FPS) or 30); c.release()
        said_s = sum(len((l if isinstance(l, str) else l.get("text", "")).split()) for l in SC.parse(a.script)["lines"]) / 2.6
        if said_s and take_s < 1.15 * said_s:
            print(f"the take is {take_s:.0f} s for about {said_s:.0f} s of script: it looks already edited, not raw. Cutting an edit again cuts it twice\n"
                  f"(clipped words at the old joins, the push applied twice, mirrored back). Give the raw, full recording, or --take-is-edited to go on anyway."); return 2
    if a.preview:
        os.makedirs(a.out, exist_ok=True); full = a.script; a.script, n = preview_script(full, os.path.abspath(a.out), a.preview)
        a.label = f"{a.label or os.path.basename(a.out)} (preview, first {a.preview:.0f} s)"
        print(f"preview: the first {n} section(s) of {full} -> {a.script}")
        if a.cut_from:
            t_end, n_cuts = preview_from_cut(os.path.abspath(a.cut_from), os.path.abspath(a.out), a.script)
            print(f"preview: the approved cut's first {t_end:.1f} s ({n_cuts} cuts) and its eye contact, from {a.cut_from}")
    B = Build(a)
    if not B.url: sys.exit("no docs URL: give --url, or put 'Source page: URL' or a [B-ROLL: URL | ...] marker in the script")
    if a.patch: return patch(B, a)
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
