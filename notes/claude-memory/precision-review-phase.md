---
name: precision-review-phase
description: 2026-10-19 John's next phase: rebuild Bulk Uploads from scratch with all skills together (script, cut, B-roll, both editing styles) and build a review skill that audits the small details
metadata:
  type: project
---

On 2026-10-19 John said he is "not a big fan" of the NetworkChuck-style sample and moved to the last skill: **precision and reviewing**. He wants to "look at the small details, pay attention".

The plan:
1. Rebuild Bulk Uploads from scratch using every skill together: the existing script edited into three layers (B-roll by key term, camera calls, transitions), the cut, B-roll recorded by broll-recorder, and both approved editing styles (Animated Board and Code Report) with the B-roll in.
2. Build a review skill that audits the finished work and reports problems with frame and timestamp.

The work lives in `camera_audit/full_suite/`. The script is `bulk_uploads_script_final.md`, also copied to `Desktop/Qdrant Videos/Bulk Uploads/bulk_uploads_script_all_layers.md`.

Precision problems found while building, to be caught automatically by the review skill:
- keyterms.py mapped the HNSW line to "Defer HNSW Indexing", where the right section is "Why Vector Type Matters".
- camera_plan.py read the script's notes as an Opening passage, printed 1:00 as "0:60", and planned FULL face inside look-aways.
- `[**B-ROLL: ...**]` with bold is not parsed by script_broll.py.
- My own Count section in the script was wrong (26 vs 23 calls, 99 vs 112 s face off) until checked by script.

**Why:** the styles are approved; what is left is making sure nothing small is wrong before a video ships.
**How to apply:** verify every number and claim with code before stating it. Cross-check the skills' outputs against each other: script against cut, B-roll against section, camera calls against look-aways.

Related: [[coding-channel-styles]], [[eye-contact-hide-face]], [[face-framing-annotations-feedback]], [[script-three-layers]].

**Status 2026-10-19 (end of day):** done. Both styles rebuilt with the 8 B-roll clips (broll2: readthrough, --zoom 1.4) via
`styles/broll_layer.py`, mastered to about -15 LUFS (`styles/master_audio.py`), and reviewed with [[video-review-skill]]: 0 to fix on
both. Finals and reviews are in `Desktop/Qdrant Videos/Bulk Uploads/full suite/` (with `review_before_after.jpg`). Left for John to
decide: the styles do not follow the script's FULL camera calls (Code Report 12/23, Animated Board 16/23); joke numbers on Code
Report memes; captions on the chin; a 4.3 s still batch board at 2:35; B-roll text at 23 px against a 24 px bar. Nothing pushed
to GitHub (video-review is local, like the engine).
