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
