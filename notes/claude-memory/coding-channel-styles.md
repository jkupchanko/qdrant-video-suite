---
name: coding-channel-styles
description: 2026-10-19 John rejected the metaphor styles (simulation, character world, isometric) as goofy; new styles must copy what the top coding channels actually show
metadata:
  type: feedback
---

On 2026-10-19 John said the Simulation, Character World and Isometric Machine styles "kind of look goofy" and "don't really match". His direction: look at the top coding videos, see what animations they use, "stick around them" and "not reinvent the wheel".

An audit of 16 coding videos (`camera_audit/coding_audit/report.md`) found two serious patterns. The first is the editor itself (Nick Chapsas, CodeAesthetic, NeetCode): code typed, the line selected and zoomed, hover docs, a terminal, and a round face cam. The second is the line-icon architecture diagram (ByteByteGo, Nana). Both were built as `style_ide.py` and `style_sysdesign.py`, with 41 s samples in `Desktop\Qdrant Videos\Bulk Uploads\coding styles`.

Same day he called both "a little too basic". Copying the plain references one-to-one was the mistake. The answer was `style_launch.py` (LAUNCH): the same real-code and real-component vocabulary with launch-video polish (3D code window, beams, glass cards, count-ups, a 3D HNSW graph, gauges), a different element and transition per section, and changing face layouts. The 41 s sample is in the coding styles folder.

Then he asked for "something completely new" again. A concept board of six stills (hologram stage, terminal, blueprint, Swiss data-ink, particle field, newsroom) let him pick: A, B, C and D/F, plus "find more that are different" (a second board followed: split-flap, metro map, risograph, notebook, mission control, paper diorama). Five were built as 41 s samples in `Desktop\Qdrant Videos\Bulk Uploads\new directions` (style_holo, style_term, style_blueprint, style_swiss, style_news). **Lesson:** after repeated rejections, show cheap concept stills and let him choose before building motion.

His feedback on those five: "need to moving around more, give me something else". The answer was FLY-THROUGH (style_fly.py): a continuous 3D camera through a world of panels, with streaking particles and a face card that swings with the moves. **Lesson:** he wants constant motion: the camera itself should move, not only elements popping in.

He rejected Fly-through too ("something else, don't like it") and sent a reference: Fireship's "vibe coding mind virus" (https://www.youtube.com/watch?v=Tw18-4U7mts). Built `style_report.py` (CODE REPORT): real media only (Qdrant docs screenshots with a synced red highlight, stock photos with heavy captions, memes, logos, red option cards), a cut every ~2 s, face between inserts. Sample: Desktop\Qdrant Videos\Bulk Uploads\code report. **Lesson:** when he rejects repeatedly, ask for a reference video and copy it. Real imagery beats generated graphics for him.

He approved Code Report as an editing option (pushed to GitHub, styles/code-report, full 3:36 video delivered), then sent a second reference: NetworkChuck's 'You've Been Using AI the Hard Way' (https://www.youtube.com/watch?v=MsQACpcuTkU&t=523s). Built style_chuck.py: real docs browser scrolling with yellow marker annotations, terminal, gold-framed face cam, marker sketches on the wall in talk shots. 41 s sample in Desktop\Qdrant Videos\Bulk Uploads\networkchuck style.

**Why:** his audience is developers; characters and invented worlds read as childish next to Qdrant's technical content.
**How to apply:** copy the vocabulary, not the plainness: raise the finish above the reference and follow [[motion-design-feedback]] (varied moves, a different element per section, exact layout). For new styles, copy a real top coding channel's on-screen vocabulary (real code, real components, real output). No mascots, creatures or metaphor worlds unless he asks. Related: [[animated-board-looks]], [[eye-contact-hide-face]], [[editing-styles-five]].
