---
name: script-three-layers
description: "John's rule that any script request in the video suite must come back with camera calls and transition values written in, not just the spoken lines"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 39bc7a71-3509-46be-83a4-5d1a21b62df7
  modified: 2026-10-15T00:13:07.340Z
---

When John asks for a script (any phrasing), the deliverable is the script with three layers: the script library's structure and lines (with Show and B roll fields), a `[**Camera:** ...]` call under every passage where the camera changes (camera-layout skill), and a `**Transition:**` value on every call limited to the seen vocabulary: cut, push on a card arrival, white flash at a chapter (transitions skill). He does not want to have to name the skills, and he wants the result shown inline in chat, not only as a downloadable file.

**Why:** the whole suite exists so one request produces a finished, consistent script; separate passes defeat that.
**How to apply:** after drafting a script, run camera_plan.py, write the camera calls in the script's own direction lines, fill Transition fields, and paste the script in the reply. Related: [[camera-layout-skill]], [[transitions-skill]], [[broll-keyword-trigger]].
