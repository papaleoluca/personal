# DJ and piano console

Design package for a custom light-oak console that holds a DJ set-up (turntable, Xone:92, two XDJ-700) at standing height, a stage piano (133 × 35 × 12 cm) on a pull-out tray at seated height, about 160 records in two 20 cm end columns, books, two drawers with a power niche between them, and two 5-inch monitors on caps above the columns. 185 × 50 × 130 cm, natural oak, matte oiled. Built by a carpenter.

## Files

- `dj-piano-console-spec.pdf` — the v1 package to hand to the carpenter (overview, ergonomics, four dimensioned drawings, parts list, hardware, materials, construction notes, concept render).
- `dj-piano-console-v2-spec.pdf` — the v2 package (flush-mounted gear variant): same structure plus a fifth drawing, Detail B, the section through a gear well, and a cut list for quoting (every piece of wood at its finished size, with totals per stock).
- `generate.py` — single source of truth for both variants. Every dimension is a parameter at the top; the `VARIANT` env var (1 or 2, default 1) switches to the v2 flush-mount geometry. Writes the SVG drawings and the HTML spec for whichever variant is selected.
- `render-cg.html` — Three.js scene of the piece built from the same centimetre dimensions; append `?v=2` to the URL to render the v2 flush-mounted massing. Its PRNG is seeded from a constant, so a re-render is byte-identical and the renders can be checked by hash like everything else. `render-cg.png` / `render-cg-v2.png` are its outputs and are embedded as the last page of the respective PDF.
- `drawing-*.svg` — v1 generated drawings (front elevation, side section, plan, tray detail).
- `drawing-*-v2.svg` — v2 generated drawings: front elevation, side section, plan, Detail A (tray edge), Detail B (gear well).
- `check-regen.sh` — the regression guard. Regenerates everything into a temporary directory and compares it with the copy checked in here. See [Check for drift](#check-for-drift).

## Regenerate

```bash
cd "$(git rev-parse --show-toplevel)/dj-piano-console"   # works from anywhere in the repo
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

If a dimension changes, edit it in `generate.py` and, if it affects the massing, mirror it in `render-cg.html` (the two files do not share code). `VARIANT` selects the v2 flush-mount geometry in both scripts; v1.7 is still generated with `VARIANT` unset.

Steps 1 and 2 are ordered: `generate.py` embeds whichever `render-cg*.png` it finds, so
re-render before regenerating the HTML. The block above covers both variants end to end —
two renders, two HTML specs with their nine drawings, two PDFs.

## Check for drift

```bash
dj-piano-console/check-regen.sh    # or ./check-regen.sh, or any absolute path
```

`check-regen.sh` regenerates **both** variants and **both** concept renders into a
temporary directory, never touching the working tree, and compares all thirteen
artefacts sitting in this directory — the committed ones, on a clean tree: nine SVGs and two PNGs by sha256, and the two HTML
specs by sha256 after normalising the `date.today()` stamp, which is the only difference
a second run may legitimately have. It prints an `OK` or `DRIFT` line per file and exits
non-zero on any drift, keeping the regenerated copies behind for diffing.

It locates the package from its own path, so it behaves the same from any working
directory — the check it replaces was invoked by hand, built its paths relative to `$PWD`,
and reported success from the wrong directory because the doubled prefix matched no files
at all. It refuses to report a pass on a run that compared fewer than thirteen files, and
it errors rather than passes if the date-stamp normaliser ever stops matching.

The PDFs are deliberately out of scope: Chrome stamps a creation date into every print, so
two prints of one HTML never match. Rebuild and read them by hand after any drift is
resolved. Chrome is found at the usual macOS path or on `$PATH`; override with `CHROME=`.

## Decisions log

- 2026-09-12 — v1.0 approved: 174 cm wide, wing columns with speaker caps, tray top at 63 cm, 20 cm foot and pedal recess, gear order turntable / XDJ / Xone:92 / XDJ.
- 2026-09-14 — v1.1 power niche between the drawers; v1.2 cable slot widened to 6 cm and optional pass-throughs into the drawers; v1.3 record capacity corrected to about 110; v1.4 accepted 110 in the wings; v1.5 wings widened to 20 cm each (185 cm overall, about 160 records), bay unchanged at 145; v1.6 speaker caps made flush with the columns (20 cm, no overhang; enough for KRK Rokit 5).
- 2026-09-14 — v2.0 flush-mounted gear: each unit sunk 9 cm into a 9 cm slab, faceplates flush. Envelope unchanged at 185 × 50 × 130. Back panel moved to the rear face to buy a 5 cm front rail and a 7 cm back rail; the freed band under the back rail becomes a continuous cable trough that also vents the Xone:92. Drawers 15.2 → 9.2. Book zone set back 15 cm for seated shin clearance (v2 only; v1's 43.2 cm interior cannot afford it without losing LP storage). Power bricks no longer stack on the strip — they stand on the niche floor beside it. No dust covers. v1.6 still generated with `VARIANT` unset.
- 2026-09-16 — v1.7 book zone set back 10 cm, the v2 shin fix brought back to v1: bay bottom panel, book divider and both adjustable shelves move back 10 cm from the front plane, which takes a seated player's shin clearance at the bottom panel's front edge (z 21.8) from about 1 cm to 11. The compartment lands on 33.2 deep — the same as v2 — and still takes a 31.4 cm LP sleeve with 1.8 to spare. v1 cannot take v2's 15 cm: it keeps the 5 cm cable chase, so its interior is 43.2 and a 15 cm setback would leave 28.2 and lose LP storage. Everything else in v1 is untouched; only the book zone and the version string move. Drawings: the bay bottom panel now reads as a ghost in the front elevation with a setback note, and the side section gains a 10 cm setback dimension. `render-cg.html` mirrors the setback, and `render-cg.png` was re-captured from it once the scene was seeded later the same day; the caveat that once stood here — a pre-setback capture from an unseeded scene that no re-render could reproduce — no longer applies.
- 2026-09-16 — cleanup pass, no geometry moved. `render-cg.html` seeds its PRNG from a constant, so both concept renders re-render byte-identically; both were re-captured against the current geometry and now sit in the drift check alongside the drawings. `generate.py` rejects any `VARIANT` other than 1 or 2 instead of silently falling back to v1, derives its drawing cross-references instead of hard-coding the numbers, and shares one stylesheet between the variants. `check-regen.sh` replaces the ad-hoc hash check that nobody was obliged to run and that reported success when run from the wrong directory. Shelf-pin setting-out disambiguated: with the book zone set back, “37 mm from the front edge” no longer named an edge, so the two rows are given from the compartment’s own faces and as absolute distances behind the console’s front face (v1 13.7 and 39.5, v2 18.7 and 44.5, 25.8 apart in both). Both PDFs rebuilt: v1 nine pages, v2 thirteen.
- 2026-09-28 — v2 cut list for quoting, no geometry moved. A new page after the parts list gives every piece of wood at its finished size, grouped by stock, with totals per stock: the per-well pieces are spelled out, and the drawer boxes are broken into panels at nominal size (the runner sets the final width). `cut_list_check()` asserts that a part in both lists has one count, size and thickness, and that the per-well pieces add up to the parts list. Building it corrected two parts-list rows and one quantity. The slab fascia is 50 mm thick, filling the 5 cm front rail as both sections draw it; the list said 60, which is its height. The drawer band divider blank is 48.2 × 11, notched down to 9.2; the list gave the notched height. The ply takes four 250 × 125 sheets, not three: every piece longer than half a sheet has to run with its grain along the sheet, no two of them fit end to end, and side by side they are 394.4 cm wide. `ply_sheets()` lays all 39 pieces on four sheets and asserts that no layout could use fewer. v1's materials note still says three sheets and has the same long panels; it was left as it was. The shared stylesheet gains one `.cut` rule, so v1 was regenerated too, with no change beyond the date stamp. Both PDFs rebuilt: v1 nine pages, v2 fifteen.
