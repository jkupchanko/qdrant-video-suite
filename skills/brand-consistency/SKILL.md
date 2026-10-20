---
name: brand-consistency
description: The Qdrant brand layer of the video suite. Every Qdrant video shows the presenter's name lower third (a white circle with the Qdrant brandmark and a red bar with the name and title, sliding in from the bottom left, holding about 5 s, sliding out), uses the brand's colours, Mona Sans and Geist Mono, the supplied logo files (never redrawn), and ends on the logo. Use it whenever a Qdrant video is built, styled or reviewed, whenever someone mentions a lower third, name card, name tag, presenter title, "our branding", "brand consistency", "make it look like Qdrant", or "Qdrant's essential layout", and before any build starts, to ask the presenter the intake questions (name, title) that only they can answer. The script controls it with [**Lower third:** NAME | TITLE | 5 s].
---

# Brand consistency

Qdrant videos look like each other on purpose: the presenter's name always comes up early, in the same card, the
colours and type are the brand's, and the logo is the supplied file. This skill holds those pieces for the video suite:
the lower third renderer, the rules, and the questions to ask before anything is built.

## Before building: ask

Some answers only the presenter has, and a build that guesses them puts a wrong name on screen. Ask these before the
first stage runs (the video builder stops with exit 2 and the same questions when the name is missing):

1. **Your name**, as it should read on the name card? (Spelling matters: the review checks the card against it.)
2. **Your title** under it? (e.g. Developer Relations Engineer)
3. **The raw take**: where is the recording?
4. **The script**: is there one in the three-layer form, or should one be written first (and shown, inline, before building)?
5. **The docs page** the video is about (the B-roll, figures and code come from it)?
6. **The style**: listed sections (default, builds itself), Code Report or Animated Board?

See `references/intake.md` for why each one matters and what happens with each answer.

## The script runs it

The video is controlled by the script. The name card is a script line like any other direction:

```
It's also handling indexing, payloads, and much more in the background.

[**Lower third:** John Kupchanko | Developer Relations Engineer | 5 s]
```

It comes in on the line above it (here 0:04.9, the moment the title card leaves) and holds for the given seconds. The
style moves it later if the eyes leave the lens inside its window, and shortens the hold (never under 3 s) so it is gone
before the next graphic. If the script has no directive, `build.py --name ... --role ...` adds one to a copy of the script
on the hook's second line; the original script is never edited.

## The lower third

`scripts/lower_third.py`: `LowerThird(name, title, t_in, hold=5.0)` is a function of time returning a 1920x1080 RGBA layer
(or None off screen); the shared engine lays it over every frame, whatever the shot (`Renderer(..., overlays=[...])`).

| part | value | from |
|---|---|---|
| circle | 150 px, white ring, the supplied `Qdrant-Profile-Circular-Light.png` cropped to its circle | qdrant-brand logos (never redrawn) |
| bar | 104 px tall, radius 14, Qdrant Red `#DC244C` into Primary Dark `#9E0D38`, left to right | brand palette (gradient on the bar only) |
| name | Mona Sans Bold 46 px, white | brand type (headings) |
| title | Mona Sans Regular 29 px, white | brand type (body) |
| place | left 64 px, bottom 40 px above the bottom letterbox bar | bottom left, clear of the face |
| motion | the circle slides in from the left (0.42 s), the bar unrolls out of it (0.38 s), the words rise (0.3 s); out in reverse (0.6 s) | John's example |

Preview without a build:

```bash
python ~/.claude/skills/brand-consistency/scripts/lower_third.py --name "John Kupchanko" --title "Developer Relations Engineer" --frame STILL.jpg --sheet sheet.png
python ~/.claude/skills/brand-consistency/scripts/lower_third.py --name "..." --title "..." --frame STILL.jpg --mp4 lower_third.mp4
```

## The rest of the brand, on screen

- Colours: background `#0B0F19`, cards `#111824`, text `#F0F3FA`, secondary `#656B7F`, border `#4E5366`, accent Qdrant Red
  `#DC244C`; Violet `#6047FF`, Teal `#009688` and Orange for groups and charts in the brand's order.
- Type: Mona Sans (headings SemiBold or Bold, body Regular), Geist Mono for code. Never gradient text.
- Logos: the supplied files only (`assets/`, from the qdrant-brand skill). The video ends on `Qdrant-Logo-Red-White`.
- Code: the brand's code snippet (surface card, header bar with the language tab, line numbers in `#656B7F`).

## The review checks it

`video-review` reads the name card from the pixels (OCR): a script without a lower third is a **fix**; a name card that
never appears, or reads differently from the script's spelling, or lacks the title is a **fix**; one held much shorter
than asked, not in the lower left, over a frame without the presenter, or after the first minute is a **check**.

Fonts: Mona Sans (GitHub) and Geist Mono (Vercel) are under the SIL Open Font License 1.1; see `assets/fonts/FONTS.md`.
