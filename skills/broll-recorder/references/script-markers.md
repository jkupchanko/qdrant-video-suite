# Marking B-roll in a script

Put a marker right after the sentence it illustrates. The recorder reads the script, records every marker, and
returns a shot list. Any of these forms work (case does not matter):

```
JOHN: Qdrant doesn't just store vectors. It handles payloads and indexes too.
[B-ROLL: https://qdrant.tech/documentation/concepts/payload/]

JOHN: You can create the payload index before you upload the data.
[B-ROLL: https://qdrant.tech/documentation/concepts/indexing/ | create the payload index before you upload | 6s]

JOHN: And there is a free tier.
[B-ROLL: https://qdrant.tech/pricing/ | section: Free Tier | hover | 5s | name: free_tier]

<!-- b-roll: https://qdrant.tech/ | high performance vector search at scale | readthrough | 8s -->
```

Fields after the URL, in any order, separated by `|`:

| field | example | meaning |
|---|---|---|
| spoken line | `create the payload index before you upload` | what the page must prove; picks the section. If omitted, the sentence before the marker is used. |
| duration | `6s` or `6` | clip length (default 6 s; 4-8 is the useful range) |
| style | `reveal`, `hover`, `highlight`, `readthrough`, `look` | how the shot moves (see plan-format.md). Default: `reveal`, or `readthrough` for a homepage. `look` = scroll, stop, push in, circle the spot, hold, swoop out (its duration is computed; ~9 s) |
| `section: ...` | `section: Free Tier` | pin a heading when the spoken line is vague |
| `name: ...` | `name: free_tier` | file name for the clip; default comes from the line |

Labels accepted: `B-ROLL`, `BROLL`, `B ROLL`, `CUTAWAY`, `SCREEN`. Wrappers accepted: `[...]`, `{{...}}`,
`<!-- ... -->`, `**B-roll:** URL` on its own line, or `B-roll: URL` at the start of a line.

Then:

```bash
python <skill>/scripts/script_broll.py script.md --out ./broll --dry-run     # see the shot list first
python <skill>/scripts/script_broll.py script.md --out ./broll              # record everything
python <skill>/scripts/script_broll.py script.md --out ./broll --compose fullscreen-pip --presenter talk.mp4
```

Outputs: one `<name>.mp4` + sheet + manifest per marker, `shotlist.md` (a table: script line, what is said, page,
section matched, clip, caption, notes), `shotlist.json`, and `script.annotated.md` with each marker followed by
its clip's file name, so the editor can read the script and the clips side by side.

Pages behind a login are skipped here (no session in the recorder); mark them `[B-ROLL: URL | ... | login]` and
record those with the real-Chrome method in SKILL.md.
