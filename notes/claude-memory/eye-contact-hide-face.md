---
name: eye-contact-hide-face
description: "John's hard rule: whenever his eyes are not on the lens (reading to the side, any glance), his face must not be on screen; show only the animation"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 39bc7a71-3509-46be-83a4-5d1a21b62df7
  modified: 2026-10-16T18:12:46.152Z
---

On 2026-10-16 John flagged the full animated Bulk Uploads video at 0:53. His face was in the card while he read to the side. His words: if my eye contact is not directly in the camera, "completely remove that and only show the animations", and he asked for it to be fixed in the skill. It applies to every glance and every style; demos are the only exception.

**Why:** the old gaze.py took the median of the take as "on the lens". John reads a screen beside the camera about 40% of the time, so the median sat between the lens and the script, and whole reading stretches passed as eye contact.

**How to apply:**
- Run `~/.claude/skills/editing/scripts/gaze.py CUT.mp4 --out gaze.json --lookaways lookaways.json` on the finished cut. It is now cluster-based: a Gaussian mixture on iris h and head yaw, merged into gaze targets, with the heaviest target as the lens. Short runs count when they are clear glances.
- The engine's Renderer applies `protect_eyes` to every style automatically: the card slides out early and the board recentres.
- Finish with `check_eyes.py OUT.mp4 gaze.json lookaways.json`, which checks the face in every output frame. A render is done only when it reports 0.
- Vertical iris position is unreliable for him (it moves with the eyelids), so it is only an outlier check.

Follow-up the same day: he liked that he now only ever sees himself looking straight at the lens, and asked for the face to come back more whenever he IS looking: "small sections, half sections, corner sections" to drive attention, with consistency. Built as `engine.invite_face`: a corner window (half the side card's size, same border), placed by reading the board's frames so it never covers content, sticky corner (bottom right on Bulk Uploads), at least 2 s, and it grows into the side card. Keep the layout set small: full face, side card, corner window.

Then (same day) he asked for more variety: half-screen face, full-screen face for 5 to 10 s, "more movement than not", because a viewer gets lost while he explains. Built as `engine.direct_face`, which replaces invite_face in style_full. It uses layouts half / card / full / corner / none, changed every ~6.5 s within on-lens stretches. Feasibility is read from the board's frames. Full face is placed where the board changes under 1.5% of the frame (he accepted missing a beat: "I don't care really"). Every change is a 0.5 s morph of the face window and the board together.

Then: "no dead space ... make sure all space is always taken up", after seeing a card-layout board shown with a corner window and the left side empty. The fix is a content-following camera in direct_face: the content is fitted into the free region of each layout (fit_place / free_regions) with a 0.75 s look-ahead and slow zoom-in, up to 2x. Boards are rendered at 4K (-qk) for that.

He also caught the voice drifting from the lips toward the end. The cause was the cut, stitched from per-piece AAC files with `-c copy`: about 1.4 s over 53 joins. The same drift put look-aways on screen. The fix is `editing/scripts/assemble.py`, which is frame- and sample-exact. Every render must pass `check_sync.py` as well as `check_eyes.py`. Older deliverables built on the drifted cut: bulk_uploads_full_edit, full_styled, full_v3. A corrected face-only cut was delivered as bulk_uploads_full_edit_synced.mp4.

Related: [[editing-skill]], [[explanatory-animation-focus]], [[camera-code-small-window]].
