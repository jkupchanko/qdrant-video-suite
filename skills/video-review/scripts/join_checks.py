"""join_checks.py: the sound at every join of the cut. A join that starts or ends while the voice is sounding clips a word
("you still cut off my audio on one of the parts": 0:21.9 of the first Listed Sections build kept the first 40 ms of "when"
after "...dense and sparse vectors"). Read from the raw take at each piece's source in- and out-point, from the cut list.

  joins(take, cutlist) -> [dict(t, edge, src, sev, msg)]
"""
import re, subprocess, numpy as np

def envelope(path):
    """loudness 10 ms a step (dB), with the take's own quiet and voice levels"""
    import imageio_ffmpeg
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768; n = len(x) // 160
    env = 20 * np.log10(np.maximum(1e-6, np.sqrt((x[:n * 160].reshape(n, 160) ** 2).mean(axis=1))))
    floor, speech = np.percentile(env, [10, 90])
    return env, floor + 0.45 * (speech - floor), floor + 0.7 * (speech - floor)

def rows(cutlist):
    """(edit time, source in, source out, line) per piece, in edit order"""
    t = open(cutlist, encoding="utf-8").read()
    return [(float(a), float(b), float(c), d) for a, b, c, d in re.findall(r"^\| ([\d.]+) \| ([\d.]+)-([\d.]+) \| x[\d.]+ \| (.*?) \|", t, flags=re.M)]

def joins(take, cutlist):
    env, quiet, loud = envelope(take); R = rows(cutlist); out = []
    lv = lambda a, b: float(env[max(0, int(round(a * 100))):max(int(round(a * 100)) + 1, int(round(b * 100)))].max())
    for k, (t, a, b, line) in enumerate(R):
        dur = b - a; tb = t + dur
        # the in-point: the voice sounding on both sides of it means the piece starts in the middle of a sound
        pre, post = lv(a - 0.03, a), lv(a, a + 0.03)
        gap = next((i / 100 for i in range(int(round((a + 0.1) * 100)), int(round((a - 0.45) * 100)), -1) if env[i] < quiet), None)
        if pre > loud and post > loud and gap is not None:
            out.append(dict(t=t, edge="in", src=a, sev="fix", msg=f"the piece starts mid-sound: the voice is at {pre:.0f} dB just before its in-point (source {a:.2f} s) and {post:.0f} dB after it, so a sound is cut in half; there is a pause to cut in at source {gap:.2f} s"))
        elif pre > loud and post > loud:
            out.append(dict(t=t, edge="in", src=a, sev="check", msg=f"the piece starts while the voice is going ({pre:.0f} / {post:.0f} dB around source {a:.2f} s): one word running into the next, with no pause to cut in; listen to it"))
        elif pre > quiet and post > quiet:
            out.append(dict(t=t, edge="in", src=a, sev="note", msg=f"the piece starts on a soft sound ({pre:.0f} / {post:.0f} dB around source {a:.2f} s), with no pause to cut in"))
        # the out-point: the voice still loud as the piece ends cuts a sound off; after a pause in the last 0.25 s it is the
        # next word's first sound kept (a sound that has died down by the out-point is a word's own end: the "-load" of "upload")
        end, after = lv(b - 0.03, b), lv(b, b + 0.03)
        if end > loud:
            i0 = int(round((b - 0.25) * 100)); seg = env[i0:int(round(b * 100))]
            qi = [i for i in range(len(seg) - 2) if seg[i] < quiet and seg[i + 1] < quiet and seg[i + 2] < quiet]
            if qi:
                on = (i0 + qi[-1] + 3) / 100
                out.append(dict(t=tb - (b - on), edge="out", src=b, sev="fix", msg=f"the piece keeps the first {1000 * (b - on):.0f} ms of the next word (a new sound at source {on:.2f} s, after a pause, cut at {b:.2f} s, still {end:.0f} dB): a clipped word at the join"))
            elif after > loud:
                out.append(dict(t=tb, edge="out", src=b, sev="fix", msg=f"the piece ends mid-word: the voice is at {end:.0f} dB at its out-point (source {b:.2f} s) and still {after:.0f} dB after it"))
        # the next piece starting before this one ends, in the source: the same sound twice
        if k + 1 < len(R) and a < R[k + 1][1] < b - 0.05 and lv(R[k + 1][1], b) > loud:
            out.append(dict(t=R[k + 1][0], edge="in", src=R[k + 1][1], sev="fix", msg=f"this piece starts at source {R[k + 1][1]:.2f} s, before the piece before it ends ({b:.2f} s): {b - R[k + 1][1]:.2f} s of voice is heard twice"))
    return out

if __name__ == "__main__":
    import sys
    for j in joins(sys.argv[1], sys.argv[2]): print(f"{j['t']:7.2f}  {j['sev']:5s} {j['edge']:3s}  {j['msg']}")
