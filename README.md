# Qdrant video suite

Skills that take a technical video from idea to edit with less hand work. Each skill does one job, has its
own README, and can be used on its own or chained with the others.

| skill | job | status |
|---|---|---|
| [broll-recorder](skills/broll-recorder/) | say what to show, get finished B-roll (docs, articles, sites, code, click-through flows) in one consistent look | ready |
| technical-video-script-library | script styles, a selection guide and examples; writes the `[B-ROLL: ...]` markers the recorder reads | separate repo for now, folding in next |

## How the pieces connect

1. Write the script with the script library. Mark cutaways inline: `[B-ROLL: URL | the line you say there]`.
2. Run `skills/broll-recorder/scripts/script_broll.py SCRIPT.md --out clips/`. Every marker becomes a finished 1080p60 clip.
3. Drop the clips into the edit. Nothing to install beyond the recorder's one-time `setup.py`.

## Demo

`demos/broll_skill_pitch.mp4` (77 s): a login flow done by the tool, a docs zoom, an article slide, and code typing.

## Using a skill with Claude

Copy the skill folder into `~/.claude/skills/` (or point Claude Code at it) and ask in plain words, e.g.
"make B-roll for the payload docs where I say 'a payload is just JSON on the point'". The SKILL.md in each
folder is what Claude follows.
