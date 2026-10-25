#!/usr/bin/env python
"""setup.py: get this computer ready for the video suite in one step, then prove it works.

  python setup.py           set up (about 15 minutes the first time, mostly the Python packages)
  python setup.py --check   report what is missing, change nothing

Run it from the repo folder with Python 3.12 or newer, and again after every `git pull` (it copies the skills, so a pull
alone does not reach Claude). It does what the README's five manual steps did:
  1. a Python environment for the suite (.venv in this folder) with requirements.txt installed
  2. the skills copied into ~/.claude/skills, where Claude Code finds them
  3. the build pointed at this repo: ~/camera_audit/styles -> engine/, ~/camera_audit/assets -> engine/assets/
     (a link; a junction on Windows, which needs no admin), and the brand fonts in ~/camera_audit/fonts
  4. the B-roll recorder's browser check (skills/broll-recorder/scripts/setup.py)
  5. the review self-test on the demo clip, which must end SELF-TEST PASSED
Anything it cannot do (an old Python, no Chrome) is listed at the end in plain words, with what to install.
"""
import os, platform, shutil, subprocess, sys

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
    step(2, f"skills -> {SKILLS}")
    names = sorted(d for d in os.listdir(os.path.join(REPO, "skills")) if os.path.isdir(os.path.join(REPO, "skills", d)))
    if CHECK: missing = [n for n in names if not os.path.isdir(os.path.join(SKILLS, n))]; (todo if missing else done).append(f"skills not installed: {', '.join(missing)}" if missing else "skills installed")
    else:
        for n in names: shutil.copytree(os.path.join(REPO, "skills", n), os.path.join(SKILLS, n), dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
        done.append(f"{len(names)} skills copied"); print(f"  {len(names)} skills copied")
    step(3, f"the build pointed at this repo ({CA})")
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
    step(4, "the B-roll recorder's browser")
    r = run([VPY, os.path.join(REPO, "skills", "broll-recorder", "scripts", "setup.py")] + (["--check"] if CHECK else []), capture_output=True, text=True)
    print("  " + "\n  ".join((r.stdout or r.stderr).strip().splitlines()[-4:])); (done if r.returncode == 0 else todo).append("B-roll browser" if r.returncode == 0 else "B-roll browser: see step 4 above")
    step(5, "the review self-test on the demo clip")
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
    main()
