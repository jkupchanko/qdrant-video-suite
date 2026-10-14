#!/usr/bin/env python
"""cues.py: what is being said when the camera layout changes.

  python cues.py --audio audio/ --audit audit/ --out cues/     (transcribe each video, align with its audit)

For every layout switch in an audit json it records the words spoken in the 6 s before and 4 s after the
switch, then counts the phrases that recur across all videos just before each kind of change
(e.g. none->small when "let me show you", full->none when "here's the code"). Output: one json per video
with the switch lines, and cues_summary.md with the recurring phrases per transition.
"""
import argparse, json, os, re, sys
from collections import Counter, defaultdict

def load_audio(path):
    """decode with ffmpeg to 16 kHz mono float32 (avoids PyAV version mismatches)"""
    import subprocess, numpy as np, imageio_ffmpeg
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)

def transcribe(path, model):
    segs, _ = model.transcribe(load_audio(path), language="en", vad_filter=True, beam_size=1)
    return [{"start": round(s.start, 1), "end": round(s.end, 1), "text": s.text.strip()} for s in segs]

def words_between(tr, t0, t1):
    return " ".join(s["text"] for s in tr if s["end"] >= t0 and s["start"] <= t1)

CUE_PATTERNS = {
    "show/look": r"\b(let me show|let's look|take a look|look at|here's|here is|check (this|it) out|as you can see|you can see)\b",
    "code/screen": r"\b(code|terminal|editor|screen|file|command|run|type|click|open)\b",
    "explain": r"\b(basically|the idea|think of|means|because|why|so what)\b",
    "transition": r"\b(now|next|so|alright|okay|let's|first|then|finally)\b",
    "address": r"\b(you|your)\b",
}

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audio", required=True); ap.add_argument("--audit", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="base.en")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    from faster_whisper import WhisperModel
    model = WhisperModel(a.model, device="cpu", compute_type="int8")
    by_transition = defaultdict(Counter); lines_by_transition = defaultdict(list)
    for fn in sorted(os.listdir(a.audio)):
        vid = os.path.splitext(fn)[0]
        aj = os.path.join(a.audit, vid + ".json")
        if not os.path.exists(aj): continue
        tp = os.path.join(a.out, vid + "_transcript.json")
        if os.path.exists(tp): tr = json.load(open(tp))
        else:
            tr = transcribe(os.path.join(a.audio, fn), model); json.dump(tr, open(tp, "w"), indent=0)
        rep = json.load(open(aj)); segs = rep["segments"]
        out = []
        for prev, cur in zip(segs, segs[1:]):
            t = cur["start"]; key = f"{prev['layout']}->{cur['layout']}"
            before = words_between(tr, t - 6, t); after = words_between(tr, t, t + 4)
            cues = [k for k, p in CUE_PATTERNS.items() if re.search(p, (before + " " + after).lower())]
            out.append({"t": t, "transition": key, "before": before, "after": after, "cues": cues})
            for c in cues: by_transition[key][c] += 1
            lines_by_transition[key].append((vid, t, before[-90:], after[:60]))
        json.dump(out, open(os.path.join(a.out, vid + "_cues.json"), "w"), indent=1)
        print(f"  {vid}: {len(out)} switches, {len(tr)} lines")
    with open(os.path.join(a.out, "cues_summary.md"), "w", encoding="utf-8") as fh:
        fh.write("# What is said around camera changes\n\n")
        for key, cnt in sorted(by_transition.items(), key=lambda kv: -sum(kv[1].values())):
            n = len(lines_by_transition[key])
            fh.write(f"## {key}  ({n} switches)\n\n")
            for c, k in cnt.most_common(): fh.write(f"- {c}: {k} ({100 * k // n}%)\n")
            fh.write("\nExamples:\n\n")
            for vid, t, b, af in lines_by_transition[key][:8]: fh.write(f"- {vid} @{t:.0f}s: ...{b} | {af}...\n")
            fh.write("\n")
    print(f"-> {os.path.join(a.out, 'cues_summary.md')}")

if __name__ == "__main__":
    main()
