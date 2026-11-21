#!/usr/bin/env python3
"""Draw the news-image-20261120 front page (1024x1024).

Fresh build for the 20 Nov 2026 entry: 4 features + 12 mediums + 16 briefs
(target 32 stories), all verified 20-Nov 2026. Layout, top to bottom:
masthead (date-led) -> region bar -> stat band -> timeline -> 2x2 features
-> 4x3 mediums -> map + briefs -> DATE CHECK -> footer.
Python + PIL only. Run: python3 draw_20nov.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 22
WORK = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("ENTRY_OUT") or os.path.join(WORK, "entry.png")

# ---------------------------------------------------------------- palette
PAPER   = (250, 247, 240)
INK     = (24, 24, 24)
MUTED   = (105, 105, 105)
RULE    = (198, 192, 180)
RED     = (178, 26, 26)
DARKRED = (122, 27, 27)
WHITE   = (255, 255, 255)
NAVY    = (23, 52, 96)
GREEN   = (21, 128, 61)

REGION_COLORS = {
    "ASIA":     (37, 99, 235),
    "EUROPE":   (124, 58, 237),
    "MIDEAST":  (217, 119, 6),
    "AFRICA":   (5, 150, 105),
    "AMERICAS": (220, 38, 38),
    "OCEANIA":  (8, 145, 178),
    "GLOBAL":   (100, 116, 139),
}

# ---------------------------------------------------------------- fonts
FD = "/usr/share/fonts/truetype/noto"

def F(name, size):
    return ImageFont.truetype(os.path.join(FD, name), size)

F_TOP     = F("NotoSans-Bold.ttf", 11)
F_DATE    = F("NotoSerif-Black.ttf", 40)
F_KICK    = F("NotoSerif-BoldItalic.ttf", 13)
F_CAL_M   = F("NotoSans-Bold.ttf", 12)
F_CAL_D   = F("NotoSans-Black.ttf", 30)
F_CAL_W   = F("NotoSans-Bold.ttf", 10)
F_REG     = F("NotoSans-Bold.ttf", 10)
F_STAT_N  = F("NotoSans-Black.ttf", 20)
F_STAT_L  = F("NotoSans-Regular.ttf", 9)
F_TL_LBL  = F("NotoSans-Black.ttf", 11)
F_TL_T    = F("NotoSans-Black.ttf", 11)
F_TL      = F("NotoSans-Regular.ttf", 11)
F_FTAG    = F("NotoSans-Bold.ttf", 10)
F_FHEAD   = F("NotoSerif-Bold.ttf", 24)
F_FHEAD_S = F("NotoSerif-Bold.ttf", 21)
F_FDECK   = F("NotoSans-Regular.ttf", 13)
F_MTAG    = F("NotoSans-Bold.ttf", 9)
F_MHEAD   = F("NotoSans-Bold.ttf", 15)
F_MDECK   = F("NotoSans-Regular.ttf", 10)
F_SEC     = F("NotoSans-Black.ttf", 12)
F_BRIEF   = F("NotoSans-Regular.ttf", 11)
F_BRIEF_B = F("NotoSans-Bold.ttf", 11)
F_MAPCAP  = F("NotoSans-Regular.ttf", 9)
F_DC      = F("NotoSans-Bold.ttf", 11)
F_DC_T    = F("NotoSans-Regular.ttf", 11)
F_FOOT    = F("NotoSans-Regular.ttf", 10)
F_ART_L   = F("NotoSans-Bold.ttf", 10)
F_ART_N   = F("NotoSans-Black.ttf", 14)

# ---------------------------------------------------------------- text helpers
def tw(d, text, font):
    return d.textlength(text, font=font)

def wrap_text(d, text, font, max_w):
    """Greedy word wrap to max_w pixels; returns list of lines."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if tw(d, trial, font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def fit_lines(d, text, font, max_w, max_lines):
    """Wrap text; truncate with ellipsis if it exceeds max_lines."""
    lines = wrap_text(d, text, font, max_w)
    if len(lines) <= max_lines:
        return lines
    lines = lines[:max_lines]
    while lines and tw(d, lines[-1] + "…", font) > max_w:
        lines[-1] = lines[-1][:-1].rstrip()
    lines[-1] = lines[-1] + "…"
    return lines

def draw_lines(d, x, y, lines, font, fill, leading):
    for i, ln in enumerate(lines):
        d.text((x, y + i * leading), ln, font=font, fill=fill)
    return y + len(lines) * leading

def one_line(d, text, font, max_w):
    """Truncate a single line to max_w with an ellipsis."""
    t = text
    while t and tw(d, t, font) > max_w:
        t = t[:-1].rstrip()
    if t != text:
        while t and tw(d, t + "…", font) > max_w:
            t = t[:-1].rstrip()
        t = t + "…"
    return t

# ---------------------------------------------------------------- world map
# Coarse continent polygons in (lon, lat); equirectangular projection.
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-120, 72), (-100, 72), (-85, 70), (-78, 72),
     (-65, 62), (-60, 52), (-66, 44), (-74, 40), (-80, 32), (-81, 26),
     (-90, 21), (-97, 16), (-92, 15), (-86, 12), (-82, 9), (-80, 8),
     (-86, 14), (-94, 17), (-97, 26), (-106, 23), (-112, 28), (-118, 33),
     (-124, 42), (-125, 49), (-132, 56), (-148, 60), (-158, 58), (-166, 60)],
    # South America
    [(-80, 8), (-72, 12), (-64, 10), (-58, 6), (-52, 5), (-50, 0), (-44, -3),
     (-35, -8), (-39, -15), (-41, -23), (-48, -28), (-52, -33), (-58, -39),
     (-62, -41), (-66, -47), (-69, -52), (-72, -54), (-73, -44), (-73, -33),
     (-71, -20), (-75, -15), (-79, -8), (-81, -3), (-80, 2)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 48), (2, 51), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (32, 66), (40, 68),
     (44, 67), (40, 62), (36, 58), (32, 55), (30, 51), (28, 46), (24, 44),
     (28, 44), (30, 46), (24, 42), (23, 40), (19, 42), (16, 44), (12, 44),
     (8, 44), (6, 43), (3, 42), (0, 39), (-6, 36)],
    # Africa
    [(-6, 35), (10, 37), (20, 32), (30, 31), (34, 28), (37, 22), (40, 15),
     (43, 12), (51, 11), (46, 4), (41, -2), (40, -10), (36, -18), (33, -26),
     (28, -33), (20, -35), (17, -29), (14, -22), (12, -17), (13, -12),
     (9, -1), (9, 4), (4, 6), (-8, 5), (-13, 8), (-17, 15), (-16, 21),
     (-14, 26), (-10, 31)],
    # Asia
    [(30, 62), (36, 58), (40, 62), (44, 67), (60, 69), (80, 73), (100, 77),
     (120, 73), (140, 72), (160, 70), (178, 66), (178, 62), (162, 58),
     (156, 52), (142, 50), (140, 42), (132, 42), (127, 38), (122, 37),
     (120, 32), (122, 28), (118, 24), (110, 20), (108, 12), (105, 9),
     (100, 7), (98, 10), (94, 17), (90, 22), (86, 20), (80, 15), (77, 8),
     (74, 12), (70, 20), (66, 25), (61, 25), (56, 27), (52, 26), (50, 29),
     (48, 30), (44, 29), (40, 32), (36, 36), (30, 36), (28, 41), (30, 46),
     (32, 51), (30, 55)],
    # Oceania / SE Asia islands
    [(95, 5), (100, 0), (104, -6), (110, -7), (114, -8), (120, -10),
     (125, -9), (130, -8), (131, -3), (136, -2), (141, -3), (146, -6),
     (150, -10), (146, -19), (142, -15), (140, -17), (135, -15), (132, -12),
     (126, -14), (122, -17), (118, -20), (114, -22), (113, -26), (115, -32),
     (118, -35), (124, -33), (130, -32), (136, -35), (140, -38), (146, -39),
     (150, -37), (153, -31), (153, -27), (146, -19), (142, -11), (142, -10),
     (137, -12), (132, -11), (128, -14), (124, -16), (118, -20), (112, -22),
     (108, -8), (102, -2), (98, 4)],
    [(166, -46), (172, -41), (176, -38), (178, -37), (174, -41), (168, -47)],
]

def draw_map(d, x, y, w, h, dots):
    """Coarse world map + region-coloured story dots."""
    d.rectangle([x, y, x + w, y + h], fill=(222, 232, 238))
    def proj(lon, lat):
        px = x + (lon + 180) / 360 * w
        py = y + (75 - lat) / 135 * h
        return (px, py)
    for poly in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in poly]
        d.polygon(pts, fill=(198, 196, 178), outline=(170, 168, 150))
    for lon, lat, reg in dots:
        px, py = proj(lon, lat)
        c = REGION_COLORS[reg]
        d.ellipse([px - 3.5, py - 3.5, px + 3.5, py + 3.5], fill=c,
                  outline=WHITE, width=1)

# ---------------------------------------------------------------- feature art
def art_kyiv(d, x, y, w, h):
    """Dnipro river + three bridges, strike markers on each."""
    d.rectangle([x, y, x + w, y + h], fill=(228, 236, 228))
    # river (diagonal band)
    d.polygon([(x + 20, y + h), (x + 60, y), (x + 110, y), (x + 70, y + h)],
              fill=(150, 190, 220))
    # three bridges across the river
    for i, by in enumerate([30, 62, 94]):
        d.line([x + 14, y + by, x + w - 14, y + by], fill=(90, 90, 90),
               width=4)
        cx = x + 40 + i * 22
        for dx, dy in [(0, -7), (0, 7), (-7, 0), (7, 0), (-5, -5), (5, -5),
                       (-5, 5), (5, 5)]:
            d.line([cx, y + by, cx + dx, y + by + dy], fill=(230, 80, 20),
                   width=2)
        d.ellipse([cx - 3, y + by - 3, cx + 3, y + by + 3], fill=(255, 200, 40))
    d.text((x + 12, y + h - 26), "3 BRIDGES HIT", font=F_ART_L, fill=DARKRED)

def art_akvan(d, x, y, w, h):
    """Cyclone spiral over the Odisha coast + landfall arrow."""
    d.rectangle([x, y, x + w, y + h], fill=(210, 230, 240))
    # coast
    d.polygon([(x, y + h), (x, y + 78), (x + 60, y + 66), (x + 110, y + 82),
               (x + w, y + 70), (x + w, y + h)], fill=(198, 196, 178))
    cx, cy = x + w // 2 - 10, y + 46
    for r, a0, a1 in [(30, 200, 340), (22, 20, 160), (14, 180, 320),
                      (7, 0, 360)]:
        d.arc([cx - r, cy - r, cx + r, cy + r], a0, a1, fill=(30, 90, 160),
              width=3)
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(30, 90, 160))
    # landfall arrow
    d.line([cx + 8, cy + 30, cx + 26, cy + 52], fill=RED, width=3)
    d.polygon([(cx + 26, cy + 52), (cx + 18, cy + 48), (cx + 28, cy + 44)],
              fill=RED)
    d.text((x + 12, y + h - 26), "LANDFALL: ODISHA", font=F_ART_L,
           fill=(30, 90, 160))

def art_chart(d, x, y, w, h, label_top, label_bot, points, lo, hi, color):
    """Generic price line: points = [(frac, price), ...]."""
    d.rectangle([x, y, x + w, y + h], fill=(232, 240, 232))
    gx, gy, gw, gh = x + 30, y + 18, w - 44, h - 54
    d.rectangle([gx, gy, gx + gw, gy + gh], outline=(180, 180, 180))
    def P(frac, price):
        return (gx + frac * gw, gy + gh - (price - lo) / (hi - lo) * gh)
    prev = None
    for frac, price in points:
        p = P(frac, price)
        if prev:
            d.line([prev, p], fill=color, width=3)
        prev = p
    p0 = P(*points[0])
    p1 = P(*points[-1])
    d.ellipse([p0[0] - 4, p0[1] - 4, p0[0] + 4, p0[1] + 4], fill=color)
    d.ellipse([p1[0] - 4, p1[1] - 4, p1[0] + 4, p1[1] + 4], fill=RED)
    d.text((gx, y + 2), label_top, font=F_ART_L, fill=color)
    d.text((x + w - tw(d, label_bot, F_ART_L) - 8, y + h - 24), label_bot,
           font=F_ART_L, fill=RED)

def art_anthropic(d, x, y, w, h):
    """Day-2 fade: open $89.86 -> low $83.05 -> close $88.91.
    Only verified points are plotted; Thu close $97.17 is a dashed line."""
    art_chart(d, x, y, w, h, "OPEN $89.86", ANT_CLOSE_LABEL,
              ANT_POINTS, ANT_LO, ANT_HI, RED)
    gx, gy, gw, gh = x + 30, y + 18, w - 44, h - 54
    y97 = gy + gh - (97.17 - ANT_LO) / (ANT_HI - ANT_LO) * gh
    for px in range(gx, gx + gw, 10):
        d.line([px, y97, px + 5, y97], fill=MUTED, width=1)
    d.text((x + 4, y97 - 8), "$97", font=F_ART_L, fill=MUTED)

def art_tower(d, x, y, w, h):
    """Night tower silhouette + strike streak."""
    d.rectangle([x, y, x + w, y + h], fill=(30, 40, 70))
    d.polygon([(x + w // 2 - 16, y + h), (x + w // 2 - 11, y + 8),
               (x + w // 2 + 11, y + 8), (x + w // 2 + 16, y + h)],
              fill=(200, 190, 160))
    for wy in range(y + 12, y + h - 4, 6):
        d.rectangle([x + w // 2 - 9, wy, x + w // 2 + 9, wy + 2],
                    fill=(255, 220, 120))
    d.line([x + w - 14, y + 4, x + w // 2 + 8, y + 18], fill=(255, 120, 40),
           width=3)
    d.ellipse([x + w // 2 + 2, y + 12, x + w // 2 + 14, y + 24],
              fill=(255, 180, 60))
    d.text((x + 12, y + h - 26), "PIF TOWER HIT", font=F_ART_L,
           fill=(255, 200, 120))

def art_cop(d, x, y, w, h):
    """Draft document with the fossil-fuel line struck out."""
    d.rectangle([x, y, x + w, y + h], fill=(225, 240, 225))
    d.rectangle([x + 18, y + 8, x + w - 18, y + h - 30], fill=WHITE,
                outline=(150, 150, 150))
    for i in range(5):
        ly = y + 22 + i * 12
        ln_w = w - 60 - (i % 2) * 20
        d.line([x + 26, ly, x + 26 + ln_w, ly], fill=(190, 190, 190), width=2)
    t = "PHASE OUT FOSSIL FUELS"
    d.text((x + (w - tw(d, t, F_ART_L)) / 2, y + 30), t, font=F_ART_L,
           fill=(150, 150, 150))
    d.line([x + 24, y + 34, x + w - 24, y + 34], fill=RED, width=3)
    d.text((x + 12, y + h - 26), "CUT FROM THE DRAFT", font=F_ART_L,
           fill=DARKRED)

def art_poland(d, x, y, w, h):
    """SE Poland map: three impact markers + jets scrambled."""
    d.rectangle([x, y, x + w, y + h], fill=(228, 236, 228))
    # Ukraine border (right edge)
    d.line([x + w - 26, y + 6, x + w - 18, y + h - 30], fill=(150, 150, 150),
           width=2)
    d.text((x + w - 24, y + h - 44), "UA", font=F_ART_L, fill=MUTED)
    # three impact points (burst markers)
    for cx, cy in [(x + 52, y + 30), (x + 92, y + 58), (x + 122, y + 34)]:
        for dx, dy in [(0, -6), (0, 6), (-6, 0), (6, 0)]:
            d.line([cx, cy, cx + dx, cy + dy], fill=(230, 80, 20), width=2)
        d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(255, 200, 40))
    # jets scrambled (two small triangles, top-left)
    for jx, jy in [(x + 14, y + 16), (x + 30, y + 10)]:
        d.polygon([(jx, jy - 6), (jx + 10, jy + 4), (jx - 2, jy + 4)],
                  fill=NAVY)
    d.text((x + 12, y + h - 26), "2 MISSILES + 1 DRONE", font=F_ART_L,
           fill=DARKRED)

FEATURE_ART = {"kyiv": art_kyiv, "akvan": art_akvan,
               "anthropic": art_anthropic, "tower": art_tower,
               "cop": art_cop, "poland": art_poland}

# ---------------------------------------------------------------- medium strips
def strip(d, x, y, w, h, bg):
    d.rectangle([x, y, x + w, y + h], fill=bg)

def s_bridge(d, x, y, w, h):
    strip(d, x, y, w, h, (200, 220, 235))
    d.rectangle([x, y + h - 10, x + w, y + h], fill=(70, 120, 180))
    d.line([x + 8, y + h - 12, x + w // 2, y + 6, x + w - 8, y + h - 12],
           fill=(90, 90, 90), width=3)
    d.line([x, y + h - 12, x + w, y + h - 12], fill=(90, 90, 90), width=2)
    cx, cy = x + w // 2, y + 8
    for dx, dy in [(0, -7), (0, 7), (-7, 0), (7, 0)]:
        d.line([cx, cy, cx + dx, cy + dy], fill=(230, 80, 20), width=2)
    d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(255, 200, 40))

def s_cyclone(d, x, y, w, h):
    strip(d, x, y, w, h, (210, 230, 240))
    cx, cy = x + w // 2, y + 13
    for r, a0, a1 in [(11, 200, 340), (8, 20, 160), (5, 180, 320)]:
        d.arc([cx - r, cy - r, cx + r, cy + r], a0, a1, fill=(30, 90, 160),
              width=2)
    d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(30, 90, 160))
    d.text((x + 6, y + 3), "LANDFALL", font=F_ART_L, fill=(30, 90, 160))

def s_chart_down(d, x, y, w, h):
    strip(d, x, y, w, h, (240, 228, 228))
    pts = [(0.05, 0.25), (0.3, 0.35), (0.55, 0.55), (0.8, 0.7), (0.97, 0.85)]
    prev = None
    for fx, fy in pts:
        p = (x + fx * w, y + fy * h)
        if prev:
            d.line([prev, p], fill=RED, width=3)
        prev = p
    d.text((x + 6, y + 3), "DOWN", font=F_ART_L, fill=RED)

def s_gavel(d, x, y, w, h):
    strip(d, x, y, w, h, (238, 232, 220))
    d.rectangle([x + 20, y + 5, x + 62, y + 11], fill=(140, 100, 60))
    d.rectangle([x + 38, y + 11, x + 44, y + 20], fill=(140, 100, 60))
    d.rectangle([x + 26, y + 20, x + 56, y + 23], fill=(120, 85, 50))
    d.text((x + w - tw(d, "RULED", F_ART_L) - 8, y + 7), "RULED",
           font=F_ART_L, fill=DARKRED)

def s_tower(d, x, y, w, h):
    strip(d, x, y, w, h, (30, 40, 70))
    d.polygon([(x + w // 2 - 14, y + h), (x + w // 2 - 10, y + 6),
               (x + w // 2 + 10, y + 6), (x + w // 2 + 14, y + h)],
              fill=(200, 190, 160))
    for wy in range(y + 10, y + h - 4, 6):
        d.rectangle([x + w // 2 - 8, wy, x + w // 2 + 8, wy + 2],
                    fill=(255, 220, 120))
    d.line([x + w - 12, y + 2, x + w // 2 + 6, y + 14], fill=(255, 120, 40),
           width=3)
    d.ellipse([x + w // 2 + 2, y + 10, x + w // 2 + 12, y + 20],
              fill=(255, 180, 60))

def s_crowd(d, x, y, w, h):
    strip(d, x, y, w, h, (235, 230, 215))
    cols = [(200, 60, 60), (60, 120, 200), (60, 160, 90), (220, 150, 40),
            (150, 90, 200)]
    for i in range(9):
        cx = x + 12 + i * ((w - 24) // 8)
        c = cols[i % len(cols)]
        d.ellipse([cx - 4, y + 3, cx + 4, y + 11], fill=c)
        d.rectangle([cx - 5, y + 12, cx + 5, y + h - 2], fill=c)

def s_bars(d, x, y, w, h):
    """Bar chart — for a statistics release."""
    strip(d, x, y, w, h, (235, 235, 240))
    for i, bh in enumerate([8, 12, 10, 16, 20, 14]):
        bx = x + 14 + i * 18
        d.rectangle([bx, y + h - 4 - bh, bx + 12, y + h - 4],
                    fill=(150, 60, 60))

def s_doc(d, x, y, w, h):
    strip(d, x, y, w, h, (225, 240, 225))
    d.rectangle([x + 10, y + 3, x + w - 10, y + h - 3], fill=WHITE,
                outline=(150, 150, 150))
    for i in range(3):
        ly = y + 8 + i * 6
        d.line([x + 16, ly, x + w - 16, ly], fill=(190, 190, 190), width=2)
    d.line([x + 14, y + 9, x + w - 14, y + 9], fill=RED, width=2)

def s_flame(d, x, y, w, h):
    strip(d, x, y, w, h, (250, 235, 210))
    d.rectangle([x + 12, y + 8, x + 34, y + h - 6], fill=(180, 120, 40))
    cx, cy = x + 58, y + h - 8
    d.polygon([(cx - 10, cy), (cx - 4, cy - 18), (cx, cy - 10),
               (cx + 4, cy - 22), (cx + 10, cy)], fill=(240, 120, 20))
    d.text((x + 76, y + 8), "ENERGY", font=F_ART_L, fill=(150, 80, 10))

def s_plane(d, x, y, w, h):
    strip(d, x, y, w, h, (220, 235, 245))
    cx, cy = x + w // 2, y + h // 2
    d.polygon([(cx - 40, cy), (cx + 40, cy - 6), (cx + 52, cy),
               (cx + 40, cy + 6)], fill=(70, 110, 160))
    d.polygon([(cx - 6, cy - 2), (cx + 6, cy - 12), (cx + 14, cy - 12),
               (cx + 8, cy - 2)], fill=(70, 110, 160))
    d.line([x + 8, y + h - 4, x + w - 8, y + h - 4], fill=RED, width=3)
    d.text((x + 6, y + 3), "GROUNDED", font=F_ART_L, fill=DARKRED)

def s_virus(d, x, y, w, h):
    strip(d, x, y, w, h, (230, 245, 235))
    cx, cy = x + 30, y + 12
    for ang in range(0, 360, 45):
        import math
        dx = math.cos(math.radians(ang)) * 9
        dy = math.sin(math.radians(ang)) * 9
        d.line([cx, cy, cx + dx, cy + dy], fill=(60, 140, 80), width=2)
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(60, 140, 80))
    d.text((x + 52, y + 3), "42 DAYS TO GO", font=F_ART_L, fill=(40, 110, 60))

def s_ballot(d, x, y, w, h):
    strip(d, x, y, w, h, (235, 232, 245))
    d.rectangle([x + 12, y + 6, x + 44, y + h - 4], fill=WHITE,
                outline=(120, 120, 160))
    d.line([x + 18, y + 14, x + 26, y + 20], fill=GREEN, width=3)
    d.line([x + 26, y + 20, x + 38, y + 8], fill=GREEN, width=3)
    d.text((x + 52, y + 7), "VOTED", font=F_ART_L, fill=NAVY)

def s_ship(d, x, y, w, h):
    strip(d, x, y, w, h, (210, 230, 240))
    d.rectangle([x, y + h - 8, x + w, y + h], fill=(70, 120, 180))
    d.polygon([(x + 30, y + h - 8), (x + w - 30, y + h - 8),
               (x + w - 44, y + h - 16), (x + 44, y + h - 16)],
              fill=(120, 90, 60))
    d.rectangle([x + w // 2 - 4, y + 4, x + w // 2 + 4, y + h - 16],
                fill=(90, 90, 90))
    cx, cy = x + w - 30, y + 6
    d.polygon([(cx - 6, cy + 6), (cx, cy - 6), (cx + 6, cy + 6)],
              fill=(240, 120, 20))

def s_chip(d, x, y, w, h):
    strip(d, x, y, w, h, (235, 240, 235))
    d.rectangle([x + 14, y + 5, x + 46, y + h - 5], fill=(60, 60, 60))
    d.rectangle([x + 20, y + 10, x + 40, y + h - 10], fill=(120, 200, 120))
    for px in (20, 30, 40):
        d.line([x + px, y + 2, x + px, y + 5], fill=(60, 60, 60), width=2)
        d.line([x + px, y + h - 5, x + px, y + h - 2], fill=(60, 60, 60),
               width=2)
    d.text((x + 54, y + 3), "SEC PROBE", font=F_ART_L, fill=DARKRED)
    d.text((x + 54, y + 14), "-14%", font=F_ART_N, fill=RED)

def s_game(d, x, y, w, h):
    strip(d, x, y, w, h, (40, 20, 70))
    for bx, bw, bh in [(6, 22, 18), (32, 16, 24), (52, 26, 14), (82, 18, 22),
                       (104, 24, 16), (132, 16, 20)]:
        d.rectangle([x + bx, y + h - bh, x + bx + bw, y + h],
                    fill=(90, 60, 140))
    d.ellipse([x + w - 34, y + 4, x + w - 12, y + 26], fill=(255, 150, 80))
    d.text((x + 8, y + 4), "VI", font=F_ART_N, fill=(255, 220, 90))
    d.text((x + 34, y + 7), "$3.79BN", font=F_ART_L, fill=WHITE)

def s_quake(d, x, y, w, h):
    strip(d, x, y, w, h, (240, 235, 220))
    d.line([x + 8, y + h - 8, x + w - 8, y + h - 8], fill=(120, 100, 70),
           width=2)
    # jagged crack
    pts = [(x + w // 2 - 30, y + h - 8), (x + w // 2 - 18, y + 12),
           (x + w // 2 - 6, y + h - 14), (x + w // 2 + 8, y + 8),
           (x + w // 2 + 22, y + h - 10)]
    d.line(pts, fill=(150, 80, 40), width=2)
    d.text((x + 8, y + 3), "M6.7", font=F_ART_N, fill=DARKRED)

def s_cricket(d, x, y, w, h):
    strip(d, x, y, w, h, (225, 240, 220))
    d.rectangle([x, y + h - 8, x + w, y + h], fill=(90, 160, 90))
    # stumps
    for sx in (x + 20, x + 26, x + 32):
        d.line([sx, y + h - 18, sx, y + h - 8], fill=(220, 180, 80), width=2)
    # bat
    d.line([x + 60, y + 4, x + 78, y + h - 10], fill=(180, 140, 90), width=4)
    d.ellipse([x + 100, y + 4, x + 108, y + 12], fill=RED)
    d.text((x + w - 52, y + 8), "175*", font=F_ART_N, fill=NAVY)

def s_soccer(d, x, y, w, h):
    strip(d, x, y, w, h, (225, 240, 225))
    d.rectangle([x, y + h - 6, x + w, y + h], fill=(90, 160, 90))
    cx, cy = x + 30, y + 12
    d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=WHITE,
              outline=(60, 60, 60))
    d.polygon([(cx - 3, cy - 3), (cx + 3, cy - 3), (cx + 4, cy + 2),
               (cx, cy + 5), (cx - 4, cy + 2)], fill=(60, 60, 60))
    d.text((x + 48, y + 3), "986 GOALS", font=F_ART_L, fill=NAVY)
    d.text((x + 48, y + 14), "3–1", font=F_ART_N, fill=DARKRED)

def s_planet(d, x, y, w, h):
    strip(d, x, y, w, h, (20, 25, 45))
    d.ellipse([x + 14, y + 2, x + 38, y + 26], fill=(200, 170, 130))
    d.ellipse([x + 20, y + 8, x + 26, y + 14], fill=(170, 140, 105))
    d.ellipse([x + 28, y + 16, x + 33, y + 21], fill=(170, 140, 105))
    # probe + path
    d.line([x + 48, y + 20, x + w - 20, y + 6], fill=(150, 200, 255), width=2)
    d.rectangle([x + w - 24, y + 2, x + w - 14, y + 10], fill=(220, 220, 220))
    d.text((x + 48, y + 12), "8 YEARS", font=F_ART_L, fill=(180, 210, 255))

def s_rain(d, x, y, w, h):
    strip(d, x, y, w, h, (215, 230, 240))
    d.ellipse([x + 10, y + 2, x + 40, y + 14], fill=(120, 140, 160))
    d.ellipse([x + 26, y + 0, x + 52, y + 12], fill=(140, 160, 180))
    for rx in (16, 26, 36, 46):
        d.line([x + rx, y + 15, x + rx - 3, y + 23], fill=(60, 110, 180),
               width=2)
    d.text((x + 60, y + 3), "RECORD RAIN", font=F_ART_L, fill=(30, 80, 140))
    d.text((x + 60, y + 14), "17 IN", font=F_ART_N, fill=(30, 80, 140))

def s_fence(d, x, y, w, h):
    strip(d, x, y, w, h, (235, 230, 215))
    for fx in range(x + 8, x + w - 8, 10):
        d.line([fx, y + 4, fx, y + h - 4], fill=(120, 110, 90), width=2)
    d.line([x + 6, y + 8, x + w - 6, y + 8], fill=(120, 110, 90), width=2)
    d.line([x + 6, y + h - 8, x + w - 6, y + h - 8], fill=(120, 110, 90),
           width=2)
    d.text((x + w - 52, y + 9), "6 MONTHS", font=F_ART_L, fill=DARKRED)

def s_tokyo(d, x, y, w, h):
    strip(d, x, y, w, h, (240, 230, 230))
    # torii gate
    d.rectangle([x + 12, y + 4, x + 44, y + 8], fill=RED)
    d.rectangle([x + 16, y + 8, x + 20, y + h - 4], fill=RED)
    d.rectangle([x + 36, y + 8, x + 40, y + h - 4], fill=RED)
    d.rectangle([x + 16, y + 14, x + 40, y + 17], fill=RED)
    d.text((x + 52, y + 3), "NIKKEI", font=F_ART_L, fill=DARKRED)
    d.text((x + 52, y + 14), "-5.06%", font=F_ART_N, fill=RED)

MEDIUM_ART = {"bridge": s_bridge, "cyclone": s_cyclone,
              "chart_down": s_chart_down, "gavel": s_gavel,
              "tower": s_tower, "crowd": s_crowd, "doc": s_doc,
              "flame": s_flame, "plane": s_plane, "virus": s_virus,
              "ballot": s_ballot, "ship": s_ship, "chip": s_chip,
              "game": s_game, "quake": s_quake, "cricket": s_cricket,
              "soccer": s_soccer, "planet": s_planet, "rain": s_rain,
              "fence": s_fence, "tokyo": s_tokyo, "bars": s_bars}

# ---------------------------------------------------------------- data
# All figures from the four verification logs (verify-regions.md,
# verify-markets.md, verify-misc.md, verify-features.md): every story
# CONFIRMED by 2+ independent sources dated 20 Nov 2026.
# Slate: 4 features + 12 mediums + 16 briefs = 32 stories.
# Regions: ASIA 5, EUROPE 6, MIDEAST 4, AFRICA 4, AMERICAS 8,
# OCEANIA 2, GLOBAL 3 — no region above 30%, all at 2 or more.
REGIONS = [("ASIA", 5), ("EUROPE", 6), ("MIDEAST", 4), ("AFRICA", 4),
           ("AMERICAS", 8), ("OCEANIA", 2), ("GLOBAL", 3)]

STATS = [
    ("3", "Kyiv bridges hit"),
    ("372,000", "evacuated, Akvan"),
    ("-8.5%", "Anthropic, day 2"),
    ("-3.7%", "S&P 500, 7th loss"),
    ("$3.79bn", "GTA VI, day one"),
    ("M6.7", "Peru quake"),
]

TIMELINE = [
    [("00:13", "Japan CPI 2.2%, a 2026 high"),
     ("00:40", "Missiles land in Poland"),
     ("02:00", "Akvan landfall, Odisha"),
     ("06:00", "Nikkei closes -5.06%"),
     ],
    [("15:00", "Tanker struck off Oman"),
     ("17:49", "Anthropic low $83.05"),
     ("21:00", "Wall St closes in correction"),
     ],
]

FEATURES = [
    dict(tag="WAR IN UKRAINE", num="1",
         head="Russia smashes three Kyiv bridges",
         deck="Largest strike package of November: 27 ballistic + 84 "
              "cruise missiles + 404 drones; 8 killed, 28 injured. "
              "Power and water hit in Kyiv.",
         art="kyiv", src="Reuters · AP · ISW"),
    dict(tag="NATO SOIL", num="2",
         head="Russian missiles land in Poland",
         deck="Two missiles and a drone come down in the south-east; "
              "NATO calls it a 'grave violation'. No casualties.",
         art="poland", src="AP · ISW"),
    dict(tag="CYCLONE AKVAN", num="3",
         head="Cyclone Akvan hits Odisha, weaker than feared",
         deck="Landfall near Gopalpur at dawn, winds 70-80 km/h; 372,000 "
              "evacuated, no deaths reported. Patrapur sees 209 mm of rain.",
         art="akvan", src="IMD · Reuters"),
    dict(tag="THE AI ROUT", num="4",
         head="Anthropic sinks 8.5% on day two",
         deck="Closes $88.91 after touching $83.05 - five cents above its "
              "IPO price - as the AI selloff deepens across markets.",
         art="anthropic", src="Finnhub · Reuters"),
]

MEDIUMS = [
    dict(tag="MARKETS", head="Wall Street enters correction",
         deck="S&P 500 falls 3.7% in its seventh straight loss; Nasdaq "
              "plunges 5.3%, erasing its 2026 gains.",
         art="chart_down"),
    dict(tag="MARKETS", head="Nikkei plunges 5.06% in its fifth-worst day",
         deck="Kospi -5.2%, Taiwan -6.2% as the AI rout sweeps Asia.",
         art="tokyo"),
    dict(tag="TECH", head="Nvidia plunges 14% on SEC probe report",
         deck="Worst day since the DeepSeek selloff; SEC is examining "
              "accounting issues.",
         art="chip"),
    dict(tag="CLIMATE", head="COP31 slips into overtime with no deal",
         deck="Talks miss the 3pm deadline; a third draft is due Saturday.",
         art="doc"),
    dict(tag="EUROPE", head="EU-UK summit: food checks scrapped",
         deck="Carbon markets linked; youth scheme opens for 100,000.",
         art="ballot"),
    dict(tag="RED SEA", head="Saudi coalition bombs Hodeidah port",
         deck="Strikes on Hodeidah and Sanaa a day after the PIF Tower "
              "hit; intercepts reported.",
         art="flame"),
    dict(tag="BORDERS", head="Estonia seals its Russia border",
         deck="Formal decision: all five road crossings shut from 1 Dec "
              "for at least six months.",
         art="fence"),
    dict(tag="HORMUZ", head="Tanker set ablaze off Oman",
         deck="Projectile strike 8 nm north of Khasab; no casualties. A "
              "new incident, not last week's.",
         art="ship"),
    dict(tag="GAMING", head="GTA VI banks $3.79bn on day one",
         deck="Announced Friday: biggest entertainment launch ever; "
              "32.5m copies pre-sold.",
         art="game"),
    dict(tag="AFRICA", head="South Africa: 5,590 murders in a quarter",
         deck="Police release Jul-Sep figures: ~60 a day; 581 women, "
              "4,362 child rape victims.",
         art="bars"),
    dict(tag="CRICKET", head="Nicholls' 175* lifts New Zealand to 368",
         deck="Phillips adds 118; Jaiswal's 85 takes India to 159/1.",
         art="cricket"),
    dict(tag="QUAKE", head="Peru rocked by M6.7 quake",
         deck="Deep quake rattles the Andes; felt in Lima, no casualties "
              "reported.",
         art="quake"),
]

BRIEFS = [
    ("Space", "BepiColombo at Mercury; orbit insertion Sat."),
    ("Florida", "Record floods; river beats 1953 crest."),
    ("Football", "Ronaldo scores No. 986; Al-Ahli win 3-1."),
    ("Bundesliga", "Bayern 1-1 Koln; Kane injures ankle."),
    ("California", "Jury convicts Palisades Fire arsonist."),
    ("Japan", "Core CPI 2.2%, a 2026 high."),
    ("China", "Central bank holds rates for an 18th month."),
    ("Markets", "Gold -3%; bitcoin below $60,000."),
    ("Italy", "CGIL strike: a million march, union says."),
    ("Iraq", "Army enters Kataib Hezbollah stronghold."),
    ("South Africa", "First woman deputy president dies at 71."),
    ("Nigeria", "Barge capsizes; 4 dead, 24 rescued."),
    ("Kenya", "Oil drilling begins; first crude due 1 Dec."),
    ("Diplomacy", "Xi and Albanese hail a 'turnaround'."),
    ("Diplomacy", "Aus, Canada, NZ demand a ceasefire."),
    ("Washington", "Senate passes energy bill 62-33."),
]

MAP_DOTS = [
    (30.5, 50.5, "EUROPE"),    # Kyiv
    (22.0, 50.0, "EUROPE"),    # SE Poland
    (84.8, 19.1, "ASIA"),      # Gopalpur
    (-74.0, 41.0, "AMERICAS"), # New York
    (139.7, 35.7, "ASIA"),     # Tokyo
    (4.4, 50.9, "EUROPE"),     # Brussels
    (42.9, 14.8, "MIDEAST"),   # Hodeidah
    (24.7, 59.4, "EUROPE"),    # Tallinn
    (56.2, 26.2, "MIDEAST"),   # Khasab
    (28.2, -25.7, "AFRICA"),   # Pretoria
    (174.8, -41.3, "OCEANIA"), # Wellington
    (-75.5, -11.2, "AMERICAS"),# Junin, Peru
    (30.7, 36.9, "GLOBAL"),    # Antalya
    (46.7, 24.7, "MIDEAST"),   # Riyadh
    (11.6, 48.1, "EUROPE"),    # Munich
    (-80.8, 28.1, "AMERICAS"), # Melbourne, Florida
    (6.1, 4.8, "AFRICA"),      # Bayelsa
    (35.7, 3.5, "AFRICA"),     # Turkana
    (44.2, 32.9, "MIDEAST"),   # Jurf al-Sakhar
    (114.1, 22.5, "ASIA"),     # Shenzhen
    (149.1, -35.3, "OCEANIA"), # Canberra
    (116.4, 39.9, "ASIA"),     # Beijing
    (12.5, 41.9, "EUROPE"),    # Rome
    (-77.0, 39.0, "AMERICAS"), # Washington
    (-118.5, 34.0, "AMERICAS"),# Los Angeles
]

DATECHECK_BODY = ("Every story here happened, or was first reported, on "
                  "Friday 20 November 2026. LEFT OUT AS OTHER DAYS' NEWS: "
                  "Shenzhen summit (Thu) · ICJ verdict 9-6 (Thu) · "
                  "Anthropic debut $97.17 (Thu) · GTA VI launch (Thu) · "
                  "PIF Tower strike (Thu) · COP31 draft cut (Thu) · Kenya "
                  "Ebola discharge (11 Nov).")

FOOTER_SOURCES = ("Sources: Reuters, AP, AFP, BBC, IMD, ISW, Finnhub, "
                  "CNN, UKMTO, SAPS, Nature Astronomy.")
KICKER = ("Russia smashes three Kyiv bridges · Missiles land in Poland · "
          "Anthropic sinks 8.5% on day two")

# Anthropic day-2 chart (verified: open $89.86, low $83.05, close $88.91)
ANT_CLOSE_LABEL = "CLOSE $88.91  -8.5%"
ANT_POINTS = [(0.02, 89.86), (0.55, 83.05), (0.98, 88.91)]
ANT_LO, ANT_HI = 80, 100

# ---------------------------------------------------------------- zones
def draw_masthead(d, story_count):
    """Top kicker, date-led masthead, calendar box, red kicker line."""
    d.text((MARGIN, 6), "THE WORLD TODAY", font=F_TOP, fill=INK)
    r = f"{story_count} STORIES  ·  7 REGIONS  ·  ONE DAY"
    d.text((W - MARGIN - tw(d, r, F_TOP), 6), r, font=F_TOP, fill=MUTED)
    d.line([MARGIN, 24, W - MARGIN, 24], fill=RULE, width=1)
    d.text((MARGIN, 24), "Friday 20 November 2026", font=F_DATE, fill=INK)
    bx, by, bw, bh = W - MARGIN - 64, 24, 64, 60
    d.rectangle([bx, by, bx + bw, by + bh], outline=RED, width=2)
    d.rectangle([bx, by, bx + bw, by + 18], fill=RED)
    t = "NOVEMBER"
    d.text((bx + (bw - tw(d, t, F_CAL_M)) / 2, by + 2), t, font=F_CAL_M,
           fill=WHITE)
    t = "20"
    d.text((bx + (bw - tw(d, t, F_CAL_D)) / 2, by + 18), t, font=F_CAL_D,
           fill=INK)
    t = "FRIDAY"
    d.text((bx + (bw - tw(d, t, F_CAL_W)) / 2, by + 48), t, font=F_CAL_W,
           fill=MUTED)
    d.text((MARGIN, 74), KICKER, font=F_KICK, fill=DARKRED)
    d.line([MARGIN, 90, W - MARGIN, 90], fill=INK, width=2)
    return 92

def draw_region_bar(d, y):
    """Coloured segments with story counts per region."""
    total_w = W - 2 * MARGIN
    seg_w = total_w / len(REGIONS)
    for i, (name, n) in enumerate(REGIONS):
        x0 = MARGIN + i * seg_w
        c = REGION_COLORS[name]
        d.rectangle([x0, y, x0 + seg_w - 2, y + 16], fill=c)
        t = f"{name} {n}"
        d.text((x0 + (seg_w - 2 - tw(d, t, F_REG)) / 2, y + 2), t,
               font=F_REG, fill=WHITE)
    return y + 18

def draw_stat_band(d, y):
    """Six headline numbers."""
    total_w = W - 2 * MARGIN
    cell = total_w / len(STATS)
    for i, (num, lbl) in enumerate(STATS):
        x0 = MARGIN + i * cell
        d.text((x0 + 4, y), num, font=F_STAT_N, fill=RED)
        d.text((x0 + 4, y + 22), lbl, font=F_STAT_L, fill=MUTED)
        if i:
            d.line([x0, y + 2, x0, y + 32], fill=RULE, width=1)
    d.line([MARGIN, y + 36, W - MARGIN, y + 36], fill=RULE, width=1)
    return y + 40

def draw_timeline(d, y):
    """Two rows of UTC time beats."""
    label = "THE DAY IN UTC"
    d.text((MARGIN, y + 1), label, font=F_TL_LBL, fill=RED)
    lx = MARGIN + tw(d, label, F_TL_LBL) + 10
    row_h = 16
    for ri, row in enumerate(TIMELINE):
        yy = y + ri * row_h
        cx = lx if ri == 0 else MARGIN
        avail = W - MARGIN - cx
        cell = avail / len(row)
        for i, (t, txt) in enumerate(row):
            bx = cx + i * cell
            d.text((bx, yy), t, font=F_TL_T, fill=RED)
            d.text((bx + tw(d, t, F_TL_T) + 5, yy), txt, font=F_TL, fill=INK)
    d.line([MARGIN, y + 2 * row_h + 2, W - MARGIN, y + 2 * row_h + 2],
           fill=RULE, width=1)
    return y + 2 * row_h + 4

def draw_features(d, y, height):
    """2x2 features: art left, text right."""
    gap = 14
    cw = (W - 2 * MARGIN - gap) // 2
    ch = (height - gap) // 2
    art_w = 168
    for i, f in enumerate(FEATURES):
        cx = MARGIN + (i % 2) * (cw + gap)
        cy = y + (i // 2) * (ch + gap)
        d.rectangle([cx, cy, cx + cw, cy + ch], outline=RULE, width=1)
        FEATURE_ART[f["art"]](d, cx + 1, cy + 1, art_w, ch - 2)
        tx = cx + art_w + 12
        twd = cw - art_w - 20
        d.text((tx, cy + 6), f"{f['num']}  {f['tag']}", font=F_FTAG, fill=RED)
        d.text((cx + cw - 8 - tw(d, f["src"], F_ART_L), cy + 6), f["src"],
               font=F_ART_L, fill=MUTED)
        if len(wrap_text(d, f["head"], F_FHEAD, twd)) > 2:
            head_lines = fit_lines(d, f["head"], F_FHEAD_S, twd, 2)
            hf, lh = F_FHEAD_S, 24
        else:
            head_lines = fit_lines(d, f["head"], F_FHEAD, twd, 2)
            hf, lh = F_FHEAD, 26
        hy = draw_lines(d, tx, cy + 22, head_lines, hf, INK, lh)
        deck_lines = fit_lines(d, f["deck"], F_FDECK, twd, 3)
        draw_lines(d, tx, hy + 3, deck_lines, F_FDECK, (70, 70, 70), 15)
    return y + height

def draw_mediums(d, y, height):
    """4 cols x 3 rows of icon-led mediums."""
    cols, rows = 4, 3
    gap = 10
    cw = (W - 2 * MARGIN - gap * (cols - 1)) // cols
    ch = (height - gap * (rows - 1)) // rows
    for i, m in enumerate(MEDIUMS):
        cx = MARGIN + (i % cols) * (cw + gap)
        cy = y + (i // cols) * (ch + gap)
        d.rectangle([cx, cy, cx + cw, cy + ch], outline=RULE, width=1)
        MEDIUM_ART[m["art"]](d, cx + 1, cy + 1, cw - 2, 24)
        tx = cx + 8
        twd = cw - 16
        d.text((tx, cy + 28), f"{i + 5}  {m['tag']}", font=F_MTAG, fill=RED)
        head_lines = fit_lines(d, m["head"], F_MHEAD, twd, 2)
        hy = draw_lines(d, tx, cy + 40, head_lines, F_MHEAD, INK, 17)
        deck_lines = fit_lines(d, m["deck"], F_MDECK, twd, 2)
        draw_lines(d, tx, hy + 2, deck_lines, F_MDECK, (70, 70, 70), 11)
    return y + height

def draw_map_briefs(d, y, height):
    """Map left; briefs in 2 columns right."""
    map_w = 320
    d.text((MARGIN, y), "WHERE IT HAPPENED", font=F_SEC, fill=INK)
    draw_map(d, MARGIN, y + 18, map_w, height - 36, MAP_DOTS)
    d.text((MARGIN, y + height - 15),
           "Dots mark the stories — colour = region.",
           font=F_MAPCAP, fill=MUTED)
    bx = MARGIN + map_w + 16
    d.text((bx, y), "ALSO ON FRIDAY 20 NOVEMBER", font=F_SEC, fill=INK)
    bw_total = W - MARGIN - bx
    col_w = (bw_total - 14) // 2
    per_col = (len(BRIEFS) + 1) // 2
    row_h = (height - 22) // per_col
    for i, (place, text) in enumerate(BRIEFS):
        col = i // per_col
        row = i % per_col
        x0 = bx + col * (col_w + 14)
        yy = y + 20 + row * row_h
        num = f"{i + 17}"
        d.text((x0, yy), num, font=F_BRIEF_B, fill=RED)
        px = x0 + tw(d, num, F_BRIEF_B) + 5
        d.text((px, yy), place + " — ", font=F_BRIEF_B, fill=INK)
        tx = px + tw(d, place + " — ", F_BRIEF_B)
        avail = x0 + col_w - tx
        t = one_line(d, text, F_BRIEF, avail)
        d.text((tx, yy), t, font=F_BRIEF, fill=(60, 60, 60))
    return y + height

def draw_datecheck(d, y):
    """DATE CHECK in a red-ruled box."""
    h = 28
    d.rectangle([MARGIN, y, W - MARGIN, y + h], outline=RED, width=1)
    label = "DATE CHECK: "
    lx = MARGIN + 8
    d.text((lx, y + 7), label, font=F_DC, fill=RED)
    tx = lx + tw(d, label, F_DC)
    lines = fit_lines(d, DATECHECK_BODY, F_DC_T, W - MARGIN - 8 - tx, 2)
    draw_lines(d, tx, y + 2, lines, F_DC_T, INK, 12)
    return y + h + 4

def draw_footer(d, y):
    """Sources + the any-time-zone standard (2 lines)."""
    tag = "THE WORLD TODAY · 20 NOV 2026"
    d.text((MARGIN, y), FOOTER_SOURCES, font=F_FOOT, fill=MUTED)
    d.text((W - MARGIN - tw(d, tag, F_FOOT), y), tag, font=F_FOOT, fill=MUTED)
    l2 = ("Every story on this page happened, or was first reported, on "
          "Friday 20 November 2026, in any time zone. Pictures and map: "
          "original, drawn in code.")
    d.text((MARGIN, y + 13), l2, font=F_FOOT, fill=MUTED)
    return y + 26

# ---------------------------------------------------------------- main
def main():
    story_count = len(FEATURES) + len(MEDIUMS) + len(BRIEFS)
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    y = draw_masthead(d, story_count)      # -> 92
    y = draw_region_bar(d, y)              # -> 110
    y = draw_stat_band(d, y)               # -> 150
    y = draw_timeline(d, y)                # -> 186
    y = draw_features(d, y, 280)           # -> 466
    y = draw_mediums(d, y + 6, 320)        # -> 792
    y = draw_map_briefs(d, y + 6, 166)     # -> 964
    y = draw_datecheck(d, y + 2)           # -> 998
    draw_footer(d, y)                      # -> 1024
    img.save(OUT, "PNG", optimize=True)
    size = os.path.getsize(OUT)
    print(f"wrote {OUT}  {size} bytes  ({size / 1024:.0f} KB)")
    if size > 1024 * 1024:
        print("WARNING: over 1 MiB hard cap")
    elif size > 800 * 1024:
        print("note: over 800 KB target")
    for px, name in [(300, "entry_300.png"), (512, "entry_512.png")]:
        small = img.resize((px, px), Image.LANCZOS)
        small.save(os.path.join(WORK, name), "PNG", optimize=True)
        print(f"wrote {name}")

if __name__ == "__main__":
    main()
