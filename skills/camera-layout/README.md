# camera-layout

**Where is the person while this is said?**

The camera piece of the video suite. Give it a script and it returns a camera plan: for each passage, the
layout (full talking head, half split, large inset window, small corner window, or no face), the size and
corner, how long it holds, and why. The rules are not taste; they are measured from 32 of the most-watched
AI and software-development videos (Fireship, NetworkChuck, Tech With Tim, IBM, Theo, Sajjaad Khader and
others), sampled every two seconds and tied to what was being said at each change.

## What the audit found

- Videos use three layouts, not one. A small window left in the corner for the whole video is the
  exception, not the norm.
- The most common move is face to screen and back. Nearly half of all changes are that pair.
- The face comes back fast. Three videos in four return to the full face within 40 s; stretches with no
  face at all run about 10 s and rarely pass 50 s.
- The opening holds about 20 s before the first change, whether it starts on the face or the screen.
- Changes happen where the sentence turns ("now", "so", "let's") and where the words name the screen
  ("code", "terminal", "run", "click"), not on a clock.
- Two families: cut videos (mostly face, 3-4 changes a minute) and window videos (one window over the
  screen, under 1 change a minute). The cut family is the more watched one here.

Full numbers: `references/tendencies.md`. Speech cues at each change: `references/cues.md`.
Layout proportions and framing: `references/layouts.md`.

## Use it

```bash
python scripts/camera_plan.py SCRIPT.md --out camera_plan.md
```

Works on a script from the script-writing skill (it reads the Camera and Show directions and reports where
it disagrees) or on plain prose with headings. Options: `--style window` for long courses that live in one
window, `--corner top-left` to move the window.

To measure a video instead of planning one:

```bash
python scripts/audit.py VIDEO.mp4 --sheet check.png
```

## Files

```
camera-layout/
  SKILL.md                   what Claude follows
  README.md                  this file
  scripts/camera_plan.py     script -> camera plan
  scripts/audit.py           video -> layout timeline and stats
  scripts/tendencies.py      many audits -> the habits
  scripts/cues.py            transcripts + audits -> what is said at each change
  references/tendencies.md   the measured corpus report
  references/cues.md         speech around changes
  references/layouts.md      the five layouts with proportions
  references/audit_summary.csv  one row per audited video
```

Needs Python with opencv-python, numpy and imageio-ffmpeg; cues.py also needs faster-whisper; the corpus
download used yt-dlp.
