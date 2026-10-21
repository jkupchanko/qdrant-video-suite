---
name: video-builder-skill
description: "2026-10-20 the one-request build (~/.claude/skills/video-builder): raw take + three-layer script -> every suite skill in order -> mastered video -> video-review; the listed-sections style it uses; what the first build caught"
metadata:
  node_type: memory
  type: project
  originSessionId: be8ef0fa-6d40-4f4e-90af-386ddb45c6e8
  modified: 2026-10-20T16:44:19.474Z
---

John's goal (2026-10-20): "ask it a question... can you build this for me", and it uses all the skills together, with the review
as the final step that confirms the video and identifies the issues. Built as `~/.claude/skills/video-builder/scripts/build.py
--take RAW --script SCRIPT --out BUILD_DIR`: stages cut (editing) -> words -> gaze -> camera (camera-layout) -> keyterms ->
broll (broll-recorder) -> assets (page_assets.py) -> style -> master -> review (video-review), resumable per stage, BUILD.md at the end.

The default style is the new **listed-sections** style (`camera_audit/styles/style_list.py`), the only one that builds itself
from script + docs page + cut (Code Report and Animated Board are hand-authored per video). Copied from peer list videos John
asked to see (`camera_audit/peers/peer_list_layouts.jpg`, also on the Desktop under Bulk Uploads/list style): ByteByteGo's master
list with the current row lit, Fireship's numbered card + TRADEOFF chips (BEST FOR / WATCH FOR from the docs' own lines),
NeetCode's group cards. Imagery is the docs page's own figures and code captured at 2x.

Build 1 from the raw take: the review first found 7 fixes (8 with the final review, which also flags the face where the lost B-roll was), all real: 6 script lines the editing skill dropped because they were said
in other words (strict first/last-word match), and the Option 3 B-roll lost because the style placed one dropped line at the
wrong time. Fixed at the source (cut_takes.py second pass between neighbours' takes; style refuses unplaced/out-of-order lines),
then build 2. Same final review on all three builds: build 1 8 fix / 36 check, build 2 0 / 25, build 3 0 / 19 (the 19: corner window vs FULL calls, docs text 23 px vs 24, the script's Count still timed for the v2 cut, title over the chin, list lead-in). Final video: Desktop/Qdrant Videos/Bulk Uploads/list style/. Related: [[video-review-skill]], [[editing-skill]], [[precision-review-phase]], [[script-three-layers]].

**Why:** John wants one command from recording to reviewed video, and to see the review prove itself on a real build.
**How to apply:** for "build/make this video", run video-builder; read the review, fix at the stage that caused each fix, re-run
from that stage; report from report.json with frames.

Build 4 (2026-10-20, builds/bulk_uploads_list_build4, Desktop .../list style/bulk_uploads_listed_sections_build4_*.mp4): John heard a clipped word in build 3; fixed at the cut (sound-placed edges), the review got join_checks (--take), the name lower third and live-typed code added, intake questions before building (build.py exits 2 without a name card). Review: 0 fix / 23 check / 11 notes. Render ~32 min, review ~8-18 min. Pushed as 93af2e2. See [[brand-consistency-skill]], [[script-controls-video]].
