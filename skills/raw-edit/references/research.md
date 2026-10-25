# What 49 popular technical videos say about the raw edit

The camera and transitions audits (2026-10-14) measured 50 popular AI and software-development videos for layouts and
shot changes. On 2026-10-24 the same videos were measured again for what the raw edit decides: pauses, restarts, stops
and glances. 49 downloaded (one is no longer public). `scripts/audit_raw_edit.py` measured the first five minutes of
each, the way `raw_edit_checks.py` measures a take, and ran our checks on each finished video as if it were our cut. Our
approved Get Started raw edit was measured the same way, to compare.

![Checked against 49 popular technical videos](../images/research.png)

## What was measured, and what it showed

| measure | 49 pro videos | our approved cut | what it decided |
|---|---|---|---|
| typical pause inside a sentence | median 0.14 s (from 0.12 to 0.28 s) | 0.14 s | the stop limit is learned per speaker, with a 0.5 s floor |
| 90th percentile of those pauses | median 0.28 s; under 0.5 s in 47 of 49 | 0.28 s | 0.5 s is past what 96% of pros ever leave |
| restart fixes on a finished video | 40 hits before the change, mostly lists said on purpose; 2 after | 0 | only a sure restart is fixed by itself; the rest go to a person |
| stop fixes | none in 40 of 49 | 0 | kept: most pros never leave one |
| glance at a cut (stop mid-thought, then the eyes go) | none in 49 of 49 | 0 | kept: it is a raw-take fault, never in a finished edit |
| any glance of 0.3 s or more | 14 a minute; 93% under 1 s | 8 a minute | flag only glances of 1 s or more |
| speaking rate | median 194 words a minute | 211 | (not a rule) |
| jump cuts a minute, face videos | median 8 (90th percentile 21) | 24 | not a rule: see below |

## The decisions, with the reason for each

1. **The stop limit is twice the speaker's fluent pause, at least 0.5 s.** Pros' typical pause inside a sentence runs from
   0.12 to 0.28 s, so no single number fits everyone; that is why it is measured. It was measured over every pause in
   the raw take, which counts stops to think: Get Started gave 0.52 s and a limit of 0.79 s, looser than 96% of pros
   ever go. Now only pauses under 1 s count (0.29 s on Get Started), and the limit is twice that (0.59 s). The 0.5 s
   floor: 47 of 49 pros keep 90% of their pauses under it.
2. **A restart is fixed by itself only when it is sure.** On the 49 finished videos the restart check fired 40 times, and
   nearly all were said on purpose: lists ("it can diagnose, it can assemble, it can assess") and sentences that open
   alike ("It could be changed. It could be made..."). Fixing those would cut the content. So a restart is fixed by
   itself only when the second try repeats all of the first ("For the first, / for the first cluster"; at least three
   words if the first ends a sentence) or the first stops on a word no sentence ends on (a, the, to, of, with, our...).
   Anything else is shown on the review page for a person. After the change: 2 fixes in 49 videos, and all 11 real
   restarts in the Get Started cut before checking still fixed. "This", "that", "is", "are" and "be" were taken off the
   cut-off list: pros end sentences on them ("we've got this", "what generics are").
3. **The glance at a cut stays a fix.** No finished pro video has one, so it is purely a raw-take fault: the speaker stops
   mid-thought and looks away to think, and only a cut placed after the last word shows it.
4. **Other glances are flagged from 1 s, not 0.3 s.** Pros look away from the lens 14 times a minute, 93% of the time for
   under a second; it reads as thinking, not as a fault. At 0.3 s the check flagged three glances in the approved cut that
   the presenter had accepted. At 1 s it flags none there, and only the long looks in pro videos.
5. **Dropped script words stay a fix.** It cannot be measured on finished videos (their scripts are not known); it comes
   from the presenter ("run requests" lost from a list) and is exact: only words of the script line that were said count.

## What it did not change, and why

- **Jump cuts.** Our approved cut has 24 joins a minute, more than 90% of the pros (median 8). They are 57 line changes,
  47 restarts taken out and 26 long pauses taken out (the median gap removed is 4.9 s): the joins come from how many
  retakes the take has, not from cutting too much. Fewer retakes while recording, or a picture laid over the join
  later, is the answer, not a rule here.
- **Silence across a join.** Pros' jump cuts mostly go word to word; ours keep about 0.24 s. Not changed: the measure is
  mixed with false cut detections (below), and a tighter join risks a clipped word, which a presenter noticed before.
- **Zoom at a jump cut.** Measured, but the face boxes are too noisy: the approved cut changes its zoom at 2 joins and the
  measure said 55%. Not used.

## Limits

- The first five minutes of each video, with `small.en` and greedy decoding: enough for the words a restart needs.
- Jump cuts are found as a frame difference five times its own neighbourhood. On the approved cut, where every join is
  known, that finds 68 of 73 joins with about two false cuts a minute (gestures), so the pros' rate is a little high.
  The first version used a fixed threshold and found 0 of 127 joins: always test a detector on a cut where the answer is
  known before trusting it.
- The eyes are read at 360p, 3 frames a second, and only where the face is large.
- These are popular videos, not necessarily good raw edits; they show what viewers accept, which is the bar.

Re-run: `python scripts/audit_raw_edit.py CORPUS_DIR` (the video IDs are the file names in camera-layout's
`references/audit_summary.csv`; `yt-dlp` at 360p), then `python scripts/make_images.py --audit CORPUS_DIR/raw_edit_audit
--ours OUR_CUT_RESULT.json --out ../images --only research`.
