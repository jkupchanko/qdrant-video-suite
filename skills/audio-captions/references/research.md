# What 49 popular technical videos say about voice and captions

The same 49 popular AI and software-development videos the camera, transitions and raw-edit audits used (one of the 50
is no longer public), measured again on 2026-10-26 for what this skill decides: how clean and how loud the voice is, and
whether and how captions sit in the picture. `scripts/audit_audio_captions.py` measured the first five minutes of each
360p copy, using the words raw-edit's audit had already transcribed. The cleaner's own measure (`voice_clean.measure`)
was then run on the whole of each video, so the limits below are in the same units the cleaner uses.

![49 popular technical videos: captions and voice](../images/research.png)

## What was measured, and what it showed

| measure | 49 pro videos | Get Started (our cut) | what it decided |
|---|---|---|---|
| captions burned into the picture | **0 of 49** | | captions ship as a file (SRT/VTT) by default; burning in is an option |
| loudness | median -21.7 LUFS (90% between -24.7 and -18.4) | | the master stays at -14 LUFS (see 4 below) |
| voice above the room (cleaner's measure) | median 39.5 dB; 10% under 29.0; lowest 24.8 | 48.3 dB | denoise only under 30 dB |
| share of energy under 100 Hz | median 1.5%; 10% over 7.9% | | 80 Hz high-pass only over 5% |
| mains hum 6 dB or more out of the quiet | 2 of 49 (6.1 and 6.4 dB) | none | notch only at 6 dB or more |
| loudness range (3 s windows) | median 3.3 LU | | (not a rule: speech is already even) |
| level jumps over 3 dB between the cut's pieces | (no cut lists for finished videos) | 36 before, 0 after (an independent LUFS meter: 34 to 3) | even every piece more than 1.5 dB off |

How the caption detector was proven before it was trusted: the same clip with its own words burned in, and without them.
Burned: 56 of 59 speech seconds found as captions. Plain: 0 (its slides and animated titles repeat the speech, but hold
still or come and go; a caption changes nearly every second in one band of the frame). A detector that found nothing on
49 videos could have been broken; this one finds captions when they are there.

## The decisions, with the reason for each

1. **Captions are a file, not burned in, by default.** None of the 49 burn them in. Technical videos are watched at a
   desk, and the screen carries code, docs and cards that a caption bar would cover. YouTube shows the uploaded file as
   closed captions the viewer can turn on, and indexes its words for search. `--burn` (`build.py --captions burned`) still
   makes a burned copy for platforms that play without sound (a social clip).
2. **The burned look is the subtitle rules in the brand, not a copy.** With no pro example to measure, the burned style
   (`caption_style.json`) is the reading standard: two lines of up to 32 characters, held long enough to read at 17
   characters a second, low in the frame, in Mona Sans on a dark box. No word highlight and no all-capitals: those are
   short-form social looks, and none of the 49 uses them.
3. **Denoise only under 30 dB.** A denoise always costs a little of the voice. The pros' voices sit a median 39.5 dB above
   their room, and 9 of 10 sit above 29 dB. Under 30 dB a take is noisier than nearly every pro video, so the room is
   taken down; above it, the take is left alone. (35 dB was the first guess: it would have denoised 15 of the 49 pros.)
4. **Loudness stays at -14 LUFS, louder than the pros.** The pros sit at a median -21.7 LUFS. YouTube turns anything
   louder than -14 down to -14 and never turns a quiet video up, so a -14 master plays at the platform's reference level and a
   -21.7 one plays 7.7 dB quieter. A voice-only video has nothing to lose by being at the reference. The master stage
   (master_audio.py) sets it; this skill does not.
5. **High-pass only when the take rumbles.** Pros carry a median 1.5% of their energy under 100 Hz; 1 in 10 over 7.9%.
   A voice has almost nothing down there, so a take over 5% has a fan, a desk knock or a boomy room, and an 80 Hz
   high-pass takes it out without touching the voice.
6. **Hum is notched only when it stands out.** Two pros show a borderline 6 dB peak at mains frequency; the notch is
   three narrow bands (the hum and two harmonics), which costs a voice nothing audible.
7. **Every piece of the cut is evened, not the whole take compressed.** A cut joins pieces from different moments; one
   can sit 6 dB under the next. The pros' loudness range is a narrow 3.3 LU, so an even voice is the norm. Each piece more
   than 1.5 dB from the cut's own median is brought to within 1 dB of it, with 30 ms ramps: no join can jump much more
   than 3 dB. On Get Started: 36 joins over 3 dB before, 0 after (biggest 6.9 to 2.5 dB). Checked with a separate
   meter (pyloudnorm, per piece): joins over 3 LU 34 to 3, the spread between pieces 1.86 to 0.97 LU. A piece's level is the
   power mean of its voiced part, gated 15 dB under its own peak, so it moves exactly with a gain: the first measure (a
   median over a fixed threshold) under-read how far a loud piece came down.
8. **The voice never moves.** Every filter's delay is measured by cross-correlation and taken back, and the length is
   kept to the sample: the first denoise tried (afftdn) put the voice 25 ms behind the lips.

## Not decided by the research

- **Spelling.** Captions are what was said, spelled the way the script spells it, with a glossary for product names.
  The pros' captions are not readable at 360p to check, so this comes from the script, not the corpus.
- **Music.** This skill is voice only by choice: no music bed.
