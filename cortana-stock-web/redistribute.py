"""
Cortana stock redistribution — Pyodide-compatible version.

Derived from ~/.claude/skills/cortana-stock/scripts/{redistribute.py,generate_shipments.py}.
This version operates entirely on strings (no filesystem access) so it can run
in Pyodide inside the browser.

Public entry point: process_csv(csv_text) -> dict with the CSV strings, the
table data for on-screen display, and a stats block.
"""

import csv
import io
import re


DEFAULT_RECEIVE_CAPS = {"M": 1, "P": 3, "B": 1}


def compute_transfers(m, p, b, priority=("P", "B", "M"), receive_caps=None):
    if receive_caps is None:
        receive_caps = DEFAULT_RECEIVE_CAPS

    stocks = {"M": m, "P": p, "B": b}
    total = sum(stocks.values())

    if total <= 1:
        return 0, 0, 0, 0, 0, 0

    if all(1 <= s <= 2 for s in (m, p, b)) or all(2 <= s <= 3 for s in (m, p, b)):
        return 0, 0, 0, 0, 0, 0

    base, rem = divmod(total, 3)
    ideals = {shop: base for shop in stocks}
    for shop in priority[:rem]:
        ideals[shop] += 1

    max_recv = {shop: max(0, receive_caps[shop] - stocks[shop]) for shop in stocks}
    available_to_send = {shop: max(0, stocks[shop] - ideals[shop]) for shop in stocks}
    receive_need = {
        shop: min(max(0, ideals[shop] - stocks[shop]), max_recv[shop])
        for shop in stocks
    }

    transfers = {(s, d): 0 for s in stocks for d in stocks if s != d}
    running = dict(stocks)

    for dest in priority:
        need = receive_need[dest]
        if need == 0:
            continue
        for src in reversed(priority):
            if src == dest or need == 0:
                continue
            take = min(need, available_to_send[src])
            if take == 0:
                continue
            if running[src] == 1:
                continue
            transfers[(src, dest)] += take
            available_to_send[src] -= take
            running[src] -= take
            running[dest] += take
            need -= take

    return (
        transfers[("M", "P")],
        transfers[("M", "B")],
        transfers[("B", "P")],
        transfers[("B", "M")],
        transfers[("P", "B")],
        transfers[("P", "M")],
    )


def _find_column_index(header, *patterns):
    for i, h in enumerate(header):
        h_lower = h.strip().lower()
        for pat in patterns:
            if pat.lower() in h_lower:
                return i
    return -1


_SCI_NOTATION_RE = re.compile(r"^[+-]?\d+(\.\d+)?[Ee][+-]?\d+$")


def _is_corrupt_sku(sku):
    return bool(_SCI_NOTATION_RE.match(sku.strip()))


def clean_input(rows):
    if not rows:
        return rows, {
            "input_rows": 0, "dropped_zero": 0, "dropped_duplicate": 0,
            "duplicate_keys": [], "corrupt_sku_rows": [],
        }

    header = rows[0]
    cols = {
        "title": _find_column_index(header, "title"),
        "size": _find_column_index(header, "option1", "talla", "size"),
        "sku": _find_column_index(header, "sku"),
        "madrid": _find_column_index(header, "madrid"),
        "palma": _find_column_index(header, "palma"),
        "barcelona": _find_column_index(header, "barcelona"),
    }
    missing = [k for k, v in cols.items() if v == -1]
    if missing:
        raise ValueError(
            f"Input is missing required column(s): {missing}. Got header: {header}"
        )

    new_header = [header[cols[k]] for k in ("title", "size", "sku", "madrid", "palma", "barcelona")]
    cleaned = [new_header]
    seen = set()
    dropped_zero = 0
    dropped_duplicate = 0
    duplicate_keys = []
    corrupt_sku_rows = []

    max_idx = max(cols.values())
    for input_row_num, row in enumerate(rows[1:], start=2):
        if len(row) <= max_idx:
            continue
        title = row[cols["title"]]
        size = row[cols["size"]]
        sku = row[cols["sku"]]
        try:
            m = int(row[cols["madrid"]])
            p = int(row[cols["palma"]])
            b = int(row[cols["barcelona"]])
        except ValueError:
            continue

        if m == 0 and p == 0 and b == 0:
            dropped_zero += 1
            continue

        key = (title, size, sku)
        if key in seen:
            dropped_duplicate += 1
            duplicate_keys.append(sku)
            continue
        seen.add(key)

        if _is_corrupt_sku(sku):
            corrupt_sku_rows.append({
                "input_row": input_row_num, "title": title, "size": size,
                "sku": sku, "m": m, "p": p, "b": b,
            })

        cleaned.append([title, size, sku, str(m), str(p), str(b)])

    return cleaned, {
        "input_rows": len(rows) - 1,
        "dropped_zero": dropped_zero,
        "dropped_duplicate": dropped_duplicate,
        "duplicate_keys": duplicate_keys,
        "corrupt_sku_rows": corrupt_sku_rows,
    }


def _rows_to_csv(rows):
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", lineterminator="\r\n")
    writer.writerows(rows)
    return buf.getvalue()


SHIPMENT_HEADER = ["Destination", "Title", "Size", "SKU", "Quantity"]


def process_csv(csv_text):
    if csv_text.startswith("﻿"):
        csv_text = csv_text[1:]

    reader = csv.reader(io.StringIO(csv_text), delimiter=";")
    raw_rows = list(reader)

    cleaned, cleanup_stats = clean_input(raw_rows)
    header = cleaned[0]
    data = cleaned[1:]

    out_header = header + [
        "Madrid -> Palma", "Madrid -> Barcelona",
        "Barcelona -> Palma", "Barcelona -> Madrid",
        "Palma -> Barcelona", "Palma -> Madrid",
        "Final Madrid", "Final Palma", "Final Barcelona",
        "Moves",
    ]

    out_rows = [out_header]
    table_rows = []
    skus_with_moves = 0
    total_units_transferred = 0
    negative_input_rows = []
    shipments = {"Madrid": [], "Palma": [], "Barcelona": []}

    for i, row in enumerate(data):
        input_row_num = i + 2
        m, p, b = int(row[3]), int(row[4]), int(row[5])

        if m < 0 or p < 0 or b < 0:
            negative_input_rows.append({
                "input_row": input_row_num, "title": row[0], "m": m, "p": p, "b": b,
            })

        mp, mb, bp, bm, pb, pm = compute_transfers(m, p, b)
        moves = mp + mb + bp + bm + pb + pm
        if moves > 0:
            skus_with_moves += 1
            total_units_transferred += moves

        final_m = m - mp - mb + bm + pm
        final_p = p + mp + bp - pb - pm
        final_b = b + mb + pb - bp - bm

        r = i + 2  # spreadsheet row number: header is row 1, first data row is 2
        out_rows.append(row + [
            str(mp), str(mb), str(bp), str(bm), str(pb), str(pm),
            f"=D{r}-G{r}-H{r}+J{r}+L{r}",
            f"=E{r}+G{r}+I{r}-K{r}-L{r}",
            f"=F{r}+H{r}+K{r}-I{r}-J{r}",
            f"=SUM(G{r}:L{r})",
        ])

        title, size, sku = row[0], row[1], row[2]
        table_rows.append({
            "title": title, "size": size, "sku": sku,
            "m": m, "p": p, "b": b,
            "mp": mp, "mb": mb, "bp": bp, "bm": bm, "pb": pb, "pm": pm,
            "final_m": final_m, "final_p": final_p, "final_b": final_b,
            "moves": moves,
        })

        outflows = [
            ("Madrid", "Palma", mp),
            ("Madrid", "Barcelona", mb),
            ("Barcelona", "Palma", bp),
            ("Barcelona", "Madrid", bm),
            ("Palma", "Barcelona", pb),
            ("Palma", "Madrid", pm),
        ]
        for sender, receiver, qty in outflows:
            if qty > 0:
                shipments[sender].append((receiver, title, size, sku, qty))

    main_csv = _rows_to_csv(out_rows)

    shipment_csvs = {}
    shipment_summary = []
    for shop, items in shipments.items():
        items.sort(key=lambda r: (r[0], r[1], r[2]))
        rows_out = [SHIPMENT_HEADER] + [
            [dest, title, size, sku, str(qty)] for dest, title, size, sku, qty in items
        ]
        shipment_csvs[shop] = _rows_to_csv(rows_out)
        total_units = sum(item[4] for item in items)
        shipment_summary.append({"shop": shop, "lines": len(items), "units": total_units})

    return {
        "main_csv": main_csv,
        "shipments": shipment_csvs,
        "rows": table_rows,
        "stats": {
            "raw_input_rows": cleanup_stats["input_rows"],
            "dropped_zero_rows": cleanup_stats["dropped_zero"],
            "dropped_duplicate_rows": cleanup_stats["dropped_duplicate"],
            "duplicate_keys": cleanup_stats["duplicate_keys"],
            "corrupt_sku_rows": cleanup_stats["corrupt_sku_rows"],
            "cleaned_rows": len(data),
            "output_rows": len(out_rows) - 1,
            "skus_with_moves": skus_with_moves,
            "total_units_transferred": total_units_transferred,
            "negative_input_rows": negative_input_rows,
            "shipment_summary": shipment_summary,
        },
    }
