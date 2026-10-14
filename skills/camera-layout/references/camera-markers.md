# Camera calls in a script

The script is the one document everyone works from, so the camera lives in it, not in a side file. A camera
call is a direction line under the passage where the camera changes. Between calls the camera stays where it
is. This is the same `[**Camera:** ...]` field the script library already uses; this page fixes what goes in it
and when it has to be there.

## The line

```
[**Camera:** SMALL, top right, 20% width. **Show:** the three passages, intended answer marked. **Transition:** keep the query visible.]
```

The Camera field is: a layout word, then position and size when the layout is a window or a panel, then
anything the editor needs (same crop as before, hide during the insert). Keep it under one line.

| word | means | add |
|---|---|---|
| FULL | head and shoulders fill the frame | nothing, or "centred" / "a touch left" if a title shares the frame |
| HALF | full-height panel beside the content | side and width: "right, 40%" |
| INSET | large window over the content | corner and width: "bottom right, 28%" |
| SMALL | small window over the content | corner and width: "top right, 20%" |
| NONE | no presenter | optionally why: "code must be read" |

Framing inside any of them is the rule in `layouts.md` (headroom, chin to shoulders, side clearance, face
dead centre), so the call never describes the crop; it names the layout.

## Where a call is required

Write a call under a passage when any of these is true. If none is, write nothing: the camera holds.

1. **The opening.** The first passage always carries one, so the editor knows whether the video opens on the
   person or the screen. The opening holds about 20 s; don't call a change inside it unless the hook needs
   the screen.
2. **Something must be read.** Code, results, a table, a diagram, an article insert.
   - Code: SMALL, top right, 20% width. House rule: the person stays on while the viewer reads the code,
     because code is explained as much as read. The window lives in the top right, where a code card has
     nothing. Drop to NONE only when the code or its output runs under that corner.
   - Results, tables, diagrams, article inserts: NONE. These are looked at, and a window would cover part of
     them. Every B-roll block implies NONE for its duration; write a call only if the camera should be
     somewhere other than hidden when the insert ends.
3. **The person carries the line.** A reason, an opinion, a question, the summary of a section, the call to
   action. The call is FULL. Also write FULL when the face has been away for about 40 s, even mid-section:
   that is when watched videos bring it back.
4. **A section boundary where the material changes.** Code section to results section, explanation to
   demonstration. One call at the top of the new section; the window corner and size may change here and
   nowhere else.
5. **The close.** The last passage carries one. FULL unless the last thing is a result worth looking at.

Not a reason for a call: a new paragraph, a pause, a feeling that it has been a while. Changes land on
sentence turns ("now", "so", "let's", "here's") and on screen words ("code", "terminal", "run", "click");
put the call under the passage that starts with one.

## The window never covers the point of focus

Before a SMALL or INSET call stands, look at what is under that corner on the card or page the viewer sees.
If text, code, a diagram or a control sits there, the window does not go there. The order to try is top
right, top left, bottom right, bottom left; the first clear corner wins. If no corner is clear (a ranked
list that runs the full width, a page with navigation on both sides), the call is NONE, not a window on
top of the material. Once a corner is chosen it stays for the section: the window is removed and restored
in the same place, and only a section boundary may move it. `scripts/window_overlay.py --auto-corner`
measures what is under each corner and moves or refuses the window; the example sheet
`examples/corner-safety.png` shows it on four screens.

## What a good script looks like

Two or three layouts over a 5 minute video, 10 to 15 calls, one corner for the window in each section, no
stretch over about 50 s without a face in some size, no window that never changes. A script whose calls are
all SMALL is the pattern to avoid; one whose calls alternate FULL and NONE every 4 s is the other.

## For the writer who does not want to decide

Write the Show and B roll fields and leave Camera out. Run:

```bash
python skills/camera-layout/scripts/camera_plan.py SCRIPT.md --annotate SCRIPT.camera.md
```

It writes a `[**Camera:** ...]` call under each passage where the camera changes, in this form, using the
rules above, and lists where it differs from any calls already in the script. Keep yours where they do not
break a rule; the plan says which rule a departure breaks.
