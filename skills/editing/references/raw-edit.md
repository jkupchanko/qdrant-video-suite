# The raw edit: one clean pass

The raw edit is the presenter's own footage cut to the script, before anything visual is added. A viewer should hear one
person say each thought once, in whole sentences, looking at them. This file is the rule set, how each rule is measured,
and how to fix what the check finds. It comes from the Get Started raw edit (2026-10-22), where the presenter flagged the
same four faults again and again until the cut was right.

## The rules

1. **Each thought said once.** No restart left in: "Now this can be useful if you want more of a... / Now this can be
   useful if you want more control" keeps the second try only. A list that repeats its opening on purpose is not a
   restart ("You can run it locally, you can deploy it, or use the cloud"). The first try counts as a restart only when it
   was cut off (three words or fewer, or it ends on a word a sentence cannot end on: *to, the, a, of, with...*) or when it
   matches the second try for three words, not just two.
2. **No stop inside a sentence.** A silence heard in the cut after a word that does not end the sentence must not be longer
   than this speaker's normal pause inside a sentence. That includes a piece's tail plus the next piece's head.
3. **No glance with words over it.** The eyes leaving the lens while speaking. The most common case is the hardest to see:
   the presenter stops mid-thought ("...allows you to"), looks away to think, then goes on. The piece must end on the
   word, before the eyes move, and the next piece must start after they are back.
4. **Nothing lost from the middle of a line.** A word of the script line that was said in the take, between two kept
   pieces of that line, but is not in the cut, is a loss. The typical case is a list item: "run requests" dropped from
   "explore the clusters, manage collections, run requests, and follow tutorials". Retakes and asides between pieces
   are not losses: only the script line's own words count.
5. **Whole sentences, close to the script, not word for word.** The spoken wording wins. A sentence said in other words
   is fine if it makes sense and says the same thing.

## Everything is measured on this speaker, not on a constant

People pause, glance and restart differently, and the suite is used by a whole team, so no threshold is fixed for
everyone. Each one is learned from the take before it is applied (`video-review/scripts/raw_edit_checks.py`, `speaker()`):

| what | learned from the take | used for |
|---|---|---|
| pause inside a sentence | the median silence (from the sound, not the transcript) after words with no punctuation | a stop is over 1.25x that, at least 0.5 s; a fix over 2x |
| quiet and voice levels | the 10th and 90th percentile of the take's loudness | where a word starts and ends, every silence |
| the eyes' resting place | the median and spread (MAD) of the iris position over the whole take | a glance is 3 spreads off for 0.3 s or more |
| the lens | `gaze.py` clusters the gaze and takes the heaviest cluster as the lens | look-aways in the cut |

A fast talker's 0.4 s silence is a stop; a slow talker's is a breath. A presenter who reads off to one side has a
different resting place. Both are handled by measuring first.

Pauses come from the sound because a literal transcript's word times run into each other, and Whisper stretches a word
over a pause ("follow" from 934.5 to 936.9 s), so words are placed in a piece by how much of them overlaps it, not by
their middle.

## How the raw edit is made

`build.py --only cut` (video-builder) runs, in order:

1. `cut_takes.transcribe`: the take's words, as Whisper tidies them (`cut/words.json`).
2. `transcribe_literal.py`: the take split at every 0.3 s pause, each stretch transcribed alone, so every attempt is
   written where it was said (`cut/words_literal.json`). Whisper's default transcript writes a restart once.
3. `gaze.py` on the whole take (`cut/raw_gaze.json`).
4. `sentence_cut.py`: whole sentences matched to the script lines, the best take of each chosen over the whole video,
   silences over 0.45 s removed from inside a line.
5. `verify_pieces.py`: every piece heard again on its own, and false starts and stutters cut.
6. `fix_cut.py --apply`: every fix the check finds, applied and checked again.
7. `raw_edit_checks.py`: what is left, against this speaker, written to `cut/raw_edit_check.md`, and `cut/review.html`
   to click through it.

Steps 1 to 3 run side by side (each reads the whole take; on a 14-core laptop they do not slow each other).

`--cutter takes` runs the older last-complete-take cutter instead.

## Fixing what the check finds

The build fixes them itself before anyone watches: every finding carries its fix (new source spans for the pieces it
touches, each cut point in this speaker's own quiet), and `fix_cut.py --apply` applies them, rebuilds the cut, checks
again and repeats until nothing is left to fix. What it does by kind:

- **restart**: drops the first try (its piece, or the part of a piece before the second try starts).
- **stop**: splits the piece around the silence, keeping a short natural pause.
- **glance**: ends the piece on the last word, before the eyes move.
- **dropped**: adds the phrase the missing words belong to, or swaps in the fuller retake when the piece before is a
  shorter try of the same phrase ("the Quick Start" -> "You can follow the Quick Start").

```bash
python ~/.claude/skills/editing/scripts/fix_cut.py BUILD_DIR/cut RAW.mp4 --at 2:33           # what is at 2:33
python ~/.claude/skills/editing/scripts/fix_cut.py BUILD_DIR/cut RAW.mp4 --apply             # fix every fix
python ~/.claude/skills/editing/scripts/fix_cut.py BUILD_DIR/cut RAW.mp4 --notes review_notes.json
```

`--at` shows the pieces around a time with their words, the words said between pieces that the cut leaves out, where
the eyes leave their resting place (`~`), and the findings there. Use it when a person names a time the check did not
flag, then fix with `respan.py` (below).

**The person reviews on a page, not in a chat.** The build writes `cut/review.html` (video-review's `review_page.py`):
the cut with every flagged moment beside it. They click a time to jump there, mark it Fine or Fix, and press M wherever
something is off that nothing flagged. "Save notes" gives `review_notes.json`; `fix_cut.py --notes` fixes the ones marked
Fix and shows each added moment with `--at`. "Copy notes" gives the same as text to paste into a chat.

By hand, for anything else: `respan.py` changes or drops pieces by their edit time.

```bash
python ~/.claude/skills/editing/scripts/respan.py BUILD_DIR/cut RAW.mp4 --mirror --bars 72 --piece "EDIT_T=SRC_IN-SRC_OUT[,SRC_IN-SRC_OUT]" --drop EDIT_T
```

Put every cut point in a quiet stretch (the take's quiet level, from `join_checks.envelope`), then run the join check and
the raw edit check again. Both must show no fixes before the cut goes to the presenter.

## When the presenter finds something the check missed

That is a new rule, or a rule measured wrong. Write it down here, plant it in `video-review/scripts/selftest.py`
(`raw_edit_selftest`), make the check catch it there, and confirm it catches the real case without new fixes on an
approved cut. Then fix the cut.
