# Rendering engine (from the editing PC)

The shared engine (`engine.py`) and every editing style (`style_*.py`), with the helpers the video builder calls
(`broll_layer.py`, `master_audio.py`, `check_eyes.py`, `check_sync.py`). The listed-sections style is `style_list.py`.

The files the video builder runs (`engine.py`, `style_list.py`, the builder's `build.py`) find everything under
`~/camera_audit`: on another machine, link `~/camera_audit/styles` to this folder and `~/camera_audit/assets` to `assets/`,
and put the fonts in `~/camera_audit/fonts`. The other styles still name the editing PC (`C:\Users\ADMIN\camera_audit\...`).
Fonts (`camera_audit/fonts`, 68 MB) are not here: Mona Sans and Geist Mono are free (SIL OFL) from
github.com/github/mona-sans and github.com/vercel/geist-font; the brand-consistency skill carries the ones the name card uses.
