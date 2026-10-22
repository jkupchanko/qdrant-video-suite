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
6. `raw_edit_checks.py`: the rules above, against this speaker, written to `cut/raw_edit_check.md`.

`--cutter takes` runs the older last-complete-take cutter instead.

## Fixing what the check finds

Read `cut/raw_edit_check.md` and fix every **fix** before showing the cut. **Check** items are for a person to look at.
Fixes go into the cut list, and the cut is rebuilt in minutes:

```bash
python ~/.claude/skills/editing/scripts/respan.py BUILD_DIR/cut RAW.mp4 --mirror --bars 72 --piece "EDIT_T=SRC_IN-SRC_OUT[,SRC_IN-SRC_OUT]" --drop EDIT_T
```

- **restart**: drop the first try's piece, or move its in-point past it.
- **stop**: split the piece around the silence (two spans in one `--piece`).
- **glance**: move the out-point onto the end of the last word, and the next in-point to where the eyes are back.
- **dropped**: add the missing words' span to the piece (or replace the piece with the full second try if the first
  one was cut short).

Put every cut point in a quiet stretch (the take's quiet level, from `join_checks.envelope`). Then run the join check and
the raw edit check again. Both must show no fixes before the cut goes to the presenter.

## When the presenter finds something the check missed

That is a new rule, or a rule measured wrong. Write it down here, plant it in `video-review/scripts/selftest.py`
(`raw_edit_selftest`), make the check catch it there, and confirm it catches the real case without new fixes on an
approved cut. Then fix the cut.
