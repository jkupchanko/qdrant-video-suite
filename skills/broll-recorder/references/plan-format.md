# Shot plan format (`broll.py plan` writes it, `broll.py record` plays it)

```json
{
  "url": "https://qdrant.tech/documentation/concepts/indexing/",
  "match": "you can create a payload index before you upload",
  "section": { "index": 3, "tag": "H2", "text": "Payload Index", "top": 1880, "left": 268, "width": 700, "height": 900, "has_code": true },
  "match_score": 3.9,
  "style": "reveal",
  "duration": 6,
  "width": 1920, "height": 1080, "scale": 1.0, "light": false, "hide": [], "state": null, "channel": "chrome",
  "start_y": 1058,
  "steps": [
    { "t": 0.3, "move": [628, 648], "dur": 0.8 },
    { "t": 1.2, "scroll": 1578, "dur": 1.7 },
    { "t": 3.1, "hover": { "heading": "Payload Index" }, "dur": 0.8 },
    { "t": 4.0, "click": true },
    { "t": 4.5, "hover": { "heading": "Payload Index", "offset": [120, 260] }, "dur": 0.8 },
    { "t": 5.4, "scroll": 1700, "dur": 0.4 }
  ]
}
```

Every step has `t` (seconds from the start of the clip) and one action:

| key | value | effect |
|---|---|---|
| `scroll` | absolute page y | eased wheel-scroll from the current y to that y over `dur` |
| `move` | `[x, y]` viewport px | cursor glides there over `dur` |
| `hover` | `{"heading": "text"}` or `{"selector": "css"}`, optional `"offset": [dx, dy]` | cursor glides to that element (headings are matched by their first 40 characters) |
| `click` | `true` | click ripple at the cursor; add `"real_click": true` to actually click (navigates!) |
| `highlight` | `{"heading": "text", "height": 420, "color": "#DC244C"}` | red rounded box fades in around the section, from the heading down `height` px |

`start_y` is where the page sits before the recording begins (the jump happens before frame one).
`dur` defaults to 0.9 s. Steps run in time order; a step whose time has passed runs immediately.

Styles produced by `plan --style`:
- `reveal`: start half a screen above, scroll to put the heading at 28% of the viewport, hover, click, drift.
- `hover`: no reveal scroll; hover the heading, click, drift. For heroes and short pages.
- `highlight`: `reveal` plus the red box around the section.
- `readthrough`: steady 110 px/s scroll from half a screen above the section, no hover. For long articles.
