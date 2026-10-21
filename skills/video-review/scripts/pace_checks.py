"""pace_checks.py: what John and his boss saw that the review did not, measured from the pixels.

  hard_cuts(...)      a graphic cut in or out with no transition ("how quick we are transitioning": the house wants soft
                      changes of about 0.8 s; a jump cut between two face takes is fine)
  scenes(...)         the video split at every change of picture (hard cuts and soft transitions alike)
  reading(...)        a card taken away before its words can be read ("I can't actually sit there and look at it... it
                      instantly is already gone"): words on screen against the time on screen, at READ_WPS
  broll_context(...)  the first B-roll of a page that never shows which page it is (its title, breadcrumb or menu):
                      "we show this section of something... we don't actually show what it is"
  brand_colours(...)  accents on the graphics that are not in the Qdrant palette (brand-consistency's brand.py)
"""
import os, sys, re, numpy as np, cv2

def bright(small): return small.reshape(len(small), -1).mean(axis=1)

def hard_cuts(small, motion, fps, graphic_mean=70.0):
    """[(frame, before_is_graphic, after_is_graphic)]: a one-frame change with a still lead-in (a cut, not a move)"""
    m = bright(small); out = []
    for i in range(3, len(small) - 3):
        if motion[i] > 18 and max(motion[i - 2:i]) < 6:
            g0, g1 = m[i - 1] < graphic_mean, m[min(len(m) - 1, i + 2)] < graphic_mean
            if g0 or g1: out.append((i, bool(g0), bool(g1)))
    return out

def scenes(small, motion, fps, min_len=0.4):
    """[(first_frame, last_frame)] between changes of picture: a cut (one big frame) or a soft transition (a run of moving
    frames whose two ends differ). Typing, a chip sliding in or a talking face do not change the picture this much"""
    n = len(small); cut = np.zeros(n, bool); i = 1
    while i < n:
        if motion[i] > 18: cut[i] = True; i += 1; continue
        if motion[i] > 2.5:
            j = i
            while j < n and motion[j] > 2.5: j += 1
            a, b = max(0, i - 2), min(n - 1, j + 1)
            if j - i >= 3 and np.abs(small[a].astype(np.int16) - small[b].astype(np.int16)).mean() > 14: cut[i:j] = True
            i = j; continue
        i += 1
    out, start = [], None
    for k in range(n):
        if not cut[k] and start is None: start = k
        if cut[k] and start is not None:
            if (k - start) / fps >= min_len: out.append((start, k - 1))
            start = None
    if start is not None and (n - start) / fps >= min_len: out.append((start, n - 1))
    return out

def _words(lines, H, is_code):
    """(prose words, code lines) a viewer reads: big titles and short all-caps labels are glanced, not read"""
    prose, code = 0, 0
    for l in lines:
        if l["score"] < 0.7 or l["h"] < 16: continue
        if l["box"][1] < 0.13 * H and l["h"] > 36: continue                             # the card's own title, along the top
        t = l["text"].strip()
        if is_code(t): code += 1; continue
        ws = re.findall(r"[A-Za-z0-9][A-Za-z0-9'.-]*", t)
        if len(ws) <= 3 and t.upper() == t: continue
        prose += len(ws)
    return prose, code

def cards(res, fps, small, H, is_code, graphic_mean=70.0, step=1.0):
    """the cards on screen, from the text itself: consecutive reads (about one a second) whose words mostly match are one
    card, a new set of words is a new card (typing and chips arriving add to a card; they do not start one). Motion is no
    guide here: a B-roll scroll, live typing and a moving focus box all move. -> [dict(i0, i1, t0, t1, words, prose, code, best)]"""
    m = bright(small); out = []; cur = None
    for i in sorted(res):
        if i >= len(m) or m[i] >= graphic_mean: cur = None; continue                   # the face: no card
        lines = res[i]; ws = {w.lower() for l in lines for w in re.findall(r"[A-Za-z]{3,}", l["text"])}
        if len(ws) < 3: cur = None; continue
        prose, code = _words(lines, H, is_code)
        if cur and len(ws & cur["words"]) / max(1, min(len(ws), len(cur["words"]))) >= 0.5 and i / fps - cur["t1"] <= step * 1.6:
            cur["words"] |= ws; cur["t1"] = i / fps; cur["i1"] = i
            if prose + 3 * code > cur["prose"] + 3 * cur["code"]: cur.update(prose=prose, code=code, best=i)
        else:
            cur = dict(i0=i, i1=i, t0=i / fps, t1=i / fps, words=set(ws), prose=prose, code=code, best=i); out.append(cur)
    return out

def reading(small, motion, fps, res, H, is_code, broll_spans=(), wps=3.8, min_words=15, step=1.0):
    """-> [(sev, t0, t1, frame, msg)] for cards whose words need longer than they stay up"""
    out = []; seen = set()
    for c in cards(res, fps, small, H, is_code, step=step):
        t0, t1 = c["t0"], c["t1"]; dur = t1 - t0 + step                                # read about once a second: first to last, plus a step
        if any(x0 - 0.5 <= t0 and t1 <= x1 + 1.0 for x0, x1 in broll_spans): continue  # a recorded page: it illustrates, it is not read whole
        again = len(c["words"] & seen) / max(1, len(c["words"])); seen |= c["words"]
        prose, code = c["prose"], c["code"]
        if prose + 3 * code < min_words or again >= 0.7: continue                     # little to read, or read already (the list coming back)
        need = min(14.0, prose / wps + 0.4 * code + 1.0)
        what = f"{prose} words" + (f" and {code} lines of code" if code else "")
        if dur < 0.6 * need: out.append(("fix", t0, t1, c["best"], f"on screen about {dur:.0f} s with {what} to read: about {need:.0f} s needed; it is gone before it can be read"))
        elif dur < 0.8 * need: out.append(("check", t0, t1, c["best"], f"on screen about {dur:.0f} s with {what}: about {need:.0f} s to read it all"))
    return out

def broll_context(res, fps, windows, page_titles):
    """the first B-roll of each page must show the page's title (or its breadcrumb or menu entry) in its opening seconds"""
    out, done = [], set()
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
    for w in sorted([w for w in windows if w.get("t_arrive") is not None], key=lambda w: w["t_arrive"]):
        page = (w.get("url") or "").split("#")[0].rstrip("/")
        if page in done: continue
        done.add(page); title = norm(page_titles.get(page, ""))
        if not title: continue
        ks = [i for i in res if w["t_arrive"] - 0.1 <= i / fps <= w["t_arrive"] + 3.5]
        shown = any(title[:24] in norm(" ".join(l["text"] for l in res[i])) for i in ks)
        if not shown: out.append((w["t_arrive"], ks[0] if ks else int(w["t_arrive"] * fps), f'the first B-roll of this page ("{page_titles[page][:50]}") never shows which page it is: open on its title, breadcrumb and menu, or click into it (broll-recorder --arrive-first)'))
    return out

def palette():
    try:
        sys.path.insert(0, os.path.expanduser(r"~/.claude/skills/brand-consistency/scripts")); import brand
        return np.array(brand.PALETTE, np.float32)
    except Exception:                                                                 # the core of the palette, if the brand skill is not installed
        return np.array([(220, 36, 76), (158, 13, 56), (255, 135, 146), (96, 71, 255), (148, 148, 255), (0, 150, 136), (3, 169, 244), (255, 152, 0), (0, 188, 212),
                         (240, 243, 250), (171, 177, 199), (101, 107, 127), (78, 83, 102), (17, 24, 36), (11, 15, 25)], np.float32)

def brand_colours(frame_bgr, mask_boxes=(), share=0.12, far=70.0):
    """-> (share of accent pixels far from every palette colour, the commonest such colour as #hex) on one graphic frame"""
    f = cv2.resize(frame_bgr, (480, 270), interpolation=cv2.INTER_AREA); keep = np.ones(f.shape[:2], bool)
    for (x, y, w, h) in mask_boxes: keep[int(y / 4):int((y + h) / 4), int(x / 4):int((x + w) / 4)] = False   # the presenter's window is not a graphic
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV); acc = keep & (hsv[..., 1] > 115) & (hsv[..., 2] > 90)
    if acc.sum() < 0.004 * acc.size: return 0.0, None
    px = f[acc][:, ::-1].astype(np.float32); P = palette()
    d = np.sqrt(((px[:, None, :] - P[None, :, :]) ** 2).sum(axis=2)).min(axis=1); off = px[d > far]
    if len(off) < share * len(px): return float(len(off) / len(px)), None
    q = (off // 24 * 24 + 12).astype(int); vals, cnt = np.unique(q, axis=0, return_counts=True); c = vals[cnt.argmax()]
    return float(len(off) / len(px)), "#%02X%02X%02X" % tuple(c)
