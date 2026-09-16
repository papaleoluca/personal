# DJ + Piano Console v2: Flush-Mounted Gear — Design

## Context

v1.6 of the console (`dj-piano-console/`, approved 2026-09-14) stands the DJ gear
*on* the 100 cm top: turntable, XDJ-700, Xone:92, XDJ-700 in a row across the
145 cm bay, chassis and cabling fully visible.

Luca wants a second version where the gear is sunk into the top so that only the
working face of each unit surfaces — platters, faceplates, jog wheels — and every
chassis side, rear socket and cable disappears below the oak. His words: "the only
part of the gears that surface is the one you use. they look nestled."

Two reference photos set the intent. The decisive one shows two Technics decks and
a rotary mixer dropped into individual oak cut-outs with narrow webs between them,
finger notches at the well corners, and drawers surviving underneath.

Hardware constraint given by Luca: **the gear needs 9 cm of height below the top
surface.** Every dimension below derives from that figure.

v1.6 is not superseded. Both versions must remain generable and comparable.

## Goals

- Gear faceplates flush with the top surface, chassis and cabling hidden.
- Approved envelope held exactly: 185 x 50 x 130, top surface at 100.
- Piano tray, wings, record capacity and speaker caps carried over untouched.
- Drawers retained, even if shallower.
- Seated shin clearance at the book compartments (raised by Luca on review of the v1 section).
- Cables and mixer heat handled deliberately, not left to the carpenter.
- One generator still producing both versions — `generate.py` stays the single
  source of truth, as the README promises.

## Non-goals

- No change to the gear list or its left-to-right order.
- No change to the piano tray, its slides, the record wings or the speaker caps.
- No lid, hood or closing cover. "Cover" was ambiguous in the opening request and
  was resolved to mean flush-mounting, not a lid.
- No re-layout of the bay to create slack around the gear (see Open questions).

## Architecture

### Derived dimensions

Well floors sit at `H_TOP - WELL_DROP` = 100 - 9 = **91.0**. Everything follows:

| | v1.6 | v2 | note |
|---|---|---|---|
| `WELL_DROP` | — | **9.0** | given by Luca |
| `Z_WELL_FLOOR` | — | **91.0** | `H_TOP - WELL_DROP` |
| `FASCIA_H` | — | **6.0** | 91.0 -> 97.0 |
| apparent top thickness | 3.0 | **9.0** | `TT + FASCIA_H` |
| `TT` (oak top board) | 3.0 | 3.0 | unchanged, 97 -> 100 |
| `GEAR_Y` (front rail) | 2.0 | **5.0** | |
| `BACK_INSET` | 5.0 | **0.0** | back panel moves to the rear face |
| `Y_BACK0` / `INT_D` | 43.2 | **48.2** | |
| back rail (min) | — | **7.0** | 48.2 - 41.2, behind the Xone |
| `DRW_H` | 15.2 | **9.2** | `Z_WELL_FLOOR - Z_FIX_TOP` |
| drawer box depth | 43.2 | **48.2** | wells stop at 91, so drawers run full depth |
| well floor | — | **89.2 -> 91.0** | 18 mm, `T`; its top face is the plane the gear stands on |
| `Z_CAV_TOP` | 80.0 | **78.2** | mid panel drops 18 mm so the drawer band keeps its height |
| `Z_FIX_TOP` | 81.8 | **80.0** | `Z_CAV_TOP + T` |
| `Z_DRW_TOP` | 97.0 | **89.2** | drawer band ceiling = the floor's underside, not 91 |
| back panel top | 97.0 | **91.0** | stops at the trough so its whole rear face is open |
| `BOOK_SETBACK` | 0 | **15.0** | book zone front plane, for shin clearance |
| book compartment depth | 43.2 | **33.2** | `INT_D - BOOK_SETBACK`; a 31.4 cm LP fits with 1.8 spare |

Unchanged: `W` 185, `D` 50, `H_TOP` 100, `H_WING` 130, `WING_W` / `CAP_W` 20,
`BAY_W` 145, `T` 1.8, `Z_FIX_TOP` 81.8, `Z_CAV_TOP` 80, `Z_TRAY_TOP` 63,
`Z_CAP_UNDER` 127, `NICHE_W` 24, `DRW_W` 58.7, record capacity ~160.

Name `FASCIA_H`, not `APRON_*` — `APRON_UP` / `APRON_H` already denote the piano
tray apron in `generate.py`.

### The top assembly

The top becomes a 9 cm deep open grid rather than a 3 cm board:

- 3 cm oak top board, 97 -> 100, with four cut-outs through it.
- 6 cm fascia, 91 -> 97, returned across the front and both ends. Its bottom edge
  lands exactly on the well floors at 91. The drawer fronts run the full 80.0 -> 91.0,
i.e. **11.0 tall on 9.2 boxes**, overhanging each box upward by 18 mm so the front
face is closed: the well floors start 5 cm back, so nothing below the fascia would
otherwise fill z 89.2 -> 91 and an 18 mm slot would run the width of the piece into
the drawer cavity. The two drawer-band dividers are notched to match over their
front 5 cm. Front height therefore no longer equals `DRW_H`.
- Well side walls (1.8) hang from the top board down to the floors at 91.

Each web between two wells is therefore a 3 cm oak cap with two 6 cm walls glued
under it — a ~9 cm deep section, not a 3 cm strip. This is what resolves the
apparent fragility of a 5.6 cm web spanning 40 cm; the webs are also captured at
both ends by the front rail and the back rail.

### Well geometry

All four wells share a front line at y = 5.0 so the front rail is uniform. Back
edges vary by unit. Cut-outs are +2 mm per side on the unit footprint.

| unit | x (cm) | width | well y | well back |
|---|---|---|---|---|
| Turntable | 23.0 - 68.3 | 45.3 | 5.0 | 40.7 |
| XDJ-700 | 74.3 - 96.1 | 21.8 | 5.0 | 36.0 |
| Xone:92 | 102.1 - 134.1 | 32.0 | 5.0 | 41.2 |
| XDJ-700 | 140.1 - 161.9 | 21.8 | 5.0 | 36.0 |

Resulting oak after clearance: webs **5.6**, margin to the left wing **2.8**, to
the right wing **2.9**.

Finger notches at two corners of each well, per the reference photo, so a unit can
be lifted out without tools.

### Support

The Technics plinth is a plain box with no flange — it cannot bear on a rebate. Its
wells get adjustable cleats and a floor at 91; the deck stands on its own
height-adjustable feet, which is what dials the top face truly flush.

The Xone:92 and XDJ-700 have faceplates that overhang their chassis and can bear on
a rebate instead. Confirm against the real units before cutting (see Open questions).

All four wells are templated off the actual hardware, not off the numbers in this
document.

### Cable trough and heat

Moving the back panel to the rear face removes v1's 5 cm cable chase. The
replacement: the back rail is solid oak at the surface but **open underneath**,
z 91 -> 97, giving a continuous trough across the full 145 cm bay, 7.0 cm deep
behind the Xone and 12.2 cm behind the XDJs. Every well has a slot in its rear wall
opening into it.

This also answers the Xone:92 — an analogue mixer that runs warm and would
otherwise sit in a sealed box. Its well vents rearward into the trough.

**The trough's rear is open across the whole bay.** The bay back panel stops at
`Z_WELL_FLOOR` 91 rather than `Z_TOP_UNDER` 97, so the trough's entire rear face —
about 145 x 6 cm, roughly 870 cm2 — opens into the wall gap. An earlier version of
this design vented the trough through the upper 4 cm of the niche cutout alone,
about 96 cm2 at a single location, which made one aperture serve as both inlet and
outlet and could not sustain any flow. Stopping the panel short costs less material,
not more: the panel's stiffening job is its glued bottom edge at 21.8, and the top
assembly is carried by the top board, the webs and the two rails.

The power niche (x 80.5 - 104.5) becomes 80.0 -> 89.2 and keeps its back-panel cutout
at 83 -> 91, which now spans both the niche and the trough — so the power strip
feeds straight up into the trough.

### Power bricks must stand at the rear of the niche

Found during implementation, not at design time. Shrinking the drawer band to 9.2
also shrinks the power niche to 9.2 (80.0 -> 89.2), and v1's arrangement no longer
fits. v1 stood the wall-wart bricks **on** the power strip: strip about 4 cm, brick
about 8.5, total 12.5 measured from the niche floor at 81.8, topping out at 94.3.
That cleared v1's 97 ceiling with room to spare. In v2 it overshoots the 89.2 well-floor
underside by 3.3 cm at the front of the niche,
and there is no air above to overshoot into — directly over the niche (x 80.5 -
104.5) sit two well floors at z 91, the XDJ-700's across x 80.5 - 96.3 and the
Xone:92's across x 101.9 - 104.5. The brick would meet solid ply.

**The constraint is that bricks may no longer be stacked on the strip**, and that
they belong at the rear of the niche rather than the front.

Be careful which clearance applies where, because an earlier version of this section
got it wrong. At the **front** of the niche a brick stands under a well floor, so the
headroom is `Z_DRW_TOP` 89.2 - `Z_FIX_TOP` 80.0 = 9.2, and an 8.5 cm brick clears by
7 mm. At the **rear** — y 41.2 to 48.2, beyond the deepest well — there is no floor
overhead at all, only the open trough running up to the top board at 97, so the same
brick has roughly 17 cm. The 7 mm margin is a front-position figure and must not be
quoted against the rear placement this spec prescribes.

Place the bricks at the **rear** of the niche, within the trough footprint
(y 41.2 - 48.2). That is not needed for the brick to fit — it fits anywhere on the
floor — but it keeps the open trough above them free as the route for the mains lead
out through the niche cutout at 83 - 95. The trough is 7 cm deep there and a brick
about 6.

Carry into the build notes and the hardware list. The margin is 7 mm, so a taller
brick than 8.5 cm will not fit at all: worth measuring the actual units.

Because `BACK_INSET` is 0, the back panel is the rear face of the piece. The console
must stand a few centimetres off the wall for the trough to vent and for cables to
exit. This is a placement note for the spec sheet, not a construction detail.

### Book zone setback

Reviewing the v1 section, Luca flagged that a seated player's shins pass very close
to the book compartments. They do. The shin line in the section runs knee (-8, 54)
to ankle (2, 8), so it crosses:

| height | shin at y | clearance to the shelf front edge at y = 0 |
|---|---|---|
| 54 (knee) | -8.0 | 8.0 |
| 43.1 (upper shelf) | -5.6 | 5.6 |
| 30 | -2.8 | 2.8 |
| **21.8 (compartment floor)** | **-1.0** | **1.0** |

The pinch is not the books — it is the front edge of the bay bottom panel at 21.8,
which the shin passes at the moment it angles into the recess. One centimetre. The
figure in the drawing is an illustration rather than a measured model, but the
conclusion does not depend on it: any seated player with their feet in the recess
runs their shins through that plane.

Fix: set the whole book zone back **15.0 cm** — bay bottom panel, book divider and
both adjustable shelves, not merely the books. That leaves 16.0 cm at the pinch.

Consequence to accept: the front 15 cm then stands open from the floor to the tray
underside at 61.2, so the 20 cm foot recess grows into an L. This reads as the bay
floating and is consistent with the reference photos.

This is affordable only because moving the back panel already bought 5 cm. The
compartment lands at 48.2 - 15.0 = 33.2 deep, and a 31.4 cm LP sleeve fits with 1.8
to spare. v1.6 could not take this change: at 43.2 interior a 15 cm setback leaves
28.2 and LPs stop fitting. **v2 only** — whether to revisit v1 is deferred.

**Update, 2026-09-16 — no longer deferred; v1.7 has a setback too.** v1 took the same
fix at a smaller figure: **10.0 cm** in v1.7 against **15.0 cm** here, moving the same
parts (bay bottom panel, book divider, both adjustable shelves) and leaving 11.0 cm at
the 21.8 pinch instead of 1.0.

The two figures differ because the interiors do, and the binding constraint is the LP
sleeve rather than the shin line. v1 keeps its 5 cm cable chase, so it has 43.2 inside
and 15.0 would leave 28.2 — below the 31.4 an LP needs, which is exactly the objection
recorded above. 10.0 is the most it can give up: 43.2 - 10.0 = 33.2. v2 bought the
missing 5 cm by moving its back panel to the rear face, so 48.2 - 15.0 = 33.2 clears
with the same 1.8 to spare. Both versions therefore land on an identical 33.2 cm
compartment by different routes, and each is set back as far as its own interior allows.

### Consequence: no dust covers

v1 lists the turntable at 45.3 x 35.3 x **16.2** — that height includes the dust
cover. Flush-mounted, the covers cannot be fitted at all. Permanent and worth
stating on the drawing.

### Package structure

`generate.py` gains a `VARIANT` constant (1 or 2) at the top. v2 overrides the
parameters in the table above and adds the well/fascia geometry to the four
drawings. Outputs are suffixed per variant:

- `dj-piano-console-spec.{html,pdf}` (v1), `dj-piano-console-v2-spec.{html,pdf}`
- `drawing-*.svg` (v1), `drawing-*-v2.svg`

`render-cg.html` reads a `?v=2` query parameter and mirrors the massing, as it
already mirrors v1's by hand. The README's regenerate block gains the v2 commands.

## Verification

- Arithmetic closes, **including the 18 mm well floor** — the first version of this
  list omitted it, and the drawings and the parts list then resolved it in opposite
  directions. `Z_WELL_FLOOR` cannot be both the drawer-band ceiling and the plane the
  gear stands on. Chain, bottom to top: `Z_FIX_TOP` 80.0 + `DRW_H` 9.2 = `Z_DRW_TOP`
  89.2 (floor underside); 89.2 + `T` 1.8 = `Z_WELL_FLOOR` 91.0 (floor top face, gear
  bears here); 91.0 + `WELL_DROP` 9.0 = `H_TOP` 100.0; 91.0 + `FASCIA_H` 6.0 =
  `Z_TOP_UNDER` 97.0.
- The keyboard still clears the lowered mid panel: stowed top 63.0 + 12.0 = 75.0
  against a cavity ceiling of 78.2, leaving 3.2 (was 5.0).
- Depth closes: `GEAR_Y` 5.0 + deepest well 36.2 (Xone + clearance) + back rail 7.0
  = `INT_D` 48.2; + `T` 1.8 = `D` 50.0.
- Bay closes: 3.0 + 45.3 + 6 + 21.8 + 6 + 32.0 + 6 + 21.8 + 3.1 = `BAY_W` 145.0.
- Shin clearance closes: the shin line crosses z = 21.8 at y = -1.0, so a 15.0
  setback leaves 16.0 cm; compartment depth `INT_D` 48.2 - 15.0 = 33.2 >= 31.4 (LP).
- Power niche closes only unstacked: strip 4 + brick 8.5 stacked = 12.5 > niche
  height 9.2, but a floor-standing brick is 8.5 <= 9.2, clearing the floor underside
  at 89.2 by 0.7 — and at the REAR, beyond the wells, roughly 17 to the top board.
- Front face closes: drawer fronts 80.0 -> 91.0 meet the fascia's bottom edge at 91,
  leaving no open strip at 89.2 -> 91.
- Both variants regenerate from a clean checkout. v1's `drawing-*.svg` must come
  back byte-identical to the committed v1.6 files (`draw_books` is seeded, so the
  drawings are deterministic); the HTML and PDF will differ by the `date.today()`
  stamp at `generate.py:436` and by Chrome's own PDF metadata, so those are
  compared by eye, not by hash.
  *Update, 2026-09-16:* `dj-piano-console/check-regen.sh` now does this instead of a
  person doing it: it regenerates both variants and both concept renders into a temp
  directory and compares all thirteen artefacts by sha256, normalising the date stamp
  in the two HTML specs. `render-cg.html` is seeded as well now, so the PNGs are in
  the check too. Only the PDFs are still read by eye — Chrome's creation-date metadata
  makes them unhashable, and reading them is the point anyway.
- v2 PDF opened and read end to end against v1 before it goes to the carpenter.

## Testing

`generate.py` has no test suite today and this design does not add one. Verification
is the arithmetic assertions above plus visual review of the regenerated drawings
and render. If the assertions are worth keeping, they belong as plain `assert`
statements at the end of the parameter block, where they run on every generate.

## Open questions

- The 9 cm figure is Luca's. The chassis height *below the faceplate* differs per
  unit and must be measured off the real hardware before cutting; cleats are
  adjustable precisely so this can be dialled in late.
- Whether the Xone:92 and XDJ-700 faceplates can genuinely bear on a rebate, or
  whether they also need cleats. Decided at templating time.
- The gear fills the bay to within a millimetre, so there is no slack for wider
  future gear. Accepted for now rather than widening the piece.
