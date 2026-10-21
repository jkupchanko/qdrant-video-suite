---
name: pacing-context-feedback
description: "John's build 4 notes (2026-10-20): first B-roll must show which page it is; cards too fast to read; boss wants slower soft transitions; brand colours from Qdrant's own brand skill; name card first; small guide animation on full face"
metadata:
  node_type: memory
  type: feedback
  originSessionId: be8ef0fa-6d40-4f4e-90af-386ddb45c6e8
  modified: 2026-10-20T23:39:10.766Z
---

After watching build 4 (liked the structure, "simple... clean layout"):
- B-roll at 0:23 showed a docs section without saying what page it was: "show the title and a few of the sections, or show
  me clicking on the actual article so that people can actually see where you can find it". -> broll-recorder `arrive`
  style (`--arrive-first`): page top, click the article in the docs menu, mark the title, click the section in "On this
  page", scroll, hold. Readthrough now settles (>= 1.8 s still at the end).
- At 0:40 the code, Best for and Watch for flashed by: "I can't actually sit there and look at it". -> one item card that
  stays up (code typed + tradeoff beside it), scheduled by reading time (3.8 wps, code 65 cps).
- His boss: "how quick we are transitioning" -> soft 0.8 s transitions (soft_zoom, dissolve), engine TR 0.8. He likes the
  small zooms. Face-to-face stays a cut.
- "when I'm full screen... a little animation to help guide the direction" -> the top-left where-we-are chip.
- Brand: copy Qdrant's own brand skill into the repo ("those colors, those logos... the whole entire nine yards") and use it.
- "put the title your name first" -> read as: name card opens the video, then the title (unconfirmed reading).
- The review must catch all of these (abrupt, read, broll_context, brand_colour checks).

**Why:** viewers must be able to read and orient; abrupt changes bother his boss.
**How to apply:** default every listed-sections build to these; when a card or B-roll would be shorter than its reading time, drop or merge rather than flash. Related: [[transitions-skill]], [[broll-recorder-skill]], [[brand-consistency-skill]], [[animation-pacing-feedback]].
