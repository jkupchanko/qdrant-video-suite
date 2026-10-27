---
name: video-builder
description: Build a whole video from a request, using every skill of the video suite in order and ending with the review. Give it a raw talking-head take and a three-layer script (lines, B-roll markers, camera calls, transition values); it cuts the take into one clean pass (raw-edit), finds the look-aways (gaze), plans the camera (camera-layout), checks the B-roll by key term and records every marker (broll-recorder), captures the docs page's figures and code (broll-recorder), evens and cleans the voice (audio-captions), renders a styled video (editing-style; the listed-sections style builds itself from the script and the page), masters the loudness, writes captions spelled like the script (audio-captions), and audits the result frame by frame (video-review), then reports what the review found. Use it whenever someone asks to "build this video", "make the video", "do the whole thing", "run it end to end", "use all the skills", "go from the recording to the finished video", or asks a question that ends in a finished video, even if they name only the topic.
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
background and report progress from `BUILD_DIR/build.json`. Offer a preview first: `--preview 30` builds only the
sections that start in the first 30 s (their lines, B-roll, name card and review), in minutes, into its own folder, so
the person can judge the direction before the long build. Before either, `--only cut` makes just the raw edit for
the person to approve.

The style sheet: `style_<style>.json` beside the style's script in the engine folder (`engine/style_list.json` for
Listed Sections). The build reads it for the cut's zoom, the B-roll recording (click-through first, lead-in, length, page
zoom) and passes it to the style for transitions, reading pace and the presenter's window. Change the sheet, not the code.

Small edits after the build: `--patch T0 T1` re-renders only those seconds (grown to whole shots, with a second of
lead-in so the transition into the first shot is drawn from the real previous frame) using the script as it is now,
splices them into `video.mp4` frame for frame, masters again, and writes `patch_T0-T1.mp4` (the moment, a second either
side) to show. About 40 s for a few seconds of video; the spliced video matched the original to within encoding noise.
It marks the review out of date: run `--only review --redo review` once at the end. Edits to the cut, the B-roll
recordings or the spoken lines change everything after them; re-run those from their stage instead. Each stage keeps its outputs, so a second run skips what is
done: `--from style` starts at a stage, `--only review` runs one, `--redo broll,style` forces some again.

| stage | skill | makes |
|---|---|---|
| cut | raw-edit (+ editing) | `cut/cut.mp4`, `cut/cutlist.md`, `cut/words.json`: each thought said once, no stop mid-sentence, no glance at a cut, nothing dropped, every limit measured on the presenter; what it found fixed by itself; `cut/raw_edit_check.md` and `cut/review.html` to review on. `--cutter takes` for the old per-take cutter |
| words | (glue) | `words.json`: the cut's words at cut time, one piece per line |
| gaze | editing (gaze.py) | `gaze.json`, `lookaways.json`: where the face must be off screen |
| camera | camera-layout | `camera_plan.md`: the planner's plan, as a check on the script's own calls |
| keyterms | broll-recorder | `keyterms.md`: which lines the key-term rule gives B-roll, against the script's markers |
| broll | broll-recorder | `broll/`: every marker recorded (readthrough, 1.4x page zoom, section pinned) |
| assets | broll-recorder | `page_assets/`: the page's figures and code (2x, sharp) and its Best fit / Watch for lines |
| voice | audio-captions | `cut/cut_voice.mp4`, `cut/voice.json`: every piece of the cut at one level; room noise, hum and rumble taken out only when measured over a limit; the voice never moved off the lips. The style stage uses it |
| style | editing-style + brand-consistency | `video.mp4` (style `list`: master list, numbered items, docs figures, live-typed code, tradeoff cards) with the Qdrant name lower third; `video_overlays.json` says when it is up |
| master | editing-style | `video_master.mp4` at about -14 LUFS |
| review | video-review | `review/report.md`, `review/sheet.jpg`, `review/frames/`; also hears every join in the raw take (`--take`) and reads the name card |
| captions | audio-captions | the last step, only when asked (`--captions file` or `burned`; start-here asks once the video is approved): `captions/captions.srt` and `.vtt` to upload, heard from the finished video, spelled the way the script spells things; with `burned` also `captions/captioned.mp4` |

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

## Prove the whole chain still works

```bash
python ~/.claude/skills/video-builder/scripts/chain_test.py
```

Builds the repo's 30-second demo (`demos/bulk-uploads-first30`) through every stage, captions included, and checks what
each stage made: every script line found, the cleaned voice the cut's length to the millisecond, the B-roll clip
recorded, the master the cut's length at about -14 LUFS, the review written, the captions spelled right with nothing to
fix. Several minutes; needs the network and Chrome. Run it after changing any skill and before every push: each skill's
self-test proves that skill, and only this proves they still work one after another. A number that moved since the last
pass (a length, the loudness, the review's counts) is printed even when it passes.

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
