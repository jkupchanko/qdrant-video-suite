"""Reference reel: real joins from the most-watched presenter-plus-screen videos in the corpus, 1.5 s each side,
labelled with channel, what changes and the measured kind. Also writes reel/models.json."""
import json, os, subprocess, imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
FONT = r"C\\:/Windows/Fonts/segoeui.ttf"
meta = {}
for l in open("meta.txt", encoding="utf-8", errors="ignore"):
    p = l.strip().split("|")
    if len(p) >= 5: meta[p[0]] = (int(p[2] or 0), p[3], p[4])
models = []
for f in os.listdir("transitions_all"):
    vid = f[:-5]; t = json.load(open(os.path.join("transitions_all", f)))
    cp = os.path.join("audit_all", f)
    if not os.path.exists(cp): continue
    cam = json.load(open(cp))
    face = cam["share"]["full"] + cam["share"]["half"]; shot = {k: v for k, v in t["counts"].items() if not k.startswith("element")}; n = sum(shot.values())
    spm = n / (t["duration"] / 60)
    if face < 0.2 or spm < 1.5: continue
    v, ch, title = meta.get(vid, (0, "", ""))
    joins = [e for e in t["events"] if e["context"] and e["context"].split("->")[0] != e["context"].split("->")[1] and "None" not in e["context"] and not e["kind"].startswith("element")]
    kinds = {}
    for e in joins: kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    models.append(dict(id=vid, channel=ch, title=title, views=v, face=face, shot_per_min=spm, joins=len(joins), join_kinds=kinds, soft=t["soft_median_s"], events=joins))
models.sort(key=lambda m: -m["views"])
top = [m for m in models if m["joins"] >= 6][:8]
for m in top: print(f"{m['id']} {m['channel'][:18]:18s} {m['views']:>10,} face {100*m['face']:.0f}%  {m['shot_per_min']:.1f} shot/min  joins {m['joins']}  {m['join_kinds']}  soft {m['soft']}")
os.makedirs("reel", exist_ok=True); parts = []
for m in top:
    src = f"videos/{m['id']}.mp4" if os.path.exists(f"videos/{m['id']}.mp4") else f"videos2/{m['id']}.mp4"
    picks = []
    for want in ("face->screen", "face->window", "screen->face", "window->face", "screen->screen", "window->window"):
        for e in m["events"]:
            if e["context"] == want and e["t"] > 5 and len(picks) < 3 and all(abs(e["t"] - p["t"]) > 10 for p in picks):
                picks.append(e); break
    for i, e in enumerate(picks):
        out = f"reel/{m['id']}_{i}.mp4"; t0 = max(0, e["t"] - 1.5)
        label = f"{m['channel'][:22]}  |  {e['context']}  |  {e['kind']}" + (f" {e['dur']:.2f}s" if e["kind"] != "cut" else "")
        label = label.replace("'", "").replace(":", "\\:").replace(">", "\\>")
        vf = f"scale=1280:720:flags=lanczos,fps=30,drawbox=x=0:y=660:w=1280:h=60:color=black@0.75:t=fill,drawtext=text='{label}':x=24:y=676:fontsize=28:fontcolor=white:fontfile={FONT},format=yuv420p"
        subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-ss", str(t0), "-t", "3.2", "-i", src, "-vf", vf, "-an", "-c:v", "libx264", "-crf", "20", out], check=True)
        parts.append(out)
open("reel/list.txt", "w").write("".join(f"file '{os.path.abspath(p).replace(os.sep, '/')}'\n" for p in parts))
subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", "reel/list.txt", "-c", "copy", "reel/reference_reel.mp4"], check=True)
json.dump([{k: v for k, v in m.items() if k != "events"} for m in models], open("reel/models.json", "w"), indent=1)
print("reel parts:", len(parts))
