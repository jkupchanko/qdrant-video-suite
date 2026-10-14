#!/usr/bin/env python
"""render_transitions.py: the same join rendered with several transitions, to compare.

  python render_transitions.py VIDEO.mp4 --a 18,24 --b 40,46 --out DIR [--kinds cut,dissolve:0.25,fadeblack:0.4,slideleft:0.3,punch:1.12,zoomin:0.4]
  python render_transitions.py A.mp4 B.mp4 --out DIR ...            (two separate clips)

--a and --b are start,end seconds of the shot before and the shot after. For each kind it writes
<out>/<kind>.mp4 with the two shots joined by that transition, then a comparison reel that plays them one
after another with a label. Kinds (ffmpeg xfade names, plus two of our own):
  cut                 hard cut
  punch:S             hard cut, but the second shot starts scaled by S (1.08-1.2) and eases back: the creator punch-in
  dissolve:D fade:D fadeblack:D fadewhite:D slideleft:D slideright:D slideup:D slidedown:D wipeleft:D smoothleft:D
  zoomin:D circleopen:D pixelize:D hblur:D   (D = seconds, default 0.3)
Audio: the first shot's audio runs through; the second shot's audio follows after the join.
"""
import argparse, os, subprocess, tempfile
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()

def run(cmd): subprocess.run(cmd, check=True)

def cut_clip(src, t0, t1, out, fps=30):
    run([FF, "-hide_banner", "-loglevel", "error", "-y", "-ss", str(t0), "-to", str(t1), "-i", src, "-vf", f"scale=1920:1080,fps={fps}", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-ac", "2", out])

def join(a, b, kind, d, out):
    da = float(subprocess.run([FF, "-i", a], capture_output=True, text=True).stderr.split("Duration: ")[1].split(",")[0].split(":")[-1]) if False else None
    import re
    def dur(p):
        info = subprocess.run([FF, "-i", p], capture_output=True, text=True).stderr; m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info); return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    la = dur(a)
    if kind == "cut":
        lst = os.path.join(os.path.dirname(out), "_list.txt"); open(lst, "w").write(f"file '{os.path.abspath(a).replace(os.sep, '/')}'\nfile '{os.path.abspath(b).replace(os.sep, '/')}'\n")
        run([FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out]); return
    if kind == "punch":
        s = d or 1.12; ease = 0.35   # scale from s back to 1 over `ease` seconds with a smooth curve
        zp = f"zoompan=z='if(lt(it,{ease}),{s}-({s}-1)*(it/{ease})*(it/{ease})*(3-2*it/{ease}),1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30"
        tmpb = out + ".b.mp4"
        run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i", b, "-vf", "scale=3840:2160:flags=lanczos," + zp, "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "copy", tmpb])
        join(a, tmpb, "cut", 0, out); os.remove(tmpb); return
    name = {"dissolve": "dissolve", "fade": "fade"}.get(kind, kind)
    run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i", a, "-i", b,
         "-filter_complex", f"[0:v][1:v]xfade=transition={name}:duration={d}:offset={la - d:.3f}[v];[0:a][1:a]acrossfade=d={d}[aud]",
         "-map", "[v]", "-map", "[aud]", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", out])

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video"); ap.add_argument("video_b", nargs="?"); ap.add_argument("--a", required=True); ap.add_argument("--b", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--kinds", default="cut,punch:1.12,dissolve:0.25,fadeblack:0.4,slideleft:0.3,zoomin:0.4")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    a0, a1 = (float(v) for v in a.a.split(",")); b0, b1 = (float(v) for v in a.b.split(","))
    A = os.path.join(a.out, "_a.mp4"); B = os.path.join(a.out, "_b.mp4")
    cut_clip(a.video, a0, a1, A); cut_clip(a.video_b or a.video, b0, b1, B)
    outs = []
    for spec in a.kinds.split(","):
        kind, _, d = spec.partition(":"); d = float(d) if d else (0.3 if kind not in ("cut",) else 0)
        out = os.path.join(a.out, f"{kind}.mp4"); join(A, B, kind, d, out); outs.append((kind, d, out)); print(f"-> {out}")
    # comparison reel: each variant with a label, one after another
    parts = []
    for kind, d, out in outs:
        lab = out + ".lab.mp4"; txt = f"{kind}" + (f" {d:g}s" if kind not in ("cut",) and d else "") + (f" x{d:g}" if kind == "punch" else "")
        run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i", out, "-vf", f"drawbox=x=0:y=1000:w=1920:h=80:color=black@0.75:t=fill,drawtext=text='{txt}':x=40:y=1022:fontsize=40:fontcolor=white:fontfile=C\\\\:/Windows/Fonts/segoeuib.ttf", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "copy", lab]); parts.append(lab)
    lst = os.path.join(a.out, "_reel.txt"); open(lst, "w").write("".join(f"file '{os.path.abspath(p).replace(os.sep, '/')}'\n" for p in parts))
    reel = os.path.join(a.out, "comparison_reel.mp4"); run([FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", reel]); print(f"-> {reel}")
    for p in parts: os.remove(p)

if __name__ == "__main__":
    main()
