#!/usr/bin/env python
"""setup.py: get this computer ready for the video suite in one step, then prove it works.

  python setup.py           set up (about 15 minutes the first time, mostly the Python packages)
  python setup.py --check   report what is missing, change nothing

Run it from the repo folder with Python 3.12 or newer. The skills are linked, not copied, so a `git pull` or an edit in
this folder reaches Claude at once; run it again after a pull only when requirements.txt changed. It does what the
README's manual steps did:
  1. a Python environment for the suite (.venv in this folder) with requirements.txt installed
  2. every library the build uses, loaded the way the build loads it: a file Windows' app-control policy blocks is
     named (or shown as worked around), not found an hour into a build
  3. the skills linked into ~/.claude/skills, where Claude Code finds them (a link per skill to this folder; copies an
     older setup made are moved to ~/.claude/skill-copies-replaced/, never deleted)
  4. the build pointed at this repo: ~/camera_audit/styles -> engine/, ~/camera_audit/assets -> engine/assets/
     (a link; a junction on Windows, which needs no admin), and the brand fonts in ~/camera_audit/fonts
  5. the B-roll recorder's browser check (skills/broll-recorder/scripts/setup.py)
  6. the review self-test on the demo clip, which must end SELF-TEST PASSED
Anything it cannot do (an old Python, no Chrome) is listed at the end in plain words, with what to install.
"""
import os, platform, shutil, subprocess, sys, time

REPO = os.path.dirname(os.path.abspath(__file__)); HOME = os.path.expanduser("~"); CHECK = "--check" in sys.argv
WIN = platform.system() == "Windows"
VENV = os.path.join(REPO, ".venv"); VPY = os.path.join(VENV, "Scripts" if WIN else "bin", "python.exe" if WIN else "python")
CA = os.path.join(HOME, "camera_audit"); SKILLS = os.path.join(HOME, ".claude", "skills")
done, todo = [], []

def step(n, what): print(f"\n[{n}/5] {what}", flush=True)
def run(cmd, **kw): return subprocess.run([str(c) for c in cmd], **kw)

def link(target, path):
    """path -> target: a junction on Windows (no admin), a symlink elsewhere. A real folder already there is left alone"""
    if os.path.islink(path) or (hasattr(os.path, "isjunction") and os.path.isjunction(path)):
        if os.path.realpath(path) == os.path.realpath(target): return "already linked"
        if CHECK: return f"links elsewhere ({os.path.realpath(path)})"
        try: os.unlink(path)
        except OSError: os.rmdir(path)                                             # a junction or a folder link on Windows
    elif os.path.exists(path):
        return f"a real folder is there: left alone (move it away and run again to link it to {target})"
    if CHECK: return "missing"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if WIN: run(["cmd", "/c", "mklink", "/J", path, target], capture_output=True)
    else: os.symlink(target, path)
    return "linked" if os.path.exists(path) else "could not link"


# Every library the build loads, loaded the way the suite loads it (with its workarounds), each in its own process, so a
# file Windows' app-control policy blocks is named here and not discovered an hour into a build. (2026-10-26: the policy
# started blocking av's and scikit-learn's k-means DLLs on a machine where the suite had worked two days before.)
SK_DIR = os.path.join(REPO, "skills")
PROBES = [   # (name, needed for, required, code)
    ("numpy", "everything", True, "import numpy"),
    ("OpenCV", "frames, faces, the review", True, "import cv2, os; assert os.path.exists(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')"),
    ("Pillow", "pictures and cards", True, "from PIL import ImageFont; ImageFont.truetype(r'%s', 20)" % os.path.join(SK_DIR, "brand-consistency", "assets", "fonts", "MonaSans-Regular.ttf")),
    ("ffmpeg", "every render", True, "import imageio_ffmpeg, subprocess; f = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-filters'], capture_output=True, text=True).stdout; "
                                     "missing = [x for x in ('subtitles', 'loudnorm', 'anlmdn', 'bandreject') if ' ' + x + ' ' not in f]; assert not missing, 'ffmpeg has no ' + ', '.join(missing)"),
    ("pyloudnorm", "loudness", True, "import pyloudnorm"),
    ("pyspellchecker", "spelling on screen and in captions", True, "from spellchecker import SpellChecker; SpellChecker()"),
    ("RapidOCR", "reading text on screen", True, "from rapidocr_onnxruntime import RapidOCR; RapidOCR()"),
    ("faster-whisper", "transcripts, captions", True, "import sys\ntry: import av\nexcept ImportError: sys.modules['av'] = type(sys)('av'); print('WORKAROUND av')\nfrom faster_whisper import WhisperModel"),
    ("scikit-learn", "where the eyes rest (gaze)", True, "import sys; sys.path.insert(0, r'%s'); import gaze\ntry: import sklearn.cluster._k_means_lloyd\nexcept ImportError: print('WORKAROUND _k_means_lloyd')\n"
                                                     "gaze._kmeans_loop_fallback(); from sklearn.mixture import GaussianMixture; import numpy as np; GaussianMixture(2, random_state=0).fit(np.random.default_rng(0).normal(size=(200, 2)))" % os.path.join(SK_DIR, "editing", "scripts")),
    ("MediaPipe", "the eyes and the face", True, "import mediapipe"),
    ("Playwright", "B-roll recording", True, "from playwright.sync_api import sync_playwright"),
    ("skia-python", "the styled render", True, "import skia"),
    ("Pygments", "code on screen", True, "import pygments"),
    ("rembg", "cutting the presenter out (optional)", False, "import rembg"),
    ("python-pptx, python-docx, openpyxl", "the brand tools for decks and documents (optional)", False, "import pptx, docx, openpyxl"),
]

def probe():
    """run under the suite's Python: one line per library, ok / worked around / blocked (and which file) / missing"""
    import re as _re
    for name, why, req, code in PROBES:
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=REPO)
        err = (r.stderr or "").strip().splitlines(); last = err[-1] if err else ""
        if r.returncode == 0:
            w = [l.split()[1] for l in r.stdout.splitlines() if l.startswith("WORKAROUND")]
            print(f"PROBE|ok|{name}|{why}|{req}|" + (f"worked around: Windows blocks {', '.join(w)}" if w else ""))
        elif "Application Control" in r.stderr or "blocked" in last:
            f = _re.search(r"while importing (\w+)", r.stderr); print(f"PROBE|blocked|{name}|{why}|{req}|Windows app-control policy blocks {f.group(1) if f else 'a file'} ({last[:120]})")
        elif "No module named" in last: print(f"PROBE|missing|{name}|{why}|{req}|{last}")
        else: print(f"PROBE|broken|{name}|{why}|{req}|{last[:160]}")

def main():
    print(f"video suite setup{' (check only)' if CHECK else ''}: {REPO}")
    step(1, "Python environment and packages")
    if sys.version_info < (3, 12): todo.append(f"Python 3.12 or newer (this is {platform.python_version()}): https://python.org/downloads"); return report()
    if not os.path.exists(VPY):
        if CHECK: todo.append("the Python environment (.venv): run python setup.py")
        else: run([sys.executable, "-m", "venv", VENV], check=True); print("  made .venv")
    if os.path.exists(VPY) and not CHECK:
        if run([VPY, "-m", "pip", "--version"], capture_output=True).returncode:      # an environment made without pip (uv, --without-pip)
            run([VPY, "-m", "ensurepip", "--upgrade"], capture_output=True)
        print("  installing requirements.txt (the first time takes several minutes)...", flush=True)
        r = run([VPY, "-m", "pip", "install", "--disable-pip-version-check", "-q", "-r", os.path.join(REPO, "requirements.txt")])
        (done if r.returncode == 0 else todo).append("Python packages" if r.returncode == 0 else "Python packages failed to install: see the pip messages above")
    if os.path.exists(VPY):
        step(2, "every library the build loads, loaded")
        r = run([VPY, os.path.abspath(__file__), "--probe"], capture_output=True, text=True, timeout=900)
        rows = [l.split("|", 5)[1:] for l in r.stdout.splitlines() if l.startswith("PROBE|")]
        for st, name, why, req, note in rows:
            print(f"  {'ok  ' if st == 'ok' else st:8s} {name}: {why}" + (f"  ({note})" if note else ""))
            if st != "ok" and req == "True": todo.append(f"{name} ({why}): {note or st}" + (": ask IT to allow this file, or tell Claude the message above" if st == "blocked" else ""))
        if not rows: todo.append("the library check did not run: " + (r.stderr or "").strip()[-200:])
        elif all(st == "ok" for st, _, _, req, _ in rows if req == "True"):
            done.append(f"{sum(1 for x in rows if x[0] == 'ok')} of {len(rows)} libraries load" + (f"; {sum(1 for x in rows if 'worked around' in x[4])} with a workaround" if any("worked around" in x[4] for x in rows) else ""))
    step(3, f"skills -> {SKILLS}")
    names = sorted(d for d in os.listdir(os.path.join(REPO, "skills")) if os.path.isdir(os.path.join(REPO, "skills", d)))
    moved, bad = [], []
    for n in names:
        path, target = os.path.join(SKILLS, n), os.path.join(REPO, "skills", n)
        is_link = os.path.islink(path) or (hasattr(os.path, "isjunction") and os.path.isjunction(path))
        if os.path.isdir(path) and not is_link and not CHECK:          # a copy from an older setup: kept aside, then linked
            keep = os.path.join(HOME, ".claude", "skill-copies-replaced", time.strftime("%Y-%m-%d_%H%M%S"), n)
            os.makedirs(os.path.dirname(keep), exist_ok=True); shutil.move(path, keep); moved.append(n)
        r = link(target, path)
        if r not in ("linked", "already linked"): bad.append(f"{n}: {r if not (os.path.isdir(path) and not is_link) else 'a copy, not a link (python setup.py links it)'}")
    if moved: print(f"  old copies of {len(moved)} skills moved to ~/.claude/skill-copies-replaced/ (delete them once you are happy)")
    (todo if bad else done).append(f"skills not linked: {'; '.join(bad)}" if bad else f"{len(names)} skills linked to this folder")
    print(f"  {len(names) - len(bad)} of {len(names)} skills linked to {os.path.join(REPO, 'skills')}")
    step(4, f"the build pointed at this repo ({CA})")
    for name, target in (("styles", os.path.join(REPO, "engine")), ("assets", os.path.join(REPO, "engine", "assets"))):
        r = link(target, os.path.join(CA, name)); print(f"  {name}: {r}"); (done if r in ("linked", "already linked") else todo).append(f"~/camera_audit/{name}: {r}")
    fonts = os.path.join(REPO, "skills", "brand-consistency", "assets", "fonts"); fdir = os.path.join(CA, "fonts")
    ttf = [f for f in os.listdir(fonts) if f.endswith(".ttf")]
    if not CHECK:
        os.makedirs(fdir, exist_ok=True)
        for f in ttf: shutil.copy2(os.path.join(fonts, f), fdir)
    have = [f for f in ttf if os.path.exists(os.path.join(fdir, f))]
    print(f"  fonts: {len(have)} of {len(ttf)}"); (done if len(have) == len(ttf) else todo).append(f"fonts in ~/camera_audit/fonts: {len(have)} of {len(ttf)}")
    if not os.path.exists(VPY): return report()
    step(5, "the B-roll recorder's browser")
    r = run([VPY, os.path.join(REPO, "skills", "broll-recorder", "scripts", "setup.py")] + (["--check"] if CHECK else []), capture_output=True, text=True)
    print("  " + "\n  ".join((r.stdout or r.stderr).strip().splitlines()[-4:])); (done if r.returncode == 0 else todo).append("B-roll browser" if r.returncode == 0 else "B-roll browser: see step 4 above")
    step(6, "the review self-test on the demo clip")
    clip = os.path.join(REPO, "demos", "bulk-uploads-first30", "face_only_720.mp4")
    out = os.path.join(REPO, ".selftest")
    r = run([VPY, os.path.join(REPO, "skills", "video-review", "scripts", "selftest.py")] + ([clip] if os.path.exists(clip) else []) + ["--out", out], capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or ["(no output)"])[-1]; print(f"  {last}")
    (done if "PASSED" in last else todo).append("self-test passed" if "PASSED" in last else f"self-test: {last} (details: {out})")
    if not (shutil.which("chrome") or shutil.which("google-chrome") or any(os.path.exists(p) for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe", "/Applications/Google Chrome.app"))):
        todo.append("Google Chrome, for B-roll recording: https://www.google.com/chrome")
    report()

def report():
    print("\n" + "-" * 60)
    for d in done: print(f"  ok    {d}")
    for t in todo: print(f"  TODO  {t}")
    if todo: print("\nNot ready yet: fix the TODO lines, then run python setup.py again."); sys.exit(1)
    print("\nReady. Open Claude Code and say: I want to make a video"); sys.exit(0)

if __name__ == "__main__":
    probe() if "--probe" in sys.argv else main()
