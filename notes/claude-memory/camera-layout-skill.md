---
name: camera-layout-skill
description: "The camera-layout skill (third piece of John's video suite): measured camera habits from a 32-video audit and a script-to-camera planner; where the corpus and tooling live"
metadata:
  node_type: memory
  type: project
  originSessionId: 39bc7a71-3509-46be-83a4-5d1a21b62df7
  modified: 2026-10-14T16:37:25.238Z
---

Built 2026-10-14 at `~/.claude/skills/camera-layout` and in the suite repo under `skills/camera-layout`. John asked for it after the B-roll skill: audit how popular AI/dev videos place the presenter (full, half, inset, small, none), when they switch, and turn that into a plan for any script, with variety (not the same small window 100 times).

- Corpus and working files: `C:\Users\ADMIN\camera_audit\` (videos/ at 360p via yt-dlp with `--js-runtimes node`, audio/ for 16 transcribed, audit/ jsons, cues/, tendencies.md). The original 60-video review behind the script library was done outside Claude Code, so the list was not recoverable; this corpus is my own 32 (9 from earlier sessions + YouTube search for top AI/dev videos).
- Key numbers: full 36% / none 31% / small 17% / inset 14% / half 2% of time; median 2.4 changes/min; opening holds ~20 s; face back to full within 40 s (75th pct); no-face stretches median 10 s, rarely >50 s; 3 layouts per video median; two families: cut (face<->screen, 3-4/min) vs window (one inset, <1/min).
- Classifier caveats: Haar faces + flood-fill body test; tiny PiPs (<5% width) undercounted; half splits rare, thin data.
- Planner: `scripts/camera_plan.py SCRIPT.md` parses the script library format (sections with times, [**Camera:**/**Show:**] directions apply to all paragraphs since the previous direction) and reports conflicts with the script's own Camera notes; writer's choice wins unless it breaks a habit.

**How to apply:** when John asks about camera placement, PiP size, or wants a camera plan for a script, use this skill; re-run `tendencies.py` if he adds videos to the corpus. Related: [[broll-recorder-skill]], [[video-suite-repo]], [[motion-design-feedback]].
