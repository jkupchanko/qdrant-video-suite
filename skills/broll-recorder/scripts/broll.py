#!/usr/bin/env python
"""broll.py: turn any web page into screen-style B-roll for a video.

Subcommands
  inspect URL                       list the page's sections (headings, positions, what sits under each)
  plan URL --match "spoken line"    pick the section that matches what the video says, write a shot plan
  record PLAN.json --out clip.mp4   record the plan: 1080p, moving cursor, eased scrolling, click ripples
  review clip.mp4                   contact sheet + checks (duration, size, motion, not black)
  auto URL --match "..." --out DIR  inspect + plan + record + review + manifest.json, in one go
  batch jobs.json --out DIR         many `auto` jobs from one file

Examples
  python broll.py auto https://qdrant.tech/documentation/concepts/indexing/ \
      --match "you can create a payload index before you upload" --duration 6 --out broll/payload_index
  python broll.py inspect https://qdrant.tech/articles/bulk-uploads-in-qdrant/ --table
  python broll.py plan URL --match "..." --section "Choosing the Right Bulk Upload Strategy" --style highlight

Requires: playwright (pip), Google Chrome or `python -m playwright install chromium`, imageio-ffmpeg, Pillow, numpy.
Playwright's own ffmpeg is needed for video capture; `record` installs it on first use if it is missing.
"""
import argparse, json, math, os, re, shutil, subprocess, sys, tempfile, time

# ----------------------------------------------------------------------------- shared helpers
STOP = set("the a an and or of to in on for with is are be this that it its as at by from you your we our can will into over about what when how which".split())
BANNER_SELECTORS = ["#onetrust-banner-sdk", "#onetrust-consent-sdk", ".ot-sdk-container", "#CybotCookiebotDialog", "#cookie-banner", "#cookieConsent",
                    "[id*='cookie-banner' i]", "[class*='cookie-banner' i]", "[id*='CookieConsent' i]", "[class*='cookieconsent' i]",
                    "[aria-label*='cookie' i]", "[id*='gdpr' i]", ".cc-window", "#hs-eu-cookie-confirmation", "[class*='consent-banner' i]"]
SWEEP_JS = """(sels) => {
  const sweep = () => {
    for (const s of sels) { try { document.querySelectorAll(s).forEach(e => e.remove()); } catch (e) {} }
    for (const e of document.querySelectorAll('div, section, aside, dialog')) {
      const st = getComputedStyle(e);
      if ((st.position === 'fixed' || st.position === 'sticky') && /cookie|consent|we use cookies/i.test(e.textContent || '') && e.getBoundingClientRect().height < innerHeight * 0.45) e.remove();
    }
    document.documentElement.style.scrollBehavior = 'auto';
  };
  sweep(); if (!window.__sweeper) window.__sweeper = setInterval(sweep, 250);
}"""
CURSOR_JS = """() => {
  if (document.getElementById('__cursor')) return;
  const c = document.createElement('div'); c.id = '__cursor';
  c.innerHTML = `<svg width="28" height="36" viewBox="0 0 28 36" xmlns="http://www.w3.org/2000/svg"><path d="M3 2 L3 29 L10 22 L15 34 L20 32 L15 20 L25 20 Z" fill="#fff" stroke="#111" stroke-width="2" stroke-linejoin="round"/></svg>`;
  Object.assign(c.style, {position:'fixed', left:'0px', top:'0px', zIndex: 2147483647, pointerEvents:'none', filter:'drop-shadow(0 2px 3px rgba(0,0,0,.45))', transform:'translate(-3px,-2px)'});
  document.body.appendChild(c);
  const ring = document.createElement('div'); ring.id = '__cursor_ring';
  Object.assign(ring.style, {position:'fixed', width:'44px', height:'44px', borderRadius:'50%', border:'3px solid #DC244C', opacity:'0', zIndex: 2147483646, pointerEvents:'none', transform:'translate(-22px,-22px) scale(0.4)'});
  document.body.appendChild(ring);
  window.__moveCursor = (x, y) => { c.style.left = x + 'px'; c.style.top = y + 'px'; ring.style.left = x + 'px'; ring.style.top = y + 'px'; };
  window.__clickRing = () => { ring.style.transition = 'none'; ring.style.opacity = '0.9'; ring.style.transform = 'translate(-22px,-22px) scale(0.4)';
    requestAnimationFrame(() => { ring.style.transition = 'opacity .45s ease-out, transform .45s ease-out'; ring.style.opacity = '0'; ring.style.transform = 'translate(-22px,-22px) scale(1.4)'; }); };
  window.__highlight = (top, left, width, height, color) => {
    const h = document.createElement('div'); h.className = '__hl';
    Object.assign(h.style, {position:'absolute', top: top + 'px', left: left + 'px', width: width + 'px', height: height + 'px', border: '3px solid ' + color, borderRadius: '10px',
      boxShadow: '0 0 0 4px rgba(0,0,0,0.0), 0 0 24px ' + color + '66', pointerEvents:'none', zIndex: 2147483645, opacity: '0', transition: 'opacity .35s ease-out'});
    document.body.appendChild(h); requestAnimationFrame(() => { h.style.opacity = '1'; });
  };
}"""
SECTIONS_JS = """() => {
  const heads = [...document.querySelectorAll('h1, h2, h3, h4')].filter(h => h.offsetParent !== null && (h.textContent || '').trim().length > 0);
  const out = [];
  for (let i = 0; i < heads.length; i++) {
    const h = heads[i]; const r = h.getBoundingClientRect(); const top = r.top + scrollY;
    let body = '', code = false, img = false, table = false, n = 0, el = h.nextElementSibling;
    while (el && !/^H[1-4]$/.test(el.tagName) && n < 12) {
      if (el.querySelector && (el.querySelector('pre') || el.tagName === 'PRE')) code = true;
      if (el.querySelector && (el.querySelector('img, svg, video') || el.tagName === 'IMG')) img = true;
      if (el.querySelector && (el.querySelector('table') || el.tagName === 'TABLE')) table = true;
      if (body.length < 400) body += ' ' + (el.innerText || '').replace(/\\s+/g, ' ').trim();
      el = el.nextElementSibling; n++;
    }
    const next = heads[i + 1]; const nextTop = next ? next.getBoundingClientRect().top + scrollY : document.body.scrollHeight;
    out.push({ index: i, tag: h.tagName, text: (h.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 120), id: h.id || '', top: Math.round(top), left: Math.round(r.left), width: Math.round(r.width),
               height: Math.round(Math.min(nextTop - top, 1400)), body: body.trim().slice(0, 400), has_code: code, has_image: img, has_table: table });
  }
  return { title: document.title, page_height: document.body.scrollHeight, sections: out };
}"""

def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def ease(a, b, k):
    k = 0 if k < 0 else 1 if k > 1 else k
    k = k * k * (3 - 2 * k)
    return a + (b - a) * k

def tokens(s):
    s = re.sub(r"[\-‐‑‒–—_/]", " ", (s or "").lower())      # "high-performance" -> "high performance"
    return [w for w in re.findall(r"[a-z0-9]+", s) if w not in STOP and len(w) > 2]

def launch(p, a, record_dir=None):
    kw = dict(headless=not getattr(a, "headful", False))
    channel = getattr(a, "channel", "chrome")
    browser = None
    for ch in ([channel] if channel == "chromium" else [channel, "msedge", "chrome", "chromium"]):
        try:
            browser = p.chromium.launch(channel=ch, **kw) if ch != "chromium" else p.chromium.launch(**kw)
            break
        except Exception:
            continue
    if browser is None:
        raise SystemExit("no browser could be started. Install Google Chrome or Microsoft Edge, or run: python -m playwright install chromium")
    ctx_kw = dict(viewport={"width": a.width, "height": a.height}, device_scale_factor=a.scale, color_scheme="light" if getattr(a, "light", False) else "dark")
    if getattr(a, "state", None): ctx_kw["storage_state"] = a.state
    if record_dir: ctx_kw.update(record_video_dir=record_dir, record_video_size={"width": a.width, "height": a.height})
    return browser, browser.new_context(**ctx_kw)

THEME_SWITCHES = [".theme-switch", "[aria-label*='theme' i]", "[title*='theme' i]", "button[class*='theme-toggle' i]", "button[class*='color-mode' i]", "[data-theme-toggle]"]
def open_page(ctx, url, a, extra_hide=()):
    page = ctx.new_page()
    try:
        page.goto(url, wait_until="networkidle", timeout=a.timeout * 1000)
    except Exception:
        page.goto(url, wait_until="load", timeout=a.timeout * 1000)
    page.evaluate(SWEEP_JS, BANNER_SELECTORS + list(extra_hide))
    # sites with their own theme switch ignore prefers-color-scheme; click the switch until the page matches
    want_light = bool(getattr(a, "light", False))
    def page_lum():
        import io
        from PIL import Image
        im = Image.open(io.BytesIO(page.screenshot(clip={"x": a.width * 0.2, "y": a.height * 0.2, "width": a.width * 0.6, "height": a.height * 0.6}))).convert("L")
        return sum(im.resize((40, 30)).getdata()) / 1200.0
    for _ in range(2):
        if (page_lum() > 128) == want_light: break
        clicked = False
        for sel in THEME_SWITCHES:
            try:
                loc = page.locator(sel)
                for i in range(min(loc.count(), 6)):
                    if loc.nth(i).is_visible():
                        loc.nth(i).click(timeout=1500); clicked = True; time.sleep(0.6); break
            except Exception:
                continue
            if clicked: break
        if not clicked: break
    for sel in getattr(a, "pre_click", None) or []:
        try: page.locator(sel).first.click(timeout=2500); time.sleep(0.5)
        except Exception as e: print(f"pre-click {sel} failed: {str(e)[:80]}", file=sys.stderr)
    time.sleep(0.4)
    return page

def add_common(sp):
    sp.add_argument("--width", type=int, default=1920); sp.add_argument("--height", type=int, default=1080)
    sp.add_argument("--scale", type=float, default=1.0, help="device scale factor (1 = crisp 1080p, 2 = retina look, heavier)")
    sp.add_argument("--light", action="store_true", help="light color scheme (default dark)")
    sp.add_argument("--channel", default="chrome", help="chrome | msedge | chromium")
    sp.add_argument("--state", default=None, help="Playwright storage_state JSON for pages that need a login (you create it)")
    sp.add_argument("--hide", action="append", default=[], help="extra CSS selector to remove before recording")
    sp.add_argument("--pre-click", action="append", default=[], help="CSS selector to click before recording (open a tab, dismiss a modal)")
    sp.add_argument("--timeout", type=int, default=45)
    sp.add_argument("--headful", action="store_true")

# ----------------------------------------------------------------------------- inspect
def do_inspect(a, _ctx=None):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser, ctx = launch(p, a)
        page = open_page(ctx, a.url, a, a.hide)
        # let lazy sections load
        h = page.evaluate("document.body.scrollHeight"); y = 0
        while y < min(h, 12000):
            page.evaluate(f"window.scrollTo(0, {y})"); time.sleep(0.12); y += 900
        page.evaluate("window.scrollTo(0, 0)"); time.sleep(0.4)
        data = page.evaluate(SECTIONS_JS)
        data["url"] = a.url; data["viewport"] = [a.width, a.height]
        browser.close()
    if getattr(a, "out", None):
        json.dump(data, open(a.out, "w"), indent=1)
    if getattr(a, "table", False) or not getattr(a, "out", None):
        print(f"{data['title']}  ({data['page_height']} px tall, {len(data['sections'])} sections)")
        for s in data["sections"]:
            flags = "".join(["c" if s["has_code"] else "-", "i" if s["has_image"] else "-", "t" if s["has_table"] else "-"])
            print(f"  [{s['index']:2d}] y={s['top']:6d}  {s['tag']:2s} {flags}  {s['text'][:70]}")
    return data

# ----------------------------------------------------------------------------- plan
def score_section(s, match):
    q = tokens(match)
    if not q: return 0.0
    ht, bt = set(tokens(s["text"])), set(tokens(s["body"]))
    qs = set(q)
    head = len(qs & ht) / len(qs)
    body = len(qs & bt) / len(qs)
    # bigram bonus on the heading
    qb = set(zip(q, q[1:])); hb = set(zip(tokens(s["text"]), tokens(s["text"])[1:]))
    big = len(qb & hb) / max(1, len(qb))
    import difflib
    fuzz = difflib.SequenceMatcher(None, match.lower(), s["text"].lower()).ratio()
    score = 3.0 * head + 1.0 * body + 1.5 * big + 1.0 * fuzz
    # lines about doing something ("run it in docker", "one command", "pip install") belong on a code block
    if s.get("has_code") and qs & {"command", "run", "install", "docker", "pip", "npm", "curl", "cli", "terminal", "code", "snippet", "request", "query"}: score += 0.6
    return round(score - s.get("top", 0) / 1e6, 3)     # ties go to the section nearer the top

def build_plan(data, sec, a):
    W, H = a.width, a.height
    dur = a.duration
    style = a.style
    top = sec["top"] if sec else 0
    y_target = max(0, top - int(H * 0.28))
    cx = min(W - 200, max(300, (sec["left"] if sec else W * 0.35) + 360))
    steps, t = [], 0.3
    if style == "readthrough":
        start = max(0, top - int(H * 0.5))
        steps = [{"t": 0.3, "move": [cx, int(H * 0.55)], "dur": 0.8}, {"t": 1.0, "scroll": start + int(110 * (dur - 1.4)), "dur": dur - 1.4}]
        return {"start_y": start, "steps": steps}
    start = max(0, y_target - (520 if style != "hover" else 0))
    if style != "hover":
        steps.append({"t": t, "move": [cx, int(H * 0.6)], "dur": 0.8}); t += 0.9
        steps.append({"t": t, "scroll": y_target, "dur": 1.7}); t += 1.9
    else:
        steps.append({"t": t, "move": [cx, int(H * 0.5)], "dur": 0.8}); t += 0.9
    if sec:
        if style == "highlight":
            # the box is the payoff of this style: fire it the moment the scroll settles, before the cursor arrives
            steps.append({"t": t, "highlight": {"heading": sec["text"], "height": min(sec["height"], int(H * 0.55))}}); t += 0.25
        steps.append({"t": t, "hover": {"heading": sec["text"]}, "dur": 0.8}); t += 0.9
        if style == "look":
            # the composer does the looking (push, mark, hold): the page must sit dead still from here on
            return {"start_y": start, "steps": steps}
        steps.append({"t": t, "click": True}); t += 0.5
        if sec.get("has_code"):
            steps.append({"t": t, "hover": {"heading": sec["text"], "offset": [120, 260]}, "dur": 0.8}); t += 0.9
    # short clips: compress the step timings so everything lands inside the duration
    planned_end = max(st["t"] + st.get("dur", 0.9) for st in steps) if steps else 0
    if planned_end > dur - 0.4:
        f = (dur - 0.4) / planned_end
        for st in steps:
            st["t"] = round(st["t"] * f, 2)
            if "dur" in st: st["dur"] = round(max(0.3, st["dur"] * f), 2)
        t = round(t * f, 2)
    # closing drift: never push the matched heading off the top of the frame
    rest = dur - t - 0.2
    if rest > 0.8:
        heading_vp_y = (top - y_target) if style != "hover" else (top - start)
        room = max(0, int(heading_vp_y) - 70)
        drift = int(min(420, 140 * rest, room if sec else 420))
        if drift >= 40:
            steps.append({"t": t, "scroll": (y_target if style != "hover" else start) + drift, "dur": rest})
    return {"start_y": start, "steps": steps}

def do_plan(a):
    data = a._data if hasattr(a, "_data") else do_inspect(argparse.Namespace(**{**vars(a), "out": None, "table": False}))
    secs = data["sections"]
    chosen, score = None, 0.0
    if getattr(a, "section", None):
        cands = [s for s in secs if a.section.lower() in s["text"].lower()]
        chosen = cands[0] if cands else None
        if chosen and a.match: score = score_section(chosen, a.match)
        if not chosen: print(f"no heading contains '{a.section}'; falling back to --match", file=sys.stderr)
    if not chosen and a.match:
        ranked = sorted(secs, key=lambda s: -score_section(s, a.match))
        if ranked:
            chosen, score = ranked[0], score_section(ranked[0], a.match)
            if getattr(a, "verbose", False):
                for s in ranked[:5]: print(f"  {score_section(s, a.match):5.2f}  y={s['top']:6d}  {s['text'][:60]}")
    if chosen and score < 0.35 and not getattr(a, "section", None) and a.match:
        print(f"WARNING: weak match ({score}); best guess is '{chosen['text']}'. Run `inspect --table` and pass --section to pin it.", file=sys.stderr)
    plan = {"url": a.url, "match": a.match, "section": chosen, "match_score": score, "style": a.style, "duration": a.duration,
            "width": a.width, "height": a.height, "scale": a.scale, "light": a.light, "hide": a.hide, "state": a.state, "channel": a.channel, "pre_click": getattr(a, "pre_click", [])}
    plan.update(build_plan(data, chosen, a))
    out = a.out or "plan.json"
    json.dump(plan, open(out, "w"), indent=1)
    print(f"plan -> {out}   section: {chosen['text'] if chosen else '(top of page)'}   score {score}   style {a.style}   {a.duration}s")
    return plan

# ----------------------------------------------------------------------------- record
def ensure_pw_ffmpeg():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "ffmpeg"], check=True, capture_output=True)
        return True
    except Exception:
        return False

LAST_BOX = {}   # filled by do_record: where the matched section sat on screen at the end (viewport px)

def do_record(a):
    from playwright.sync_api import sync_playwright
    plan = json.load(open(a.plan)) if isinstance(a.plan, str) else a.plan
    for k in ("width", "height", "scale", "light", "hide", "state", "channel", "pre_click"):
        if plan.get(k) is not None and getattr(a, k, None) in (None, [], False, 1920, 1080, 1.0, "chrome"):
            setattr(a, k, plan[k])
    W, H, dur = a.width, a.height, plan.get("duration", 6)
    tmp = tempfile.mkdtemp(prefix="broll_")
    for attempt in range(2):
        try:
            with sync_playwright() as p:
                browser, ctx = launch(p, a, record_dir=tmp)
                t_page = time.time()
                page = open_page(ctx, plan["url"], a, a.hide)
                page.evaluate(f"window.scrollTo(0, {plan.get('start_y', 0)})")
                page.evaluate(CURSOR_JS)
                cur = [W * 0.55, H * 0.6]
                page.mouse.move(*cur); page.evaluate("([x, y]) => window.__moveCursor(x, y)", cur)
                time.sleep(0.6)
                t_start = time.time(); trim = max(0.0, t_start - t_page - 0.1)
                y_now = plan.get("start_y", 0)
                def heading_box(spec):
                    txt = spec.get("heading") if isinstance(spec, dict) else None
                    sel = spec.get("selector") if isinstance(spec, dict) else spec
                    try:
                        if txt:
                            box = page.evaluate("""(t) => { const h = [...document.querySelectorAll('h1,h2,h3,h4')].find(e => (e.textContent||'').replace(/\\s+/g,' ').trim().startsWith(t.slice(0, 40)));
                                if (!h) return null; const r = h.getBoundingClientRect(); return {x: r.left, y: r.top, width: r.width, height: r.height, top: r.top + scrollY}; }""", txt)
                        else:
                            box = page.locator(sel).first.bounding_box(timeout=1500)
                    except Exception:
                        box = None
                    return box
                for s in sorted(plan["steps"], key=lambda s: s["t"]):
                    while time.time() - t_start < s["t"]: time.sleep(0.005)
                    length = s.get("dur", 0.9)
                    if "scroll" in s:
                        y0, y1, t0, sent = y_now, s["scroll"], time.time(), 0.0
                        while True:
                            k = (time.time() - t0) / length
                            want = ease(0, y1 - y0, k); d = want - sent
                            if abs(d) >= 1: page.mouse.wheel(0, d); sent += d
                            if k >= 1: break
                            time.sleep(1 / 60)
                        y_now = y1
                    if "move" in s or "hover" in s or "click" in s:
                        target = cur
                        if "move" in s: target = s["move"]
                        elif "hover" in s:
                            box = heading_box(s["hover"])
                            off = s["hover"].get("offset", [0, 0]) if isinstance(s["hover"], dict) else [0, 0]
                            if box: target = [box["x"] + min(box["width"] * 0.5, 160) + off[0], box["y"] + box["height"] / 2 + off[1]]
                        if target != cur:
                            x0, y0, t0 = cur[0], cur[1], time.time()
                            while True:
                                k = (time.time() - t0) / length
                                x, y = ease(x0, target[0], k), ease(y0, target[1], k)
                                page.evaluate("([x, y]) => window.__moveCursor(x, y)", [x, y]); page.mouse.move(x, y)
                                if k >= 1: break
                                time.sleep(1 / 90)
                            cur = list(target)
                        if s.get("click"):
                            page.evaluate("() => window.__clickRing()")
                            if s.get("real_click"): page.mouse.click(cur[0], cur[1])
                    if "highlight" in s:
                        box = heading_box(s["highlight"])
                        if box:
                            hh = s["highlight"].get("height", 400) if isinstance(s["highlight"], dict) else 400
                            page.evaluate("([t, l, w, h, c]) => window.__highlight(t, l, w, h, c)", [box["top"] - 12, box["x"] - 16, min(box["width"] + 32, W * 0.6), hh, s["highlight"].get("color", "#DC244C") if isinstance(s["highlight"], dict) else "#DC244C"])
                # measure where the matched section really sits now that everything has settled (viewport px):
                # the heading, and the block from the heading down to the next heading. Marks and pushes use this.
                sec_txt = (plan.get("section") or {}).get("text")
                if sec_txt:
                    try:
                        LAST_BOX.clear(); LAST_BOX.update(page.evaluate("""(t) => {
                            const hs = [...document.querySelectorAll('h1,h2,h3,h4')];
                            const h = hs.find(e => (e.textContent||'').replace(/\\s+/g,' ').trim().startsWith(t.slice(0, 40)));
                            if (!h) return {};
                            const r = h.getBoundingClientRect();
                            let x0 = r.left, y0 = r.top, x1 = r.right, y1 = r.bottom, n = h.nextElementSibling, k = 0;
                            while (n && k < 12 && !/^H[1-4]$/.test(n.tagName)) {
                                const q = n.getBoundingClientRect();
                                if (q.height > 0 && q.top < innerHeight) { x0 = Math.min(x0, q.left); x1 = Math.max(x1, q.right); y1 = Math.max(y1, q.bottom); }
                                n = n.nextElementSibling; k++; }
                            y1 = Math.min(y1, innerHeight - 8);
                            return {heading: {x: r.left, y: r.top, w: r.width, h: r.height}, block: {x: x0, y: y0, w: x1 - x0, h: y1 - y0}}; }""", sec_txt) or {})
                    except Exception:
                        pass
                while time.time() - t_start < dur + 0.7: time.sleep(0.05)     # the capture flushes late; leave room so the cut lands at the full duration
                t_close = time.time()
                ctx.close(); browser.close()
            break
        except Exception as e:
            if "ffmpeg" in str(e).lower() and attempt == 0:
                print("Playwright's ffmpeg is missing; installing it (python -m playwright install ffmpeg) ...", file=sys.stderr)
                ensure_pw_ffmpeg(); continue
            raise
    webm = [f for f in os.listdir(tmp) if f.endswith(".webm")]
    if not webm: raise SystemExit("no video was captured")
    # Playwright starts the capture at the page's first paint, not when the page is requested, and a cold load can
    # take a second or more. The capture ends at close, so its true start is close-time minus captured length.
    captured = probe(os.path.join(tmp, webm[0]))["duration"]
    if captured:
        video_start = t_close - captured
        trim = max(0.0, t_start - video_start)
    out = a.out
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{trim:.2f}", "-i", os.path.join(tmp, webm[0]), "-t", str(dur),
                    "-vf", f"scale={W}:{H}" + (f",minterpolate=fps={a.fps}:mi_mode=mci:mc_mode=obmc:me_mode=bidir:search_param=16" if (a.fps > 40 and not getattr(a, "no_interp", False)) else ""),
                    "-r", str(a.fps), "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-an", out], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"recorded -> {out}  ({dur}s, {W}x{H}, {a.fps} fps)")
    return out

# ----------------------------------------------------------------------------- review
def probe(path):
    info = subprocess.run([ffmpeg(), "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info); dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else None
    r = re.search(r", (\d{3,5})x(\d{3,5})", info); fps = re.search(r"([\d.]+) fps", info)
    return {"duration": dur, "width": int(r[1]) if r else None, "height": int(r[2]) if r else None, "fps": float(fps[1]) if fps else None}

def do_review(a):
    import numpy as np
    from PIL import Image
    clip = a.clip
    base = os.path.splitext(clip)[0]
    sheet = a.sheet or base + "_sheet.png"
    info = probe(clip)
    n = max(4, int(info["duration"] or 6))
    subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-i", clip, "-vf", f"fps=1,scale=480:-1,tile={min(n, 4)}x{math.ceil(n / 4)}", "-frames:v", "1", sheet], check=True)
    tmp = tempfile.mkdtemp(prefix="rev_")
    subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-i", clip, "-vf", "fps=2,scale=320:-1", os.path.join(tmp, "s_%03d.png")], check=True)
    frames = [np.asarray(Image.open(os.path.join(tmp, f)).convert("L"), dtype=np.float32) for f in sorted(os.listdir(tmp))]
    shutil.rmtree(tmp, ignore_errors=True)
    bright = float(np.mean([f.mean() for f in frames])) if frames else 0
    detail = float(np.mean([f.std() for f in frames])) if frames else 0        # a dark page with text has detail; a black clip does not
    motion = float(np.mean([np.abs(frames[i + 1] - frames[i]).mean() for i in range(len(frames) - 1)])) if len(frames) > 1 else 0
    checks = {"has_duration": bool(info["duration"] and info["duration"] >= 2), "is_1080p": info["width"] == 1920 and info["height"] == 1080,
              "not_black": bright > 3 and detail > 8, "not_blank": bright < 243, "has_motion": motion > 0.6, "size_ok": os.path.getsize(clip) > 200_000}
    rev = {"clip": clip, "sheet": sheet, **info, "brightness": round(bright, 1), "detail": round(detail, 1), "motion": round(motion, 2), "checks": checks, "ok": all(checks.values())}
    if a.out: json.dump(rev, open(a.out, "w"), indent=1)
    print(f"review: {'OK' if rev['ok'] else 'PROBLEMS'}  {info['width']}x{info['height']} {info['duration']}s {info['fps']}fps  brightness {bright:.0f}  motion {motion:.2f}  -> {sheet}")
    for k, v in checks.items():
        if not v: print(f"  FAIL {k}")
    return rev

# ----------------------------------------------------------------------------- auto / batch
STYLE_HINTS = {
    "docs": "fullscreen-pip: page full-screen with a slow push, presenter as a small bottom-right PiP, caption pill of the spoken line.",
    "article": "fullscreen-pip, or evidence-card if only one paragraph matters: crop it, tilt it over the shoulder, draw a red box on the key lines.",
    "home": "window: the clip in a browser-chrome window floating beside or behind the presenter; or fullscreen with a push.",
    "pricing": "fullscreen-pip, cursor parked on the plan the line names; pricing pages are often light-only, so dim or vignette them in a dark edit.",
    "dashboard": "fullscreen with the presenter PiP framed top-right; keep the cursor slow and let the data be the subject.",
}
def guess_kind(url, data):
    u = url.lower()
    if "/documentation" in u or "/docs" in u: return "docs"
    if "pricing" in u or "/plans" in u: return "pricing"
    if "/articles/" in u or "/blog/" in u or "/post" in u: return "article"
    if any(k in u for k in ("cloud.", "dashboard", "console")): return "dashboard"
    path = re.sub(r"https?://[^/]+", "", u).strip("/")
    return "home" if path == "" else "article"

def do_auto(a):
    os.makedirs(a.out, exist_ok=True)
    name = a.name or re.sub(r"[^a-z0-9]+", "_", (a.match or a.url)[:40].lower()).strip("_") or "clip"
    ia = argparse.Namespace(**{**vars(a), "out": os.path.join(a.out, name + "_sections.json"), "table": False})
    data = do_inspect(ia)
    pa = argparse.Namespace(**{**vars(a), "out": os.path.join(a.out, name + "_plan.json"), "_data": data})
    plan = do_plan(pa)
    ra = argparse.Namespace(**{**vars(a), "plan": plan, "out": os.path.join(a.out, name + ".mp4")})
    clip = do_record(ra)
    va = argparse.Namespace(clip=clip, sheet=os.path.join(a.out, name + "_sheet.png"), out=os.path.join(a.out, name + "_review.json"))
    rev = do_review(va)
    kind = guess_kind(a.url, data)
    man = {"name": name, "url": a.url, "page_title": data["title"], "kind": kind, "spoken_line": a.match, "section": plan["section"]["text"] if plan["section"] else None,
           "section_y": plan["section"]["top"] if plan["section"] else 0, "match_score": plan["match_score"], "style": plan["style"], "clip": os.path.abspath(clip),
           "duration": rev["duration"], "width": rev["width"], "height": rev["height"], "fps": rev["fps"], "sheet": os.path.abspath(rev["sheet"]), "review_ok": rev["ok"],
           "caption_suggestion": (a.match or plan["section"]["text"] if plan["section"] else "").strip(), "ae_style_hint": STYLE_HINTS[kind],
           "page_scheme": "light" if rev["brightness"] > 128 else "dark",
           "notes": ("the page rendered light (no dark theme); dim or vignette it in a dark edit, or pass --light on purpose" if rev["brightness"] > 128 and not a.light else ""),
           "suggested_in": 0.0, "suggested_out": rev["duration"], "plan": os.path.abspath(pa.out), "sections": os.path.abspath(ia.out),
           "section_box": dict(LAST_BOX)}   # heading + block rects in viewport px, measured after the moves settled
    if getattr(a, "compose", None):
        # bake the style with compose.py so the result works in any editor
        here = os.path.dirname(os.path.abspath(__file__))
        ext = ".mov" if (a.compose in ("evidence-card", "window") and not getattr(a, "presenter", None)) else ".mp4"
        cout = os.path.join(a.out, f"{name}_{a.compose.replace('-', '_')}{ext}")
        cmd = [sys.executable, os.path.join(here, "compose.py"), clip, "--style", a.compose, "--out", cout, "--caption", man["caption_suggestion"], "--url", a.url]
        if getattr(a, "presenter", None): cmd += ["--presenter", a.presenter, "--at", str(getattr(a, "at", 0.0))]
        subprocess.run(cmd, check=True)
        man["composed"] = {"style": a.compose, "file": os.path.abspath(cout), "kind": "overlay-with-alpha" if ext == ".mov" else ("section-with-presenter-audio" if getattr(a, "presenter", None) else "clip")}
    mp = os.path.join(a.out, name + "_manifest.json")
    json.dump(man, open(mp, "w"), indent=1)
    print(f"manifest -> {mp}")
    return man

def do_batch(a):
    jobs = json.load(open(a.jobs))
    mans = []
    for j in jobs:
        ja = argparse.Namespace(**{**vars(a), **{k: v for k, v in j.items() if k != "name"}, "name": j.get("name")})
        for k, d in (("match", None), ("duration", 6), ("style", "reveal"), ("section", None)):
            if not hasattr(ja, k): setattr(ja, k, d)
        try:
            mans.append(do_auto(ja))
        except Exception as e:
            print(f"job {j.get('name') or j.get('url')} failed: {e}", file=sys.stderr)
    json.dump(mans, open(os.path.join(a.out, "manifests.json"), "w"), indent=1)
    print(f"{len(mans)} of {len(jobs)} jobs done -> {os.path.join(a.out, 'manifests.json')}")

# ----------------------------------------------------------------------------- cli
def ensure_deps():
    """First run on a new machine: install the pip packages quietly, and point at setup.py if that is not enough."""
    need = []
    for mod, pkg in {"playwright": "playwright", "imageio_ffmpeg": "imageio-ffmpeg", "PIL": "pillow", "numpy": "numpy"}.items():
        try: __import__(mod)
        except Exception: need.append(pkg)
    if need:
        print(f"installing {', '.join(need)} ...", file=sys.stderr)
        r = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check", *need], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"could not install {need}. Run: python {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'setup.py')}")

def main():
    ensure_deps()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("inspect"); s.add_argument("url"); s.add_argument("--out"); s.add_argument("--table", action="store_true"); add_common(s)
    s = sub.add_parser("plan"); s.add_argument("url"); s.add_argument("--match", default=""); s.add_argument("--section"); s.add_argument("--style", default="reveal", choices=["reveal", "hover", "highlight", "readthrough", "look"])
    s.add_argument("--duration", type=float, default=6); s.add_argument("--out"); s.add_argument("--verbose", action="store_true"); add_common(s)
    s = sub.add_parser("record"); s.add_argument("plan"); s.add_argument("--out", required=True); s.add_argument("--fps", type=int, default=60); s.add_argument("--no-interp", action="store_true", help="skip motion interpolation when upsampling the capture to 60 fps"); add_common(s)
    s = sub.add_parser("review"); s.add_argument("clip"); s.add_argument("--sheet"); s.add_argument("--out")
    s = sub.add_parser("auto"); s.add_argument("url"); s.add_argument("--match", default=""); s.add_argument("--section"); s.add_argument("--style", default="reveal", choices=["reveal", "hover", "highlight", "readthrough", "look"])
    s.add_argument("--duration", type=float, default=6); s.add_argument("--out", required=True); s.add_argument("--name"); s.add_argument("--fps", type=int, default=60); s.add_argument("--no-interp", action="store_true", help="skip motion interpolation when upsampling the capture to 60 fps"); s.add_argument("--verbose", action="store_true")
    s.add_argument("--compose", choices=["fullscreen", "fullscreen-pip", "evidence-card", "window"], help="also bake a finished, editor-agnostic file in this style")
    s.add_argument("--presenter", help="presenter video for --compose (PiP + audio)"); s.add_argument("--at", type=float, default=0.0, help="where the clip sits in the presenter video (s)")
    add_common(s)
    s = sub.add_parser("batch"); s.add_argument("jobs"); s.add_argument("--out", required=True); s.add_argument("--fps", type=int, default=60); s.add_argument("--no-interp", action="store_true", help="skip motion interpolation when upsampling the capture to 60 fps"); add_common(s)
    a = ap.parse_args()
    {"inspect": do_inspect, "plan": do_plan, "record": do_record, "review": do_review, "auto": do_auto, "batch": do_batch}[a.cmd](a)

if __name__ == "__main__":
    main()
