---
name: editing
description: The editing piece of the video suite. Use when someone has a raw talking-head recording (Zoom, webcam, phone) and a script and wants it cut, or says "edit this", "cut this down", "pick the good takes", "I did several retakes", "make the cuts clean", "flip it", "hide the Zoom tag", or asks for the first N seconds edited. It transcribes the take, finds every take of every script line, keeps the last complete one, checks that the presenter is looking at the lens on each chosen take, cuts on word boundaries with short handles, mirrors, covers a recording tag with matching bars, alternates a slight push between cuts, fades the audio at every join, and writes a cut list saying which take each line came from and where the spoken words differ from the script. Also use it after the script, camera and transitions skills have done their part, to produce the face-only cut the B-roll and transitions are laid onto.
---

# Editing

The raw take is the hardest part to hand to anyone else: several retakes per line, stumbles, ad-libs, a
camera tag in the corner, a mirrored webcam. This skill does the first pass a careful editor would do by
hand, in one command, and writes down every decision so a person can change any of them.

## What it does, in order

1. **Transcribes** the recording with word timestamps.
2. **Finds every take of every script line.** A line said five times is five takes; the last complete one
   is kept, because that is the one a presenter settles on. Stumbles, half-lines and ad-libs between lines
   are dropped. If a line was never said, the cut list says so instead of guessing.
   **A line said in other words is still found.** The strict match wants the line's first and last words; a
   presenter who says "Now we just went through all three options for dense vectors" for "Those first three
   options were for dense vectors." misses it. So a line the strict pass misses is looked for again, only where it
   must be (between the takes of the lines either side), as the run that says at least half its content words,
   cut to the whole spoken sentence (the transcript's full stops and pauses), from the last restart. The first
   end-to-end build lost 6 of 42 lines (53 s of the video) to the strict match alone; the cut list marks these
   "said in other words".
3. **Checks eye contact** on every chosen take, frame by frame: a frontal face with both eyes near centre.
   Any take under 80% is flagged in the cut list for a human look; it is not silently swapped.
4. **Cuts on word boundaries, placed by the sound**, so a cut never clips a syllable. The transcript's word times can be
   a quarter of a second off, and cut points placed by them alone clipped words: the in-point started mid-sound at 20 of
   26 joins of one build, and an out-point kept the first 40 ms of the next word ("...dense and sparse vectors. Wh-",
   which a person heard). So the in-point is the end of the last pause before the first word (up to 0.45 s back, with a
   little room tone), the out-point is the first silence after the last word but never past the voice rising out of a
   pause into the next word, a hiss right after the last word (its s, ch) stays in as that word's tail, and two pieces
   next to each other in the take never overlap (nothing is heard twice). Where one word runs straight into the next, the
   cut takes the quietest moment between them; the review's join check lists those for a listen.
5. **Fixes the picture**: mirrors it when the webcam recorded a mirror image (house rule: the presenter
   faces the way they do in life), covers a recording tag with a black bar at the bottom and a matching
   bar at the top so it reads as a deliberate frame, and alternates a slight push (1.00 / 1.06) between
   cuts so each jump reads as a cut rather than a glitch.
6. **Fades the audio** 20 ms at every join. No clicks. **Joins with the voice locked to the lips**
   (`scripts/assemble.py`): every piece is exact to the frame in both picture and sound, so nothing drifts
   however many joins there are. Stitching per-piece AAC files with `-c copy` drifted 1.4 s over 53 joins.
7. **Writes it down**: `cut.mp4`, `cutlist.md` (edit time, source time, push, script line, what was actually
   said, which take of how many, eye-contact score), and `gaze_sheet.png` (the eyes on every chosen take).

```bash
python <skill>/scripts/cut_takes.py RAW.mp4 SCRIPT.md --out DIR --max-seconds 30 --mirror --bars 72
```

## Rules the cut keeps

The full list, with the reasons, is in [references/rules.md](references/rules.md): choosing the take, eyes on
the lens, where a cut goes (out-point at the real end of speech plus air, never into the next word, pauses
over 0.7 s removed), the picture and sound, and what to check before shipping. The short version:


- **Spoken wording wins.** If the presenter said "all workflows" and the script says "every workload", the
  cut keeps the words that were said; the cut list shows the difference so the writer can decide.
- **Looking at the lens is not negotiable.** `scripts/gaze.py` tracks the irises frame by frame and learns
  the presenter's lens position from clusters of gaze, not the median (reading to the side is its own
  cluster). Any look-away of 0.25 s or more, or any clear glance, is swapped for a clean take. If no clean take
  exists, it is listed in `lookaways.json`, measured on the finished cut with `--lookaways`, so the styling
  pass takes the face off screen there. Demos, where the presenter is meant to look at the screen, are exempt.
- **Cut on the word, never on the breath.** In-point 0.08 s before the first word; out-point where the voice
  actually stops plus 0.25 s, never into the next word. Silences over 0.7 s inside a line are removed.
- **Nothing added.** No music, no labels, no B-roll. Those are other skills, laid on this cut afterwards.
- **Length is a sentence boundary.** `--max-seconds 30` stops at the last line that ends under 30 s, not
  mid-sentence.

## When a human has to decide

The tool asks in the cut list rather than guessing: a line with no take found, a take with eye contact
under 80%, a line that would push the cut past the requested length, and every place the spoken words
differ from the script. Read the cut list before shipping the cut.

## Hand-off

This produces the face-only cut. The camera skill's calls say where the face goes NONE or SMALL; the
B-roll skill supplies what replaces it; the transitions skill says how the join is made. `assets/how-it-works.png`
shows the six steps on a real take.
