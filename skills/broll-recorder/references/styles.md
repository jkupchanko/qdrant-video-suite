# B-roll styles seen in creator videos, and how to reproduce each

Studied on 2026-10-05 and 2026-10-13 from four reference videos plus John's own Qdrant edits. Use this to pick a
treatment that matches the video you are cutting into, then record with the matching `broll.py --style` and bake
it with `scripts/compose.py --style` (a finished mp4 section or a transparent .mov overlay that works in any
editor). `scripts/ae_insert.jsx` builds the same looks as live layers for people who do use After Effects.

| Treatment | `compose.py --style` | Output without a presenter video | Output with `--presenter` |
|---|---|---|---|
| 1. full-screen + PiP + caption | `fullscreen-pip` | (needs the presenter) | finished section, their audio |
| 2. evidence card | `evidence-card` | transparent overlay .mov | finished section |
| 3. full-screen push | `fullscreen` | clip over dark background | finished section |
| 6. floating window | `window` | transparent overlay .mov | finished section |
| 4, 5. dashboard PiP, monitor mockup | `fullscreen-pip` / editor | | |

## Contents
1. Full-screen site + PiP + caption (AI Master, "Ultimate Claude Code Tutorial" 0:41-0:44)
2. Evidence card over the shoulder (Sajjaad Khader, "How To Learn To Code In 2026" 0:05-0:08)
3. Full-screen capture with slow push (ForrestKnight)
4. Dashboard recording + framed PiP (John, "Bulk Uploads" 0:03-0:07)
5. Monitor mockup (John, "Bulk Uploads" 0:10-0:16)
6. Floating 3D window (Apple keynote / Bricks-style)
7. Timing, motion and cursor rules that hold across all of them
8. Choosing a style from the page kind

## 1. Full-screen site + PiP + caption
What it looks like: the web page fills the frame and scrolls slowly; the presenter sits in a small rounded
rectangle bottom-right (about 22% of frame width) with a thin white border; the spoken words appear as a dark
caption pill at the bottom centre. The cursor is visible and moves with purpose (to a heading, a plan card, a
button), never idle in the middle.
Record with: `--style reveal` (default). 5-8 s. Dark scheme if the video is dark.
Insert: `ae_insert.jsx` with `STYLE = "fullscreen-pip"`. Push 1.00 -> 1.05 over the shot. Slide in from the right
on a whoosh, cut out or slide left.
Use when: the line names a product, page, feature or plan ("check your plan", "the payload docs say").

## 2. Evidence card over the shoulder
What it looks like: a cropped still or short clip of the proof (a diploma, a pricing table, a JSON payload) floats
top-left of the presenter, tilted 5-8 degrees, with a drop shadow; a red rounded box draws itself around the
key lines; big title text sits lower in the frame (name, number, claim). The presenter stays full-frame.
Record with: `--style highlight --duration 4` so the section gets its red box in the recording itself, or record
plain and draw the box in After Effects (cleaner, animatable).
Insert: `STYLE = "evidence-card"`: scale 0.45-0.55, position left third, rotation -6, slide in from top-left over
0.5 s with a whoosh, gentle float (6 px sine). Keep it under 4 s; it is punctuation, not a scene.
Use when: the line makes a claim that one visual proves ("I'm a Georgia Tech grad", "Point 1 has a payload").

## 3. Full-screen capture with slow push
What it looks like: clean page or app capture, no presenter, 1.0 -> 1.06 scale push over 4-6 s, thin caption bar
at the bottom. Cuts are hard; no slide. Light pages are fine here because the whole frame is the page.
Record with: `--style readthrough` for an article (steady 110 px/s scroll) or `--style hover` for a feature.
Insert: `STYLE = "fullscreen"`.
Use when: the presenter is already a PiP elsewhere, or the clip is pure demonstration.

## 4. Dashboard recording + framed PiP
What it looks like (John's own edit): a real app recording (Qdrant Cloud) full-screen, presenter PiP top-right
inside a thin red-bordered frame, cursor clicking through tabs. Audio continues under it.
Record with: a real screen recording (OBS) when the page needs a login; `broll.py` can only record pages it can
open, or pages you give it a Playwright storage state for (`--state`).
Insert: `STYLE = "fullscreen-pip"` with `PIP_CORNER = "top-right"` and `PIP_BORDER = [0.86, 0.14, 0.3]`.

## 5. Monitor mockup
What it looks like: the recording sits inside a monitor PNG, presenter visible behind it, cursor visible.
Insert: in After Effects, parent the clip to the monitor image, scale to the screen area, add a 10% screen
reflection gradient. `broll.py` only supplies the clip.
Use when: the video already uses the mockup elsewhere; keep it consistent.

## 6. Floating 3D window
What it looks like: the clip inside browser chrome (title bar, traffic lights, URL pill), floating as a 3D card
with a soft shadow while the camera drifts; the page scrolls inside. Often two or three windows at different
depths with depth-of-field blur.
Record with: `--style reveal` at `--scale 1` (chrome is added in After Effects, not in the browser).
Insert: a window precomp (1440x944: 44 px bar + page) as a 3D layer, rotate Y 10-20 degrees, camera with DOF.
Use when: the whole edit is the Apple/keynote look.

## 6b. Clean card with pushes (Anthropic, "What is Claude Code?")
What it looks like: a warm off-white background (#F3F0E8), the page or app in a rounded card with a soft shadow
and generous margins, no browser chrome. Every shot starts wide, then a slow eased push (1.3-1.6x) toward the thing
being talked about, holds, and either cuts back to the presenter or eases to the next region. Nothing moves
unless the narration points at something. Hard cuts, no slides. Title cards share the cream and use a big serif.
Record with: `--light` (the recorder flips the site's own theme switch if it has one) and `--style hover` or
`reveal`; keep the page's own scroll small so the push is the motion.
Compose with: `compose.py --style clean --focus "T:cx,cy,zoom:speed"` per move (output-frame coordinates; find
them on the composed wide frame, e.g. the code block centre). Speeds: `slow` (1.4 s, the default push in),
`normal` (0.7), `fast` (0.3), `snap` (0.12). `--focus "T:out"` returns to the full view in ONE swoop (fast by
default): never creep back, and never chain small drifts; between moves the view holds dead still.
Example: `--focus "1.5:900,470,1.55:slow" --focus "4.0:1300,700,1.55:fast" --focus "6.0:out"`.
Beats (same thing, one string): `--beats "zoom@1.5=900,470,1.55:slow circle@3.2=905,470,150:until=5.9 out@6.0:slow"`.
A rectangle with a small even margin on the real element beats a circle (a circle never fits a block of text). Marks ride with the zoom, so give them pre-zoom (wide-frame) coordinates: `circle@T=cx,cy,r`, `box@T=x,y,w,h`,
`underline@T=x,y,w`; `:until=T2` fades the mark out before the swoop. Colour via `--mark-color` (house red #DC244C,
or black when red clashes). Marks pop on in 0.35 s with a touch of overshoot, like a hand-drawn stroke.
The stop-and-look shot (`shot.py look`) is this grammar with the timing baked in: scroll to the section, a beat
of stillness, push in (slow by default), mark the spot 0.4 s after the push lands, hold (2.5 s default, `--hold`),
then swoop out at the SAME speed the push used. Stillness between moves is what makes the move read.
Use when: the edit is bright and calm; explainer videos; anything that should feel like a product film.

## 6c. Code typing itself (IDE look, no IDE needed)
What it looks like: a dark editor window (traffic lights, file tab, line numbers, syntax colours) in the same
off-white card; the snippet types in at a natural uneven pace with a blinking cursor, pauses at line ends, the
view scrolls to follow; optionally a terminal strip "runs" the file at the end; then a push into the lines that
matter. Theme `qdrant` uses the brand dark (#0B0F19) and keeps the brand colours out of the UI chrome; `dark` is
VS Code's; `light` for bright edits.
Make with: `code_broll.py snippet.py --out clip.mp4 --card --theme qdrant --cps 30 --focus-lines 13-19
--run "python upload.py" --run-output "Uploaded 1,000,000 points in 41s"`. Three reveal modes: `--reveal typed` (default, types in), `--reveal static` (the finished snippet with a cursor
blinking at the end of the last line, as if waiting for you; `--cursor-line N` moves it), `--reveal all`
(finished, no cursor). Static/all take `--duration`. The push uses `--zoom-speed slow|normal|fast|snap`, and
`--zoom-out` swoops back to the full view in one move before the end. The font shrinks automatically so the
whole snippet fits without scrolling. Language is taken from the extension
(`--lang` to override). Keep snippets to 8-20 lines; longer ones scroll and the viewer loses the line.
Use when: the narration says "here's the code", names a parameter, or walks through a call.

## 6d. House colours for all of the above
Background: rgb(245,244,240) (`#F5F4F0`), chosen by John to match Anthropic's off-white; never pure white.
Page/editor stays Qdrant dark (#0B0F19) inside the card; no red or blue washes in backgrounds. Qdrant red is
reserved for small accents (a highlight box, a PiP border) when the edit already uses it.

## 7. Timing, motion and cursor rules
- 4-8 s per clip. Under 3 s reads as a flash; over 8 s the viewer stops reading the page.
- Start the recording slightly above the target section (about half a screen) so the scroll REVEALS the heading;
  landing cold on it feels like a screenshot.
- One scroll, one hover, one click per clip is plenty. Eased moves (slow-in, slow-out) at 0.8-1.8 s each.
- Cursor: always visible, moves toward the thing being talked about, parks on it. A click ripple reads as a
  click without actually navigating (the recorder fakes it unless `real_click` is set).
- Scrolling speed about 110-150 px/s for reading; the final drift scroll can be slower.
- Match the page scheme to the video: dark videos get dark pages (`--light` off), bright edits get light pages.
- No cookie banners, no chat widgets, no "Sign in" modals. The recorder strips consent banners; use `--hide`
  for anything else (`--hide ".intercom-launcher"`).
- Caption text is the spoken line, shortened to one clause, in the video's caption style.
- Whoosh on the slide-in; a soft click on the cursor click; keep levels around -16 dB under speech.

## 8. Choosing a style from the page kind
| Page kind | Default style | Notes |
|---|---|---|
| Documentation page | fullscreen-pip | hover the matched heading; if there is a code block, park the cursor on it |
| Article / blog post | fullscreen-pip or evidence-card | `--style highlight` when one paragraph is the point |
| Homepage / landing | floating-window or fullscreen | hero plus one scroll; logos row reads well |
| Dashboard (login) | fullscreen-pip, top-right PiP | needs OBS or a storage state |
| Pricing / plans | fullscreen-pip | hover the plan the line mentions |
