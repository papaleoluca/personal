# Cortana Stock Multi-File Input Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let both the `cortana-stock` skill and the `cortana-stock-web` app accept multiple raw Shopify inventory export files (instead of one pre-cleaned CSV) by adding a new combine-and-clean stage that runs before the existing, unmodified redistribution pipeline.

**Architecture:** A new `combine_exports.py` file in each location (skill: file-based CLI; web: string-based Pyodide module) detects each input file's delimiter, projects it down to the 6 canonical columns, normalizes `not stocked` → `0`, and concatenates everything under one header. The existing `clean_input()` / `compute_transfers()` pipeline in `redistribute.py` (both variants) is untouched — it already does the right thing with the combined output. A diagnostic pass flags (but never auto-resolves) cross-file duplicate SKUs.

**Tech Stack:** Python 3 stdlib only (`csv`, `io`, `pathlib`) for the skill; Pyodide v0.26.4 + vanilla JS for the web app. No new dependencies.

## Global Constraints

- File count is flexible: 1 or more input files, never hardcoded to exactly 3.
- Both the skill (`~/.claude/skills/cortana-stock/`) and the web app (`cortana-stock-web/`) get this capability — not just one.
- `redistribute.py`'s existing logic (`compute_transfers`, `clean_input`) is not modified in either variant.
- Output CSV convention is unchanged: `;` delimiter, UTF-8 BOM, CRLF line endings.
- `not stocked` matching is case-insensitive and whitespace-trimmed, scoped to only the Madrid/Palma/Barcelona stock columns.
- Duplicate SKUs across files are never auto-merged or silently resolved beyond what `clean_input()` already does (first-occurrence-by-title+size+SKU) — new behavior here is diagnostic warnings only, matching the existing "always process, just warn" precedent used for corrupt SKUs and negative stock (SKILL.md).
- Test fixtures must be small and synthetic, never Luca's real inventory files — `cortana-stock-web/` is served publicly via GitHub Pages from this repo's `main` branch, and the skill's real export files must never be committed anywhere.
- `~/.claude/skills/cortana-stock/` is **not** a git repository — tasks there end by saving files in place, not committing. `cortana-stock-web/` lives inside the `personal` git repo and every task there ends with a commit.

---

### Task 1: Skill — `combine_exports.py` core logic + tests

**Files:**
- Create: `~/.claude/skills/cortana-stock/scripts/combine_exports.py`
- Create: `~/.claude/skills/cortana-stock/scripts/test_combine_exports.py`

**Interfaces:**
- Produces: `combine_raw_exports(file_texts: list[tuple[str, str]]) -> tuple[header: list[str], rows: list[list[str]], stats: dict]`, where `stats = {"files": [{"filename": str, "rows": int}, ...], "identical_duplicate_skus": list[str], "conflicting_duplicate_skus": list[str], "mismatched_duplicate_skus": list[str]}`. `rows` are 6-wide: `[title, size, sku, madrid, palma, barcelona]`.
- Produces: `project_file(raw_text: str, filename: str) -> tuple[header: list[str], rows: list[list[str]]]` — used directly by tests.
- Produces: `detect_delimiter(raw_text: str) -> str` — returns `","` or `";"`.
- CLI: `python3 combine_exports.py <file1.csv> [file2.csv ...] <output.csv>` — last arg is always the output path.

No other task depends on this task's Python objects directly (Task 3 is a separate, self-contained port, not an import of this file).

- [ ] **Step 1: Write the failing test file**

Create `~/.claude/skills/cortana-stock/scripts/test_combine_exports.py`:

```python
#!/usr/bin/env python3
"""Tests for combine_exports.py. Run after any change to combine_exports.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from combine_exports import combine_raw_exports, detect_delimiter, project_file


RAW_HEADER = (
    "Handle,Title,Option1 Name,Option1 Value,SKU,COO,"
    "Barcelona Online,Tienda Madrid,Tienda Palma de Mallorca,Tienda Barcelona,Paris"
)


def make_raw_csv(rows):
    """
    rows: list of (title, size, sku, madrid, palma, barcelona) tuples.

    Mirrors the real Shopify export shape: "Option1 Name" sits before
    "Option1 Value" (both contain "option1"), and "Barcelona Online" sits
    before "Tienda Barcelona" (both contain "barcelona") -- the two
    ambiguous cases the column locator must resolve correctly. Barcelona
    Online is always given a different, fixed stock number (999) so a
    wrong column pick is easy to catch in assertions.
    """
    lines = [RAW_HEADER]
    for title, size, sku, m, p, b in rows:
        lines.append(f"h-{sku},{title},Talla,{size},{sku},ES,999,{m},{p},{b},0")
    return "\n".join(lines) + "\n"


def check(condition, label):
    assert condition, f"FAIL: {label}"
    print(f"OK: {label}")


def test_detect_delimiter_comma():
    text = make_raw_csv([("A", "40", "SKU1", "1", "2", "3")])
    check(detect_delimiter(text) == ",", "detect_delimiter: comma raw export")


def test_detect_delimiter_semicolon():
    text = "Title;Option1 Value;SKU;Tienda Madrid;Tienda Palma;Tienda Barcelona\nA;40;SKU1;1;2;3\n"
    check(detect_delimiter(text) == ";", "detect_delimiter: semicolon pre-cleaned file")


def test_detect_delimiter_failure():
    text = "Foo;Bar;Baz\n1;2;3\n"
    try:
        detect_delimiter(text)
        check(False, "detect_delimiter: should have raised when no 'madrid' column exists")
    except ValueError:
        check(True, "detect_delimiter: raises when neither delimiter finds a 'madrid' column")


def test_project_file_resolves_ambiguous_columns():
    text = make_raw_csv([("Ryo pantalon", "40", "SKU1", "1", "2", "3")])
    header, rows = project_file(text, "f1.csv")
    check(
        header == ["Title", "Option1 Value", "SKU", "Tienda Madrid", "Tienda Palma de Mallorca", "Tienda Barcelona"],
        "project_file: canonical header, extra columns dropped",
    )
    check(
        rows == [["Ryo pantalon", "40", "SKU1", "1", "2", "3"]],
        "project_file: picks 'Option1 Value' (40) not 'Option1 Name' (Talla), "
        "and 'Tienda Barcelona' (3) not 'Barcelona Online' (999)",
    )


def test_project_file_replaces_not_stocked():
    text = make_raw_csv([("Thalo bracelet", "S", "SKU2", "not stocked", "0", "0")])
    _, rows = project_file(text, "f1.csv")
    check(rows == [["Thalo bracelet", "S", "SKU2", "0", "0", "0"]],
          "project_file: 'not stocked' replaced with 0")


def test_combine_merges_identical_duplicate():
    f1 = make_raw_csv([("A", "40", "SKU1", "1", "1", "1")])
    f2 = make_raw_csv([("A", "40", "SKU1", "1", "1", "1")])
    _, rows, stats = combine_raw_exports([("f1.csv", f1), ("f2.csv", f2)])
    check(len(rows) == 2, "combine: both rows kept pre-dedup (clean_input dedupes later)")
    check(stats["identical_duplicate_skus"] == ["SKU1"], "combine: identical duplicate flagged")
    check(stats["conflicting_duplicate_skus"] == [], "combine: no conflicting duplicates")
    check(stats["mismatched_duplicate_skus"] == [], "combine: no mismatched duplicates")


def test_combine_flags_conflicting_stock():
    f1 = make_raw_csv([("A", "40", "SKU1", "1", "1", "1")])
    f2 = make_raw_csv([("A", "40", "SKU1", "2", "1", "1")])
    _, _, stats = combine_raw_exports([("f1.csv", f1), ("f2.csv", f2)])
    check(stats["conflicting_duplicate_skus"] == ["SKU1"], "combine: conflicting stock flagged")


def test_combine_flags_mismatched_title():
    f1 = make_raw_csv([("A", "40", "SKU1", "1", "1", "1")])
    f2 = make_raw_csv([("B", "42", "SKU1", "1", "1", "1")])
    _, _, stats = combine_raw_exports([("f1.csv", f1), ("f2.csv", f2)])
    check(stats["mismatched_duplicate_skus"] == ["SKU1"], "combine: title/size mismatch flagged")


def test_combine_missing_column_error():
    bad_text = "Title,SKU,Tienda Madrid\nA,SKU1,1\n"
    try:
        combine_raw_exports([("bad.csv", bad_text)])
        check(False, "combine: should have raised on missing columns")
    except ValueError as e:
        check("bad.csv" in str(e), "combine: error names the offending file")


def test_combine_single_file_passthrough():
    text = make_raw_csv([("A", "40", "SKU1", "1", "1", "1")])
    header, rows, stats = combine_raw_exports([("only.csv", text)])
    check(len(rows) == 1 and stats["files"] == [{"filename": "only.csv", "rows": 1}],
          "combine: works with a single file (flexible file count)")


def main():
    test_detect_delimiter_comma()
    test_detect_delimiter_semicolon()
    test_detect_delimiter_failure()
    test_project_file_resolves_ambiguous_columns()
    test_project_file_replaces_not_stocked()
    test_combine_merges_identical_duplicate()
    test_combine_flags_conflicting_stock()
    test_combine_flags_mismatched_title()
    test_combine_missing_column_error()
    test_combine_single_file_passthrough()
    print("\nAll tests passed!")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 ~/.claude/skills/cortana-stock/scripts/test_combine_exports.py`
Expected: `ModuleNotFoundError: No module named 'combine_exports'`

- [ ] **Step 3: Write the implementation**

Create `~/.claude/skills/cortana-stock/scripts/combine_exports.py`:

```python
#!/usr/bin/env python3
"""
Combine multiple raw Cortana stock export files into one cleaned CSV in the
format redistribute.py expects.

Usage:
    python3 combine_exports.py <file1.csv> [file2.csv ...] <output.csv>

The last argument is always the output path; every argument before it is
an input file (any count >= 1). Handles Shopify-style raw exports:
comma-delimited, ~29 columns including many locations irrelevant to this
tool (Barcelona Online, hotels, wholesale, etc.), and "not stocked" cells
for untracked locations. Also accepts today's semicolon-delimited
pre-cleaned format, so a single already-clean file still works unchanged.

Preprocessing, per file:
1. Detect the delimiter (comma or semicolon).
2. Locate the 6 required columns by header name. Raw Shopify exports have
   ambiguous columns that a naive first-match substring search would get
   wrong -- "Option1 Name" sits before "Option1 Value" (both contain
   "option1"), and "Barcelona Online" sits before "Tienda Barcelona"
   (both contain "barcelona"). _locate_column tries each pattern across
   the WHOLE header before falling back to the next, broader pattern, so
   "option1 value" and "tienda barcelona" win over their ambiguous
   neighbors.
3. Project the file down to just those 6 columns -- this is what drops
   every irrelevant column.
4. Replace the literal cell value "not stocked" (case-insensitive,
   trimmed) with "0", scoped to the 3 stock columns only.

Then all files' projected rows are concatenated under one header (from
the first file).

This does NOT deduplicate SKUs -- that's still redistribute.py's
clean_input() job, unchanged, once the combined file reaches it. This
script only reports duplicate-SKU diagnostics (see combine_raw_exports()'s
returned stats) so the caller can warn about them; it does not decide
what gets kept.
"""

import csv
import io
import sys
from pathlib import Path


STOCK_COLUMN_KEYS = ("madrid", "palma", "barcelona")
NOT_STOCKED_VALUE = "not stocked"


def _locate_column(header, *patterns):
    """
    Return the index of the header cell matching the first pattern that
    matches ANY cell, trying patterns in order across the whole header
    before falling back to the next (broader) pattern. Needed because a
    simple first-matching-cell scan would let a broader later pattern
    match an earlier, wrong column (see module docstring).
    """
    for pat in patterns:
        pat_lower = pat.lower()
        for i, h in enumerate(header):
            if pat_lower in h.strip().lower():
                return i
    return -1


def _parse_rows(raw_text, delimiter):
    reader = csv.reader(io.StringIO(raw_text), delimiter=delimiter)
    return list(reader)


def detect_delimiter(raw_text):
    """Return ',' or ';', whichever produces a header with a 'madrid' column."""
    for delimiter in (",", ";"):
        rows = _parse_rows(raw_text, delimiter)
        if not rows or len(rows[0]) < 2:
            continue
        if _locate_column(rows[0], "madrid") != -1:
            return delimiter
    raise ValueError("Could not detect delimiter: no column matching 'madrid' found with ',' or ';'")


def _locate_columns(header, filename):
    cols = {
        "title": _locate_column(header, "title"),
        "size": _locate_column(header, "option1 value", "talla", "size"),
        "sku": _locate_column(header, "sku"),
        "madrid": _locate_column(header, "tienda madrid", "madrid"),
        "palma": _locate_column(header, "tienda palma", "palma"),
        "barcelona": _locate_column(header, "tienda barcelona", "barcelona"),
    }
    missing = [k for k, v in cols.items() if v == -1]
    if missing:
        raise ValueError(
            f"{filename}: missing required column(s): {missing}. Got header: {header}"
        )
    return cols


def _normalize_stock(value):
    if value.strip().lower() == NOT_STOCKED_VALUE:
        return "0"
    return value


def project_file(raw_text, filename):
    """
    Parse one raw export file's text and return (header, rows) trimmed to
    the 6 canonical columns, with "not stocked" replaced by "0" in the 3
    stock columns. `filename` is used only for error messages.
    """
    delimiter = detect_delimiter(raw_text)
    parsed = _parse_rows(raw_text, delimiter)
    header = parsed[0]
    cols = _locate_columns(header, filename)
    order = ("title", "size", "sku", "madrid", "palma", "barcelona")
    canonical_header = [header[cols[k]] for k in order]

    max_idx = max(cols.values())
    rows = []
    for row in parsed[1:]:
        if len(row) <= max_idx:
            continue
        projected = [row[cols[k]] for k in order]
        for i, k in enumerate(order):
            if k in STOCK_COLUMN_KEYS:
                projected[i] = _normalize_stock(projected[i])
        rows.append(projected)

    return canonical_header, rows


def diagnose_duplicates(all_rows):
    """
    Scan combined rows (each [title, size, sku, m, p, b]) for duplicate
    SKUs across the input files (SKU alone -- a broader net than
    redistribute.py's (title, size, sku) dedup key). Returns a stats dict;
    does not modify or drop anything -- clean_input() still owns dedup.
    """
    by_sku = {}
    for row in all_rows:
        by_sku.setdefault(row[2], []).append(row)

    identical, conflicting, mismatched = [], [], []
    for sku, rows in by_sku.items():
        if len(rows) < 2:
            continue
        titles_sizes = {(r[0], r[1]) for r in rows}
        stocks = {(r[3], r[4], r[5]) for r in rows}
        if len(titles_sizes) > 1:
            mismatched.append(sku)
        elif len(stocks) > 1:
            conflicting.append(sku)
        else:
            identical.append(sku)

    return {
        "identical_duplicate_skus": identical,
        "conflicting_duplicate_skus": conflicting,
        "mismatched_duplicate_skus": mismatched,
    }


def combine_raw_exports(file_texts):
    """
    file_texts: list of (filename, raw_text) tuples, one per input file
    (any count >= 1).

    Returns (header, rows, stats):
      header: list[str] -- canonical 6-column header (from the first file)
      rows:   list[list[str]] -- concatenated, projected, normalized rows
      stats:  dict with "files" (per-file row counts) and the 3 duplicate
              categories from diagnose_duplicates().
    """
    if not file_texts:
        raise ValueError("combine_raw_exports requires at least one file")

    header = None
    all_rows = []
    file_stats = []
    for filename, raw_text in file_texts:
        file_header, rows = project_file(raw_text, filename)
        if header is None:
            header = file_header
        all_rows.extend(rows)
        file_stats.append({"filename": filename, "rows": len(rows)})

    stats = {"files": file_stats}
    stats.update(diagnose_duplicates(all_rows))
    return header, all_rows, stats


def _rows_to_csv_text(header, rows):
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", lineterminator="\r\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buf.getvalue()


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        sys.exit(1)

    *input_args, output_arg = argv[1:]
    input_paths = [Path(p).expanduser() for p in input_args]
    output_path = Path(output_arg).expanduser()

    for p in input_paths:
        if not p.exists():
            print(f"Input not found: {p}", file=sys.stderr)
            sys.exit(1)

    file_texts = []
    for p in input_paths:
        with open(p, "r", encoding="utf-8-sig", newline="") as f:
            file_texts.append((p.name, f.read()))

    header, rows, stats = combine_raw_exports(file_texts)

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(_rows_to_csv_text(header, rows))

    print(f"Combined {len(input_paths)} file(s) into {len(rows)} rows -> {output_path}")
    for fs in stats["files"]:
        print(f"  {fs['filename']}: {fs['rows']} rows")

    if stats["identical_duplicate_skus"]:
        n = len(stats["identical_duplicate_skus"])
        print(f"\n{n} duplicate SKU(s) will be merged automatically when you run redistribute.py (identical data across files).")

    if stats["conflicting_duplicate_skus"]:
        n = len(stats["conflicting_duplicate_skus"])
        sample = ", ".join(stats["conflicting_duplicate_skus"][:5])
        print(f"\n!! WARNING: {n} duplicate SKU(s) had conflicting stock values across files: {sample}")
        print("   redistribute.py will keep the first file's numbers for each -- verify these are correct.")

    if stats["mismatched_duplicate_skus"]:
        n = len(stats["mismatched_duplicate_skus"])
        sample = ", ".join(stats["mismatched_duplicate_skus"][:5])
        print(f"\n!! WARNING: {n} SKU(s) matched across files but title/size differed: {sample}")
        print("   Both rows were kept as distinct entries -- verify this is correct.")

    print(f"\nNext: python3 redistribute.py \"{output_path}\"")


if __name__ == "__main__":
    main(sys.argv)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 ~/.claude/skills/cortana-stock/scripts/test_combine_exports.py`
Expected: 10 `OK: ...` lines followed by `All tests passed!`

Not a git repo — nothing to commit. The two files being saved in `~/.claude/skills/cortana-stock/scripts/` is the deliverable for this task.

---

### Task 2: Skill — SKILL.md documentation

**Files:**
- Modify: `~/.claude/skills/cortana-stock/SKILL.md`

**Interfaces:**
- Consumes: nothing code-level; describes Task 1's `combine_exports.py` CLI usage.

- [ ] **Step 1: Insert a new "Raw multi-file input" section**

In `~/.claude/skills/cortana-stock/SKILL.md`, insert this new section immediately after the existing "## Input format" table and before the existing "## Preprocessing (always run before redistribution)" heading (i.e., right after the line `| Tienda Barcelona | \`barcelona\` |` and its blank line):

```markdown
## Raw multi-file input (Shopify exports)

The stock export process can also hand over multiple raw Shopify inventory
export files instead of one pre-cleaned CSV. These look different from the
format above:

- Comma-delimited (not semicolon), no BOM, LF line endings.
- ~29 columns, including many locations irrelevant to this tool (e.g.
  `Barcelona Online`, `Almacén Huelva`, `Paris`, several hotels,
  `Production Warehouse`, `WHOLESALE B2B`, `Concept`).
- Untracked-location cells contain the literal text `not stocked` instead
  of `0`.
- The same SKU can appear in more than one file.

Run `combine_exports.py` first to turn any number (1 or more) of these raw
files into the single cleaned CSV the rest of this skill expects:

```bash
python3 ~/.claude/skills/cortana-stock/scripts/combine_exports.py "<file1.csv>" "<file2.csv>" "<file3.csv>" "<combined.csv>"
```

The last argument is always the output path; every argument before it is
an input file. It:

1. Detects each file's delimiter (comma or semicolon).
2. Locates the 6 required columns by header name. Raw Shopify exports have
   ambiguous columns that a naive first-match search gets wrong —
   `Option1 Name` sits before `Option1 Value` (both contain "option1"),
   and `Barcelona Online` sits before `Tienda Barcelona` (both contain
   "barcelona"). The script tries the precise pattern (`option1 value`,
   `tienda barcelona`, etc.) across the whole header before falling back
   to a broader one, so it picks the right column.
3. Projects each file down to just those 6 columns, dropping everything
   else.
4. Replaces `not stocked` (case-insensitive, trimmed) with `0`, only in
   the 3 stock columns.
5. Concatenates all files' rows under one header.

It does **not** deduplicate SKUs itself — that's still this skill's normal
job (see Preprocessing below), unchanged. It only reports duplicate-SKU
diagnostics so you can warn the user about them:

- Same SKU, same title/size, same stock across files → routine, silently
  merged like any other duplicate.
- Same SKU, same title/size, **different stock** across files → flagged;
  the first file's numbers are kept.
- Same SKU, **different title or size** across files → flagged; both rows
  are kept as distinct entries (today's dedup key is title+size+SKU, so
  these don't collide) — worth a second look since it usually means one
  export has stale data.

Then run the normal pipeline on the combined file:

```bash
python3 ~/.claude/skills/cortana-stock/scripts/combine_exports.py f1.csv f2.csv f3.csv combined.csv
python3 ~/.claude/skills/cortana-stock/scripts/redistribute.py combined.csv
```
```

- [ ] **Step 2: Add a forward-reference in "How to run"**

In the same file, find this line under "## How to run":

```
The bundled script handles everything. Default behavior: write `<input>(out).csv` next to the input AND three per-shop shipment sheets.
```

Replace it with:

```
The bundled script handles everything. Default behavior: write `<input>(out).csv` next to the input AND three per-shop shipment sheets.

If you're starting from raw Shopify export files instead of one pre-cleaned CSV, run `combine_exports.py` first (see "Raw multi-file input" above) to produce a single input file for this script.
```

- [ ] **Step 3: Re-read the file to confirm both edits render correctly**

Read `~/.claude/skills/cortana-stock/SKILL.md` and confirm: the new section sits between "Input format" and "Preprocessing", headings are well-formed, and the "How to run" addition reads naturally.

Not a git repo — nothing to commit.

---

### Task 3: Web app — `combine_exports.py` (Pyodide port)

**Files:**
- Create: `/Users/lucapapaleo/Desktop/claude/personal/cortana-stock-web/combine_exports.py`

**Interfaces:**
- Produces: `combine_raw_exports_web(filenames: list[str], csv_texts: list[str]) -> dict` with keys `"csv_text"` (str, semicolon-delimited combined CSV) and `"stats"` (same shape as Task 1's `combine_raw_exports` stats).
- Consumes: nothing from Task 1 or from `redistribute.py` — fully self-contained, matching how `cortana-stock-web/redistribute.py` is already a standalone port rather than an import of the skill's version. (Do not import between the two `combine_exports.py` files, and do not name-collide with anything `redistribute.py` defines — Task 4 loads both files into the same Pyodide global namespace, so a same-named function in both would silently overwrite one.)
- Consumed by: Task 4's `app.js`, via `pyodide.globals.get("combine_raw_exports_web")`.

- [ ] **Step 1: Write the file**

Create `/Users/lucapapaleo/Desktop/claude/personal/cortana-stock-web/combine_exports.py`:

```python
"""
Cortana stock export combining — Pyodide-compatible version.

Derived from ~/.claude/skills/cortana-stock/scripts/combine_exports.py.
This version operates entirely on strings (no filesystem access) so it can
run in Pyodide inside the browser. If you change the rules in one place,
sync the other.

Public entry point: combine_raw_exports_web(filenames, csv_texts) -> dict
with the combined CSV text and a stats block.
"""

import csv
import io


STOCK_COLUMN_KEYS = ("madrid", "palma", "barcelona")
NOT_STOCKED_VALUE = "not stocked"


def _locate_column(header, *patterns):
    """
    Return the index of the header cell matching the first pattern that
    matches ANY cell, trying patterns in order across the whole header
    before falling back to the next (broader) pattern. Needed because a
    simple first-matching-cell scan would let a broader later pattern
    match an earlier, wrong column -- e.g. raw Shopify exports have
    "Barcelona Online" before "Tienda Barcelona" (both contain
    "barcelona"), and "Option1 Name" before "Option1 Value" (both contain
    "option1").
    """
    for pat in patterns:
        pat_lower = pat.lower()
        for i, h in enumerate(header):
            if pat_lower in h.strip().lower():
                return i
    return -1


def _parse_rows(raw_text, delimiter):
    reader = csv.reader(io.StringIO(raw_text), delimiter=delimiter)
    return list(reader)


def detect_delimiter(raw_text):
    for delimiter in (",", ";"):
        rows = _parse_rows(raw_text, delimiter)
        if not rows or len(rows[0]) < 2:
            continue
        if _locate_column(rows[0], "madrid") != -1:
            return delimiter
    raise ValueError("Could not detect delimiter: no column matching 'madrid' found with ',' or ';'")


def _locate_columns(header, filename):
    cols = {
        "title": _locate_column(header, "title"),
        "size": _locate_column(header, "option1 value", "talla", "size"),
        "sku": _locate_column(header, "sku"),
        "madrid": _locate_column(header, "tienda madrid", "madrid"),
        "palma": _locate_column(header, "tienda palma", "palma"),
        "barcelona": _locate_column(header, "tienda barcelona", "barcelona"),
    }
    missing = [k for k, v in cols.items() if v == -1]
    if missing:
        raise ValueError(
            f"{filename}: missing required column(s): {missing}. Got header: {header}"
        )
    return cols


def _normalize_stock(value):
    if value.strip().lower() == NOT_STOCKED_VALUE:
        return "0"
    return value


def project_file(raw_text, filename):
    if raw_text.startswith("﻿"):
        raw_text = raw_text[1:]
    delimiter = detect_delimiter(raw_text)
    parsed = _parse_rows(raw_text, delimiter)
    header = parsed[0]
    cols = _locate_columns(header, filename)
    order = ("title", "size", "sku", "madrid", "palma", "barcelona")
    canonical_header = [header[cols[k]] for k in order]

    max_idx = max(cols.values())
    rows = []
    for row in parsed[1:]:
        if len(row) <= max_idx:
            continue
        projected = [row[cols[k]] for k in order]
        for i, k in enumerate(order):
            if k in STOCK_COLUMN_KEYS:
                projected[i] = _normalize_stock(projected[i])
        rows.append(projected)

    return canonical_header, rows


def diagnose_duplicates(all_rows):
    by_sku = {}
    for row in all_rows:
        by_sku.setdefault(row[2], []).append(row)

    identical, conflicting, mismatched = [], [], []
    for sku, rows in by_sku.items():
        if len(rows) < 2:
            continue
        titles_sizes = {(r[0], r[1]) for r in rows}
        stocks = {(r[3], r[4], r[5]) for r in rows}
        if len(titles_sizes) > 1:
            mismatched.append(sku)
        elif len(stocks) > 1:
            conflicting.append(sku)
        else:
            identical.append(sku)

    return {
        "identical_duplicate_skus": identical,
        "conflicting_duplicate_skus": conflicting,
        "mismatched_duplicate_skus": mismatched,
    }


def combine_raw_exports(file_texts):
    if not file_texts:
        raise ValueError("combine_raw_exports requires at least one file")

    header = None
    all_rows = []
    file_stats = []
    for filename, raw_text in file_texts:
        file_header, rows = project_file(raw_text, filename)
        if header is None:
            header = file_header
        all_rows.extend(rows)
        file_stats.append({"filename": filename, "rows": len(rows)})

    stats = {"files": file_stats}
    stats.update(diagnose_duplicates(all_rows))
    return header, all_rows, stats


def _rows_to_csv_text(header, rows):
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", lineterminator="\r\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buf.getvalue()


def combine_raw_exports_web(filenames, csv_texts):
    file_texts = list(zip(filenames, csv_texts))
    header, rows, stats = combine_raw_exports(file_texts)
    return {"csv_text": _rows_to_csv_text(header, rows), "stats": stats}
```

- [ ] **Step 2: Manual parity sanity check (plain CPython, no browser needed)**

This file has no Pyodide-specific syntax, so it runs directly under regular Python. Run this from `/Users/lucapapaleo/Desktop/claude/personal/cortana-stock-web/`:

```bash
python3 -c "
from combine_exports import combine_raw_exports

f1 = 'Title,Option1 Name,Option1 Value,SKU,Barcelona Online,Tienda Madrid,Tienda Palma,Tienda Barcelona\n' \
     'Ryo pantalon,Talla,40,SKU1,999,not stocked,2,3\n'
f2 = 'Title,Option1 Name,Option1 Value,SKU,Barcelona Online,Tienda Madrid,Tienda Palma,Tienda Barcelona\n' \
     'Ryo pantalon,Talla,40,SKU1,999,not stocked,2,3\n'

header, rows, stats = combine_raw_exports([('f1.csv', f1), ('f2.csv', f2)])
assert rows == [['Ryo pantalon', '40', 'SKU1', '0', '2', '3'], ['Ryo pantalon', '40', 'SKU1', '0', '2', '3']], rows
assert stats['identical_duplicate_skus'] == ['SKU1'], stats
print('OK: web combine_exports.py matches skill behavior')
"
```

Expected: `OK: web combine_exports.py matches skill behavior`

- [ ] **Step 3: Commit**

```bash
cd /Users/lucapapaleo/Desktop/claude/personal
git add cortana-stock-web/combine_exports.py
git commit -m "$(cat <<'EOF'
Add combine_exports.py to cortana-stock-web

Ports the skill's raw-export combining logic (comma-delimited Shopify
exports, not-stocked normalization, duplicate-SKU diagnostics) to a
Pyodide-compatible, string-based module.
EOF
)"
```

---

### Task 4: Web app — multi-file UI wiring

**Files:**
- Modify: `/Users/lucapapaleo/Desktop/claude/personal/cortana-stock-web/index.html`
- Modify: `/Users/lucapapaleo/Desktop/claude/personal/cortana-stock-web/app.js`

**Interfaces:**
- Consumes: `combine_raw_exports_web(filenames, csv_texts) -> {"csv_text": str, "stats": {...}}` from Task 3 (loaded into Pyodide as a global function).
- Consumes: `process_csv(csv_text) -> {...}` from the existing `redistribute.py` (unchanged).

- [ ] **Step 1: Edit `index.html` — accept multiple files, update copy, add a CSS variant for informational warnings**

In `index.html`, replace the subtitle line:

```html
      <p class="subtitle">Upload the weekly stock CSV to compute inter-shop transfers across Madrid, Palma, and Barcelona.</p>
```

with:

```html
      <p class="subtitle">Upload one or more weekly stock export files to compute inter-shop transfers across Madrid, Palma, and Barcelona.</p>
```

Replace the drop-zone block:

```html
      <label class="drop-zone" id="drop-zone">
        <input type="file" id="file-input" accept=".csv,text/csv" />
        <div class="drop-zone-icon">CSV</div>
        <p class="drop-zone-text" id="drop-zone-text">Drop the stock CSV here or click to select</p>
        <p class="drop-zone-hint">Semicolon-delimited. Needs columns for Title, SKU, Madrid, Palma, Barcelona.</p>
      </label>
```

with:

```html
      <label class="drop-zone" id="drop-zone">
        <input type="file" id="file-input" accept=".csv,text/csv" multiple />
        <div class="drop-zone-icon">CSV</div>
        <p class="drop-zone-text" id="drop-zone-text">Drop one or more stock export files here or click to select</p>
        <p class="drop-zone-hint">Comma or semicolon-delimited. Needs columns for Title, SKU, and the Madrid/Palma/Barcelona stock columns — any other columns are ignored.</p>
      </label>
```

In the `<style>` block, find:

```css
    .warnings ul {
      margin: 4px 0 0;
      padding-left: 20px;
    }
```

and add this new rule immediately after it:

```css
    .warnings ul {
      margin: 4px 0 0;
      padding-left: 20px;
    }

    .warnings.info {
      background: #eff6ff;
      border-color: #bfdbfe;
      color: #1e40af;
    }
```

- [ ] **Step 2: Edit `app.js` — multi-file state, combine step, new summary/warnings**

Replace the state object:

```javascript
const state = {
  pyodide: null,
  processFn: null,
  file: null,
  result: null,
};
```

with:

```javascript
const state = {
  pyodide: null,
  processFn: null,
  combineFn: null,
  files: [],
  result: null,
};
```

Replace `bootPyodide`:

```javascript
async function bootPyodide() {
  try {
    setStatus("Loading Python runtime…", true);
    state.pyodide = await loadPyodide();
    setStatus("Loading redistribution logic…", true);
    const pySource = await fetch("./redistribute.py").then((r) => {
      if (!r.ok) throw new Error(`Failed to load redistribute.py: ${r.status}`);
      return r.text();
    });
    state.pyodide.runPython(pySource);
    state.processFn = state.pyodide.globals.get("process_csv");
    setStatus("Ready. Drop a CSV above.", false);
    updateButtons();
  } catch (err) {
    setStatus("", false);
    showError(`Could not initialize Python: ${err.message}`);
  }
}
```

with:

```javascript
async function bootPyodide() {
  try {
    setStatus("Loading Python runtime…", true);
    state.pyodide = await loadPyodide();

    setStatus("Loading redistribution logic…", true);
    const redistributeSource = await fetch("./redistribute.py").then((r) => {
      if (!r.ok) throw new Error(`Failed to load redistribute.py: ${r.status}`);
      return r.text();
    });
    state.pyodide.runPython(redistributeSource);

    setStatus("Loading combine logic…", true);
    const combineSource = await fetch("./combine_exports.py").then((r) => {
      if (!r.ok) throw new Error(`Failed to load combine_exports.py: ${r.status}`);
      return r.text();
    });
    state.pyodide.runPython(combineSource);

    state.processFn = state.pyodide.globals.get("process_csv");
    state.combineFn = state.pyodide.globals.get("combine_raw_exports_web");
    setStatus("Ready. Drop file(s) above.", false);
    updateButtons();
  } catch (err) {
    setStatus("", false);
    showError(`Could not initialize Python: ${err.message}`);
  }
}
```

Replace `updateButtons`:

```javascript
function updateButtons() {
  el.runBtn.disabled = !state.file || !state.processFn;
  el.clearBtn.disabled = !state.file;
}
```

with:

```javascript
function updateButtons() {
  el.runBtn.disabled = !state.files.length || !state.processFn || !state.combineFn;
  el.clearBtn.disabled = !state.files.length;
}
```

Replace `handleFile` and `clearFile`:

```javascript
function handleFile(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".csv")) {
    showError("Please choose a .csv file.");
    return;
  }
  clearError();
  state.file = file;
  el.dropZone.classList.add("has-file");
  el.dropZoneText.innerHTML = `<span class="file-name">${escapeHtml(file.name)}</span>`;
  updateButtons();
}

function clearFile() {
  state.file = null;
  state.result = null;
  el.fileInput.value = "";
  el.dropZone.classList.remove("has-file");
  el.dropZoneText.textContent = "Drop the stock CSV here or click to select";
  el.results.classList.add("hidden");
  clearError();
  updateButtons();
}
```

with:

```javascript
function handleFiles(fileList) {
  const files = Array.from(fileList || []);
  if (!files.length) return;
  const nonCsv = files.filter((f) => !f.name.toLowerCase().endsWith(".csv"));
  if (nonCsv.length) {
    showError(`Please choose .csv files only. Not a CSV: ${nonCsv.map((f) => f.name).join(", ")}`);
    return;
  }
  clearError();
  state.files = files;
  el.dropZone.classList.add("has-file");
  const label = files.length === 1 ? "1 file selected" : `${files.length} files selected`;
  el.dropZoneText.innerHTML = `<span class="file-name">${label}: ${files.map((f) => escapeHtml(f.name)).join(", ")}</span>`;
  updateButtons();
}

function clearFiles() {
  state.files = [];
  state.result = null;
  el.fileInput.value = "";
  el.dropZone.classList.remove("has-file");
  el.dropZoneText.textContent = "Drop one or more stock export files here or click to select";
  el.results.classList.add("hidden");
  clearError();
  updateButtons();
}
```

Replace the event listener wiring:

```javascript
el.fileInput.addEventListener("change", (e) => handleFile(e.target.files[0]));

el.dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  el.dropZone.classList.add("dragging");
});
el.dropZone.addEventListener("dragleave", () => el.dropZone.classList.remove("dragging"));
el.dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  el.dropZone.classList.remove("dragging");
  handleFile(e.dataTransfer.files[0]);
});

el.clearBtn.addEventListener("click", clearFile);
```

with:

```javascript
el.fileInput.addEventListener("change", (e) => handleFiles(e.target.files));

el.dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  el.dropZone.classList.add("dragging");
});
el.dropZone.addEventListener("dragleave", () => el.dropZone.classList.remove("dragging"));
el.dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  el.dropZone.classList.remove("dragging");
  handleFiles(e.dataTransfer.files);
});

el.clearBtn.addEventListener("click", clearFiles);
```

Replace the run-button handler:

```javascript
el.runBtn.addEventListener("click", async () => {
  if (!state.file || !state.processFn) return;
  clearError();
  el.runBtn.disabled = true;
  setStatus("Reading file…", true);

  try {
    const buf = await state.file.arrayBuffer();
    const csvText = new TextDecoder("utf-8").decode(buf);

    setStatus("Running redistribution…", true);
    await new Promise((r) => setTimeout(r, 30));  // let the UI update

    const proxy = state.processFn(csvText);
    const jsResult = proxy.toJs({ dict_converter: Object.fromEntries });
    proxy.destroy();

    state.result = jsResult;
    renderResults(jsResult);
    setStatus("Done.", false);
  } catch (err) {
    console.error(err);
    setStatus("", false);
    showError(`Processing failed: ${err.message}`);
  } finally {
    updateButtons();
  }
});
```

with:

```javascript
el.runBtn.addEventListener("click", async () => {
  if (!state.files.length || !state.processFn || !state.combineFn) return;
  clearError();
  el.runBtn.disabled = true;
  setStatus("Reading file(s)…", true);

  try {
    const decoder = new TextDecoder("utf-8");
    const texts = [];
    for (const f of state.files) {
      const buf = await f.arrayBuffer();
      texts.push(decoder.decode(buf));
    }
    const names = state.files.map((f) => f.name);

    setStatus("Combining file(s)…", true);
    await new Promise((r) => setTimeout(r, 30));  // let the UI update

    const combineProxy = state.combineFn(names, texts);
    const combined = combineProxy.toJs({ dict_converter: Object.fromEntries });
    combineProxy.destroy();

    setStatus("Running redistribution…", true);
    await new Promise((r) => setTimeout(r, 30));

    const proxy = state.processFn(combined.csv_text);
    const jsResult = proxy.toJs({ dict_converter: Object.fromEntries });
    proxy.destroy();

    state.result = jsResult;
    renderResults(jsResult, combined.stats);
    setStatus("Done.", false);
  } catch (err) {
    console.error(err);
    setStatus("", false);
    showError(`Processing failed: ${err.message}`);
  } finally {
    updateButtons();
  }
});
```

Replace the start of `renderResults` (the summary-tile and warnings block; the downloads/table logic below it is unchanged except `baseName`):

```javascript
function renderResults(result) {
  const stats = result.stats;

  const shipmentSummary = stats.shipment_summary || [];
  const madridSummary = shipmentSummary.find((s) => s.shop === "Madrid");
  const palmaSummary = shipmentSummary.find((s) => s.shop === "Palma");
  const barcelonaSummary = shipmentSummary.find((s) => s.shop === "Barcelona");

  el.summaryGrid.innerHTML = "";
  addSummary("Input rows", stats.raw_input_rows, `${stats.dropped_zero_rows} zero, ${stats.dropped_duplicate_rows} dup dropped`);
  addSummary("Processed", stats.cleaned_rows);
  addSummary("SKUs to move", stats.skus_with_moves);
  addSummary("Units total", stats.total_units_transferred);
  if (madridSummary) addSummary("Madrid ships", `${madridSummary.units}`, `${madridSummary.lines} lines`);
  if (palmaSummary) addSummary("Palma ships", `${palmaSummary.units}`, `${palmaSummary.lines} lines`);
  if (barcelonaSummary) addSummary("Barcelona ships", `${barcelonaSummary.units}`, `${barcelonaSummary.lines} lines`);

  el.warningsContainer.innerHTML = "";
  const warnings = [];
  if (stats.corrupt_sku_rows && stats.corrupt_sku_rows.length) {
    warnings.push({
      title: `${stats.corrupt_sku_rows.length} row(s) with scientific-notation SKUs`,
      detail: "The source spreadsheet mangled long numeric SKUs into '9E+12'-style values. Rows are processed but you should fix the source.",
      items: stats.corrupt_sku_rows.slice(0, 5).map((r) => `Row ${r.input_row}: ${r.title} — SKU=${r.sku}`),
    });
  }
  if (stats.negative_input_rows && stats.negative_input_rows.length) {
    warnings.push({
      title: `${stats.negative_input_rows.length} row(s) with negative stock`,
      detail: "Passed through unchanged.",
      items: stats.negative_input_rows.slice(0, 5).map((r) => `Row ${r.input_row}: ${r.title} — M=${r.m} P=${r.p} B=${r.b}`),
    });
  }
  warnings.forEach(renderWarning);

  el.downloads.innerHTML = "";
  const baseName = state.file.name.replace(/\.csv$/i, "");
  addDownload(`${baseName}(out).csv`, result.main_csv);
```

with:

```javascript
function renderResults(result, combineStats) {
  const stats = result.stats;

  const shipmentSummary = stats.shipment_summary || [];
  const madridSummary = shipmentSummary.find((s) => s.shop === "Madrid");
  const palmaSummary = shipmentSummary.find((s) => s.shop === "Palma");
  const barcelonaSummary = shipmentSummary.find((s) => s.shop === "Barcelona");

  el.summaryGrid.innerHTML = "";
  addSummary("Files combined", combineStats.files.length);
  addSummary("Input rows", stats.raw_input_rows, `${stats.dropped_zero_rows} zero, ${stats.dropped_duplicate_rows} dup dropped`);
  addSummary("Processed", stats.cleaned_rows);
  addSummary("SKUs to move", stats.skus_with_moves);
  addSummary("Units total", stats.total_units_transferred);
  if (madridSummary) addSummary("Madrid ships", `${madridSummary.units}`, `${madridSummary.lines} lines`);
  if (palmaSummary) addSummary("Palma ships", `${palmaSummary.units}`, `${palmaSummary.lines} lines`);
  if (barcelonaSummary) addSummary("Barcelona ships", `${barcelonaSummary.units}`, `${barcelonaSummary.lines} lines`);

  el.warningsContainer.innerHTML = "";
  const warnings = [];
  if (combineStats.conflicting_duplicate_skus && combineStats.conflicting_duplicate_skus.length) {
    warnings.push({
      title: `${combineStats.conflicting_duplicate_skus.length} duplicate SKU(s) had conflicting stock values across files`,
      detail: "Kept the first file's numbers for each. Verify these are correct.",
      items: combineStats.conflicting_duplicate_skus.slice(0, 5),
    });
  }
  if (combineStats.mismatched_duplicate_skus && combineStats.mismatched_duplicate_skus.length) {
    warnings.push({
      title: `${combineStats.mismatched_duplicate_skus.length} SKU(s) matched across files but title/size differed`,
      detail: "Both rows were kept as distinct entries. Verify this is correct.",
      items: combineStats.mismatched_duplicate_skus.slice(0, 5),
    });
  }
  if (stats.corrupt_sku_rows && stats.corrupt_sku_rows.length) {
    warnings.push({
      title: `${stats.corrupt_sku_rows.length} row(s) with scientific-notation SKUs`,
      detail: "The source spreadsheet mangled long numeric SKUs into '9E+12'-style values. Rows are processed but you should fix the source.",
      items: stats.corrupt_sku_rows.slice(0, 5).map((r) => `Row ${r.input_row}: ${r.title} — SKU=${r.sku}`),
    });
  }
  if (stats.negative_input_rows && stats.negative_input_rows.length) {
    warnings.push({
      title: `${stats.negative_input_rows.length} row(s) with negative stock`,
      detail: "Passed through unchanged.",
      items: stats.negative_input_rows.slice(0, 5).map((r) => `Row ${r.input_row}: ${r.title} — M=${r.m} P=${r.p} B=${r.b}`),
    });
  }
  if (combineStats.identical_duplicate_skus && combineStats.identical_duplicate_skus.length) {
    warnings.push({
      variant: "info",
      title: `${combineStats.identical_duplicate_skus.length} duplicate SKU(s) merged`,
      detail: "Same SKU, title, size, and stock appeared in more than one file. Kept one copy.",
      items: combineStats.identical_duplicate_skus.slice(0, 5),
    });
  }
  warnings.forEach(renderWarning);

  el.downloads.innerHTML = "";
  const baseName = state.files.length === 1 ? state.files[0].name.replace(/\.csv$/i, "") : "combined";
  addDownload(`${baseName}(out).csv`, result.main_csv);
```

Replace `renderWarning`:

```javascript
function renderWarning(w) {
  const div = document.createElement("div");
  div.className = "warnings";
  div.innerHTML = `
    <strong>${escapeHtml(w.title)}</strong>
    <div>${escapeHtml(w.detail)}</div>
    ${w.items.length ? `<ul>${w.items.map((i) => `<li>${escapeHtml(i)}</li>`).join("")}</ul>` : ""}
  `;
  el.warningsContainer.appendChild(div);
}
```

with:

```javascript
function renderWarning(w) {
  const div = document.createElement("div");
  div.className = w.variant === "info" ? "warnings info" : "warnings";
  div.innerHTML = `
    <strong>${escapeHtml(w.title)}</strong>
    <div>${escapeHtml(w.detail)}</div>
    ${w.items.length ? `<ul>${w.items.map((i) => `<li>${escapeHtml(i)}</li>`).join("")}</ul>` : ""}
  `;
  el.warningsContainer.appendChild(div);
}
```

- [ ] **Step 3: Manual smoke test with small synthetic files**

Start a local server:

```bash
cd /Users/lucapapaleo/Desktop/claude/personal/cortana-stock-web
python3 -m http.server 8000
```

Create two tiny synthetic fixture files in `/private/tmp/claude-501/-Users-lucapapaleo-Desktop-claude-personal/224c8b4e-4bef-47ae-aaa5-252900ddd97b/scratchpad/`:

`smoke1.csv`:
```
Title,Option1 Name,Option1 Value,SKU,Barcelona Online,Tienda Madrid,Tienda Palma,Tienda Barcelona
Smoke Test Item,Talla,40,SMOKE1,999,not stocked,2,3
```

`smoke2.csv`:
```
Title,Option1 Name,Option1 Value,SKU,Barcelona Online,Tienda Madrid,Tienda Palma,Tienda Barcelona
Smoke Test Item,Talla,40,SMOKE1,999,not stocked,2,3
```

Open `http://localhost:8000/` in a browser, drop both files at once, click "Run redistribution", and confirm:
- The drop zone shows "2 files selected".
- The summary grid shows a "Files combined" tile reading `2`.
- A blue/informational warning card reads "1 duplicate SKU(s) merged".
- The results table shows one row for `SMOKE1` with Madrid `0` (not "not stocked" or a crash).

Stop the server (Ctrl+C) once confirmed.

- [ ] **Step 4: Commit**

```bash
cd /Users/lucapapaleo/Desktop/claude/personal
git add cortana-stock-web/index.html cortana-stock-web/app.js
git commit -m "$(cat <<'EOF'
Accept multiple raw export files in the Cortana stock web app

The drop zone now takes any number of files, combines them via
combine_exports.py before running the existing redistribution logic
unchanged, and surfaces cross-file duplicate-SKU diagnostics as
summary/warning UI.
EOF
)"
```

---

### Task 5: Web app — README update

**Files:**
- Modify: `/Users/lucapapaleo/Desktop/claude/personal/cortana-stock-web/README.md`

**Interfaces:** None — documentation only.

- [ ] **Step 1: Update the README**

In `cortana-stock-web/README.md`, replace this paragraph:

```markdown
A single-page web app that runs the Cortana stock redistribution algorithm entirely in the browser. Upload the weekly stock CSV, get the redistribution sheet plus per-shop shipment CSVs, and see the results table on the page.
```

with:

```markdown
A single-page web app that runs the Cortana stock redistribution algorithm entirely in the browser. Drop one or more weekly stock export files (raw Shopify exports or an already-cleaned CSV), get the redistribution sheet plus per-shop shipment CSVs, and see the results table on the page.
```

Replace the "Files" list:

```markdown
## Files

- `index.html` — UI (drop zone, summary, downloads, results table)
- `app.js` — bootstraps Pyodide, wires the UI, triggers downloads, renders the table
- `redistribute.py` — the redistribution algorithm (adapted from the Claude Code skill to work on strings instead of files)
```

with:

```markdown
## Files

- `index.html` — UI (drop zone, summary, downloads, results table)
- `app.js` — bootstraps Pyodide, wires the UI, triggers downloads, renders the table
- `redistribute.py` — the redistribution algorithm (adapted from the Claude Code skill to work on strings instead of files)
- `combine_exports.py` — combines any number of raw export files into one cleaned CSV before redistribution runs (adapted from the Claude Code skill's `combine_exports.py`)
```

Replace the last bullet under "## Notes":

```markdown
- The redistribution logic is a copy of the Claude Code skill at `~/.claude/skills/cortana-stock/scripts/redistribute.py`. If you change the rules in one place, sync the other.
```

with:

```markdown
- The redistribution logic is a copy of the Claude Code skill at `~/.claude/skills/cortana-stock/scripts/redistribute.py`. If you change the rules in one place, sync the other.
- Same goes for `combine_exports.py` and `~/.claude/skills/cortana-stock/scripts/combine_exports.py`.
```

- [ ] **Step 2: Commit**

```bash
cd /Users/lucapapaleo/Desktop/claude/personal
git add cortana-stock-web/README.md
git commit -m "Document multi-file input and combine_exports.py in cortana-stock-web README"
```

---

### Task 6: End-to-end verification with real data

**Files:** None — verification only, using Luca's real downloaded files.

**Interfaces:** Exercises the full pipeline from Tasks 3 and 4 together.

- [ ] **Step 1: Start the local server**

```bash
cd /Users/lucapapaleo/Desktop/claude/personal/cortana-stock-web
python3 -m http.server 8000
```

- [ ] **Step 2: Drive the app with Playwright against the 3 real files**

Use the Playwright MCP browser tools (already used in this repo — see the `.playwright-mcp/` directory and the `result-v1.png`/`diag-success.png`-style screenshots at the repo root from this app's original build):

1. `browser_navigate` to `http://localhost:8000/`.
2. `browser_file_upload` with all three real files:
   - `/Users/lucapapaleo/Downloads/inventory_export_1 (36).csv`
   - `/Users/lucapapaleo/Downloads/inventory_export_1 (37).csv`
   - `/Users/lucapapaleo/Downloads/inventory_export_1 (38).csv`
3. Click "Run redistribution".
4. `browser_snapshot` and confirm:
   - "Files combined" tile reads `3`.
   - "Input rows" is close to 963 + 217 + 950 = 2130 (minus any all-zero rows dropped).
   - A duplicate-SKU warning (informational, blue) appears, consistent with the 26 identical cross-file duplicates found during design (no conflicting or mismatched warnings expected, since none were found in this real data during design research).
   - The results table renders with real product titles/sizes, and no row shows the literal text `not stocked` or `Talla` in the wrong place.
5. `browser_console_messages` and confirm there are no JavaScript errors or unhandled promise rejections.

- [ ] **Step 3: Stop the server**

Stop the `python3 -m http.server` process (Ctrl+C, or kill the background shell).

No commit — this task changes no files.
