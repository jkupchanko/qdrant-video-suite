---
name: video-review
description: Audit a rendered video for the small details before anyone sees it, and report every problem with its timestamp, frame number and a marked frame. Checks the presenter (face on screen while the eyes are off the lens, stretched face, head cut off by its window, lip sync, voice drift), the sound at every join of the cut (a word clipped, a piece starting or ending mid-word, words heard twice), the brand (the presenter's name lower third present, spelled as the script gives it, held, first; accents in the Qdrant palette), the pace (a hard cut into or out of a card, a card gone before its words can be read, a first B-roll that never shows which page it is), the text on screen (words cut at the frame edge, text spilling out of its card, text too small for a phone, typos, numbers the script and docs never gave, stale API spellings, code shown without the top-right presenter window), the B-roll (missing, late against its line, the wrong docs section, ghost frames), the script (camera calls not followed, lines missing from the cut, a Count section that disagrees with itself), and the picture and sound (black or frozen frames, static stretches, dead space, loudness, clipping). Use it after every render made with the editing, editing-style, broll-recorder, camera-layout or transitions skills, and whenever the user asks to review, audit, QA, proof or check a video, to "look at the small details", "pay attention", "make sure it looks good", or asks whether a video is ready to ship, even if they do not say "review".
---

# Video review

A finished render can look right at a glance and still be wrong in a dozen small places: a face on screen
during a glance away, a B-roll that opens on the section before the one being talked about, a word cut by the
frame edge, a made-up "6.8 GB" on a card. Each of these was a real bug in this suite. This skill finds them
from the pixels and the sound of the output, not from the plan that made it: the plan can be right and the
render still wrong.

## Run it

```bash
python ~/.claude/skills/video-review/scripts/review.py OUTPUT.mp4 --out REVIEW_DIR \
  --cut CUT.mp4 --script SCRIPT.md --words WORDS.json \
  --gaze GAZE.json --lookaways LOOKAWAYS.json --broll BROLL_DIR --label "Code Report + B-roll"
```

Only the video is required. Give it everything the project has: each input switches on the checks that need it.

| input | what it is (Bulk Uploads paths) | checks it switches on |
|---|---|---|
| `--cut` | the presenter cut the style was built on (`edit/full_edit/bulk_uploads_full_edit_v2.mp4`) | whose face is on screen; stretched face; head cut off; lip sync; voice drift |
| `--lookaways`, `--gaze` | `edit/full_edit/lookaways_v2.json`, `gaze/v2/gaze_v2_locked.json` | face on screen while the eyes are off the lens |
| `--script` | the three-layer script (`full_suite/bulk_uploads_script_final.md`) | camera calls, script lines in the cut, the Count section, B-roll markers |
| `--words` | the cut's transcript with word times (`styles/out/v2_words.json`) | where each script line and B-roll line is in the cut |
| `--broll` | the broll-recorder output folder (`full_suite/broll2`) | B-roll found, timed, on its section, no ghosts; the docs page's words for spelling and numbers |
| `--cutlist` | the editing skill's `cutlist.md` | a line it found no take of is a **fix** (missing); one it found "said in other words" is a note |
| `--assets` | `page_assets.py`'s `assets.json` | the page's code and figure captions count as its own words and numbers (`size=768` is the docs') |
| `--take` | the raw recording the cut was made from (with `--cutlist`) | every join heard in the take: the next word's first sound kept at an out-point, a piece ending or starting mid-word, two pieces overlapping (heard twice) |

Always, from the pixels (`scripts/pace_checks.py`), the pace John and his boss noticed and the review did not:
- **`abrupt`** (fix): a hard cut into, out of or between cards. The house wants soft changes of about 0.8 s ("how quick we
  are transitioning"); a jump cut between two face takes and a white flash the script asks for are fine.
- **`read`** (fix under 60% of the time needed, check under 80%): the video is split at every change of picture, and each
  card's words (OCR; big titles and short labels are glanced, not read) are timed at 3.8 words a second plus 0.4 s a
  line of code. A card that comes back (the list) is not counted again. Build 4's 4 s tradeoff cards were the case.
- **`broll_context`** (fix, with `--broll`): the first B-roll of each page must show the page's title in its first 3.5 s
  ("we show this section of something... we don't actually show what it is").
- **`brand_colour`** (check): every 2 s on the graphics (not the face window, not a recorded page), accents more than a
  little off every colour of the Qdrant palette (brand-consistency's `brand.py`).

With `--script`, the name lower third is checked too: the script's `[**Lower third:** NAME | TITLE | 5 s]` must be read on
screen (OCR) with that spelling and the title, held about its time, in the lower left, over the presenter; a script
without one is a **fix** (brand-consistency skill).

The join check exists because a person heard what the review did not: "you still cut off my audio on one of the parts".
The first Listed Sections build kept the first 40 ms of "when" after "...dense and sparse vectors" (0:21.9), and two
pieces overlapped so a word was heard twice. The check found 16 fixes on that cut, none on the cut after the editing
skill placed its cut points by the sound. When a person reports something the review missed, add the check before the fix.

It takes about 4 to 8 minutes for a 3.5 minute video. OCR results are cached in `REVIEW_DIR/ocr_cache.json`,
so a re-run after a fix to the face or the B-roll is faster. `--skip ocr,face,audio,broll` leaves passes out
while you iterate on one thing.

## What it writes

- `report.md`: the counts, a table of every pass's result, then each finding by time under **To fix**,
  **To check** and **Notes**, each with its frame and the fix (which skill, which file).
- `frames/*.jpg`: the frame of each finding with the region marked in red.
- `sheet.jpg`: all the fix and check frames on one sheet.
- `report.json`: the same, for scripts. `faces.json`: every face sample (window, aspect, sync), for a closer look.

## Prove it still works: the self-test

```bash
python ~/.claude/skills/video-review/scripts/selftest.py CUT.mp4 --gaze GAZE.json --lookaways LOOKAWAYS.json --out REVIEW_DIR/selftest
```

Plants four faults in the cut's first 10 s (empty frames, a 10% stretch, the picture 3 frames behind the voice, a caption off
the edge), reviews the clip, and fails if one is missed or a fix is reported that was not planted. Run it after changing any
check: a check that stops firing looks exactly like a clean video.

Severity:
- **fix**: wrong, whatever the style. A word clipped at a join, a missing or misspelled name card, face during a look-away, stretched face, desync, wrong B-roll section, ghost frames, text cut at the edge, black frames, clipping.
- **check**: probably wrong; a person decides. An unsourced number (a joke figure on a meme may be fine; a figure on a docs card is not), a possible typo, small text, a long static hold, dead space, a camera call the edit departs from.
- **note**: worth knowing, not wrong. Another heading visible in a B-roll frame, scroll cadence.

## How to work with the findings

1. **Look at every fix frame yourself before acting on it.** The checks are measurements, and measurements
   have failure modes (below). Open `sheet.jpg`, then the frames. A finding you have not looked at is not a
   finding you can report.
2. **Fix at the source, not in the render.** Each finding's fix line names the skill and file: a late B-roll
   is fixed in the B-roll timing (`broll_layer.py`), a wrong section in the recording (`broll.py --section`,
   `--style readthrough`), a stretched face in the face crop (`engine.face_crop`). Then re-render and re-run
   the review until nothing is left to fix.
3. **Report with the numbers from `report.json`**, not from memory: how many fixes were found, what was
   fixed, what is left to check, with times. When telling the user about a check item, show the frame.
4. **Unsourced numbers** are listed for a person to decide: an invented figure presented as fact must go,
   while an obvious joke label can stay. Say which is which when reporting.

## Known limits (so a finding is read correctly)

- **OCR glues words** ("AMOUNTSOFDATA"). The spelling check splits glued words before it calls anything a
  typo; a real term it does not know goes in `references/rules.json` → `lexicon`.
- **Edges are not checked during transitions** (pushes move text across the edge on purpose). Only the left
  and right edges count: a scrolling page cuts lines at the top and bottom by design.
- **Lip sync** is read three times a second: each of the 9 cut frames around the output's frame is aligned to the
  face on its own (ECC), and the one on screen leaves almost nothing unexplained. A still face leaves every frame
  equal, and a caption over the face raises every error alike: neither gets a verdict. The finding needs 3 agreeing
  reads in 6 s. (Aligning only the same-numbered frame would always pick it: that bug made the first version blind.)
- **Stretch** is judged per window, as the median over 5+ samples: a crop's shape is fixed for a whole layout, while
  landmarks on a small face jitter a few percent from frame to frame.
- **Text spilling out of its box** is seen as a straight line (a card or panel border) running through a word and on
  past it, on a flat background. A word cramped against a shape without touching it is not reported.
- **Other people's faces** (memes, photos) are told apart from the presenter by matching the cut's face at the
  same frame. A frame where the presenter is heavily tinted or blurred may not match, and is then not checked.
- **The head-cut check** is judged per layout: the window's rectangle is the median over the stretch between two
  transitions, and the head is measured against it (one sample's window can stop short). It assumes hair adds about 45%
  of the face height above the brow. A tight full-frame
  shot of the cut itself is not counted: only what the camera framed (inside the cut's bars).
- **B-roll section**: headings are read only in the page's own column (the sidebars list every heading), and
  must be set larger than the body text. While no heading is in frame, the section is the last one that
  crossed the middle.
- **Dead space** means a layout that leaves a whole side of the frame empty (John: "the whole left side is completely
  empty"), or an empty frame. Words or a card centred on plain background (a Fireship-style word stack or title card)
  are a look, not dead space, and are not reported. Short empty flashes are the separate `blank` check, every frame.
- **The face window** is found by mapping the cut onto the output (landmarks, then ECC over the face for a sub-pixel fit)
  and walking out from the face while the output still is the cut, judged by the size of the difference (a hairline
  misfit by 2 px differs a little; the board past the window's edge differs a lot). The cut's black bars never count.
  A full-width match that stops short is a caption over the face (`covered`), not a window edge.
- **Two labels colliding** are not seen when OCR reads them as one word that splits into real words ("its own write
  path" over "shards" read as "pathhards"). Look at the board frames on the sheet yourself; this one was found by eye.
- **The eye-contact rule is the engine's**: the face is held off over each look-away widened by its leaving transition, and
  between two look-aways closer than 2.5 s. A missing face window there (code without the top-right window, a FULL call
  with no face) is the rule working, so those checks skip it.
- **Camera calls are placed by their lines**, not by the script's m:ss times: those belong to the cut the script was timed
  on, and a new cut moves them. A timed call belongs to the line just before it; an untimed one to its block.
- **Static holds** are reported from 6 s: John's word on pacing is that holds are fine (2026-10-15), so 4-5 s of a card
  being read is not a fault.
- **Camera calls are read loosely**: FULL means the face fills most of the frame, SMALL a window under 20% of
  the frame in the top right, NONE no presenter. Styles that direct the face themselves (Animated Board's
  half and card layouts) will differ from FULL calls; read those as a style choice unless the call is NONE.

## Thresholds

`references/rules.json`: line height for phone-readable text (24 px at 1080), face aspect tolerance (4%),
head cut (5%), lip sync (1 frame), voice lag (45 ms), B-roll lateness (0.4 s), static hold (6 s), dead space (a whole
side empty edge to edge, 35% of the width or 40% of the height, for 2 s; or 92% of the frame), loudness (-17 to -11 LUFS),
peak (-1 dBFS). Stale API spellings and the project's
vocabulary are there too. Change them there, not in the code.

## Related skills

editing (the cut and its sync), editing-style (the styles, the engine, eye contact), broll-recorder (the B-roll
clips), camera-layout (the camera calls), transitions.
