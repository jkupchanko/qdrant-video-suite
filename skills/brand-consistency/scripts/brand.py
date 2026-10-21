"""brand.py: the Qdrant palette for video, as RGB tuples, read from the Qdrant brand skill itself (qdrant-brand/, copied
from Qdrant's company-wide qdrant-brand skill: its brand_utils.QdrantColors is the one source). Styles take every colour
from here, and the review checks the screen against PALETTE.

  from brand import C, PALETTE, GROUPS, SYNTAX, LOGO_DIR
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); QB = os.path.join(os.path.dirname(HERE), "qdrant-brand")
sys.path.insert(0, os.path.join(QB, "scripts")); from brand_utils import QdrantColors as Q
LOGO_DIR = os.path.join(QB, "assets", "logos")

def rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

class C:
    """the roles a video uses, each a colour of the brand palette"""
    BG = rgb(Q.BG_DEFAULT)               # page background #0B0F19
    CARD = rgb(Q.BG_ELEVATION_1)         # cards #111824
    CARD2 = rgb(Q.BG_ELEVATION_2)        # nested cards, header bars #141A2A
    RAISED = rgb(Q.BG_ELEVATION_8)       # highest surface #212635
    BORDER = rgb(Q.NEUTRAL_700)          # borders #4E5366
    TEXT = rgb(Q.NEUTRAL_50)             # text #F0F3FA
    MUTED = rgb(Q.NEUTRAL_400)           # secondary text that must read at 1080 on a phone #ABB1C7
    FAINT = rgb(Q.NEUTRAL_600)           # captions, line numbers #656B7F
    RED = rgb(Q.PRIMARY_500)             # Qdrant Red #DC244C
    RED_DARK = rgb(Q.PRIMARY_800)        # #9E0D38
    RED_LIGHT = rgb(Q.PRIMARY_300)       # #FF8792
    VIOLET = rgb(Q.SECONDARY_500)        # #6047FF
    VIOLET_LIGHT = rgb(Q.SECONDARY_300)  # #9494FF
    TEAL = rgb(Q.CHART_SEQUENCE[2])      # #009688
    BLUE = rgb(Q.CHART_SEQUENCE[3])      # #03A9F4
    ORANGE = rgb(Q.CHART_SEQUENCE[4])    # #FF9800
    CYAN = rgb(Q.CHART_SEQUENCE[7])      # #00BCD4
    WHITE = (255, 255, 255)

GROUPS = [rgb(h) for h in Q.CHART_SEQUENCE]          # list groups, charts: the brand's order (red, violet, teal, light blue, ...)
SYNTAX = dict(kw=C.VIOLET_LIGHT, str=C.CYAN, num=C.ORANGE, call=C.BLUE, arg=C.RED_LIGHT, punct=rgb(Q.NEUTRAL_500), comment=C.FAINT, name=C.TEXT)

# every colour in the palette: what the review accepts as on brand (accents are matched by hue and saturation)
PALETTE = sorted({rgb(v) for k, v in vars(Q).items() if isinstance(v, str) and v.startswith("#")} | {rgb(h) for h in Q.CHART_SEQUENCE})
