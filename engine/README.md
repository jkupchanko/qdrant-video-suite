# Rendering engine (from the editing PC)

The shared engine (`engine.py`) and every editing style (`style_*.py`), with the helpers the video builder calls
(`broll_layer.py`, `master_audio.py`, `check_eyes.py`, `check_sync.py`). The listed-sections style is `style_list.py`.

Paths are written for the editing PC (`C:\Users\ADMIN\camera_audit\...`): to run elsewhere, put this folder at
`camera_audit/styles` under the same user, or change `FONTS`, `ASSETS` and `STYLES` at the top of the scripts.
Fonts (`camera_audit/fonts`, 68 MB) are not here: Mona Sans and Geist Mono are free (SIL OFL) from
github.com/github/mona-sans and github.com/vercel/geist-font; the brand-consistency skill carries the ones the name card uses.
