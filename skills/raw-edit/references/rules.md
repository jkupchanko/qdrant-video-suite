# The raw edit: the rules and why

The raw edit is the presenter's own footage cut to the script, before anything visual is added. A viewer should hear one
person say each thought once, in whole sentences, looking at them. Each rule below comes from something a presenter
flagged by hand on the Get Started raw edit (2026-10-22), and each limit was then checked against 49 popular technical
videos ([research.md](research.md)).

## The rules

### 1. Each thought said once

No restart left in: "For the first, / for the first cluster, I'm just going to name it..." keeps the second try only.

- **Fixed by itself** only when it is sure: the second try repeats all of the first (at least three words if the first
  ends a sentence), or the first stops on a word no sentence ends on (a, an, the, to, of, and, or, but, in, on, at,
  for, with, as, by, from, your, our, my).
- **Shown to a person** (review page) when two or three words match but neither of those holds.

**Why.** The presenter heard "Now this can be useful..." twice at 1:24 and asked for "one clear path that I only say one
time". But in 49 finished pro videos the looser check fired 40 times, nearly all on things said on purpose: lists ("it
can diagnose, it can assemble, it can assess") and sentences that open alike ("It could be changed. It could be
made..."). Cutting those by itself would remove content. With the sure-only rule: 2 fixes in 49 pro videos, and all 11
real restarts in the Get Started cut before checking are still fixed.

### 2. No stop inside a sentence

A silence heard in the cut after a word that does not end the sentence (inside a piece, or a piece's tail plus the next
piece's head) is a stop when it is longer than **twice this speaker's fluent pause, and at least 0.5 s**. Over twice the
limit it is a fix; between the limit and twice it is a check.

**Why.** The presenter: "I stopped during my actual talk" (1:32). Pros' typical pause inside a sentence runs from 0.12 to
0.28 s, so one number cannot fit everyone: it is measured. Only pauses under 1 s count as fluent, because a raw take is
full of stops to think (counting those gave Get Started a limit of 0.79 s, looser than 96% of pros ever go; now 0.59 s).
The 0.5 s floor: 47 of 49 pros keep 90% of their pauses under it.

### 3. No glance with words over it

- **A glance at a cut** (a fix): the piece ends on a word no sentence ends on ("...allows you to"), runs on into a
  thinking pause, and the eyes start to leave the lens there. The piece ends on the word, before the eyes move.
- **A long glance** (a check): the eyes off their resting place by three of their own spreads for 1 s or more.

**Why.** The presenter: "at 2:33 it gets cut off, but I look away and it cuts". A glance at a cut never appears in a
finished pro video (0 of 49), so it is purely a raw-take fault. Short glances are normal: pros look away 14 times a
minute, 93% for under a second, so flagging every 0.3 s glance only adds noise (it flagged three in the approved cut that
the presenter had accepted).

### 4. Nothing lost from the middle of a line

A word of the script line that was said in the take between two kept pieces of that line, but is not in the cut. The
phrase it belongs to goes back in, or the fuller retake replaces a shorter try.

**Why.** "run requests" dropped out of "explore the clusters, manage collections, run requests, and follow tutorials",
and "You can follow" out of "You can follow the Quick Start" (found by this check in a cut the presenter had approved).
Only the script line's own words count, so retakes and asides between pieces are never called losses.

### 5. Whole sentences, close to the script, not word for word

The spoken wording wins when it says the same thing. **Why.** The presenter: "doesn't matter if the script is one to one,
it needs to make sense". A sentence is matched to its script line by content words (`sentence_cut.py`), not word for word.

## Measured on the speaker, never a constant

| what | learned from the take | used for |
|---|---|---|
| fluent pause inside a sentence | the median silence under 1 s after a word with no punctuation, from the sound | a stop is over twice that, at least 0.5 s |
| quiet and voice levels | the 10th and 90th percentile of the take's loudness | where a word starts and ends; every cut point goes in this quiet |
| the eyes' resting place | the median and spread (MAD) of the iris position over the whole take | a glance is three spreads off |
| the lens | `gaze.py` (editing) clusters the gaze; the heaviest cluster is the lens | look-aways in the cut |

Pauses come from the sound because a literal transcript's word times run into each other, and Whisper stretches a word
over a pause ("follow" from 934.5 to 936.9 s): a word is placed in a piece by how much of it overlaps it, not by its
middle, and a quiet stretch inside a stretched word is not counted as a pause.

## How the cut is made

`build.py --only cut` (video-builder) runs:

1. editing's `cut_takes.transcribe`: the take's words as Whisper tidies them (`cut/words.json`); side by side with
2. `transcribe_literal.py`: the take split at every 0.3 s pause, each stretch heard alone, so every attempt is written where
   it was said (`cut/words_literal.json`); and
3. editing's `gaze.py` on the whole take (`cut/raw_gaze.json`).
4. `sentence_cut.py`: whole sentences matched to the script lines, the best take of each chosen over the whole video.
5. `verify_pieces.py`: every piece heard again on its own; false starts and stutters cut.
6. `fix_cut.py --apply`: every fix the check finds, applied, checked again, repeated until none is left.
7. `raw_edit_checks.py` writes what is left to `cut/raw_edit_check.md`, and `review_page.py` writes `cut/review.html`.

## Fixing

Every finding carries its fix: new source spans for the pieces it touches, every cut point in this take's quiet.

- **restart**: drops the first try (its piece, or the part of a piece before the second try).
- **stop**: splits the piece around the silence, keeping a short natural pause.
- **glance**: ends the piece on the last word, before the eyes move.
- **dropped**: adds the phrase the missing words belong to, or swaps in the fuller retake.

```bash
S=~/.claude/skills/raw-edit/scripts
python $S/fix_cut.py BUILD_DIR/cut RAW.mp4 --at 2:33                    # what is at 2:33
python $S/fix_cut.py BUILD_DIR/cut RAW.mp4 --apply                      # fix every fix
python $S/fix_cut.py BUILD_DIR/cut RAW.mp4 --notes review_notes.json    # what the presenter marked on review.html
python ~/.claude/skills/editing/scripts/respan.py BUILD_DIR/cut RAW.mp4 --mirror --bars 72 --piece "EDIT_T=IN-OUT[,IN-OUT]" --drop EDIT_T
```

Then the join check (video-review's `join_checks.py`) and the raw edit check must both show no fixes before the cut goes
to the presenter.

## When the presenter finds something the check missed

It is a new rule, or a rule measured wrong. Write it here with its reason, plant it in video-review's `selftest.py`
(`raw_edit_selftest`), make the check catch it there and on the real case with no new fixes on an approved cut, and run
`audit_raw_edit.py` to see what the 49 videos say. Then fix the cut.
