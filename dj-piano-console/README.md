# DJ and piano console

Design package for a custom light-oak console that holds a DJ set-up (turntable, Xone:92, two XDJ-700) at standing height, a stage piano (133 × 35 × 12 cm) on a pull-out tray at seated height, about 160 records in two 20 cm end columns, books, two drawers with a power niche between them, and two 5-inch monitors on caps above the columns. 185 × 50 × 130 cm, natural oak, matte oiled. Built by a carpenter.

## Files

- `dj-piano-console-spec.pdf` — the package to hand to the carpenter (overview, ergonomics, four dimensioned drawings, parts list, hardware, materials, construction notes, concept render).
- `generate.py` — single source of truth. Every dimension is a parameter at the top; it writes the four SVG drawings and `dj-piano-console-spec.html`.
- `render-cg.html` — Three.js scene of the piece built from the same centimetre dimensions; `render-cg.png` is its output and is embedded as the last page of the PDF.
- `drawing-*.svg` — generated drawings (front elevation, side section, plan, tray detail).

## Regenerate

```bash
cd personal/dj-piano-console
CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# 1. concept render (WebGL via SwiftShader in headless Chrome)
"$CH" --headless=new --use-angle=swiftshader --enable-unsafe-swiftshader --hide-scrollbars \
  --window-size=1600,1200 --virtual-time-budget=20000 \
  --screenshot="$PWD/render-cg.png" "file://$PWD/render-cg.html"

# 2. drawings + HTML spec (embeds render-cg.png if present)
python3 generate.py

# 3. PDF
"$CH" --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$PWD/dj-piano-console-spec.pdf" "file://$PWD/dj-piano-console-spec.html"
```

If a dimension changes, edit it in `generate.py` and, if it affects the massing, mirror it in `render-cg.html` (the two files do not share code).

## Decisions log

- 2026-09-12 — v1.0 approved: 174 cm wide, wing columns with speaker caps, tray top at 63 cm, 20 cm foot and pedal recess, gear order turntable / XDJ / Xone:92 / XDJ.
- 2026-09-14 — v1.1 power niche between the drawers; v1.2 cable slot widened to 6 cm and optional pass-throughs into the drawers; v1.3 record capacity corrected to about 110; v1.4 accepted 110 in the wings; v1.5 wings widened to 20 cm each (185 cm overall, about 160 records), bay unchanged at 145; v1.6 speaker caps made flush with the columns (20 cm, no overhang; enough for KRK Rokit 5).
