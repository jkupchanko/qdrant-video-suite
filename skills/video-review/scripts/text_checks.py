"""Text pass: read what is on screen (RapidOCR) and check it the way a careful viewer would.

  edge      a word cut by the frame edge (a box touching it), outside transitions
  small     body text too small for a phone: the median line height of a text-heavy frame under MIN_LINE px
  spelling  words not in the dictionary nor in the project's own words (script, transcript, docs page); OCR
            glues words together ("AMOUNTSOFDATA"), so a token that splits into known words is not a typo
  numbers   a number on screen that is not in the script, the transcript or the docs page: invented figures
            ("-69%", "6.8 GB") read as fact to a viewer
  stale     API spellings the docs have moved on from (references/rules.json), e.g. on_disk=True after v1.19
  code      whether the frame shows code (for the house rule: code keeps a small top-right presenter window)
  section   which docs section a frame of a page shows (B-roll): the last section heading above the middle of
            the frame, else the section whose text the frame matches best
"""
import re, json, os, difflib, cv2, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = json.load(open(os.path.join(HERE, "..", "references", "rules.json"), encoding="utf-8"))
MIN_LINE = RULES["thresholds"]["min_line_px"]
_ocr = None
def ocr(bgr, pad=24):
    """-> [dict(text, score, box=(x0, y0, x1, y1), h)]. The frame is read with its edge pixels repeated `pad` px outwards: the
    detector drops a letter the frame edge has cut in half, and that letter is the one the edge check needs (OpenCV 4 here
    read "UPLOADS" from "K UPLOADS"); boxes come back in frame coordinates, clamped to it"""
    global _ocr
    if _ocr is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr = RapidOCR()
    H, W = bgr.shape[:2]
    res, _ = _ocr(cv2.copyMakeBorder(bgr, pad, pad, pad, pad, cv2.BORDER_REPLICATE) if pad else bgr); out = []
    for quad, text, score in (res or []):
        q = np.array(quad, np.float32) - pad; x0, y0 = np.maximum(q.min(axis=0), 0); x1, y1 = np.minimum(q.max(axis=0), (W - 1, H - 1))
        if x1 <= x0 or y1 <= y0: continue                                              # wholly in the repeated border
        out.append(dict(text=str(text), score=float(score), box=[int(x0), int(y0), int(x1), int(y1)], h=int(y1 - y0)))
    return out

def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())

# ---------------------------------------------------------------- words
NUM_WORDS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
             "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "hundred": 100, "thousand": 1000, "million": 1000000, "first": 1, "second": 2, "third": 3, "final": None}
class Lexicon:
    """the words and numbers this video may legitimately show: from the script, the transcript, the docs page"""
    def __init__(self, texts):
        from spellchecker import SpellChecker
        self.sp = SpellChecker(); self.own = set(); self.nums = set()
        for t in texts + RULES["lexicon"]:
            for w in re.findall(r"[A-Za-z][A-Za-z']+", t): self.own.add(w.lower().strip("'"))
            for n in numbers_in(t): self.nums.add(n)
            for w in re.findall(r"[a-z]+", t.lower()):
                if NUM_WORDS.get(w) is not None: self.nums.add(float(NUM_WORDS[w]))
        self.own |= {w.replace("'", "") for w in self.own}
    def known(self, w):
        w = w.lower().strip("'"); return len(w) <= 2 or w in self.own or w in self.sp or w.replace("'", "") in self.own
    def splits(self, w):
        """can OCR-glued letters be read as known words? (dynamic programming, longest words first)"""
        w = w.lower(); n = len(w); ok = [False] * (n + 1); ok[0] = True
        for i in range(1, n + 1):
            for j in range(max(0, i - 18), i):
                if ok[j] and (i - j >= 2 or w[j:i] in ("a", "i")) and (w[j:i] in self.own or w[j:i] in self.sp): ok[i] = True; break
        return ok[n]

def numbers_in(s):
    """numbers as values: 1,024 -> 1024; 10M -> 1e7; 64-256 -> 64, 256; v1.19 -> 1.19"""
    out = []
    for m in re.finditer(r"(?<![0-9.,])(\d[\d,]*(?:\.\d+)?)\s*([kKmMbB](?![a-z])|%|GB|MB|KB|ms)?", s):        # whole digit runs: OCR glues "to256"
        try: v = float(m.group(1).replace(",", ""))
        except ValueError: continue
        u = (m.group(2) or "").lower(); v *= {"k": 1e3, "m": 1e6, "b": 1e9}.get(u, 1); out.append(v)
    return out

def is_code(text):
    return bool(re.search(r"[=({}\[\]]|\w\.\w+\(|\b(client|models|def|import|return)\b", text)) and not re.search(r"\s{2,}", text)

# ---------------------------------------------------------------- checks on one frame's lines
def reread(bgr, box, scale=2.0):
    """OCR one box again, larger: a misread changes, a real typo reads the same"""
    x0, y0, x1, y1 = box; p = 8; crop = bgr[max(0, y0 - p):y1 + p, max(0, x0 - p):x1 + p]
    if crop.size == 0: return ""
    return " ".join(l["text"] for l in ocr(cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)))

def check_frame(lines, W, H, lex, in_transition=False, bgr=None, page=False):
    """-> list of (kind, severity, message, box). page=True: the frame is a recorded web page (B-roll), whose words and numbers are
    its own source: only the edges, the size and stale API spellings are the edit's business there"""
    out = []; good = [l for l in lines if l["score"] >= 0.75 and len(l["text"].strip()) >= 2]
    if not in_transition:
        for l in good:
            x0, y0, x1, y1 = l["box"]
            if (x0 <= 10 or x1 >= W - 10) and len(l["text"]) >= 3:          # OCR boxes whole letters only: a cut one leaves a few px
                out.append(("edge", "fix", f'text cut at the frame edge: "{l["text"][:60]}"', l["box"]))
    if bgr is not None and not in_transition and not page:                         # a recorded page's own boxes and rules are not the edit's
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        for l in good:
            if l["h"] < 16: continue                                                 # text that small is picture (a thumbnail's), not reading
            k = crossed(gray, l["box"])
            if k: out.append(("overlap", "check", f'a {k} line runs through "{l["text"][:50]}": text spilling out of its box, or a shape drawn over it', l["box"]))
    body = [l["h"] for l in good if len(l["text"]) >= 12]
    if len(body) >= 3 and float(np.median(body)) < MIN_LINE:
        bb = [min(l["box"][0] for l in good), min(l["box"][1] for l in good), max(l["box"][2] for l in good), max(l["box"][3] for l in good)]
        out.append(("small", "check", f"text too small for a phone: lines {int(np.median(body))} px tall (want {MIN_LINE}+ at 1080)", bb))
    for l in good:
        if l["score"] < 0.85: continue
        for bad, why in RULES["stale"].items():
            if bad.replace(" ", "") in l["text"].replace(" ", ""): out.append(("stale", "check" if page else "fix", f'"{bad}" on screen: {why}', l["box"]))
        if page or l["h"] < 26: continue                                            # small text: OCR misreads it too often to call typos
        text = re.sub(r"\S*(\.\.+|…)\s*$", "", l["text"])                       # a word cut by "..." is the layout's, not a typo
        for tok in re.findall(r"[A-Za-z][A-Za-z']{3,}", text):
            if is_code(l["text"]) or lex.known(tok) or lex.splits(tok): continue
            if text.rstrip().endswith(tok) and len(tok) >= 3 and any(w.startswith(tok.lower()) for w in lex.own): continue   # live code: typed partway
            if any(lex.known(tok.replace(x, y)) for x, y in (("I", "l"), ("l", "I"), ("1", "l"), ("0", "o"))): continue      # sans fonts: l / I
            low = tok.lower()
            if len(low) >= 4 and all(ord(b) - ord(a_) == 1 for a_, b in zip(low, low[1:])): continue   # "ABCDEFGH": a sequence (drawer labels), not a word
            if bgr is not None:
                again = re.findall(r"[A-Za-z][A-Za-z']{3,}", reread(bgr, l["box"]))
                if tok not in again: continue                                        # read differently at 2x: an OCR misread, not the screen
            out.append(("spelling", "check", f'"{tok}" is not a known word (in "{l["text"][:50]}"); suggestion: {lex.sp.correction(tok.lower()) or "none"}', l["box"]))
        tail = re.search(r"(\d+)\s*$", l["text"])                                    # live code: a number typed partway ("size=76" of 768)
        for v in numbers_in(l["text"]):
            if v in lex.nums or (v == int(v) and int(v) in (0, 1)): continue
            if tail and v == float(tail.group(1)) and any(f"{n:g}".startswith(tail.group(1)) for n in lex.nums): continue
            out.append(("number", "check", f'{l["text"][:60]!r}: the number {v:g} is not in the script, the transcript or the docs page', l["box"]))
    return out

def crossed(gray, box):
    """a straight drawn line (a card or panel border) running through a line of text and on past it: text spilling out of its
    box, or a box drawn over text. Letters make short strokes; a border runs on above and below (or left and right of) the word.
    -> 'vertical' | 'horizontal' | None"""
    H, W = gray.shape; x0, y0, x1, y1 = box; h = y1 - y0; e = max(6, int(0.45 * h))
    X0, Y0, X1, Y1 = max(0, x0 - e), max(0, y0 - e), min(W, x1 + e), min(H, y1 + e)
    if X1 - X0 < 20 or Y1 - Y0 < 12 or y0 - Y0 < 4 or Y1 - y1 < 4: return None
    g = gray[Y0:Y1, X0:X1].astype(np.float32)
    gx = np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)); gy = np.abs(cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)); T = 60
    up, dn = slice(0, y0 - Y0), slice(y1 - Y0, Y1 - Y0)
    for c in range(x0 - X0 + 3, x1 - X0 - 3):                                   # a vertical border inside the word, running on above and below
        col = np.maximum(gx[:, c - 1], np.maximum(gx[:, c], gx[:, c + 1])) > T
        if col[up].mean() > 0.9 and col[dn].mean() > 0.9 and col[y0 - Y0:y1 - Y0].mean() > 0.6:
            side = np.r_[g[up, max(0, c - 14):max(0, c - 4)].ravel(), g[up, c + 5:c + 15].ravel(), g[dn, max(0, c - 14):max(0, c - 4)].ravel(), g[dn, c + 5:c + 15].ravel()]
            if side.size and side.std() < 10: return "vertical"                  # a drawn border on a flat background, not a photo's edges
    lf, rt = slice(0, x0 - X0), slice(x1 - X0, X1 - X0)
    for r in range(y0 - Y0 + 2, y1 - Y0 - 2):                                   # a horizontal one through it, running on left and right
        row = np.maximum(gy[r - 1], np.maximum(gy[r], gy[r + 1])) > T
        if lf.stop > 3 and rt.stop - rt.start > 3 and row[lf].mean() > 0.9 and row[rt].mean() > 0.9 and row[x0 - X0:x1 - X0].mean() > 0.6:
            side = np.r_[g[max(0, r - 14):max(0, r - 4), lf].ravel(), g[r + 5:r + 15, lf].ravel(), g[max(0, r - 14):max(0, r - 4), rt].ravel(), g[r + 5:r + 15, rt].ravel()]
            if side.size and side.std() < 10: return "horizontal"
    return None

def code_lines(lines): return [l for l in lines if l["score"] >= 0.7 and is_code(l["text"])]

def content_sections(sections):
    """the page's own sections, not the navigation's: those that start where the page title (H1) starts. -> (sections, column left)"""
    h1 = next((x for x in sections if x.get("tag") == "H1"), None)
    if not h1: return sections, None
    return [x for x in sections if abs(x.get("left", 0) - h1["left"]) <= 40], h1["left"]

def section_of(lines, sections, H, W=1920):
    """which docs section the frame shows: the last heading above the middle, else the best body match. -> (heading, how, others)
    Only the page's own column counts: the sidebars list every heading (contents, navigation) and would match anything."""
    sections, col = content_sections(sections)
    if col is not None: lines = [l for l in lines if col - 40 <= l["box"][0] < col + 0.6 * (W - col)]
    heads = []; med = float(np.median([l["h"] for l in lines])) if lines else 0
    for l in lines:
        # a heading is set bigger than the text around it; a contents entry is small and cut with "..."
        if l["h"] < 1.3 * med or l["text"].rstrip().endswith(("...", "…", "..")): continue
        for s in sections:
            t = s["text"]
            if len(norm(l["text"])) >= 6 and difflib.SequenceMatcher(None, norm(l["text"]), norm(t)).ratio() > 0.82 or (len(norm(l["text"])) >= 12 and norm(t).startswith(norm(l["text"]))):
                heads.append((l["box"][1], t))
    heads.sort(); mid = H * 0.5
    above = [t for y, t in heads if y <= mid]
    if above: return above[-1], "heading above the middle", sorted({t for _, t in heads} - {above[-1]})
    txt = norm(" ".join(l["text"] for l in lines))
    if not txt: return None, "no text", []
    best = max(sections, key=lambda s: difflib.SequenceMatcher(None, txt[:400], norm(s.get("body", ""))).find_longest_match(0, min(400, len(txt)), 0, len(norm(s.get("body", "")))).size)
    return best["text"], "body text", sorted({t for _, t in heads})
