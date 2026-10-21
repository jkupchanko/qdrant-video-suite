---
name: video-review-skill
description: "the video-review skill (~/.claude/skills/video-review): audits a render from its pixels and sound, reports each fault with time, frame and a marked frame; self-test with planted faults"
metadata:
  node_type: memory
  type: project
  originSessionId: be8ef0fa-6d40-4f4e-90af-386ddb45c6e8
  modified: 2026-10-20T00:08:39.484Z
---

Built 2026-10-19 as the "precision and reviewing" skill John asked for ([[precision-review-phase]]). `scripts/review.py VIDEO --out DIR`
plus `--cut --script --words --gaze --lookaways --broll`; writes report.md / report.json / frames / sheet.jpg. `scripts/selftest.py CUT`
plants four faults (blank, 10% stretch, 3-frame desync, caption off the edge) and must catch all four and invent nothing.

Real faults it found in work that looked done: seven empty-background gaps in the approved Code Report (up to 1.09 s), the legacy
`on_disk = True` and invented "100M / 1B points" on the Animated Board boards, the corner face window cutting the hair (zoom 1.25),
B-roll opening on the previous section and 14 px docs text, -24 LUFS audio, and my own regressions (a label overflowing its card,
then a connector line through it).

**Why:** John wants the small details caught before he sees a video; a plan can be right and the render still wrong.
**How to apply:** run it on every render before showing John, look at every fix frame yourself before acting, fix at the source skill,
re-run until nothing is left to fix. Re-run selftest.py after changing any check. Related: [[broll-recorder-skill]], [[eye-contact-hide-face]].

2026-10-20 additions: `--take` (raw recording, with --cutlist) runs join_checks.py: the next word's first sound kept at an out-point, a piece starting or ending mid-word (fix only when a pause was there to cut in; otherwise check/note), two pieces overlapping. Added because John heard a clipped word the review missed. With --script, brand_pass reads the name lower third by OCR (missing directive, never on screen, misspelled, no title = fix; short, not lower left, no presenter, after 1 min = check). Live code: a word or number typed partway at a line's end is not a typo. selftest.py now also plants two bad joins in a synthetic take. See [[brand-consistency-skill]], [[script-controls-video]].
