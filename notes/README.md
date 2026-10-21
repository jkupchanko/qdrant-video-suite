# Notes: picking the work up on another machine

- `STATUS_2026-10-20.md`: where everything stood when the desktop went to sleep, and the next steps.
- `claude-memory/`: Claude's memory for this project (John's rules, each skill's state, the feedback). On a new machine,
  copy these files into `~/.claude/projects/<project>/memory/` (or just point Claude at this folder) so a new session
  knows everything this one did.
- The skills are in `skills/`; copy a folder into `~/.claude/skills/` to use it. The rendering engine
  (`camera_audit/styles/engine.py`), the raw takes and the builds stay on the desktop PC.
