---
name: broll-keyword-trigger
description: "John's rule that the word \"B-roll\" is the trigger for the broll-recorder skill across the whole video suite"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 39bc7a71-3509-46be-83a4-5d1a21b62df7
  modified: 2026-10-13T22:11:58.301Z
---

When John (or his script-writing skill, or any text he hands over) says "B-roll" / "b roll" / "broll" / a `[B-ROLL: ...]` marker, that means: use the broll-recorder skill and record the clip. The only exception is when he is merely explaining what B-roll is.

**Why:** the suite has several skills (script writer, B-roll recorder, more coming) and he wants one unambiguous keyword that routes work to this one, so the script writer's output can hand off without him re-asking.
**How to apply:** on hearing "B-roll" in a request, load `~/.claude/skills/broll-recorder` and start the shot (or the script runner for marked scripts) rather than asking what he means. Related: [[broll-recorder-skill]], [[video-suite-repo]].
