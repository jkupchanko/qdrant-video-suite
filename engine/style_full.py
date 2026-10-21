"""ANIMATED BOARDS, full video: the boards from animkit/full_bulk.py over the v2 cut of Bulk Uploads.

Face plan: full frame at the open and between sections; in a card on the left while a board builds beside
it; off screen for full-width boards. SHOTS is the wish; E.protect_eyes then takes the face off wherever
lookaways_v2.json (gaze.py run on the cut) says the eyes are off the lens, sliding the card out a moment
early and centring the board while it is gone.
Transitions (0.5 s): the face shrinks into its card and grows back out of it; pushes into full boards and
chapter cards; the card slides in when a board makes room, and slides out before a look-away.

  python style_full.py                  render 0 to the end
  python style_full.py 30 60            render a range
  python style_full.py stills 1 2 3     contact sheet
"""
import os, sys
from PIL import Image
import engine as E
sys.path.insert(0, r"C:\Users\ADMIN\camera_audit\animkit"); from themes import THEMES
THEME = os.environ.get("BOARD_THEME", "brand"); LOOK = THEMES[THEME]           # a look: same boards and face direction, another treatment
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\full_animated.mp4" if THEME == "brand" else rf"C:\Users\ADMIN\camera_audit\styles\out\full_{THEME}.mp4"
BG = LOOK["bg"]
import broll_layer as BL
BROLL = os.environ.get("BROLL") == "1"                                          # the script's B-roll cut in (broll_layer.py)
if BROLL: OUT = OUT.replace(".mp4", "_broll.mp4")
if LOOK["fx"] == "glow": E.BOARD_FX = E.glow
D = r"C:\Users\ADMIN\camera_audit\edit\full_edit"
MEDIA = r"C:\Users\ADMIN\camera_audit\animkit\media\videos\full_bulk" if THEME == "brand" else rf"C:\Users\ADMIN\camera_audit\animkit\media_{THEME}\videos\full_bulk"
QUALITY = os.environ.get("BOARD_Q", "2160p30")     # boards at 4K: layouts enlarge them to fill the space the face leaves
SC = {"Intro": 0.0, "Opt1": 35.85, "Opt2": 54.55, "Opt3": 76.2, "Opt4": 104.95, "Batch": 134.55, "Workers": 161.0, "Shards": 181.25, "Wrap": 200.25}
CARD = ("card", (90, 180, 620, 720), 16); BORDER = LOOK["border"]
SHOTS = [  # (t0, t1, kind, scene, transition in)
    (0.00, 0.75, "face", None, "cut"),
    (0.75, 17.94, "card", "Intro", "shrink"),
    (17.94, 20.43, "face", None, "grow"),
    (20.43, 34.43, "full", "Intro", "push_left"),
    (34.43, 35.85, "face", None, "push_left"),
    (35.85, 49.55, "full", "Opt1", "push_up"),        # look-aways 36.45, 48.88
    (49.55, 54.55, "card", "Opt1", "slide_card"),
    (54.55, 57.05, "full", "Opt2", "push_up"),
    (57.05, 76.20, "card", "Opt2", "slide_card"),
    (76.20, 87.55, "full", "Opt3", "push_up"),        # look-away 83.26
    (87.55, 92.30, "card", "Opt3", "slide_card"),
    (92.30, 97.55, "full", "Opt3", "card_out"),       # look-away 92.90; the card is gone by 92.80
    (97.55, 102.20, "card", "Opt3", "slide_card"),
    (102.20, 104.95, "face", None, "grow"),
    (104.95, 109.55, "full", "Opt4", "push_up"),
    (109.55, 134.55, "card", "Opt4", "slide_card"),
    (134.55, 150.00, "full", "Batch", "push_up"),     # look-aways 146.38, 147.74
    (150.00, 161.00, "card", "Batch", "slide_card"),
    (161.00, 175.20, "full", "Workers", "push_up"),   # look-aways 168.00, 171.69
    (175.20, 181.25, "card", "Workers", "slide_card"),
    (181.25, 191.20, "full", "Shards", "push_up"),    # look-aways 188.97, 190.17
    (191.20, 200.25, "card", "Shards", "slide_card"),
    (200.25, 214.30, "card", "Wrap", "cut"),
    (214.30, 999.0, "face", None, "grow"),
]

def board(scene):
    path = os.path.join(MEDIA, QUALITY, f"{scene}.mp4"); t0 = SC[scene]
    def draw(t, dur, ctx):
        return E.clip(path).frame(ctx["t"] - t0)        # native size; the engine crops and scales it (place_board)
    return draw

SC_END = {"Intro": 35.9, "Opt1": 54.65, "Opt2": 76.35, "Opt3": 102.35, "Opt4": 134.7, "Batch": 161.1, "Workers": 181.4, "Shards": 200.35, "Wrap": 214.65}
RECENTER = int(round(2.8 * E.W / (8 * 16 / 9)))   # the boards sit around x = RX = 2.8 beside the card; this many pixels puts them in the middle

def board_at(a, b):
    """the board running over [a, b], to stand in for the face during a look-away"""
    for sc, t0 in SC.items():
        if t0 <= a and b <= SC_END[sc]: return board(sc)
    return None

def plan(p, t0, t1):
    S = []; sfx = []
    for a, b, kind, scene, tr in SHOTS:
        if a >= t1: continue                                                     # a sample needs only the boards it shows
        b = min(b, p.dur)
        if kind == "face": S.append(dict(t0=a, t1=b, kind="face", tr=tr))
        else: S.append(dict(t0=a, t1=b, kind="graphic", draw=board(scene), tr=tr, face=CARD if kind == "card" else None, face_border=BORDER, scene=scene))
    if BROLL: S = BL.splice(S, BL.windows(), bg=BG, after_tr="push_up")        # B-roll lands on its line; the board pushes back in after
    S = E.protect_eyes(S, p.look, board_at=board_at, recenter_px=0, bg=BG)          # the eyes decide where the face may not be
    S = E.direct_face(S, p.look, project=p, bg=BG, border=BORDER)                    # and on the lens, which layout it takes, changed every few seconds
    S = E.hold_over_empty(S, p, BG)                                                   # and never an empty screen between two boards
    for sh in S:
        if sh["tr"] in ("push_up", "push_left", "slide_card", "card_out", "shrink", "grow", "zoom"): sfx.append((sh["t0"] - 0.06, E.whoosh(0.03, 0.4)))
        if sh["tr"] == "morph": sfx.append((sh["t0"] - 0.04, E.whoosh(0.02, 0.35)))
    # a soft tick as each board piece lands: the move starts recorded in animkit/logs
    import json, glob
    for lg in glob.glob(r"C:\Users\ADMIN\camera_audit\animkit\logs\*.json"):
        sc = os.path.basename(lg)[:-5]
        if sc not in SC: continue
        for x in json.load(open(lg)):
            if x[0] == "@" and x[3] in ("build", "label", "connect", "negate"): sfx.append((SC[sc] + x[2] + 0.1, E.tone(0.05, 1800, 1300, 0.02)))
    return S, sfx

def project():
    return E.Project(base=os.path.join(D, "bulk_uploads_full_edit_v2.mp4"), cutlist=os.path.join(D, "cutlist_v2.md"), lookaways=os.path.join(D, "lookaways_v2.json"))

if __name__ == "__main__":
    a = sys.argv[1:]; p = project()
    if a[:1] == ["stills"]:
        ts = [float(x) for x in a[1:]]; S, sfx = plan(p, 0, max(ts) + 2); r = E.Renderer(p, S, 0, p.dur, OUT, sfx, BG); print(r.stills([float(x) for x in a[1:]], OUT.replace(".mp4", "_sheet.png"), cols=4))
    else:
        t0, t1 = (float(a[0]), float(a[1])) if len(a) >= 2 else (0.0, p.dur)
        S, sfx = plan(p, t0, t1); E.Renderer(p, S, t0, t1, OUT if (t0, t1) == (0.0, p.dur) else OUT.replace(".mp4", f"_{int(t0)}-{int(t1)}.mp4"), sfx, BG).render()
