#!/usr/bin/env python
"""captions.py: captions for a cut, spelled the way the script spells things, as a subtitle file and burned into the video.

  python captions.py VIDEO.mp4 --cutlist cutlist.md [--script SCRIPT.md] --out DIR [--burn] [--words words.json]
      -> DIR/captions.srt, captions.vtt (upload to YouTube), captions.ass, and with --burn DIR/captioned.mp4

VIDEO is anything on the cut's timeline (the cut, cut_voice.mp4, or the styled video). Its own sound is transcribed
(DIR/heard.json, kept for the next run), so the captions are what the viewer hears. The take's transcript placed through
the cut list (--words) is the old way: around a restart its word times smear, and Get Started's captions lost "Make sure
you subscribe" at 5:18 that way, with the words plainly in the cut.

  spelling   what was said wins, spelled as the script spells it: each line's words are aligned to its script line and a
             word that is a close miss of the script's word takes the script's spelling ("Quadrant" -> "Qdrant", "web ui"
             -> "Web UI"); then the glossary (references/glossary.txt) for terms the script does not carry.
  cues       a subtitle (SRT/VTT) is the reading kind: up to two lines of 42 characters, 1 to 7 s, held long enough to read
             at 17 characters a second where the next one allows, broken at a full stop first, then a comma or a pause. This is
             the default and the only kind the 49 pro videos use (research.md): none of them burns captions in.
  burned     only with --burn: an ASS file in the brand font (Mona Sans, from brand-consistency), white on a dark box,
             placed and sized by references/caption_style.json, rendered with ffmpeg's libass; the audio is copied.
"""
import argparse, difflib, json, os, re, subprocess, sys
import imageio_ffmpeg
HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE); SK = os.path.dirname(SKILL)
FF = imageio_ffmpeg.get_ffmpeg_exe(); FONTS = os.path.join(SK, "brand-consistency", "assets", "fonts")
SRT_RULES = dict(chars=42, lines=2, min_s=1.0, max_s=7.0, cps=17.0)

def norm(w): return re.sub(r"[^a-z0-9]", "", w.lower())

def rows(cutlist):
    return [(float(t), float(a), float(b), line.strip()) for t, a, b, line in
            re.findall(r"^\| ([\d.]+) \| ([\d.]+)-([\d.]+) \| x[\d.]+ \| (.*?) \|", open(cutlist, encoding="utf-8").read(), flags=re.M)]

def glossary():
    G = {}
    p = os.path.join(SKILL, "references", "glossary.txt")
    for ln in open(p, encoding="utf-8") if os.path.exists(p) else []:
        if "<-" in ln and not ln.startswith("#"):
            right, wrong = ln.split("<-"); [G.__setitem__(w.strip().lower(), right.strip()) for w in wrong.split(",") if w.strip()]
    return G

def placed(words, R):
    """the cut's words on the cut's timeline, grouped by script line: [[(word, s, e), ...], script line]"""
    out = []
    for t, a, b, line in R:
        ws = [(w["w"], round(t + max(w["s"], a) - a, 3), round(t + min(w["e"], b) - a, 3)) for w in words
              if min(w["e"], b) - max(w["s"], a) >= min(0.08, 0.5 * max(0.01, w["e"] - w["s"]))]
        if line.startswith("(same line") and out: out[-1][0].extend(ws)
        else: out.append([ws, line])
    return out

def hear(video, cache):
    """the video's own words on its own timeline: [{w, s, e}]"""
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(video): return json.load(open(cache, encoding="utf-8"))
    try: import av                                                     # faster-whisper imports av only to read files; on a machine
    except ImportError: sys.modules["av"] = type(sys)("av")            # whose policy blocks av's DLL, the audio goes in as an array
    from faster_whisper import WhisperModel
    import numpy as np
    x = np.frombuffer(subprocess.run([FF, "-v", "error", "-i", video, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout,
                      np.int16).astype(np.float32) / 32768
    segs, _ = WhisperModel("small.en", device="cpu", compute_type="int8").transcribe(x, language="en", beam_size=5, word_timestamps=True,
                                                                                     condition_on_previous_text=False)
    W = [dict(w=w.word.strip(), s=round(w.start, 3), e=round(w.end, 3)) for sg in segs for w in (sg.words or []) if w.word.strip()]
    json.dump(W, open(cache, "w", encoding="utf-8")); return W

def heard_groups(W, R):
    """the heard words grouped by script line: each word goes to the cut list row its middle falls in"""
    out, starts = [], [t for t, _, _, _ in R]
    for k, (t, a, b, line) in enumerate(R):
        end = starts[k + 1] if k + 1 < len(starts) else 1e9
        ws = [(w["w"], w["s"], w["e"]) for w in W if t <= (w["s"] + w["e"]) / 2 < end]
        if line.startswith("(same line") and out: out[-1][0].extend(ws)
        else: out.append([ws, line])
    return out

def respell(group, line, G):
    """what was said, spelled as the script spells it"""
    said = [w for w, _, _ in group]; sc = re.findall(r"[\w'.:/-]+", line.replace("’", "'")); a = [norm(x) for x in said]; b = [norm(x) for x in sc]   # "I’ll" is one word
    fixed = list(said)
    from spellchecker import SpellChecker
    known = SpellChecker()                                      # a real word that differs from the script was said: keep it
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):
            for i, j in zip(range(i1, i2), range(j1, j2)):
                if op == "equal" or (said[i].lower().strip(".,:;!?") not in known and difflib.SequenceMatcher(None, a[i], b[j]).ratio() >= 0.6):
                    lead, tail = re.match(r"^(\W*)", said[i]).group(1), re.search(r"(\W*)$", said[i]).group(1)
                    word = sc[j].strip(".,:;!?")
                    name = any(ch.isupper() for ch in word[1:]) or (word[:1].isupper() and j > 0 and not re.search(r"[.?!]$", sc[j - 1]))
                    if a[i] != b[j] or name: fixed[i] = lead + word + tail          # the script's spelling, and its capitals only for a name
    for i, w in enumerate(fixed):
        k = norm(w)
        if k in G: fixed[i] = re.sub(r"[\w']+", G[k], w, count=1)
        if re.search(r"['’]s\W*$", said[i]) and not re.search(r"['’]s\W*$", fixed[i]):          # "Quadrant's" is "Qdrant's", not "Qdrant"
            fixed[i] = re.sub(r"(\W*)$", r"'s\1", fixed[i], count=1)
    return [(f, s, e) for f, (_, s, e) in zip(fixed, group)]

def sentence_case(words):
    """every sentence starts with a capital, whatever the transcript wrote; "self -hosting" is one word"""
    joined = []
    for w, s, e in words:
        if (w.startswith("-") or re.match(r"^\.[a-z]{2,6}\b", w, flags=re.I)) and joined:
            p = joined[-1]; t = p[0] + w
            joined[-1] = (t.lower() if re.match(r"^\w+\.[a-z]{2,6}\W*$", t, flags=re.I) else t, p[1], e)   # "Qdrant .Tech" is qdrant.tech
        else: joined.append((w, s, e))
    words, out = joined, []
    for k, (w, s, e) in enumerate(words):
        if k == 0 or re.search(r"[.?!]$", words[k - 1][0]): w = w[:1].upper() + w[1:]
        out.append((w, s, e))
    return out

def cues(words, chars, lines, min_s, max_s, cps):
    """words -> [(start, end, [line, ...])], broken at a full stop, then a comma or a pause, within the limits"""
    out, cur = [], []
    def flush():
        if not cur: return
        text = " ".join(w for w, _, _ in cur); out.append([cur[0][1], cur[-1][2], text]); cur.clear()
    for k, (w, s, e) in enumerate(words):
        if cur:
            text = " ".join(x for x, _, _ in cur + [(w, s, e)]); span = e - cur[0][1]
            if max(len(x) for x in split(text, chars, lines)) > chars or span > max_s:     # it must still split into lines that fit
                k = max((i for i, (x, _, _) in enumerate(cur[:-1]) if re.search(r"[,;:]$", x)), default=None)
                if k is not None and k >= 2 and len(" ".join(x for x, _, _ in cur[:k + 1])) >= 0.4 * chars * lines: rest = cur[k + 1:]; del cur[k + 1:]; flush(); cur.extend(rest)   # full: break at its last comma
                else: flush()
            elif re.search(r"[.?!]$", cur[-1][0]): flush()
            elif (re.search(r"[,;:]$", cur[-1][0]) or s - cur[-1][2] > 0.4) and len(" ".join(x for x, _, _ in cur)) > 0.55 * chars * lines: flush()
        cur.append((w, s, e))
    flush()
    res = []
    for k, (s, e, text) in enumerate(out):
        nxt = out[k + 1][0] if k + 1 < len(out) else e + 2
        e = min(max(e + 0.2, s + min_s, s + len(text) / cps), nxt - 0.04)   # long enough to read, never over the next one
        res.append((s, e, split(text, chars, lines)))
    return res

def split(text, chars, lines):
    if len(text) <= chars or lines == 1: return [text]
    ws = text.split(); best = None
    for i in range(1, len(ws)):
        a, b = " ".join(ws[:i]), " ".join(ws[i:])
        if len(a) <= chars and len(b) <= chars:
            score = abs(len(a) - len(b)) - (8 if re.search(r"[,.;:]$", ws[i - 1]) else 0)
            if best is None or score < best[0]: best = (score, [a, b])
    return best[1] if best else [text]

def tc(t, sep=","): return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d}{sep}{int(round(t * 1000)) % 1000:03d}"

def write_srt(C, p): open(p, "w", encoding="utf-8").write("\n".join(f"{i + 1}\n{tc(s)} --> {tc(e)}\n" + "\n".join(L) + "\n" for i, (s, e, L) in enumerate(C)))
def write_vtt(C, p): open(p, "w", encoding="utf-8").write("WEBVTT\n\n" + "\n".join(f"{tc(s, '.')} --> {tc(e, '.')}\n" + "\n".join(L) + "\n" for s, e, L in C))

def write_ass(C, p, W, H, st, words=None):
    size = int(round(st["text_height"] * H * 1.25)); margin = int(round((1 - st["y"]) * H - size * 0.6))
    hl = st.get("highlight") and words
    head = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\nWrapStyle: 2\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: Cap,Mona Sans,{size},&H00FFFFFF,&H00FFFFFF,&H00241A0B,&H8C1A0F0B,-1,0,0,0,100,100,0,0,3,{max(2, size // 6)},0,2,60,60,{margin},1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    ev = []
    for s, e, L in C:
        text = "\\N".join(L).upper() if st.get("caps") else "\\N".join(L)
        if not hl:
            ev.append(f"Dialogue: 0,{tc(s, '.')[1:-1]},{tc(e, '.')[1:-1]},Cap,,0,0,0,,{text}"); continue
        ws = [w for w in words if s - 0.01 <= w[1] < e]                                  # the word being said, in the brand red
        for k, (w, ws_, we) in enumerate(ws):
            a = ws_; b = ws[k + 1][1] if k + 1 < len(ws) else e
            parts = [("{\\c&H4C24DC&}" + x[0] + "{\\c&HFFFFFF&}") if j == k else x[0] for j, x in enumerate(ws)]
            line = " ".join(parts); ev.append(f"Dialogue: 0,{tc(a, '.')[1:-1]},{tc(b, '.')[1:-1]},Cap,,0,0,0,,{line.upper() if st.get('caps') else line}")
    open(p, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video"); ap.add_argument("--cutlist", required=True); ap.add_argument("--words", help="the take's transcript placed through the cut list, instead of hearing VIDEO"); ap.add_argument("--script")
    ap.add_argument("--out", required=True); ap.add_argument("--burn", action="store_true"); ap.add_argument("--style", default=os.path.join(SKILL, "references", "caption_style.json"))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); G = glossary()
    st = json.load(open(a.style, encoding="utf-8")); R = rows(a.cutlist)
    groups = placed(json.load(open(a.words, encoding="utf-8")), R) if a.words else heard_groups(hear(a.video, os.path.join(a.out, "heard.json")), R)
    words = [w for g, line in groups for w in respell(g, line if not line.startswith("(") else "", G)]
    words = sentence_case(sorted(words, key=lambda w: w[1]))
    C = cues(words, **SRT_RULES); write_srt(C, os.path.join(a.out, "captions.srt")); write_vtt(C, os.path.join(a.out, "captions.vtt"))
    B = cues(words, st["chars"], st["lines"], st["min_s"], st["max_s"], st["cps"])
    import cv2
    v = cv2.VideoCapture(a.video); Wd, H = int(v.get(3)), int(v.get(4)); v.release()
    write_ass(B, os.path.join(a.out, "captions.ass"), Wd, H, st, words)
    print(f"{len(words)} words, {sum(1 for w, _, _ in words if 'Qdrant' in w)} spelled Qdrant; {len(C)} subtitles (SRT/VTT), {len(B)} burned-in captions")
    if a.burn:
        out = os.path.join(a.out, "captioned.mp4"); fonts = FONTS.replace("\\", "/").replace(":", "\\:")
        subprocess.run([FF, "-v", "error", "-y", "-i", os.path.abspath(a.video), "-vf", f"subtitles=captions.ass:fontsdir='{fonts}'", "-c:v", "libx264", "-crf", "18",
                        "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", "captioned.mp4"], check=True, cwd=a.out)
        print("->", out)

if __name__ == "__main__":
    main()
