#!/usr/bin/env python
"""checks.py: the captions and the voice, checked before anyone watches.

  python checks.py --srt captions.srt [--voice voice.json]      -> findings, one a line; exit 1 if anything is to fix
  srt_findings(path) / voice_findings(report) -> [dict(t, kind, sev, msg)]

captions   a brand or script term spelled the way the transcript heard it ("Quadrant": fix); a cue faster to read than
           20 characters a second and 1.3 times this speaker's own pace (check: a fast talker's captions cannot be slower
           than the talk, so only a crammed cue is flagged); a cue under
           0.8 s (check); a line over 42 characters or more than 2 lines (fix); cues that overlap (fix)
voice      a level jump over 3 dB left between two pieces after voice_clean.py (check); the voice under 30 dB above the
           room after it (check); a length change of more than one sample (fix: the voice would drift off the lips)
"""
if __name__ == "__main__":                                   # run on the suite's own Python (.venv, made by setup.py), whichever python started it
    import os as _o, sys as _s, subprocess as _sp
    _v = _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), "..", "..", "..", ".venv", *(("Scripts", "python.exe") if _o.name == "nt" else ("bin", "python")))
    if _o.path.exists(_v) and _o.path.normcase(_o.path.realpath(_s.prefix)) != _o.path.normcase(_o.path.realpath(_o.path.dirname(_o.path.dirname(_v)))):
        _s.exit(_sp.call([_v, _o.path.realpath(__file__)] + _s.argv[1:]))
import argparse, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE)
LIMITS = dict(cps_check=20.0, min_s=0.8, chars=42, lines=2, jump_db=3.0, snr_db=30.0)

def glossary_wrong():
    p = os.path.join(SKILL, "references", "glossary.txt"); bad = {}
    for ln in open(p, encoding="utf-8") if os.path.exists(p) else []:
        if "<-" in ln and not ln.startswith("#"):
            right, wrong = ln.split("<-"); [bad.__setitem__(w.strip().lower(), right.strip()) for w in wrong.split(",") if w.strip()]
    return bad

def parse_srt(path):
    out = []
    for block in re.split(r"\n\s*\n", open(path, encoding="utf-8").read().strip()):
        m = re.search(r"(\d+):(\d+):(\d+)[,.](\d+) --> (\d+):(\d+):(\d+)[,.](\d+)\n(.*)", block, flags=re.S)
        if not m: continue
        g = [int(x) for x in m.groups()[:8]]; s = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000; e = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        out.append((s, e, m.group(9).strip().splitlines()))
    return out

def srt_findings(path):
    C = parse_srt(path); bad = glossary_wrong(); F = []
    import numpy as np                                          # reading speed against this speaker: a fast talker's captions
    pace = float(np.median([len(" ".join(L)) / max(0.3, e - s) for s, e, L in C])) if C else 15.0   # cannot be slower than the talk
    fast = max(LIMITS["cps_check"], 1.3 * pace)
    for k, (s, e, L) in enumerate(C):
        text = " ".join(L); d = max(1e-3, e - s)
        for w in re.findall(r"[\w'-]+", text):
            if w.lower() in bad and w != bad[w.lower()]: F.append(dict(t=s, kind="spelling", sev="fix", msg=f'"{w}" should read "{bad[w.lower()]}": "{text[:60]}"'))
        if len(L) > LIMITS["lines"]: F.append(dict(t=s, kind="lines", sev="fix", msg=f"{len(L)} lines; at most {LIMITS['lines']}"))
        for ln in L:
            if len(ln) > LIMITS["chars"]: F.append(dict(t=s, kind="line_length", sev="fix", msg=f"{len(ln)} characters on a line, over {LIMITS['chars']}: \"{ln[:50]}\""))
        if len(text) / d > fast: F.append(dict(t=s, kind="reading", sev="check", msg=f"{len(text) / d:.0f} characters a second, over {fast:.0f} (this speaker's captions run at {pace:.0f}): \"{text[:50]}\""))
        if d < LIMITS["min_s"]: F.append(dict(t=s, kind="short", sev="check", msg=f"on screen {d:.2f} s, under {LIMITS['min_s']} s"))
        if k + 1 < len(C) and C[k + 1][0] < e - 0.001: F.append(dict(t=s, kind="overlap", sev="fix", msg=f"overlaps the next caption by {e - C[k + 1][0]:.2f} s"))
    return F

def voice_findings(rep):
    R = json.load(open(rep)) if isinstance(rep, str) else rep; A = R["after"]; F = []
    if A["jumps_over_3db"]: F.append(dict(t=0, kind="level", sev="check", msg=f"{A['jumps_over_3db']} joins still jump over 3 dB (biggest {A['biggest_jump_db']} dB): listen to them"))
    if A["snr_db"] < LIMITS["snr_db"]: F.append(dict(t=0, kind="noise", sev="check", msg=f"the voice is {A['snr_db']} dB over the room after cleaning, under {LIMITS['snr_db']}"))
    if abs(R["length_s"]["after"] - R["length_s"]["before"]) > 1 / 48000 + 1e-4:
        F.append(dict(t=0, kind="length", sev="fix", msg=f"the length changed {R['length_s']['before']} -> {R['length_s']['after']} s: the voice will drift off the lips"))
    return F

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument("--srt"); ap.add_argument("--voice")
    a = ap.parse_args(); F = (srt_findings(a.srt) if a.srt else []) + (voice_findings(a.voice) if a.voice else [])
    for f in F: print(f"{int(f['t'] // 60)}:{f['t'] % 60:04.1f}  {f['sev']:5s} {f['kind']:11s} {f['msg']}")
    print(f"{sum(1 for f in F if f['sev'] == 'fix')} to fix, {sum(1 for f in F if f['sev'] == 'check')} to check")
    return 1 if any(f["sev"] == "fix" for f in F) else 0

if __name__ == "__main__":
    sys.exit(main())
