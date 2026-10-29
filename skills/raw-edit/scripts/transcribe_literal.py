#!/usr/bin/env python
"""transcribe_literal.py: the take's words as said, restarts and all, for sentence_cut.py.

  python transcribe_literal.py RAW.mp4 --out words.json [--model small.en]

cut_takes.py transcribes with Whisper's defaults, and Whisper cleans speech up: carrying the text it has written into
the next stretch, it writes a restart once ("Now this can be useful if you want more of a... / Now this can be useful
if you want more control" came out as one clean sentence at 406-411 s of the Get Started take) and stretches words over
the pauses. A cut built on that keeps both attempts and the stop between them. Here the take is split at every pause
of 0.3 s (voice activity), and every stretch is transcribed on its own, with nothing carried over, so each attempt is
written where it was said.
"""
if __name__ == "__main__":                                   # run on the suite's own Python (.venv, made by setup.py), whichever python started it
    import os as _o, sys as _s, subprocess as _sp
    _v = _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), "..", "..", "..", ".venv", *(("Scripts", "python.exe") if _o.name == "nt" else ("bin", "python")))
    if _o.path.exists(_v) and _o.path.normcase(_o.path.realpath(_s.prefix)) != _o.path.normcase(_o.path.realpath(_o.path.dirname(_o.path.dirname(_v)))):
        _s.exit(_sp.call([_v, _o.path.realpath(__file__)] + _s.argv[1:]))
import argparse, json, subprocess, sys
import numpy as np, imageio_ffmpeg

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("raw"); ap.add_argument("--out", required=True); ap.add_argument("--model", default="small.en")
    a = ap.parse_args()
    try: import av                                    # faster-whisper imports av only to read files; where a policy blocks
    except ImportError: sys.modules["av"] = type(sys)("av")   # av's DLL, the audio goes in as an array
    from faster_whisper import WhisperModel
    audio = np.frombuffer(subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", a.raw, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                                         capture_output=True).stdout, np.int16).astype(np.float32) / 32768
    m = WhisperModel(a.model, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(audio, language="en", beam_size=5, word_timestamps=True, condition_on_previous_text=False,
                           vad_filter=True, vad_parameters=dict(min_silence_duration_ms=300, speech_pad_ms=120))
    words = [dict(w=w.word.strip(), s=round(w.start, 2), e=round(w.end, 2)) for s in segs for w in (s.words or []) if w.word.strip()]
    json.dump(words, open(a.out, "w", encoding="utf-8"))
    long_ = sum(1 for w in words if w["e"] - w["s"] > 1.0)
    print(f"{len(words)} words, {long_} over a second long -> {a.out}")

if __name__ == "__main__":
    main()
