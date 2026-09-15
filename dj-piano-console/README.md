# DJ and piano console

Design package for a custom light-oak console that holds a DJ set-up (turntable, Xone:92, two XDJ-700) at standing height, a stage piano (133 × 35 × 12 cm) on a pull-out tray at seated height, about 160 records in two 20 cm end columns, books, two drawers with a power niche between them, and two 5-inch monitors on caps above the columns. 185 × 50 × 130 cm, natural oak, matte oiled. Built by a carpenter.

## Files

- `dj-piano-console-spec.pdf` — the v1 package to hand to the carpenter (overview, ergonomics, four dimensioned drawings, parts list, hardware, materials, construction notes, concept render).
- `dj-piano-console-v2-spec.pdf` — the v2 package (flush-mounted gear variant): same structure plus a fifth drawing, Detail B, the section through a gear well.
- `generate.py` — single source of truth for both variants. Every dimension is a parameter at the top; the `VARIANT` env var (1 or 2, default 1) switches to the v2 flush-mount geometry. Writes the SVG drawings and the HTML spec for whichever variant is selected.
- `render-cg.html` — Three.js scene of the piece built from the same centimetre dimensions; append `?v=2` to the URL to render the v2 flush-mounted massing. `render-cg.png` / `render-cg-v2.png` are its outputs and are embedded as the last page of the respective PDF.
- `drawing-*.svg` — v1 generated drawings (front elevation, side section, plan, tray detail).
- `drawing-*-v2.svg` — v2 generated drawings: front elevation, side section, plan, Detail A (tray edge), Detail B (gear well).

## Regenerate

```bash
cd personal/dj-piano-console
CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# 1. concept render (WebGL via SwiftShader in headless Chrome)
"$CH" --headless=new --use-angle=swiftshader --enable-unsafe-swiftshader --hide-scrollbars \
  --window-size=1600,1200 --virtual-time-budget=20000 \
  --screenshot="$PWD/render-cg.png" "file://$PWD/render-cg.html"
# v2 (flush-mounted gear): append ?v=2 to the URL and change the output filename
"$CH" --headless=new --use-angle=swiftshader --enable-unsafe-swiftshader --hide-scrollbars \
  --window-size=1600,1200 --virtual-time-budget=20000 \
  --screenshot="$PWD/render-cg-v2.png" "file://$PWD/render-cg.html?v=2"

# 2. drawings + HTML spec (embeds render-cg.png / render-cg-v2.png if present)
python3 generate.py
VARIANT=2 python3 generate.py

# 3. PDF
"$CH" --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$PWD/dj-piano-console-spec.pdf" "file://$PWD/dj-piano-console-spec.html"
"$CH" --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$PWD/dj-piano-console-v2-spec.pdf" "file://$PWD/dj-piano-console-v2-spec.html"
```

If a dimension changes, edit it in `generate.py` and, if it affects the massing, mirror it in `render-cg.html` (the two files do not share code). `VARIANT` selects the v2 flush-mount geometry in both scripts; v1.6 is still generated with `VARIANT` unset.

## Decisions log

- 2026-09-12 — v1.0 approved: 174 cm wide, wing columns with speaker caps, tray top at 63 cm, 20 cm foot and pedal recess, gear order turntable / XDJ / Xone:92 / XDJ.
- 2026-09-14 — v1.1 power niche between the drawers; v1.2 cable slot widened to 6 cm and optional pass-throughs into the drawers; v1.3 record capacity corrected to about 110; v1.4 accepted 110 in the wings; v1.5 wings widened to 20 cm each (185 cm overall, about 160 records), bay unchanged at 145; v1.6 speaker caps made flush with the columns (20 cm, no overhang; enough for KRK Rokit 5).
- 2026-09-14 — v2.0 flush-mounted gear: each unit sunk 9 cm into a 9 cm slab, faceplates flush. Envelope unchanged at 185 × 50 × 130. Back panel moved to the rear face to buy a 5 cm front rail and a 7 cm back rail; the freed band under the back rail becomes a continuous cable trough that also vents the Xone:92. Drawers 15.2 → 9.2. Book zone set back 15 cm for seated shin clearance (v2 only; v1's 43.2 cm interior cannot afford it without losing LP storage). Power bricks no longer stack on the strip — they stand on the niche floor beside it. No dust covers. v1.6 still generated with `VARIANT` unset.
