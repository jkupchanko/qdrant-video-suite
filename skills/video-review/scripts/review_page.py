#!/usr/bin/env python
"""review_page.py: a page to review a raw edit by clicking, not by typing times into a chat.

  python review_page.py CUT_DIR RAW.mp4 [--open]          -> CUT_DIR/review.html

The page plays CUT_DIR/cut.mp4 with every moment the raw edit check and the join check flagged listed beside it. Click a
time to jump there (2 s before it). Mark each one Fine or Fix, add a note, and press M (or "Add a moment") wherever you
see something the check missed. "Save notes" downloads review_notes.json; "Copy notes" puts the same as plain text on the
clipboard, to paste into a chat. Then:

  python ~/.claude/skills/editing/scripts/fix_cut.py CUT_DIR RAW.mp4 --notes review_notes.json

fixes every moment marked Fix that has a fix, and shows each added moment (the words, the pauses, the eyes) to decide on.
Decisions stay in the browser for this cut until the cut changes. The page is a local file next to the video: nothing is
uploaded, and anyone with the folder can open it.
"""
import argparse, html, json, os, sys, webbrowser
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import raw_edit_checks as RE, join_checks as JC

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Raw Edit Review</title>
<style>
:root{--bg:#f6f7f9;--panel:#fff;--ink:#14161a;--soft:#5b616b;--line:#e2e5ea;--fix:#c4302b;--check:#b26a00;--ok:#1f7a4d;--accent:#dc244c;--chip:#eef0f3}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0f1115;--panel:#171a20;--ink:#e9ebef;--soft:#9aa1ad;--line:#2a2f38;--fix:#ff6b62;--check:#f0a83a;--ok:#4cc38a;--chip:#222730}}
:root[data-theme="dark"]{--bg:#0f1115;--panel:#171a20;--ink:#e9ebef;--soft:#9aa1ad;--line:#2a2f38;--fix:#ff6b62;--check:#f0a83a;--ok:#4cc38a;--chip:#222730}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
header{padding:14px 16px;border-bottom:1px solid var(--line);display:flex;gap:12px;align-items:baseline;flex-wrap:wrap}
h1{font-size:17px;margin:0}header .sub{color:var(--soft);font-size:13px}
main{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(300px,1fr);gap:16px;padding:16px;max-width:1500px;margin:0 auto}
@media (max-width:900px){main{grid-template-columns:1fr}}
video{width:100%;background:#000;border-radius:10px;display:block}
.bar{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;align-items:center}
button{font:inherit;font-size:13px;border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:8px;padding:6px 10px;cursor:pointer}
button:hover{border-color:var(--soft)}button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
.now{font-variant-numeric:tabular-nums;color:var(--soft);font-size:13px;margin-left:auto}
#list{display:flex;flex-direction:column;gap:8px;max-height:calc(100vh - 120px);overflow:auto;padding-right:2px}
.m{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.m.on{border-color:var(--accent)}.m.fine{opacity:.55}
.top{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.t{font-weight:600;font-variant-numeric:tabular-nums;background:var(--chip);border:0}
.k{font-size:12px;padding:2px 7px;border-radius:99px;background:var(--chip);color:var(--soft)}
.sev-fix .k{color:var(--fix)}.sev-check .k{color:var(--check)}.sev-yours .k{color:var(--accent)}
.msg{margin:6px 0 8px;font-size:14px}
.dec{display:flex;gap:6px;align-items:center}.dec button.sel-fix{background:var(--fix);border-color:var(--fix);color:#fff}
.dec button.sel-fine{background:var(--ok);border-color:var(--ok);color:#fff}
.note{flex:1;min-width:120px;font:inherit;font-size:13px;padding:6px 8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink)}
.empty{color:var(--soft);padding:12px}
kbd{font-size:12px;border:1px solid var(--line);border-bottom-width:2px;border-radius:4px;padding:0 4px}
</style></head><body>
<header><h1>Raw edit review</h1><span class="sub">__TITLE__ · __N__ flagged · click a time to jump · <kbd>M</kbd> adds a moment at the playhead · <kbd>Space</kbd> plays</span></header>
<main>
<section><video id="v" src="cut.mp4" controls preload="metadata"></video>
<div class="bar"><button class="primary" id="add">Add a moment here</button><button id="save">Save notes</button><button id="copy">Copy notes</button><span class="now" id="now">0:00.0</span></div></section>
<section id="list"></section>
</main>
<script>
const DATA = __DATA__;
const KEY = "rawreview:" + DATA.key;
let S; try { S = JSON.parse(localStorage.getItem(KEY)) || {} } catch (e) { S = {} }
S.dec = S.dec || {}; S.note = S.note || {}; S.mine = S.mine || [];
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(S)) } catch (e) {} };
const v = document.getElementById("v"), list = document.getElementById("list");
const ts = t => `${Math.floor(t / 60)}:${(t % 60).toFixed(1).padStart(4, "0")}`;
function all() { return DATA.items.map((f, i) => ({...f, id: "f" + i})).concat(S.mine.map((m, i) => ({t: m.t, kind: "yours", sev: "yours", msg: "", id: "m" + i, mi: i}))).sort((a, b) => a.t - b.t) }
function render() {
  const items = all(); list.innerHTML = items.length ? "" : '<div class="empty">Nothing flagged. Watch it through and add a moment wherever something is off.</div>';
  for (const f of items) {
    const d = document.createElement("div"); d.className = `m sev-${f.sev}` + (S.dec[f.id] === "fine" ? " fine" : ""); d.dataset.t = f.t;
    d.innerHTML = `<div class="top"><button class="t">${ts(f.t)}</button><span class="k">${f.sev === "yours" ? "your moment" : f.sev + " · " + f.kind}</span></div>` +
      (f.msg ? `<div class="msg"></div>` : "") +
      `<div class="dec">` + (f.sev === "yours" ? `<button class="del">Remove</button>` : `<button class="fine">Fine</button><button class="fix">Fix</button>`) + `<input class="note" placeholder="${f.sev === "yours" ? "what is wrong here?" : "note (optional)"}"></div>`;
    if (f.msg) d.querySelector(".msg").textContent = f.msg;
    const note = d.querySelector(".note"), mine = f.sev === "yours" ? S.mine[f.mi] : null;   // your moments keep their own note
    note.value = (mine ? mine.note : S.note[f.id]) || ""; note.oninput = () => { if (mine) mine.note = note.value; else S.note[f.id] = note.value; save() };
    d.querySelector(".t").onclick = () => { v.currentTime = Math.max(0, f.t - 2); v.play() };
    const mark = (k) => { S.dec[f.id] = S.dec[f.id] === k ? undefined : k; save(); render() };
    if (f.sev !== "yours") {
      const fi = d.querySelector(".fine"), fx = d.querySelector(".fix");
      if (S.dec[f.id] === "fine") fi.classList.add("sel-fine"); if (S.dec[f.id] === "fix") fx.classList.add("sel-fix");
      fi.onclick = () => mark("fine"); fx.onclick = () => mark("fix");
    } else d.querySelector(".del").onclick = () => { S.mine.splice(f.mi, 1); save(); render() };
    list.appendChild(d);
  }
}
function add() { S.mine.push({t: +v.currentTime.toFixed(2)}); save(); render(); const el = [...list.querySelectorAll(".sev-yours")].find(e => Math.abs(+e.dataset.t - v.currentTime) < 0.05); if (el) { el.scrollIntoView({block: "center"}); el.querySelector(".note").focus() } }
function notes() {
  return {cut: DATA.key, items: all().map(f => ({t: f.t, kind: f.kind, sev: f.sev, decision: f.sev === "yours" ? "look" : (S.dec[f.id] || "unmarked"), note: (f.sev === "yours" ? S.mine[f.mi].note : S.note[f.id]) || "", msg: f.msg}))};
}
function text() { return notes().items.filter(i => i.decision !== "unmarked" || i.note).map(i => `${ts(i.t)} ${i.decision === "look" ? "LOOK" : i.decision.toUpperCase()} ${i.kind}${i.note ? ": " + i.note : ""}`).join("\n") || "No notes: the raw edit is approved as it is." }
document.getElementById("add").onclick = add;
document.getElementById("save").onclick = () => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([JSON.stringify(notes(), null, 1)], {type: "application/json"})); a.download = "review_notes.json"; a.click() };
document.getElementById("copy").onclick = async (e) => { try { await navigator.clipboard.writeText(text()); e.target.textContent = "Copied" } catch (err) { prompt("Copy these notes:", text()) } setTimeout(() => e.target.textContent = "Copy notes", 1500) };
document.addEventListener("keydown", e => { if (e.target.tagName === "INPUT") return; if (e.key === "m" || e.key === "M") { e.preventDefault(); add() } if (e.key === " ") { e.preventDefault(); v.paused ? v.play() : v.pause() } });
v.ontimeupdate = () => { document.getElementById("now").textContent = ts(v.currentTime); for (const el of list.children) el.classList.toggle("on", el.dataset && Math.abs(+el.dataset.t - v.currentTime) < 1.5) };
render();
</script></body></html>"""

def find(cut_dir, name):
    for d in (cut_dir, os.path.join(cut_dir, ".."), os.path.join(cut_dir, "..", "..")):
        if os.path.exists(os.path.join(d, name)): return os.path.abspath(os.path.join(d, name))

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cut_dir"); ap.add_argument("raw"); ap.add_argument("--literal"); ap.add_argument("--gaze"); ap.add_argument("--title"); ap.add_argument("--open", action="store_true")
    a = ap.parse_args(); cl = os.path.join(a.cut_dir, "cutlist.md"); items = []
    lit = a.literal or find(a.cut_dir, "words_literal.json"); gz = a.gaze or find(a.cut_dir, "raw_gaze.json")
    if lit:
        F, _ = RE.checks(a.raw, cl, lit, gz)
        items += [dict(t=round(f["t"], 2), kind=f["kind"], sev=f["sev"], msg=f["msg"]) for f in F if f["sev"] in ("fix", "check")]
    items += [dict(t=round(j["t"], 2), kind="join", sev=j["sev"], msg=j["msg"]) for j in JC.joins(a.raw, cl) if j["sev"] in ("fix", "check")]
    mp4 = os.path.join(a.cut_dir, "cut.mp4"); key = f"{os.path.abspath(mp4)}:{int(os.path.getmtime(mp4))}"
    title = a.title or os.path.basename(os.path.abspath(os.path.join(a.cut_dir, "..")))
    page = PAGE.replace("__DATA__", json.dumps(dict(items=sorted(items, key=lambda d: d["t"]), key=key)).replace("</", "<\\/")).replace("__TITLE__", html.escape(title)).replace("__N__", str(len(items)))
    out = os.path.join(a.cut_dir, "review.html"); open(out, "w", encoding="utf-8").write(page)
    print(f"{len(items)} flagged moments -> {out}")
    if a.open: webbrowser.open("file:///" + os.path.abspath(out).replace("\\", "/"))

if __name__ == "__main__":
    main()
