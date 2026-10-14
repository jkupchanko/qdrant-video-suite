---
name: camera-layout
description: The camera piece of the video suite. Decides, passage by passage, where the presenter's camera goes in a technical video (full talking head, half split, large inset window, small corner window, or no face at all), how big it is, which corner, how long it holds, and when it changes. Based on a measured audit of 32 popular AI and software-development videos. Use it whenever someone asks about camera placement, PiP or picture-in-picture, "where should my face be", "how big should the webcam be", "when do I cut to the screen", camera layout, framing, or wants a camera plan for a script, including scripts from the script-writing skill that carry Camera directions. Also use it to audit an existing video's camera habits ("how does Fireship do it").
---

# Camera layout

A script says what is said and what is shown. This skill decides where the person is while that happens.
The answer is one of five layouts per passage, and the skill's value is in choosing between them the way
the videos people actually watch do, instead of leaving the same small window in the corner for ten
minutes.

## The five layouts

| layout | what it is | use it for |
|---|---|---|
| full | head and shoulders fill the frame | hooks, questions, opinions, reasons, summaries, calls to action |
| half | full-height panel beside the content (35-45% width) | comparisons, slides the person points at, conversation |
| inset | large corner window (25-32% width) | walking the viewer through something while talking a lot |
| small | small corner window (16-22% width) | presence while the viewer follows the cursor or reads lightly |
| none | screen only | anything that must be read: code, results, diagrams, articles, B-roll |

Proportions, framing (headroom, eye line) and corner choice are in `references/layouts.md`.

## How to make a plan

1. Read the script. If it is in the suite's format (sections with times, passages, `[**Camera:** ...]`
   and `[**Show:** ...]` directions, `[**B roll:** ...]` blocks), the directions tell you what is on screen;
   if it is plain prose, infer it from the words (code, results, diagrams mean something to read; "why",
   "because", "I think" mean the person).
2. Run the planner for a first pass. It applies the habits below and reports where it differs from any
   Camera notes already in the script:

   ```bash
   python <skill>/scripts/camera_plan.py SCRIPT.md --out camera_plan.md [--style cut|window] [--corner bottom-right]
   ```

3. Read the plan against the script and fix it by hand where the planner's keyword guess is wrong. The
   table is the deliverable: time, what is said, layout, size and position, hold, and the reason.
4. When the script already has Camera directions, the plan is a second opinion: keep the writer's choice
   unless it breaks one of the habits below, and say which one.

## The habits (what the corpus does)

These come from `references/tendencies.md`; the numbers there are the evidence.

- **Open on the person or on the result, then hold.** Half the videos open on the face, half on the screen.
  Either way the opening shot holds about 20 s before the first change. A hook that is a question or a
  claim goes on the face; a hook that is a result ("look what happens") goes on the screen.
- **Change at the material, not on a timer.** The median is 2.4 changes a minute in cut-style videos, under
  1 in window-style ones. Changes land on sentence boundaries that start with "now", "so", "let's", "next",
  and on the words "code", "terminal", "run", "click" (`references/cues.md`). Put the cut where the sentence
  turns.
- **Hide the face when the viewer must read.** The most common move in the corpus is full to none and back
  (45% of all changes). Code, results, a diagram, an article: no window over it. The viewer reads, then the
  face comes back.
- **Come back to the face.** Three videos in four return to full within 40 s of leaving it; stretches with no
  face at all run a median 10 s and rarely pass 50 s. If a code walkthrough is long, the face returns for
  the sentence that explains why, then leaves again.
- **Three layouts per video.** The median video uses three layouts for 5%+ of its time; two is the floor
  past three minutes. A small window that never changes is the pattern to avoid: when a long walkthrough
  needs presence, alternate small (reading) with inset (talking) with full (the point).
- **One corner per section.** Pick the corner that does not cover the terminal, the results or where the
  cursor works (bottom-right and top-left are the common ones), keep it through the section, and change
  size only at a section boundary or when the material changes.
- **Close on the person.** 14 of 32 close on the face, 10 on the screen. The summary and the call to action
  are full unless the last thing is a result worth looking at.

## Two styles

- **cut** (default): mostly full, cutting to screen and back, 3-4 changes a minute. Sajjaad Khader,
  ForrestKnight, NetworkChuck, Aaron Jack. Closer to the Qdrant house look.
- **window**: one window over the screen nearly all the time, under 1 change a minute. Tech With Tim,
  corbin, pixegami. Right for long courses where the screen is the whole point.

`--style window` keeps the inset through the body of the video and uses full only to open and close.

## Auditing a video instead

To measure how someone else does it (or check a finished edit):

```bash
python <skill>/scripts/audit.py VIDEO.mp4            # shares, changes per minute, corner, runs
python <skill>/scripts/audit.py VIDEO.mp4 --sheet check.png   # labelled contact sheet to verify by eye
python <skill>/scripts/audit.py --dir videos/ --out audit/    # a corpus; then tendencies.py rolls it up
```

Check the sheet before quoting numbers: tiny windows (under about 5% of the frame width) are undercounted,
and a presenter standing in a wide shot can be mistaken for a window when the body test fails.

## Hand-off

The plan's layout column maps onto the script's `**Camera:**` direction, so a writer can paste it back. The
B-roll skill handles anything marked none with a B-roll block; this skill only says that the face is off
during it.
