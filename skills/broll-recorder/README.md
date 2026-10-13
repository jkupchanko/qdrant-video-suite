# broll-recorder

**Say what to show. Get finished B-roll.**

One skill in the Qdrant video suite. Give it the line you say in the video and where the proof lives (a docs
page, an article, a site, a code file, or a flow like "log into Qdrant Cloud"), and it hands back a finished
clip. It drives a browser itself, finds the right section, records it with a visible cursor, and finishes it
in the house look. It needs nothing beyond the one-time setup: no screen recorder, no editor plug-ins, no hunting for the
paragraph that matches the sentence.

Watch `broll_skill_pitch.mp4` (77 seconds) before reading further.

## What it is for

Every explainer, tutorial, or launch video needs cutaways: the docs page you are talking about, the article
you are quoting, the code you are describing, the thing you click through. Making those by hand is the slow
part of editing: record the screen, trim, crop, add a zoom, match it to the last clip. This skill replaces
that loop. Every clip comes out the same shape, so a video made by three people looks like one person made it.

Use it when:

- a script says "show the docs here" or "cut to the pricing page"
- you want a slow slide down an article or a home page behind your voice
- you need a code snippet typing itself, or sitting still with a cursor, without opening an IDE
- you want the viewer to see a real flow (log in, create a cluster, open a dashboard) and don't want to record it
- you need a chapter title in the same look as the rest

Do not use it for: footage of the presenter, screen captures of desktop apps that are not in a browser,
or anything that needs a password typed (it stops at the Google account picker and never enters credentials).

## What comes out

Plain MP4, 1920x1080, 60 fps, drops into any editor.
The look is fixed:

- off-white background rgb(245,244,240)
- the page or editor inside a rounded card with a soft shadow; the page keeps its own colours
- a push that lands and holds; one clean swoop back out; never creeping zooms
- hard-cut safe: no slides, no fades to black

## How to use it

### 1. Set up once

```bash
python scripts/setup.py
```

Installs the Python packages, finds Chrome or Edge (or installs a Playwright Chromium), and fetches the
capture ffmpeg. Takes about a minute. Nothing else to install.

### 2. Make a shot

All commands run from `scripts/`. Pick by what the narration is doing:

| you are saying... | run |
|---|---|
| "the docs explain X" (zoom into the section that proves it) | `python shot.py docs URL --says "the line you say" --out DIR` |
| "look at this part" (zoom in, rectangle on the element, hold, zoom out) | `python shot.py look URL --says "the line" --out DIR` |
| "read this article" / "this is the site" (slow slide from the top) | `python shot.py site URL --out DIR --duration 10` |
| "here is the code" (editor types it in) | `python shot.py code FILE --out DIR` |
| same, but the code sits still | `python shot.py code FILE --out DIR --static` |
| a chapter title | `python shot.py title "Headline" --sub "small line" --out DIR` |
| "log in and open..." (a real click-through) | ask Claude with the skill loaded; it drives your real browser (see SKILL.md, "Pages behind a login") |

Each writes `<name>_shot.mp4` into DIR, plus the raw recording, a contact sheet image, and a manifest with
the section it matched. Open the sheet to check the right section is on screen; if it is wrong, add
`--section "Heading text"` to pin it.

### 3. Or hand it a whole script

Writers mark B-roll inline:

```
We batch the points so the server does less work. [B-ROLL: https://qdrant.tech/documentation/concepts/points/ | upload points in batches]
```

Then:

```bash
python scripts/script_broll.py SCRIPT.md --out DIR
```

It records every marker, finishes each one as a shot, and writes a shot list next to the clips. Marker
syntax (duration, style, section pins) is in `references/script-markers.md`.

### 4. Adjust if needed

- `--zoom-speed slow|normal|fast|snap` on docs/look/code shots
- `--hold 4` on a look shot to sit on the element longer
- `--light` on any recording to use the site's light theme
- `--fps 30` or `--no-interp` to skip the 60 fps upsample when speed matters (it costs about 2 minutes per 7 s of browser footage)

Everything else (custom zoom timing with `--beats`, marks, PiP and overlay styles for editors who want to
frame it themselves) is in `SKILL.md` and `references/styles.md`.

## Where it fits

This is the B-roll piece of a larger suite. The script-writing skill emits the `[B-ROLL: ...]` markers;
this skill turns them into clips; the edit assembles them. Each skill stays small on purpose so it can be
swapped or improved on its own.

## Files

```
broll-recorder/
  SKILL.md                 instructions Claude follows when the skill is loaded
  README.md                this file
  scripts/shot.py          the front door (docs, look, site, code, title)
  scripts/broll.py         the recorder (find section, record, review, manifest)
  scripts/compose.py       finishing (card, pushes, marks, PiP, overlays)
  scripts/code_broll.py    editor shots
  scripts/script_broll.py  whole-script runner
  scripts/setup.py         one-time setup
  references/              look rules, plan format, marker syntax
  evals/                   test prompts
```

Demo material: `broll_skill_pitch.mp4` (the reel) and `more_options/` (one clip per extra style).
