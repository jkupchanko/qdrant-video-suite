---
name: shared-repo-no-overwrite
description: "John runs several Claude sessions against the same repo (qdrant-video-suite); never replace a folder wholesale, pull and merge first"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 39bc7a71-3509-46be-83a4-5d1a21b62df7
  modified: 2026-10-14T16:39:05.948Z
---

On 2026-10-14 another of John's sessions pushed a `skills/camera-layout` to qdrant-video-suite while I was building my own version; my `rm -rf` + copy overwrote their files (decision guide, frame review, output format, placeholder SVG, example plan). I restored them from the earlier commit and merged the two.

**Why:** John works in parallel sessions and pushes often ("pushes are being made right now"); a folder in the shared repo may already hold someone else's work by the time I push.
**How to apply:** before writing into `C:\Users\ADMIN\qdrant-video-suite`, `git pull`, then `git log --stat` / `ls` the target folder; add or edit files, never delete-and-copy a whole folder. If two versions exist, merge them and keep both sets of references. Related: [[video-suite-repo]], [[camera-layout-skill]].
