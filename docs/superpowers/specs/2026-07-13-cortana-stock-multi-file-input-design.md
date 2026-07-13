# Cortana Stock: Multi-File Raw Export Ingestion — Design

## Context

Today, both the `cortana-stock` skill and the `cortana-stock-web` app take a single, already-cleaned, semicolon-delimited CSV with exactly 6 columns (Title, Option1 Value, SKU, Tienda Madrid, Tienda Palma, Tienda Barcelona).

Luca's stock export process is changing: the source system now produces multiple raw Shopify inventory export files per run (3 today, but the split could change). Inspection of 3 real sample files confirmed:

- Comma-delimited, UTF-8, no BOM, LF line endings — not the semicolon/BOM/CRLF format the pipeline expects today.
- ~29 columns each, all three files sharing an identical header, including many locations irrelevant to this tool (Barcelona Online, Almacén Huelva, Paris, several hotels, Production Warehouse, WHOLESALE B2B, Concept, Hotel Mandarin Oriental) alongside the 3 needed shop columns.
- Untracked-location cells contain the literal string `not stocked` rather than `0`.
- 26 of ~2,100 SKUs appeared in more than one file. All 26 had identical data (same title, size, and stock counts) in every occurrence — no observed conflicts, but the design must not assume this holds forever.

Luca wants this handled as a lasting feature (not a one-off cleanup) in both the web app and the skill, so either interface can take the raw files directly going forward.

## Goals

- Web app and skill both accept N raw export files (N ≥ 1 — flexible, not hardcoded to 3) instead of one pre-cleaned file.
- The combined/cleaned output is indistinguishable, to the existing `clean_input` / `compute_transfers` pipeline, from today's single pre-cleaned CSV — that pipeline is not modified.
- Real data problems (conflicting duplicates) are surfaced, not silently resolved.

## Non-goals

- No changes to redistribution rules, priorities, or receive caps.
- No "smart" reconciliation of conflicting stock values — conflicts are flagged, not auto-resolved.
- No fixed file-count validation (not locked to exactly 3).
- No reprocessing of the 3 sample files as part of this feature — Luca chose to build the durable feature rather than get a one-off run from them.

## Architecture

### New function: `combine_raw_exports`

A new, standalone stage that runs *before* the existing (untouched) `clean_input()` / `compute_transfers()` pipeline. Implemented twice, mirroring the existing pattern where `redistribute.py` already has a file-based skill version and a string-based web version.

**Skill** — new file `~/.claude/skills/cortana-stock/scripts/combine_exports.py`:

```python
def combine_raw_exports(paths: list[Path]) -> tuple[list[list[str]], dict]:
    ...
```

- Reads each file BOM-tolerant (`utf-8-sig`).
- Detects each file's delimiter independently: try `,` first (today's raw-export format), fall back to `;` (today's legacy pre-cleaned format), deciding by whether the resulting header row contains a column matching "madrid" (reusing `_find_column_index` from `redistribute.py`).
- Per file, locates the 6 canonical columns via the existing fuzzy header matching and projects the file down to just those — this is what drops all the irrelevant location columns, since only the 6 targets are ever selected.
- Replaces the literal value `not stocked` (case-insensitive, trimmed) with `0`, scoped to the 3 stock cells only.
- Concatenates all files' projected rows under one canonical header (taken from the first file).
- Returns `(combined_rows, stats)`. `stats` includes files processed, rows contributed per file, and duplicate-SKU diagnostics (see "Duplicate detection" below).
- A CLI wrapper (`main()`) writes `combined_rows` to an output CSV using today's output convention (`;`, UTF-8 BOM, CRLF), so the workflow becomes:
  ```
  python3 combine_exports.py f1.csv f2.csv f3.csv combined.csv
  python3 redistribute.py combined.csv
  ```
  matching the existing `redistribute.py` → `generate_shipments.py` two-stage pattern already documented in SKILL.md.

**Web app** — new file `cortana-stock-web/combine_exports.py`:

```python
def combine_raw_exports(csv_texts: list[str]) -> str:
    ...
```

Same logic, string-in/string-out (no filesystem), matching how the web variant of `redistribute.py` already works. Returns a single semicolon-delimited CSV string in the canonical 6-column shape. `app.js` fetches this file alongside `redistribute.py` at boot (a second `runPython` call) and exposes `combine_raw_exports` the same way `process_csv` is exposed today.

This gives the project a second pair of files (alongside `redistribute.py`'s existing skill/web pair) that must be kept in sync manually if the cleaning rules change later — same convention the `cortana-stock-web/README.md` already documents for `redistribute.py`.

### Duplicate detection: diagnostic only, no new merge/drop logic

Luca's read, confirmed during design review: these conflict cases realistically shouldn't occur, so the right amount of handling is the same amount the pipeline already gives every other anomaly (corrupt SKUs, negative stock, per SKILL.md) — never drop or auto-correct, just keep processing and warn. No new merge or drop logic is added for either case below; both already resolve exactly as they would today with zero new code:

- **Same SKU, same title/size, different stock** across files → `clean_input()`'s existing `(title, size, sku)` key already keeps only the first occurrence — unchanged. New: a warning surfaces that this happened ("N duplicate SKU(s) had conflicting stock values — kept the first file's numbers"), so it doesn't pass unnoticed.
- **Same SKU, different title or size** across files → `clean_input()`'s tuple key already treats these as distinct rows and lets both through — unchanged. New: a warning flags it ("N SKU(s) matched but title/size differed"), since this is otherwise invisible and worth a glance before trusting the output.
- **Same SKU, same title/size, same stock** across files → routine merge (first occurrence kept, as always), reported as an informational count only ("N duplicate SKU(s) merged").

The combine stage's only new responsibility here is a read-only diagnostic scan (keyed on SKU alone — a broader net than `clean_input`'s tuple key) that produces the counts and examples above for the UI. It does not influence what `clean_input` keeps or drops.

## UI changes (web app)

- `index.html` / `app.js`: file `<input>` gains `multiple`; drop zone and click-to-select accept any number of files.
- Selecting files shows "N file(s) selected" with the filenames listed (replacing today's single-filename display). "Clear" removes all.
- "Run redistribution" reads all selected files as text, calls `combine_raw_exports(texts)`, then passes the result into the existing `process_csv()` — everything downstream (summary, table, downloads) is unchanged.
- Summary grid: new tile "Files combined: N".
- Warnings panel: new cards for the three duplicate cases above, styled like today's corrupt-SKU / negative-stock warnings, each listing a few examples. The two escalated cases are visually distinguished from the routine "merged silently" case.

## Error handling

- A file missing a required column, even after fuzzy matching, raises an error naming that specific file and the missing column(s) — extending today's error message, which doesn't currently identify a source file since there's only ever one.
- A file where neither `,` nor `;` produces a recognizable header raises a clear per-file error.
- `not stocked` replacement is scoped to the 3 stock columns only, so it can never alter a title or SKU that happens to contain similar text.

## Testing

New `test_combine_exports.py` alongside the skill's existing `test_redistribute.py`, with fixtures trimmed from the 3 real sample files, covering:

- Column projection with the full set of extra columns present.
- `not stocked` → `0` replacement.
- Cross-file duplicates with identical data (routine merge).
- Cross-file duplicates with conflicting stock values (escalated warning).
- Cross-file SKU match with differing title/size (escalated warning, both rows retained).
- Missing-required-column error path, naming the offending file.

Existing `compute_transfers` / `clean_input` tests are untouched, since that logic isn't modified.
