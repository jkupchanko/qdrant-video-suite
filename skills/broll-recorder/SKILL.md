---
name: broll-recorder
description: The B-roll skill of the video suite. The word "B-roll" (also b roll, broll, B-ROLL markers, cutaway) is the trigger. Whenever a person, a script, or another skill says B-roll, this skill records it, unless they are only explaining what B-roll is. It turns a URL (docs, article, product site, pricing page, blog, code file, or a click-through flow like a login) plus the line being said at that moment into a finished 1080p60 clip in one consistent look, with nothing to install beyond a one-time setup. Also use it for "scroll the docs", "grab the article", "record the site", "show the page while I talk about X", "zoom in on that section", code typing itself, a title card, or a script that contains B-ROLL markers to record in bulk. Trigger even if they just paste a URL and a line of script.
---

# B-roll recorder

Turns a URL plus "what the video says here" into a finished B-roll clip: the right section of the page, revealed
by a slow scroll, a visible cursor that glides to the heading and clicks, no cookie banners, 1080p, 60 fps, with
a contact sheet to check and a manifest describing where and how to use it. One command does the whole thing;
the pieces are separate for when a shot needs adjusting.

## Start here: the suite (house defaults, one command per shot)

`scripts/shot.py` is the front door. It applies the house look (off-white rgb(245,244,240) background, the page
or editor in a rounded shadowed card, slow push in, one swoop out, hard-cut safe) so every shot in a video
matches without anyone remembering flags. Pick the shot from what the narration is doing:

| narration is... | command |
|---|---|
| naming a feature or page | `shot.py docs URL --says "line" --out DIR` |
| making a claim one paragraph proves | `shot.py article URL --says "line" --out DIR` (section highlighted) |
| pointing at one thing: "look at this" | `shot.py look URL --says "line" --out DIR [--mark box\|underline] [--hold 2.5]` (scroll, stop, push in, rectangle on the real element, hold, swoop out) |
| introducing a product or site | `shot.py site URL --out DIR` (slow top-to-bottom glide) |
| showing or explaining code | `shot.py code FILE --out DIR [--static] [--lines a-b] [--run cmd]` |
| opening a chapter | `shot.py title "Headline" --sub "line" --out DIR` |
| clicking through or logging in | the real-browser method below (`flow`) |

Each writes `<name>_shot.mp4` (the finished shot, 1080p at 60 fps) next to the raw clip and manifest. Only drop to the lower-level
tools (`broll.py`, `compose.py`, `code_broll.py`) when a shot needs something the defaults don't cover; the
sections below explain those. Scripts with `[B-ROLL: ...]` markers go through `script_broll.py` (below), which
uses the same defaults. `README.md` next to this file lists every option with the clip it produces; hand that to
anyone who needs to pick a shot without reading the rest.

## When you have the two inputs

1. The URL. If the person only names a site ("the Qdrant payload docs"), find the exact page first (search or
   the site's nav) and confirm it opens without a login.
2. The spoken line (or the topic) at that point in the video. This is what picks the section: a docs page has
   dozens of headings and the viewer should see the one that proves the sentence.

Then run:

```bash
python <skill>/scripts/broll.py auto <URL> --match "<the spoken line>" --duration 6 --out <folder> --name <short_name>
```

It inspects the page, scores every heading against the line, writes a plan, records, reviews, and writes
`<name>_manifest.json` next to `<name>.mp4` and `<name>_sheet.png`. Read the printed `section:` and `score`,
then open the sheet (it is an image) and check that the matched heading is on screen and the page looks right.

## Which lines get B-roll at all (key terms)

B-roll follows the script's key terms, not its mood. A line that names something specific (HNSW,
quantization, a payload index, batch size, parallel workers, shards, on_disk, any identifier) gets the
section of the page that is about that thing. A line that is general talk ("this reduces RAM", "let's get
started", "thanks for watching", the hook) gets nothing: the person carries it. Generic words (memory,
disk, vectors, uploads) never earn an insert on their own. One insert per section: the first line that
names the thing gets it, later lines on the same thing hold. Run:

```bash
python <skill>/scripts/keyterms.py SCRIPT.md URL --out shotlist.md
```

`assets/keyterm-board.png` shows the rule on six lines. It prints every line with its terms, the matching section and the call (B-ROLL, hold, none), and writes
the B-ROLL markers the recorder reads. Read the "none" lines as the camera's: FULL, or SMALL over a card
that is already up.

## A whole script at once

When the person has a script (or an AI wrote one for them) with B-roll called out in it, don't record shot by
shot. `scripts/script_broll.py script.md --out <folder>` finds every marker such as
`[B-ROLL: https://site/page | what is being said]` (also `{{b-roll: ...}}`, `<!-- b-roll: ... -->`, `**B-roll:**`,
`CUTAWAY`), uses the sentence before a bare marker as the spoken line, records all of them, and writes
`shotlist.md` (script line, what is said, page, section matched, clip, caption, notes) plus `script.annotated.md`
with each marker followed by its clip's file name. Run with `--dry-run` first and show the person the shot list;
fix any "match weak" rows by adding `section:` to that marker, then record. Marker syntax is in
`references/script-markers.md`; tell script writers about it so their drafts come out ready to record.

For docs pages cut into an edit full frame, record raw with the readable settings:
`script_broll.py script.md --out <folder> --raw --style readthrough --zoom 1.4`. `--zoom` is CSS zoom on the page: the
text renders 1.4x bigger and stays sharp (about 22 px body text at 1080 instead of 16, which a phone can read), and the
docs layout still fits 1920 with the header on one line (1.5 wraps "Log in"). `--scale` does NOT do this: Playwright
records CSS pixels, so a higher device scale only pads the video. `--style readthrough` opens with the section's heading
just under the site header and reads down the section, stopping before the next heading rises past the middle.

## Judging the match, and fixing it

- Score above 1.0: the heading itself matched; use it.
- Score 0.35-1.0: the body text matched more than the heading. Usually right, but look at the sheet.
- Below 0.35 (the tool prints a warning): the line probably doesn't name anything on the page. Run
  `broll.py inspect <URL> --table` to see every heading with its position, pick one by eye, and re-run with
  `--section "<part of the heading>"`. For a homepage or a page with no useful headings, `--style readthrough`
  simply scrolls from the top; for a hero, `--style hover` stays put.

Why the section matters: a cutaway earns its place only when the viewer can see the thing the sentence claims.
A generic scroll of the right page is filler; the right paragraph under the right heading is evidence.

## Choosing the look

Read `references/styles.md` before inserting the clip. It catalogues the treatments creators use for website
B-roll (full-screen with a PiP and caption, evidence card over the shoulder, slow push, floating 3D window)
with when to use each and the recorder/insert settings. Match the video you are cutting into, not your taste:
if the edit already uses a monitor mockup, keep using it; if it is an Apple-style 3D space, use the floating window.

Quick defaults by page kind (the manifest's `ae_style_hint` says this too):

| Page | Record style | Treatment |
|---|---|---|
| docs page | `reveal` (default) | full-screen + PiP + caption |
| article, one paragraph is the point | `highlight` | evidence card, or full-screen with the red box |
| homepage / landing | `reveal` or `hover` | floating window or full-screen push |
| pricing / plans | `hover` on the plan | full-screen + PiP |

Match the colour scheme to the video: dark video, dark page (default); bright edit, add `--light` (the recorder
also flips a site's own theme switch when the page ignores the system setting). For the bright, calm "product
film" look (cream background, rounded card, slow pushes into the part being discussed) use `compose.py --style clean`
with one `--focus` per push; see styles.md section 6b.

## Code on screen

When the line is about code ("here's the call", "set batch_size to 256"), don't record a docs page; make the code
itself the B-roll with `scripts/code_broll.py snippet.py --out clip.mp4 --card --theme qdrant` (IDE-style
window, the snippet typing itself, optional `--run` terminal line, `--focus-lines a-b` push). Write the snippet to
a file first (8-20 lines, real API names), name it like a real file (`upload.py`), and match the theme to the edit.
See styles.md 6c.

## Delivering something anyone can use (no After Effects required)

Most people cut in Premiere, DaVinci, CapCut, Final Cut, iMovie or Descript, so the deliverable is a finished
video file, not a project. `scripts/compose.py` bakes the style into the clip with ffmpeg:

```bash
# a finished SECTION: the page full-screen with a push, the presenter's own footage as a face-cropped PiP,
# the caption pill, and the presenter's audio for that stretch. Drop it straight into the timeline.
python <skill>/scripts/compose.py <clip.mp4> --style fullscreen-pip --presenter <their talking-head video> --at <seconds where the clip sits> --caption "<spoken line>" --out <name>_section.mp4

# a transparent OVERLAY (ProRes 4444 .mov with alpha): the evidence card or the browser window, with shadow and
# slide-in, to lay above their footage in any editor that handles alpha (all of the ones above do).
python <skill>/scripts/compose.py <clip.mp4> --style evidence-card --duration 4 --out <name>_card.mov
python <skill>/scripts/compose.py <clip.mp4> --style window --url "<site>" --out <name>_window.mov

# the page alone with the push and caption, over a dark background (no presenter needed)
python <skill>/scripts/compose.py <clip.mp4> --style fullscreen --caption "<line>" --out <name>_full.mp4
```

`--manifest <name>_manifest.json` fills the caption and URL from the recording. The PiP crop finds the face
automatically; pass `--pip-crop cx,cy,w,h` to choose it by hand, `--pip-corner top-right` to move it.

Always hand back three things: the raw clip (`<name>.mp4`, for people who want to style it themselves), the
composed file for the style you chose, and the manifest. Say which editor-agnostic file is which in one line each.

If the person does use After Effects, `scripts/ae_insert.jsx` builds the same styles as live layers (fill the
CONFIG block from the manifest and run it on the open comp); if their project has its own helper library,
prefer that so the result matches the rest of the piece.

## Pages behind a login, and flows with real clicks

`broll.py` records its own signed-out browser, so it cannot show an account. For "click Log in, pick my Google
account, land on the dashboard" record the person's real Chrome instead:

1. Use the Claude in Chrome tools to open the page in their Chrome (their sessions are there), then put that window
   on one display, fullscreen (`scripts/osmouse.py key F11` after focusing it; check with `GetWindowRect`).
2. Capture that display with ffmpeg `gdigrab` (`-offset_x/-offset_y` of the monitor, 1920x1080, 30 fps) into a raw
   file, and note the capture start time.
3. Drive the REAL pointer with `scripts/osmouse.py move/click` (eased glide, slight arc) so the recording shows a
   genuine cursor; find targets with `javascript_tool` (`getBoundingClientRect`, scaled by `devicePixelRatio`) or
   by grabbing a single frame with gdigrab and reading it. Log the seconds of each click.
4. Never type a password or code. Account pickers and "Continue with Google" are fine because the person's
   session already exists; if a password or 2FA prompt appears, stop and let them do it, then resume.
5. `scripts/cut_marks.py RAW.mp4 OUT.mp4 --marks t1,t2,t3` keeps a short window around each click, waits for the
   final screen to fully load (frame comparison, not a timer), holds, and concatenates. Read the contact sheet:
   loaders and skeleton screens are the usual thing to trim.
6. Leave the browser as you found it (F11 off, your tab closed) and delete the long raw capture.

## Adjusting a shot

- Longer scroll or a different end point: `broll.py plan ... --out plan.json`, edit the `steps` (each has a
  time `t`, and one of `scroll` (absolute y), `move` [x, y], `hover` {"heading": text}, `click`, `highlight`),
  then `broll.py record plan.json --out clip.mp4`. See `references/plan-format.md`.
- A widget or popup in the way: `--hide "<css selector>"`.
- Page needs a login: ask the person to record it (OBS), or to give you a Playwright storage state (`--state`).
  Never type credentials yourself.
- Several clips for one video: write a `jobs.json` list of `{url, match, duration, name}` and run
  `broll.py batch jobs.json --out <folder>`; every job gets its own manifest, plus `manifests.json`.

## Rules that keep the clips good

- 4-8 seconds. For a reveal, start about half a screen above the section so the scroll reveals the heading. When the
  line is about the section from its first word (docs evidence), use readthrough instead: a reveal shows the end of
  the section before for its first 1-2 s, and near the top of a page it starts on the hero image (both happened).
- Check what the viewer sees, not what the manifest says: the manifest records the section the recorder aimed at.
  The video-review skill reads the heading off the frames, every half second, and reports a clip that shows
  another section.
- One scroll, one hover, one click. Eased, unhurried. The cursor parks on the subject.
- The review must say OK (duration, 1080p, not black, has motion). If it fails, look at the sheet before re-recording;
  a blank clip usually means the page needed a login or the section is below a lazy-loading boundary.
- Name clips by the spoken idea (`payload_index`, `no_single_config`), never by number.
- Keep every clip's manifest; an editor reusing the clip later needs the URL and the section it shows.

## Setup (first run on a new machine)

Nothing beyond Python and a Chromium browser is required: no After Effects, no editor, no accounts. Run
`python <skill>/scripts/setup.py` once; it installs the pip packages (playwright, imageio-ffmpeg, pillow, numpy,
opencv), finds Chrome or Edge (or downloads Playwright's Chromium), fetches Playwright's ffmpeg for video capture,
and prints READY / MISSING lines in plain words. `broll.py` also installs the packages by itself on first use, so
a person who skips setup still gets a clip. If something is missing, tell the person exactly which line to fix
(usually "install Google Chrome" or "install Python 3.9+"), then run setup again.
