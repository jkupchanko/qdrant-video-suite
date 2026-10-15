---
name: transitions
description: The transitions piece of the video suite. Use when someone asks how to get from one shot to the next in a technical video (cut, dissolve, fade, slide or push, punch-in, card animation), "what transition should I use here", "is this too many effects", wants a transition plan for a script that already has camera calls, wants to audit the transitions in an existing video or a creator's style, or wants the same join rendered several ways to compare. Based on a measured audit of 50 popular AI and software-development videos covering what kind of change they use at each kind of join, how often, and how long the soft ones last.
---

# Transitions

The camera plan says where the person is for each passage. This skill says how the picture gets from one
state to the next: at a camera change, at a change of card or page, and when a label or card appears over a
shot that stays. The answer is nearly always a cut, and the skill's value is mostly in saying when it is not,
and in keeping the few soft moves short and consistent.

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

1. **Default is a cut.** Every camera call in the script (FULL, SMALL, NONE and back) is a cut unless a rule
   below says otherwise. A cut lands on the sentence turn the camera call already sits on.
2. **Slide or push for a card that arrives while the shot stays in mind.** When a code card, a result or a
   checklist comes in over the presenter and will go away again, a short push (0.25 to 0.3 s, one direction
   for the whole video) is the one soft move the corpus uses with any regularity. Use it for arriving cards,
   not for leaving them: a card leaves on a cut.
3. **Dissolve only between two screens of the same kind.** Page to page, card to card, when the content
   changes but the viewer's attention does not. 0.25 s. Never between the face and a screen.
4. **Fade to black only at a chapter boundary**, and at most once or twice in a video. 0.4 s. Never inside a
   demonstration.
5. **Elements are not transitions.** Labels, captions and highlights pop or slide in over the shot; they do
   not change the shot. Keep one entrance style for them for the whole video (the motion-design rule).
6. **One vocabulary per video.** Pick the push direction, the dissolve length and the element entrance once.
   A video with three kinds of transition reads as edited; one with eight reads as a template.
7. **Never more than one soft move in a row.** Soft, cut, soft is fine. Two dissolves back to back read as
   a slideshow.

## Writing it into the script

The script's `**Transition:**` field already exists. Fill it with one of: `cut`, `push left 0.3`,
`dissolve 0.25`, `fade black 0.4`, or `element: <label> slides in`. Leave it as `cut` whenever in doubt;
the editor reads an empty Transition field as a cut too.

## Comparing on real footage

```bash
python <skill>/scripts/render_transitions.py VIDEO.mp4 --a 20,24 --b 40,44 --out DIR --kinds "cut,slideleft:0.27,dissolve:0.25"
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
