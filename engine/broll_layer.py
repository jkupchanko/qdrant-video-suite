"""B-ROLL LAYER: the B-roll the script calls for, at the moment the cut says the line, for any style.

The script carries `[B-ROLL: url | spoken line | section: X | 6s | name: n]` markers (the broll-recorder skill's format);
script_broll.py has recorded each one to <broll>/<name>.mp4 with <name>_manifest.json beside it. Here each marker's
line is found in the cut by its words (the take's wording differs from the script, so it is matched, not looked up),
and the clip is given a window [t0, t0 + length] starting where that line is spoken.

  windows()            -> [dict(name, t0, t1, path, section, line, piece, match)]
  draw(w, bg)          -> draw(lt, dur, ctx) for the shot list: the page full frame, a slow push toward the docs
                          column; it arrives with the engine's zoom, a 0.5 s push in (the script's value for a card arrival)
  splice(shots, ws, retime)  cut the windows into a style's shot list (Animated Board); each piece keeps its own clock

The page is used full frame (no card): the docs page is dark like both styles, and full frame leaves no dead space.
"""
import os, re, json, difflib
import cv2
from PIL import Image
import engine as E

SCRIPT = os.environ.get("BROLL_SCRIPT", r"C:\Users\ADMIN\camera_audit\full_suite\bulk_uploads_script_final.md")
BROLL = os.environ.get("BROLL_DIR", r"C:\Users\ADMIN\camera_audit\full_suite\broll2")   # readthrough at 1.4x page zoom
WORDS = r"C:\Users\ADMIN\camera_audit\styles\out\v2_words.json"
MARK = re.compile(r"\[B-ROLL:\s*([^|\]]+)\|([^|\]]+)\|(.*?)\]")
PUSH_MAX = 1.0                                     # no push: a crop cuts the sidebars mid-word; the page is recorded at 1.4x zoom, readable full frame

CUT = r"C:\Users\ADMIN\camera_audit\edit\full_edit\bulk_uploads_full_edit_v2.mp4"
def _norm(s): return re.findall(r"[a-z0-9]+", s.lower())

_aud = {}
def onset(a, b, path=CUT, sr=16000, win=0.05, db=-32.0):
    """the first moment in [a, b] the voice is up: the transcript can miss a line's first words, the audio cannot"""
    import subprocess, numpy as np, imageio_ffmpeg
    if path not in _aud:
        raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"], capture_output=True).stdout
        _aud[path] = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    x = _aud[path]; n = int(win * sr)
    for i in range(int(a * sr), int(b * sr), n):
        if 20 * np.log10(max(1e-6, float(np.sqrt((x[i:i + n] ** 2).mean())))) > db: return i / sr
    return b

def markers(path=SCRIPT):
    out = []
    for m in MARK.finditer(open(path, encoding="utf-8").read()):
        url, line, rest = m.group(1).strip(), m.group(2).strip(), m.group(3)
        f = dict(x.split(":", 1) if ":" in x else ("len", x) for x in [p.strip() for p in rest.split("|")] if x)
        f = {k.strip(): v.strip() for k, v in f.items()}
        secs = float(re.sub(r"[^0-9.]", "", f.get("len", "6")) or 6)
        out.append(dict(url=url, line=line, section=f.get("section", ""), name=f.get("name", ""), secs=secs))
    return out

def _pieces(words=None):
    P = json.load(open(words or WORDS))["pieces"]
    return [(p["t0"], p.get("t1", p["t0"]), [w[0] for w in p.get("words", [])], [w[1] for w in p.get("words", [])]) for p in P]

def find_line(line, pieces=None):
    """the cut piece (or two, when the take split the line) that says this line; returns (index, t0, ratio)"""
    pieces = pieces or _pieces(); want = _norm(line); best = (0.0, None, None)
    for i in range(len(pieces)):
        for span in (1, 2):
            ws = sum((pieces[j][2] for j in range(i, min(len(pieces), i + span))), [])
            if not ws: continue
            r = difflib.SequenceMatcher(None, _norm(" ".join(ws)), want).ratio() - 0.04 * (span - 1)
            if r > best[0]: best = (r, i, pieces[i][3][0] if pieces[i][3] else pieces[i][0])
    return best[1], best[2], best[0]

def windows(path=SCRIPT, broll=BROLL, words=None, cut=None):
    """words / cut: another build's cut-time word pieces and cut (default: the v2 Bulk Uploads cut)"""
    pcs = _pieces(words); out = []
    for m in markers(path):
        clip = os.path.join(broll, m["name"] + ".mp4"); man = os.path.join(broll, m["name"] + "_manifest.json")
        if not os.path.exists(clip): print(f"  B-roll {m['name']}: no clip at {clip}"); continue
        i, t0, r = find_line(m["line"], pcs); t0 = max(0.0, onset(pcs[i][0], t0 + 0.01, path=cut or CUT) - 0.05)   # lands with the first sound of the line
        mj = json.load(open(man)) if os.path.exists(man) else {}
        dur = mj.get("duration", m["secs"]) if mj.get("style") == "arrive" else min(m["secs"], mj.get("duration", m["secs"]))   # the click-through runs whole
        out.append(dict(name=m["name"], t0=round(t0, 2), t1=round(t0 + dur, 2), path=clip, section=m["section"], line=m["line"],
                        piece=i, match=round(r, 2), box=mj.get("section_box", {}).get("block")))
    out.sort(key=lambda w: w["t0"])
    for a, b in zip(out, out[1:]):                                                  # never overlapping
        if b["t0"] < a["t1"]: a["t1"] = b["t0"]
    return out

def frame(w, lt):
    """the page at clip time lt, pushed slowly toward the docs column, on a 16:9 crop (nothing stretched)"""
    im = E.clip(w["path"]).frame(lt).convert("RGB"); iw, ih = im.size; dur = w["t1"] - w["t0"]
    bx = w.get("box") or dict(x=iw * 0.29, w=iw * 0.44); cx = bx["x"] + bx["w"] / 2
    k = E.ease(min(1.0, max(0.0, lt / max(0.1, dur)))); z = 1.0 + (PUSH_MAX - 1.0) * k
    cw, ch = iw / z, ih / z; x0 = min(max(0, cx - cw / 2), iw - cw); y0 = (ih - ch) / 2
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((E.W, E.H), Image.LANCZOS)

def draw(w, bg=(0, 0, 0)):
    """for a shot list; the arrival is the engine's `zoom` (a hard cut, settling in from 92% over TR)"""
    return lambda lt, dur, ctx: frame(w, ctx["t"] - w["t0"]).convert("RGBA")

def splice(shots, ws, bg=(0, 0, 0), after_tr="push_up", min_piece=0.6, arrive="zoom"):
    """cut the B-roll windows into a shot list of dict(t0, t1, kind, ...): the shot under a window is split
    around it, a leftover shorter than min_piece is given to the B-roll (it holds its last frame), and the
    shot coming back after a window arrives with `after_tr`. B-roll shots are marked no_face: the layouts
    and the corner window leave them alone (the script's camera call for B-roll is NONE)."""
    out = []
    for sh in shots:
        pieces = [[sh["t0"], sh["t1"]]]
        for w in ws:
            nxt = []
            for a, b in pieces:
                if w["t1"] <= a or w["t0"] >= b: nxt.append([a, b]); continue
                if w["t0"] - a >= min_piece: nxt.append([a, w["t0"]])
                if b - w["t1"] >= min_piece: nxt.append([w["t1"], b])
            pieces = nxt
        for k, (a, b) in enumerate(pieces):
            tr = sh["tr"] if abs(a - sh["t0"]) < 1e-6 else after_tr
            if any(abs(a - w["t1"]) < 1e-6 for w in ws): tr = after_tr
            out.append(dict(sh, t0=a, t1=b, tr=tr))
    for w in ws:
        out.append(dict(t0=w["t0"], t1=w["t1"], kind="graphic", draw=draw(w, bg), tr=arrive, face=None, no_face=True, shows_face=False, _hidden=False, scene="broll:" + w["name"], broll=w["name"]))
    out.sort(key=lambda s: s["t0"])
    for x, y in zip(out, out[1:]): x["t1"] = y["t0"]                                 # a dropped sliver: the shot before runs on over it
    gaps = [(round(x["t1"], 2), round(y["t0"], 2)) for x, y in zip(out, out[1:]) if abs(x["t1"] - y["t0"]) > 1e-3]
    if gaps: print("  B-roll splice left gaps/overlaps:", gaps)
    return out

if __name__ == "__main__":
    for w in windows(): print(f"{w['name']:12s} {w['t0']:7.2f}-{w['t1']:7.2f}  piece {w['piece']:2d}  match {w['match']:.2f}  {w['section']}")
