#!/usr/bin/env python3
"""DJ + piano console: SVG drawings and HTML/PDF spec generator. All dimensions in cm."""
import os, html as H, random, datetime

OUT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)

VARIANT = int(os.environ.get("VARIANT", "1"))   # 1 = gear on top (v1.6), 2 = flush-mounted
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
BOOK_SETBACK = 0.0                        # v1: book zone flush with the front plane
if VARIANT == 2:
    GEAR_Y = 5.0                          # front rail, was 2.0
    BACK_INSET = 0.0                      # back panel moves to the rear face
    Y_BACK0 = D - BACK_INSET - T          # 48.2
    Y_BACK1 = D - BACK_INSET              # 50.0
    INT_D = Y_BACK0                       # 48.2
    DRW_H = Z_WELL_FLOOR - Z_FIX_TOP      # 9.2, was 15.2
    BOOK_SETBACK = 15.0                   # seated shin clearance; see the spec
Z_DRW_TOP = Z_WELL_FLOOR if VARIANT == 2 else Z_TOP_UNDER
BOOK_D = INT_D - BOOK_SETBACK             # 33.2 in v2, 43.2 in v1

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
    assert _eq(Z_FIX_TOP + DRW_H, Z_WELL_FLOOR) and _eq(Z_WELL_FLOOR, 91.0)
    assert _eq(Z_WELL_FLOOR + FASCIA_H, Z_TOP_UNDER) and _eq(Z_TOP_UNDER, 97.0)
    assert _eq(Z_TOP_UNDER + TT, H_TOP)
    _deep = max(w[4] for w in well_positions())          # deepest well back edge
    assert _eq(_deep, 41.2), _deep                        # the Xone:92
    assert _eq(INT_D - _deep, 7.0)                        # minimum back rail
    assert _eq(Y_BACK1, D)                                # back panel at the rear face
    _last = gear_positions()[-1]
    assert _last[1] + _last[2] <= X_BAY1 - 3.0            # right margin holds
    assert _eq(BOOK_D, 33.2)
    assert BOOK_D >= 31.4                                 # a 12" LP sleeve still fits

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
    if VARIANT == 1:
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
    d.rect(X_BAY0, Z_FIX_TOP, BAY_W, DRW_H, fill="#6B5A40", stroke="none")
    for ox in (X_BAY0, NICHE_X + NICHE_W + T):
        d.rect(ox + GAP, Z_FIX_TOP + GAP, DRW_W - 2 * GAP, DRW_H - 2 * GAP, fill=OAK)
        d.line(ox + 8, Z_DRW_TOP - 1.7, ox + DRW_W - 8, Z_DRW_TOP - 1.7, stroke=OAKE, sw=1.2)
    d.rect(NICHE_X - T, Z_FIX_TOP, T, DRW_H); d.rect(NICHE_X + NICHE_W, Z_FIX_TOP, T, DRW_H)
    d.rect(NICHE_X + GAP, Z_FIX_TOP + GAP, NICHE_W - 2 * GAP, DRW_H - 2 * GAP, fill=OAK)
    cxn, czn = NICHE_X + NICHE_W / 2, Z_FIX_TOP + DRW_H / 2 + 0.8
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
        # 9 cm slab (3 cm oak top board over a 6 cm fascia), wells cut through both
        d.rect(X_BAY0, Z_WELL_FLOOR, BAY_W, FASCIA_H + TT)
        for n, wx, ww, wy0, wy1, wfz in well_positions():
            d.rect(wx, wfz, ww, WELL_DROP, fill=GEARC, stroke="none")
            d.text(wx + ww / 2, H_TOP + 3.6, n, size=9)
        d.line(X_BAY0, Z_TOP_UNDER, X_BAY1, Z_TOP_UNDER, stroke=OAKE, sw=0.6, dash="4,3")
    # notes
    if VARIANT == 1:
        d.text(W / 2, 123.6, f"Cable slot {SLOT_Y1 - SLOT_Y0:g} × {SLOT_X1 - SLOT_X0:g} cm routed in the top behind the gear; leads, plugs and the XDJ bricks pass down into the chase and the power niche", size=9, fill=NOTE, italic=True)
    else:
        d.text(W / 2, 123.6, "Gear sunk 9 cm into the slab, faceplates flush. Each well slots at the rear into a continuous cable trough under the back rail; no dust covers can be fitted", size=9, fill=NOTE, italic=True)
    d.text(X_BAY0 + DRW_W / 2, Z_FIX_TOP + DRW_H / 2, "Drawer: cables, adapters, needles", size=9, dy=3)
    d.text(NICHE_X + NICHE_W + T + DRW_W / 2, Z_FIX_TOP + DRW_H / 2, "Drawer: headphones", size=9, dy=3)
    d.text(W / 2, 77.4, "Keyboard 133 × 35 × 12 stowed on the pull-out tray (extends 40 cm, see section)", size=9, fill=NOTE, italic=True)
    d.text(X_BAY0 + OPEN_W / 2, Z_TRAY_UNDER - 3.2, "Books or LPs (39 cm clear)", size=9, fill=NOTE, italic=True)
    d.text(rx + OPEN_W / 2, Z_TRAY_UNDER - 3.2, "Adjustable shelf on 5 mm pins", size=9, fill=NOTE, italic=True)
    d.text(W / 2, 8.6, "Foot and pedal recess, 20 cm clear, full width, open through to the wall", size=9, fill=NOTE, italic=True)
    d.leader(W + 0.2, 105, W + 3, 112, "headphone hook, outer face", size=8, italic=True)
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
    d.dim_v(Z_TRAY_TOP, Z_CAV_TOP, xr, "17", ext=X_BAY1); d.dim_v(Z_FIX_TOP, Z_DRW_TOP, xr, f"{DRW_H:g}", ext=X_BAY1)
    if VARIANT == 2: d.dim_v(Z_WELL_FLOOR, H_TOP, xr, f"{FASCIA_H + TT:g} slab", ext=X_BAY1)
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
    d.line(-78, 0, D + 4, 0, sw=1.6)
    d.line(D, 0, D, H_WING + SPK_H + 4, stroke="#777", sw=3)
    d.text(D + 2, 158, "wall", size=9, anchor="start", fill="#777")
    # chase hatch
    if VARIANT == 1:
        for zz in range(22, 97, 4): d.line(Y_BACK1, zz, D, zz + 3, stroke=GHOST, sw=0.5)
    # carcass
    d.rect(BOOK_SETBACK, RECESS_H, Y_BACK1 - BOOK_SETBACK, T)
    d.rect(Y_BACK0, Z_BOT_TOP, T, Z_TOP_UNDER - Z_BOT_TOP)
    d.rect(Y_BACK0 - 0.05, CUT_Z0, T + 0.1, CUT_H, fill=VOID, stroke="none")
    d.rect(Y_BACK0 - 0.05, NICHE_CUT_Z0, T + 0.1, NICHE_CUT_H, fill=VOID, stroke="none")
    d.rect(0, Z_CAV_TOP, Y_BACK0, T)
    if VARIANT == 1:
        d.rect(0, Z_TOP_UNDER, SLOT_Y0, TT); d.rect(SLOT_Y1, Z_TOP_UNDER, D - SLOT_Y1, TT)
    else:
        xone = [w for w in well_positions() if w[0] == "Xone:92"][0]
        d.rect(0, Z_WELL_FLOOR, GEAR_Y, FASCIA_H + TT)                 # front rail, 5 cm, solid 91 -> 100
        d.rect(xone[4], Z_TOP_UNDER, Y_BACK0 - xone[4], TT)            # back rail: oak at the surface (97 -> 100), open underneath -> the trough
        d.rect(GEAR_Y, Z_WELL_FLOOR, xone[4] - GEAR_Y, 0.9, fill=OAK2) # well floor on its cleat
        d.text((xone[4] + Y_BACK0) / 2 + 0.3, Z_WELL_FLOOR + 4.3, "trough", size=7, fill=NOTE)
    # books
    d.rect(BOOK_SETBACK + 1.0, Z_BOT_TOP + SHELF_UP, (BOOK_D - 1.0) if VARIANT == 2 else 40.0, T)
    for (y, h, dep, c) in [(1.5, 17, 13, "#6E8B74"), (1.5, 15.5, 22, "#A67C52"), (1.5, 30, 31.5, "#5E5548")]:
        pass
    d.rect(BOOK_SETBACK + 1.5, Z_BOT_TOP, 22, 17, fill="#A67C52", stroke="none")
    d.rect(BOOK_SETBACK + 1.5, Z_BOT_TOP + SHELF_UP + T, 20, 15.5, fill="#6E8B74", stroke="none")
    if VARIANT == 2:
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
    d.rect(GAP, Z_FIX_TOP + 1.0, T, DRW_H - 1.0 - GAP)
    d.rect(5, Z_FIX_TOP, 30, 4.0, fill="#444", stroke="none")
    for yy in (9, 16, 23): d.rect(yy, Z_FIX_TOP + 4.0, 4.0, 2.5, fill="#777", stroke="none")
    if VARIANT == 1:
        d.rect(28.5, Z_FIX_TOP + 4.0, 6, 8.5, fill="#666", stroke="none")       # stacked on the strip: 4 + 8.5 only fits v1's 15.2 band
    else:
        d.rect(Y_BACK0 - 6, Z_FIX_TOP, 6, 8.5, fill="#666", stroke="none")      # stands on the niche floor behind the strip, headroom into the trough
    # mixer in section + cables
    if VARIANT == 1:
        d.rect(GEAR_Y, H_TOP, 35.8, 10.7, fill=GEARC, stroke="none")
    else:
        d.rect(GEAR_Y, Z_WELL_FLOOR + 0.9, 35.8, WELL_DROP - 0.9, fill=GEARC, stroke="none")
    if VARIANT == 1:
        d.poly([(GEAR_Y + 35.8, H_TOP + 4), (SLOT_Y0 + 2.5, H_TOP + 1.5), (SLOT_Y0 + 2.5, Z_TOP_UNDER - 3), (47.0, 93), (46.0, 89.5), (36, 88.5), (18, 88.3)], stroke="#C0392B", sw=1.2)
    else:
        # mixer's rear in its well -> back into the trough (z 91-97) -> down along the back panel -> into the power niche
        d.poly([(GEAR_Y + 35.8, Z_WELL_FLOOR + 5), (xone[4] + 0.5, Z_WELL_FLOOR + 3.2), (xone[4] + 0.5, Z_FIX_TOP + 5.2), (20, Z_FIX_TOP + 2)], stroke="#C0392B", sw=1.2)
    if VARIANT == 1:
        d.poly([(TRAY_D - 3, 69), (Y_BACK0 + 0.5, 70.5), (46.5, 72), (46.5, 87.5), (25, 88.3)], stroke="#C0392B", sw=1.0)
        d.poly([(35, Z_FIX_TOP + 2), (47.5, 84.5), (47.5, 10), (50, 8)], stroke="#333", sw=1.2)
        d.text(36, 11.5, "mains lead to wall socket", size=7.5, fill=NOTE, italic=True)
    else:
        # keyboard lead: behind the tray and straight out of the tray cutout (66 -> 74) -- no chase to climb in v2
        d.poly([(TRAY_D - 3, 71.5), (44.0, 71.8), (Y_BACK0 - 0.3, 72.2)], stroke="#C0392B", sw=1.0)
        # mains: off the end of the strip, out of the niche cutout (83 -> 95) to the wall behind
        d.poly([(35, Z_FIX_TOP + 3.2), (41.4, 90.2), (42.6, 92.2), (Y_BACK0 - 0.3, 92.9)], stroke="#333", sw=1.2)
        d.text(D + 2, 92.6, "mains lead to wall socket", size=7.5, anchor="start", fill=NOTE, italic=True)
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
        d.leader(xone[4] + 2, Z_WELL_FLOOR + 3, R, 154, "cable trough under the back rail, 7 cm deep", anchor="end", italic=True)
        d.leader(Y_BACK0 + 0.9, 40, R, 146, "back panel 18 mm, flush with the rear face", anchor="end", italic=True)
    d.leader(20, Z_FIX_TOP + 2, R, 138, "power niche: strip and bricks, vented door", anchor="end", italic=True)
    d.leader(Y_BACK0 + 0.9, NICHE_CUT_Z0 + 6, R, 122, "back panel cut away behind the niche", anchor="end", italic=True)
    d.leader(21, 65.5, R, 130, "heavy-duty tray slide 400 mm (detail A)", anchor="end", italic=True)
    d.leader(18, 2.5, R, 5, "sustain pedal in the recess", anchor="end", italic=True)
    d.text(-EXT + TRAY_D / 2 - 8, 84, "tray extended 40 cm (dashed)", size=8, fill=INK, italic=True)
    if VARIANT == 1: d.text(45, 40, "chase", size=8, rot=-90, fill=NOTE, dx=13)
    # dims
    d.dim_h(0, INT_D, -5, f"{INT_D:g} interior", ext=0, above=False)
    if VARIANT == 1: d.dim_h(Y_BACK1, D, -5, "5", ext=0, above=False)
    if VARIANT == 2:
        d.dim_h(0, GEAR_Y, 114, f"{GEAR_Y:g} front rail", ext=H_TOP)
        d.dim_h(xone[4], Y_BACK0, 114, f"{Y_BACK0 - xone[4]:g} back rail", ext=H_TOP)
    d.dim_h(0, D, -12, "50 overall depth", above=False)
    d.dim_h(-EXT, 0, 92, "40 extension", ext=Z_TRAY_UNDER + 14)
    if VARIANT == 1:
        d.dim_h(0, SLOT_Y0, 114, f"{SLOT_Y0:g} from front edge to slot", ext=H_TOP); d.dim_h(SLOT_Y0, SLOT_Y1, 114, f"{SLOT_Y1 - SLOT_Y0:g}", ext=H_TOP)
    d.dim_h(0, TRAY_D, 58.5, "42 tray", above=False)
    xr = D + 8
    d.dim_v(0, RECESS_H, xr, "20 recess"); d.dim_v(Z_TRAY_TOP, Z_CAV_TOP, xr, "17"); d.dim_v(H_TOP, H_WING, xr, "30")
    d.dim_v(0, Z_TRAY_UNDER, D + 17, "61.2 clear under tray"); d.dim_v(0, H_TOP, D + 26, "100")
    return d.render()

# ---------------- 3. plan view ----------------
def plan_view():
    d = Drawing(0, W, -22, D + 12, scale=4.0, pad=(40, 20, 130, 20))
    d.line(0, D, W, D, stroke="#777", sw=3); d.text(W + 1, D, "wall", size=9, anchor="start", fill="#777", dy=3)
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
    d.dim_v(0, D, W + 24, "50")
    return d.render()

# ---------------- 4. detail A: tray edge ----------------
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
    d.dim_v(Z_TRAY_TOP + 0.3 + KB_H, Z_CAV_TOP, xg, "4.7", right=False)
    d.dim_v(Z_TRAY_UNDER, Z_TRAY_TOP, 23.0, "1.8", right=False)
    R = 25.5
    d.leader(T + 8, Z_CAV_TOP + 0.9, R, 82.5, "Fixed panel 18 mm at 80 to 81.8; drawer band above")
    d.leader(x_slide + SLIDE_T / 2, Z_TRAY_TOP + 2.5, R, 78, "Heavy-duty slide 400 mm, 100 kg or more per pair, hold-open detent")
    d.leader(x_apron + T / 2, Z_TRAY_UNDER + 1.0, R, 73.5, "Solid oak apron 18 x 68 mm over the tray edge; slide screws into it")
    d.leader(x_kb + 6, Z_TRAY_TOP + 6, R, 69, "Keyboard 133 wide, 2.3 cm to each apron, key tops at about 74")
    d.leader(x_tray + 3, Z_TRAY_TOP + 0.15, R, 64.5, "Thin non-slip mat under the keyboard")
    d.leader(x_tray + 5, Z_TRAY_UNDER + 0.9, R, 60, "Tray 18 mm oak-veneered birch ply, 137.6 x 42, finished both faces")
    d.leader(T / 2, 59, R, 56.5, "Wing inner panel 18 mm = bay side wall; slide cabinet member fixes to it")
    return d.render()

# ---------------- 5. detail B: gear well (v2) ----------------
def detail_well():
    d = Drawing(-4, 20, 86, 103, scale=16.0, pad=(30, 20, 400, 40))
    x0 = GEAR_Y                                                      # front rail depth
    d.rect(0, Z_WELL_FLOOR, x0, FASCIA_H + TT, fill=OAK)              # front rail in section
    d.line(0, Z_TOP_UNDER, x0, Z_TOP_UNDER, stroke=OAKE, sw=0.8, dash="3,2")
    d.rect(x0, Z_WELL_FLOOR, 0.9, 1.4, fill=OAK2)                     # cleat / rebate
    d.rect(x0 + 0.9, Z_WELL_FLOOR, 12, 0.9, fill=OAK2)                # well floor
    d.rect(x0 + 0.9, Z_WELL_FLOOR + 0.9, 12, WELL_DROP - 0.9, fill=GEARC, stroke="none")
    d.line(x0, H_TOP, 20, H_TOP, stroke=INK, sw=1.4)                  # the flush line
    d.dim_v(Z_WELL_FLOOR, H_TOP, -2, f"{WELL_DROP:g} clear", right=False)
    d.dim_v(Z_TOP_UNDER, H_TOP, 2.5, f"{TT:g}", right=False)
    d.dim_v(Z_WELL_FLOOR, Z_TOP_UNDER, 2.5, f"{FASCIA_H:g}", right=False)
    R = 21.0
    d.leader(3.5, Z_TOP_UNDER + 1.4, R, 101.5, "Oak top board 30 mm; cut-out edges eased, not lipped")
    d.leader(3.5, Z_WELL_FLOOR + 3.0, R, 99.0, "Fascia 60 mm solid oak, front and ends; bottom sits on the well floor at 91")
    d.leader(x0 + 5.0, Z_WELL_FLOOR + 0.4, R, 96.5, "Well floor 18 mm on adjustable cleat: slots give +/-10 mm at fit-out")
    d.leader(x0 + 3.0, Z_WELL_FLOOR + 0.1, R, 94.0, "Technics plinth has no flange: stands on its own feet at the floor")
    d.leader(x0 + 0.45, Z_WELL_FLOOR + 0.9, R, 91.5, "Xone:92 and XDJ-700 faceplates may bear on the rebate; confirm against units")
    d.leader(14, H_TOP, R, 89.0, "Faceplate flush with oak; 2 mm clearance at sides and rear, none at front")
    d.leader(18.0, Z_WELL_FLOOR + 5.0, R, 86.5, "Rear wall slots into the cable trough; leads and the Xone's heat exit there")
    d.text(2.0, 87.5, "finger notches at two corners of each well, r 20 mm", size=8, fill=NOTE, italic=True, anchor="start")
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
        ("Bay", "Top", 1, f"{BAY_W:g} × {D:g}", 30, "Solid oak, or 30 mm veneered board with 30 mm oak lipping", "Routed cable slot 115 × 6 cm, 41 cm from the front edge, centred, ends rounded r 3. Passes plugs and the XDJ bricks."),
        ("Bay", "Bay bottom panel", 1, f"{BAY_W:g} × {Y_BACK1:g}", 18, "Oak-veneered ply, front edge lipped", "Top face at 21.8 cm. Carries the books; stiffened by the divider and the back panel, no rail underneath."),
        ("Bay", "Fixed mid panel", 1, f"{BAY_W:g} × {INT_D:g}", 18, "Oak-veneered ply, front edge lipped", "Top face at 81.8 cm. Ceiling of the keyboard slot, floor of the drawer band."),
        ("Bay", "Bay back panel", 1, f"{BAY_W:g} × {Z_TOP_UNDER - Z_BOT_TOP:g}", 18, "Oak-veneered ply", f"Inset 5 cm. Cutout {CUT_W:g} × {CUT_H:g} cm behind the tray at {CUT_Z0:g} to {CUT_Z0 + CUT_H:g} cm; cutout {NICHE_W:g} × {NICHE_CUT_H:g} cm behind the niche at {NICHE_CUT_Z0:g} to {NICHE_CUT_Z0 + NICHE_CUT_H:g} cm."),
        ("Bay", "Book zone divider", 1, f"{INT_D:g} × {Z_TRAY_UNDER - Z_BOT_TOP - 0.5:g}", 18, "Oak-veneered ply, front edge lipped", "Centred. Glued and screwed to bottom and back panel along its length; 5 mm gap under the tray."),
        ("Bay", "Drawer band divider", 2, f"{INT_D:g} × {DRW_H:g}", 18, "Oak-veneered ply, front edge lipped", "Frame the 24 cm power niche. Optional 6 × 4 cm pass-through at the rear of each for a charging lead."),
        ("Bay", "Power niche door", 1, f"{NICHE_W - 0.4:g} × {DRW_H - 0.4:g}", 18, "Solid oak, grain continuous with the drawer fronts", "Flush inset, concealed hinges, push-to-open latch, 1 cm vent gap at the bottom edge."),
        ("Bay", "Adjustable shelf", 2, f"{OPEN_W - 0.2:g} × 40", 18, "Oak-veneered ply, front edge lipped", "One per book compartment, on 5 mm pins."),
        ("Bay", "Drawer front", 2, f"{DRW_W - 0.4:g} × {DRW_H - 0.4:g}", 18, "Solid oak (grain running across both fronts)", "Flush inset, 2 mm gaps, finger pull routed under the top edge."),
        ("Bay", "Drawer box", 2, "40 deep × 12 high, width per runner spec", 15, "Birch ply, 6 mm bottom", "For the 58.7 cm openings, sized to the runners. Notch the niche-side wall 6 × 4 cm at the rear if the pass-through is used."),
        ("Tray", "Keyboard tray panel", 1, f"{TRAY_PANEL_W:g} × {TRAY_D:g}", 18, "Oak-veneered birch ply, both faces", "Underside is visible from the book compartments: finish it. Front edge lipped."),
        ("Tray", "Tray side apron", 2, f"{TRAY_D:g} × {APRON_H:g}", 18, "Solid oak", "Covers the tray edge (1.8) and rises 5 cm above it. Slide drawer member screws into it."),
        ("Tray", "Tray rear rail", 1, f"{TRAY_PANEL_W:g} × {APRON_UP:g}", 18, "Solid oak", "On the tray top along the rear edge, doweled to the aprons. Stops racking."),
        ("All", "Solid oak lipping", "~28 m", "5 × 18 mm", "", "Solid oak", "All exposed ply edges."),
    ]
    return rows

HARDWARE = [
    ("Keyboard tray slides", "1 pair", "Heavy-duty full-extension ball-bearing, 400 mm, rated 100 kg or more per pair, with hold-open detent. Accuride 3634 (400 mm) or Fulterer FR 5000 (400 mm). Side mount at 63 to 68 cm."),
    ("Drawer runners", "2 pairs", "Full-extension undermount with soft close, 400 mm, 40 kg class. Blum Movento 760H4000S with Blumotion, or Hettich Actro 5D."),
    ("Shelf pins", "8", "5 mm steel, for two adjustable shelves. Drill 32 mm pitch, 37 mm from front and rear edges."),
    ("Levelling feet", "8", "M8 adjustable glides, 15 to 25 mm, two per wing side panel, hidden behind the plinth boards."),
    ("Anti-tip brackets", "2", "One per wing, concealed, fixed to the wall. Recommended: the wings are 130 cm tall with speakers on top."),
    ("Speaker isolation pads", "2", "IsoAcoustics ISO-155 or Auralex MoPAD, set with a slight upward tilt toward the standing position."),
    ("Headphone hook", "1", "Black steel or oak, on the outer face of the right wing at about 105 cm."),
    ("Power strip", "1", "6-way with switch, up to 40 cm long, or two 4-way strips side by side. Lies on the niche floor with sockets facing up; bricks stand on it. Niche is 24 wide × 15 tall × 48 deep including the chase."),
    ("Niche door hardware", "1 set", "Two concealed hinges (Blum Clip top or similar) and a push-to-open latch (Blum Tip-On), so the door needs no handle."),
    ("Cable slot brush strip", "1 (optional)", "Black brush grommet strip 115 cm, for a 60 mm slot, to line the slot."),
    ("Drawer pass-through grommets", "2 (optional)", "Rubber or oak-lined 60 × 40 mm grommets in the drawer-band dividers, for charging leads from the strip into the drawers."),
    ("Non-slip mat", "1", "Thin rubber or EVA sheet, about 133 × 35 cm, under the keyboard."),
    ("Carcass fixings", "as needed", "8 mm dowels and glue at all visible joints; concealed confirmat screws where hidden (behind drawers and tray). Slide screws per manufacturer."),
    ("Finish", "about 1 L", "Osmo Polyx-Oil 3062 Matt, two coats, or Rubio Monocoat Oil Plus 2C Pure (about 350 ml). Natural oak tone, no stain."),
]

def table(headers, rows):
    th = "".join(f"<th>{H.escape(str(h))}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(f"<td>{H.escape(str(c))}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>"

def build_html(svgs, render_path=None):
    today = datetime.date.today().strftime("%d %B %Y")
    gear_rows = []
    for n, gx, gw, gd, gh in gear_positions():
        gear_rows.append((n, f"{gw:g} × {gd:g} × {gh:g}", f"{gx - X_BAY0:g} to {gx - X_BAY0 + gw:g}"))
    zones = [
        ("Speaker caps", "127 to 130", f"Two 5-inch monitors on isolation pads, one per wing. Cap {CAP_W:g} × {D:g} cm, 30 mm oak, flush with the column on every side. A KRK Rokit 5 (18.5 wide) leaves 7 mm each side."),
        ("DJ surface", "100 (top 97 to 100)", "Turntable, XDJ-700, Xone:92, XDJ-700 left to right, within a 145 cm span, 2 cm back from the front edge. Cable slot 115 × 6 cm behind the gear, wide enough for plugs and the XDJ power bricks."),
        ("Drawer band", "81.8 to 97", "Two flush drawers of 58.7 cm (cables and adapters left, headphones right) with a 24 cm power niche between them: push-to-open door, strip and wall-wart bricks inside, open at the back into the cable chase."),
        ("Keyboard slot", "63 to 80", "Pull-out tray, top face at 63 cm, 40 cm extension on heavy-duty slides. Keyboard 133 × 35 × 12 stowed inside, 5 cm air above it."),
        ("Book compartments", "21.8 to 61.2", "Two openings 71.6 wide × 39.4 tall × 43.2 deep, one adjustable shelf each. Tall enough for LPs and art books."),
        ("Recess", "0 to 20", "Open across the whole bay and through to the wall: sustain pedal and feet when seated, toe space when standing."),
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
    """
    key = [
        ("Overall", f"{W:g} wide × {D:g} deep × {H_WING:g} high (caps). DJ surface at {H_TOP:g}. Footprint is the same at every height: the caps are flush with the columns."),
        ("Bay (between wings)", f"{BAY_W:g} wide. Gear span {BAY_W:g}, keyboard tray {TRAY_W:g} overall including aprons, keyboard {KB_W:g}."),
        ("Wings", f"{WING_W:g} wide each, {WING_INT_W:g} clear inside, full height to {Z_CAP_UNDER:g}, cap {CAP_W:g} × {D:g} × 3 on top."),
        ("Keyboard tray", f"Top face {Z_TRAY_TOP:g}, underside {Z_TRAY_UNDER:g}, extension {EXT:g}, tray {TRAY_PANEL_W:g} × {TRAY_D:g}. Key tops about 74 (piano height)."),
        ("Recess", f"{RECESS_H:g} clear, full bay width, open to the wall."),
        ("Depth budget", f"{INT_D:g} usable inside the bay, 1.8 back panel, {BACK_INSET:g} chase. Wings use the full depth ({D - T:g} inside)."),
        ("Panel thickness", "18 mm carcass, 30 mm top and caps, 15 mm drawer boxes."),
        ("Storage", f"About {REC_TOTAL} records in the wings (six openings, 6 mm per sleeve; {REC_TOTAL_S} if mostly single sleeves), two book compartments of 71.6 cm, two drawers. Each book compartment holds about 110 more LPs if wanted."),
        ("Weight, empty", "Roughly 120 to 130 kg. Loaded with records, books and gear about 250 kg. Spread over the two wings and the floating bay."),
    ]
    ergo = [
        "Seated at the keyboard: tray at 63 cm puts the key tops at about 74 cm, the same as an acoustic piano. Clear height under the tray is 61.2 cm; use a stool of 44 to 46 cm. The tray extends 40 cm so the knees sit under the tray and the feet and pedal go into the 20 cm recess. Nothing projects below the tray at the front.",
        "Standing at the decks: surface at 100 cm, mixer faders at about 111 cm. Toes go under the floating bay.",
        "Speakers: cap tops at 130 cm put a 5-inch monitor's tweeter at about 152 cm, a little below standing ear height; the isolation pads add a slight upward tilt. Toe them in toward the centre.",
        "Cables: everything on the top drops through the slot into the 5 cm chase and straight into the power niche behind the drawer band, where the switched strip and the wall-wart bricks sit at standing height. The keyboard's mains lead and the pedal cable share the chase through the cutout behind the tray; leave a 60 cm slack loop for the tray travel. The strip's own lead runs down the chase to the wall socket.",
    ]
    build = [
        f"Build the two wings first as closed columns (open front) {WING_W:g} × {D:g} × {Z_CAP_UNDER:g}. Their inner panels are the bay side walls, so drill them for the tray slides (cabinet member at 63 to 68 cm, 1.5 cm from the front) and for the bay panel fixings before assembly.",
        "Tie the wings together with the bay panels: bottom (top face 21.8), fixed mid panel (top face 81.8), top (97 to 100) and the back panel. Dowels and glue at visible joints; concealed confirmats behind the drawers and the tray where they will not be seen.",
        "The bay bottom spans 145 cm with no leg. The book divider is glued and screwed along its full length to the bottom and back panels, and the back panel is glued along the rear edge: together they act as the stiffeners. Do not add a rail under the front edge; the recess must stay 20 cm clear.",
        "The bay back panel is inset 5 cm to form the cable chase. It is open at the bottom into the recess and closed at the sides by the wing panels and at the top by the top. The wing back panels are flush with the rear edge.",
        "Rout the slot in the top before finishing: 115 × 6 cm, 41 cm from the front edge, centred on the bay, ends rounded, edges eased. Six centimetres lets the XDJ-700 power bricks and Schuko plugs pass without turning. Optional brush strip.",
        "Keyboard tray: side-mounted heavy-duty slides above the tray surface, screwed into the solid oak aprons (detail A). Confirm the keyboard's actual footprint and connector positions before cutting the tray and the back-panel cutout.",
        "Drawers on undermount runners with flush inset fronts, 2 mm gaps, finger pull routed under the top edge. Run the grain across both fronts and the niche door as one board.",
        "Power niche: cut the back panel away behind it (24 × 12 cm at 83 to 95) so niche and chase are one space. Door on concealed hinges with a push latch and a 1 cm gap at the bottom for air. The strip lies on the mid panel with sockets up; leads from the slot and from the keyboard arrive through the chase. Optional: a 6 × 4 cm hole through each divider at the rear, with a matching notch in the drawer side, lets a lead from the strip charge headphones or a phone inside the drawers; leave a 45 cm loop for the drawer travel. Bricks stay in the niche.",
        "Adjustable shelves on 5 mm pins, holes at 32 mm pitch. Finish the underside of the tray: it is the ceiling of the book compartments.",
        "Level on the eight feet so the tray runs true, then fix each wing to the wall with a concealed anti-tip bracket.",
    ]
    variants = [
        "Speaker caps: the earlier 24 cm cap overhanging 4 cm inward was dropped on 14 September 2026; a flush 20 cm cap is enough for a KRK Rokit 5. Widen the cap only if the speakers change.",
        f"Record capacity: wings widened from 14.5 to {WING_W:g} cm on 14 September 2026 ({W:g} cm overall), about {REC_TOTAL} records at 6 mm per sleeve. Each book compartment holds about 110 more LPs if wanted.",
        f"Wall shelf for the speakers later: the caps can be left off and the wings capped at 100 cm, which turns the piece into a plain {W:g} × 100 box.",
    ]
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>DJ and piano console, design package</title><style>{css}</style></head><body><div class="wrap">
<div class="page">
<h1>DJ and piano console</h1>
<p class="muted">Design package for the carpenter. Version 1.6, {today}. All dimensions in centimetres unless marked mm. Light natural oak, matte oiled.</p>
<p>One piece, {W:g} cm wide, that holds a DJ set-up on top at standing height, a stage piano on a pull-out tray at seated height, about {REC_TOTAL} records in two end columns, books in two open compartments, two drawers with a power niche between them, and two studio monitors on caps at the top of the columns. The middle section floats 20 cm above the floor so a sustain pedal and feet fit underneath.</p>
<div class="cols"><div><h3>Key dimensions</h3>{table(["Item", "Value"], key).replace('<table>', '<table class="kv">')}</div>
<div><h3>What goes where</h3>{table(["Zone", "Height (cm)", "Contents"], zones)}</div></div>
</div>
<div class="page"><h2>Ergonomics</h2><ul>{"".join(f"<li>{H.escape(e)}</li>" for e in ergo)}</ul>
<h2 style="margin-top:12pt">Gear layout on the top</h2>{table(["Device", "W × D × H (cm)", "Position from left wing inner face (cm)"], gear_rows)}
<p class="muted">Positions assume a Technics-size turntable (45.3 × 35.3), an Allen &amp; Heath Xone:92 and two Pioneer XDJ-700 with 6 cm gaps and 3 cm end margins. Re-measure your own units before fixing anything; the slot and top do not depend on it.</p>
<h2 style="margin-top:12pt">Variants left open</h2><ul>{"".join(f"<li>{H.escape(v)}</li>" for v in variants)}</ul>
</div>
<div class="page drawing"><h2>1. Front elevation</h2>{svgs['front'].replace('<svg ', '<svg style="height:168mm" ', 1)}</div>
<div class="page drawing"><h2>2. Side section through the bay, cut through the power niche and the mixer, looking toward the right wing</h2>{svgs['side'].replace('<svg ', '<svg style="height:165mm" ', 1)}</div>
<div class="page drawing"><h2>3. Plan of the top</h2>{svgs['plan'].replace('<svg ', '<svg style="height:66mm" ', 1)}
<h2 style="margin-top:14pt">4. Detail A: tray edge, slide and apron (section looking from the front, left side)</h2>{svgs['detail'].replace('<svg ', '<svg style="height:82mm" ', 1)}
{("<h2 style='margin-top:14pt'>5. Detail B: gear well (section through the front rail)</h2>" + svgs['well'].replace('<svg ', '<svg style="height:70mm" ', 1)) if 'well' in svgs else ''}
</div>
<div class="page parts"><h2>Parts list</h2>
{table(["Group", "Part", "Qty", "Size L × W (cm)", "Thk (mm)", "Material", "Notes"], parts_rows())}
</div>
<div class="page"><h2>Hardware</h2>{table(["Item", "Qty", "Specification"], HARDWARE)}
<h2 style="margin-top:12pt">Materials and finish</h2>
<ul>
<li>Carcass: 18 mm oak-veneered birch plywood, A/B crown-cut veneer, every exposed edge lipped with 5 mm solid oak. Grain vertical on the wing panels, horizontal on the long panels and continuous across the two drawer fronts.</li>
<li>Top and speaker caps: 30 mm solid European oak from glued-up boards. If movement is a concern, 30 mm veneered blockboard with 30 mm solid oak lipping.</li>
<li>Solid oak for the drawer fronts, tray aprons, rear rail and plinth boards.</li>
<li>Quantities: about 7.5 m² of 18 mm oak-veneered birch ply (three 250 × 125 sheets with waste), about 1 m² of 30 mm solid oak for the top and caps, plus solid oak for aprons, rail, drawer fronts, plinths and lipping. The carpenter should re-check against their stock sizes.</li>
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
