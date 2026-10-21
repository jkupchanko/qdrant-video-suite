---
name: brand-consistency-skill
description: "2026-10-20 brand-consistency skill (~/.claude/skills/brand-consistency): the Qdrant name lower third John asked for, the [**Lower third:**] script directive, the intake questions asked before any build"
metadata:
  node_type: memory
  type: project
  originSessionId: be8ef0fa-6d40-4f4e-90af-386ddb45c6e8
  modified: 2026-10-20T22:21:59.927Z
---

John (2026-10-20): Qdrant videos always show the presenter's name: "it slides in from the bottom left corner... holds a few
seconds... slides back". He showed an example: a white circle with the red Qdrant brandmark overlapping a red gradient bar,
name bold, title under it. His card: **John Kupchanko | Developer Relations Engineer**.

Built as `~/.claude/skills/brand-consistency/` (SKILL.md, scripts/lower_third.py, references/intake.md, assets: the brand's
Qdrant-Profile-Circular-Light.png cropped to its circle, never redrawn; Mona Sans + Geist Mono, OFL). Bar #DC244C into
#9E0D38 (gradient on the bar only), circle slides in 0.42 s, bar unrolls, words rise, holds 5 s, out in reverse.
Script directive `[**Lower third:** NAME | TITLE | 5 s]` after the line it comes in on; the engine draws it as an overlay
(`Renderer(..., overlays=)`). The suite README's "Qdrant brand consistency: Coming soon" card is this skill.

Intake (John: "before we actually start really building, we need to ask these questions... can you tell me what your
name is"): name, title, take, script, docs page, style. build.py exits 2 with the questions when the script has no name
card and no --name/--role. Related: [[video-builder-skill]], [[video-review-skill]], [[script-controls-video]].

**Why:** brand consistency across every Qdrant video; a guessed or misspelled name is the most visible mistake.
**How to apply:** every Qdrant build gets the name card; ask the intake questions first unless already answered (then say what is used).
