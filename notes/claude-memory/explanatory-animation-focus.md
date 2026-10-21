---
name: explanatory-animation-focus
description: "2026-10-16 John narrowed the style work to explanatory animation: which animation types support what is being said, how top creators time and build them, and the best way to do it"
metadata:
  node_type: memory
  type: project
  originSessionId: 39bc7a71-3509-46be-83a4-5d1a21b62df7
  modified: 2026-10-16T16:11:33.007Z
---

After nineteen channel-copied editing styles ([[editing-styles-five]]), John asked (2026-10-16) to focus on animations specifically: the different kinds of animation that support an explanation while he talks, how people animate things across many examples, and "keep looking until you find" the best way.

Result (2026-10-16): the progressive build on one board is the best way. One piece per spoken idea about every 2 s, starting 0.2 to 0.4 s before the word, under 1 s, ease-out; focus by dimming the rest; transform instead of cut; clear only in pauses. Measured in C:\Users\ADMIN\camera_audit\anim_audit (detect.py, labels.txt, stats.py, scenes.py, gallery/, report.md). Kit in camera_audit\animkit (animkit.py, timing.json, demo_bulk.py), composited by styles\style_animdemo.py, copied into the local editing-style skill. Demo: Desktop\Qdrant Videos\Bulk Uploads\animated_board_demo_0-41s_720.mp4. His reaction: "This looks incredible, actually. Good job." He then asked for the full video. Full video (2026-10-16): animkit\full_bulk.py (nine scenes, one per section) composited by styles\style_full.py over a v2 cut (edit\full_edit\bulk_uploads_full_edit_v2.mp4, which drops a 3.6 s silence and a doubled "And finally, for larger uploads"; the original cut is unchanged).

**Why:** the styles showed him many looks; what he wants to get right is the motion that explains, tied to his words.
**How to apply:** measure animation events in reference videos (type, entrance duration, easing, hold, sync to the spoken keyword), ground the rules in multimedia-learning research, and turn the result into a reusable animation vocabulary applied to his cuts. Pacing note still holds: not too fast, holds are fine ([[animation-pacing-feedback]]).
