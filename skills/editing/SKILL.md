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
3. **Checks eye contact** on every chosen take, frame by frame: a frontal face with both eyes near centre.
   Any take under 80% is flagged in the cut list for a human look; it is not silently swapped.
4. **Cuts on word boundaries** with a short handle before the first word and after the last, so a cut
   never clips a syllable.
5. **Fixes the picture**: mirrors it when the webcam recorded a mirror image (house rule: the presenter
   faces the way they do in life), covers a recording tag with a black bar at the bottom and a matching
   bar at the top so it reads as a deliberate frame, and alternates a slight push (1.00 / 1.06) between
   cuts so each jump reads as a cut rather than a glitch.
6. **Fades the audio** 20 ms at every join. No clicks.
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
- **Looking at the lens is not negotiable.** A take where the eyes wander is flagged, not used quietly.
  The only exception is a passage where the script has the presenter looking at something on screen.
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
