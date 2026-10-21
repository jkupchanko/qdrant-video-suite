"""The Manim scene behind the MATH style (3Blue1Brown). One continuous 41-second animation timed to the cue
sheet in out/cues.json; the face windows are left empty (the engine cuts the presenter in over them).

Render:  python -m manim -qh --fps 30 -o math_scene.mp4 style_math_scene.py BulkUploads
"""
import json, numpy as np
from manim import *
C = json.load(open(r"C:\Users\ADMIN\camera_audit\styles\out\cues.json"))
FONT = r"C:\Users\ADMIN\camera_audit\fonts\cmunrm.otf"
BLUE_ = "#58C4DD"; YEL = "#FFFF00"; GRN = "#83C167"; RED_ = "#FC6255"; GREY = "#888888"; BLUE_DK = "#1C758A"

PLAYLOG = []
class Clock:
    def __init__(self, scene): self.s = scene; self.t = 0.0
    def until(self, T):
        if T > self.t + 1e-3: self.s.wait(T - self.t); self.t = T
    def play(self, *anims, run_time=1.0, **kw):
        PLAYLOG.append((round(self.t, 3), run_time, type(anims[0]).__name__)); self.s.play(*anims, run_time=run_time, **kw); self.t += run_time

class BulkUploads(Scene):
    def T(self, s, size=40, color=WHITE, **kw): return Text(s, font="CMU Serif", font_size=size, color=color, **kw)
    def construct(self):
        with register_font(FONT): self.body()
    def body(self):
        ck = Clock(self); until, play = ck.until, ck.play; rng = np.random.default_rng(1)
        # 1.24  data flows into Qdrant
        until(C["large"] - 0.3)
        box = RoundedRectangle(corner_radius=0.2, width=3.2, height=2.0, stroke_width=3, color=BLUE_).shift(RIGHT * 4); lab = self.T("Qdrant", 44).move_to(box)
        play(Create(box), Write(lab), run_time=0.7)
        dots = VGroup(*[Dot(radius=0.05, color=BLUE_).move_to([-7.6 + rng.uniform(-1.5, 1.5), rng.uniform(-2.6, 2.6), 0]) for _ in range(160)]); self.add(dots)
        targets = [box.get_center() + np.array([rng.uniform(-1.3, 1.3), rng.uniform(-0.7, 0.7), 0]) for _ in dots]
        play(LaggedStart(*[d.animate.move_to(tg) for d, tg in zip(dots, targets)], lag_ratio=0.004), run_time=1.6)
        # 3.0  "doesn't just store vectors": a cross through "just"
        until(C["just"] - 0.15)
        line = self.T("Qdrant doesn't just store vectors", 40).to_edge(DOWN, buff=1.2); play(Write(line), run_time=0.7)
        until(C["just"] + 0.55); cross = Cross(line[13:17], stroke_width=5, scale_factor=1.2); play(Create(cross), run_time=0.35)
        # 4.75  what happens on upload: a list, one item per spoken word
        until(C["list_t0"]); play(FadeOut(line), FadeOut(cross), dots.animate.set_opacity(0.3), run_time=0.4)
        items = ["vectors", "payloads", "indexes", "much more"]; cues_ = [C["list_t0"] + 0.5, C["payloads"], C["indexes"], C["much"]]
        texts = VGroup(*[self.T("\u2022 " + s, 42) for s in items]).arrange(DOWN, aligned_edge=LEFT, buff=0.45).shift(LEFT * 3.5)
        for tx, cu in zip(texts, cues_): until(cu - 0.1); play(Write(tx), run_time=0.5)
        until(C["background"]); play(texts[3].animate.set_color(YEL), run_time=0.3)
        # 9.32  one configuration for everything? no
        until(C["cfg_t0"]); play(FadeOut(texts), FadeOut(dots), FadeOut(box), FadeOut(lab), run_time=0.4)
        top = RoundedRectangle(corner_radius=0.15, width=4.6, height=1.1, stroke_width=3, color=WHITE).shift(UP * 2.4); tl = self.T("one configuration", 36).move_to(top)
        until(C["single"] - 0.2); play(Create(top), Write(tl), run_time=0.6)
        lows = VGroup(*[VGroup(RoundedRectangle(corner_radius=0.15, width=3.4, height=1.0, stroke_width=3, color=BLUE_), self.T(s, 30)) for s in ["RAG app", "100M points", "multi-tenant"]])
        for g in lows: g[1].move_to(g[0])
        lows.arrange(RIGHT, buff=0.6).shift(DOWN * 1.6)
        arrows = VGroup(*[Arrow(top.get_bottom(), g[0].get_top(), buff=0.1, stroke_width=3, color=GREY) for g in lows])
        until(C["works"] - 0.3); play(LaggedStart(*[AnimationGroup(Create(a), Create(g[0]), Write(g[1])) for a, g in zip(arrows, lows)], lag_ratio=0.3), run_time=1.0)
        until(C["all"]); cr = Cross(top, stroke_width=6); play(Create(cr), run_time=0.35)
        until(C["plan_t0"] - 0.3); play(FadeOut(VGroup(top, tl, lows, arrows, cr)), run_time=0.3)
        # 13.48 to 18.04  the presenter (nothing drawn)
        # 18.04  dense and sparse vectors as arrays
        until(C["ds_t0"] + 0.3); title = self.T("two kinds of vectors", 36, GREY).to_edge(UP, buff=0.6); play(Write(title), run_time=0.6)
        dense = self.T("[ 0.12,  -0.87,  0.33,  0.91,  0.04,  ... ]", 34).shift(LEFT * 3.3 + UP * 0.6); dl = self.T("dense", 40, BLUE_).next_to(dense, UP, buff=0.5)
        until(C["dense"] - 0.1); play(Write(dl), Write(dense), run_time=0.6)
        sparse = self.T("[ 0,  0,  0.9,  0,  0,  0,  0.6,  0,  0,  0.8 ]", 34).shift(RIGHT * 3.3 + UP * 0.6); sl = self.T("sparse", 40, YEL).next_to(sparse, UP, buff=0.5)
        until(C["sparse"] - 0.1); play(Write(sl), Write(sparse), run_time=0.6)
        until(C["sparse"] + 0.6); play(*[sparse[i].animate.set_color(GREY) for i in (1, 3, 9, 11, 13, 19, 21)], run_time=0.4)
        # 22.08  the HNSW graph under the dense vector
        until(C["hnsw_t0"] + 0.4); play(dense.animate.scale(0.7).shift(UP * 0.4), sparse.animate.scale(0.7).shift(UP * 0.4), run_time=0.5)
        rng2 = np.random.default_rng(5); pts = [np.array([-5.6 + rng2.uniform(0, 4.6), -3.1 + rng2.uniform(0, 2.6), 0]) for _ in range(18)]
        nodes = VGroup(*[Dot(p, radius=0.07, color=BLUE_) for p in pts]); edges = VGroup()
        for i, a in enumerate(pts):
            for j in sorted(range(18), key=lambda j: np.linalg.norm(pts[j] - a))[1:3]: edges.add(Line(a, pts[j], stroke_width=2, color=BLUE_DK))
        until(C["hnsw"] - 0.2); play(Create(nodes), run_time=0.5); play(Create(edges), run_time=0.9)
        hl = self.T("HNSW graph", 34, BLUE_).next_to(nodes, DOWN, buff=0.3); play(Write(hl), run_time=0.4)
        order = sorted(range(18), key=lambda j: pts[j][0])[:5]; path = VMobject(color=YEL, stroke_width=5).set_points_as_corners([pts[j] for j in order]); play(Create(path), run_time=0.8)
        # 25.13  the sparse index under the sparse vector
        until(C["sparse2"] + 0.3)
        rows = VGroup(*[self.T(s, 28) for s in ["term 3    \u2192   doc 4,  doc 9,  doc 31", "term 7    \u2192   doc 4,  doc 12", "term 10  \u2192   doc 9,  doc 18,  doc 77"]]).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([3.3, -1.6, 0])
        until(C["indexing"] - 0.5); play(LaggedStart(*[Write(r) for r in rows], lag_ratio=0.4), run_time=1.2)
        sl2 = self.T("sparse index", 34, YEL).next_to(rows, DOWN, buff=0.3); play(Write(sl2), run_time=0.4)
        # 28.36  memory and performance as bars
        until(C["mp_t0"]); play(FadeOut(VGroup(title, dense, dl, sparse, sl, nodes, edges, hl, path, rows, sl2)), run_time=0.5)
        base_y = -1.8; bars = VGroup(); labels = VGroup(); spec = [("dense", BLUE_, 2.8, -4.2), ("sparse", YEL, 1.6, -2.4), ("dense", BLUE_, 2.0, 1.4), ("sparse", YEL, 2.6, 3.2)]
        for name, col, hgt, x in spec:
            r = Rectangle(width=1.2, height=0.02, stroke_width=2, color=col, fill_color=col, fill_opacity=0.6).move_to([x, base_y, 0], aligned_edge=DOWN); bars.add(r); labels.add(self.T(name, 26, col).next_to(r, DOWN, buff=0.2))
        mem = self.T("memory", 38).move_to([-3.3, 2.2, 0]); perf = self.T("performance", 38).move_to([2.3, 2.2, 0]); axis = Line([-6, base_y, 0], [6, base_y, 0], stroke_width=2, color=GREY)
        until(C["memory"] - 0.3); play(Create(axis), Write(mem), run_time=0.5)
        play(*[bars[i].animate.stretch_to_fit_height(spec[i][2]).move_to([spec[i][3], base_y, 0], aligned_edge=DOWN) for i in (0, 1)], *[Write(labels[i]) for i in (0, 1)], run_time=0.8)
        until(C["perf"] - 0.1); play(Write(perf), run_time=0.3)
        play(*[bars[i].animate.stretch_to_fit_height(spec[i][2]).move_to([spec[i][3], base_y, 0], aligned_edge=DOWN) for i in (2, 3)], *[Write(labels[i]) for i in (2, 3)], run_time=0.8)
        until(C["bulk"] - 0.1); bu = self.T("during bulk uploads", 34, YEL).to_edge(DOWN, buff=0.5); play(Write(bu), run_time=0.5)
        until(C["ch_t0"] - 0.3); play(FadeOut(VGroup(axis, bars, labels, mem, perf, bu)), run_time=0.3)
        # 34.43 to 36.10  the presenter
        # 36.10  chapter title, then RAM to disk
        until(C["ch_face_end"])
        t1 = self.T("Option 1", 72).shift(UP * 0.5); ul = Line(t1.get_left() + DOWN * 0.6, t1.get_right() + DOWN * 0.6, stroke_width=3, color=BLUE_); t2 = self.T("store dense vectors on disk", 36, GREY).next_to(ul, DOWN, buff=0.4)
        play(Write(t1), run_time=0.6); play(Create(ul), Write(t2), run_time=0.5)
        until(C["o1_t0"] + 0.2); play(VGroup(t1, ul, t2).animate.scale(0.5).to_edge(UP, buff=0.4), run_time=0.5)
        ram = RoundedRectangle(corner_radius=0.2, width=4.2, height=3.2, stroke_width=3, color=RED_).shift(LEFT * 3.5 + DOWN * 0.4); rl = self.T("RAM", 36, RED_).next_to(ram, UP, buff=0.2)
        dsk = RoundedRectangle(corner_radius=0.2, width=4.2, height=3.2, stroke_width=3, color=BLUE_).shift(RIGHT * 3.5 + DOWN * 0.4); dkl = self.T("disk", 36, BLUE_).next_to(dsk, UP, buff=0.2)
        play(Create(ram), Write(rl), Create(dsk), Write(dkl), run_time=0.7)
        vec = VGroup(*[Dot(radius=0.07, color=BLUE_) for _ in range(48)]).arrange_in_grid(6, 8, buff=0.25).move_to(ram); play(FadeIn(vec), run_time=0.3)
        until(C["storing"]); play(LaggedStart(*[d.animate.shift(RIGHT * 7) for d in vec], lag_ratio=0.02), run_time=1.3)
        until(C["disk"] - 0.1); od = self.T("on_disk = True", 36, YEL).next_to(dsk, DOWN, buff=0.3); play(Write(od), run_time=0.5)
        until(41.3)
        json.dump(PLAYLOG, open('C:/Users/ADMIN/camera_audit/anim_audit/calib_truth.json', 'w'))
