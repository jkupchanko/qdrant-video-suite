#!/usr/bin/env python
"""setup.py: get a fresh machine ready for the B-roll recorder, and say plainly what is missing.

usage: python setup.py            install what can be installed, then report
       python setup.py --check    report only, change nothing

Needs: Python 3.9+ (you are running it), a Chromium browser (Google Chrome or Microsoft Edge are used if present;
otherwise Playwright's own Chromium is downloaded), and the Python packages below (installed with pip).
Nothing else: no After Effects, no video editor, no accounts.
"""
import importlib, os, platform, shutil, subprocess, sys

CHECK = "--check" in sys.argv
PKGS = {"playwright": "playwright", "imageio_ffmpeg": "imageio-ffmpeg", "PIL": "pillow", "numpy": "numpy", "cv2": "opencv-python"}
ok, missing = [], []

def pip(*args):
    return subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check", *args], capture_output=True, text=True).returncode == 0

py = sys.version_info
print(f"Python {py.major}.{py.minor}.{py.micro} on {platform.system()} {platform.release()}")
if py < (3, 9): missing.append("Python 3.9 or newer (https://python.org)")

for mod, pkg in PKGS.items():
    try:
        importlib.import_module(mod); ok.append(pkg)
    except Exception:
        if CHECK: missing.append(f"pip package {pkg}")
        elif pip(pkg):
            try: importlib.import_module(mod); ok.append(pkg + " (installed now)")
            except Exception: missing.append(f"pip package {pkg} (install failed)")
        else: missing.append(f"pip package {pkg} (install failed)")

# a browser
browser = None
candidates = {
    "Windows": [("chrome", r"C:\Program Files\Google\Chrome\Application\chrome.exe"), ("chrome", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
                ("msedge", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"), ("msedge", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")],
    "Darwin": [("chrome", "/Applications/Google Chrome.app"), ("msedge", "/Applications/Microsoft Edge.app")],
    "Linux": [("chrome", shutil.which("google-chrome") or ""), ("chrome", shutil.which("google-chrome-stable") or ""), ("chromium", shutil.which("chromium") or "")],
}
for ch, p in candidates.get(platform.system(), []):
    if p and os.path.exists(p): browser = (ch, p); break
if browser:
    ok.append(f"browser: {browser[0]} ({browser[1]})")
else:
    if "playwright" in " ".join(ok):
        if CHECK: missing.append("a Chromium browser (Chrome or Edge), or run: python -m playwright install chromium")
        else:
            r = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], capture_output=True, text=True)
            if r.returncode == 0: ok.append("browser: Playwright Chromium (downloaded now)"); browser = ("chromium", "playwright")
            else: missing.append("a Chromium browser: install Google Chrome, or run python -m playwright install chromium")
    else:
        missing.append("a Chromium browser (Google Chrome or Microsoft Edge)")

# Playwright's ffmpeg (needed for video capture) and imageio's ffmpeg (used for everything else)
try:
    import imageio_ffmpeg; ok.append("ffmpeg (bundled with imageio-ffmpeg)")
except Exception:
    pass
if "playwright" in " ".join(ok):
    r = subprocess.run([sys.executable, "-m", "playwright", "install", "--dry-run", "ffmpeg"], capture_output=True, text=True)
    present = False
    for line in (r.stdout + r.stderr).splitlines():
        if "Install location" in line:
            loc = line.split(":", 1)[1].strip()
            present = os.path.isdir(loc) and any(os.scandir(loc))
    if present: ok.append("Playwright ffmpeg (video capture)")
    elif CHECK: missing.append("Playwright ffmpeg: run python -m playwright install ffmpeg")
    else:
        r2 = subprocess.run([sys.executable, "-m", "playwright", "install", "ffmpeg"], capture_output=True, text=True)
        if r2.returncode == 0: ok.append("Playwright ffmpeg (installed now)")
        else: missing.append("Playwright ffmpeg (python -m playwright install ffmpeg failed)")

print("\nREADY:")
for o in ok: print("  +", o)
if missing:
    print("\nMISSING (fix these, then run setup.py again):")
    for m in missing: print("  -", m)
    sys.exit(1)
print("\nAll set. Try:\n  python broll.py auto https://qdrant.tech/documentation/ --match \"top to bottom\" --style readthrough --duration 8 --out ./broll --name docs")
