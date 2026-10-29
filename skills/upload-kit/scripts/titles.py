#!/usr/bin/env python
"""titles.py: a title judged by what 19,463 titles from 63 technical YouTube channels did, inside each channel.

  python titles.py --score "Getting Started with Qdrant" "Qdrant Cloud Setup: Cluster, API Key, Web UI"
  python titles.py SCRIPT.md [--minutes 5.5]      -> title ideas from the script, each scored

Each feature's effect is measured by title_study.py (references/title_effects.json): a video's views against the median of
its 30 nearest uploads on the same channel, so channel size and age cancel out, then the median across channels of
(with the feature) - (without it). A title's score multiplies the effects that held up (90% range clear of 1x), from the
DevRel channels (company channels: MongoDB, Docker, AWS, Redis, Supabase, Pinecone, ...) where measured, else from all.

The score is a ranking aid, not a forecast: what a video is about moves views far more than how its title is worded, and
"Explained" or "Getting Started" also say what kind of video it is. The person picks the title.
"""
if __name__ == "__main__":                                   # run on the suite's own Python (.venv, made by setup.py), whichever python started it
    import os as _o, sys as _s, subprocess as _sp
    _v = _o.path.join(_o.path.dirname(_o.path.realpath(__file__)), "..", "..", "..", ".venv", *(("Scripts", "python.exe") if _o.name == "nt" else ("bin", "python")))
    if _o.path.exists(_v) and _o.path.normcase(_o.path.realpath(_s.prefix)) != _o.path.normcase(_o.path.realpath(_o.path.dirname(_o.path.dirname(_v)))):
        _s.exit(_sp.call([_v, _o.path.realpath(__file__)] + _s.argv[1:]))
import argparse, json, math, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REF = os.path.join(HERE, "..", "references", "title_effects.json")

TOOL_WORDS = """Python JavaScript TypeScript Rust Go Golang Java Kotlin Swift C++ C# Ruby PHP Elixir Zig Bash SQL HTML CSS WASM WebAssembly
React Vue Svelte Angular Next.js Nextjs Nuxt Astro Remix Solid Qwik htmx Tailwind Bootstrap Node Node.js Deno Bun Express Django Flask FastAPI
Spring Rails Laravel Docker Kubernetes K8s Helm Terraform Ansible Linux Ubuntu Windows macOS Git GitHub GitLab Actions Copilot VSCode Neovim Vim
AWS Azure GCP Lambda S3 EC2 Firebase Supabase Vercel Netlify Cloudflare Postgres PostgreSQL MySQL SQLite MongoDB Redis Elasticsearch Kafka
GraphQL REST gRPC API APIs JSON YAML Nginx Prisma Drizzle Stripe Auth0 OAuth JWT Qdrant Pinecone Weaviate Milvus Zilliz Chroma ChromaDB pgvector
Neon PlanetScale LangChain LangGraph LlamaIndex CrewAI AutoGen OpenAI ChatGPT GPT GPT-4 GPT-4o GPT-5 Claude Anthropic Gemini Llama Mistral DeepSeek
Ollama HuggingFace Transformers PyTorch TensorFlow Keras JAX NumPy Pandas Jupyter RAG LLM LLMs MCP n8n Cursor Devin Grok Sora Whisper Postman Figma
Excel Obsidian Notion Raspberry Pi Arduino ESP32 Unity Godot Blender Jenkins ArgoCD Prometheus Grafana Istio OpenTelemetry Datadog Snowflake
Databricks Spark Airflow dbt BigQuery Vertex Bedrock SageMaker Streamlit Gradio Electron Flutter Expo Tauri Vite Webpack npm pnpm""".split()
TOOLS = set(TOOL_WORDS) | {w.lower() for w in TOOL_WORDS}       # a fixed list: capitalised words in Title Case titles catch "About"

def features(t):
    """the title's features, as title_study.py measures them -> {name: bool}"""
    T = t.strip(); low = T.lower(); words = re.findall(r"[A-Za-z0-9'+#.]+", T)
    caps = [w for w in words if len(w) >= 3 and w.isupper() and not w.isdigit() and w not in TOOLS]
    cap_share = sum(1 for w in words if w[:1].isupper()) / max(1, len(words))
    first = re.sub(r"[^A-Za-z0-9.+#]", "", T.split()[0]) if T.split() else ""
    return {
        "length: under 30 chars": len(T) < 30, "length: 30-49 chars": 30 <= len(T) < 50, "length: 50-69 chars": 50 <= len(T) < 70,
        "length: 70+ chars": len(T) >= 70,
        "shape: two parts (colon)": ":" in T, "shape: two parts (dash)": bool(re.search(r"\s[-–—]\s", T)), "shape: two parts (pipe)": "|" in T,
        "shape: question": T.rstrip().endswith("?"), "shape: exclamation": "!" in T,
        "shape: (parentheses) or [brackets]": bool(re.search(r"[(\[]", T)),
        "opens: How to": low.startswith("how to"), "opens: How (not to)": low.startswith("how ") and not low.startswith("how to"),
        "opens: Why": low.startswith("why"), "opens: What is/are": bool(re.match(r"what (is|are)\b", low)),
        "opens: a number": bool(re.match(r"\d", T)), "opens: I / I'm / I've": bool(re.match(r"i('m|'ve)?\b", low)),
        "opens: Stop / Don't / Never": bool(re.match(r"(stop|don't|dont|never)\b", low)),
        "opens: a tool's name": first in TOOLS, "opens: The": low.startswith("the "),
        "has: a number": bool(re.search(r"\d", T)), "has: the year": bool(re.search(r"\b20[12]\d\b", T)),
        "has: a time (in N minutes/seconds)": bool(re.search(r"\b\d+\s*(min|mins|minute|minutes|second|seconds|hours?)\b", low)),
        "has: Tutorial": "tutorial" in low, "has: for Beginners": "beginner" in low, "has: Explained": "explained" in low,
        "has: Crash Course / Full Course": bool(re.search(r"(crash|full) course", low)), "has: Guide": "guide" in low,
        "has: Getting Started / Get Started": bool(re.search(r"get(ting)? started", low)), "has: Intro / Introduction": bool(re.search(r"\bintro(duction)?\b", low)),
        "has: vs": bool(re.search(r"\bvs\.?\b|\bversus\b", low)), "has: Build / Building": bool(re.search(r"\bbuild(ing)?\b", low)),
        "has: from Scratch": "scratch" in low, "has: Step by Step": "step by step" in low or "step-by-step" in low,
        "has: Best Practices": "best practice" in low, "has: Mistakes": "mistake" in low,
        "has: Easy / Simple": bool(re.search(r"\b(easy|easily|simple|simplest)\b", low)),
        "has: you / your": bool(re.search(r"\byou(r|'re)?\b", low)), "has: I / my (in the title)": bool(re.search(r"\b(i|my|i'm|i've)\b", low)),
        "has: New / Finally / Just": bool(re.search(r"\b(new|finally|just released|announcing)\b", low)),
        "has: a word in capitals (not a tool)": bool(caps), "has: an emoji": bool(re.search("[\U0001F300-\U0001FAFF☀-➿]", T)),
        "has: Live / Webinar / Stream / Podcast / Ep": bool(re.search(r"\b(live|webinar|stream|podcast|ep\.?\s*\d|episode)\b", low)),
        "has: Part N / #N / Ep N (a series)": bool(re.search(r"\b(part|pt\.?|ep\.?|episode|day)\s*\d+|#\d+|\b\d+/\d+\b", low)),
        "has: an event (Conf, Summit, | EVENT 2025)": bool(re.search(r"\b(conf|conference|summit|universe|keynote|posette|reinvent|re:invent|kubecon|meetup|ama)\b", low)),
        "has: a person's name (with NAME / - Name Surname)": bool(re.search(r"\bwith [A-Z][a-z]+ [A-Z][a-z]+|\s[-–|]\s*[A-Z][a-z]+ [A-Z][a-z]+\s*$|\(([A-Z][a-z]+ [A-Z][a-z]+)\)", T)),
        "names a tool": any(w in TOOLS for w in re.findall(r"[A-Za-z0-9.+#]+", T)),
        "case: Title Case (most words capitalised)": cap_share >= 0.7, "case: sentence case": cap_share < 0.4,
    }

_E = None
def effects():
    """the measured effects that held up: {feature: (multiplier, source)} - DevRel channels first, all channels otherwise"""
    global _E
    if _E is None:
        E = json.load(open(REF, encoding="utf-8"))["effects"]; _E = {}
        for src in ("all", "devrel"):                                           # devrel overrides all where it is measured
            for k, e in E[src].items():
                if e and e["n"] >= 6 and (e["lo"] > 1 or e["hi"] < 1): _E[k] = (e["x"], src)
    return _E

def score(title):
    """-> (score, [(feature, x, source)]): the measured effects multiplied. Effects overlap (a "Getting Started" title is also
    short and names a tool), so the score ranks titles; it is not a forecast of views"""
    E = effects(); hit = [(k, *E[k]) for k, on in features(title).items() if on and k in E]
    return math.prod(x for _, x, _ in hit), sorted(hit, key=lambda h: -abs(math.log(h[1])))

def check(title):
    """what the study says to look at again -> [(severity, message)]"""
    f = features(title); F = []
    if f["length: 70+ chars"]: F.append(("check", f"{len(title)} characters: titles of 70+ did worse on 92% of DevRel channels (0.74x); under 50 did best"))
    if f["has: the year"]: F.append(("check", "a year in the title: 0.76x on DevRel channels, and the title ages"))
    if f["has: Part N / #N / Ep N (a series)"]: F.append(("check", "a part or episode number: 0.74x on DevRel channels; a newcomer skips part 3"))
    if f["has: an event (Conf, Summit, | EVENT 2025)"]: F.append(("check", "an event name: 0.69x on DevRel channels; name what the viewer learns instead"))
    if f["has: Live / Webinar / Stream / Podcast / Ep"]: F.append(("check", "says live, webinar or stream: 0.80x on DevRel channels"))
    if not f["names a tool"]: F.append(("check", "no product or tool named: titles naming one did 1.19x on DevRel channels"))
    return F

def ideas(script, minutes=None):
    """title ideas from the script's own title and sections, in the shapes that did best; Claude adds its own and scores them"""
    text = open(script, encoding="utf-8").read()
    h1 = next((re.sub(r"\s+\d+:\d{2}.*$", "", m.group(1)).strip() for m in re.finditer(r"(?m)^#\s+(.+)$", text)), "")
    secs = [re.sub(r"\s+\d+:\d{2}.*$", "", m.group(1)).strip() for m in re.finditer(r"(?m)^##\s+(.+)$", text)]
    secs = [s for s in secs if s.lower() not in ("intro", "outro", "count", "introduction", "conclusion", "wrap-up")]
    tool = next((w for w in re.findall(r"[A-Za-z0-9.+#]+", h1) if w in TOOLS), "Qdrant")
    base = re.sub(r"^get started with", "Getting Started with", h1, flags=re.I)
    out = [h1, base] if base != h1 else [h1]
    if minutes: out.append(f"{base} in {round(minutes)} Minutes")
    out += [f"{base} for Beginners", f"{base}: A Step-by-Step Guide"]
    for s in secs[:12]:                                                        # a section that is a task: "How to <task>"
        if re.match(r"(create|run|deploy|install|build|set up|connect|add|save|use|upload|search|query|filter|load)\b", s, re.I):
            out.append(f"How to {s}" + ("" if tool.lower() in s.lower() else f" with {tool}"))
    return list(dict.fromkeys(o for o in out if o))

def show(titles):
    for t in sorted(titles, key=lambda t: -score(t)[0]):
        x, why = score(t); F = check(t)
        print(f"score {x:4.1f}  {t}  ({len(t)} chars)")
        print("            " + "; ".join(f"{k.split(': ', 1)[-1]} {v:.2f}x" for k, v, _ in why[:5]) if why else "            (no measured feature)")
        for sev, msg in F: print(f"            {sev}: {msg}")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", nargs="?"); ap.add_argument("--score", nargs="+"); ap.add_argument("--minutes", type=float); a = ap.parse_args()
    if a.score: show(a.score)
    elif a.script: show(ideas(a.script, a.minutes))
    else: ap.error("give a script or --score")

if __name__ == "__main__":
    main()
