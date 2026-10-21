---
name: editing-styles-five
description: "Eleven channel-copied editing styles (3Blue1Brown, Kurzgesagt, Species, Cleo Abram, CGP Grey, Karpathy, Jeff Su, IBM lightboard, CodeAesthetic, NetworkChuck, Fireship, Vox) on a shared engine in C:\\Users\\ADMIN\\camera_audit\\styles, built 2026-10-15/16; local only"
metadata:
  node_type: memory
  type: project
  originSessionId: 39bc7a71-3509-46be-83a4-5d1a21b62df7
  modified: 2026-10-16T02:07:24.129Z
---

On 2026-10-15 John asked for completely different editing styles copied one-to-one from the most popular AI videos on YouTube, with a gap analysis and packaging so anyone can hand over a cut + script. First five (MATH, CARTOON, DOCUMENTARY, STUDIO, FAST) he called "all relatively pretty good" and asked for more, a wider audit of the most popular creators, and a look at HeyGen. Second round added BRIGHT (Cleo Abram), STICK (CGP Grey), SKETCH (Karpathy/Excalidraw), LIGHTBOARD (IBM, via a rembg presenter matte), CODE (CodeAesthetic), ANNOTATED (NetworkChuck, glitch cuts), EDITORIAL (Vox). Third round ("Do more.", 2026-10-16) added FLOWCHART (StatQuest), WORDS (H3Vtux), NOTES (Tina Huang), GLOSSY (Dan Martell), ARCHIVE (ColdFusion), CAPTIONS (Hormozi/Gadzhi word-by-word captions), WHITEBOARD (After Skool). YouTube's sign-in wall stopped further downloads mid-sweep (yt-dlp needs browser cookies); the last five references are documented from known formats, not frame audits. All in C:\Users\ADMIN\camera_audit\styles (engine.py, beats.py, style_*.py, matte.py, README.md with the 45-channel audit table and pace numbers, CREDITS.md); copies in ~/.claude/skills/editing-style/scripts/styles (local skill, not on GitHub). Outputs: styles\out and Desktop\Qdrant Videos\Bulk Uploads (style_1..12 *_720.mp4, all_styles_sheet.png). Reference corpus: camera_audit\popular (search_merged.txt ranking, videos/, sheets/).

**Why:** he wants to see which look suits Qdrant videos and where automated quality falls short before choosing; he likes seeing many options.
**How to apply:** pick a style by name/channel/adjective, read the recipe at the top of the style file, write plan() for the new video from its cue sheet; run stills before a full render; every render must report zero face frames in look-aways. Not copyable: crew documentaries (Veritasium, Bloomberg), 3D (Primer, Branch), hand animation (Alan Becker, TED-Ed). HeyGen needs an account he must create; its digital twin is the feature relevant to the eye-contact rule. Related: [[animation-pacing-feedback]], [[motion-design-feedback]], [[editing-skill]].
