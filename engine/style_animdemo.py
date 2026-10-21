"""ANIMATED BOARD: the audit's best practice on the first 41 s of Bulk Uploads (animkit/demo_bulk.py).
The presenter is full frame at the open, between boards and for the chapter line; in a face card on the
left while board A and the plan build; off screen for the full-width dense/sparse board and Option 1 (the
house rule: no face over diagrams). The look-away at 36.45 s falls inside the Option 1 board.
Transitions: the face shrinks into its card when the first board starts and grows back out of it; pushes
between face and full boards; 0.5 s each."""
import os
import engine as E
from engine import W, H
from beats import cues
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\animdemo_0-41.mp4"; BG = (11, 15, 25)
SCENE = r"C:\Users\ADMIN\camera_audit\animkit\media\videos\demo_bulk\1080p30\demo_bulk.mp4"
CARD = ("card", (90, 180, 620, 720), 16)

def plan(p, t0, t1):
    c = cues(p); S = []; sfx = []
    board = lambda a: (lambda t, dur, ctx: E.clip(SCENE).frame(a + t))
    def face(a, b, tr="cut"): S.append(dict(t0=a, t1=b, kind="face", tr=tr))
    def card(a, b, tr="cut"): S.append(dict(t0=a, t1=b, kind="graphic", draw=board(a), tr=tr, face=CARD, face_border=((78, 83, 102), 3)))
    def full(a, b, tr="cut"): S.append(dict(t0=a, t1=b, kind="graphic", draw=board(a), tr=tr, face=None))
    face(t0, 0.75)
    card(0.75, c["ds_t0"] - 0.1, "shrink")                  # board A and the plan, face in the card
    face(c["ds_t0"] - 0.1, c["dense"] - 0.45, "grow")       # "Before we start, ..." to camera
    full(c["dense"] - 0.45, c["ch_t0"], "push_left")         # dense vs sparse, full width
    face(c["ch_t0"], 35.85, "push_left")                     # "let's start with our first option"
    full(35.85, t1, "push_up")                               # Option 1 board; covers the look-away at 36.45
    for k in ("large", "just", "payloads", "indexes", "much", "single", "works", "all", "options", "best", "dense", "sparse", "hnsw", "indexing", "memory", "perf", "bulk", "storing", "disk"):
        sfx.append((c[k] - 0.3, E.tone(0.05, 1800, 1300, 0.025)))           # a soft tick as each piece lands
    for k in ("ds_t0", "ch_t0"): sfx.append((c[k] - 0.1, E.whoosh(0.03, 0.4)))
    return S, sfx

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
