"""page_assets.py: the stills a docs page offers each of its sections, sharp, with the words around them.

  python page_assets.py URL --out DIR [--scale 2] [--light]

For every section of the page's own column (h2 / h3; the navigation's headings are skipped) it saves
  <slug>_figure_<k>.png   each figure / diagram (element screenshot at --scale device pixels, so it stays sharp when enlarged)
  <slug>_code_<k>.png     each code block, and its text
and writes DIR/assets.json: [{heading, level, tag ("Dense vectors"...), text (the section's paragraphs), figures [{png, caption}],
code [{png, text}], best_fit, watch_for}] - the labelled lines ("Best fit:", "Watch for:") are the page's own words for
pros and cons, so a style can put them on screen without inventing any.
Uses broll.py's page opener: cookie banners removed, dark theme matched.
"""
import os, sys, re, json, argparse, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import broll as B

JS = r"""() => {
  const col = document.querySelector('h1'); const left = col ? col.getBoundingClientRect().left : null;
  const hs = [...document.querySelectorAll('h2, h3')].filter(h => left === null || Math.abs(h.getBoundingClientRect().left - left) < 40);
  return hs.map((h, i) => {
    const items = []; let n = h.nextElementSibling;
    while (n && !/^H[1-3]$/.test(n.tagName)) { items.push(n); n = n.nextElementSibling; }
    const id = 'pa_' + i; const out = {heading: h.innerText.trim(), level: h.tagName, paras: [], figures: [], code: []};
    items.forEach((el, k) => {
      const t = (el.innerText || '').replace(/\s+/g, ' ').trim();
      if (el.tagName === 'FIGURE' || el.querySelector('figure')) { const f = el.tagName === 'FIGURE' ? el : el.querySelector('figure'); f.setAttribute('data-pa', id + '_f' + out.figures.length);
        out.figures.push({sel: '[data-pa="' + id + '_f' + out.figures.length + '"]', caption: (f.querySelector('figcaption') || {}).innerText || ''}); }
      else if (el.matches('div.highlight, pre') || el.querySelector('pre')) { el.setAttribute('data-pa', id + '_c' + out.code.length);
        out.code.push({sel: '[data-pa="' + id + '_c' + out.code.length + '"]', text: (el.innerText || '').trim()}); }
      else if (t) out.paras.push(t);
    });
    return out; }); }"""

def slug(s): return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("url"); ap.add_argument("--out", required=True); ap.add_argument("--scale", type=float, default=2.0); ap.add_argument("--light", action="store_true")
    ap.add_argument("--timeout", type=int, default=45); ap.add_argument("--channel", default="chrome")
    a = ap.parse_args(); a.out = os.path.abspath(a.out); os.makedirs(a.out, exist_ok=True)              # absolute paths in assets.json
    ns = argparse.Namespace(width=1920, height=1080, scale=a.scale, zoom=1.0, light=a.light, state=None, hide=[], pre_click=[], timeout=a.timeout, headful=False, channel=a.channel)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser, ctx = B.launch(p, ns); page = B.open_page(ctx, a.url, ns, [])
        h = page.evaluate("document.body.scrollHeight"); y = 0
        while y < h: page.evaluate(f"window.scrollTo(0, {y})"); time.sleep(0.1); y += 900          # lazy content loads
        page.evaluate("window.scrollTo(0, 0)"); time.sleep(0.4)
        secs = page.evaluate(JS); out = []
        for s in secs:
            base = slug(s["heading"]); rec = dict(heading=s["heading"], level=s["level"], figures=[], code=[])
            paras = s["paras"]; rec["tag"] = paras[0] if paras and len(paras[0].split()) <= 4 and "vector" in paras[0].lower() else ""
            rec["text"] = " ".join(x for x in paras if x != rec["tag"])
            rec["best_fit"] = next((x.split(":", 1)[1].strip() for x in paras if x.lower().startswith("best fit:")), "")
            rec["watch_for"] = next((x.split(":", 1)[1].strip() for x in paras if x.lower().startswith("watch for:")), "")
            for k, f in enumerate(s["figures"]):
                pth = os.path.join(a.out, f"{base}_figure_{k}.png"); page.locator(f["sel"]).first.screenshot(path=pth); rec["figures"].append(dict(png=pth, caption=f["caption"].strip()))
            for k, c in enumerate(s["code"]):
                pth = os.path.join(a.out, f"{base}_code_{k}.png"); page.locator(c["sel"]).first.screenshot(path=pth); rec["code"].append(dict(png=pth, text=c["text"]))
            out.append(rec)
        json.dump(dict(url=a.url, title=page.title(), sections=out), open(os.path.join(a.out, "assets.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        browser.close()
    print(f"{len(out)} sections, {sum(len(s['figures']) for s in out)} figures, {sum(len(s['code']) for s in out)} code blocks -> {os.path.join(a.out, 'assets.json')}")

if __name__ == "__main__":
    main()
