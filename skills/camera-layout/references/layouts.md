# The five layouts, with proportions

## Framing the face (applies inside every layout)

Measure the face first (brow to chin = one unit, h), then build the crop around it. The same rule in a
full frame, an inset, a small window or a half panel; only the aspect changes.

- top: the top of the head (about 0.35 h above the face box) plus 0.25 h of headroom
- bottom: the chin plus 0.9 h, so the neck and the top of the chest are in and the shoulders read
- sides: at least 0.6 h of clear space left and right of the face, so a turn or a lean stays inside
- centre: the face sits dead on the vertical centre line, always. When the source is too tight for the
  clearances, the crop shrinks symmetrically around the face; it never slides sideways to fit. Vertically the
  face centre lands a little above the crop's middle so the eyes are near the upper third
- movement: on a recording, measure where the face goes through the whole clip and frame around that
  envelope, not one frame

Not every source has room for this. A close-up recorded too tight cannot be fixed in the crop; the tool
says so ("source too tight: N px below the chin") and the fix is at the camera. `scripts/frame_face.py`
applies the rule and writes the crops with a guide image.


Every camera decision in a script is one of these. Sizes are for a 1920x1080 frame; scale with the frame.

## full: talking head
The presenter fills the frame. Head and shoulders: top of the head just under the top edge (3-5% headroom),
chin above the lower third, eyes on the upper-third line. Centred, or a touch off-centre if a title or
graphic will share the frame. This is where opinions, questions, hooks, summaries and calls to action live.
In the corpus: 36% of all time, used by 29 of 32 videos, a typical run of about 20 s, the longest run about
50-70 s. The face comes back to full within about 40 s of leaving it in three videos out of four.

## half: presenter beside content
A full-height panel for the presenter on one side (35-45% of the width) and the content on the other. The
presenter is framed as in full, just narrower. Use it when the person and the thing need equal weight for a
stretch: a comparison, a conversation, slides the presenter is pointing at. Rare in the corpus (one video,
Google Cloud Tech, lives in it); it reads as "presentation", so do not use it for code.

## inset: large picture-in-picture
A window 25-32% of the width (round or rounded rectangle), 16:9 or circle, 2-3% in from a corner. Face
framed as in full but tighter: head and the top of the shoulders. This is the "I am walking you through
this" layout: Tech With Tim, corbin and NetworkChuck sit here for whole sections at a time. Used by 12 of 32
videos; in tutorial-length videos it runs about 15-25 s between changes, in long courses it can sit for
minutes. Its weakness is that it covers a lot of screen: hide it (none) whenever the viewer has to read what
is under it.

## small: small picture-in-picture
A window 16-22% of the width in a corner, same framing as inset. Presence without weight: the viewer knows
someone is there while they read the screen. Used by 16 of 32 videos, typical run about 15 s, rarely more
than 25 s before either the face returns to full or the window goes away. Bottom-right and top-left are the
common corners (10 and 9 videos); pick the corner that does not cover the terminal, the results or the
cursor's working area, and keep the same corner through a section.

## none: screen only
No presenter. The viewer reads code, results, a diagram, an article, a product. 31% of all time; median
stretch 10 s, three quarters under 22 s, almost never over 50 s without the face coming back in some size.
This is also the right layout for a B-roll insert and for any moment the face would cover something that
must be read.

## What the corpus does with them
- Two families. "Cut" videos (Sajjaad Khader, ForrestKnight, NetworkChuck, Aaron Jack, Aishwarya): mostly
  full, cutting to screen and back, 3-4.5 changes a minute. "Window" videos (Tech With Tim, corbin,
  pixegami): one window over the screen nearly all the time, under 1 change a minute. The cut family is the
  more watched one in this corpus and is what the Qdrant house style is closer to.
- Three layouts per video is the median; 17 of 32 use three or more. Two is the floor for anything over
  three minutes.
- Moves between full and none make up 45% of all changes; full and small another 19%. Inset is entered from
  full and left to full. Half is entered from full.
- Opening: 16 videos open on the face, 14 on the screen. The opening shot holds about 20 s before the first
  change. Closing: 14 on the face, 10 on the screen.
- Changes are front-loaded: 40% of them fall in the first third of a video.
