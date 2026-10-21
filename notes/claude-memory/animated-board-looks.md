---
name: animated-board-looks
description: 2026-10-18 John made the animated-board Bulk Uploads video a named style and asked for "new looks, same system" as the next options
metadata:
  type: project
---

On 2026-10-18 John said the animated-board example "can be a style of editing now". This is the progressive build board plus the face director, the no-dead-space camera, and the eye and sync checks. For "more options" he chose **new looks on the same system**, over upgrading the old styles, building styles for other formats, or running the style on another video.

Looks live in `camera_audit/animkit/themes.py`: brand (original), whiteboard (Excalifont, Excalidraw markers), paper (cream, Playfair serif), neon (glow on the board layer, Space Grotesk) and editor (Catppuccin Mocha, Fira Code at FONT_SCALE 0.8). Select one with `BOARD_THEME`. Boards render into `media_<look>`, and the composite writes `out/full_<look>.mp4`. 41 s samples of each go to him first (small amounts), and the ones he likes go to full length.

2026-10-19: he said the four looks are sub-styles of one style ("technically one style, four options") and asked for the differences on GitHub. They were pushed to jkupchanko/qdrant-video-suite in `styles/animated-board/` (grid of five looks at five moments, one frame each, a 41 s side-by-side clip, README). He then asked for 2 or 3 completely different styles from scratch, with real animation and imagery and nothing like the board. After an audit of 16 popular explainers (`camera_audit/paradigm_audit/report.md`) three 41 s samples were built: SIMULATION (Primer), CHARACTER WORLD (Kurzgesagt/TED-Ed) and ISOMETRIC MACHINE (Branch/Jared Owen), in `Desktop\Qdrant Videos\Bulk Uploads\new styles`. He rejected a text-only kinetic type attempt ("make sure it's not only text").

**Why:** he wants several finished options that all keep the rules he set (eyes, layouts, no dead space, sync).
**How to apply:** a new look is a themes.py entry plus a board re-render. Never fork the face director or the camera per look. Related: [[eye-contact-hide-face]], [[explanatory-animation-focus]], [[editing-styles-five]].
