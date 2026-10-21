---
name: video-suite-repo
description: "John's private GitHub repo for the video skill suite (qdrant-video-suite) and the plan to fold the script library repo into it"
metadata:
  node_type: memory
  type: reference
  originSessionId: 39bc7a71-3509-46be-83a4-5d1a21b62df7
  modified: 2026-10-13T22:18:13.857Z
---

Private repo: https://github.com/jkupchanko/qdrant-video-suite (GitHub user `jkupchanko`, created 2026-10-13). Local clone: `C:\Users\ADMIN\qdrant-video-suite`. Layout: `README.md` (suite overview), `skills/broll-recorder/` (the skill, copied from `~/.claude/skills/broll-recorder`), `demos/broll_skill_pitch.mp4`.

`skills/technical-video-script-library/` is a git SUBTREE of `jkupchanko/technical-video-script-library` (added 2026-10-13, squashed). That repo is still being pushed to separately; sync with `git subtree pull --prefix skills/technical-video-script-library <url> main --squash` and push back with `git subtree push`. Order in the suite README: 1 script writing, 2 B-roll, 3 edit. The script skill does not yet emit `[B-ROLL: ...]` markers; that is the planned hand-off.

2026-10-20 (commit 8b1e6d3, pushed at John's ask "push a little bit of this... really good imagery"): `skills/video-review/` (README: a real example image per check), `skills/video-builder/` (README: build 1-3 table), `styles/listed-sections/` (peer frames + device sheet + style_list.py/broll_layer.py), editing and broll-recorder synced; suite README's Final review card now live plus a Build/Editing-styles row. `styles/` (added 2026-10-19) holds the finished editing options: `styles/README.md` (index), `animated-board/` (five looks, gallery) and `code-report/` (Fireship copy: README, device frames, 41 s sample, style_report.py + capture_docs.py). The shared engine (engine.py etc.) stays in the local editing-style skill unless John asks to push it.

**How to apply:** when the skill under `~/.claude/skills/broll-recorder` changes, copy it into the clone and push; don't let the two drift. John asked (2026-10-13) to stop repeating "no After Effects" in docs and slates: say "nothing to install" instead. Related: [[broll-recorder-skill]].
