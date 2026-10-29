"""Script side of the review: what the script promised, found in the cut.

  parse(path)        -> dict(lines, markers, calls, counts): spoken lines (not headings, notes or [brackets]),
                        [B-ROLL: url | line | section: X | 6s | name: n] markers, [**Camera:** FULL/SMALL/NONE ...]
                        calls with their times, and the numbers the script's Count section claims
  find_line(...)     the cut piece that says a script line (the take's wording differs: matched, not looked up)
  onset(...)         the first sound of a piece: the transcript can miss a line's first words, the audio cannot
"""
import re, json, difflib, subprocess, numpy as np

def _norm_words(s): return re.findall(r"[a-z0-9]+", s.lower())
def mmss(s):
    m = re.match(r"(\d+):(\d{2}(?:\.\d+)?)", s); return int(m.group(1)) * 60 + float(m.group(2)) if m else None

MARK = re.compile(r"\[B-ROLL:\s*([^|\]]+)\|([^|\]]+)\|(.*?)\]")
CALL = re.compile(r"\[\*\*Camera:\*\*\s*(FULL|SMALL|NONE)\b([^\]]*)\]")
LOWER = re.compile(r"\[\*\*Lower third:\*\*\s*([^|\]]+)\|([^|\]]+)(?:\|([^\]]*))?\]", re.I)
def lower_thirds_in(s):
    """[**Lower third:** NAME | TITLE | 5 s] -> [dict(name, title, secs)]: the presenter's name card (brand-consistency)"""
    return [dict(name=m.group(1).strip(), title=m.group(2).strip(), secs=float(re.sub(r"[^0-9.]", "", m.group(3) or "") or 5.0)) for m in LOWER.finditer(s)]

def parse(path):
    text = open(path, encoding="utf-8").read(); body = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    lines, markers, calls, counts, block_first, last_line = [], [], [], {}, None, None   # block_first: the first line since the last call
    lowers = []
    in_count = False
    for raw in body.splitlines():
        s = raw.strip()
        if s.startswith("## "): in_count = s.lower().startswith("## count"); block_first = None; continue     # a call's block stays in its section
        if in_count:
            m = re.search(r"Camera calls:\s*(\d+)", s); counts.update({"calls": int(m.group(1))} if m else {})
            m = re.search(r"B-roll:\s*(\d+)", s); counts.update({"broll": int(m.group(1))} if m else {})
            m = re.search(r"face is off for (\d+) s of the (\d+) s", raw); counts.update({"face_off_s": int(m.group(1)), "dur_s": int(m.group(2))} if m else {})
            continue
        if not s or s.startswith("#"): continue
        for m in MARK.finditer(s):
            f = {}
            for part in [p.strip() for p in m.group(3).split("|") if p.strip()]:
                if ":" in part: k, v = part.split(":", 1); f[k.strip()] = v.strip()
                else: f["len"] = part
            markers.append(dict(url=m.group(1).strip(), line=m.group(2).strip(), section=f.get("section", ""), name=f.get("name", ""),
                                secs=float(re.sub(r"[^0-9.]", "", f.get("len", "6")) or 6), under=last_line))   # under: the spoken line it sits under
        for lw in lower_thirds_in(s): lowers.append(dict(lw, line=last_line))
        for m in CALL.finditer(s):
            rest = m.group(2); at = re.search(r"\bat (\d+:\d{2})", rest); to = re.search(r"\bto (\d+:\d{2}|the end)", rest); fo = re.search(r"\bfor (\d+(?:\.\d+)?) s\b", rest)
            calls.append(dict(layout=m.group(1), text=m.group(0)[:160], at=mmss(at.group(1)) if at else None,
                              to=(None if not to else (1e9 if to.group(1) == "the end" else mmss(to.group(1)))), dur=float(fo.group(1)) if fo else None,
                              after_line=block_first, last_line=last_line, corner="top right" if "top right" in rest.lower() else None))
            block_first = None
        if s.startswith("["): continue
        lines.append(s); block_first = block_first or s; last_line = s
    return dict(lines=lines, markers=markers, calls=calls, counts=counts, lowers=lowers)

def pieces(words_json):
    P = json.load(open(words_json))["pieces"]
    return [(p["t0"], p.get("t1", p["t0"]), [w[0] for w in p.get("words", [])], [w[1] for w in p.get("words", [])]) for p in P]

def find_line(line, pcs):
    want = _norm_words(line); best = (0.0, None, None)
    for i in range(len(pcs)):
        for span in (1, 2, 3, 4):                                                     # a line the cut split at its pauses spans several pieces
            ws = sum((pcs[j][2] for j in range(i, min(len(pcs), i + span))), [])
            if not ws: continue
            r = difflib.SequenceMatcher(None, _norm_words(" ".join(ws)), want).ratio() - 0.04 * (span - 1)
            if r > best[0]: best = (r, i, pcs[i][3][0] if pcs[i][3] else pcs[i][0])
    return best[1], best[2], best[0]

STOP = set("a an the and or but so to of for in on at is are be can it its this that these those you your we our they with as by from if then than when while which what into just also more most very".split())
def recall(line, pcs, i, span=4):
    """how many of the line's content words the cut says from piece i on (up to `span` pieces: the cut splits a line at its
    pauses): rewording keeps them, a missing line does not"""
    want = [w for w in _norm_words(line) if w not in STOP]
    have = set(_norm_words(" ".join(sum((pcs[j][2] for j in range(i, min(len(pcs), i + span))), []))))
    return sum(1 for w in want if w in have or w.rstrip("s") in have or w + "s" in have) / max(1, len(want))

_aud = {}
def audio(path, sr=16000):
    if path not in _aud:
        import imageio_ffmpeg
        raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"], capture_output=True).stdout
        _aud[path] = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    return _aud[path]

def onset(path, a, b, sr=16000, win=0.05, db=-32.0):
    x = audio(path, sr); n = int(win * sr)
    for i in range(int(a * sr), int(b * sr), n):
        if 20 * np.log10(max(1e-6, float(np.sqrt((x[i:i + n] ** 2).mean())))) > db: return i / sr
    return b

def line_time(line, pcs, cut):
    """(piece index, the line's first sound in the cut, match ratio)"""
    i, t0, r = find_line(line, pcs)
    if i is None: return None, None, 0.0
    return i, (onset(cut, pcs[i][0], t0 + 0.01) if cut else t0), r

def placed(script, pcs, cut):
    """each script line's time in the cut, found in script order as the style places them -> {line: t}. A B-roll marker
    quotes a fragment, and a fragment searched alone can match a near-twin minutes away (Docker Compose's "you can also use
    Docker Compose" found the outro's "Now you can use Docker", Get Started 10-28); the line it sits under, in order, cannot"""
    out, last = {}, None
    for s in script["lines"]:
        i, t0, r = line_time(s, pcs, cut)
        if i is None or (r < 0.38 and recall(s, pcs, i) < 0.5): continue           # not in the cut
        if last is not None and t0 < last - 0.5: continue                           # out of order: a match elsewhere
        last = t0; out.setdefault(s, t0)
    return out

def call_spans(calls, pcs, cut, dur):
    """each camera call's [t0, t1] in the cut: its 'at', else the first of the lines it describes (those since the call before);
    it runs to its 'to' / 'for', else to the next call"""
    out = []
    for c in calls:                                                                   # by its line first: a script's m:ss times belong to
        t0 = None                                                                     # the cut it was timed on, and a new cut moves them
        anchor = c.get("last_line") if c["at"] is not None else c["after_line"]      # a timed call is about the line just before it;
        if anchor:                                                                    # an untimed one, about its whole block
            _, tl, r = line_time(anchor, pcs, cut)
            if tl is not None and r >= 0.4: t0 = tl
        if t0 is None: t0 = c["at"]
        span = (c["to"] - c["at"]) if (c["to"] and c["at"] is not None and c["to"] < 1e8) else c["dur"]   # not `dur`: that is the video's
        out.append(dict(c, t0=t0 if t0 is not None else 0.0, span=span))
    for k, c in enumerate(out):
        nxt = out[k + 1]["t0"] if k + 1 < len(out) else dur
        c["t1"] = (c["t0"] + c["span"]) if c.get("span") else (dur if c["to"] and c["to"] >= 1e8 else nxt)
        c["t1"] = max(c["t0"] + 0.5, min(c["t1"], dur))
    return out
