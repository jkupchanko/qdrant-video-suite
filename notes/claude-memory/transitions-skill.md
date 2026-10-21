---
name: transitions-skill
description: "The transitions skill (fourth piece of John's video suite): 50-video audit numbers, classifier limits, where the corpus and tools live"
metadata:
  node_type: memory
  type: project
  originSessionId: 39bc7a71-3509-46be-83a4-5d1a21b62df7
  modified: 2026-10-14T23:18:48.180Z
---

Built 2026-10-14 at `~/.claude/skills/transitions` and in the suite repo under `skills/transitions`. Corpus: the 32 camera-audit videos plus 18 more (`C:\Users\ADMIN\camera_audit\videos2`, audits in `audit2/`, `transitions2/`; merged in `audit_all/`, `transitions_all/`). Camera tendencies were re-rolled over the same 50.

Key numbers: 62% of visible changes are element animations (labels/cards over a held shot), not shot changes. Among shot changes: cut 65%, slide/push 6%, dissolve 4%, fade 4%, animated "other" 20%. Face<->screen joins are cuts (45-52%) with slides 3-5%; only 7/43 videos soften more than a quarter of them. Soft moves median 0.27 s. 2.6 shot changes/min median.

John's Bulk Uploads edit: 56% slides, 29% cuts among shot changes, 11.9 shot changes/min: the inverse of the corpus; the rules keep the push for cards arriving over the face and cut everything else.

Classifier (`audit_transitions.py`): streams frames in two passes (long videos do not fit in RAM; running two audits in parallel OOMed). `other` = unnamed animated whole-frame moves; bright graphic wipes can read as fade-white; punch-ins between different takes count as cuts. `render_transitions.py` uses ffmpeg xfade plus a `punch:S` variant.

**How to apply:** when John asks about transitions or effects between shots, use this skill; cut by default, push only for arriving cards, dissolve only screen-to-screen of the same kind, fade only at chapter breaks. Related: [[camera-layout-skill]], [[motion-design-feedback]], [[video-suite-repo]].
