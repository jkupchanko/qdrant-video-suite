"""raw_edit_checks.py: does the raw edit read as one clean pass? Every thought said once, no restart left in, no stop in the
middle of a sentence, no glance away with words over it, nothing dropped from the middle of a line.

  python raw_edit_checks.py TAKE.mp4 CUTLIST.md --literal WORDS_LITERAL.json [--gaze RAW_GAZE.json] [--out report.md]
  checks(take, cutlist, literal, gaze=None, cut=None) -> ([dict(t, kind, sev, msg)], speaker)

These are the faults a presenter flagged, one at a time, on the Get Started raw edit (2026-10-22): a sentence started,
stopped and said again ("Now this can be useful if you want more of a... / Now this can be useful..." at 1:24), a stop in
the middle of a sentence (1:32), a glance away with a word or two over it (0:33, 2:44, 2:33), and a list item lost from the
middle of a line ("run requests" dropped from "explore the clusters, manage collections, run requests, and follow...").

No number in here is a constant for everyone. People pause, glance and restart differently, so every threshold is
measured on this speaker's own take first (`speaker()`): their normal pause between words, their eyes' resting place and
spread, their room's quiet and voice levels. A fast talker's 0.3 s stop is a stop; a slow talker's is a breath.

The words come from transcribe_literal.py (the editing skill), which writes every attempt where it was said. Whisper's
default transcript tidies a restart into one clean sentence, so a check on it cannot see one. Before words are called
dropped, the cut itself is heard over that line (hear_cut): the take's transcript says where words were said, only the
cut's own sound says what the viewer hears.
"""
import os, re, json, sys, numpy as np
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "video-review", "scripts"))   # join_checks

STOP = set("a an the to of and or but so in on at for with as by from that this is are was be it you we i your our my can will just then now also".split())
CUTOFF = set("a an the to of and or but in on at for with as by from your our my".split())   # a sentence cannot end here
# ("this", "that", "is", "are", "be" can: "we've got this", "what generics are", "the more specific you can be" - 49 pro videos)

def norm(w): return re.sub(r"[^a-z0-9']", "", w.lower())
def ends(w): return bool(re.search(r"[.?!]$", w))
def ts(t): return f"{int(t // 60)}:{t % 60:04.1f}"

_EAR = []
def hear_cut(cut, t0, t1):
    """the cut's own words between t0 and t1 (edit time): what a viewer hears. The take's transcript, placed through the cut
    list, smears around a restart: on Get Started (5:18) it put "Make sure you subscribe" outside the piece that holds it,
    and a person was told the words were not in the cut when they were."""
    import subprocess, imageio_ffmpeg
    try: import av                                                     # faster-whisper imports av only to read files; where a policy
    except ImportError: sys.modules["av"] = type(sys)("av")            # blocks av's DLL, the audio goes in as an array
    if not _EAR:
        from faster_whisper import WhisperModel
        _EAR.append(WhisperModel("small.en", device="cpu", compute_type="int8"))
    t0 = max(0.0, t0)
    x = np.frombuffer(subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{max(0.5, t1 - t0):.3f}", "-i", cut, "-ac", "1",
                                      "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout, np.int16).astype(np.float32) / 32768
    segs, _ = _EAR[0].transcribe(x, language="en", beam_size=5, word_timestamps=True, condition_on_previous_text=False)
    return [dict(w=w.word.strip(), s=round(t0 + w.start, 2), e=round(t0 + w.end, 2)) for sg in segs for w in (sg.words or []) if w.word.strip()]

def heard_cut(cut):
    """the whole cut heard once, kept next to it (heard_cut.json) until the cut changes"""
    p = os.path.join(os.path.dirname(os.path.abspath(cut)), "heard_cut.json")
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        if d.get("mtime") == os.path.getmtime(cut): return d["words"]
    import subprocess, imageio_ffmpeg
    dur = len(subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", cut, "-ac", "1", "-ar", "100", "-f", "u8", "-"], capture_output=True).stdout) / 100
    W = hear_cut(cut, 0.0, dur + 0.5); json.dump(dict(mtime=os.path.getmtime(cut), words=W), open(p, "w", encoding="utf-8")); return W

def said_twice(take, R, key, cache):
    """words a cut says twice across a join ("run requests in... / run requests and follow" at 2:36 of Get Started): the
    end of each piece and the start of the next are heard apart, so nothing tidies the repeat away. Whisper over the whole
    cut writes that moment "run requests, and follow" once, and the take's transcript wrote it once too; only the two
    sides heard on their own show it. A repeat of two words or more with a word that is not a filler ("you can" is a list,
    not a restart); the fix ends the first piece before the repeated words, or drops it when it is nothing else."""
    C = json.load(open(cache, encoding="utf-8")) if os.path.exists(cache) else {}
    spans = {"tails": [(max(a, b - 2.5), b) for _, a, b, _ in R[:-1]], "heads": [(a, min(b, a + 2.5)) for _, a, b, _ in R[1:]]}
    need = {g: [sp for sp in v if f"{sp[0]:.2f}-{sp[1]:.2f}" not in C] for g, v in spans.items()}
    if any(need.values()):                                               # all the ends in one stream and all the starts in another,
        import subprocess, imageio_ffmpeg                                # 1 s of silence apart: two transcriptions, not one per side,
        x = np.frombuffer(subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", take, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                                         capture_output=True).stdout, np.int16).astype(np.float32) / 32768      # and the two sides of a join are
        # never in one stream, so nothing tidies a repeat away
        try: import av
        except ImportError: sys.modules["av"] = type(sys)("av")
        if not _EAR:
            from faster_whisper import WhisperModel
            _EAR.append(WhisperModel("small.en", device="cpu", compute_type="int8"))
        for g, sps in need.items():
            if not sps: continue
            parts, offs, o = [], [], 0.0
            sps = sorted(sps, key=lambda sp: (spans[g].index(sp) % 9, spans[g].index(sp)))   # neighbours in the stream are 9 joins apart: two
            for a, b in sps:                                                                 # pieces that open alike never share a window
                clip = x[int(a * 16000):int(b * 16000)]; parts += [clip, np.zeros(16000, np.float32)]; offs.append((o, o + len(clip) / 16000, a, b)); o += len(clip) / 16000 + 1.0
            segs, _ = _EAR[0].transcribe(np.concatenate(parts), language="en", beam_size=5, word_timestamps=True, condition_on_previous_text=False)
            ws = [w for sg in segs for w in (sg.words or []) if w.word.strip()]
            for o0, o1, a, b in offs:
                C[f"{a:.2f}-{b:.2f}"] = [dict(w=w.word.strip(), s=round(a + w.start - o0, 2)) for w in ws if o0 <= (w.start + w.end) / 2 < o1]
    side = lambda a, b: C[f"{a:.2f}-{b:.2f}"]
    out = []
    for k in range(len(R) - 1):
        t, a, b, _ = R[k]; a2, b2 = R[k + 1][1], R[k + 1][2]
        tail = side(max(a, b - 2.5), b); head = side(a2, min(b2, a2 + 2.5))
        tn, hn = [norm(w["w"]) for w in tail], [norm(w["w"]) for w in head]
        hit = None                     # the next piece opens (from its first or second word: a clip can lose its first) with words
        for n in range(min(6, len(hn)), 1, -1):                   # the end of this piece already said, and that end is a false
            for j in (0, 1):                                      # start, not a finished sentence ("look at Qdrant Cloud." /
                ph = hn[j:j + n]                                  # "With Qdrant Cloud" is two sentences, not a restart)
                if len(ph) < n or not all(ph) or not any(x not in STOP for x in ph): continue
                at = next((i for i in range(len(tn) - n + 1) if tn[i:i + n] == ph and i + n >= len(tn) - 2), None)
                after = [norm(w) for w in tn[at + n:] if w] if at is not None else []         # a false start stops there or on a
                if at is not None and not ends(tail[-1]["w"]) and not ends(tail[at + n - 1]["w"]) and all(w in CUTOFF or w in STOP for w in after):
                    hit = (at, n, j); break                                                # little word; "or maybe a mount, / or maybe a
                                                                                           # balance" finishes an item: a list on purpose
            if hit: break
        if hit:
            at, n, j = hit; s_occ = tail[at]["s"]; t_occ = t + s_occ - a
            edit = {key(k): None} if s_occ - a < 0.3 else {key(k): [(a, round(float(s_occ) - 0.04, 2))]}
            out.append(dict(t=t_occ, kind="restart", sev="fix", edit=edit,
                            msg=f'said twice across a join: "{" ".join(w["w"] for w in tail[at:at + n])}" at {ts(t_occ)} and again at {ts(R[k + 1][0])} (heard in the cut; keep the second)'))
    json.dump(C, open(cache, "w", encoding="utf-8")); return out

def rows(cutlist):
    """(edit time, source in, source out, line) per piece, in edit order"""
    t = open(cutlist, encoding="utf-8").read()
    return [(float(a), float(b), float(c), d.strip()) for a, b, c, d in re.findall(r"^\| ([\d.]+) \| ([\d.]+)-([\d.]+) \| x[\d.]+ \| (.*?) \|", t, flags=re.M)]

def quiet_runs(voiced, t0=0.0):
    """(start, end) in seconds of every quiet stretch of a 10 ms voiced mask"""
    out, s = [], None
    for i, x in enumerate(list(voiced) + [True]):
        if not x and s is None: s = i
        if x and s is not None: out.append((t0 + s / 100, t0 + i / 100)); s = None
    return out

def speaker(words, env, quiet, gaze=None):
    """this speaker's own norms, from the whole take. Pauses come from the sound: a literal transcript's word times run
    into each other (no gaps), so they cannot measure a pause"""
    starts = [w["s"] for w in words]; mid = []
    for a, b in quiet_runs(env > quiet):
        k = int(np.searchsorted(starts, a)) - 1
        if 0.1 <= b - a < 3 and k >= 0 and not re.search(r"[.,?!]$", words[k]["w"]) and k + 1 < len(words) and words[k + 1]["s"] >= b - 0.3:
            mid.append(b - a)                                                  # (a quiet stretch inside a word Whisper stretched is no pause)
    # the fluent pause: a raw take is full of stops to think (Get Started: median 0.52 s over all pauses inside a sentence),
    # so only the ones under 1 s say how this person speaks (0.29 s). In 49 finished pro videos the median is 0.14 s and
    # 90% of their pauses inside a sentence stay under 0.28 s; 90% of the videos never leave one over 0.46 s
    fluent = [x for x in mid if x < 1.0]; m = float(np.median(fluent)) if fluent else 0.3
    S = dict(pause=m,                       # their typical pause inside a sentence (breath, a beat before a key word)
             stop=max(0.5, 2 * m),          # longer than this inside a sentence, heard in the cut: a stop
             phrase_gap=0.25)               # literal words further apart than this: a new phrase
    if gaze:
        fr = [f for f in gaze["frames"] if f.get("face")]
        for k in ("h", "v"):
            x = np.array([f[k] for f in fr]); m = float(np.median(x)); S[k] = (m, max(1e-3, 1.4826 * float(np.median(np.abs(x - m)))))
        S["fps"] = 1 / max(1e-3, float(np.median(np.diff([f["t"] for f in fr]))))
    return S

def inside(w, a, b):
    """a word is in a piece if enough of it is: a word Whisper stretched over a pause ("follow" from 934.5 to 936.9 s)
    has its middle in the pause, outside the piece that holds its sound"""
    if w["e"] - w["s"] < 0.05: return a <= w["s"] <= b                     # a word given no length ("manage@135.0-135.0")
    return min(w["e"], b) - max(w["s"], a) >= min(0.15, 0.5 * (w["e"] - w["s"]))

def same(a, b): return a == b or (len(a) > 3 and len(b) > 3 and (a.startswith(b) or b.startswith(a)))

def checks(take, cutlist, literal, gaze=None, cut=None, raw=None):
    """cut: the cut itself (default: cut.mp4 next to the cut list). Words the take's transcript says the cut left out are
    listened for in the cut before they are reported: a smeared transcript must not put back words the cut already has"""
    if cut is None and isinstance(cutlist, str): cut = os.path.join(os.path.dirname(os.path.abspath(cutlist)), "cut.mp4")
    if cut and not os.path.exists(cut): cut = None
    W = json.load(open(literal, encoding="utf-8")) if isinstance(literal, str) else literal
    G = json.load(open(gaze, encoding="utf-8")) if isinstance(gaze, str) else gaze
    import join_checks as JC
    env, quiet, _ = JC.envelope(take) if isinstance(take, str) else take
    S = speaker(W, env, quiet, G); R = rows(cutlist); out = []
    vo = lambda a, b: env[int(round(a * 100)):int(round(b * 100))] > quiet
    # each finding carries its fix as new source spans for the pieces it touches ({edit time: [(in, out), ...]}, None to
    # drop the piece), every cut point placed in this take's own quiet; fix_cut.py (editing) applies them with respan.py
    key = lambda k: f"{R[k][0]:.2f}"
    def gap(x0, x1):
        """the longest quiet stretch in [x0, x1] of the take: where two attempts part"""
        q = quiet_runs(vo(x0, x1), x0)
        return max(q, key=lambda r: r[1] - r[0]) if q else ((x0 + x1) / 2, (x0 + x1) / 2)
    def phrase(x0, x1):
        """[x0, x1] grown out to a pause of at least half this speaker's pause on each side: the whole phrase"""
        lo, hi = int(round(x0 * 100)), int(round(x1 * 100)); n = int(max(0.25, S["pause"] / 2) * 100)
        while lo > n and (env[lo - n:lo] > quiet).any(): lo -= 1
        while hi < len(env) - n and (env[hi:hi + n] > quiet).any(): hi += 1
        return round(lo / 100 - 0.04, 2), round(hi / 100 + 0.04, 2)
    # the cut as heard: every kept word, at its edit time, with the join it follows
    kept = []
    for k, (t, a, b, line) in enumerate(R):
        for w in W:
            if inside(w, a, b): kept.append(dict(w=w["w"], n=norm(w["w"]), s=w["s"], e=w["e"], et=t + w["s"] - a, piece=k, first=False))
        ks = [x for x in kept if x["piece"] == k]
        if ks: ks[0]["first"] = True
    # 1. a restart left in: a phrase start said again a few words later, at another phrase start. A list says its opening
    #    words again on purpose ("you can run it locally, you can deploy it"), so the first try must be cut off (three
    #    words or fewer, or ending on a word a sentence cannot end on) or match three words, not two
    def starts(i): return i == 0 or kept[i]["first"] or kept[i]["s"] - kept[i - 1]["e"] > S["phrase_gap"] or re.search(r"[,.?!…-]$", kept[i - 1]["w"])
    i = 0
    while i < len(kept) - 3:
        hit = None
        if starts(i) and kept[i]["n"] and kept[i]["n"] not in ("and", "so", "but"):        # "and so..." opens many sentences
            for j in range(i + 2, min(len(kept) - 1, i + 14)):                               # an attempt dropped after up to a dozen words
                if not starts(j) or not (same(kept[i]["n"], kept[j]["n"]) and same(kept[i + 1]["n"], kept[j + 1]["n"])): continue
                three = j + 2 < len(kept) and i + 2 < j and same(kept[i + 2]["n"], kept[j + 2]["n"])
                if j - i <= 3 or kept[j - 1]["n"] in CUTOFF or three: hit = j; break
        # sure (fixed by itself) only when the second try repeats ALL of the first ("for the first, / for the first cluster")
        # or the first stops on a word a sentence cannot end on ("just add Quadrant to the,"). Anything else may be said on
        # purpose ("it can diagnose, it can assemble, it can assess"), so it is shown to a person, never cut by itself
        if hit:
            said = " ".join(x["w"] for x in kept[i:hit]); again = " ".join(x["w"] for x in kept[hit:hit + 4])
            pi, ph = kept[i]["piece"], kept[hit]["piece"]; a_i, b_i = R[pi][1], R[pi][2]; a_h, b_h = R[ph][1], R[ph][2]
            g0 = gap(kept[i - 1]["s"], kept[i]["s"] + 0.1) if i and not kept[i]["first"] else None        # where the first try begins
            g1 = gap(kept[hit - 1]["s"], kept[hit]["s"] + 0.1)                                              # where the second try begins
            if pi == ph: edit = {key(pi): ([(a_i, round(g0[0] + 0.04, 2))] if g0 else []) + [(round(g1[1] - 0.04, 2), b_h)]}
            else:
                edit = {key(pi): [(a_i, round(g0[0] + 0.04, 2))] if g0 else None}
                edit.update({key(k): None for k in range(pi + 1, ph)})
                if not kept[hit]["first"]: edit[key(ph)] = [(round(g1[1] - 0.04, 2), b_h)]
            whole = all(same(kept[i + q]["n"], kept[hit + q]["n"]) for q in range(hit - i) if hit + q < len(kept)) and                     (hit - i >= 3 or not ends(kept[hit - 1]["w"]))          # "the server. / The server will..." is said on purpose
            sure = whole or kept[hit - 1]["n"] in CUTOFF or re.search(r"[-…]$", kept[hit - 1]["w"])   # three words alone are not sure:
            # in 49 pro videos the 30 left were two whole sentences opening alike ("It could be changed. / It could be made")
            out.append(dict(t=kept[i]["et"], kind="restart", sev="fix" if sure else "check", edit=edit, msg=f'said twice: "{said}" then "{again}..." (a restart left in; keep the second try)'))
            i = hit
        i += 1
    # 2. a stop inside a sentence: a silence heard in the cut (inside a piece, or a piece's tail plus the next one's head)
    #    after a word that does not end the sentence, longer than this speaker's own pause inside a sentence
    heard = np.concatenate([vo(a, b) for _, a, b, _ in R]); src = np.concatenate([np.arange(int(round(a * 100)), int(round(a * 100)) + len(vo(a, b))) / 100 for _, a, b, _ in R])
    for qa, qb in quiet_runs(heard):
        if qa == 0 or qb >= len(heard) / 100: continue
        n = qb - qa; at = src[min(len(src) - 1, int(round(qa * 100)))]
        before = [w for w in W if w["s"] < at - 0.02]
        if not before: continue
        w = before[-1]
        if ends(w["w"]) or (w["w"].endswith(",") and n < 1.5 * S["stop"]) or n <= S["stop"]: continue
        k1 = int(np.searchsorted(np.cumsum([len(vo(a, b)) for _, a, b, _ in R]), int(round(qa * 100)), side="right")); k2 = int(np.searchsorted(np.cumsum([len(vo(a, b)) for _, a, b, _ in R]), int(round(qb * 100)) - 1, side="right"))
        s_a = float(src[min(len(src) - 1, int(round(qa * 100)))]); s_b = float(src[min(len(src) - 1, int(round(qb * 100)))]); keep = min(0.15, S["pause"] / 2)
        edit = ({key(k1): [(R[k1][1], round(s_a + keep, 2)), (round(s_b - keep, 2), R[k1][2])]} if k1 == k2 else
                {key(k1): [(R[k1][1], round(s_a + keep, 2))], key(k2): [(round(s_b - keep, 2), R[k2][2])]}) if k2 < len(R) else None
        out.append(dict(t=qa, kind="stop", sev="fix" if n > 2 * S["stop"] else "check", edit=edit,
                        msg=f'a {n:.2f} s stop in the middle of a sentence, after "{w["w"]}" (this speaker pauses about {S["pause"]:.2f} s inside a sentence)'))
    # 3. words lost from the middle of a line: words of the script line that were said in the take, between that line's
    #    pieces, but are not in the cut. A retake or an aside between pieces is not a loss; a list item the script has is
    groups = []
    for k, r in enumerate(R):
        if r[3].startswith("(same line") and groups: groups[-1].append(k)
        else: groups.append([k])
    for g in groups:
        script_line = R[g[0]][3]
        said = {x["n"] for x in kept if x["piece"] in g}
        want = [n for n in dict.fromkeys(norm(w) for w in script_line.split()) if n and n not in STOP and not any(same(n, x) for x in said)]
        lost, edit = [], {}
        for k0, k1 in zip(g, g[1:]):
            between = [w for w in W if inside(w, R[k0][2], R[k1][1]) and not inside(w, R[k0][1], R[k0][2]) and not inside(w, R[k1][1], R[k1][2])]
            here = [w for w in between if any(same(norm(w["w"]), n) for n in want)]
            if not here or edit: lost += here; continue
            lost += here; x0, x1 = phrase(here[0]["s"], here[-1]["e"]); x0, x1 = max(x0, R[k0][2]), min(x1, R[k1][1])
            ph = {norm(w["w"]) for w in W if inside(w, x0, x1)}; prev = [x["n"] for x in kept if x["piece"] == k0 and x["n"] not in STOP]
            if prev and all(any(same(n, q) for q in ph) for n in prev): edit = {key(k0): [(x0, x1)]}   # a fuller retake of the piece before
            else: edit = {key(k1): [(x0, x1), (R[k1][1], R[k1][2])]}                                   # the missing words, then the piece
        if lost:
            names = list(dict.fromkeys(w["w"].strip(",.") for w in lost))
            if cut:                                                         # listen to the cut over this line's pieces
                t_end = R[g[-1]][0] + R[g[-1]][2] - R[g[-1]][1]
                heard = [norm(w["w"]) for w in heard_cut(cut) if R[g[0]][0] - 0.5 <= w["s"] <= t_end + 0.5]
                names = [n for n in names if not any(same(norm(n), h) for h in heard if h)]
                if not names: continue                                     # the cut says them: the transcript was wrong, not the cut
            out.append(dict(t=R[g[0]][0], kind="dropped", sev="fix", edit=edit or None,
                            msg=f'"{", ".join(names)}" is in the script line and was said (source {lost[0]["s"]:.1f} s), but the cut leaves it out: "{script_line[:80]}"'))
    # 4. the eyes, against this speaker's own resting place: a glance is the eyes leaving it by 3 of their own spreads for
    #    a quarter of a second, or a stop followed by any move off it at a piece's edge (a thought, then the eyes go)
    if G:
        fr = [f for f in G["frames"] if f.get("face")]
        T = np.array([f["t"] for f in fr]); Z = np.sqrt(sum(((np.array([f[k] for f in fr]) - S[k][0]) / S[k][1]) ** 2 for k in ("h", "v")))
        for k, (t, a, b, line) in enumerate(R):
            idx = np.where((T >= a) & (T <= b))[0]                                # 0.3 s: a blink or a nod is shorter; idx = np.where(m)[0]
            if not len(idx): continue
            run = []
            for q in list(idx) + [None]:
                if q is not None and Z[q] > 3.0: run.append(q); continue
                if run and T[run[-1]] - T[run[0]] + 1 / S["fps"] >= 1.0:      # pros glance 14 times a minute, 95% under 1.3 s
                    over = [x["w"] for x in kept if x["piece"] == k and T[run[0]] - 0.1 <= x["s"] <= T[run[-1]] + 0.1]
                    out.append(dict(t=t + T[run[0]] - a, kind="glance", sev="check",
                                    msg=f"eyes off their resting place for {T[run[-1]] - T[run[0]] + 1 / S['fps']:.2f} s" + (f' over "{" ".join(over)}"' if over else "") + " (source {:.1f} s)".format(T[run[0]])))
                run = []
            ks = [x for x in kept if x["piece"] == k]
            if not ks: continue
            last = ks[-1]; v = vo(a, b); vend = a + (np.where(v)[0][-1] + 1) / 100 if v.any() else b; tail = b - vend
            after = next((w["s"] for w in W if w["s"] > last["e"] + 0.02), b + 9) - last["e"]
            if norm(last["w"]) in CUTOFF and not re.search(r"[,.?!]$", last["w"]) and after > 2 * S["stop"] and tail > 0.12:   # stopped mid-thought to think: the eyes go next
                zt = Z[(T > last["e"]) & (T <= b)]
                if len(zt) and zt.max() > 1.5:
                    out.append(dict(t=t + last["e"] - a, kind="glance", sev="fix", edit={key(k): [(a, round(float(vend) + 0.04, 2))]},
                                    msg=f'the piece runs {tail:.2f} s past "{last["w"]}" into a {after:.1f} s thinking pause, and the eyes start to leave the lens there; end it on the word'))
    out.sort(key=lambda d: d["t"])
    raw = take if isinstance(take, str) else raw                        # (fix_cut passes the envelope; it skipped this, Get Started 10-28)
    if cut and raw:                                                     # a restart the transcript wrote once, heard in the cut
        for f in said_twice(raw, R, key, os.path.join(os.path.dirname(os.path.abspath(cut)), "heard_joins.json")):
            if not any(o["kind"] == "restart" and abs(o["t"] - f["t"]) < 3 for o in out): out.append(f)
    return out, S

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("take"); ap.add_argument("cutlist"); ap.add_argument("--literal", required=True); ap.add_argument("--gaze"); ap.add_argument("--out")
    a = ap.parse_args(); F, S = checks(a.take, a.cutlist, a.literal, a.gaze)
    head = f"speaker: pauses about {S['pause']:.2f} s inside a sentence, so a stop is over {S['stop']:.2f} s" + (f"; eyes rest at h {S['h'][0]:.2f} ± {S['h'][1]:.3f}, v {S['v'][0]:.2f} ± {S['v'][1]:.3f}" if "h" in S else "")
    lines = [head] + [f"{ts(f['t'])}  {f['sev']:5s} {f['kind']:8s} {f['msg']}" for f in F]
    print("\n".join(lines))
    if a.out: open(a.out, "w", encoding="utf-8").write("# Raw edit check\n\n" + "\n".join(f"- {l}" for l in lines) + "\n")
