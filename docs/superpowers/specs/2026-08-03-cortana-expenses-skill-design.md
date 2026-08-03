# Cortana Expense Reports: `cortana-expenses` Skill — Design

## Context

On 2026-08-03 Luca produced three expense reports for Katerina Marchenko from four photos of receipts laid out on a table. The photos held 29 receipt images: 23 real receipts plus 6 card slips that duplicated receipts already counted. They covered three Barcelona → Madrid work trips in July 2026 (7–10 July, 16 July, 24 July), totalling 275,32 €.

That run was ad hoc. Every step was done by hand in one session: read each receipt by eye (with contrast enhancement where thermal print had faded), match card slips to their receipts, group receipts into trips, fill `PLANTILLA GASTOS.xlsx`, and crop each receipt out of the table photos into per-trip folders. It worked, and it produced code worth keeping.

Katerina will send receipts again, so the process should be repeatable. Luca runs it from his CLI; Katerina does not. A self-service web app on GitHub Pages was considered and rejected — the reading step needs a vision model, and a public static page cannot hold an API key without either a proxy or asking Katerina to paste her own.

Facts established during the session that this skill must preserve:

- The template's data area is only 2 rows (8–9). Adding more rows means shifting the totals block below it **and** rewriting its formulas (`SUM(F8:F9)`, `+F10`, `+F13-F12`) to the new row numbers.
- openpyxl silently drops the template's `Tipo Gasto` dropdown, because it is an x14 `dataValidations` extension rather than a standard `dataValidation`. Filling the template therefore has to happen on the raw OOXML, not through openpyxl.
- Column E is `F` or `T` (factura vs ticket), per a cell comment attached to E7 — not a document number. Every receipt in the July batch was `T`; none carried Cortana's CIF as recipient.
- Style 20 on column B is `numFmtId="14"`, a date format, so dates must be written as Excel serial numbers, not strings.
- All food and restaurant spend goes under **Dietas**, never Relaciones Públicas. This is Luca's explicit rule (2026-08-03), including for a two-person tablao dinner that looked like client entertainment.
- Card slips carry only `Importe` plus card data and no line items. They must be excluded from totals but kept as backup.
- One taxi total was unreadable even after channel separation and contrast stretching. Luca supplied it manually. Guessing was never on the table.

## Goals

- One invocation turns a set of receipt photos into: one xlsx per trip, template-faithful, plus one folder of numbered ticket images per trip.
- Everything except reading the receipts is deterministic and unit-testable.
- Reading failures surface as a question to Luca, never as a guessed or estimated number.
- Employee name is a parameter, not hardcoded to Katerina — Cortana has other staff.

## Non-goals

- No web app, no self-service for Katerina. Explicitly rejected during design.
- No OCR library. Tesseract on faded, crumpled thermal paper was considered and rejected; reading is done by the model.
- No accounting-system integration and no email. The Cortana email policy is drafts-only anyway.
- No sourcing of AVE/train tickets. They were absent from the July photos; the skill reports their absence rather than inventing them.
- No Relaciones Públicas category, ever.
- No attempt to reconcile against card or bank statements.

## Architecture

Five stages. Stage 2 is the model; the other four are scripts under
`~/.claude/skills/cortana-expenses/scripts/`, following the layout `cortana-stock`
already uses (`SKILL.md` + `scripts/` + `test_*.py`).

Stages hand off through JSON files in a working directory, so any stage can be
re-run alone after a correction without redoing the ones before it.

### Stage 1 — `segment_receipts.py`

```
segment_receipts.py <photo>... --out <workdir>
```

Finds each receipt in each photo and crops it to its own JPEG.

The session's crop code used hand-measured boxes, which are worthless on the next
batch. What *is* reusable is the paper-vs-table discrimination underneath it: in
HSV, receipt paper is `V > 140 and S < 70`, and the oak table is not. So:

1. Build the paper mask for the photo.
2. Label connected components; discard any smaller than ~1.5% of the frame (kills highlights and specks).
3. For each surviving blob, take its bounding box, then apply the session's `autofit` — grow each edge outward while the perpendicular line stays ≥22% paper, capped at 80px per edge, then add a 12px margin. This recovers edges the mask under-detects on shadowed or curled paper.
4. Write `NN.jpg` per blob plus `segments.json`: `[{id, source_photo, box}]`.

Two known failure modes, both handled rather than assumed away:

- **Touching receipts merge into one blob.** Detected by aspect ratio and area against the batch median; flagged in `segments.json` as `suspect: "merged"` for the model to look at, since a merged crop is obvious on sight.
- **A bright plank seam between two receipts reads as paper**, which is what made autofit swallow a neighbour in the session. The 80px growth cap bounds the damage, and the clip check in Verification catches what survives.

Works unchanged on single-receipt photos — one blob instead of eight.

### Stage 2 — reading (the model, not a script)

For each crop, produce one record:

```json
{"id": 7, "date": "2026-07-09", "time": "08:30", "merchant": "Santagloria",
 "city": "Madrid", "total": 4.25, "doc": "receipt|card_slip",
 "ref": "factura simplificada nº", "category": "Dietas", "confidence": "high|low"}
```

`enhance.py <image> --box l,t,r,b --mode gray|channels` supports this stage. It
applies what actually worked in the session: crop, upscale with LANCZOS,
autocontrast, contrast stretch, unsharp mask, and — for the worst cases — per-channel
separation, since faded thermal print survives differently in R, G and B.

The model writes these records to `<workdir>/records.json`, carrying each crop's
`id` and file path through from `segments.json` so stages 3–5 can trace a row back
to its image.

Rules SKILL.md must encode, each one learned from a real receipt in the July batch:

- A **card slip** has an `Importe` and card data but no line items. It is not a receipt. Two slips (cliente + comercio copies) can exist for one transaction.
- A **factura proforma** total excludes suggested tip. Patio de Leones showed 62,50 € and 65,63 € with a 5% suggested tip; 62,50 € is the claim.
- A merchant's **fiscal address is not the venue**. "Gran Café Santander" is registered in Santander but was consumed in Madrid, provable from the timestamps either side of it.
- If a total cannot be read after enhancement, **stop and ask Luca**. Do not estimate from distance, duration, or comparable receipts. Write the row with a blank amount if the user wants to continue, and say so in the summary.
- Read the **date** off the receipt body, not the card slip, when they disagree.

**Categories.** Assigned from the template's `leyenda` sheet, which is the only
allowed vocabulary: Alojamiento, Material Oficina, Material Producción, Dietas,
Relaciones Públicas, Billete tren o avión, Alquiler de coche, Parking y peajes,
Taxi, Gasolina, Telefono, Otros.

| Receipt | Category |
|---|---|
| Any food or drink — café, restaurant, supermarket snacks, station kiosk | Dietas |
| Taxi (Madrid `A.P.C`, Barcelona `Servei Taxi`, or a taxi card slip) | Taxi |
| Hotel, hostal, apartamento | Alojamiento |
| AVE, Renfe, Iberia, Vueling, boarding pass | Billete tren o avión |
| Parking, peaje, aparcamiento | Parking y peajes |
| Gasolinera, Repsol, Cepsa | Gasolina |
| Anything else | Otros, and say so in the summary |

Relaciones Públicas is never assigned, even for a multi-person dinner with
alcohol. Column E is `T` unless the receipt names Cortana's CIF as recipient,
in which case `F`.

### Stage 3 — `group_trips.py`

```
group_trips.py <workdir>/records.json --out <workdir>/trips.json
```

Deterministic. Two jobs:

**Dedupe.** A card slip is matched to a receipt when the amounts are equal and the
timestamps are within 15 minutes. Matched slips are attached to their receipt as
`duplicate_of` rather than deleted. Slips that match nothing stay as unresolved
records and are reported — an unmatched slip means a missing receipt, which is
information, not noise. Two receipts with the same merchant, amount and document
number are the same receipt photographed twice; different document numbers mean
two real visits (Elcano appeared twice in two days, Fermento twice in a week).

**Trip splitting.** Sort by date; start a new trip when the gap to the previous
receipt is ≥2 days. On the July data this yields exactly 7–10 / 16 / 24 July.

The gap rule alone is not trustworthy — a week-long stay with one quiet day would
split in two. So `trips.json` records the travel markers that corroborate each
boundary (a Barcelona Sants receipt marks a departure, an Atocha one marks a
return leg) and **the model shows Luca the proposed grouping for confirmation
before stage 4 writes anything.**

### Stage 4 — `fill_template.py`

```
fill_template.py <workdir>/trips.json --employee "Katerina Marchenko" --out <dir> [--template <path>]
```

The session's OOXML editor, kept as-is because it is verified working. Per trip it
rebuilds `sheetData`: rows 1–7 from the template with D2 (employee), D3 (motivo) and
D4 (fecha) filled, N data rows, then the totals block with formulas re-pointed at
the new row numbers.

D2 must be **overwritten**, not left alone — the template ships with Katerina's name
already in it, which would silently mislabel another employee's report. Motivo
defaults to `Viaje de trabajo a <destination>`, where destination is the dominant
city outside Barcelona; `--motivo` overrides. Fecha is a single date for a one-day
trip and `dd/mm/yyyy - dd/mm/yyyy` for a longer one, written as text since the range
form is not a date value.

**Trip label**, used in both filenames and the summary, is
`<destination> <day(s)> <month in Spanish> <year>` — e.g. `Madrid 07-10 julio 2026`
or `Madrid 16 julio 2026`. It also extends the dropdown's `xm:sqref` from `C8:C9` to cover every data
row, updates `dimension`, drops `calcChain.xml` (plus its content-type override and
workbook relationship), and sets `fullCalcOnLoad="1"` so Excel recalculates on open.
Cached values are written alongside each formula so the numbers show before any
recalculation.

The template is vendored at `assets/PLANTILLA GASTOS.xlsx` so the skill is
self-contained; `--template` overrides it. `~/.claude/skills/` is not the public
`personal` repo, so vendoring it does not publish the Cortana logo.

### Stage 5 — `file_tickets.py`

```
file_tickets.py <workdir>/trips.json --out <dir>
```

Copies each crop to `Tickets <employee> - <trip label>/NN - <date> - <merchant> - <amount> EUR.jpg`,
numbered to match spreadsheet row order so the folder and the report read in the
same sequence. Card slips go to `duplicados/` inside their trip folder — kept, but
out of the numbered sequence that maps 1:1 to report rows.

## Output layout

```
~/Downloads/Gastos <employee> <month año>/
  GASTOS <employee> - <trip label>.xlsx        (one per trip)
  Tickets <employee> - <trip label>/
    01 - 2026-07-07 - CF Ave Sants - 9,40 EUR.jpg
    duplicados/
```

`--out` overrides. `~/Downloads` is the default because that is where the July run
landed and where Luca picks files up to forward.

## Verification

Every check below caught a real defect during the session, so all of them run on
every invocation and their results go in the summary:

- **Clip detection** — for each crop, the fraction of border pixels that are paper. Above 15% means the receipt may be cut off. This found 26 clipped crops on the first pass, including a Carrefour receipt missing its amounts column.
- **Contact sheet** — one strip per trip, all crops side by side with filenames, for a visual pass. This is what confirmed each crop holds one complete, correct receipt.
- **Totals cross-check** — row sum equals the cached `SUM`, equals the per-category totals, equals the reported trip total.
- **Count reconciliation** — unique receipts + duplicates equals blobs segmented. A mismatch means a receipt was dropped or double-counted.
- **Excel-open check** — reload each output and assert it survived intact. Values, dates and formula targets come from openpyxl; the dropdown, logo and comments must be checked by reading the sheet XML and file list straight out of the zip, because openpyxl cannot see the x14 dropdown extension at all. Checking it through openpyxl would report a missing dropdown on a perfectly good file.

## Testing

Unit tests beside the scripts, matching the `test_*.py` convention in `cortana-stock`:

- `test_group_trips.py` — card slip matched to its receipt; two slips for one transaction; unmatched slip reported not dropped; same merchant twice in one day with different document numbers kept as two; trip boundaries on the real July dates; a 1-day gap not splitting.
- `test_fill_template.py` — N data rows produce `SUM(F8:F{7+N})` with the totals block at the right offsets; dropdown `sqref` spans the data rows; dates land as serials with numFmt 14; a blank amount leaves the SUM valid; a non-Katerina `--employee` replaces D2 rather than inheriting the template's name.
- `test_segment_receipts.py` — a synthetic photo with three known paper rectangles on a wood-toned background yields three boxes within tolerance; a merged pair is flagged `suspect`.

## Open questions

None blocking. Two defaults chosen rather than asked, both easy to change later:
`~/Downloads` as the output root, and 2 days as the trip-gap threshold — with the
grouping shown for confirmation before any file is written, which is the real
safeguard against the threshold being wrong.
