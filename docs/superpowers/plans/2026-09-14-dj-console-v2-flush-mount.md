# DJ Console v2 (Flush-Mounted Gear) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a second variant of the DJ + piano console in which the gear is sunk 9 cm into the top so only its working faces surface, without disturbing v1.6.

**Architecture:** `generate.py` gains a `VARIANT` switch read from the environment. v2 overrides six parameters and adds well/fascia geometry; the four drawing functions branch on `VARIANT`; outputs are suffixed `-v2`. v1.6's outputs must be unchanged.

**Tech Stack:** Python 3 standard library only (no deps). SVG written by hand. Headless Chrome for the WebGL render and the PDF. No test framework in this repo — verification is `assert` statements in the parameter block plus greps on the generated SVGs.

**Spec:** `docs/superpowers/specs/2026-09-14-dj-console-v2-flush-mount-design.md`

## Global Constraints

- All dimensions in centimetres. Envelope is fixed at 185 × 50 × 130; top surface at 100.
- `WELL_DROP = 9.0` — given by Luca, the clearance the hardware needs below the top surface. Everything else derives from it.
- Derived, exact: `Z_WELL_FLOOR` 91.0, `FASCIA_H` 6.0, `DRW_H` 9.2, `GEAR_Y` 5.0, `BACK_INSET` 0.0, `INT_D` 48.2, min back rail 7.0.
- Name the new fascia `FASCIA_H`. Do **not** call it `APRON_*` — `APRON_UP` / `APRON_H` already mean the piano tray apron (`generate.py:20`).
- Never edit anything under `codebase/`. This work is confined to `personal/`.
- v1 invariant, checked after every task: `VARIANT` unset must reproduce `drawing-{front,side,plan,detail}.svg` byte-identically against git.
- Float comparisons use a tolerance; `81.8` and `9.2` are not exact in binary.

---

### Task 1: Variant switch, v2 parameters, assertions

**Files:**
- Modify: `dj-piano-console/generate.py:1-57` (parameter block), `:545-552` (main)

**Interfaces:**
- Produces: `VARIANT`, `SUFFIX`, `WELL_DROP`, `Z_WELL_FLOOR`, `FASCIA_H`, `WELL_CLEAR`, `Z_DRW_TOP`, and `well_positions() -> list[tuple[str, float, float, float, float, float]]` returning `(name, x, width, y0, y1, floor_z)` per unit. Every later task consumes these.

- [ ] **Step 1: Write the failing assertions**

Append **after `well_positions()`** (added in Step 3), not inside the parameter block: the checks call it, so placing them at `generate.py:52` as the spec's wording suggests would raise `NameError` at import. The spec says "end of the parameter block"; the nearest honest reading is "before any drawing code runs", which this satisfies.

```python
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
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd ~/Desktop/claude/personal/dj-piano-console && VARIANT=2 python3 generate.py
```
Expected: `NameError: name 'VARIANT' is not defined` (the guard itself is undefined, so the block never runs). After Step 3 defines `VARIANT` but before the overrides land, the same command must fail on `assert _eq(_deep, 41.2)` instead — run it once in that intermediate state to confirm the assertions actually bite.

- [ ] **Step 3: Add the switch and the v2 overrides**

At the top of the parameter block, after `os.makedirs(OUT, exist_ok=True)` (`generate.py:6`):

```python
VARIANT = int(os.environ.get("VARIANT", "1"))   # 1 = gear on top (v1.6), 2 = flush-mounted
SUFFIX = "" if VARIANT == 1 else f"-v{VARIANT}"
```

Then, immediately after `GEAR_MARGIN, GEAR_GAP, GEAR_Y = 3.0, 6.0, 2.0` (`generate.py:57`):

```python
# ---------------- v2: flush-mounted gear ----------------
WELL_DROP = 9.0                           # clearance the hardware needs below the surface
Z_WELL_FLOOR = H_TOP - WELL_DROP          # 91.0
FASCIA_H = Z_TOP_UNDER - Z_WELL_FLOOR     # 6.0 -> apparent slab TT + FASCIA_H = 9.0
WELL_CLEAR = 0.2                          # cut-out clearance per side
if VARIANT == 2:
    GEAR_Y = 5.0                          # front rail, was 2.0
    BACK_INSET = 0.0                      # back panel moves to the rear face
    Y_BACK0 = D - BACK_INSET - T          # 48.2
    Y_BACK1 = D - BACK_INSET              # 50.0
    INT_D = Y_BACK0                       # 48.2
    DRW_H = Z_WELL_FLOOR - Z_FIX_TOP      # 9.2, was 15.2
Z_DRW_TOP = Z_WELL_FLOOR if VARIANT == 2 else Z_TOP_UNDER
```

Add below `gear_positions()` (after `generate.py:63`):

```python
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
```

- [ ] **Step 4: Suffix the outputs**

In `__main__` (`generate.py:545-552`), replace the three output paths:

```python
    for k, v in svgs.items():
        with open(os.path.join(OUT, f"drawing-{k}{SUFFIX}.svg"), "w") as f: f.write(v)
    render = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, f"render-cg{SUFFIX}.png")
    with open(os.path.join(OUT, f"dj-piano-console{SUFFIX}-spec.html"), "w") as f: f.write(build_html(svgs, render))
```

- [ ] **Step 5: Run both variants**

```bash
cd ~/Desktop/claude/personal/dj-piano-console
python3 generate.py && VARIANT=2 python3 generate.py
git diff --stat -- drawing-front.svg drawing-side.svg drawing-plan.svg drawing-detail.svg
```
Expected: both print `ok`; the `git diff --stat` is **empty** (v1 unchanged); `drawing-*-v2.svg` now exist.

- [ ] **Step 6: Commit**

```bash
git add dj-piano-console/generate.py
git commit -m "Add VARIANT switch and v2 flush-mount parameters to the console generator"
```

---

### Task 2: Front elevation

**Files:**
- Modify: `dj-piano-console/generate.py:189-237` (`front_elevation`)

**Interfaces:**
- Consumes: `VARIANT`, `Z_WELL_FLOOR`, `FASCIA_H`, `WELL_DROP`, `Z_DRW_TOP`, `well_positions()`.

- [ ] **Step 1: Write the failing check**

```bash
cd ~/Desktop/claude/personal/dj-piano-console && VARIANT=2 python3 generate.py && grep -c '9 slab' drawing-front-v2.svg
```
Expected: `0` — v2 currently draws v1's 3 cm top with the gear standing on it.

- [ ] **Step 2: Make the drawer band variant-aware**

At `generate.py:191`, the finger-pull line is anchored to the old drawer top. Replace `Z_TOP_UNDER` with `Z_DRW_TOP`:

```python
        d.line(ox + 8, Z_DRW_TOP - 1.7, ox + DRW_W - 8, Z_DRW_TOP - 1.7, stroke=OAKE, sw=1.2)
```

- [ ] **Step 3: Branch the top and gear block**

Replace `generate.py:200-206` (from `d.rect(X_BAY0, Z_TOP_UNDER, BAY_W, TT)` through the turntable platter line):

```python
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
```

Chassis are drawn filling the well exactly to 100 — faceplates flush. Do not invent knob or tonearm projections above the line; the spec does not fix them and the carpenter templates off the real units.

- [ ] **Step 4: Branch the cable note**

Replace the note at `generate.py:208`:

```python
    if VARIANT == 1:
        d.text(W / 2, 123.6, f"Cable slot {SLOT_Y1 - SLOT_Y0:g} × {SLOT_X1 - SLOT_X0:g} cm routed in the top behind the gear; leads, plugs and the XDJ bricks pass down into the chase and the power niche", size=9, fill=NOTE, italic=True)
    else:
        d.text(W / 2, 123.6, "Gear sunk 9 cm into the slab, faceplates flush. Each well slots at the rear into a continuous cable trough under the back rail; no dust covers can be fitted", size=9, fill=NOTE, italic=True)
```

- [ ] **Step 5: Fix the drawer dimension and add the slab dimension**

Replace `generate.py:226` (which hardcodes `"15.2"`):

```python
    d.dim_v(Z_TRAY_TOP, Z_CAV_TOP, xr, "17", ext=X_BAY1); d.dim_v(Z_FIX_TOP, Z_DRW_TOP, xr, f"{DRW_H:g}", ext=X_BAY1)
    if VARIANT == 2: d.dim_v(Z_WELL_FLOOR, H_TOP, xr, f"{FASCIA_H + TT:g} slab", ext=X_BAY1)
```

This also removes a latent wart in v1, where the label was a literal that would silently lie if `DRW_H` ever moved.

- [ ] **Step 6: Run to verify it passes**

```bash
cd ~/Desktop/claude/personal/dj-piano-console
python3 generate.py && VARIANT=2 python3 generate.py
grep -c '9 slab' drawing-front-v2.svg          # expect 1
grep -c '>9.2<' drawing-front-v2.svg           # expect 1
git diff --stat -- drawing-front.svg           # expect empty
open drawing-front-v2.svg
```
Eyeball: the slab reads 9 cm deep across the bay, four dark wells sit in it flush at 100, the drawer band below is visibly shallower than v1.

- [ ] **Step 7: Commit**

```bash
git add dj-piano-console/generate.py dj-piano-console/drawing-front-v2.svg
git commit -m "Draw the v2 slab and gear wells in the front elevation"
```

---

### Task 3: Side section

**Files:**
- Modify: `dj-piano-console/generate.py:250-315` (`side_section`)

**Interfaces:**
- Consumes: `VARIANT`, `Z_WELL_FLOOR`, `FASCIA_H`, `GEAR_Y`, `INT_D`, `Y_BACK0`, `Y_BACK1`, `well_positions()`.

This is the drawing that carries the two ideas a carpenter most needs: the 9 cm slab in section, and the cable trough under the back rail.

- [ ] **Step 1: Write the failing check**

```bash
cd ~/Desktop/claude/personal/dj-piano-console && VARIANT=2 python3 generate.py && grep -c '48.2 interior' drawing-side-v2.svg
```
Expected: `0`.

- [ ] **Step 2: Branch the chase hatch**

`generate.py:250-251` hatches the 5 cm chase, which no longer exists in v2. Guard it:

```python
    # chase hatch
    if VARIANT == 1:
        for zz in range(22, 97, 4): d.line(Y_BACK1, zz, D, zz + 3, stroke=GHOST, sw=0.5)
```

- [ ] **Step 3: Branch the top section**

Replace `generate.py:258` (`d.rect(0, Z_TOP_UNDER, SLOT_Y0, TT); d.rect(SLOT_Y1, ...)`):

```python
    if VARIANT == 1:
        d.rect(0, Z_TOP_UNDER, SLOT_Y0, TT); d.rect(SLOT_Y1, Z_TOP_UNDER, D - SLOT_Y1, TT)
    else:
        xone = [w for w in well_positions() if w[0] == "Xone:92"][0]
        d.rect(0, Z_WELL_FLOOR, GEAR_Y, FASCIA_H + TT)                 # front rail, 5 cm
        d.rect(xone[4], Z_WELL_FLOOR, Y_BACK0 - xone[4], TT)           # back rail: oak at the surface...
        d.rect(xone[4], Z_TOP_UNDER, Y_BACK0 - xone[4], 0)             # ...open beneath -> the trough
        d.rect(GEAR_Y, Z_WELL_FLOOR, xone[4] - GEAR_Y, 0.9, fill=OAK2) # well floor on its cleat
        d.text((xone[4] + Y_BACK0) / 2, Z_WELL_FLOOR + 2.6, "trough", size=7, fill=NOTE)
```

The zero-height `rect` is a deliberate no-op placeholder for the open band; delete it and rely on the surrounding outlines if it renders as a stray line.

- [ ] **Step 4: Sink the mixer**

Replace `generate.py:280` so the Xone sits in its well instead of on the top:

```python
    if VARIANT == 1:
        d.rect(GEAR_Y, H_TOP, 35.8, 10.7, fill=GEARC, stroke="none")
    else:
        d.rect(GEAR_Y, Z_WELL_FLOOR + 0.9, 35.8, WELL_DROP - 0.9, fill=GEARC, stroke="none")
```

- [ ] **Step 5: Fix the depth dimensions**

Replace `generate.py:307`:

```python
    d.dim_h(0, INT_D, -5, f"{INT_D:g} interior", ext=0, above=False)
    if VARIANT == 1: d.dim_h(Y_BACK1, D, -5, "5", ext=0, above=False)
    if VARIANT == 2:
        d.dim_h(0, GEAR_Y, 114, f"{GEAR_Y:g} front rail", ext=H_TOP)
        d.dim_h(xone[4], Y_BACK0, 114, f"{Y_BACK0 - xone[4]:g} back rail", ext=H_TOP)
```

`xone` is bound in Step 3 inside the same function, so it is in scope. If the executor reordered anything, re-derive it rather than relying on that.

- [ ] **Step 6: Branch the leaders**

`generate.py:300-304` label the chase and the inset back panel, both gone in v2. Wrap the two chase leaders in `if VARIANT == 1:` and add for v2:

```python
    else:
        d.leader(xone[4] + 2, Z_WELL_FLOOR + 3, R, 154, "cable trough under the back rail, 7 cm deep, runs the full bay and vents the Xone", anchor="end", italic=True)
        d.leader(Y_BACK0 + 0.9, 40, R, 146, "back panel 18 mm, flush with the rear face", anchor="end", italic=True)
```

Also branch `generate.py:302` ("back panel 18 mm, inset 5 cm") so v1 keeps its wording.

- [ ] **Step 7: Run to verify it passes**

```bash
cd ~/Desktop/claude/personal/dj-piano-console
python3 generate.py && VARIANT=2 python3 generate.py
grep -c '48.2 interior' drawing-side-v2.svg    # expect 1
grep -c 'front rail' drawing-side-v2.svg       # expect >= 1
git diff --stat -- drawing-side.svg            # expect empty
open drawing-side-v2.svg
```
Eyeball: front rail solid from 91 to 100; the well floor visible at 91; the band from 91 to 97 behind the well open through to the back panel.

- [ ] **Step 8: Commit**

```bash
git add dj-piano-console/generate.py dj-piano-console/drawing-side-v2.svg
git commit -m "Draw the v2 slab section, sunk mixer and cable trough in the side section"
```

---

### Task 4: Plan view

**Files:**
- Modify: `dj-piano-console/generate.py:329-352` (`plan_view`)

**Interfaces:**
- Consumes: `VARIANT`, `GEAR_Y`, `well_positions()`, `Y_BACK0`.

- [ ] **Step 1: Write the failing check**

```bash
cd ~/Desktop/claude/personal/dj-piano-console && VARIANT=2 python3 generate.py && grep -c 'cut-out' drawing-plan-v2.svg
```
Expected: `0`.

- [ ] **Step 2: Replace the cable slot with the wells**

Replace `generate.py:329-331` (the slot rect and its label):

```python
    if VARIANT == 1:
        d.rect(SLOT_X0, SLOT_Y0, SLOT_X1 - SLOT_X0, SLOT_Y1 - SLOT_Y0, fill="#3a3a3a", stroke="none", rx=2.5)
        d.text((SLOT_X0 + SLOT_X1) / 2, SLOT_Y0 + 3, f"cable slot {SLOT_X1 - SLOT_X0:g} × {SLOT_Y1 - SLOT_Y0:g}", size=8, fill="white", dy=3)
    else:
        for n, wx, ww, wy0, wy1, wfz in well_positions():
            d.rect(wx, wy0, ww, wy1 - wy0, fill="none", stroke="#C0392B", sw=1.2, dash="4,3")
            d.text(wx + ww / 2, wy1 + 2.0, f"cut-out {ww:g} × {wy1 - wy0:g}", size=7, fill="#C0392B", dy=3)
        d.text((X_BAY0 + X_BAY1) / 2, Y_BACK0 - 3.4, "cable trough under the back rail, full bay width", size=8, fill=NOTE, italic=True, dy=3)
```

The red dashed outline is the cut-out; the solid dark rect already drawn by the gear loop is the unit itself, so the 2 mm clearance reads directly off the drawing.

- [ ] **Step 3: Fix the depth dimensions**

Replace `generate.py:350`:

```python
    if VARIANT == 1:
        d.dim_v(0, SLOT_Y0, xr, f"{SLOT_Y0:g}", ext=X_BAY1); d.dim_v(SLOT_Y0, SLOT_Y1, xr, f"{SLOT_Y1 - SLOT_Y0:g}", ext=X_BAY1); d.dim_v(SLOT_Y1, D, xr, f"{D - SLOT_Y1:g}", ext=X_BAY1)
    else:
        _deep = max(w[4] for w in well_positions())
        d.dim_v(0, GEAR_Y, xr, f"{GEAR_Y:g} front rail", ext=X_BAY1)
        d.dim_v(GEAR_Y, _deep, xr, f"{_deep - GEAR_Y:g} deepest well", ext=X_BAY1)
        d.dim_v(_deep, Y_BACK0, xr, f"{Y_BACK0 - _deep:g} back rail", ext=X_BAY1)
```

- [ ] **Step 4: Run to verify it passes**

```bash
cd ~/Desktop/claude/personal/dj-piano-console
python3 generate.py && VARIANT=2 python3 generate.py
grep -c 'cut-out' drawing-plan-v2.svg          # expect 4
grep -c 'back rail' drawing-plan-v2.svg        # expect >= 1
git diff --stat -- drawing-plan.svg            # expect empty
open drawing-plan-v2.svg
```
Eyeball: four dashed cut-outs, all front edges on one line at 5 cm; webs between them read as ~5.6 cm of oak.

- [ ] **Step 5: Commit**

```bash
git add dj-piano-console/generate.py dj-piano-console/drawing-plan-v2.svg
git commit -m "Draw the v2 gear cut-outs and rails in the plan view"
```

---

### Task 5: Detail B — well section (BEYOND THE APPROVED SPEC)

**Files:**
- Create: nothing
- Modify: `dj-piano-console/generate.py` (new `detail_well()` after `detail_tray`, `generate.py:386`), `:545` (svgs dict), `build_html` drawing page

**Scope note:** the approved spec says v2 adds well geometry "to the four drawings" and does not ask for a fifth. This task adds one anyway, because the well — rebate versus cleat, floor, rear slot, finger notch — is v2's only genuinely novel joint and the thing most likely to be built wrong from plan and section alone. **Confirm with Luca before doing this task.** If he declines, skip it and renumber nothing; no later task depends on it.

**Interfaces:**
- Consumes: `Z_WELL_FLOOR`, `FASCIA_H`, `TT`, `WELL_CLEAR`, `T`.
- Produces: `detail_well() -> str` (SVG), and `svgs["well"]` when `VARIANT == 2`.

- [ ] **Step 1: Write the failing check**

```bash
cd ~/Desktop/claude/personal/dj-piano-console && VARIANT=2 python3 generate.py && test -f drawing-well-v2.svg && echo present || echo absent
```
Expected: `absent`.

- [ ] **Step 2: Write the detail**

Add after `detail_tray()` ends (`generate.py:386`). Follow `detail_tray`'s idiom exactly — same `Drawing` construction with a large right pad for the leader column, same `d.leader` stack:

```python
# ---------------- 5. detail B: gear well (v2) ----------------
def detail_well():
    d = Drawing(-4, 20, 86, 103, scale=16.0, pad=(30, 20, 400, 40))
    d.rect(0, Z_WELL_FLOOR, 5.0, FASCIA_H + TT, fill=OAK)            # front rail in section
    d.line(0, Z_TOP_UNDER, 5.0, Z_TOP_UNDER, stroke=OAKE, sw=0.8, dash="3,2")
    d.rect(5.0, Z_WELL_FLOOR, 0.9, 1.4, fill=OAK2)                   # cleat
    d.rect(5.0 + 0.9, Z_WELL_FLOOR, 12, 0.9, fill=OAK2)              # well floor
    d.rect(5.0 + 0.9, Z_WELL_FLOOR + 0.9, 12, WELL_DROP - 0.9, fill=GEARC, stroke="none")
    d.line(5.0, H_TOP, 20, H_TOP, stroke=INK, sw=1.4)                # the flush line
    d.dim_v(Z_WELL_FLOOR, H_TOP, 18.4, f"{WELL_DROP:g} clear", right=False)
    d.dim_v(Z_TOP_UNDER, H_TOP, 2.5, f"{TT:g}", right=False)
    d.dim_v(Z_WELL_FLOOR, Z_TOP_UNDER, 2.5, f"{FASCIA_H:g}", right=False)
    R = 21.0
    d.leader(2.5, Z_TOP_UNDER + 1.4, R, 101.5, "Oak top board 30 mm; cut-out edges eased, not lipped")
    d.leader(2.5, Z_WELL_FLOOR + 3.0, R, 99, "Fascia 60 mm solid oak, front and both ends; bottom edge lands on the well floors at 91")
    d.leader(5.6, Z_WELL_FLOOR + 0.4, R, 96.5, "Well floor 18 mm on an adjustable cleat: slotted screw holes, +/- 10 mm, set at fit-out")
    d.leader(9, Z_WELL_FLOOR + 5, R, 94, "Unit stands on its own feet. The Technics plinth has no flange and cannot bear on a rebate; the Xone:92 and XDJ-700 faceplates may, confirm against the units")
    d.leader(14, H_TOP, R, 91.5, "Faceplate flush with the oak. 2 mm clearance each side and at the rear, none at the front so the rail reads straight")
    d.leader(16, Z_WELL_FLOOR + 6, R, 89, "Slot the rear wall into the cable trough: leads out, and the Xone's heat with them")
    d.text(2.0, 87.5, "finger notches at two corners of each well, r 20 mm", size=8, fill=NOTE, italic=True, anchor="start")
    return d.render()
```

- [ ] **Step 3: Register it**

In `__main__` (`generate.py:546`):

```python
    svgs = {"front": front_elevation(), "side": side_section(), "plan": plan_view(), "detail": detail_tray()}
    if VARIANT == 2: svgs["well"] = detail_well()
```

In `build_html`, on the drawing page that currently holds Detail A, append when present:

```python
{("<h2 style='margin-top:14pt'>5. Detail B: gear well (section through the front rail)</h2>" + svgs['well'].replace('<svg ', '<svg style="height:70mm" ', 1)) if 'well' in svgs else ''}
```

- [ ] **Step 4: Run to verify it passes**

```bash
cd ~/Desktop/claude/personal/dj-piano-console
python3 generate.py && VARIANT=2 python3 generate.py
test -f drawing-well-v2.svg && echo present
git diff --stat -- drawing-detail.svg          # expect empty
open drawing-well-v2.svg
```

- [ ] **Step 5: Commit**

```bash
git add dj-piano-console/generate.py dj-piano-console/drawing-well-v2.svg
git commit -m "Add Detail B, a section through a gear well, to the v2 package"
```

---

### Task 6: Parts list and hardware

**Files:**
- Modify: `dj-piano-console/generate.py:388-412` (`parts_rows`), `:413-430` (`HARDWARE`)

**Interfaces:**
- Consumes: `VARIANT`, `FASCIA_H`, `Z_WELL_FLOOR`, `WELL_DROP`, `DRW_H`, `INT_D`, `Y_BACK0`, `well_positions()`.

`parts_rows()` currently returns one flat list. Make it branch: build the shared rows, then append or substitute the variant-specific ones. Rows already interpolating `DRW_H`, `INT_D`, `Y_BACK1` correct themselves.

- [ ] **Step 1: Write the failing check**

```bash
cd ~/Desktop/claude/personal/dj-piano-console && VARIANT=2 python3 generate.py && grep -c 'Slab fascia' dj-piano-console-v2-spec.html
```
Expected: `0`.

- [ ] **Step 2: Substitute the Top row and add the new parts**

At `generate.py:396`, the `("Bay", "Top", ...)` row describes the routed cable slot. Replace that row for v2 and add four parts after it:

```python
        ("Bay", "Top", 1, f"{BAY_W:g} × {D:g}", 30, "Solid oak, or 30 mm veneered board with 30 mm oak lipping",
         "Routed cable slot 115 × 6 cm, 41 cm from the front edge, centred, ends rounded r 3. Passes plugs and the XDJ bricks."
         if VARIANT == 1 else
         f"Four cut-outs for the gear, all front edges {GEAR_Y:g} cm from the front edge. Sizes per the plan; 2 mm clearance at sides and rear, none at the front. Finger notches r 20 mm at two corners of each. Edges eased, not lipped."),
```

Then, for `VARIANT == 2` only, append:

```python
    if VARIANT == 2:
        rows += [
            ("Bay", "Slab fascia", 1, f"{BAY_W:g} × {FASCIA_H:g}", 60, "Solid oak", f"Front face, returned on both ends. Bottom edge at {Z_WELL_FLOOR:g}, flush with the well floors. Makes the top read as a {TT + FASCIA_H:g} cm slab."),
            ("Bay", "Well side wall", 8, f"{FASCIA_H:g} × well depth", 18, "Oak-veneered ply", "Two per well, hung from the underside of the top board down to 91. Glued to the top board: this is what stiffens the webs between the wells."),
            ("Bay", "Well rear wall", 4, f"{FASCIA_H:g} × well width", 18, "Oak-veneered ply", "One per well, slotted for cables into the trough. Slot the Xone:92's full width for airflow."),
            ("Bay", "Well floor", 4, "well width × well depth", 18, "Oak-veneered ply", f"Top face at {Z_WELL_FLOOR:g}. On adjustable cleats, slotted +/- 10 mm, so the flush line is set against the real units at fit-out."),
            ("Bay", "Well floor cleat", 8, "20 × 14 mm × well depth", 20, "Solid oak", "Two per well, slotted screw holes."),
        ]
```

- [ ] **Step 3: Fix the back panel row**

`generate.py:399` says "Inset 5 cm". Make the lead sentence variant-aware:

```python
        ("Bay", "Bay back panel", 1, f"{BAY_W:g} × {Z_TOP_UNDER - Z_BOT_TOP:g}", 18, "Oak-veneered ply",
         ("Inset 5 cm. " if VARIANT == 1 else "Flush with the rear face. Vent cutout behind the trough at 91 to 97. ")
         + f"Cutout {CUT_W:g} × {CUT_H:g} cm behind the tray at {CUT_Z0:g} to {CUT_Z0 + CUT_H:g} cm; cutout {NICHE_W:g} × {NICHE_CUT_H:g} cm behind the niche at {NICHE_CUT_Z0:g} to {NICHE_CUT_Z0 + NICHE_CUT_H:g} cm."),
```

- [ ] **Step 4: Fix the drawer box row**

`generate.py:405` hardcodes "40 deep × 12 high". With `DRW_H` at 9.2 a 12 cm box no longer fits, and the box can now run deeper than v1's 40 because the wells stop at 91:

```python
        ("Bay", "Drawer box", 2, "45 deep × 7 high, width per runner spec" if VARIANT == 2 else "40 deep × 12 high, width per runner spec", 15, "Birch ply, 6 mm bottom", "For the 58.7 cm openings, sized to the runners. Notch the niche-side wall 6 × 4 cm at the rear if the pass-through is used."),
```

- [ ] **Step 5: Fix the hardware list**

In `HARDWARE` (`generate.py:413`), three entries are wrong for v2. Make the list a function of `VARIANT`, or post-filter it:
- "Cable slot brush strip" — drop for v2, there is no slot.
- "Power strip" — its note says "Niche is 24 wide × 15 tall × 48 deep including the chase". For v2: `24 wide × {DRW_H:g} tall × {INT_D:g} deep, open at the top into the cable trough`.
- "Drawer runners" — 400 mm is still right, but add "check the 45 cm box depth against the 48.2 cm interior before ordering" for v2.

Add for v2: `("Well floor cleats and fixings", "8 cleats", "M5 threaded inserts and pan screws in slotted holes, +/- 10 mm of travel, so each unit's flush line is set at fit-out rather than at cutting.")`

- [ ] **Step 6: Run to verify it passes**

```bash
cd ~/Desktop/claude/personal/dj-piano-console
python3 generate.py && VARIANT=2 python3 generate.py
grep -c 'Slab fascia' dj-piano-console-v2-spec.html      # expect 1
grep -c 'brush grommet' dj-piano-console-v2-spec.html    # expect 0
grep -c 'brush grommet' dj-piano-console-spec.html       # expect 1
```

- [ ] **Step 7: Commit**

```bash
git add dj-piano-console/generate.py
git commit -m "Update the parts list and hardware for the v2 slab, wells and shallower drawers"
```

---

### Task 7: Spec prose

**Files:**
- Modify: `dj-piano-console/generate.py:440-474` (`zones`), `:475-485` (`key`), `:486-491` (`ergo`), `:492-503` (`build`)

Four prose blocks still describe v1's geometry. Every one of them is read by the carpenter, so a stale sentence here is worse than a stale drawing.

- [ ] **Step 1: Write the failing check**

```bash
cd ~/Desktop/claude/personal/dj-piano-console && VARIANT=2 python3 generate.py && grep -c 'cable chase' dj-piano-console-v2-spec.html
```
Expected: a non-zero count — v1's chase prose is still being emitted into the v2 spec.

- [ ] **Step 2: Rewrite `zones`**

`"DJ surface"` (`:442`) and `"Drawer band"` (`:443`) for v2:

```python
        ("DJ surface", f"100 (slab {Z_WELL_FLOOR:g} to 100)", f"Turntable, XDJ-700, Xone:92, XDJ-700 left to right within the 145 cm bay, each sunk {WELL_DROP:g} cm into the slab with its faceplate flush. Front rail {GEAR_Y:g} cm, oak webs about 5.6 cm between units. Dust covers cannot be fitted."),
        ("Drawer band", f"81.8 to {Z_WELL_FLOOR:g}", f"Two flush drawers of 58.7 cm ({DRW_H:g} cm high) with a 24 cm power niche between them: push-to-open door, strip and bricks inside, open at the top into the cable trough."),
```

Add a zone: `("Cable trough", f"{Z_WELL_FLOOR:g} to {Z_TOP_UNDER:g}", "Continuous under the back rail, full 145 cm bay, 7 cm deep behind the Xone:92 and 12.2 behind the XDJs. Every well slots into it. Also the mixer's ventilation path.")`

- [ ] **Step 3: Fix `key`**

`"Depth budget"` (`:481`) still says "5 chase". For v2:

```python
        ("Depth budget", f"{INT_D:g} usable inside the bay, 1.8 back panel flush with the rear face. Front rail {GEAR_Y:g}, deepest well 36.2, back rail 7.0. Wings use the full depth ({D - T:g} inside)."),
```

`"Panel thickness"` (`:482`) for v2: `"18 mm carcass, 30 mm top and caps over a 60 mm fascia, 15 mm drawer boxes."`

- [ ] **Step 4: Fix `ergo`**

Two of the four entries are wrong for v2:
- "Standing at the decks" (`:488`) — "mixer faders at about 111 cm" assumed the Xone standing on the top. For v2: `"Standing at the decks: surface at 100 cm, every faceplate flush with it. Toes go under the floating bay. Reaching into a well for a rear socket means lifting the unit out by its finger notches."`
- "Cables" (`:489`) — rewrite around the trough: `"Cables: each unit's leads leave through a slot in the rear wall of its well into the trough under the back rail, run along the bay and drop into the power niche, where the switched strip and the bricks sit. The keyboard's mains lead and the pedal cable keep their cutout behind the tray; leave a 60 cm slack loop for the tray travel. Stand the console a few centimetres off the wall: the back panel is flush with the rear face, and the trough vents through it."`

- [ ] **Step 5: Fix `build`**

Four of the numbered construction notes are v1-specific (`:493`, `:495`, `:496`, `:499` — tie the wings, the inset back panel, rout the slot, the power niche). For v2:
- Tie-the-wings note: top band becomes `91 to 100` rather than `97 to 100`.
- Inset-back-panel note: replace with "The bay back panel is flush with the rear face. The cable trough is formed by leaving the band from 91 to 97 open behind the wells, from wing to wing."
- Rout-the-slot note: replace with "Cut the four gear wells in the top before finishing, and dry-fit every unit before the fascia goes on. The flush line is set by the cleats, so cut the cut-outs to the units and leave the floor heights to fit-out."
- Power-niche note: the niche is now `24 × {DRW_H:g}` and opens upward into the trough, not rearward into a chase.

Add one: "Glue the well side walls to the underside of the top board before the fascia goes on. Each web between two wells is then a 30 mm cap on two 60 mm walls, which is what carries the span; a bare 30 mm web is not stiff enough to lean on."

- [ ] **Step 6: Run to verify it passes**

```bash
cd ~/Desktop/claude/personal/dj-piano-console
python3 generate.py && VARIANT=2 python3 generate.py
grep -c 'cable chase' dj-piano-console-v2-spec.html      # expect 0
grep -c 'cable chase' dj-piano-console-spec.html         # expect >= 1, v1 untouched
grep -c 'cable trough' dj-piano-console-v2-spec.html     # expect >= 3
```

- [ ] **Step 7: Commit**

```bash
git add dj-piano-console/generate.py
git commit -m "Rewrite the zones, key figures, ergonomics and build notes for v2"
```

---

### Task 8: Concept render

**Files:**
- Modify: `dj-piano-console/render-cg.html` (105 lines)

`render-cg.html` does not share code with `generate.py` — it restates the dimensions in its own Three.js scene, and the README already warns that massing changes must be mirrored by hand.

**Interfaces:**
- Consumes: nothing from `generate.py`. Reads `?v=2` from `location.search`.

- [ ] **Step 1: Write the failing check**

```bash
cd ~/Desktop/claude/personal/dj-piano-console && grep -c 'searchParams' render-cg.html
```
Expected: `0`.

- [ ] **Step 2: Add the variant switch**

Near the top of the script block, before the geometry is built:

```js
const V = new URLSearchParams(location.search).get('v') === '2' ? 2 : 1;
const WELL_DROP = 9.0, Z_WELL_FLOOR = 91.0, FASCIA_H = 6.0, GEAR_Y_V2 = 5.0;
```

- [ ] **Step 3: Mirror the massing**

Read the file first and follow its existing unit convention (it works in centimetres, matching `generate.py`). Three changes, all guarded by `V === 2`:
1. The bay top: extend it down from 100 to 91 so it reads as a 9 cm slab, and move the gear's y origin from 2 to 5.
2. The gear meshes: drop each one so its top face is at 100 rather than its base, i.e. translate down by its own height minus nothing — the top face sits on the plane at 100 either way; what changes is that the body is now inside the slab. Simplest faithful version: keep each unit's box but set its base at `Z_WELL_FLOOR` and its height to `WELL_DROP`, so nothing protrudes.
3. The drawer band: top at 91 instead of 97.

- [ ] **Step 4: Render both**

```bash
cd ~/Desktop/claude/personal/dj-piano-console
CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CH" --headless=new --use-angle=swiftshader --enable-unsafe-swiftshader --hide-scrollbars \
  --window-size=1600,1200 --virtual-time-budget=20000 \
  --screenshot="$PWD/render-cg-v2.png" "file://$PWD/render-cg.html?v=2"
open render-cg-v2.png
```
Expected: a visibly thicker top with the gear flush in it and a shallower drawer band. Compare side by side with `render-cg.png`.

- [ ] **Step 5: Commit**

```bash
git add dj-piano-console/render-cg.html dj-piano-console/render-cg-v2.png
git commit -m "Mirror the v2 flush-mount massing in the concept render"
```

---

### Task 9: Regenerate, PDF, README

**Files:**
- Modify: `dj-piano-console/README.md`
- Create: `dj-piano-console/dj-piano-console-v2-spec.pdf`

- [ ] **Step 1: Full regenerate, both variants**

```bash
cd ~/Desktop/claude/personal/dj-piano-console
CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
python3 generate.py
VARIANT=2 python3 generate.py
"$CH" --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$PWD/dj-piano-console-v2-spec.pdf" "file://$PWD/dj-piano-console-v2-spec.html"
```

- [ ] **Step 2: Verify v1 is untouched**

```bash
git status --porcelain dj-piano-console/drawing-front.svg dj-piano-console/drawing-side.svg \
  dj-piano-console/drawing-plan.svg dj-piano-console/drawing-detail.svg
```
Expected: no output. If any v1 SVG changed, a `VARIANT` guard is missing — fix it before continuing rather than committing the drift.

- [ ] **Step 3: Read the v2 PDF end to end**

```bash
open dj-piano-console-v2-spec.pdf
```
Check specifically: no sentence mentions a cable slot or a 5 cm chase; the drawer band reads 9.2 everywhere it is dimensioned; the parts list has the fascia, well walls, floors and cleats; the dust-cover consequence appears.

- [ ] **Step 4: Update the README**

Add the v2 commands to the regenerate block (`VARIANT=2 python3 generate.py`, the `?v=2` render URL, the v2 PDF), list the v2 files, and append to the decisions log:

```
- 2026-09-14 — v2.0 flush-mounted gear: each unit sunk 9 cm into a 9 cm slab, faceplates flush. Envelope unchanged at 185 × 50 × 130. Back panel moved to the rear face to buy a 5 cm front rail and a 7 cm back rail; the band under the back rail becomes a continuous cable trough that also vents the Xone:92. Drawers 15.2 → 9.2. No dust covers. v1.6 still generated with VARIANT unset.
```

- [ ] **Step 5: Commit**

```bash
git add dj-piano-console/
git commit -m "Regenerate the v2 spec package and document the variant in the README"
```

---

## Self-Review

**Spec coverage.** Every section of the design doc maps to a task: derived dimensions and the variant switch → Task 1; the top assembly → Tasks 2, 3, 6; well geometry → Tasks 2, 4, 5; support → Tasks 5, 6; cable trough and heat → Tasks 3, 6, 7; the dust-cover consequence → Tasks 2, 7; package structure → Tasks 1, 8, 9. The "Verification" section's arithmetic checks are Task 1's assertions; its depth and bay closures are covered there too.

**Known gap, deliberate.** The spec names four drawings. Task 5 adds a fifth (the well section) and is flagged in place as beyond the approved scope, to be confirmed or dropped before it is started.

**Ordering.** Task 1's assertion block must sit after `well_positions()`, not in the parameter block — it calls that function. Caught on review; the step text says so explicitly.

**Type consistency.** `well_positions()` returns `(name, x, w, y0, y1, floor_z)` and is unpacked in that order in Tasks 2, 3, 4 and 6. `Z_DRW_TOP` is defined once in Task 1 and consumed in Task 2. `SUFFIX` is defined in Task 1 and used only in `__main__`.

**Carried risk.** Task 3's side section is the fiddliest edit — it touches six separate places in one function, and `xone` is bound in one step and used in another. If it fights back, split it rather than forcing it.
