---
name: script-controls-video
description: "John's rule (2026-10-20): the script controls the whole video (lines, B-roll, camera, transitions, name card); skills can run alone for quick fixes; ask intake questions before building; a missed fault becomes a review check"
metadata:
  node_type: memory
  type: feedback
  originSessionId: be8ef0fa-6d40-4f4e-90af-386ddb45c6e8
  modified: 2026-10-20T22:22:05.294Z
---

"The video is always going to be controlled by the script. Now, you can use the actual skills on its own if you need clear
updates, but in general..." (message cut off there, 2026-10-20). Every direction goes into the script: spoken lines,
`[B-ROLL: ...]`, `[**Camera:** ...]` with **Transition:**, `[**Lower third:** ...]`. To change the video, change the script
and re-run from the affected stage.

Also from the same message: ask the presenter the questions only they can answer before building (name, title...), and
"we need to figure out these audits when we see them": when John hears or sees a fault the review missed (the clipped
"when" at 0:21.9), find it, fix it at its skill, and add a review check that catches it (join_checks.py), with a planted
case in selftest.py. He likes the short progress updates during long work.

**Why:** one source of truth keeps builds repeatable; checks that grow from real misses keep the review honest.
**How to apply:** no hand edits outside the script for a build; intake first; every reported miss -> new check + selftest case.
Related: [[brand-consistency-skill]], [[video-builder-skill]], [[script-three-layers]].
