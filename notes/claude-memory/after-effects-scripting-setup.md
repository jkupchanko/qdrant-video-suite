---
name: after-effects-scripting-setup
description: "How Claude drives John's After Effects 2026 from scripts (second instance + user Startup agent), and the gotchas found on 2026-10-05"
metadata:
  node_type: memory
  type: project
  originSessionId: 39bc7a71-3509-46be-83a4-5d1a21b62df7
  modified: 2026-10-13T18:44:35.196Z
---

John (Qdrant DevRel) has Claude build motion graphics in After Effects 2026 (26.3) on this Windows PC. Working setup found on 2026-10-05:

- John keeps his own AE instance open; never run scripts in it. `AfterFX.exe -r script.jsx` is NOT delivered to a second instance, so instead: a user-level startup script in `%APPDATA%\Adobe\After Effects\26.3\Scripts\Startup\zz_claude_build_agent.jsx` runs only in an UNTITLED instance launched with `AfterFX.exe -m`, and polls an inbox folder (scratchpad `ae_agent/inbox/*.jsx`) every 1.5 s, running each file once via `$.evalFile`. Remove the startup script and `enabled.flag` when done.
- "Allow Scripts to Write Files and Access Network" is OFF, so scripts cannot write files or `system.callSystem`. Logs go into project folder-item names ("LOG ..."/"ERR ...") read back from the saved .aep bytes; outputs are project saves and render-queue renders.
- Rendering to an existing output path stalled AE on a dialog: always render to a fresh file name. The output .mp4 appears as a 0-byte file before the mux finishes, so wait for a stable non-zero size (3 checks, 10 s apart) before copying it anywhere. Draft renders: `comp.resolutionFactor=[2,2]` + "Current Settings"; finals: "Best Settings"; output module "H.264 - Match Render Settings - 15 Mbps".
- In shape groups, adding fill/stroke invalidates earlier shape references (re-fetch by `propertyIndex`); groups render first-on-top, so create fills before tracks.
- Reusable helper library: scratchpad `ae_agent/lib/ae_lib.jsx` (windows, 3D cards, camera chains, pills, typewriter, shapes, trim draw-on, popIn/punch/slam/shake, render). Style scripts in `ae_agent/staged/`.

- Other tools in the scratchpad (2026-10-13): `record_broll.py` records a real site scrolling with a gliding cursor and click ripple via Playwright (Chrome channel, 1920x1080, consent banners stripped; needs imageio's ffmpeg copied to `%LOCALAPPDATA%\ms-playwright\ffmpeg-1011\ffmpeg-win64.exe`); `gaze_audit2.py` (Haar + iris centroid + silence) flags off-camera frames per cut and draws join strips; `match_cut.py` picks the best-matching cut frames inside each pause; `full_audit.py` runs the whole chain over the entire edit. John wants his own B-roll recorded from the real sites he mentions (like the Claude Code tutorial at 0:41: site full-screen, speaker as a small PiP, caption pill).
- John's preferences (corrected twice on 2026-10-05): his talking head must be MIRRORED (flipped horizontally) and levelled by the ~3 degree camera roll; the Zoom name tag cropped; he wants his head large on screen. Of the style explorations he only liked the data-viz "Infographic" direction, pushed toward the Apple/Bricks 3D glass-card look with a gliding camera.

**Why:** avoids touching John's open project and gives a repeatable channel despite the file-write preference being off.
**How to apply:** reuse the agent + lib instead of re-discovering; check `Get-Process AfterFX` first and never Stop-Process John's instance (his has the project path in its window title).
