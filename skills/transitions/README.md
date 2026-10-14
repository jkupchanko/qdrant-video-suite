# transitions

**How the picture gets from one shot to the next, measured from 50 watched videos.**

The fourth piece of the video suite. The camera plan says where the person is; this says what happens at
the join. It audits any video (what kinds of changes, how often, at which joins), rolls a corpus up into
habits, renders the same join several ways on real footage so you can compare, and gives the rules for
writing a transition into the script's Transition field.

## What the audit found

Fifty popular AI and software-development videos, every frame-to-frame change classified.

- Most of what moves is not a shot change. 62% of visible changes are labels, captions or cards appearing
  over a shot that stays.
- Shot changes are cuts: 65% hard cuts. Slides and pushes 6%, dissolves 4%, fades 4%, animated card moves
  and wipes about 20%.
- Face to screen and back is a cut almost everywhere. Only 7 of 43 videos soften more than a quarter of
  those joins.
- Soft moves last about a quarter of a second. Fades to black sit at chapter boundaries.
- Pace: 2.6 shot changes a minute; 11.7 visible changes a minute once elements are counted.

## The rules in one breath

Cut by default. A short push (0.3 s, one direction all video) when a card arrives over the presenter. A
0.25 s dissolve only between two screens of the same kind. Fade to black only at a chapter break, once or
twice. Elements pop in with one entrance style for the whole video. Never two soft moves in a row.

## Use it

```bash
python scripts/audit_transitions.py VIDEO.mp4 --layout camera_audit.json --out t.json   # what a video does
python scripts/strips.py VIDEO.mp4 t.json --out strips.png                             # check the labels by eye
python scripts/render_transitions.py VIDEO.mp4 --a 20,24 --b 40,44 --out DIR            # same join, several ways
python scripts/tendencies.py --audit DIR_OF_JSONS --out habits.md                        # a corpus -> habits
```

## Worked example

`examples/bulk-uploads-*`: the Bulk Uploads video audited (its joins are 56% slides where the corpus is 65%
cuts), its check strips, and three test joins from its own footage rendered as cut, push and dissolve.

## Files

```
transitions/
  SKILL.md, README.md
  scripts/audit_transitions.py   video -> every change, classified, with context
  scripts/strips.py              frames around each change, to verify
  scripts/tendencies.py          many audits -> habits
  scripts/render_transitions.py  same join rendered several ways + labelled reel
  references/tendencies.md       the 50-video report
  references/classifier-check.png  what each label looks like in three corpus videos
  references/audit_summary.csv   one row per video
  examples/                      Bulk Uploads audit, strips, three comparison reels
```

Needs Python with opencv-python, numpy and imageio-ffmpeg.
