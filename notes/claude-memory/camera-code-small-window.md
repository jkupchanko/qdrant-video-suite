---
name: camera-code-small-window
description: "John's house rule that code on screen keeps a small presenter window in the top right (20% width), not a hidden face"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 39bc7a71-3509-46be-83a4-5d1a21b62df7
  modified: 2026-10-14T18:27:17.860Z
---

John said (2026-10-14) that when code is on screen he wants his face kept in a small rectangular box in the top right corner; he likes that layout. So the camera-layout default for code passages is SMALL, top right, 20% width, 4:3. NONE is reserved for results, tables, diagrams and article/B-roll inserts, or when the code or its output runs under that corner.

**Why:** code is explained while it is read, and a code card has nothing in its top right, so the window costs nothing and keeps the presenter present.
**How to apply:** camera_plan.py already encodes it (code regex before the READ_HARD rule, default corner top-right); keep it when writing camera calls by hand. Related: [[camera-layout-skill]], [[broll-keyword-trigger]].
