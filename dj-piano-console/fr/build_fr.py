#!/usr/bin/env python3
"""Build the French v2 spec HTML from the English one that generate.py writes.

Every translatable unit (a heading, paragraph, list item, table cell or drawing label) is
replaced in place by byte span, so the markup, the drawing geometry and the styles stay
byte-identical to the English. The audit then checks that every number survived, that inline
tags match, and that no English is left over. Exits 1 if the audit finds anything, which is
also how check-regen.sh learns that the French has fallen behind the English.

    python3 fr/build_fr.py            # dj-piano-console-v2-spec.html -> ...-v2-spec-fr.html
    python3 fr/build_fr.py --check    # audit only, write nothing
"""
import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
sys.path.insert(0, str(HERE))
from units import find_units  # noqa: E402
from fr_units import FR, FR_CSS, OVERRIDES, TAG_EDITS  # noqa: E402

NBSP = " "
UNIT_RE = re.compile(r"(?<=\d) (?=(?:cm|mm|ml|kg|m²|m|L)(?![A-Za-zÀ-ÿ0-9²]))")
NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")
TAG_RE = re.compile(r"<[^>]+>")
# The sub-title carries generate.py's date.today() stamp, the one string that changes every day.
# It is looked up with the date masked, and the French gets the same date spelled in French.
STAMP_RE = re.compile(r"(?<=, )(\d{1,2}) ([A-Z][a-z]+) (\d{4})(?=\. All dimensions)")
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]


def has_letters(s):
    return bool(re.search(r"[A-Za-z]", TAG_RE.sub("", s)))


def numeric(s):
    """Numbers, dimensions and quantities with a unit symbol ("48.2 × 11", "7.55 m²"): commas only."""
    return not has_letters(s) or bool(re.fullmatch(r"[\d.×~ ]+ ?(?:cm|mm|m²|m|kg|L|ml)", TAG_RE.sub("", s).strip()))


def decimal_commas(s):
    return re.sub(r"(?<=\d)\.(?=\d)", ",", s)


def typeset(fr):
    """French spacing: non-breaking space before : and ; and between a number and its unit."""
    fr = fr.replace(" :", NBSP + ":").replace(" ;", NBSP + ";")
    return UNIT_RE.sub(NBSP, fr)


def plain(s):
    return html.unescape(TAG_RE.sub("", s))


def numbers(s, english):
    txt = plain(s)
    return sorted(NUM_RE.findall(decimal_commas(txt) if english else txt))


def mask_stamp(en):
    """(lookup key with the date stamp masked, the stamp spelled in French or None)."""
    m = STAMP_RE.search(en)
    if not m:
        return en, None
    return STAMP_RE.sub("{DATE}", en), f"{int(m.group(1))} {MOIS[MONTHS.index(m.group(2))]} {m.group(3)}"


def build(src):
    """(French HTML, audit problems) for the English spec HTML src."""
    units, stray = find_units(src)
    assert not stray, stray
    ids = {u["en"]: u["id"] for u in json.loads((HERE / "units_en.json").read_text(encoding="utf-8"))}

    problems, used, seen_count = [], set(), Counter()
    pieces, cur = [], 0
    for a, b, tag, in_svg in units:
        en = src[a:b]
        key, fr_date = mask_stamp(en)
        uid = ids.get(key)
        if uid is None:
            if numeric(en):
                fr = decimal_commas(en)
            else:
                # the English changed since units_en.json was taken: give it an id and translate it
                problems.append(f"NEW ENGLISH, not in units_en.json: {en[:90]}")
                fr = en
            pieces += [src[cur:a], typeset(fr)]
            cur = b
            continue
        occ = seen_count[uid]
        seen_count[uid] += 1
        if (uid, occ) in OVERRIDES:
            fr = OVERRIDES[(uid, occ)]
        elif uid in FR:
            fr = FR[uid]
            used.add(uid)
        elif numeric(en):
            fr = decimal_commas(en)
        else:
            problems.append(f"MISSING {uid}: {en[:70]}")
            fr = en
        if fr_date:
            fr = fr.replace("{DATE}", fr_date)
        if TAG_RE.findall(en) != TAG_RE.findall(fr):
            problems.append(f"TAGS {uid}: {TAG_RE.findall(en)} vs {TAG_RE.findall(fr)}")
        if re.search(r"&(?!amp;|quot;|#x27;|lt;|gt;)", fr) or re.search(r"<(?!/?strong>)", fr):
            problems.append(f"ESCAPE {uid}: {fr[:70]}")
        if numbers(en, True) != numbers(fr, False) and "Version" not in en:   # version numbers keep their dot
            problems.append(f"NUMBERS {uid}: en {numbers(en, True)} fr {numbers(fr, False)}")
        pieces += [src[cur:a], typeset(fr)]
        cur = b
    pieces.append(src[cur:])
    out = "".join(pieces)

    for uid in sorted(set(FR) - used):
        problems.append(f"UNUSED {uid}: the English no longer has it; delete it from fr_units.py")

    assert out.count('<html lang="en">') == 1
    out = out.replace('<html lang="en">', '<html lang="fr">')
    assert out.count("</style>") == 1
    out = out.replace("</style>", FR_CSS + "</style>")
    for old, new in TAG_EDITS:
        assert out.count(old) == 1, f"edit fragment matches {out.count(old)} times: {old}"
        out = out.replace(old, new)

    # English residue: common function words that should not survive translation ("on" is French too)
    body = plain(out.split("<body>", 1)[1])
    residue = re.findall(r"\b(the|and|with|of|to|from|for|is|are|at|in|each|per|behind|below|above|front|rear)\b", body)
    if residue:
        problems.append(f"RESIDUE {Counter(residue).most_common()}")
    return out, problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--src", type=Path, default=PKG / "dj-piano-console-v2-spec.html")
    ap.add_argument("--out", type=Path, default=PKG / "dj-piano-console-v2-spec-fr.html")
    ap.add_argument("--check", action="store_true", help="audit only, write nothing")
    args = ap.parse_args()
    out, problems = build(args.src.read_text(encoding="utf-8"))
    print("\n".join(problems) if problems else "audit: clean")
    if not args.check:
        args.out.write_text(out, encoding="utf-8")
        print(f"wrote {args.out}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
