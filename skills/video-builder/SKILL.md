---
name: video-builder
description: Build a whole video from a request, using every skill of the video suite in order and ending with the review. Give it a raw talking-head take and a three-layer script (lines, B-roll markers, camera calls, transition values); it cuts the take (editing), finds the look-aways (gaze), plans the camera (camera-layout), checks the B-roll by key term and records every marker (broll-recorder), captures the docs page's figures and code (broll-recorder), renders a styled video (editing-style; the listed-sections style builds itself from the script and the page), masters the loudness, and audits the result frame by frame (video-review), then reports what the review found. Use it whenever someone asks to "build this video", "make the video", "do the whole thing", "run it end to end", "use all the skills", "go from the recording to the finished video", or asks a question that ends in a finished video, even if they name only the topic.
---

# Video builder

One request in, a finished and reviewed video out. Each step is a skill that already exists; this skill runs them in the
right order, hands each one the files the previous ones made, and ends with the review, so nothing reaches a person
unchecked.

## Ask first

Before running anything, ask the person what only they can answer, in one message, and wait (the brand-consistency
skill's `references/intake.md` says why each one matters):

1. Your **name**, as it should read on the name card (lower third)?
2. Your **title** under it?
3. Where is the **raw take**?
4. Is there a **script** (three-layer form), or should one be written and shown first?
5. Which **docs page** is it about?
6. Which **style** (listed sections by default)?

Skip a question the conversation, the script or memory already answers, and say what you are using instead ("name
card: John Kupchanko, Developer Relations Engineer, from the script"). The build itself refuses to start without a name
card: with no `[**Lower third:** ...]` in the script and no `--name`/`--role`, it prints these questions and exits 2.

**The script controls the video.** Every direction lives in it: the lines, the B-roll markers, the camera calls and their
transitions, the name card. To change the video, change the script and re-run from the stage it affects. The skills can
still be run one by one for a quick fix, but the build is the script's.

## What it needs

- **The raw take**: the presenter's recording (Zoom, webcam). Retakes and stumbles are fine: the editing skill keeps the
  last complete take of each line. Nothing here can replace the recording; if there is none, stop and say so.
- **The script**, in the three-layer form (see the script-three-layers memory): `## Section   m:ss to m:ss` headings, the
  spoken lines, `[B-ROLL: url | line | section: X | 6s | name: n]` markers, `[**Camera:** FULL / SMALL / NONE ...]` calls
  with their **Transition:** values, and the name card `[**Lower third:** NAME | TITLE | 5 s]` after the line it comes in
  on. A `<!-- Source page: URL -->` note names the docs page. If the person has only a topic, write the script first and
  show it (script + camera calls + transitions, inline) before building.
- Optionally `--url` (else the script's Source page or first marker), `--style` (default `list`), and `--name`/`--role`
  when the script has no name card (added to a copy, `BUILD_DIR/script.md`; the given script is never edited).

## Run it

```bash
python ~/.claude/skills/video-builder/scripts/build.py --take RAW.mp4 --script SCRIPT.md --out BUILD_DIR --label "Topic, style"
```

It takes about an hour and a half for a 3.5 minute video (the render and the review are most of it); run it in the
background and report progress from `BUILD_DIR/build.json`. Each stage keeps its outputs, so a second run skips what is
done: `--from style` starts at a stage, `--only review` runs one, `--redo broll,style` forces some again.

| stage | skill | makes |
|---|---|---|
| cut | editing | `cut/cut.mp4`, `cut/cutlist.md` (which take each line came from), `cut/words.json`; every cut point placed by the sound, never mid-word |
| words | (glue) | `words.json`: the cut's words at cut time, one piece per line |
| gaze | editing (gaze.py) | `gaze.json`, `lookaways.json`: where the face must be off screen |
| camera | camera-layout | `camera_plan.md`: the planner's plan, as a check on the script's own calls |
| keyterms | broll-recorder | `keyterms.md`: which lines the key-term rule gives B-roll, against the script's markers |
| broll | broll-recorder | `broll/`: every marker recorded (readthrough, 1.4x page zoom, section pinned) |
| assets | broll-recorder | `page_assets/`: the page's figures and code (2x, sharp) and its Best fit / Watch for lines |
| style | editing-style + brand-consistency | `video.mp4` (style `list`: master list, numbered items, docs figures, live-typed code, tradeoff cards) with the Qdrant name lower third; `video_overlays.json` says when it is up |
| master | editing-style | `video_master.mp4` at about -14 LUFS |
| review | video-review | `review/report.md`, `review/sheet.jpg`, `review/frames/`; also hears every join in the raw take (`--take`) and reads the name card |

`BUILD.md` sums it up: each stage, its skill, what it did, how long it took, and the review's counts.

## After the build: the review decides what happens next

1. Read `review/report.md` and look at `review/sheet.jpg` and every fix frame yourself.
2. For each **fix**, find the stage that caused it (the report's fix line names the skill), fix it there, and re-run from
   that stage (`--from STAGE --redo STAGE`): a retake left in the cut or a word clipped at a join is the cut stage; a late
   or wrong-section B-roll is the broll stage; an empty or stretched frame, or a missing name card, is the style stage
   (and the script, if the directive is missing).
   When the person reports something the review did not find ("you still cut off my audio"), find it, fix it, and add a
   check that finds it next time before re-running: that is how the review grew its join check.
3. Report to the person: the video's path, what the review found (from `report.json`, not memory), what was fixed, what
   is left to check (with frames), and how long each stage took.

## Styles

- `list` (default, automatic): the listed-sections style (`camera_audit/styles/style_list.py`). The list is the script's
  B-roll sections whose docs section has a "Best fit" line; the groups are the page's tags; every word on a chip is the
  page's own. Copied from ByteByteGo (master list, current item lit), Fireship (numbered card, TRADEOFF chips) and
  NeetCode (group cards); the peer frames are in `camera_audit/peers/peer_list_layouts.jpg`.
- `report` (Code Report) and `full` (Animated Board) are hand-authored per video (an edit list, Manim boards); they run
  through the same stages once their plan exists for the new cut.

## Known limits

- The engine, the styles and this skill live on this machine (`camera_audit/styles`); they are not in the GitHub suite.
- The take must contain the script's lines. Lines never said are listed in the cut list as NO TAKE FOUND.
- The camera stage's plan is advisory: the style follows eye contact first, then its own layouts; the review reports
  where the result departs from the script's calls.
