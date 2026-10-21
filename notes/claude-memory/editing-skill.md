---
name: editing-skill
description: "The editing skill (raw talking-head take + script -> clean cut with cut list), John's editing rules, and where it lives in the suite"
metadata:
  node_type: memory
  type: project
  originSessionId: 39bc7a71-3509-46be-83a4-5d1a21b62df7
  modified: 2026-10-15T05:06:27.810Z
---

Built 2026-10-14 at `~/.claude/skills/editing` and `qdrant-video-suite/skills/editing` from the first-30-seconds edit of John's Bulk Uploads Zoom take (`C:\Users\ADMIN\camera_audit\edit\`). `scripts/cut_takes.py RAW.mp4 SCRIPT.md --out DIR --max-seconds 30 --mirror --bars 72`.

John's editing rules (2026-10-14): he must be looking at the lens whenever he talks (flag, never silently swap); cuts clean on word boundaries with a push between them; mirror the webcam image; hide the Zoom tag with a black bar and a matching bar on top; small amounts at a time (30 s); keep spoken wording over the script; ask when two takes conflict. Last complete take wins when there are retakes.

The suite README's "Choose a part of the video" cards: Editing and Transitions are now live links; Visual explanations and Audio and captions remain Coming soon (Final review and Brand consistency went live 2026-10-20). John wants every skill card to open to a clean explanatory image (like the camera boards), not demos.

**How to apply:** when John hands over a raw take, run cut_takes.py, read the cut list, report the flags and wording differences, deliver a 720p copy next to the source. Related: [[camera-layout-skill]], [[transitions-skill]], [[script-three-layers]].

2026-10-20: the strict take match (first and last script words) dropped 6 of 42 Bulk Uploads lines said in other words; a second pass now looks between the neighbours' takes (half the content words, whole spoken sentence, from the last restart). script_lines() also skips <!-- notes --> and the three-layer script's ## Count section. See [[video-builder-skill]].

2026-10-20 (later): John heard a clipped word ("...dense and sparse vectors. Wh-" at 0:21.9 of the listed-sections build). Cut points placed by transcript times alone started mid-sound at 20 of 26 joins and kept the next word's first 40 ms there; two pieces also overlapped (a word heard twice). cut_takes.py now places edges by the sound (pauses = 3+ steps of 10 ms below the take's own quiet level; out-point never past the voice rising out of a pause; a hiss right after the last word is its tail; neighbouring pieces never overlap). Join check: 16 fixes on the old cut, 0 on the new; 5 joins where words run together are left as checks to listen to.
