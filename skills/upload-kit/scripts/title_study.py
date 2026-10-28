#!/usr/bin/env python
"""title_study.py: which title features go with more views on technical YouTube, measured inside each channel.

  python title_study.py CORPUS_DIR --fetch     -> CORPUS_DIR/raw/<group>__<handle>.json (yt-dlp page data, no video)
  python title_study.py CORPUS_DIR             -> CORPUS_DIR/report.md and references/title_effects.json

The corpus: the newest ~400 uploads of each channel in CHANNELS (popular educators, AI builders, and the DevRel channels of
developer companies), Shorts left out. A video's lift is log10(views) minus the median log10(views) of its 30 nearest
uploads on the same channel: the list is newest first, so the neighbours share the channel's size and the video's age.
A feature's effect is the median, across channels with at least MIN titles with it and MIN without, of the difference of
median lifts, as a multiple of views; its 90% range comes from resampling the channels. Big channels do not outvote small
ones, and a channel that never uses a feature does not count for it.

It measures association, not cause: "Explained" and "Getting Started" also say what kind of video it is, and the topic
moves views far more than the wording. titles.py turns the effects that held up into a ranking aid.
"""
import argparse, glob, json, math, os, random, re, statistics as st, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import titles as TI
MIN, NB = 6, 30
CHANNELS = {
 "educator": ["Fireship", "freecodecamp", "NetworkChuck", "TechWorldwithNana", "ByteByteGo", "TraversyMedia", "t3dotgg", "hnasr",
              "coreyms", "TechWithTim", "WebDevSimplified", "NetNinja", "programmingwithmosh", "KevinPowell", "ArjanCodes", "mCoding",
              "ThePrimeTimeagen", "Computerphile", "3blue1brown", "statquest", "NeuralNine", "JeffGeerling", "LowLevelTV", "DevOpsToolkit",
              "beyondfireship", "codeaesthetic", "TheCodingTrain"],
 "ai_builder": ["jamesbriggs", "daveebbelaar", "samwitteveenai", "technovangelist", "AIJasonZ", "ColeMedin", "engineerprompt",
                "AndrejKarpathy", "TwoMinutePapers", "sentdex", "YannicKilcher", "AllAboutAI", "matthew_berman", "1littlecoder"],
 "devrel": ["IBMTechnology", "googlecloudtech", "MongoDB", "Supabase", "VercelHQ", "DockerInc", "pinecone-io", "Weaviate", "LangChain",
            "elastic", "Redisinc", "PlanetScale", "neondatabase", "cloudflaredevelopers", "GitHub", "JetBrainsTV", "anthropic-ai",
            "GoogleDevelopers", "HuggingFace", "qdrant", "awsdevelopers", "MicrosoftDeveloper", "Postman", "Zilliz", "Chromadb"],
}
TUT = re.compile(r"how to|tutorial|guide|get(ting)? started|crash course|full course|step by step|beginner|setup|set up|install|intro|deploy|build", re.I)

def fetch(corpus):
    import shutil
    yt = shutil.which("yt-dlp") or sys.exit("yt-dlp is not installed (winget install yt-dlp)")
    raw = os.path.join(corpus, "raw"); os.makedirs(raw, exist_ok=True)
    def one(group, h):
        p = os.path.join(raw, f"{group}__{h}.json")
        if os.path.exists(p) and os.path.getsize(p) > 200: return h, "kept"
        r = subprocess.run([yt, "--flat-playlist", "-J", "--playlist-end", "400", f"https://www.youtube.com/@{h}/videos"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        if r.returncode or not r.stdout.strip(): return h, "FAILED " + r.stderr.strip()[-160:]
        d = json.loads(r.stdout)
        E = [dict(id=e.get("id"), title=e.get("title"), views=e.get("view_count"), dur=e.get("duration"), i=k) for k, e in enumerate(d.get("entries") or [])]
        json.dump(dict(channel=d.get("channel") or h, handle=h, group=group, subs=d.get("channel_follower_count"), videos=E), open(p, "w", encoding="utf-8"))
        return h, f"{len(E)} videos"
    with ThreadPoolExecutor(8) as ex:
        for h, msg in ex.map(lambda j: one(*j), [(g, h) for g, hs in CHANNELS.items() for h in hs]): print(f"{h:22s} {msg}", flush=True)

def load(corpus):
    V = []
    for p in sorted(glob.glob(os.path.join(corpus, "raw", "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        vs = [v for v in d["videos"] if v.get("title") and v.get("views") and (v.get("dur") or 999) >= 75]   # no Shorts
        if len(vs) < 40: continue                                                                           # too few to judge inside
        lv = [math.log10(v["views"] + 1) for v in vs]
        for k, v in enumerate(vs):
            nb = [lv[j] for j in range(max(0, k - NB // 2), min(len(vs), k + NB // 2 + 1)) if j != k]
            V.append(dict(v, lift=lv[k] - st.median(nb), channel=d["channel"], group=d["group"], f=TI.features(v["title"])))
    return V

def effect(V, key, sub=None):
    by = {}
    for v in V:
        if sub and not sub(v): continue
        by.setdefault(v["channel"], ([], []))[0 if v["f"][key] else 1].append(v["lift"])
    diffs = [st.median(a) - st.median(b) for a, b in by.values() if len(a) >= MIN and len(b) >= MIN]
    if len(diffs) < 5: return None
    rnd = random.Random(7); boots = sorted(st.median(rnd.choices(diffs, k=len(diffs))) for _ in range(400))
    used = sum(len(a) for a, _ in by.values()) / max(1, sum(len(a) + len(b) for a, b in by.values()))
    return dict(x=round(10 ** st.median(diffs), 3), lo=round(10 ** boots[20], 3), hi=round(10 ** boots[379], 3), n=len(diffs),
                pos=round(sum(d > 0 for d in diffs) / len(diffs), 3), used=round(used, 4))

def study(corpus):
    import datetime
    V = load(corpus); keys = list(V[0]["f"]); chans = sorted({v["channel"] for v in V})
    subs = [("all", None), ("tutorials", lambda v: bool(TUT.search(v["title"]))), ("devrel", lambda v: v["group"] == "devrel"),
            ("educator", lambda v: v["group"] == "educator"), ("ai_builder", lambda v: v["group"] == "ai_builder")]
    out = {name: {k: effect(V, k, sub) for k in keys} for name, sub in subs}
    L = sorted(len(v["title"]) for v in V); q = lambda a, p: a[int(p * (len(a) - 1))]
    R = [f"# What {len(V):,} titles from {len(chans)} technical channels say\n",
         f"Measured {datetime.date.today()}. Length: median {st.median(L):.0f} characters (middle 80%: {q(L, .1)} to {q(L, .9)}).\n"]
    for name in out:
        R.append(f"\n## {name}\n\n| feature | share of titles | views vs. without | 90% range | channels | channels where it helps |\n|---|---|---|---|---|---|")
        for k, e in sorted([(k, e) for k, e in out[name].items() if e], key=lambda r: -r[1]["x"]):
            R.append(f"| {k} | {100 * e['used']:.0f}% | {e['x']:.2f}x | {e['lo']:.2f} to {e['hi']:.2f} | {e['n']} | {100 * e['pos']:.0f}% |")
    dv = sorted([v for v in V if v["group"] == "devrel" and TUT.search(v["title"])], key=lambda v: -v["lift"])
    R += ["\n## DevRel tutorials: the 40 that beat their neighbours most, and the 25 that trailed most\n"]
    R += [f"- {10 ** v['lift']:.0f}x {v['channel']}: {v['title']}" for v in dv[:40]] + ["", "..."] + [f"- {10 ** v['lift']:.2f}x {v['channel']}: {v['title']}" for v in dv[-25:]]
    open(os.path.join(corpus, "report.md"), "w", encoding="utf-8").write("\n".join(R) + "\n")
    json.dump(dict(measured=str(datetime.date.today()), titles=len(V), channels=chans, min_per_side=MIN, neighbours=NB, effects=out),
              open(TI.REF, "w", encoding="utf-8"), indent=1)
    print(f"{len(V):,} titles from {len(chans)} channels -> {os.path.join(corpus, 'report.md')}, {os.path.normpath(TI.REF)}")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corpus"); ap.add_argument("--fetch", action="store_true"); a = ap.parse_args()
    if a.fetch: fetch(a.corpus)
    study(a.corpus)

if __name__ == "__main__":
    main()
