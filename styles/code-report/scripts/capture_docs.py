"""Screenshot paragraphs of the Qdrant bulk-import docs at 2x and record where each phrase sits, so a highlight can follow the narration."""
import json
from playwright.sync_api import sync_playwright
URL = "https://qdrant.tech/documentation/production-operations/bulk-data-import/"
SHOTS = {  # name: (first item, last item, phrases to locate)
    "title": (12, 12, ["Bulk Uploading Data to Qdrant"]),
    "why_bulk": (14, 15, ["uploading large amounts of data efficiently", "bulk ingestion"]),
    "vector_type": (19, 22, ["not all vectors behave the same way", "Dense vectors rely on HNSW", "Sparse vectors use a separate indexing approach", "CPU and memory pressure"]),
    "no_single": (23, 24, ["there is no single configuration that works best for every bulk upload", "upload speed", "memory"]),
    "option1": (26, 29, ["Option 1: Reduce Memory Pressure", "the raw vector data alone can take up a large amount of RAM", "stores incoming vectors on disk from the start"]),
    "option1_code": (31, 31, ["memory=models.Memory.COLD"]),
    "option1_watch": (32, 33, ["Search performance may depend more on disk access"]),
    "option2": (34, 37, ["Create payload indexes before uploading points", "which fields will be used for filtering", "If those indexes are created after a large dataset has already been uploaded"]),
    "option2_code": (39, 39, ["field_name=\"category\""]),
    "option2_fit": (40, 41, ["category, tenant ID, document type, source, or user ID", "Payload indexes should be intentional"]),
    "option3": (42, 45, ["Option 3: Quantization to Balance Memory and Search Performance", "a compressed copy of each vector pinned in RAM for search", "the original vectors stay on disk"]),
    "option3_watch": (48, 49, ["lower memory usage while still keeping search performance practical", "search quality and latency should be tested with real data"]),
    "option4": (50, 52, ["Option 4: Reduce Sparse Index Memory During Uploads", "store the sparse vector index on disk", "reduce memory usage when the index becomes large"]),
    "option4_watch": (55, 56, ["the sparse index is putting pressure on memory", "may slow down search because queries can depend more on disk access"]),
    "batch": (60, 62, ["Batch Your Uploads", "uploading points one at a time is slow", "Upload points in batches instead"]),
    "batch_code": (63, 63, ["batch_size=256"]),
    "batch_watch": (64, 65, ["A batch size of 64 to 256 points is a reasonable starting range", "increase memory usage and make retries more expensive if a request fails"]),
    "parallel": (66, 68, ["Parallelize Uploads", "Two to four workers, each sending its own stream of batches"]),
    "parallel_code": (70, 70, ["parallel=4"]),
    "parallel_watch": (71, 72, ["Too much parallelism can create extra pressure on CPU, memory, disk I/O, and network resources", "Start with two to four workers"]),
    "shards": (73, 75, ["Use Multiple Shards for Larger Uploads", "Each shard has its own write-ahead log and update worker", "process writes in parallel"]),
    "shards_watch": (78, 79, ["especially when paired with parallel upload workers", "More shards are not always better", "Each shard adds overhead"]),
    "wrap": (92, 94, ["Not One-Size-Fits-All", "memory usage, indexing behavior", "choose the right strategy for the workload"]),
}
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome"); pg = b.new_page(viewport={"width": 1400, "height": 900}, device_scale_factor=2, color_scheme="light"); pg.goto(URL, wait_until="networkidle", timeout=60000)
    pg.add_style_tag(content="header, nav, .cookie, [class*=cookie], [id*=cookie], #onetrust-consent-sdk, #onetrust-banner-sdk, .onetrust-pc-dark-filter, [class*=ot-sdk] {display:none !important}")
    pg.add_style_tag(content="article p, article h1, article h2, article h3, article pre, article li, main p, main h1, main h2, main h3, main pre {max-width: 600px !important}")   # a narrow column: bigger text in the video
    out = {}
    for name, (a, z, phrases) in SHOTS.items():
        info = pg.evaluate("""([a, z, phrases]) => {
            const els = Array.from(document.querySelectorAll('article h1, article h2, article h3, article p, article li, article pre, main h1, main h2, main h3, main p, main pre')).slice(0, 120);
            const pick = els.slice(a, z + 1); pick[0].scrollIntoView({block: 'center'});
            const sx = window.scrollX, sy = window.scrollY; let r = pick[0].getBoundingClientRect(); let x0 = r.left + sx, y0 = r.top + sy, x1 = r.right + sx, y1 = r.bottom + sy;
            for (const e of pick) { const q = e.getBoundingClientRect(); x0 = Math.min(x0, q.left + sx); y0 = Math.min(y0, q.top + sy); x1 = Math.max(x1, q.right + sx); y1 = Math.max(y1, q.bottom + sy); }
            const found = {};
            for (const ph of phrases) {
                for (const e of pick) {
                    const walker = document.createTreeWalker(e, NodeFilter.SHOW_TEXT); let n, acc = [], s = '';
                    while ((n = walker.nextNode())) { acc.push([n, s.length]); s += n.textContent; }
                    const i = s.indexOf(ph); if (i < 0) continue;
                    const rng = document.createRange(); const loc = (k) => { let best = acc[0]; for (const t of acc) if (t[1] <= k) best = t; return [best[0], k - best[1]]; };
                    const [sn, so] = loc(i), [en, eo] = loc(i + ph.length); rng.setStart(sn, so); rng.setEnd(en, Math.min(eo, en.textContent.length));
                    found[ph] = Array.from(rng.getClientRects()).map(q => [q.left + sx, q.top + sy, q.width, q.height]); break;
                }
            }
            return {box: [x0, y0, x1 - x0, y1 - y0], phrases: found};
        }""", [a, z, phrases])
        x, y, w, h = info["box"]; pad = 28; clip = {"x": max(0, x - pad), "y": max(0, y - pad), "width": w + 2 * pad, "height": h + 2 * pad}
        pg.screenshot(path=f"docs/{name}.png", clip=clip, full_page=True)
        rel = {ph: [[(q[0] - clip["x"]) * 2, (q[1] - clip["y"]) * 2, q[2] * 2, q[3] * 2] for q in rects] for ph, rects in info["phrases"].items()}
        out[name] = {"size": [clip["width"] * 2, clip["height"] * 2], "phrases": rel}; print(name, out[name]["size"], {k: len(v) for k, v in rel.items()})
    json.dump(out, open("docs/shots.json", "w"), indent=1); b.close()
