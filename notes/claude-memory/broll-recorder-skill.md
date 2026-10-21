---
name: broll-recorder-skill
description: "John's reusable B-roll skill (URL + spoken line -> recorded page clip -> editor-agnostic composed video) lives at ~/.claude/skills/broll-recorder; status and known gaps as of 2026-10-13"
metadata:
  node_type: memory
  type: project
  originSessionId: 39bc7a71-3509-46be-83a4-5d1a21b62df7
  modified: 2026-10-13T21:38:24.229Z
---

This is ONE skill in John's planned video-production suite (he also has a script-writing skill; the goal is getting videos out faster). Keep it focused on B-roll; don't expand scope. Front door is `scripts/shot.py` (docs / article / site / code / title / flow) with house defaults.

John asked (2026-10-13) for a skill that turns any URL (docs, article, site) plus the line he says at that moment into B-roll, usable by people without After Effects. Built at `C:\Users\ADMIN\.claude\skills\broll-recorder\`:
- `scripts/broll.py`: `inspect | plan | record | review | auto | batch` (section matching from the spoken line, 1080p Playwright recording with cursor overlay and banner stripping, contact sheet, manifest). `auto --compose STYLE --presenter talk.mp4 --at T` chains the composer.
- `scripts/compose.py`: bakes styles with ffmpeg: `fullscreen`, `fullscreen-pip` (face-cropped PiP + caption + presenter audio = finished section mp4), `evidence-card` and `window` (ProRes 4444 .mov overlays with alpha when no presenter is given).
- `scripts/ae_insert.jsx` for AE users; `references/styles.md` (six creator treatments); `references/plan-format.md`; `evals/evals.json` (3 prompts + assertions); workspace with iteration-1 runs in `broll-recorder-workspace/`.
- Eval round 1 (subagents): with-skill 6/6, 6/6, 6/6 after fixes; fixes made from their findings: trim computed from the capture's true start, highlight box fires right after the reveal scroll, closing drift keeps the heading in frame, hyphen-splitting tokenizer, code-block bonus for "run/install/docker" lines, pricing page kind, light-page note in the manifest.
- `scripts/script_broll.py SCRIPT.md --out DIR` (2026-10-13): reads markers like `[B-ROLL: URL | line | 5s | hover | section: X]` (also `{{...}}`, `<!-- -->`, `**B-roll:**`, CUTAWAY), uses the preceding sentence when no line is given, records all, writes shotlist.md/json and script.annotated.md. John's script-writing flow will emit these markers; tell writers the syntax (references/script-markers.md).
- `scripts/setup.py` makes a cold machine ready (pip packages, Chrome/Edge or Playwright Chromium, Playwright ffmpeg); verified in an empty venv. No After Effects anywhere in the pipeline.
- John's look for B-roll (2026-10-13): background rgb(245,244,240), page/editor stays Qdrant dark inside a rounded shadowed card, no red/blue washes; slow eased pushes into the subject (`compose.py --style clean --focus`); code shots via `code_broll.py` (typing IDE window, `--theme qdrant`). Modeled on Anthropic's "What is Claude Code?" video.
- Login flows (2026-10-13, worked): record John's real Chrome with ffmpeg gdigrab on display 2 (offset_x 1920), drive the real pointer with `scripts/osmouse.py`, find targets via Claude-in-Chrome `javascript_tool` (DPR 1.5 in his Chrome) or a gdigrab frame, cut with `scripts/cut_marks.py`. Qdrant Cloud login: docs "Log in" -> cloud.qdrant.io login -> "Continue with Google" -> account picker (john.kupchanko@qdrant.com is the second row) -> Clusters page (the "qdrant_demo" free cluster). No password was needed; never type one.
- 2026-10-13 later: clips are 60 fps files. Since 2026-10-19 motion interpolation is opt-in (`--interp`): minterpolate ghosted and doubled scrolling text, so the default repeats captured frames (about 24 new frames a second while scrolling). `shot.py look` = scroll, stop, push in, mark, hold, same-speed swoop out; `compose.py --beats` / `--mark` for custom timing. John's rule for marks: a RECTANGLE with a small even margin on the real element, measured after the scroll (manifest `section_box`), never a big circle. He wants demo reels as ONE video (hard cuts), not many files; README.md in the skill lists every option.
- 2026-10-19 (Bulk Uploads rebuild): `section:` in a marker now reaches the recorder through shot.py and script_broll.py (it was dropped, and clips landed on the wrong section while the review said OK). For docs B-roll cut in full frame: `script_broll.py SCRIPT --raw --style readthrough --zoom 1.4`; CSS zoom makes body text ~22 px and sharp (`--scale` cannot: Playwright records CSS px), readthrough opens on the heading. Check sections from the frames (video-review), not the manifest.
- Known limits: pages behind a login need the real-Chrome route above (or OBS); Playwright's own ffmpeg must be installed for capture (`python -m playwright install ffmpeg`); pricing pages are light-only.

**Why:** John wants to reuse this across videos and hand it to others; not everyone has After Effects, so the composed mp4/mov outputs are the primary deliverable.
**How to apply:** when John (or anyone) asks for website footage in a video, use this skill rather than rebuilding the recorder; related: [[after-effects-scripting-setup]], [[motion-design-feedback]].
