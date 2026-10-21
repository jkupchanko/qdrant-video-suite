"""MATH: the look of 3Blue1Brown, whose neural-network and LLM chapters are the most-watched AI explainers on
YouTube (24.8M, 11.4M, 9.6M, 8.1M views), copied from the frame audit of "But what is a neural network?" and
"Large Language Models explained briefly".

What the audit shows
  - pure black; thin light strokes; text in Computer Modern (the LaTeX serif); blue (#58C4DD) for the main
    object, yellow for the thing to look at, grey for what is not in play
  - nothing cuts: objects are drawn on (Create), written (Write), moved, scaled and transformed into the
    next object; the camera glides; 0 hard cuts and 2.6 to 9.6 visible changes a minute
  - diagrams are literal: vectors are arrays of numbers, a graph is dots and lines, a store is a box with
    dots in it; one label per object, set beside it
  - no presenter; here the presenter is cut in at the start, for the plan and for the chapter line
The animation itself is a Manim scene (style_math_scene.py) timed to the cue sheet; this module cuts the
presenter in over its empty windows.
"""
import os
import engine as E
from engine import W, H
from beats import cues
OUT = r"C:\Users\ADMIN\camera_audit\styles\out\math_0-41.mp4"; BG = (0, 0, 0)
SCENE = r"C:\Users\ADMIN\camera_audit\styles\media\videos\style_math_scene\1080p30\math_scene.mp4"

def plan(p, t0, t1):
    c = cues(p); S = []
    def face(a, b): S.append(dict(t0=a, t1=b, kind="face", tr="cut"))
    def anim(a, b): S.append(dict(t0=a, t1=b, kind="graphic", draw=lambda t, dur, ctx, a=a: E.clip(SCENE).frame(a + t), tr="cut", face=None))
    face(c["hook_t0"], c["large"]); anim(c["large"], c["plan_t0"]); face(c["plan_t0"], c["ds_t0"]); anim(c["ds_t0"], c["ch_t0"]); face(c["ch_t0"], c["ch_face_end"]); anim(c["ch_face_end"], t1)
    return S, []      # no sound effects: the reference has none

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(__file__)); E.main(sys.modules[__name__])
