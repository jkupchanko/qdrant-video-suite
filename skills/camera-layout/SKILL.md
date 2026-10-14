---
name: camera-layout
description: The camera piece of the video suite. Use when a video needs presenter framing, camera placement, inset or PiP sizing, split screen choices, "where should my face be", "when do I cut to the screen", or a camera plan tied to a script (including scripts from the script-writing skill that carry Camera directions), and when someone wants to audit how an existing video or creator places the camera. Decides, passage by passage, whether the presenter is full screen, in a side panel, in a large or small inset, or hidden, how big, which corner, how long it holds and when it changes, using a decision guide plus a measured audit of 32 popular AI and software-development videos.
---

# Camera Layout

Let the job of the spoken passage determine what gets screen space.
Presenter visibility is a choice, not a requirement or a fixed appearance quota.

## Start from the brief

Use a supplied script, spoken explanation or standalone scene brief.
Reuse the known audience, duration, aspect ratio, footage and preferred style.
Ask only for missing information that would change the layout.
If details are unavailable, state a working assumption and produce a reviewable plan.

In the full suite, the script leads the camera plan.
Preserve its spoken words, section times, Show directions and selected B roll requests.
Attach camera decisions to the relevant passage rather than rewriting its story.
For a standalone request, plan only the requested scene or sequence.

## Choose the layout

| The passage asks the viewer to | Starting choice |
| :--- | :--- |
| Attend to the presenter's opening, explanation or close | Presenter full screen, if that presence helps |
| Read code, a passage, a table or ranked results | Content full screen |
| Follow a guide through an uncrowded demonstration | Content with a small rectangular inset |
| Follow a simple view while the presenter remains important | A content dominant side panel arrangement |
| Attend equally to the presenter and a simple visual | Equal presenter and content split |
| Compare two alternatives | Two content views, usually without the presenter |

Treat a shared lightboard scene as different from a literal split.
Narration such as "look here" suggests a visual target; inspect that target before selecting the layout.
Read [the decision guide](references/decision-guide.md) for sizing, protected content and exceptions, and
[layouts.md](references/layouts.md) for the five measured layout classes with their proportions.

## Check the plan against what watched videos do

The habits below are measured from 32 popular AI and software-development videos sampled every two seconds
with the words spoken at each change ([tendencies.md](references/tendencies.md), [cues.md](references/cues.md)).
They are observations of a sample, not retention rules; use them as checks on a plan, and say which one a
departure breaks.

- The opening shot holds about 20 s before the first change, whether it starts on the person or the screen.
- Changes land where the sentence turns ("now", "so", "let's") and where the words name the screen
  ("code", "terminal", "run", "click"), at a median of 2.4 changes a minute in cut-style videos and under 1 in
  window-style ones.
- The most common move is face to screen and back; nearly half of all changes are that pair.
- The face comes back: three videos in four return to full within 40 s of leaving it, and stretches with no
  face at all run about 10 s and rarely pass 50 s.
- Three layouts per video is the median; two is the floor past three minutes. A window that never changes
  is the pattern to avoid.
- One corner per section; size changes at section boundaries or when the material changes.
- Most videos close on the person unless the last thing is a result worth looking at.

For a first pass that applies these checks and reports where it differs from the script's own Camera
notes:

```bash
python <skill>/scripts/camera_plan.py SCRIPT.md --out camera_plan.md [--style cut|window] [--corner top-right]
```

Read its table against the script and keep the writer's choice wherever it does not break a check.

## Frame the face the same way everywhere

Inside any layout the face is framed by one rule: measure the face (brow to chin = h), keep 0.25 h of
headroom above the head, run the crop down to the chin plus 0.9 h so the shoulders are in, keep at least
0.6 h clear on each side so a turn stays in frame, and centre the face horizontally with the eyes near the
upper third. On a recording, frame around where the face goes through the clip, not one frame.

```bash
python <skill>/scripts/frame_face.py TAKE.mp4 --out crops/ [--mirror]   # crops per layout + a guide image
```

If it reports the source is too tight, the fix is at the camera (step back or widen), not in the crop.
To put that crop into a window over a screen clip (rounded rectangle, thin border, corner and size by the
layout): `python <skill>/scripts/window_overlay.py SCREEN.mp4 FACE.mp4 --crop x,y,w,h --width 0.20 --corner top-right --out OUT.mp4`.
Details in `references/layouts.md`.

## Keep the layout consistent

Use rectangular presenter placeholders when examples are requested.
Keep one inset position, size and crop through a continuous sequence.
For this suite's horizontal example, a top right inset at 20% of frame width is a starting preset, not a researched universal rule.
Hide it if it obstructs important content; a chapter boundary can justify an intentional layout change.
Distinguish physical camera angle, shot crop and screen position.
Do not invent footage or imply that a placeholder is a recorded presenter.

Specify width relative to the frame and preserve the chosen aspect ratio.
For machine handoffs, use [the output format](references/output-format.md), which also defines coordinates and transition intent.

## How the script carries the calls

A camera call is a `[**Camera:** LAYOUT, position, size.]` line under the passage where the camera changes;
between calls it holds. A call is required at the opening, wherever something must be read (code: SMALL top right by house rule; results, diagrams and inserts: NONE),
wherever the person carries the line or the face has been away about 40 s (FULL), at a section boundary
where the material changes, and at the close. Nothing else earns one. The vocabulary and the full rules are
in [camera-markers.md](references/camera-markers.md); `camera_plan.py --annotate` writes calls in exactly
this form, only at changes, so a writer can leave Camera out and get it filled.

## Return and check

Return passage specific Camera directions beneath the spoken text, with the existing Show and Transition fields.
Keep B roll blocks only where the script already requests useful supporting material.
Count planned full screen appearances from the resulting sequence.
Check content legibility, protected regions, consistent placement and any timing assumptions.
Use the [placeholder examples](assets/layout-examples.svg), the [worked camera plan](examples/miniCOIL-camera-plan.md)
and the [planner's generated plan](examples/miniCOIL-camera-plan-generated.md) for the same script when a visible example helps.
The [frame review](references/frame-review.md) records observations from ninety saved stills and their limits;
the [measured audit](references/tendencies.md) adds continuous sampling of 32 videos. Neither proves a retention effect.

## Audit a video instead

To measure how someone else does it, or check a finished edit:

```bash
python <skill>/scripts/audit.py VIDEO.mp4                     # shares, changes per minute, corner, runs
python <skill>/scripts/audit.py VIDEO.mp4 --sheet check.png   # labelled contact sheet to verify by eye
python <skill>/scripts/audit.py --dir videos/ --out audit/     # a corpus; tendencies.py rolls it up, cues.py adds speech
```

Check the sheet before quoting numbers: windows under about 5% of the frame width are undercounted, and a
presenter in a wide shot can be mistaken for a window when the body test fails.
