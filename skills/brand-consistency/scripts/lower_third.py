"""lower_third.py: the Qdrant name lower third. A white circle with the Qdrant brandmark slides in from the bottom left,
the red bar unrolls out of it with the presenter's name and title, it holds, and it all goes back the way it came.

  from lower_third import LowerThird
  lt = LowerThird("John Kupchanko", "Developer Relations Engineer", t_in=4.9, hold=5.0)
  lt(t) -> a 1920x1080 RGBA PIL image to lay over the frame at time t, or None when it is off screen
  lt.t_out                      when it is gone; lt.box: (x, y, w, h) of the whole card at full size

  python lower_third.py --name "John Kupchanko" --title "Developer Relations Engineer" --sheet OUT.png [--frame STILL.jpg]
  python lower_third.py --name ... --title ... --mp4 OUT.mp4 [--frame STILL.jpg]      the animation over a still, 8 s

Brand (qdrant-brand): the logo is the supplied Qdrant-Profile-Circular-Light file, cropped to its circle, never redrawn;
the bar is Qdrant Red #DC244C into Primary Dark #9E0D38 (the gradient is on the bar only; text is one solid colour);
the name is Mona Sans Bold, the title Mona Sans Regular, both white. It sits above the bottom letterbox bar.
"""
import os, sys, math, argparse
import numpy as np, skia
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ASSETS = os.path.join(os.path.dirname(HERE), "assets")
W, H = 1920, 1080
RED, RED_DARK, WHITE = (220, 36, 76), (158, 13, 56), (255, 255, 255)
IN_S, OUT_S = 0.75, 0.6                                           # the whole entrance and exit

def _ease_out(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def _ease_in(x): x = max(0.0, min(1.0, x)); return x ** 3
def _col(c, a=1.0): return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(255 * max(0.0, min(1.0, a))))
_tf = {}
def _font(name, size):
    if name not in _tf: _tf[name] = skia.Typeface.MakeFromFile(os.path.join(ASSETS, "fonts", name))
    return skia.Font(_tf[name], size)

class LowerThird:
    def __init__(self, name, title, t_in, hold=5.0, left=64, bottom=H - 72 - 40, scale=1.0, logo=None):
        self.name, self.title, self.t_in, self.hold = name, title, float(t_in), float(hold)
        self.t_out = self.t_in + IN_S + self.hold + OUT_S; s = scale
        self.D = 150 * s; self.BH = 104 * s; self.left, self.bottom = left, bottom
        self.fn, self.ft = _font("MonaSans-Bold.ttf", 46 * s), _font("MonaSans-Regular.ttf", 29 * s)
        tw = max(self.fn.measureText(name), self.ft.measureText(title))
        self.bar_w = self.D * 0.5 + 30 * s + tw + 46 * s                # from the circle's centre to past the longer line
        self.box = (left, int(bottom - self.D), int(self.D / 2 + self.bar_w), int(self.D))
        logo = logo or os.path.join(ASSETS, "Qdrant-Profile-Circular-Light.png")
        im = Image.open(logo).convert("RGBA"); k = int(self.D * 2)             # the supplied file, cropped to its circle
        im = im.resize((k, k), Image.LANCZOS); mask = Image.new("L", (k, k), 0)
        from PIL import ImageDraw; ImageDraw.Draw(mask).ellipse((0, 0, k - 1, k - 1), fill=255); im.putalpha(mask)
        self.logo = skia.Image.fromarray(np.asarray(im), colorType=skia.kRGBA_8888_ColorType)

    def phase(self, t):
        """(circle 0..1, bar 0..1, text 0..1) at time t; all 0 off screen"""
        a = t - self.t_in
        if a < 0 or t >= self.t_out: return 0.0, 0.0, 0.0
        if a < IN_S:                                                   # the circle slides in, the bar unrolls out of it, the words rise
            return _ease_out(a / 0.42), _ease_out((a - 0.22) / 0.38), _ease_out((a - 0.42) / 0.3)
        b = a - IN_S - self.hold
        if b < 0: return 1.0, 1.0, 1.0
        return 1 - _ease_in((b - 0.3) / 0.3), 1 - _ease_in((b - 0.1) / 0.3), 1 - _ease_in(b / 0.18)   # and back the way they came

    def __call__(self, t):
        kc, kb, kt = self.phase(t)
        if kc <= 0: return None
        s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(skia.Color(0, 0, 0, 0))
        D, BH = self.D, self.BH; cx = self.left + D / 2 - (self.left + D + 40) * (1 - kc); cy = self.bottom - D / 2
        if kb > 0:                                                     # the bar, from under the circle's centre to the right
            bw = self.bar_w * kb; r = skia.Rect.MakeXYWH(cx, cy - BH / 2, bw, BH)
            sh = skia.Paint(AntiAlias=True, Color=_col((0, 0, 0), 0.45 * kb)); sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
            cv.drawRRect(skia.RRect.MakeRectXY(r.makeOffset(0, 8), 14, 14), sh)
            g = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(cx, 0), (cx + self.bar_w, 0)], [_col(RED), _col(RED_DARK)]))
            cv.drawRRect(skia.RRect.MakeRectXY(r, 14, 14), g)
            if kt > 0:                                                 # the words, clipped to the bar as it unrolls
                cv.save(); cv.clipRect(r); x = cx + D / 2 + 30 * D / 150; dy = 10 * (1 - kt)
                p = skia.Paint(AntiAlias=True, Color=_col(WHITE, kt))
                cv.drawString(self.name, x, cy - 4 * D / 150 + dy, self.fn, p)
                cv.drawString(self.title, x, cy + 34 * D / 150 + dy, self.ft, p)
                cv.restore()
        sh = skia.Paint(AntiAlias=True, Color=_col((0, 0, 0), 0.5)); sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12))
        cv.drawCircle(cx, cy + 6, D / 2, sh)
        cv.drawCircle(cx, cy, D / 2 + 4, skia.Paint(AntiAlias=True, Color=_col(WHITE)))
        cv.drawImageRect(self.logo, skia.Rect.MakeXYWH(cx - D / 2, cy - D / 2, D, D), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
        return Image.fromarray(s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGBA")

def _bg(frame):
    if frame: return Image.open(frame).convert("RGBA").resize((W, H))
    return Image.new("RGBA", (W, H), (11, 15, 25, 255))

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True); ap.add_argument("--title", required=True); ap.add_argument("--hold", type=float, default=5.0)
    ap.add_argument("--frame"); ap.add_argument("--sheet"); ap.add_argument("--mp4")
    a = ap.parse_args(); L = LowerThird(a.name, a.title, 1.0, a.hold); bg = _bg(a.frame)
    if a.sheet:
        ts = [1.1, 1.25, 1.4, 1.6, 1.8, 4.0, L.t_out - 0.45, L.t_out - 0.2]; tiles = []
        for t in ts:
            fr = bg.copy(); o = L(t)
            if o is not None: fr.alpha_composite(o)
            tiles.append(fr.convert("RGB").crop((0, H // 2, W // 2 + 200, H)).resize((560, 316)))
        sheet = Image.new("RGB", (560 * 4, 316 * 2))
        for i, im in enumerate(tiles): sheet.paste(im, ((i % 4) * 560, (i // 4) * 316))
        sheet.save(a.sheet); print("->", a.sheet)
    if a.mp4:
        import subprocess, imageio_ffmpeg
        p = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                              "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", a.mp4], stdin=subprocess.PIPE)
        for i in range(int((L.t_out + 1.0) * 30)):
            fr = bg.copy(); o = L(i / 30)
            if o is not None: fr.alpha_composite(o)
            p.stdin.write(fr.convert("RGB").tobytes())
        p.stdin.close(); p.wait(); print("->", a.mp4)

if __name__ == "__main__":
    main()
