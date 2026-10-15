---
name: transitions
description: The transitions piece of the video suite. Use when someone asks how to get from one shot to the next in a technical video (cut, dissolve, fade, slide or push, punch-in, card animation), "what transition should I use here", "is this too many effects", wants a transition plan for a script that already has camera calls, wants to audit the transitions in an existing video or a creator's style, or wants the same join rendered several ways to compare. Based on a measured audit of 50 popular AI and software-development videos covering what kind of change they use at each kind of join, how often, and how long the soft ones last. Also use this whenever a video script is being written or requested in this suite, even if nobody mentions transitions, because every Camera call needs a Transition value (cut, push on a card arrival, white flash at a chapter) before the script is finished; run it after the camera calls are in.
---

# Transitions

The camera plan says where the person is for each passage. This skill says how the picture gets from one
state to the next: at a camera change, at a change of card or page, and when a label or card appears over a
shot that stays. The answer is nearly always a cut, and the skill's value is mostly in saying when it is not,
and in keeping the few soft moves short and consistent.

The vocabulary, the joins where each move goes, and the measured shares are drawn in `assets/vocabulary-board.png`,
`assets/where-in-the-script.png` and `assets/numbers-board.png`.

## What the audit found (50 videos)

- **Most visible changes are not shot changes.** 62% of everything that moves on screen is an element
  appearing over a shot that stays: a label, a caption, a card, a highlight. The shot underneath does not
  change. Those are graphics work, not transitions.
- **Shot changes are cuts.** Among real shot changes, 65% are hard cuts. Dissolves 4%, fades 4%, slides and
  pushes 6%, and 20% are animated moves of some kind (a card flying in with blur, a graphic wipe).
- **Face to screen and back is a cut.** At joins between the presenter and the screen, cuts are 45 to 52%
  of changes, slides 3 to 5%, dissolves 1 to 3%. Only 7 of 43 videos make more than a quarter of those joins
  soft.
- **Soft moves are short.** Where a dissolve, fade or slide is used, the median length is 0.27 s. Nothing
  lingers.
- **Fades mark chapters.** Fade to black or white is 4% of shot changes and sits at section boundaries, not
  inside a demonstration.
- **Pace.** Median 2.6 shot changes a minute; with elements counted, 11.7 visible changes a minute.

Numbers per video and by join type: `references/tendencies.md`. The eight most-watched videos in the
Qdrant format, with how each joins face and screen, and a reel of their real joins (original footage, not
re-creations): `references/models.md` and `examples/reference-joins.mp4`. Strips of each kind from three corpus
videos, for what the labels mean: `references/classifier-check.png`.

## The rules that follow

Only what the model videos do. Nothing is added to the vocabulary that was not seen there.

1. **Default is a cut.** Every camera call in the script (FULL, SMALL, NONE and back) is a cut. In the eight
   model videos, 138 of 185 joins between the face and a screen are cuts, and all eight use it. A cut lands
   on the sentence turn the camera call already sits on.
2. **A short push when a card arrives over the presenter.** Seen in Futurepedia, Aishwarya and NetworkChuck
   (7 of 185 joins): 0.25 to 0.3 s, one direction for the whole video, for a card coming in. Cards leave on a
   cut.
3. **A white flash at a chapter boundary.** Seen in Jeff Su (3) and Futurepedia (2): 0.3 to 0.5 s, at the
   start of a new chapter, at most a few times in a video. Not inside a demonstration.
4. **Animated card entrances are element work, not transitions.** The "other" joins in the models (31 of
   185) are cards and graphics flying in with motion blur over a shot that stays. One entrance style per
   video, built in the graphics, not at the cut.
5. **Not seen, so not used:** dissolves between the face and a screen (4 of 185 model joins, 2 of them in a
   voice-over video), fades to black at a join (none in the model joins), punch-in jump cuts (8 in all 50
   videos), zooms, wipes. If one of these seems wanted, the answer is a cut.
6. **One vocabulary per video; never two soft moves in a row.** The models use two or three kinds in a
   whole video.

## Writing it into the script

The script's `**Transition:**` field already exists. Fill it with one of: `cut`, `push left 0.3` (a card
arriving), `white flash 0.3` (a chapter), or `element: <label> slides in`. Leave it as `cut` whenever in
doubt; the editor reads an empty Transition field as a cut too.

## Comparing on real footage

```bash
python <skill>/scripts/render_transitions.py VIDEO.mp4 --a 20,24 --b 40,44 --out DIR --kinds "cut,slideleft:0.3,fadewhite:0.3"
```

Renders the same join each way and a labelled reel that plays them back to back. Kinds are ffmpeg xfade
names plus `punch:1.12` (a cut where the second shot lands a touch large and settles).

## Auditing a video

```bash
python <skill>/scripts/audit_transitions.py VIDEO.mp4 --layout camera_audit.json --out t.json
python <skill>/scripts/strips.py VIDEO.mp4 t.json --out strips.png     # frames around each kind, to check the labels
```

With the camera audit's json, every change also gets its context (face to screen, screen to screen, and so
on). Check the strips before quoting numbers; `other` is a catch-all for animated moves.
