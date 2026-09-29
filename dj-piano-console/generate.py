#!/usr/bin/env python3
"""DJ + piano console: SVG drawings and HTML/PDF spec generator. All dimensions in cm."""
import os, html as H, random, datetime, math

OUT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)

VARIANTS = {1: "gear on top (v1.7)", 2: "flush-mounted gear (v2.0)"}
_variant = os.environ.get("VARIANT", "1").strip()
if _variant not in {str(k) for k in VARIANTS}:
    raise SystemExit("generate.py: VARIANT=%r is not one of this package's variants. Valid values: %s."
                     % (_variant, "; ".join(f"{k} = {v}" for k, v in sorted(VARIANTS.items()))))
VARIANT = int(_variant)
SUFFIX = "" if VARIANT == 1 else f"-v{VARIANT}"

# ---------------- parameters (cm) ----------------
T = 1.8; TT = 3.0
W = 185.0; D = 50.0
H_TOP = 100.0; H_WING = 130.0
WING_W = 20.0; CAP_W = 20.0                # cap flush with the column: 20 cm is enough for a KRK Rokit 5 (18.5 wide)
BAY_W = W - 2 * WING_W                    # 145
X_BAY0, X_BAY1 = WING_W, W - WING_W       # 14.5 .. 159.5
RECESS_H = 20.0
Z_BOT_TOP = RECESS_H + T                  # 21.8
Z_TRAY_TOP = 63.0; TRAY_T = 1.8
Z_TRAY_UNDER = Z_TRAY_TOP - TRAY_T        # 61.2
APRON_UP = 5.0; APRON_H = APRON_UP + TRAY_T   # 6.8
Z_CAV_TOP = 80.0; Z_FIX_TOP = Z_CAV_TOP + T   # 81.8
Z_TOP_UNDER = H_TOP - TT                  # 97
Z_CAP_UNDER = H_WING - TT                 # 127
WING_PLINTH_H = 6.0; Z_WBOT_TOP = WING_PLINTH_H + T   # 7.8
WING_INT_H = Z_CAP_UNDER - Z_WBOT_TOP     # 119.2
WING_OPEN = (WING_INT_H - 2 * T) / 3      # 38.53
WING_INT_W = WING_W - 2 * T               # 16.4
REC_PER = int(WING_INT_W // 0.6)          # records per opening at 6 mm per sleeve
REC_TOTAL = int(round(REC_PER * 6, -1))   # six openings
REC_TOTAL_S = int(round(int(WING_INT_W // 0.5) * 6, -1))  # if mostly single sleeves
CAP_OVER = CAP_W - WING_W                 # inward overhang of the speaker cap
BACK_INSET = 5.0
Y_BACK0 = D - BACK_INSET - T              # 43.2
Y_BACK1 = D - BACK_INSET                  # 45.0
INT_D = Y_BACK0
TRAY_D = 42.0; SLIDE_LEN, SLIDE_T, SLIDE_H = 40.0, 1.9, 5.0
TRAY_W = BAY_W - 2 * SLIDE_T              # 141.2 incl. aprons
TRAY_PANEL_W = TRAY_W - 2 * T             # 137.6
KB_W, KB_D, KB_H = 133.0, 35.0, 12.0
KB_X = X_BAY0 + (BAY_W - KB_W) / 2        # 20.5
KB_CLEAR = KB_X - (X_BAY0 + SLIDE_T + T)  # 2.3
KB_Y = 1.0; EXT = 40.0
SLOT_Y0, SLOT_Y1 = 41.0, 47.0                 # 6 cm wide: passes XDJ-700 brick, Schuko and IEC plugs
SLOT_X0, SLOT_X1 = X_BAY0 + 15, X_BAY1 - 15
DIV_T = T; OPEN_W = (BAY_W - DIV_T) / 2   # 71.6
DRW_H = Z_TOP_UNDER - Z_FIX_TOP           # 15.2
NICHE_W = 24.0                            # power niche between the drawers
DRW_W = (BAY_W - NICHE_W - 2 * T) / 2     # 58.7
NICHE_X = X_BAY0 + DRW_W + T
NICHE_CUT_Z0, NICHE_CUT_H = 83.0, 12.0    # back panel cutout behind the niche
GAP = 0.2
SPK_W, SPK_D, SPK_H = 18.0, 24.0, 29.0
SPK_Y = D - 3 - SPK_D                     # 23
SHELF_UP = 19.5                           # default adjustable shelf position in right compartment
CUT_Z0, CUT_H, CUT_W = 66.0, 8.0, 20.0    # cable cutout in back panel
GEAR = [("Turntable", 45.3, 35.3, 16.2), ("XDJ-700", 21.8, 30.6, 11.1),
        ("Xone:92", 32.0, 35.8, 10.7), ("XDJ-700", 21.8, 30.6, 11.1)]
GEAR_MARGIN, GEAR_GAP, GEAR_Y = 3.0, 6.0, 2.0

# ---------------- v2: flush-mounted gear ----------------
WELL_DROP = 9.0                           # clearance the hardware needs below the surface
Z_WELL_FLOOR = H_TOP - WELL_DROP          # 91.0
FASCIA_H = Z_TOP_UNDER - Z_WELL_FLOOR     # 6.0 -> apparent slab TT + FASCIA_H = 9.0
WELL_CLEAR = 0.2                          # cut-out clearance per side
WELL_CLEAT = 1.4                          # well floor cleat: 20 wide x 14 high, two per well, front to back
WELL_SLOT_W = 12.0                        # cable notch in each player well's rear wall
BOOK_SETBACK = 10.0                       # v1.7: seated shin clearance. 15 (v2) would leave 28.2 and lose the LP
                                          # sleeve, because v1 keeps the 5 cm chase and so only has 43.2 inside
WALL_GAP = 0.0                            # v1: back panel inset 5, so the piece can stand against the wall
if VARIANT == 2:
    GEAR_Y = 5.0                          # front rail, was 2.0
    BACK_INSET = 0.0                      # back panel moves to the rear face
    Y_BACK0 = D - BACK_INSET - T          # 48.2
    Y_BACK1 = D - BACK_INSET              # 50.0
    INT_D = Y_BACK0                       # 48.2
    Z_CAV_TOP = 78.2                      # mid panel drops 18 mm so the well floor gets its own band
    Z_FIX_TOP = Z_CAV_TOP + T             # 80.0, was 81.8
    DRW_H = Z_WELL_FLOOR - T - Z_FIX_TOP  # 9.2, measured to the well floor's underside at 89.2
    BOOK_SETBACK = 15.0                   # seated shin clearance; see the spec
    WALL_GAP = 5.0                        # mandatory in v2: the trough's open rear vents and the leads exit through it
# v2: the 18 mm well floor sits 89.2 -> 91, so the drawer band stops under it, not at it
Z_DRW_TOP = Z_WELL_FLOOR - T if VARIANT == 2 else Z_TOP_UNDER
Z_BACK_TOP = Z_WELL_FLOOR if VARIANT == 2 else Z_TOP_UNDER   # v2: back panel stops at the trough, opening its rear face
WELL_WALL_H = Z_TOP_UNDER - Z_DRW_TOP     # 7.8: well side walls reach the floor's underside to carry the cleats
FASCIA_D = GEAR_Y                         # v2: the fascia fills the front rail under the top board, as both sections draw it
# v2: the well floor eats 18 mm off the drawer band, so the fronts are made taller than their boxes
# and run up to the fascia's bottom edge at 91. Nothing else is available to close that strip: the
# well floors start GEAR_Y back from the front plane, so the band from 89.2 to 91 is empty at the face.
Z_FRONT_TOP = Z_WELL_FLOOR if VARIANT == 2 else Z_DRW_TOP    # top edge of the drawer fronts and the niche door
FRONT_H = Z_FRONT_TOP - Z_FIX_TOP         # 11.0 in v2 on a 9.2 box; = DRW_H (15.2) in v1
BOOK_D = INT_D - BOOK_SETBACK             # 33.2 in both: v1 43.2 - 10.0, v2 48.2 - 15.0
# Shelf-pin rows are set out from the book compartment's own front and back faces, never from the
# carcass front: the compartment starts BOOK_SETBACK back, so on the bay side walls (which do run
# to the front face) the front row lands BOOK_SETBACK further back than the inset alone implies.
PIN_PITCH = 3.2                           # 32 mm system hole pitch
PIN_INSET = 3.7                           # 37 mm in from each face of the compartment
PIN_ROW_FRONT = BOOK_SETBACK + PIN_INSET  # from the console's front face: v1 13.7, v2 18.7
PIN_ROW_BACK = INT_D - PIN_INSET          # from the console's front face: v1 39.5, v2 44.5
PIN_ROW_GAP = PIN_ROW_BACK - PIN_ROW_FRONT  # 25.8 in both variants
# The niche door is the one flush-inset face that is not gapped evenly: the bottom edge gives up
# a whole centimetre to the vent the strip and bricks breathe through, so it loses NICHE_VENT + GAP
# off the opening, not 2 * GAP like the drawer fronts beside it.
NICHE_VENT = 1.0                          # vent gap along the door's bottom edge
NICHE_DOOR_H = FRONT_H - NICHE_VENT - GAP # v1 14.0 in a 15.2 opening, v2 9.8 in an 11.0 opening
NICHE_CUT_H_EFF = min(NICHE_CUT_H, Z_BACK_TOP - NICHE_CUT_Z0)   # v2: the panel's top edge at 91 clips the 12 cm cutout to 8

def gear_positions():
    x = X_BAY0 + GEAR_MARGIN; out = []
    for n, w, d, h in GEAR:
        out.append((n, x, w, d, h)); x += w + GEAR_GAP
    return out

def well_positions():
    """(name, x, w, y0, y1, floor_z) per flush-mounted unit.

    Front edges all sit on GEAR_Y so the front rail reads as one straight line;
    the cut-out clearance is taken at the sides and the back only.
    """
    out = []
    for n, gx, gw, gd, gh in gear_positions():
        out.append((n, gx - WELL_CLEAR, gw + 2 * WELL_CLEAR,
                    GEAR_Y, GEAR_Y + gd + 2 * WELL_CLEAR, Z_WELL_FLOOR))
    return out

def _eq(a, b): return abs(a - b) < 1e-9

if VARIANT == 2:
    # vertical chain: cavity 78.2 | mid panel 80.0 | drawers 9.2 | floor 1.8 | gear 9.0 | 100
    assert _eq(Z_CAV_TOP, 78.2) and _eq(Z_FIX_TOP, 80.0) and _eq(DRW_H, 9.2)
    assert _eq(Z_FIX_TOP + DRW_H, Z_DRW_TOP) and _eq(Z_DRW_TOP, 89.2)   # band stops under the floor
    assert _eq(Z_FIX_TOP + DRW_H + T, H_TOP - WELL_DROP)                # the 18 mm floor fits in the budget
    assert _eq(Z_DRW_TOP + T, Z_WELL_FLOOR) and _eq(Z_WELL_FLOOR, 91.0)  # gear stands on the floor's top face
    assert _eq(H_TOP - Z_WELL_FLOOR, WELL_DROP)                         # a full 9.0 clear above it
    assert Z_CAV_TOP > Z_TRAY_TOP + KB_H                                # the stowed keyboard still clears
    assert _eq(Z_WELL_FLOOR + FASCIA_H, Z_TOP_UNDER) and _eq(Z_TOP_UNDER, 97.0)
    assert _eq(Z_TOP_UNDER + TT, H_TOP)
    assert _eq(WELL_WALL_H, 7.8) and _eq(Z_BACK_TOP, Z_WELL_FLOOR)
    # the front face is continuous: fronts 80.0 -> 91.0 meet the fascia's bottom edge, no open strip
    assert _eq(Z_FRONT_TOP, Z_WELL_FLOOR) and _eq(FRONT_H, 11.0)
    assert _eq(FRONT_H - DRW_H, T)                        # the fronts overhang their boxes by exactly the floor's thickness
    assert min(w[3] for w in well_positions()) >= T        # that overhang clears: every well floor starts behind the fronts
    _deep = max(w[4] for w in well_positions())          # deepest well back edge
    assert _eq(_deep, 41.2), _deep                        # the Xone:92
    assert _eq(INT_D - _deep, 7.0)                        # minimum back rail
    assert _eq(Y_BACK1, D)                                # back panel at the rear face
    _last = gear_positions()[-1]
    assert _last[1] + _last[2] <= X_BAY1 - 3.0            # right margin holds
    assert _eq(BOOK_D, 33.2)
    assert BOOK_D >= 31.4                                 # a 12" LP sleeve still fits
    assert WELL_SLOT_W < min(w[2] for w in well_positions())    # the cable notch fits even the narrowest rear wall
    assert WALL_GAP > 0 and _eq(WALL_GAP, 5.0)            # the trough vents only through the wall gap, so it is drawn and dimensioned
    assert _eq(NICHE_CUT_H_EFF, 8.0)                      # the niche cutout runs out at the back panel's top edge

if VARIANT == 1:
    # book zone setback (v1.7): the shin line crosses the compartment floor plane at y = -1.0,
    # so a 10.0 setback takes the clearance at that pinch from 1.0 to 11.0
    assert _eq(BOOK_SETBACK, 10.0) and _eq(BOOK_D, 33.2)
    assert BOOK_D >= 31.4                                 # a 12" LP sleeve still fits, with 1.8 to spare
    assert _eq(INT_D, 43.2) and _eq(BACK_INSET, 5.0)       # nothing else moved: v1 keeps its 5 cm chase, so 43.2 inside

OAK, OAK2, OAKE = "#EAD9B9", "#D6BE94", "#7A5F32"
VOID, GEARC, INK, DIMC, GHOST = "#F8F5EE", "#3B3B3B", "#1E1E1E", "#1C5BBF", "#9A9A9A"
NOTE = "#555"
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"

class Drawing:
    def __init__(self, xmin, xmax, zmin, zmax, scale=4.0, pad=(70, 30, 70, 50)):
        self.s, self.xmin, self.zmax = scale, xmin, zmax
        self.pl, self.pt, self.pr, self.pb = pad
        self.w = (xmax - xmin) * scale + self.pl + self.pr
        self.h = (zmax - zmin) * scale + self.pt + self.pb
        self.parts = []
    def X(self, x): return self.pl + (x - self.xmin) * self.s
    def Y(self, z): return self.pt + (self.zmax - z) * self.s
    def rect(self, x, z, w, h, fill=OAK, stroke=INK, sw=1.0, dash=None, op=1.0, rx=0):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        r = f' rx="{rx*self.s:.1f}"' if rx else ""
        self.parts.append(f'<rect x="{self.X(x):.1f}" y="{self.Y(z + h):.1f}" width="{w * self.s:.1f}" height="{h * self.s:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}{r} opacity="{op}"/>')
    def line(self, x0, z0, x1, z1, stroke=INK, sw=1.0, dash=None, op=1.0):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<line x1="{self.X(x0):.1f}" y1="{self.Y(z0):.1f}" x2="{self.X(x1):.1f}" y2="{self.Y(z1):.1f}" stroke="{stroke}" stroke-width="{sw}"{d} opacity="{op}"/>')
    def poly(self, pts, stroke=INK, sw=1.0, fill="none", dash=None):
        p = " ".join(f"{self.X(x):.1f},{self.Y(z):.1f}" for x, z in pts)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<polyline points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"{d}/>')
    def circle(self, x, z, r, fill="none", stroke=INK, sw=1.0):
        self.parts.append(f'<circle cx="{self.X(x):.1f}" cy="{self.Y(z):.1f}" r="{r * self.s:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    def text(self, x, z, s, size=10, anchor="middle", fill=INK, rot=None, weight="normal", dx=0, dy=0, italic=False):
        X, Y = self.X(x) + dx, self.Y(z) + dy
        tr = f' transform="rotate({rot} {X:.1f} {Y:.1f})"' if rot is not None else ""
        st = ' font-style="italic"' if italic else ""
        self.parts.append(f'<text x="{X:.1f}" y="{Y:.1f}" font-size="{size}" text-anchor="{anchor}" fill="{fill}" font-weight="{weight}"{st}{tr}>{H.escape(s)}</text>')
    def tick(self, X, Y, vertical, color):
        if vertical: self.parts.append(f'<line x1="{X:.1f}" y1="{Y-4:.1f}" x2="{X:.1f}" y2="{Y+4:.1f}" stroke="{color}" stroke-width="0.9"/>')
        else: self.parts.append(f'<line x1="{X-4:.1f}" y1="{Y:.1f}" x2="{X+4:.1f}" y2="{Y:.1f}" stroke="{color}" stroke-width="0.9"/>')
    def dim_h(self, x0, x1, z, label=None, ext=None, size=9, above=True, color=DIMC):
        if label is None: label = f"{abs(x1 - x0):g}"
        if ext is not None:
            for x in (x0, x1): self.line(x, ext, x, z, stroke=color, sw=0.5, dash="2,2", op=0.8)
        self.line(x0, z, x1, z, stroke=color, sw=0.8)
        for x in (x0, x1): self.tick(self.X(x), self.Y(z), True, color)
        self.text((x0 + x1) / 2, z, label, size=size, fill=color, dy=(-3 if above else size + 3))
    def dim_v(self, z0, z1, x, label=None, ext=None, size=9, right=True, color=DIMC):
        if label is None: label = f"{abs(z1 - z0):g}"
        if ext is not None:
            for z in (z0, z1): self.line(ext, z, x, z, stroke=color, sw=0.5, dash="2,2", op=0.8)
        self.line(x, z0, x, z1, stroke=color, sw=0.8)
        for z in (z0, z1): self.tick(self.X(x), self.Y(z), False, color)
        self.text(x, (z0 + z1) / 2, label, size=size, fill=color, rot=-90, dx=(size + 2 if right else -3))
    def leader(self, x, z, tx, tz, s, size=9, anchor="start", color=INK, italic=False):
        self.line(x, z, tx, tz, stroke=color, sw=0.6)
        self.circle(x, z, 1.6 / self.s, fill=color, stroke="none")
        self.text(tx, tz, s, size=size, anchor=anchor, fill=color, dx=(4 if anchor == "start" else -4), dy=3, italic=italic)
    def render(self):
        w, h = int(self.w), int(self.h)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="{FONT}">'
                f'<rect width="{w}" height="{h}" fill="white"/>' + "".join(self.parts) + "</svg>")

REC_COLS = ["#B8A48A", "#7D6B57", "#D9CBB3", "#5E5548", "#A3927A", "#8C7B68"]
def draw_records(d, x0, z0, width, fill_frac=1.0):
    n = max(2, int(round(width * fill_frac / 0.78)))
    pitch = 0.78
    for i in range(n):
        d.rect(x0 + i * pitch + 0.12, z0, pitch - 0.24, 31.5, fill=REC_COLS[i % len(REC_COLS)], stroke="none")

BOOK_COLS = ["#A67C52", "#6E8B74", "#8E6E95", "#5C7C99", "#C2B280", "#B55A4A", "#4F4F4F", "#D2A679"]
def draw_books(d, x0, z0, width, hmin, hmax, seed):
    rnd = random.Random(seed); x = x0
    while True:
        w = rnd.uniform(1.4, 3.4); h = rnd.uniform(hmin, hmax)
        if x + w > x0 + width: break
        d.rect(x, z0, w, h, fill=rnd.choice(BOOK_COLS), stroke="none")
        x += w + 0.18

def speaker(d, sx, z0, w, h, top_view=False):
    d.rect(sx + 1, z0, w - 2, 1.5, fill="#666", stroke="none")
    d.rect(sx, z0 + 1.5, w, h - 1.5, fill=GEARC, stroke="none")
    d.circle(sx + w / 2, z0 + 1.5 + 9.5, 5.6, fill="#222", stroke="#5a5a5a")
    d.circle(sx + w / 2, z0 + 1.5 + 22.5, 2.3, fill="#222", stroke="#5a5a5a")

# ---------------- drawing register ----------------
# The numbers in the headings and in every cross-reference come from this list, not from literals
# typed next to them: v2 carries a fifth drawing, so any hardcoded "4." or "5." drifts the moment
# the list changes length. (key, name used in prose, heading title, rendered height)
DRAWINGS = [("front", "the front elevation", "Front elevation", "168mm"),
            ("side", "the side section", "Side section through the bay, cut through the power niche and the mixer, looking toward the right wing", "165mm"),
            ("plan", "the plan of the top", "Plan of the top", "66mm"),
            ("detail", "detail A", "Detail A: tray edge, slide and apron (section looking from the front, left side)", "82mm")]
if VARIANT == 2:
    DRAWINGS.append(("well", "detail B", "Detail B: gear well (section through the front rail)", "70mm"))
DRAWING_NO = {k: i + 1 for i, (k, _n, _t, _h) in enumerate(DRAWINGS)}
DRAWING_NAME = {k: n for k, n, _t, _h in DRAWINGS}
DRAWING_TITLE = {k: t for k, _n, t, _h in DRAWINGS}
DRAWING_HEIGHT = {k: h for k, _n, _t, h in DRAWINGS}

def dref(key):
    """Cross-reference a drawing by name and by its derived number, never by position alone."""
    return f"{DRAWING_NAME[key]}, drawing {DRAWING_NO[key]}"

# ---------------- 1. front elevation ----------------
def front_elevation():
    zmax = H_WING + SPK_H + 6
    d = Drawing(0, W, -16, zmax, scale=4.0, pad=(80, 20, 190, 20))
    d.line(-6, 0, W + 6, 0, sw=1.6)
    # voids
    d.rect(X_BAY0, 0, BAY_W, RECESS_H, fill="#E6E0D4", stroke="none")
    d.rect(X_BAY0, Z_BOT_TOP, BAY_W, Z_TRAY_UNDER - Z_BOT_TOP, fill=VOID, stroke="none")
    d.rect(X_BAY0, Z_TRAY_TOP, BAY_W, Z_CAV_TOP - Z_TRAY_TOP, fill=VOID, stroke="none")
    # wings
    for x0 in (0.0, W - WING_W):
        left = x0 == 0.0
        d.rect(x0 + T, 0, WING_INT_W, WING_PLINTH_H, fill=OAK2)
        d.rect(x0 + T, WING_PLINTH_H, WING_INT_W, T)
        z = Z_WBOT_TOP
        for i in range(3):
            d.rect(x0 + T, z, WING_INT_W, WING_OPEN, fill=VOID, stroke="none")
            if i < 2: draw_records(d, x0 + T, z, WING_INT_W)
            else:
                draw_records(d, x0 + T, z, WING_INT_W, fill_frac=0.42)
                d.text(x0 + T + WING_INT_W * 0.74, z + WING_OPEN / 2, "records, spines out", size=8, rot=-90, fill="#333", dx=3)
            z += WING_OPEN
            if i < 2:
                d.rect(x0 + T, z, WING_INT_W, T); z += T
        d.rect(x0, 0, T, Z_CAP_UNDER); d.rect(x0 + WING_W - T, 0, T, Z_CAP_UNDER)
        cx = 0.0 if left else W - CAP_W
        d.rect(cx, Z_CAP_UNDER, CAP_W, TT)
        speaker(d, cx + (CAP_W - SPK_W) / 2, H_WING, SPK_W, SPK_H)
    # bay carcass
    if not BOOK_SETBACK:
        d.rect(X_BAY0, RECESS_H, BAY_W, T)
    else:
        d.rect(X_BAY0, RECESS_H, BAY_W, T, fill="#EFE9DC", stroke=GHOST, sw=0.8, dash="4,3")
        d.text(W / 2, RECESS_H - 4.2, f"book zone set back {BOOK_SETBACK:g} cm for knee and shin clearance", size=8, fill=NOTE, italic=True)
    rx = X_BAY0 + OPEN_W + DIV_T
    draw_books(d, X_BAY0 + 2.5, Z_BOT_TOP, 44, 22, 31.5, 1)
    d.rect(rx + 0.1, Z_BOT_TOP + SHELF_UP, OPEN_W - 0.2, T)
    draw_books(d, rx + 2.5, Z_BOT_TOP, 52, 14.5, 18.5, 2)
    draw_books(d, rx + 2.5, Z_BOT_TOP + SHELF_UP + T, 46, 13.5, 16.5, 3)
    d.rect(X_BAY0 + OPEN_W, Z_BOT_TOP, DIV_T, Z_TRAY_UNDER - Z_BOT_TOP - 0.5)
    # tray (stowed)
    tx0 = X_BAY0 + SLIDE_T
    d.rect(X_BAY0, Z_TRAY_TOP, SLIDE_T, SLIDE_H, fill="#8a8a8a", stroke="none")
    d.rect(X_BAY1 - SLIDE_T, Z_TRAY_TOP, SLIDE_T, SLIDE_H, fill="#8a8a8a", stroke="none")
    d.rect(tx0 + T, Z_TRAY_UNDER, TRAY_PANEL_W, TRAY_T)
    d.rect(tx0, Z_TRAY_UNDER, T, APRON_H); d.rect(tx0 + TRAY_W - T, Z_TRAY_UNDER, T, APRON_H)
    d.rect(KB_X, Z_TRAY_TOP, KB_W, KB_H, fill="#2A2A2A", stroke="none")
    d.rect(KB_X + 5, Z_TRAY_TOP + 3.2, KB_W - 10, 3.0, fill="#F2F2F2", stroke="none")
    # fixed panel, drawers, top
    d.rect(X_BAY0, Z_CAV_TOP, BAY_W, T)
    # the fronts, not the boxes: in v2 they run 18 mm past the band's ceiling up to the fascia at 91
    d.rect(X_BAY0, Z_FIX_TOP, BAY_W, FRONT_H, fill="#6B5A40", stroke="none")
    for ox in (X_BAY0, NICHE_X + NICHE_W + T):
        d.rect(ox + GAP, Z_FIX_TOP + GAP, DRW_W - 2 * GAP, FRONT_H - 2 * GAP, fill=OAK)
        d.line(ox + 8, Z_FRONT_TOP - 1.7, ox + DRW_W - 8, Z_FRONT_TOP - 1.7, stroke=OAKE, sw=1.2)
    d.rect(NICHE_X - T, Z_FIX_TOP, T, FRONT_H); d.rect(NICHE_X + NICHE_W, Z_FIX_TOP, T, FRONT_H)
    d.rect(NICHE_X + GAP, Z_FIX_TOP + NICHE_VENT, NICHE_W - 2 * GAP, NICHE_DOOR_H, fill=OAK)
    cxn, czn = NICHE_X + NICHE_W / 2, Z_FIX_TOP + FRONT_H / 2 + 0.8
    d.circle(cxn, czn, 1.7, stroke=OAKE, sw=1.1); d.line(cxn, czn, cxn, czn + 2.4, stroke=OAKE, sw=1.4)
    d.text(cxn, Z_FIX_TOP + 2.4, "power niche", size=7, fill=NOTE)
    if VARIANT == 1:
        d.rect(X_BAY0, Z_TOP_UNDER, BAY_W, TT)
        # gear
        for n, gx, gw, gd, gh in gear_positions():
            d.rect(gx, H_TOP, gw, gh, fill=GEARC, stroke="none")
            d.text(gx + gw / 2, H_TOP + gh + 3.6, n, size=9)
        tt = gear_positions()[0]
        d.rect(tt[1] + 3, H_TOP + tt[4] - 2.4, tt[2] - 6, 1.3, fill="#8a8a8a", stroke="none")
    else:
        # 9 cm slab (3 cm oak top board over a 6 cm fascia), wells cut through both.
        # The 6 cm fascia stands in front of the gear in this view, so every unit is hidden:
        # the oak face is continuous across the bay and each unit is a dashed ghost behind it.
        d.rect(X_BAY0, Z_WELL_FLOOR, BAY_W, FASCIA_H + TT)
        for n, wx, ww, wy0, wy1, wfz in well_positions():
            d.rect(wx, wfz, ww, WELL_DROP, fill="none", stroke=GHOST, sw=0.8, dash="4,3")
            d.text(wx + ww / 2, H_TOP + 3.6, n, size=9)
        d.text(W / 2, 107.5, "units dashed: sunk below the surface, hidden behind the fascia in this view", size=8, fill=NOTE, italic=True)
        d.line(X_BAY0, Z_TOP_UNDER, X_BAY1, Z_TOP_UNDER, stroke=OAKE, sw=0.6, dash="4,3")
    # notes. Centred on the full width, so they must stay inside the clear span between the wings
    # (X_BAY0 to X_BAY1): at 9 px per em these run about 122 cm (v1) and 113 cm (v2) of the 145 available.
    if VARIANT == 1:
        d.text(W / 2, 123.6, f"Cable slot {SLOT_Y1 - SLOT_Y0:g} × {SLOT_X1 - SLOT_X0:g} cm in the top behind the gear; leads, plugs and the XDJ bricks drop into the chase and the power niche", size=9, fill=NOTE, italic=True)
    else:
        d.text(W / 2, 123.6, f"Gear sunk {WELL_DROP:g} cm into the slab: faceplates flush in one unbroken oak face, wells open to the trough, no dust covers", size=9, fill=NOTE, italic=True)
    d.text(X_BAY0 + DRW_W / 2, Z_FIX_TOP + FRONT_H / 2, "Drawer: cables, adapters, needles", size=9, dy=3)
    d.text(NICHE_X + NICHE_W + T + DRW_W / 2, Z_FIX_TOP + FRONT_H / 2, "Drawer: headphones", size=9, dy=3)
    if VARIANT == 2:
        d.text(X_BAY0 + DRW_W / 2, Z_FIX_TOP + FRONT_H / 2 - 3.2, f"front {FRONT_H:g} cm tall on a {DRW_H:g} cm box", size=7, fill=NOTE, italic=True, dy=3)
    d.text(W / 2, Z_CAV_TOP - 2.6, "Keyboard 133 × 35 × 12 stowed on the pull-out tray (extends 40 cm, see section)", size=9, fill=NOTE, italic=True)
    d.text(X_BAY0 + OPEN_W / 2, Z_TRAY_UNDER - 3.2, "Books or LPs (39 cm clear)", size=9, fill=NOTE, italic=True)
    d.text(rx + OPEN_W / 2, Z_TRAY_UNDER - 3.2, "Adjustable shelf on 5 mm pins", size=9, fill=NOTE, italic=True)
    d.text(W / 2, 8.6, "Foot and pedal recess, 20 cm clear, full width, open through to the wall", size=9, fill=NOTE, italic=True)
    # past the dimension column, not across it: at W + 3 the caption ran straight through the "27" label
    d.leader(W + 0.2, 105, W + 13, 104, "headphone hook, outer face", size=8, italic=True)
    d.text(6, H_WING + SPK_H + 3, "5\" monitors on isolation pads", size=8, fill=NOTE, italic=True, anchor="start")
    # width dims (bottom)
    d.dim_h(0, WING_W, -5, f"{WING_W:g}", ext=0, above=False); d.dim_h(X_BAY0, X_BAY1, -5, f"{BAY_W:g} bay / gear span", ext=0, above=False); d.dim_h(X_BAY1, W, -5, f"{WING_W:g}", ext=0, above=False)
    d.dim_h(0, W, -12, f"{W:g} overall (footprint = width at every height)", above=False)
    if CAP_OVER > 0:
        d.dim_h(0, CAP_W, 125.0, f"{CAP_W:g} cap", ext=Z_CAP_UNDER, above=False)
        d.dim_h(W - CAP_W, W, 125.0, f"{CAP_W:g} cap", ext=Z_CAP_UNDER, above=False)
    # height dims (right)
    xr = W + 8
    d.dim_v(0, RECESS_H, xr, "20", ext=X_BAY1); d.dim_v(Z_BOT_TOP, Z_TRAY_UNDER, xr, "39.4", ext=X_BAY1)
    d.dim_v(Z_TRAY_TOP, Z_CAV_TOP, xr, f"{Z_CAV_TOP - Z_TRAY_TOP:g}", ext=X_BAY1)
    d.dim_v(Z_FIX_TOP, Z_FRONT_TOP, xr, f"{FRONT_H:g} fronts" if VARIANT == 2 else f"{DRW_H:g}", ext=X_BAY1)
    if VARIANT == 2:
        d.dim_v(Z_WELL_FLOOR, H_TOP, xr, f"{FASCIA_H + TT:g} slab", ext=X_BAY1)
    d.dim_v(H_TOP, Z_CAP_UNDER, xr, "27", ext=X_BAY1)
    d.dim_v(0, Z_TRAY_TOP, W + 20, "63 tray top"); d.dim_v(0, H_TOP, W + 31, "100 DJ surface"); d.dim_v(0, H_WING, W + 42, "130 cap top")
    # left: wing openings
    xl = -7
    d.dim_v(0, WING_PLINTH_H, xl, "6", ext=0, right=False)
    z = Z_WBOT_TOP
    for i in range(3):
        d.dim_v(z, z + WING_OPEN, xl, "38.5", ext=0, right=False); z += WING_OPEN + T
    d.text(-14, 60, "panels 18 mm, top and caps 30 mm", size=8, rot=-90, fill=NOTE)
    return d.render()

# ---------------- 2. side section ----------------
def side_section():
    d = Drawing(-76, D + 30, -16, H_WING + SPK_H + 6, scale=4.0, pad=(70, 20, 30, 20))
    P = "#8A8A8A"
    # background wing (behind the cut)
    d.rect(0, 0, D, Z_CAP_UNDER, fill="#F1ECE2", stroke=GHOST, sw=0.8)
    d.rect(0, Z_CAP_UNDER, D, TT, fill="#EAE2D2", stroke=GHOST, sw=0.8)
    d.rect(SPK_Y, H_WING, SPK_D, SPK_H, fill="#D4D4D4", stroke=GHOST, sw=0.8)
    d.text(25, 121, "right wing (behind)", size=8, fill=GHOST, italic=True)
    d.line(-78, 0, D + WALL_GAP + 4, 0, sw=1.6)
    d.line(D + WALL_GAP, 0, D + WALL_GAP, H_WING + SPK_H + 4, stroke="#777", sw=3)
    d.text(D + WALL_GAP + 2, 158, "wall", size=9, anchor="start", fill="#777")
    if VARIANT == 2:
        d.text(D + WALL_GAP / 2 + 0.5, 66, f"{WALL_GAP:g} cm wall gap, mandatory: the trough vents and the mains lead exits here", size=7, rot=-90, fill=NOTE, italic=True)
    # chase hatch
    if VARIANT == 1:
        for zz in range(22, 97, 4): d.line(Y_BACK1, zz, D, zz + 3, stroke=GHOST, sw=0.5)
    # carcass
    d.rect(BOOK_SETBACK, RECESS_H, Y_BACK1 - BOOK_SETBACK, T)
    d.rect(Y_BACK0, Z_BOT_TOP, T, Z_BACK_TOP - Z_BOT_TOP)
    d.rect(Y_BACK0 - 0.05, CUT_Z0, T + 0.1, CUT_H, fill=VOID, stroke="none")
    d.rect(Y_BACK0 - 0.05, NICHE_CUT_Z0, T + 0.1, min(NICHE_CUT_H, Z_BACK_TOP - NICHE_CUT_Z0), fill=VOID, stroke="none")
    d.rect(0, Z_CAV_TOP, Y_BACK0, T)
    if VARIANT == 1:
        d.rect(0, Z_TOP_UNDER, SLOT_Y0, TT); d.rect(SLOT_Y1, Z_TOP_UNDER, D - SLOT_Y1, TT)
    else:
        xone = [w for w in well_positions() if w[0] == "Xone:92"][0]
        d.rect(0, Z_WELL_FLOOR, GEAR_Y, FASCIA_H + TT)                 # front rail, 5 cm, solid 91 -> 100
        d.rect(xone[4], Z_TOP_UNDER, Y_BACK0 - xone[4], TT)            # back rail: oak at the surface (97 -> 100), open underneath -> the trough
        d.rect(GEAR_Y, Z_DRW_TOP, xone[4] - GEAR_Y, T, fill=OAK2)      # well floor 18 mm, top face at 91 (detail B)
        d.text((xone[4] + Y_BACK0) / 2 + 0.3, Z_WELL_FLOOR + 4.3, "trough", size=7, fill=NOTE)
    # books
    d.rect(BOOK_SETBACK + 1.0, Z_BOT_TOP + SHELF_UP, BOOK_D - 1.0, T)
    d.rect(BOOK_SETBACK + 1.5, Z_BOT_TOP, 22, 17, fill="#A67C52", stroke="none")
    d.rect(BOOK_SETBACK + 1.5, Z_BOT_TOP + SHELF_UP + T, 20, 15.5, fill="#6E8B74", stroke="none")
    if BOOK_SETBACK:
        d.dim_h(0, BOOK_SETBACK, 24.5, f"{BOOK_SETBACK:g} setback", ext=Z_BOT_TOP, above=False)
    # tray stowed + slide + apron
    d.rect(0, Z_TRAY_UNDER, TRAY_D, TRAY_T)
    d.rect(1.5, Z_TRAY_TOP, SLIDE_LEN, SLIDE_H, fill="#C4C4C4", stroke="none", op=0.7)
    d.rect(0, Z_TRAY_UNDER, TRAY_D, APRON_H, fill="none", stroke=GHOST, dash="3,2")
    d.rect(TRAY_D - T, Z_TRAY_TOP, T, APRON_UP)
    d.rect(KB_Y, Z_TRAY_TOP, KB_D, KB_H, fill="#2A2A2A", stroke="none")
    # extended ghost
    d.rect(-EXT, Z_TRAY_UNDER, TRAY_D, TRAY_T, fill="none", stroke=INK, dash="4,3")
    d.rect(-EXT + KB_Y, Z_TRAY_TOP, KB_D, KB_H, fill="none", stroke=INK, dash="4,3")
    # power niche (the cut runs through it): door with vent gap, strip, plugs, brick
    d.rect(GAP, Z_FIX_TOP + NICHE_VENT, T, NICHE_DOOR_H)   # niche door in section: the vent gap is taken off its height
    d.rect(5, Z_FIX_TOP, 30, 4.0, fill="#444", stroke="none")
    for yy in (9, 16, 23): d.rect(yy, Z_FIX_TOP + 4.0, 4.0, 2.5, fill="#777", stroke="none")
    if VARIANT == 1:
        d.rect(28.5, Z_FIX_TOP + 4.0, 6, 8.5, fill="#666", stroke="none")       # stacked on the strip: 4 + 8.5 only fits v1's 15.2 band
    else:
        d.rect(Y_BACK0 - 5.2, Z_FIX_TOP, 5.2, 8.5, fill="#666", stroke="none")    # stands on the niche floor at the rear; the band above it is open trough
    # mixer in section + cables
    if VARIANT == 1:
        d.rect(GEAR_Y, H_TOP, 35.8, 10.7, fill=GEARC, stroke="none")
    else:
        d.rect(GEAR_Y, Z_WELL_FLOOR, 35.8, WELL_DROP, fill=GEARC, stroke="none")
    if VARIANT == 1:
        d.poly([(GEAR_Y + 35.8, H_TOP + 4), (SLOT_Y0 + 2.5, H_TOP + 1.5), (SLOT_Y0 + 2.5, Z_TOP_UNDER - 3), (47.0, 93), (46.0, 89.5), (36, 88.5), (18, 88.3)], stroke="#C0392B", sw=1.2)
    else:
        # mixer's rear in its well -> back into the trough (z 91-97) -> down behind the well floor -> into the power niche
        d.poly([(GEAR_Y + 35.8, Z_WELL_FLOOR + 5), (xone[4] + 0.4, Z_WELL_FLOOR + 3.2), (xone[4] + 0.4, Z_FIX_TOP + 5.0), (20, Z_FIX_TOP + 2)], stroke="#C0392B", sw=1.2)
    if VARIANT == 1:
        d.poly([(TRAY_D - 3, 69), (Y_BACK0 + 0.5, 70.5), (46.5, 72), (46.5, 87.5), (25, 88.3)], stroke="#C0392B", sw=1.0)
        d.poly([(35, Z_FIX_TOP + 2), (47.5, 84.5), (47.5, 10), (50, 8)], stroke="#333", sw=1.2)
        d.text(36, 11.5, "mains lead to wall socket", size=7.5, fill=NOTE, italic=True)
    else:
        # keyboard lead: behind the tray and straight out of the tray cutout (66 -> 74) -- no chase to climb in v2
        d.poly([(TRAY_D - 3, 71.5), (44.0, 71.8), (Y_BACK0 - 0.3, 72.2)], stroke="#C0392B", sw=1.0)
        # mains: off the end of the strip, up past the bricks and out over the back panel (top edge at 91) to the wall behind
        d.poly([(35, Z_FIX_TOP + 2.6), (xone[4] + 1.2, Z_FIX_TOP + 3.6), (xone[4] + 1.2, Z_WELL_FLOOR + 1.4), (Y_BACK0 - 0.3, 92.9)], stroke="#333", sw=1.2)
    d.rect(12, 0, 12, 5, fill="#555", stroke="none")
    if VARIANT == 1:
        d.poly([(24, 3), (47.0, 3), (47.0, CUT_Z0 + 4), (Y_BACK0, CUT_Z0 + 4), (TRAY_D - 3, 68.5)], stroke="#8E44AD", sw=1.0, dash="2,2")
    else:
        # pedal lead: up the set-back void, the one clear path from the recess to the tray now the chase is gone, then up behind the tray
        d.poly([(24, 3), (29, 16), (14, 19), (14, 59.6), (45, 60.2), (45, 68.8), (TRAY_D - 3, 69.2)], stroke="#8E44AD", sw=1.0, dash="2,2")
    # seated player
    d.circle(-50, 113, 7.5, stroke=P, sw=1.3)
    d.poly([(-51, 105), (-52, 51)], stroke=P, sw=1.5)
    d.poly([(-50, 101), (-37, 85), (-20, 76)], stroke=P, sw=1.2)
    d.poly([(-52, 51), (-8, 54), (2, 8), (21, 6)], stroke=P, sw=1.5)
    d.rect(-63, 43, 24, 3, fill="#D8D8D8", stroke=P)
    d.text(-51, 37.5, "stool 44 to 46 cm", size=8, fill=P, italic=True)
    d.text(-22, 47.5, "thigh clears tray underside (61.2)", size=8, fill=P, italic=True, anchor="end")
    # labels (left column)
    R = -26
    if VARIANT == 1:
        d.leader(SLOT_Y0 + 3, H_TOP, R, 162, f"cable slot {SLOT_Y1 - SLOT_Y0:g} cm in the top", anchor="end", italic=True)
    if VARIANT == 1:
        d.leader(47.5, 60, R, 154, "cable chase 5 cm behind the inset back panel", anchor="end", italic=True)
        d.leader(Y_BACK0 + 0.9, 40, R, 146, "back panel 18 mm, inset 5 cm", anchor="end", italic=True)
    else:
        d.leader(xone[4] + 2, Z_WELL_FLOOR + 3, R, 154, f"cable trough under the back rail, {Y_BACK0 - xone[4]:g} cm deep, rear open", anchor="end", italic=True)
        d.leader(Y_BACK0 + 0.9, 40, R, 146, f"back panel 18 mm, flush with the rear face, top edge at {Z_BACK_TOP:g}", anchor="end", italic=True)
    d.leader(20, Z_FIX_TOP + 2, R, 138,
             "power niche: strip and bricks, vented door" if VARIANT == 1 else
             "power niche: strip flat, bricks standing at the rear", anchor="end", italic=True)
    d.leader(Y_BACK0 + 0.9, NICHE_CUT_Z0 + 6, R, 122, "back panel cut away behind the niche", anchor="end", italic=True)
    d.leader(21, 65.5, R, 130, f"heavy-duty tray slide 400 mm ({DRAWING_NAME['detail']})", anchor="end", italic=True)
    d.leader(18, 2.5, R, 5, "sustain pedal in the recess", anchor="end", italic=True)
    d.text(-EXT + TRAY_D / 2 - 8, 84, "tray extended 40 cm (dashed)", size=8, fill=INK, italic=True)
    if VARIANT == 1: d.text(45, 40, "chase", size=8, rot=-90, fill=NOTE, dx=13)
    # dims
    d.dim_h(0, INT_D, -5, f"{INT_D:g} interior", ext=0, above=False)
    if VARIANT == 1: d.dim_h(Y_BACK1, D, -5, "5", ext=0, above=False)
    if WALL_GAP: d.dim_h(D, D + WALL_GAP, -5, f"{WALL_GAP:g} wall gap", ext=0, above=False)
    if VARIANT == 2:
        d.dim_h(0, GEAR_Y, 114, f"{GEAR_Y:g} front rail", ext=H_TOP)
        d.dim_h(xone[4], Y_BACK0, 114, f"{Y_BACK0 - xone[4]:g} back rail", ext=H_TOP)
    d.dim_h(0, D, -12, "50 overall depth", above=False)
    d.dim_h(-EXT, 0, 92, "40 extension", ext=Z_TRAY_UNDER + 14)
    if VARIANT == 1:
        d.dim_h(0, SLOT_Y0, 114, f"{SLOT_Y0:g} from front edge to slot", ext=H_TOP); d.dim_h(SLOT_Y0, SLOT_Y1, 114, f"{SLOT_Y1 - SLOT_Y0:g}", ext=H_TOP)
    d.dim_h(0, TRAY_D, 58.5, "42 tray", above=False)
    xr = D + 8
    d.dim_v(0, RECESS_H, xr, "20 recess"); d.dim_v(Z_TRAY_TOP, Z_CAV_TOP, xr, f"{Z_CAV_TOP - Z_TRAY_TOP:g}"); d.dim_v(H_TOP, H_WING, xr, "30")
    d.dim_v(0, Z_TRAY_UNDER, D + 17, "61.2 clear under tray"); d.dim_v(0, H_TOP, D + 26, "100")
    return d.render()

# ---------------- 3. plan view ----------------
def plan_view():
    # v2 needs one more dimension column on the right for the wall gap, so it gets a wider right pad
    d = Drawing(0, W, -22, D + 12, scale=4.0, pad=(40, 20, 130 if VARIANT == 1 else 165, 20))
    d.line(0, D + WALL_GAP, W, D + WALL_GAP, stroke="#777", sw=3); d.text(W + 1, D + WALL_GAP, "wall", size=9, anchor="start", fill="#777", dy=3)
    for x0, cx in ((0.0, 0.0), (W - WING_W, W - CAP_W)):
        d.rect(x0, 0, WING_W, D, fill=OAK2)
        d.rect(cx, 0, CAP_W, D, fill=OAK)
        d.line(x0 + (WING_W if x0 == 0 else 0), 0, x0 + (WING_W if x0 == 0 else 0), D, stroke=GHOST, dash="3,2")
        sx = cx + (CAP_W - SPK_W) / 2
        d.rect(sx, SPK_Y, SPK_W, SPK_D, fill=GEARC, stroke="none")
        d.text(sx + SPK_W / 2, SPK_Y + SPK_D / 2, "5\" monitor", size=7, fill="white", rot=-90, dx=3)
    d.rect(X_BAY0, 0, BAY_W, D)
    if VARIANT == 1:
        d.rect(SLOT_X0, SLOT_Y0, SLOT_X1 - SLOT_X0, SLOT_Y1 - SLOT_Y0, fill="#3a3a3a", stroke="none", rx=2.5)
        d.text((SLOT_X0 + SLOT_X1) / 2, SLOT_Y0 + 3, f"cable slot {SLOT_X1 - SLOT_X0:g} × {SLOT_Y1 - SLOT_Y0:g}", size=8, fill="white", dy=3)
    else:
        for n, wx, ww, wy0, wy1, wfz in well_positions():
            d.rect(wx, wy0, ww, wy1 - wy0, fill="none", stroke="#C0392B", sw=1.2, dash="4,3")
            d.text(wx + ww / 2, wy1 + 2.0, f"cut-out {ww:g} × {wy1 - wy0:g}", size=7, fill="#C0392B", dy=3)
        d.text((X_BAY0 + X_BAY1) / 2, Y_BACK0 - 3.4, "cable trough, full bay width", size=8, fill=NOTE, italic=True, dy=3)
        d.rect(X_BAY0, Y_BACK0, BAY_W, T, fill="none", stroke="#C0392B", sw=1.2, dash="4,3")
        d.text((X_BAY0 + X_BAY1) / 2, D + WALL_GAP / 2, f"back panel below stops at {Z_BACK_TOP:g}: the trough's rear face is open across the bay, {BAY_W:g} × {FASCIA_H:g} cm, venting into the wall gap", size=8, fill="#C0392B", italic=True, dy=3)
    for n, gx, gw, gd, gh in gear_positions():
        d.rect(gx, GEAR_Y, gw, gd, fill=GEARC, stroke="none")
        d.text(gx + gw / 2, GEAR_Y + gd / 2, n, size=8, fill="white", dy=3)
        d.text(gx + gw / 2, GEAR_Y + gd / 2 - 4.5, f"{gw:g} × {gd:g}", size=7, fill="#ccc", dy=3)
    tt = gear_positions()[0]
    d.circle(tt[1] + 18, GEAR_Y + 18.5, 15, fill="none", stroke="#777", sw=0.8)
    d.rect(W, 3.5, 1.6, 3.5, fill="#333", stroke="none"); d.text(W + 2.5, 5, "headphone hook", size=8, anchor="start", fill=NOTE, italic=True, dy=3)
    # dims
    x = X_BAY0
    d.dim_h(X_BAY0, X_BAY0 + GEAR_MARGIN, -5, "3", ext=0, above=False)
    for n, gx, gw, gd, gh in gear_positions():
        d.dim_h(gx, gx + gw, -5, f"{gw:g}", ext=0, above=False)
        if gx + gw < X_BAY1 - GEAR_MARGIN - 1: d.dim_h(gx + gw, gx + gw + GEAR_GAP, -5, "6", ext=0, above=False)
    last = gear_positions()[-1]; d.dim_h(last[1] + last[2], X_BAY1, -5, "3.1", ext=0, above=False)
    d.dim_h(0, WING_W, -12, f"{WING_W:g}", above=False); d.dim_h(X_BAY0, X_BAY1, -12, f"{BAY_W:g}", above=False); d.dim_h(X_BAY1, W, -12, f"{WING_W:g}", above=False)
    d.dim_h(0, W, -19, f"{W:g}", above=False)
    if CAP_OVER > 0:
        d.dim_h(X_BAY0, CAP_W, D + 5, f"{CAP_OVER:g} cap overhang", ext=D); d.dim_h(W - CAP_W, X_BAY1, D + 5, f"{CAP_OVER:g}", ext=D)
    xr = W + 14
    if VARIANT == 1:
        d.dim_v(0, SLOT_Y0, xr, f"{SLOT_Y0:g}", ext=X_BAY1); d.dim_v(SLOT_Y0, SLOT_Y1, xr, f"{SLOT_Y1 - SLOT_Y0:g}", ext=X_BAY1); d.dim_v(SLOT_Y1, D, xr, f"{D - SLOT_Y1:g}", ext=X_BAY1)
    else:
        _deep = max(w[4] for w in well_positions())
        d.dim_v(0, GEAR_Y, xr, f"{GEAR_Y:g}", ext=X_BAY1)
        d.dim_v(GEAR_Y, _deep, xr, f"{_deep - GEAR_Y:g} deepest well", ext=X_BAY1)
        d.dim_v(_deep, Y_BACK0, xr, f"{Y_BACK0 - _deep:g} back rail", ext=X_BAY1)
        # own column, clear of the "back rail" label: rotated labels are longer than their own spans here
        d.dim_v(D, D + WALL_GAP, W + 32, f"{WALL_GAP:g} wall gap", ext=X_BAY1)
    d.dim_v(0, D, W + 24, "50")
    return d.render()

# ---------------- detail A: tray edge ----------------
def detail_tray():
    d = Drawing(-4, 24, 55, 84, scale=11.0, pad=(30, 20, 400, 40))
    x_panel = 0.0; x_slide = T; x_apron = T + SLIDE_T; x_tray = x_apron + T; x_kb = x_tray + KB_CLEAR
    d.rect(x_panel, 55, T, 29, fill=OAK)
    d.rect(x_slide, Z_TRAY_TOP, SLIDE_T, SLIDE_H, fill="#9a9a9a")
    d.line(x_slide + 0.6, Z_TRAY_TOP + 0.4, x_slide + 0.6, Z_TRAY_TOP + SLIDE_H - 0.4, stroke="#eee", sw=1)
    d.line(x_slide + 1.3, Z_TRAY_TOP + 0.4, x_slide + 1.3, Z_TRAY_TOP + SLIDE_H - 0.4, stroke="#eee", sw=1)
    d.rect(x_apron, Z_TRAY_UNDER, T, APRON_H, fill=OAK2)
    d.rect(x_tray, Z_TRAY_UNDER, 24 - x_tray, TRAY_T, fill=OAK)
    d.rect(x_tray, Z_TRAY_TOP, 24 - x_tray, 0.3, fill="#333", stroke="none")
    d.rect(x_kb, Z_TRAY_TOP + 0.3, 24 - x_kb, KB_H, fill="#2A2A2A", stroke="none")
    d.rect(x_kb + 1.5, Z_TRAY_TOP + 0.3 + KB_H - 0.4, 24 - x_kb - 1.5, 0.4, fill="#f2f2f2", stroke="none")
    d.rect(T, Z_CAV_TOP, 24 - T, T, fill=OAK)
    for zz in range(56, 61, 2): d.line(x_tray, zz, 24, zz + 1.2, stroke=GHOST, sw=0.5)
    d.text(x_tray + 8, 57.2, "book compartment below", size=8, fill=GHOST, italic=True)
    d.text(-2.2, 70, "wing column", size=8, rot=-90, fill=NOTE)
    d.dim_h(x_panel, x_slide, 82.5, "1.8"); d.dim_h(x_slide, x_apron, 82.5, "1.9"); d.dim_h(x_apron, x_tray, 82.5, "1.8"); d.dim_h(x_tray, x_kb, 82.5, "2.3")
    d.dim_v(Z_TRAY_TOP, Z_TRAY_TOP + SLIDE_H, x_apron + T / 2, "5", right=False)
    xg = x_kb - 0.5
    d.dim_v(Z_TRAY_TOP + 0.3, Z_TRAY_TOP + 0.3 + KB_H, xg, "12 keyboard", right=False)
    d.dim_v(Z_TRAY_TOP + 0.3 + KB_H, Z_CAV_TOP, xg, f"{Z_CAV_TOP - (Z_TRAY_TOP + 0.3 + KB_H):g}", right=False)
    d.dim_v(Z_TRAY_UNDER, Z_TRAY_TOP, 23.0, "1.8", right=False)
    R = 25.5
    d.leader(T + 8, Z_CAV_TOP + 0.9, R, 82.5, f"Fixed panel 18 mm at {Z_CAV_TOP:g} to {Z_FIX_TOP:g}; drawer band above")
    d.leader(x_slide + SLIDE_T / 2, Z_TRAY_TOP + 2.5, R, 78, "Heavy-duty slide 400 mm, 100 kg or more per pair, hold-open detent")
    d.leader(x_apron + T / 2, Z_TRAY_UNDER + 1.0, R, 73.5, "Solid oak apron 18 x 68 mm over the tray edge; slide screws into it")
    d.leader(x_kb + 6, Z_TRAY_TOP + 6, R, 69, "Keyboard 133 wide, 2.3 cm to each apron, key tops at about 74")
    d.leader(x_tray + 3, Z_TRAY_TOP + 0.15, R, 64.5, "Thin non-slip mat under the keyboard")
    d.leader(x_tray + 5, Z_TRAY_UNDER + 0.9, R, 60, "Tray 18 mm oak-veneered birch ply, 137.6 x 42, finished both faces")
    d.leader(T / 2, 59, R, 56.5, "Wing inner panel 18 mm = bay side wall; slide cabinet member fixes to it")
    return d.render()

# ---------------- detail B: gear well (v2) ----------------
def detail_well():
    d = Drawing(-4, 20, 86, 103, scale=16.0, pad=(30, 20, 430, 40))
    x0 = GEAR_Y                                                      # front rail depth
    x1 = 18.0                                                        # the well runs on past the cut
    d.rect(0, Z_WELL_FLOOR, x0, FASCIA_H + TT, fill=OAK)             # front rail in section
    d.line(0, Z_TOP_UNDER, x0, Z_TOP_UNDER, stroke=OAKE, sw=0.8, dash="3,2")
    d.rect(x0, Z_DRW_TOP - WELL_CLEAT, x1 - x0, WELL_CLEAT, fill=OAK2, stroke=GHOST, sw=0.8, dash="3,2")  # cleat on the side wall, beyond the cut
    d.rect(x0, Z_DRW_TOP, x1 - x0, T, fill=OAK2)                     # well floor 18 mm, 89.2 -> 91
    d.rect(x0, Z_WELL_FLOOR, x1 - x0, WELL_DROP, fill=GEARC, stroke="none")   # unit: stands on 91, a full 9 to the surface
    d.line(x0, H_TOP, 20, H_TOP, stroke=INK, sw=1.4)                 # the flush line
    d.dim_v(Z_WELL_FLOOR, H_TOP, -2, f"{WELL_DROP:g} clear", right=False)
    d.dim_v(Z_DRW_TOP, Z_WELL_FLOOR, -2, f"{T:g}", right=False)
    d.dim_v(Z_DRW_TOP - WELL_CLEAT, Z_DRW_TOP, -2, f"{WELL_CLEAT:g}", right=False)
    d.dim_v(Z_TOP_UNDER, H_TOP, 2.5, f"{TT:g}", right=False)
    d.dim_v(Z_WELL_FLOOR, Z_TOP_UNDER, 2.5, f"{FASCIA_H:g}", right=False)
    R = 21.0
    d.leader(3.5, Z_TOP_UNDER + 1.4, R, 101.5, "Oak top board 30 mm; cut-out edges eased, not lipped")
    d.leader(3.5, Z_WELL_FLOOR + 3.0, R, 99.3, f"Fascia 60 mm solid oak, front and ends; bottom edge at {Z_WELL_FLOOR:g}, level with the well floors")
    d.leader(x0 - 0.2, H_TOP - 1.0, R, 97.1, "Xone:92 and XDJ-700 faceplates may bear on a rebate; confirm against the units")
    d.leader(14, H_TOP, R, 94.9, "Faceplate flush with oak; 2 mm clearance at sides and rear, none at front — leave it open")
    d.leader(x0 + 3.0, Z_WELL_FLOOR + 0.25, R, 92.7, f"Technics plinth has no flange: stands on its own feet on the floor at {Z_WELL_FLOOR:g}")
    d.leader(x0 + 6.0, Z_DRW_TOP + T / 2, R, 90.5, f"Well floor 18 mm on slotted cleats, +/-10 mm: top face {Z_WELL_FLOOR:g}, underside {Z_DRW_TOP:g}")
    d.leader(x0 + 9.0, Z_DRW_TOP - WELL_CLEAT / 2, R, 88.3, f"Cleat 20 x {WELL_CLEAT * 10:g} mm, two per well, front to back; top face flush under the floor")
    d.leader(x1 - 1.0, Z_WELL_FLOOR + 5.0, R, 86.1, f"Player wells: rear wall notched {WELL_SLOT_W:g} cm wide into the trough; the Xone:92 has no rear wall")
    d.text(2.0, 86.4, "finger notches at two corners of each well, r 20 mm", size=8, fill=NOTE, italic=True, anchor="start")
    return d.render()

# ---------------- HTML ----------------
def parts_rows():
    rows = [
        ("Wings", "Wing side panel", 4, f"{Z_CAP_UNDER:g} × {D:g}", 18, "Oak-veneered birch ply, front edge lipped", "Floor to cap underside. Inner pair is also the bay side wall. Grain vertical."),
        ("Wings", "Wing bottom shelf", 2, f"{D - T:g} × {WING_INT_W:g}", 18, "Oak-veneered ply", "Top face at 7.8 cm (plinth 6 cm below)."),
        ("Wings", "Wing fixed shelf", 4, f"{D - T:g} × {WING_INT_W:g}", 18, "Oak-veneered ply, front edge lipped", "Two per wing, giving three openings of 38.5 cm clear."),
        ("Wings", "Wing back panel", 2, f"{WING_INT_H:g} × {WING_INT_W:g}", 18, "Oak-veneered ply", "Flush with the rear edge (no chase in the wings)."),
        ("Wings", "Wing plinth board", 2, f"{WING_INT_W:g} × {WING_PLINTH_H:g}", 18, "Solid oak", "Set back 3 cm from the front."),
        ("Wings", "Speaker cap", 2, f"{D:g} × {CAP_W:g}", 30, "Solid oak", "Same footprint as the column, flush on every side. Screwed from below through the wing panels."),
        ("Bay", "Top", 1, f"{BAY_W:g} × {D:g}", 30, "Solid oak, or 30 mm veneered board with 30 mm oak lipping",
         "Routed cable slot 115 × 6 cm, 41 cm from the front edge, centred, ends rounded r 3. Passes plugs and the XDJ bricks."
         if VARIANT == 1 else
         f"Four cut-outs for the gear, all front edges {GEAR_Y:g} cm from the front edge. Sizes per the plan; 2 mm clearance at sides and rear, none at the front. Finger notches r 20 mm at two corners of each. Edges eased, not lipped."),
    ]
    if VARIANT == 2:
        _wp = well_positions()
        _players = [w for w in _wp if w[0] != "Xone:92"]
        _xone_w = [w[2] for w in _wp if w[0] == "Xone:92"][0]
        _well_wid = ", ".join(f"{n} {w:g}" for n, x, w, y0, y1, fz in _players)
        _well_dep = ", ".join(f"{n} {y1 - y0:g}" for n, x, w, y0, y1, fz in _wp)
        _well_wxd = ", ".join(f"{n} {w:g} × {y1 - y0:g}" for n, x, w, y0, y1, fz in _wp)
        rows += [
            ("Bay", "Slab fascia", 1, f"{BAY_W:g} × {FASCIA_H:g}", int(FASCIA_D * 10), "Solid oak", f"Front face, returned on both ends. Bottom edge at {Z_WELL_FLOOR:g}, flush with the well floors. Makes the top read as a {TT + FASCIA_H:g} cm slab."),
            ("Bay", "Well side wall", 8, f"{WELL_WALL_H:g} high, depth per well", 18, "Oak-veneered ply", f"Two per well, hung from the underside of the top board down to {Z_DRW_TOP:g}, the well floor's underside: the bottom {T*10:g} mm of each wall houses the floor and carries its cleat. Glued to the top board: this is what stiffens the webs between the wells. Depth per well: {_well_dep} cm. See the section on {dref('well')}."),
            ("Bay", "Well rear wall", 3, f"{FASCIA_H:g} high, width per well", 18, "Oak-veneered ply", f"One per player well only: the turntable and both XDJ-700s. Each is notched {WELL_SLOT_W:g} × {FASCIA_H:g} cm for cables — {WELL_SLOT_W:g} cm wide, centred on the well, cut from the well floor at {Z_WELL_FLOOR:g} clear up to the top board, so a plug passes without being lifted. The Xone:92's well has no rear wall at all: its whole rear face, {_xone_w:g} × {FASCIA_H:g} cm, stands open into the trough, which is how the mixer sheds its heat. Width per wall: {_well_wid} cm. See the section on {dref('well')}."),
            ("Bay", "Well floor", 4, "width × depth per well", 18, "Oak-veneered ply", f"Top face at {Z_WELL_FLOOR:g}, underside at {Z_DRW_TOP:g} — the ceiling of the drawer band. On adjustable cleats, slotted +/- 10 mm, so the flush line is set against the real units at fit-out. Width × depth per well: {_well_wxd} cm. See the section on {dref('well')}."),
            ("Bay", "Well floor cleat", 8, f"20 × {WELL_CLEAT*10:g} mm, length per well", 20, "Solid oak", f"Two per well, front to back on the side walls, slotted screw holes. Top face at {Z_DRW_TOP:g} so the floor lands at {Z_WELL_FLOOR:g} and nothing stands proud of it. Length per well: {_well_dep} cm. See the section on {dref('well')}."),
        ]
    rows += [
        ("Bay", "Bay bottom panel", 1, f"{BAY_W:g} × {Y_BACK1 - BOOK_SETBACK:g}", 18, "Oak-veneered ply, front edge lipped",
         "Top face at 21.8 cm. Carries the books; stiffened by the divider and the back panel, no rail underneath."
         if not BOOK_SETBACK else
         f"Top face at 21.8 cm. Front edge set back {BOOK_SETBACK:g} cm from the front plane for shin clearance; the recess is therefore open from the floor to the tray underside across that {BOOK_SETBACK:g} cm. Carries the books; stiffened by the divider and the back panel, no rail underneath."),
        ("Bay", "Fixed mid panel", 1, f"{BAY_W:g} × {INT_D:g}", 18, "Oak-veneered ply, front edge lipped", f"Top face at {Z_FIX_TOP:g} cm. Ceiling of the keyboard slot, floor of the drawer band."),
        ("Bay", "Bay back panel", 1, f"{BAY_W:g} × {Z_BACK_TOP - Z_BOT_TOP:g}", 18, "Oak-veneered ply",
         ("Inset 5 cm. " if VARIANT == 1 else f"Flush with the rear face, top edge at {Z_BACK_TOP:g}: there is no panel above that, so the trough's rear face stands open across the whole bay, {BAY_W:g} × {FASCIA_H:g} cm. That opening is how the trough breathes and how the leads leave. ")
         + f"Cutout {CUT_W:g} × {CUT_H:g} cm behind the tray at {CUT_Z0:g} to {CUT_Z0 + CUT_H:g} cm; cutout {NICHE_W:g} × {NICHE_CUT_H_EFF:g} cm behind the niche at {NICHE_CUT_Z0:g} to {NICHE_CUT_Z0 + NICHE_CUT_H_EFF:g} cm."
         + ("" if VARIANT == 1 else f" The niche cutout runs out at the panel's top edge, where the open trough takes over.")),
        ("Bay", "Book zone divider", 1, f"{BOOK_D:g} × {Z_TRAY_UNDER - Z_BOT_TOP - 0.5:g}", 18, "Oak-veneered ply, front edge lipped", "Centred. Glued and screwed to bottom and back panel along its length; 5 mm gap under the tray."),
        ("Bay", "Drawer band divider", 2, f"{INT_D:g} × {FRONT_H:g}", 18, "Oak-veneered ply, front edge lipped",   # the blank: v2 notches it down behind the front
         "Frame the 24 cm power niche. Optional 6 × 4 cm pass-through at the rear of each for a charging lead."
         if VARIANT == 1 else
         f"Frame the 24 cm power niche. Notched: the front {GEAR_Y:g} cm rises to {FRONT_H:g} cm with the fronts, closing the strip behind the gaps between them; behind that it drops to {DRW_H:g} cm to pass under the well floors. Optional 6 × 4 cm pass-through at the rear of each for a charging lead."),
        ("Bay", "Power niche door", 1, f"{NICHE_W - 2 * GAP:g} × {NICHE_DOOR_H:g}", 18, "Solid oak, grain continuous with the drawer fronts",
         f"Flush inset, concealed hinges, push-to-open latch. {NICHE_DOOR_H:g} cm in the {FRONT_H:g} cm opening: the {NICHE_VENT:g} cm vent gap is all taken at the bottom edge."
         if VARIANT == 1 else
         f"Flush inset, concealed hinges, push-to-open latch. {NICHE_DOOR_H:g} cm in the {FRONT_H:g} cm opening: the {NICHE_VENT:g} cm vent gap is all taken at the bottom edge, so the top edge still meets the fascia at {Z_WELL_FLOOR:g}."),
        ("Bay", "Adjustable shelf", 2, f"{OPEN_W - 0.2:g} × {BOOK_D - 1.0:g}", 18, "Oak-veneered ply, front edge lipped", "One per book compartment, on 5 mm pins."),
        ("Bay", "Drawer front", 2, f"{DRW_W - 0.4:g} × {FRONT_H - 0.4:g}", 18, "Solid oak (grain running across both fronts)",
         "Flush inset, 2 mm gaps, finger pull routed under the top edge."
         if VARIANT == 1 else
         f"Flush inset, 2 mm gaps, finger pull routed under the top edge. {FRONT_H:g} cm on a {DRW_H:g} cm box: it overhangs the box {T*10:g} mm upward to meet the fascia at {Z_WELL_FLOOR:g}, closing the face. Clear behind, because the well floors start {GEAR_Y:g} cm back. Size off the opening, not off the box."),
        ("Bay", "Drawer box", 2, "45 deep × 7 high, width per runner spec" if VARIANT == 2 else "40 deep × 12 high, width per runner spec", 15, "Birch ply, 6 mm bottom",
         "For the 58.7 cm openings, sized to the runners. Notch the niche-side wall 6 × 4 cm at the rear if the pass-through is used."
         if VARIANT == 1 else
         f"For the 58.7 cm openings, sized to the runners. The 45 cm depth is matched to 450 mm undermount runners: an undermount pair only engages a box of its own length, so the 400 mm runners used in v1 will not do. 7 cm sides in the {DRW_H:g} cm band leave {(DRW_H - 7.0) * 10:g} mm below and above the box for the runner and its clearances — check against the runner's own drilling diagram before cutting. Notch the niche-side wall 6 × 4 cm at the rear if the pass-through is used."),
        ("Tray", "Keyboard tray panel", 1, f"{TRAY_PANEL_W:g} × {TRAY_D:g}", 18, "Oak-veneered birch ply, both faces", "Underside is visible from the book compartments: finish it. Front edge lipped."),
        ("Tray", "Tray side apron", 2, f"{TRAY_D:g} × {APRON_H:g}", 18, "Solid oak", "Covers the tray edge (1.8) and rises 5 cm above it. Slide drawer member screws into it."),
        ("Tray", "Tray rear rail", 1, f"{TRAY_PANEL_W:g} × {APRON_UP:g}", 18, "Solid oak", "On the tray top along the rear edge, doweled to the aprons. Stops racking."),
        ("All", "Solid oak lipping", "~28 m", "5 × 18 mm", "", "Solid oak", "All exposed ply edges."),
    ]
    return rows

# ---------------- cut list (v2) ----------------
# The parts list is the assembly reference. The cut list is the same wood the way a supplier prices
# it: every piece at its finished size, the per-well pieces spelled out, the drawer boxes broken into
# panels, and a total per stock. cut_list_check() ties it back to the parts list, so the two cannot
# drift apart.
SHEET_L, SHEET_W = 250.0, 125.0                 # veneered ply sheet, face grain along SHEET_L
KERF = 0.4                                      # panel-saw kerf
LIPPING_M = 28                                  # m: the parts list's figure for every exposed ply edge
_DBOX_T, _DBOX_H = 1.5, 7.0                     # drawer boxes: 15 mm birch ply, 7 cm sides (parts list)

def _wells_by_unit():
    """{unit: (wells, cut-out width, cut-out depth)} in bay order; the two XDJ-700 wells are one entry."""
    out = {}
    for n, x, w, y0, y1, fz in well_positions():
        out[n] = (out.get(n, (0,))[0] + 1, w, y1 - y0)
    return out

def cut_list():
    """{stock: [(part, qty, L, W, thk_mm, grain, note)]} at finished sizes, L × W in cm.

    grain=True keeps L along the face grain: the pieces the spec gives a direction (vertical on the
    wing panels, horizontal on the long panels). The others may turn to nest on the sheet.
    """
    wells = _wells_by_unit()
    lip, grain = "Front edge lipped.", "Grain along L."
    ply = [
        ("Wing side panel", 4, Z_CAP_UNDER, D, 18, True, f"{grain} {lip}"),
        ("Wing bottom shelf", 2, D - T, WING_INT_W, 18, False, ""),
        ("Wing fixed shelf", 4, D - T, WING_INT_W, 18, False, lip),
        ("Wing back panel", 2, WING_INT_H, WING_INT_W, 18, True, grain),
        ("Bay bottom panel", 1, BAY_W, Y_BACK1 - BOOK_SETBACK, 18, True, f"{grain} {lip}"),
        ("Fixed mid panel", 1, BAY_W, INT_D, 18, True, f"{grain} {lip}"),
        ("Bay back panel", 1, BAY_W, Z_BACK_TOP - Z_BOT_TOP, 18, True, f"{grain} Two cutouts, see the parts list."),
        ("Book zone divider", 1, BOOK_D, Z_TRAY_UNDER - Z_BOT_TOP - 0.5, 18, False, lip),
        ("Drawer band divider", 2, INT_D, FRONT_H, 18, False, f"Notched down to {DRW_H:g} behind the front {GEAR_Y:g} cm. {lip}"),
        ("Adjustable shelf", 2, OPEN_W - 0.2, BOOK_D - 1.0, 18, True, f"{grain} {lip}"),
    ]
    ply += [(f"Well side wall ({n})", 2 * k, d, WELL_WALL_H, 18, False, "") for n, (k, w, d) in wells.items()]
    ply += [(f"Well rear wall ({n})", 2 * k, (w - WELL_SLOT_W) / 2, FASCIA_H, 18, False,
             f"Two pieces per wall, either side of the {WELL_SLOT_W:g} cm cable notch.")
            for n, (k, w, d) in wells.items() if n != "Xone:92"]
    ply += [(f"Well floor ({n})", k, w, d, 18, False, "") for n, (k, w, d) in wells.items()]
    ply.append(("Keyboard tray panel", 1, TRAY_PANEL_W, TRAY_D, 18, True, f"{grain} Both faces show. {lip}"))
    oak = [
        ("Top", 1, BAY_W, D, TT * 10, False, f"Four gear cut-outs, see {dref('plan')}. Glued up from boards, or 30 mm veneered board with 30 mm oak lipping."),
        ("Speaker cap", 2, D, CAP_W, TT * 10, False, ""),
        ("Slab fascia", 1, BAY_W, FASCIA_H, FASCIA_D * 10, False, f"Fills the {GEAR_Y:g} cm front rail under the top board, from {Z_WELL_FLOOR:g} to {Z_TOP_UNDER:g}. See {dref('well')}."),
        ("Wing plinth board", 2, WING_INT_W, WING_PLINTH_H, 18, False, ""),
        ("Drawer front", 2, DRW_W - 0.4, FRONT_H - 0.4, 18, False,
         f"Cut both fronts and the niche door in sequence from one board at least {BAY_W:g} × {FRONT_H - 0.4:g}, so the grain runs on across all three."),
        ("Power niche door", 1, NICHE_W - 2 * GAP, NICHE_DOOR_H, 18, False, "From the same board as the drawer fronts."),
        ("Tray side apron", 2, TRAY_D, APRON_H, 18, False, ""),
        ("Tray rear rail", 1, TRAY_PANEL_W, APRON_UP, 18, False, ""),
    ]
    oak += [(f"Well floor cleat ({n})", 2 * k, d, WELL_CLEAT, 20, False, "") for n, (k, w, d) in wells.items()]
    box_w, box_d = DRW_W, _RUNNER_NL / 10       # nominal: as wide as the opening; the runner sets the real width
    nominal = (f"Nominal, for pricing: drawn for a box the full {DRW_W:g} cm width of its opening. "
               "The runner's instructions set the final width.")
    birch = [
        ("Drawer box side", 4, box_d, _DBOX_H, _DBOX_T * 10, False, ""),
        ("Drawer box front and back", 4, box_w - 2 * _DBOX_T, _DBOX_H, _DBOX_T * 10, False, nominal),
        ("Drawer box bottom", 2, box_w - 2 * _DBOX_T, box_d - 2 * _DBOX_T, 6, False, "Nominal, as above."),
    ]
    return {"ply": ply, "oak": oak, "birch": birch}

def cut_list_check(cut):
    """A part in both lists has one count, size and thickness; the per-well pieces add up to the parts list."""
    parts = {r[1]: r for r in parts_rows()}
    for part, qty, L, W, thk, grain, note in cut["ply"] + cut["oak"]:
        if part in parts:
            pq, psize, pthk = parts[part][2:5]
            assert (pq, psize, pthk) == (qty, f"{L:g} × {W:g}", thk), (part, (pq, psize, pthk), (qty, L, W, thk))
    def total(prefix): return sum(r[1] for r in cut["ply"] + cut["oak"] if r[0].startswith(prefix))
    assert total("Well side wall") == parts["Well side wall"][2]
    assert total("Well floor (") == parts["Well floor"][2]
    assert total("Well floor cleat") == parts["Well floor cleat"][2]
    assert total("Well rear wall") == 2 * parts["Well rear wall"][2]     # the full-height notch splits every wall

def ply_sheets(pieces):
    """(sheets a layout uses, the fewest any layout could use) for [(L, W, grain)] on SHEET_L × SHEET_W.

    The layout packs strips cut across the sheet: one crosscut frees a strip, rips free its pieces,
    so a panel saw can cut it as drawn. A grain piece keeps L along SHEET_L; the others may turn.
    The floor: no two pieces longer than half a sheet fit end to end, so each sheet holds one strip
    of them and their widths side by side need that many sheets; the area gives the other floor.
    """
    sheets = []                                 # [length left, [[strip length, width used]]]
    def place(pl, pw):
        for left, strips in sheets:
            for st in strips:
                if pl <= st[0] and st[1] + KERF + pw <= SHEET_W:
                    st[1] += KERF + pw
                    return True
        for sh in sheets:
            if sh[0] >= pl + KERF:
                sh[0] -= pl + KERF; sh[1].append([pl, pw])
                return True
        return False
    for L, W, grain in sorted(pieces, key=lambda p: -(p[0] if p[2] else max(p[0], p[1]))):
        turns = [(L, W)] if grain else [(max(L, W), min(L, W)), (min(L, W), max(L, W))]
        assert turns[0][0] <= SHEET_L and turns[0][1] <= SHEET_W
        if not any(place(pl, pw) for pl, pw in turns):
            sheets.append([SHEET_L - turns[0][0] - KERF, [list(turns[0])]])
    long_w = sum(W for L, W, grain in pieces if grain and L > (SHEET_L - KERF) / 2)
    floor = max(math.ceil(long_w / SHEET_W), math.ceil(sum(L * W for L, W, g in pieces) / (SHEET_L * SHEET_W)))
    return len(sheets), floor

def cut_totals(cut):
    """(rows for the totals table, the sheet note, sheet count) from the cut list."""
    ply, oak, birch = cut["ply"], cut["oak"], cut["birch"]
    def pcs(rows): return sum(r[1] for r in rows)
    def m2(rows): return sum(r[1] * r[2] * r[3] for r in rows) / 1e4
    def thick(rows, t): return [r for r in rows if r[4] == t]
    cleats = [r for r in oak if r[0].startswith("Well floor cleat")]
    boards = [r for r in oak if r not in cleats]
    sheets, floor = ply_sheets([(r[2], r[3], r[5]) for r in ply for _ in range(r[1])])
    assert sheets == floor, (sheets, floor)     # the layout is as good as any: fewer sheets cannot exist
    by_area = math.ceil(m2(ply) / (SHEET_L * SHEET_W / 1e4))
    longs = [r for r in ply if r[5] and r[2] > (SHEET_L - KERF) / 2]
    names = [r[0].lower() + ("s" if r[1] > 1 else "") for r in longs]
    names = ", ".join(names[:-1]) + " and " + names[-1]
    long_w = sum(r[1] * r[3] for r in longs)
    fronts = f"{BAY_W:g} × {FRONT_H - 0.4:g}"
    rows = [
        ("Oak-veneered birch plywood, 18 mm, A/B crown-cut", pcs(ply), f"{m2(ply):.2f} m²",
         f"{sheets} sheets of {SHEET_L:g} × {SHEET_W:g}, face grain along the {SHEET_L:g}. See the note below."),
        ("Solid oak, 30 mm", pcs(thick(boards, 30)), f"{m2(thick(boards, 30)):.2f} m²", "Top and speaker caps, glued up from boards."),
        ("Solid oak, 50 mm", pcs(thick(boards, 50)), f"{m2(thick(boards, 50)):.2f} m²", f"Slab fascia, one piece {BAY_W:g} × {FASCIA_H:g}."),
        ("Solid oak, 18 mm", pcs(thick(boards, 18)), f"{m2(thick(boards, 18)):.2f} m²",
         f"Drawer fronts, niche door, plinths, tray aprons and rail. The fronts and the door come from one board at least {fronts}."),
        (f"Solid oak, 20 × {WELL_CLEAT * 10:g} mm", pcs(cleats), f"{sum(r[1] * r[2] for r in cleats) / 100:.1f} m", "Well floor cleats."),
        ("Solid oak lipping, 5 × 18 mm", "", f"about {LIPPING_M} m", "All exposed ply edges."),
        ("Birch plywood, 15 mm", pcs(thick(birch, 15)), f"{m2(thick(birch, 15)):.2f} m²", "Drawer box sides, fronts and backs, nominal."),
        ("Birch plywood, 6 mm", pcs(thick(birch, 6)), f"{m2(thick(birch, 6)):.2f} m²", "Drawer box bottoms, nominal."),
        ("Total", pcs(ply) + pcs(oak) + pcs(birch), "", "Pieces, plus the lipping."),
    ]
    note = (f"Why {sheets} sheets when {m2(ply):.2f} m² would fit on {by_area}: the grain sets the count, not the area. "
            f"The {names} are each longer than half a sheet, so each runs along a sheet's {SHEET_L:g} cm length and no two fit end to end: every sheet takes one row of them. "
            f"Side by side they need {long_w:g} cm, and {sheets - 1} sheets are only {(sheets - 1) * SHEET_W:g} cm wide. "
            f"All {pcs(ply)} pieces fit on {sheets} sheets with {KERF * 10:g} mm saw kerfs.")
    return rows, note, sheets

def _cols(tbl, widths):
    """Pin a table's column widths (%), so the cut list's tables line up one under another."""
    return tbl.replace("<table>", "<table><colgroup>" + "".join(f'<col style="width:{w}%">' for w in widths) + "</colgroup>", 1)

def cut_list_html():
    cut = cut_list()
    cut_list_check(cut)
    totals, note, _sheets = cut_totals(cut)
    head, widths = ["Part", "Qty", "L × W (cm)", "Thk (mm)", "Notes"], (24, 5, 12, 7, 52)
    def rows(rs): return [(p, q, f"{L:g} × {W:g}", f"{t:g}", n) for p, q, L, W, t, g, n in rs]
    lipping = ("Solid oak lipping", f"~{LIPPING_M} m", "1.8 wide", "5", "All exposed ply edges.")
    return (f'<div class="page cut"><h2>Cut list for quoting</h2>'
            f'<p class="muted">Every piece of wood at its finished size, grouped by the stock it is cut from, so a supplier or a carpenter can price the job without reading the drawings. '
            f'Sizes in cm, L × W; thickness in mm. "Grain along L" marks the pieces whose grain direction the spec fixes; the rest may be turned to nest. '
            f'No machining allowance or waste is included. The parts list stays the assembly reference.</p>'
            f'<h3>Totals</h3>{_cols(table(["Stock", "Pieces", "Net quantity", "Notes"], totals), (30, 7, 13, 50))}'
            f'<p class="muted">{H.escape(note)}</p>'
            f'<h3>18 mm oak-veneered birch plywood</h3>{_cols(table(head, rows(cut["ply"])), widths)}'
            f'<h3>Solid oak</h3>{_cols(table(head, rows(cut["oak"]) + [lipping]), widths)}'
            f'<h3>Birch plywood, drawer boxes</h3>{_cols(table(head, rows(cut["birch"])), widths)}'
            '</div>')

_STRIP_H = 4.0                                  # typical power-strip height, cm
_BRICK_H = 8.5                                  # typical wall-wart brick height, cm -- measure the actual units
_BRICK_TOP = Z_FIX_TOP + _BRICK_H               # a floor-standing brick's top, cm
_STACK_TOP = Z_FIX_TOP + _STRIP_H + _BRICK_H    # a brick stacked on the strip, cm
# Headroom over the niche floor depends on where in the niche you stand: at the front a well floor
# is the ceiling, at the rear (beyond the deepest well) the open trough runs up to the back rail.
_NICHE_REAR_Y0 = max(w[4] for w in well_positions())            # 41.2: where the well floors stop
_NICHE_REAR_H = Z_TOP_UNDER - Z_FIX_TOP                          # 17.0: open trough overhead, to the back rail
_NICHE_FRONT_H = Z_DRW_TOP - Z_FIX_TOP                           # 9.2: under a well floor
_BRICK_FRONT_MM = round((Z_DRW_TOP - _BRICK_TOP) * 10, 1)        # 7 mm, and only at the front
_RUNNER_NL = 450                                # v2 drawer-box depth is 45 cm, so the runners are 450 mm
_RUNNER_MIN_D = 470                             # clear cabinet depth a 450 mm undermount runner wants, mm

BOTH = (1, 2)                                   # a hardware row that both variants need
# Every row carries the variants it belongs to. A row leaves v2 because it is tagged (1,), never
# because its label matched a string: renaming a row must not move it between variants.
HARDWARE_ROWS = [
    (BOTH, "Keyboard tray slides", "1 pair", "Heavy-duty full-extension ball-bearing, 400 mm, rated 100 kg or more per pair, with hold-open detent. Accuride 3634 (400 mm) or Fulterer FR 5000 (400 mm). Side mount at 63 to 68 cm."),
    (BOTH, "Drawer runners", "2 pairs",
     "Full-extension undermount with soft close, 400 mm, 40 kg class. Blum Movento 760H4000S with Blumotion, or Hettich Actro 5D."
     if VARIANT == 1 else
     f"Full-extension undermount with soft close, {_RUNNER_NL:g} mm, 40 kg class: Blum Movento 760H4500S with Blumotion, or Hettich Actro 5D {_RUNNER_NL:g} mm. Not the 400 mm pair used in v1 — an undermount runner is matched to its box, and a {_RUNNER_NL / 10:g} cm box will not engage a 400 mm runner. Confirmed against the interior: a {_RUNNER_NL:g} mm runner wants about {_RUNNER_MIN_D:g} mm of clear depth and the bay gives {INT_D * 10:g} mm, so it fits with about {INT_D * 10 - _RUNNER_MIN_D:g} mm to spare."),
    (BOTH, "Shelf pins", "8", f"5 mm steel, two adjustable shelves. {PIN_PITCH * 10:g} mm pitch; rows {PIN_ROW_FRONT:g} and {PIN_ROW_BACK:g} cm back from the console face, {PIN_INSET * 10:g} mm in from the compartment's faces."),
    (BOTH, "Levelling feet", "8", "M8 adjustable glides, 15 to 25 mm, two per wing side panel, hidden behind the plinth boards."),
    (BOTH, "Anti-tip brackets", "2",
     "One per wing, concealed, fixed to the wall. Recommended: the wings are 130 cm tall with speakers on top."
     if VARIANT == 1 else
     f"One per wing, concealed, fixed to the wall. Recommended: the wings are 130 cm tall with speakers on top. In v2 it doubles as a spacer: pack it out to {WALL_GAP:g} cm so it holds the console that far off the wall rather than pulling it flush. The trough's open rear vents into that gap, so closing it would seal the mixer in."),
    (BOTH, "Speaker isolation pads", "2", "IsoAcoustics ISO-155 or Auralex MoPAD, set with a slight upward tilt toward the standing position."),
    (BOTH, "Headphone hook", "1", "Black steel or oak, on the outer face of the right wing at about 105 cm."),
    (BOTH, "Power strip", "1",
     f"6-way with switch, up to 40 cm long, or two 4-way strips side by side. Lies on the niche floor with sockets facing up; bricks stand on it. Niche is {NICHE_W:g} wide × {DRW_H:g} tall × {INT_D + BACK_INSET:g} deep including the chase."
     if VARIANT == 1 else
     f"6-way with switch, up to 40 cm long, or two 4-way strips side by side. Lies flat on the niche floor with sockets facing up. Niche is 24 wide × {DRW_H:g} tall × {INT_D:g} deep, its rear {INT_D - _NICHE_REAR_Y0:g} cm open at the top into the cable trough and the rest ceilinged by the well floors. "
     f"Stand the bricks on the niche floor beside the strip, toward the rear — {_NICHE_REAR_Y0:g} to {INT_D:g} cm back from the front, past the point where the well floors stop. There the trough is open overhead and the headroom is {_NICHE_REAR_H:g} cm, up to the underside of the back rail at {Z_TOP_UNDER:g}, so brick height is not a constraint at that position. "
     f"Do not stack a brick on the strip: that reaches about {_STRIP_H + _BRICK_H:g} cm above the niche floor, to {_STACK_TOP:g}, which fouls the well floor if it is anywhere near the front of the niche and blocks the trough if it is at the rear — and the trough has to stay clear as the route for the mains lead out through the niche cutout at {NICHE_CUT_Z0:g} to {NICHE_CUT_Z0 + NICHE_CUT_H_EFF:g} cm. "
     f"Height only matters if a brick has to sit at the front of the niche instead, under a well floor: {_NICHE_FRONT_H:g} cm of headroom there, which an {_BRICK_H:g} cm brick clears by {_BRICK_FRONT_MM:g} mm."),
    (BOTH, "Niche door hardware", "1 set", f"Two concealed hinges (Blum Clip top or similar) and a push-to-open latch (Blum Tip-On): no handle. Its {NICHE_VENT:g} cm vent gap goes at the bottom edge."),
    ((1,), "Cable slot brush strip", "1 (optional)", "Black brush grommet strip 115 cm, for a 60 mm slot, to line the slot."),   # v1 only: v2 has no cable slot
    (BOTH, "Drawer pass-through grommets", "2 (optional)", "Rubber or oak-lined 60 × 40 mm grommets in the drawer-band dividers, for charging leads from the strip into the drawers."),
    (BOTH, "Non-slip mat", "1", "Thin rubber or EVA sheet, about 133 × 35 cm, under the keyboard."),
    (BOTH, "Carcass fixings", "as needed", "8 mm dowels and glue at all visible joints; concealed confirmat screws where hidden (behind drawers and tray). Slide screws per manufacturer."),
    (BOTH, "Finish", "about 1 L", "Osmo Polyx-Oil 3062 Matt, two coats, or Rubio Monocoat Oil Plus 2C Pure (about 350 ml). Natural oak tone, no stain."),
    ((2,), "Well floor cleats and fixings", "8 cleats", "M5 threaded inserts and pan screws in slotted holes, +/- 10 mm of travel, so each unit's flush line is set at fit-out rather than at cutting."),
]
HARDWARE = [row[1:] for row in HARDWARE_ROWS if VARIANT in row[0]]

def table(headers, rows):
    th = "".join(f"<th>{H.escape(str(h))}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(f"<td>{H.escape(str(c))}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>"

def build_html(svgs, render_path=None):
    today = datetime.date.today().strftime("%d %B %Y")
    version_line = "Version 1.7" if VARIANT == 1 else "Version 2.0 — flush-mounted gear"
    gear_rows, gear_head = [], ["Device", "W × D × H (cm)", "Position from left wing inner face (cm)"]
    if VARIANT == 2:
        gear_head = ["Device", "W × D × H overall (cm)", f"Height below the faceplate (cm), must fit {WELL_DROP:g}",
                     "Position from left wing inner face (cm)"]
    for n, gx, gw, gd, gh in gear_positions():
        pos = f"{gx - X_BAY0:g} to {gx - X_BAY0 + gw:g}"
        gear_rows.append((n, f"{gw:g} × {gd:g} × {gh:g}", pos) if VARIANT == 1
                         else (n, f"{gw:g} × {gd:g} × {gh:g}", "measure this unit", pos))
    zones = [
        ("Speaker caps", "127 to 130", f"Two 5-inch monitors on isolation pads, one per wing. Cap {CAP_W:g} × {D:g} cm, 30 mm oak, flush with the column on every side. A KRK Rokit 5 (18.5 wide) leaves 7 mm each side."),
        ("DJ surface",
         "100 (top 97 to 100)" if VARIANT == 1 else f"100 (slab {Z_WELL_FLOOR:g} to 100)",
         ("Turntable, XDJ-700, Xone:92, XDJ-700 left to right, within a 145 cm span, 2 cm back from the front edge. Cable slot 115 × 6 cm behind the gear, wide enough for plugs and the XDJ power bricks."
          if VARIANT == 1 else
          f"Turntable, XDJ-700, Xone:92, XDJ-700 left to right within the {BAY_W:g} cm bay, each sunk into a well that gives {WELL_DROP:g} cm of clearance below its faceplate — not below its overall height. Faceplates finish flush with the oak. Front rail {GEAR_Y:g} cm, oak webs about 5.6 cm. Dust covers cannot be fitted.")),
        ("Drawer band",
         "81.8 to 97" if VARIANT == 1 else f"{Z_FIX_TOP:g} to {Z_DRW_TOP:g} (fronts to {Z_WELL_FLOOR:g})",
         ("Two flush drawers of 58.7 cm (cables and adapters left, headphones right) with a 24 cm power niche between them: push-to-open door, strip and wall-wart bricks inside, open at the back into the cable chase."
          if VARIANT == 1 else
          f"Two flush drawers of 58.7 cm ({DRW_H:g} cm high) with a 24 cm power niche between them: push-to-open door, strip and bricks inside, open at the top into the cable trough.")),
    ]
    if VARIANT == 2:
        zones.append(("Cable trough", f"{Z_WELL_FLOOR:g} to {Z_TOP_UNDER:g}", f"Continuous under the back rail, full {BAY_W:g} cm bay, 7 cm deep behind the Xone:92 and 12.2 behind the XDJs. Every well opens into it. Its own rear face is open too, {BAY_W:g} × {FASCIA_H:g} cm, so air enters and leaves along its whole length into the {WALL_GAP:g} cm wall gap; also the mixer's ventilation."))
    zones += [
        ("Keyboard slot", f"63 to {Z_CAV_TOP:g}", f"Pull-out tray, top face at 63 cm, 40 cm extension on heavy-duty slides. Keyboard 133 × 35 × 12 stowed inside, {Z_CAV_TOP - (Z_TRAY_TOP + KB_H):g} cm air above it."),
        ("Book compartments", "21.8 to 61.2",
         ("Two openings 71.6 wide × 39.4 tall × 43.2 deep, one adjustable shelf each. Tall enough for LPs and art books."
          if not BOOK_SETBACK else
          f"Two openings 71.6 wide × 39.4 tall × {BOOK_D:g} deep, one adjustable shelf each. Front plane set back {BOOK_SETBACK:g} cm from the console face for seated shin clearance. Still takes a 31.4 cm LP sleeve, with 1.8 cm to spare.")),
        ("Recess",
         "0 to 20" if not BOOK_SETBACK else "0 to 20 (to 61.2 at the front)",
         ("Open across the whole bay and through to the wall: sustain pedal and feet when seated, toe space when standing."
          if not BOOK_SETBACK else
          f"Open across the whole bay and through to the wall: sustain pedal and feet when seated, toe space when standing. The front {BOOK_SETBACK:g} cm stands open right up to the tray underside, so the shins clear the shelving.")),
        ("Wing columns", "7.8 to 127", f"Three openings per wing, {WING_INT_W:g} wide × 38.5 tall × 48.2 deep, records spine-out, about {REC_PER} per opening at 6 mm each, about {REC_TOTAL} in total."),
    ]
    render_block = ""
    if render_path and os.path.exists(render_path):
        render_block = f'<div class="page"><h2>Concept render</h2><p class="muted">Computer-generated view built from the drawing geometry (Three.js). Materials, lighting and gear details are indicative; the drawings govern.</p><img src="{os.path.basename(render_path)}" style="max-width:100%;max-height:165mm;display:block;margin:0 auto;border:1px solid #ddd"></div>'
    css = """
    @page { size: A4 landscape; margin: 11mm 12mm; }
    * { box-sizing: border-box; }
    body { font-family: -apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #1e1e1e; font-size: 10.5pt; line-height: 1.4; margin: 0; }
    .wrap { max-width: 1180px; margin: 0 auto; padding: 24px; }
    @media print { .wrap { max-width: none; padding: 0; } }
    h1 { font-size: 22pt; margin: 0 0 2pt; letter-spacing: -0.01em; }
    h2 { font-size: 13.5pt; margin: 0 0 6pt; padding-bottom: 3pt; border-bottom: 1px solid #cfcfcf; }
    h3 { font-size: 11pt; margin: 10pt 0 4pt; }
    p { margin: 0 0 6pt; }
    .muted { color: #666; font-size: 9.5pt; }
    table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 4pt 0 8pt; }
    th, td { border: 1px solid #d9d9d9; padding: 2.5pt 5pt; text-align: left; vertical-align: top; }
    th { background: #f3efe6; font-weight: 600; }
    .page { page-break-after: always; break-after: page; margin-bottom: 28px; }
    .page:last-child { page-break-after: auto; }
    .drawing svg { display: block; margin: 0 auto; width: auto; max-width: 100%; }
    .cols { display: flex; gap: 22px; } .cols > div { flex: 1; min-width: 0; }
    ul { margin: 0 0 6pt 16pt; padding: 0; } li { margin-bottom: 2pt; }
    .kv td:first-child { font-weight: 600; width: 34%; }
    .parts table { font-size: 7.9pt; } .parts th, .parts td { padding: 1.5pt 4pt; }
    .parts th:nth-child(1) { width: 6%; } .parts th:nth-child(2) { width: 14%; } .parts th:nth-child(3) { width: 5%; } .parts th:nth-child(4) { width: 15%; } .parts th:nth-child(5) { width: 5%; } .parts th:nth-child(6) { width: 22%; }
    .cut table { font-size: 7.9pt; } .cut th, .cut td { padding: 1.5pt 4pt; }
    h2, h3 { page-break-after: avoid; break-after: avoid; }
    tr { page-break-inside: avoid; break-inside: avoid; }
    .cols table { font-size: 8.2pt; } .cols th, .cols td { padding: 1.3pt 5pt; }
    """
    key = [
        ("Overall", f"{W:g} wide × {D:g} deep × {H_WING:g} high (caps). DJ surface at {H_TOP:g}. Footprint is the same at every height: the caps are flush with the columns."),
        ("Bay (between wings)", f"{BAY_W:g} wide. Gear span {BAY_W:g}, keyboard tray {TRAY_W:g} overall including aprons, keyboard {KB_W:g}."),
        ("Wings", f"{WING_W:g} wide each, {WING_INT_W:g} clear inside, full height to {Z_CAP_UNDER:g}, cap {CAP_W:g} × {D:g} × 3 on top."),
        ("Keyboard tray", f"Top face {Z_TRAY_TOP:g}, underside {Z_TRAY_UNDER:g}, extension {EXT:g}, tray {TRAY_PANEL_W:g} × {TRAY_D:g}. Key tops about 74 (piano height)."),
        ("Recess", f"{RECESS_H:g} clear, full bay width, open to the wall."),
        ("Depth budget",
         f"{INT_D:g} usable inside the bay, 1.8 back panel, {BACK_INSET:g} chase. Wings use the full depth ({D - T:g} inside)."
         if VARIANT == 1 else
         f"{INT_D:g} usable inside the bay, 1.8 back panel flush with the rear face. Front rail {GEAR_Y:g}, deepest well 36.2, back rail 7.0. Wings use the full depth ({D - T:g} inside)."),
        ("Panel thickness", "18 mm carcass, 30 mm top and caps, 15 mm drawer boxes." if VARIANT == 1 else "18 mm carcass, 30 mm top and caps over a 60 mm fascia, 15 mm drawer boxes."),
        ("Storage", f"About {REC_TOTAL} records in the wings (six openings, 6 mm per sleeve; {REC_TOTAL_S} if mostly single sleeves), two book compartments of 71.6 cm, two drawers. Each book compartment holds about 110 more LPs if wanted."),
        ("Weight, empty", "Roughly 120 to 130 kg. Loaded with records, books and gear about 250 kg. Spread over the two wings and the floating bay."),
    ]
    if VARIANT == 2:
        key.insert(6, ("Wall gap", f"{WALL_GAP:g} behind the back panel, mandatory: the panel stops at {Z_BACK_TOP:g} and the trough's whole rear is open, venting into that gap. Allow {D + WALL_GAP:g} of floor depth, not {D:g}. Dimensioned on the section and the plan."))
    _shin_note = ""
    if BOOK_SETBACK:
        _shin_note = (f" The book zone is set back {BOOK_SETBACK:g} cm from the front plane, so the shins clear it; in v1 they passed within about 1 cm of the bottom panel's front edge."
                      if VARIANT == 2 else
                      f" The book zone is set back {BOOK_SETBACK:g} cm from the front plane, so the shins clear it: a seated player's shins cross the height of the bay bottom panel, {Z_BOT_TOP:g} cm, about 1 cm in front of where its edge used to stand, so the clearance at that pinch goes from about 1 cm to about {BOOK_SETBACK + 1:g}.")
    ergo = [
        ("Seated at the keyboard: tray at 63 cm puts the key tops at about 74 cm, the same as an acoustic piano. Clear height under the tray is 61.2 cm; use a stool of 44 to 46 cm. The tray extends 40 cm so the knees sit under the tray and the feet and pedal go into the 20 cm recess. Nothing projects below the tray at the front."
         + _shin_note),
        ("Standing at the decks: surface at 100 cm, mixer faders at about 111 cm. Toes go under the floating bay."
         if VARIANT == 1 else
         "Standing at the decks: surface at 100 cm, every faceplate flush with it. Toes go under the floating bay. Reaching into a well for a rear socket means lifting the unit out by its finger notches."),
        "Speakers: cap tops at 130 cm put a 5-inch monitor's tweeter at about 152 cm, a little below standing ear height; the isolation pads add a slight upward tilt. Toe them in toward the centre.",
        ("Cables: everything on the top drops through the slot into the 5 cm chase and straight into the power niche behind the drawer band, where the switched strip and the wall-wart bricks sit at standing height. The keyboard's mains lead and the pedal cable share the chase through the cutout behind the tray; leave a 60 cm slack loop for the tray travel. The strip's own lead runs down the chase to the wall socket."
         if VARIANT == 1 else
         f"Cables: each player unit's leads leave through the {WELL_SLOT_W:g} cm notch in the rear wall of its well into the trough under the back rail; the Xone:92's well has no rear wall and opens into the trough across its full width. The leads run along the trough and drop into the power niche, where the switched strip and the bricks sit. The keyboard's mains lead and the pedal cable keep their cutout behind the tray; leave a 60 cm slack loop for the tray travel. Stand the console {WALL_GAP:g} cm off the wall: the back panel is the rear face and stops at {Z_BACK_TOP:g}, so the trough's rear is open along the whole bay and that gap is what lets air move through it and the leads out of it."),
    ]
    build = [
        f"Build the two wings first as closed columns (open front) {WING_W:g} × {D:g} × {Z_CAP_UNDER:g}. Their inner panels are the bay side walls, so drill them for the tray slides (cabinet member at 63 to 68 cm, 1.5 cm from the front) and for the bay panel fixings before assembly.",
        ("Tie the wings together with the bay panels: bottom (top face 21.8), fixed mid panel (top face 81.8), top (97 to 100) and the back panel. Dowels and glue at visible joints; concealed confirmats behind the drawers and the tray where they will not be seen."
         if VARIANT == 1 else
         f"Tie the wings together with the bay panels: bottom (top face 21.8), fixed mid panel (top face {Z_FIX_TOP:g}), top ({Z_WELL_FLOOR:g} to {H_TOP:g}) and the back panel. Dowels and glue at visible joints; concealed confirmats behind the drawers and the tray where they will not be seen."),
        "The bay bottom spans 145 cm with no leg. The book divider is glued and screwed along its full length to the bottom and back panels, and the back panel is glued along the rear edge: together they act as the stiffeners. Do not add a rail under the front edge; the recess must stay 20 cm clear.",
    ]
    if BOOK_SETBACK:
        build.append(f"Set the bay bottom panel, the book divider and both adjustable shelves back {BOOK_SETBACK:g} cm from the front plane. The panel's front edge is unsupported and unlipped at {Z_BOT_TOP:g}; lip it and ease it, it is at shin height.")
    build += [
        ("The bay back panel is inset 5 cm to form the cable chase. It is open at the bottom into the recess and closed at the sides by the wing panels and at the top by the top. The wing back panels are flush with the rear edge."
         if VARIANT == 1 else
         f"The bay back panel is the rear face of the piece and stops at {Z_BACK_TOP:g}. The cable trough is the band from {Z_WELL_FLOOR:g} to {Z_TOP_UNDER:g}, left open behind the wells from wing to wing; with no panel above {Z_BACK_TOP:g} its rear face is open as well, the full {BAY_W:g} × {FASCIA_H:g} cm. Stand the console {WALL_GAP:g} cm off the wall. That gap is what the trough breathes through along its whole length and what the leads leave through, so it is part of the build, not a placement preference: see the section and the plan, where it is drawn and dimensioned."),
        ("Rout the slot in the top before finishing: 115 × 6 cm, 41 cm from the front edge, centred on the bay, ends rounded, edges eased. Six centimetres lets the XDJ-700 power bricks and Schuko plugs pass without turning. Optional brush strip."
         if VARIANT == 1 else
         "Cut the four gear wells in the top before finishing, and dry-fit every unit before the fascia goes on. The flush line is set by the cleats, so cut the cut-outs to the units and leave the floor heights to fit-out."),
    ]
    if VARIANT == 2:
        build.append(f"The wells give {WELL_DROP:g} cm of clearance below the surface, {H_TOP:g} down to the floor at {Z_WELL_FLOOR:g}. That is the budget for each unit's chassis below its own faceplate, not for its overall height: three of the four units in the gear table are listed taller than {WELL_DROP:g} cm because those figures include everything above the faceplate, the turntable's dust cover included. Measure the below-faceplate height of all four units before cutting, and dial each well floor to it on the cleats, which give ±10 mm and no more.")
        build.append(f"Do not gasket, tape or foam anything shut. The 2 mm clearance at the sides and rear of each unit, the notches in the well rear walls, the Xone:92's missing rear wall, the open rear of the trough and the {NICHE_VENT:g} cm gap under the niche door are the whole of the ventilation, and the Xone:92 is an analogue mixer that runs warm. Every one of them stays open.")
        build.append(f"Glue the well side walls to the underside of the top board before the fascia goes on. Each web between two wells is then a {TT*10:g} mm cap on two {FASCIA_H*10:g} mm walls, which is what carries the span; a bare {TT*10:g} mm web is not stiff enough to lean on.")
    build += [
        f"Keyboard tray: side-mounted heavy-duty slides above the tray surface, screwed into the solid oak aprons ({dref('detail')}). Confirm the keyboard's actual footprint and connector positions before cutting the tray and the back-panel cutout.",
        ("Drawers on undermount runners with flush inset fronts, 2 mm gaps, finger pull routed under the top edge. Run the grain across both fronts and the niche door as one board."
         if VARIANT == 1 else
         f"Drawers on undermount runners with flush inset fronts, 2 mm gaps, finger pull routed under the top edge. Run the grain across both fronts and the niche door as one board. Cut the fronts and the door to {FRONT_H:g} cm, not to the {DRW_H:g} cm band: the well floors take {T*10:g} mm off the top of the boxes, but nothing closes the face there, so the fronts run on up to the fascia at {Z_WELL_FLOOR:g}. The {T*10:g} mm standing proud of each box has clear air behind it back to the front rail. The two dividers are notched to match over their front {GEAR_Y:g} cm."),
        (f"Power niche: cut the back panel away behind it ({NICHE_W:g} × {NICHE_CUT_H_EFF:g} cm at {NICHE_CUT_Z0:g} to {NICHE_CUT_Z0 + NICHE_CUT_H_EFF:g}) so niche and chase are one space. Door on concealed hinges with a push latch, {NICHE_DOOR_H:g} cm tall in the {FRONT_H:g} cm opening so a {NICHE_VENT:g} cm gap is left at the bottom for air. The strip lies on the mid panel with sockets up; leads from the slot and from the keyboard arrive through the chase. Optional: a 6 × 4 cm hole through each divider at the rear, with a matching notch in the drawer side, lets a lead from the strip charge headphones or a phone inside the drawers; leave a 45 cm loop for the drawer travel. Bricks stay in the niche."
         if VARIANT == 1 else
         f"Power niche: {NICHE_W:g} × {DRW_H:g}, its rear {INT_D - _NICHE_REAR_Y0:g} cm opening upward into the trough rather than rearward into a chase. Door on concealed hinges with a push latch, {NICHE_DOOR_H:g} cm tall in the {FRONT_H:g} cm opening so a {NICHE_VENT:g} cm gap is left at the bottom edge for air. The strip lies flat on the niche floor with sockets up. Stand the bricks on the floor beside it, toward the rear of the niche, y {_NICHE_REAR_Y0:g} to {INT_D:g} from the front: past that line the well floors have stopped and the open trough runs overhead, so the headroom there is {_NICHE_REAR_H:g} cm, up to the back rail's underside at {Z_TOP_UNDER:g}, and brick height is not a constraint. What matters is that nothing is stacked on the strip — strip plus brick is about {_STRIP_H + _BRICK_H:g} cm, topping out at {_STACK_TOP:g}, which fouls a well floor at the front of the niche and blocks the trough at the rear — and that the trough stays clear as the route for the mains lead out through the back-panel cutout ({NICHE_CUT_Z0:g} to {NICHE_CUT_Z0 + NICHE_CUT_H_EFF:g}, x {NICHE_X:g} to {NICHE_X + NICHE_W:g}), which runs out at the panel's top edge and hands over to the trough's own open rear. Height is only critical for a brick pushed to the front of the niche instead, under a well floor: {_NICHE_FRONT_H:g} cm of headroom there, which an {_BRICK_H:g} cm brick clears by {_BRICK_FRONT_MM:g} mm."),
        f"Adjustable shelves on 5 mm pins, holes at {PIN_PITCH * 10:g} mm pitch. Set the two rows out from the book compartment's own front and back faces, {PIN_INSET * 10:g} mm in from each, not from the front of the carcass: the compartment starts {BOOK_SETBACK:g} cm back, so the rows fall {PIN_ROW_FRONT:g} and {PIN_ROW_BACK:g} cm behind the console's front face, {PIN_ROW_GAP:g} cm apart. Finish the underside of the tray: it is the ceiling of the book compartments.",
        ("Level on the eight feet so the tray runs true, then fix each wing to the wall with a concealed anti-tip bracket"
         + ("." if VARIANT == 1 else f", packed out to {WALL_GAP:g} cm so the bracket holds the wall gap open instead of pulling the console flush.")),
    ]
    variants = [
        "Speaker caps: the earlier 24 cm cap overhanging 4 cm inward was dropped on 14 September 2026; a flush 20 cm cap is enough for a KRK Rokit 5. Widen the cap only if the speakers change.",
        f"Record capacity: wings widened from 14.5 to {WING_W:g} cm on 14 September 2026 ({W:g} cm overall), about {REC_TOTAL} records at 6 mm per sleeve. Each book compartment holds about 110 more LPs if wanted.",
        f"Wall shelf for the speakers later: the caps can be left off and the wings capped at 100 cm, which turns the piece into a plain {W:g} × 100 box.",
    ]
    cut_page, quantities = "", ("Quantities: about 7.5 m² of 18 mm oak-veneered birch ply (three 250 × 125 sheets with waste), about 1 m² of 30 mm solid oak for the top and caps, plus solid oak for aprons, rail, drawer fronts, plinths and lipping. The carpenter should re-check against their stock sizes.")
    if VARIANT == 2:
        cut = cut_list()
        _rows, _note, sheets = cut_totals(cut)
        ply_m2 = sum(r[1] * r[2] * r[3] for r in cut["ply"]) / 1e4
        oak30_m2 = sum(r[1] * r[2] * r[3] for r in cut["oak"] if r[4] == TT * 10) / 1e4
        quantities = (f"Quantities, from the cut list: {ply_m2:.2f} m² of 18 mm oak-veneered birch ply, which takes {sheets} sheets of {SHEET_L:g} × {SHEET_W:g} because of the grain, "
                      f"{oak30_m2:.2f} m² of 30 mm solid oak for the top and caps, plus solid oak for the fascia, aprons, rail, drawer fronts, plinths, cleats and lipping. The carpenter should re-check against their stock sizes.")
        cut_page = cut_list_html() + "\n"
    def _svg(key):
        return svgs[key].replace('<svg ', f'<svg style="height:{DRAWING_HEIGHT[key]}" ', 1)
    def _h2(key, top=False):
        st = ' style="margin-top:14pt"' if top else ''
        return f'<h2{st}>{DRAWING_NO[key]}. {DRAWING_TITLE[key]}</h2>'
    drawing_pages = (f'<div class="page drawing">{_h2("front")}{_svg("front")}</div>\n'
                     f'<div class="page drawing">{_h2("side")}{_svg("side")}</div>\n'
                     f'<div class="page drawing">{_h2("plan")}{_svg("plan")}\n'
                     f'{_h2("detail", True)}{_svg("detail")}'
                     + (f'\n{_h2("well", True)}{_svg("well")}' if "well" in svgs else "")
                     + '</div>')
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>DJ and piano console, design package</title><style>{css}</style></head><body><div class="wrap">
<div class="page">
<h1>DJ and piano console</h1>
<p class="muted">Design package for the carpenter. {version_line}, {today}. All dimensions in centimetres unless marked mm. Light natural oak, matte oiled.</p>
<p>One piece, {W:g} cm wide, that holds a DJ set-up on top at standing height, a stage piano on a pull-out tray at seated height, about {REC_TOTAL} records in two end columns, books in two open compartments, two drawers with a power niche between them, and two studio monitors on caps at the top of the columns. The middle section floats 20 cm above the floor so a sustain pedal and feet fit underneath.</p>
<div class="cols"><div><h3>Key dimensions</h3>{table(["Item", "Value"], key).replace('<table>', '<table class="kv">')}</div>
<div><h3>What goes where</h3>{table(["Zone", "Height (cm)", "Contents"], zones)}</div></div>
</div>
<div class="page"><h2>Ergonomics</h2><ul>{"".join(f"<li>{H.escape(e)}</li>" for e in ergo)}</ul>
<h2 style="margin-top:12pt">{"Gear layout on the top" if VARIANT == 1 else "Gear layout in the top"}</h2>{table(gear_head, gear_rows)}
<p class="muted">Positions assume a Technics-size turntable (45.3 × 35.3), an Allen &amp; Heath Xone:92 and two Pioneer XDJ-700 with 6 cm gaps and 3 cm end margins. {"Re-measure your own units before fixing anything; the slot and top do not depend on it." if VARIANT == 1 else f"Re-measure your own units before cutting: each well is templated to its unit with only 2 mm clearance per side, so the cut-outs depend on it directly. The H column is each unit's <strong>overall</strong> height, everything included — the turntable's 16.2 is mostly its dust cover, which cannot be fitted once the deck is sunk. Overall height is not what the well has to swallow. What the well gives is {WELL_DROP:g} cm of clearance <strong>below the faceplate</strong>, from the faceplate line at {H_TOP:g} down to the well floor at {Z_WELL_FLOOR:g}, and it is each unit's own chassis height below its own faceplate that has to fit in that. Measure it on all four units before cutting; the well floor cleats then take up the difference, but only ±10 mm."}</p>
<h2 style="margin-top:12pt">Variants left open</h2><ul>{"".join(f"<li>{H.escape(v)}</li>" for v in variants)}</ul>
</div>
{drawing_pages}
<div class="page parts"><h2>Parts list</h2>
{table(["Group", "Part", "Qty", "Size L × W (cm)", "Thk (mm)", "Material", "Notes"], parts_rows())}
</div>
{cut_page}<div class="page"><h2>Hardware</h2>{table(["Item", "Qty", "Specification"], HARDWARE)}
<h2 style="margin-top:12pt">Materials and finish</h2>
<ul>
<li>Carcass: 18 mm oak-veneered birch plywood, A/B crown-cut veneer, every exposed edge lipped with 5 mm solid oak. Grain vertical on the wing panels, horizontal on the long panels and continuous across the two drawer fronts.</li>
<li>Top and speaker caps: 30 mm solid European oak from glued-up boards. If movement is a concern, 30 mm veneered blockboard with 30 mm solid oak lipping.</li>
<li>Solid oak for the drawer fronts, tray aprons, rear rail and plinth boards.</li>
<li>{quantities}</li>
<li>Finish: natural light oak, no stain. Sand to 150/180 grit, two coats of Osmo Polyx-Oil 3062 Matt (or Rubio Monocoat Oil Plus 2C Pure). Finish every part, including the tray underside, before final assembly. Hardware in black.</li>
</ul>
</div>
<div class="page"><h2>Construction notes</h2><ol>{"".join(f"<li>{H.escape(b)}</li>" for b in build)}</ol>
</div>
{render_block}
</div></body></html>"""
    return html

if __name__ == "__main__":
    import sys
    svgs = {"front": front_elevation(), "side": side_section(), "plan": plan_view(), "detail": detail_tray()}
    if VARIANT == 2: svgs["well"] = detail_well()
    for k, v in svgs.items():
        with open(os.path.join(OUT, f"drawing-{k}{SUFFIX}.svg"), "w") as f: f.write(v)
    render = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, f"render-cg{SUFFIX}.png")
    with open(os.path.join(OUT, f"dj-piano-console{SUFFIX}-spec.html"), "w") as f: f.write(build_html(svgs, render))
    print("ok", OUT)
