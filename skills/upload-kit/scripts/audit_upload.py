#!/usr/bin/env python
"""audit_upload.py: how the 49 audited videos are titled, described, chaptered and thumbnailed, to set this skill's rules from.

  yt-dlp --skip-download --write-info-json --write-thumbnail --convert-thumbnails jpg -o "%(id)s.%(ext)s" -a urls.txt   (in META_DIR)
  python audit_upload.py META_DIR   -> META_DIR/upload_audit.json, and a summary

  title        length in characters and words; a colon or dash splitting it; a question; a number; all-capital words;
               brackets; an emoji; the product or tool named in it
  description  the first two lines (what shows above "more"): their length; links (how many, to docs or GitHub);
               timestamps (chapters written in it); hashtags
  chapters     present or not, how many, the shortest and the median length, the first at 0:00
  thumbnail    words on it (OCR), a face (and how much of the frame), brightness, the strongest colours, text height
"""
if __name__ == "__main__":                                   # run on the suite's own Python (.venv, made by setup.py), whichever python started it
    import os as _o, sys as _s, subprocess as _sp
    _v = _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), "..", "..", "..", ".venv", *(("Scripts", "python.exe") if _o.name == "nt" else ("bin", "python")))
    if _o.path.exists(_v) and _o.path.normcase(_o.path.realpath(_s.prefix)) != _o.path.normcase(_o.path.realpath(_o.path.dirname(_o.path.dirname(_v)))):
        _s.exit(_sp.call([_v, _o.path.realpath(__file__)] + _s.argv[1:]))
import glob, json, os, re, sys
import numpy as np, cv2

def title(t):
    w = t.split()
    return dict(chars=len(t), words=len(w), split=bool(re.search(r"[:|–—-] ", t)), question="?" in t, number=bool(re.search(r"\d", t)),
                caps_words=sum(1 for x in w if len(x) > 2 and x.isupper()), brackets=bool(re.search(r"[\(\[]", t)),
                emoji=bool(re.search(r"[\U0001F300-\U0001FAFF☀-➿]", t)))

def description(d):
    lines = [l for l in (d or "").splitlines()]
    first = " ".join(l for l in lines[:2] if l.strip())
    links = re.findall(r"https?://\S+", d or "")
    return dict(first_chars=len(first), first=first[:200], links=len(links), docs_or_github=sum(1 for l in links if re.search(r"docs?\.|/docs|github\.com|documentation", l)),
                link_in_first=bool(re.search(r"https?://", first)), timestamps=len(re.findall(r"(?m)^\s*\(?\d{1,2}:\d{2}(?::\d{2})?\)?", d or "")),
                hashtags=len(re.findall(r"(?<!\w)#\w+", d or "")), chars=len(d or ""))

def chapters(info):
    C = info.get("chapters") or []
    if not C: return dict(n=0)
    L = [c["end_time"] - c["start_time"] for c in C]
    return dict(n=len(C), first_at=C[0]["start_time"], shortest=round(min(L), 1), median=round(float(np.median(L)), 1), titles=[c["title"] for c in C][:12],
                title_words=round(float(np.median([len(c["title"].split()) for c in C])), 1))

def thumbnail(p, ocr, face):
    im = cv2.imread(p); h, w = im.shape[:2]; im = cv2.resize(im, (1280, int(1280 * h / w))); h, w = im.shape[:2]
    res, _ = ocr(im); txt = [(t, b) for b, t, s in (res or []) if float(s) > 0.6]
    words = sum(len(t.split()) for t, _ in txt); th = [max(p_[1] for p_ in b) - min(p_[1] for p_ in b) for _, b in txt]
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); F = face.detectMultiScale(g, 1.15, 6, minSize=(h // 10, h // 10))
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); sat = hsv[..., 1] > 120
    hue = np.bincount((hsv[..., 0][sat] // 15).ravel(), minlength=12) if sat.any() else np.zeros(12, int)
    names = ["red", "orange", "yellow", "yellow-green", "green", "green", "cyan", "blue", "blue", "violet", "magenta", "pink"]
    return dict(words=words, text=" | ".join(t for t, _ in txt)[:120], text_height=round(float(max(th)) / h, 3) if th else 0.0, faces=len(F),
                face_share=round(float(max(fw * fh for _, _, fw, fh in F)) / (w * h), 3) if len(F) else 0.0, brightness=round(float(g.mean()) / 255, 2),
                saturated=round(float(sat.mean()), 2), main_colour=names[int(hue.argmax())] if sat.any() else "none")

def main():
    d = sys.argv[1]; from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR(); face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml"); out = []
    for p in sorted(glob.glob(os.path.join(d, "*.info.json"))):
        I = json.load(open(p, encoding="utf-8")); vid = I["id"]; tp = os.path.join(d, vid + ".jpg")
        out.append(dict(id=vid, title_text=I.get("title", ""), channel=I.get("channel", ""), views=I.get("view_count"), duration=I.get("duration"),
                        title=title(I.get("title", "")), description=description(I.get("description", "")), chapters=chapters(I),
                        thumbnail=thumbnail(tp, ocr, face) if os.path.exists(tp) else None))
        print(vid, out[-1]["title_text"][:60], "| chapters", out[-1]["chapters"]["n"], "| thumb words", (out[-1]["thumbnail"] or {}).get("words"), flush=True)
    json.dump(out, open(os.path.join(d, "upload_audit.json"), "w", encoding="utf-8"), indent=1)

if __name__ == "__main__":
    main()
