"""Six passages of the miniCOIL script: the words, what I saw in them, the camera call, and the frame it makes
with John's Bulk Uploads footage. One composite image per passage (script on the left, frame on the right)."""
import os, textwrap, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, r"C:\Users\ADMIN\camera_audit\demo")
_src = open(r"C:\Users\ADMIN\camera_audit\demo\build_preview.py", encoding="utf-8").read()
__file__ = r"C:\Users\ADMIN\camera_audit\demo\build_preview.py"
exec(_src[:_src.index("def frame(")])      # constants, fonts, card() and rounded() from the preview builder
HERE = r"C:\Users\ADMIN\camera_audit\john_video"
art = {"home": Image.open(r"C:\Users\ADMIN\camera_audit\demo\article_home_casa.png").convert("RGB"), "bat": Image.open(r"C:\Users\ADMIN\camera_audit\demo\article_bat.png").convert("RGB")}
fullA = Image.open(os.path.join(HERE, "take_full2_fullcrop.png")).convert("RGB"); fullB = Image.open(os.path.join(HERE, "take_full2_fullcrop.png")).convert("RGB")
p43 = Image.open(os.path.join(HERE, "take_full2_43.png")).convert("RGB")
BODY = font(["segoeui.ttf"], 26); BODY_B = font(["segoeuib.ttf", "segoeui.ttf"], 26); H1 = font(["georgia.ttf"], 40); CAP = font(["segoeui.ttf"], 22); CALL = font(["consola.ttf"], 24)

EX = [
 dict(n=1, t="0:00", section="Hook", lines=["Your search box accepts Spanish, but your documents are in English.", "Can it still find the right answer?", "Let's try it with three short passages and a little Python."],
      call="[**Camera:** FULL.]", layout="full", face=fullA, kind="hook",
      saw=["It is the first passage, so a call is required (rule 1).", "The words are a question put to the viewer. Nothing on screen has to be read yet.", "A question is the person's; the hook goes on the face and holds about 20 s."]),
 dict(n=2, t="0:20", section="Set up the example", lines=["One passage is about a dog running through a park.", "One is about soup.", "And one is about a star."],
      call="[**Camera:** SMALL, top right, 20% width.]", layout="small", kind="setup",
      saw=["The Show field says the three passages are on screen with the intended answer marked.", "They are three short lines, not dense: the viewer glances, they do not study.", "You are still talking, so presence stays: a small window, not NONE."]),
 dict(n=3, t="0:58", section="Explain the connection", lines=["This version of miniCOIL connects related English and Spanish words through a shared concept.", "The article illustrates this with home and casa."],
      call="[**Camera:** NONE.]  (implied by the B roll block)", layout="none", kind="article",
      saw=["A B roll block sits under this passage: the article's home and casa figure.", "The figure is the point of the sentence; the viewer must read it (rule 2).", "A window would cover part of a diagram, so the face goes away for the insert."]),
 dict(n=4, t="1:35", section="Show the code", lines=["Here's how that becomes a search.", "We encode the passage as English.", "Then we encode the question as Spanish.", "Notice that we also mark the question as a query."],
      call="[**Camera:** NONE.]", layout="none", kind="code",
      saw=["'Here's how' is a screen word; the Show field says the two encode calls with is_query highlighted.", "Code must be read line by line: rule 2, no face over it.", "Section boundary too (rule 4): the one place the window could change corner, but here it is simply off."]),
 dict(n=5, t="2:26", section="Show the code", lines=["Now we send the encoded question to the collection.", "Let's see which passages come back."],
      call="[**Camera:** FULL.]", layout="full", face=fullB, kind="code",
      saw=["'Now' and 'let's' are sentence turns: a natural place for a change.", "The face has been off since 1:35, about 50 s. Watched videos bring it back by 40 s (rule 3).", "Nothing to read in these two lines, so the person carries the hand-off to the results."]),
 dict(n=6, t="4:51", section="Give them something to try", lines=["That's your first experiment.", "A few passages, three questions, and results you can judge yourself."],
      call="[**Camera:** FULL.]", layout="full", face=fullB, kind="close",
      saw=["Last passage: a call is required (rule 5).", "It is the take-away and the invitation, spoken to 'you'. Most videos in the corpus close on the person.", "The practice card was on screen just before; it has done its job, so the face comes back for the last line."]),
]

def frame_for(e):
    im = Image.new("RGB", (W, H), BG); lay = e["layout"]
    if lay == "full": im.paste(e["face"].resize((W, H)), (0, 0)); return im
    cw = int(W * 0.80); ch = int(cw * 9 / 16); x0, y0 = (W - cw) // 2, (H - ch) // 2
    if e["kind"] == "article": c = art["home"].resize((cw, ch), Image.LANCZOS)
    else: c = card(cw, ch, "card", {"hook": "Hook", "setup": "Set up", "code": "Show the code", "close": "Give"}[e["kind"]], "")
    im.paste(c, (x0, y0), rounded(c))
    if lay == "small":
        pw = int(W * 0.20); ph = int(pw * 3 / 4); p = p43.resize((pw, ph), Image.LANCZOS); px, py = x0 + cw - pw - 24, y0 + 24
        im.paste(p, (px, py), rounded(p, 16)); ImageDraw.Draw(im).rounded_rectangle([px - 3, py - 3, px + pw + 3, py + ph + 3], radius=18, outline=(245, 244, 240), width=4)
    return im

tiles = []
for e in EX:
    right = frame_for(e).resize((960, 540), Image.LANCZOS)
    left = Image.new("RGB", (960, 540), (255, 255, 255)); d = ImageDraw.Draw(left)
    d.text((40, 28), f"{e['n']}.  {e['t']}  {e['section']}", font=H1, fill=INK)
    y = 100
    for l in e["lines"]:
        for wl in textwrap.wrap(l, 62): d.text((40, y), wl, font=BODY, fill=INK); y += 34
    y += 10; d.rectangle([40, y, 920, y + 44], fill=(245, 244, 240)); d.text((52, y + 8), e["call"], font=CALL, fill=RED); y += 64
    d.text((40, y), "what I saw", font=BODY_B, fill=MUTED); y += 34
    for s_ in e["saw"]:
        for wl in textwrap.wrap("- " + s_, 70): d.text((40, y), wl, font=CAP, fill=INK); y += 28
        y += 4
    tile = Image.new("RGB", (1920, 540), (255, 255, 255)); tile.paste(left, (0, 0)); tile.paste(right, (960, 0))
    ImageDraw.Draw(tile).line([(0, 539), (1920, 539)], fill=(200, 200, 200), width=2)
    tile.save(os.path.join(HERE, f"walk_{e['n']}.png")); tiles.append(tile)
sheet = Image.new("RGB", (1920, 540 * len(tiles)), (255, 255, 255))
for i, t in enumerate(tiles): sheet.paste(t, (0, i * 540))
sheet.save(os.path.join(HERE, "walkthrough.png")); print("ok", len(tiles))
