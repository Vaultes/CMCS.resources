"""
build_funding_datatable_json.py

Reads the RHTP funding spreadsheet (.xlsx or .csv) and builds a JSON file for a
DataTable in the {"aaData": [ {...}, ... ]} shape.

Spreadsheet columns:
    A State | B Baseline Funding | C Workload Funding |
    D Budget Period 1 Total Funding | E Budget Period 2 Total Funding | ...

Output columns:
    - State   (column A, spelling corrected against the official state names;
               District of Columbia is left out entirely)
    - Budget Period 1 Total Funding
    - Budget Period 2 Total Funding
      (column D onward, titles taken from the header row with commas removed,
       so a new "Budget Period 3" column is picked up automatically)

The "All States Total" row is skipped. Rows are sorted alphabetically by state.

Usage:
    python3 build_funding_datatable_json.py -i rhtp-funding.xlsx -o rhtp-funding-datatable.json
    python3 build_funding_datatable_json.py
        (no flags: the script asks for the input and output file names)
"""

import argparse
import csv
import difflib
import json
import os
import re
import sys

import openpyxl

# ── Spreadsheet layout (0-based column indexes) ──────────────────────────────
STATE_COL       = 0   # column A: state name
FIRST_FUND_COL  = 3   # column D: first funding column; all later columns with a header are included

# Official spellings, keyed by abbreviation.
STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
    "PR": "Puerto Rico", "GU": "Guam", "VI": "Virgin Islands",
    "AS": "American Samoa", "MP": "Northern Mariana Islands",
}

EXCLUDED_STATES = {"District of Columbia"}   # rows left out of the datatable entirely
SKIP_PREFIXES   = ("all states", "total")     # summary rows to skip

OFFICIAL_BY_LOWER = {name.lower(): name for name in STATE_NAMES.values()}


def clean_path(text):
    """Tidy a typed or drag-and-dropped path (removes quotes and '\\ ' escapes)."""
    return text.strip().strip("'\"").replace("\\ ", " ")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build a DataTable JSON file from the RHTP funding spreadsheet."
    )
    parser.add_argument("-i", "--input", help="Input spreadsheet (.xlsx or .csv)")
    parser.add_argument("-o", "--output", help="Output JSON file name")
    args = parser.parse_args()

    if not args.input:
        args.input = input("Input file (.xlsx or .csv): ")
    if not args.output:
        args.output = input("Output JSON file name: ")

    args.input = clean_path(args.input)
    args.output = clean_path(args.output)
    if not args.output.lower().endswith(".json"):
        args.output += ".json"
    return args


def fix_state(raw):
    """
    Return the official spelling of a state name, or None if no good match.
      'Pennsylvnia' -> 'Pennsylvania',  'west virginia' -> 'West Virginia',  'TX' -> 'Texas'
    """
    text = re.sub(r"\s+", " ", raw).strip()
    if text.upper() in STATE_NAMES:                    # abbreviation
        return STATE_NAMES[text.upper()]
    if text.lower() in OFFICIAL_BY_LOWER:              # right spelling, any capitalization
        return OFFICIAL_BY_LOWER[text.lower()]
    match = difflib.get_close_matches(text.lower(), OFFICIAL_BY_LOWER.keys(), n=1, cutoff=0.8)
    return OFFICIAL_BY_LOWER[match[0]] if match else None


def column_title(header):
    """Datatable column title from a header: commas removed, extra spaces collapsed."""
    text = str(header).replace(",", " ")        # DataTable can't handle commas in titles
    return re.sub(r"\s{2,}", " ", text).strip()


def format_money(raw):
    """203404326.53999999 or '$203,404,326.54' -> '$203,404,326.54'. Leaves unparseable values as-is."""
    if raw is None:
        return ""
    text = str(raw).strip()
    try:
        return f"${float(text.replace('$', '').replace(',', '')):,.2f}"
    except ValueError:
        return text


def read_rows(path):
    """Return all rows (header first) from either a .csv or .xlsx file."""
    if path.lower().endswith(".csv"):
        # utf-8-sig strips the hidden BOM character Excel adds to the start of CSVs
        with open(path, newline="", encoding="utf-8-sig") as f:
            return [tuple(r) for r in csv.reader(f)]
    # data_only=True returns calculated values instead of formulas like "=B2+C2"
    wb = openpyxl.load_workbook(path, data_only=True)
    return list(wb.active.iter_rows(values_only=True))


def main():
    args = parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: input file not found: {args.input}")
        sys.exit(1)
    if os.path.splitext(args.input)[1].lower() not in (".xlsx", ".csv"):
        print("ERROR: input must be an .xlsx or .csv file")
        sys.exit(1)

    all_rows = read_rows(args.input)
    header, rows = all_rows[0], all_rows[1:]

    fund_cols = [
        (i, column_title(h))
        for i, h in enumerate(header)
        if i >= FIRST_FUND_COL and h not in (None, "")
    ]

    records, fixed, unmatched = [], [], []

    for row in rows:
        raw_state = str(row[STATE_COL]).strip() if len(row) > STATE_COL and row[STATE_COL] is not None else ""
        if not raw_state or raw_state.lower().startswith(SKIP_PREFIXES):
            continue

        state = fix_state(raw_state)
        if state is None:
            unmatched.append(raw_state)
            state = raw_state                      # keep as-is so the row isn't lost
        elif state != raw_state:
            fixed.append(f"{raw_state} -> {state}")

        if state in EXCLUDED_STATES:
            continue

        record = {"State": state}
        for i, title in fund_cols:
            record[title] = format_money(row[i] if i < len(row) else None)
        records.append(record)

    records.sort(key=lambda r: r["State"])

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump({"aaData": records}, f, indent=2, ensure_ascii=False)

    print(f"Read: {args.input}")
    print(f"Wrote {len(records)} records to {args.output}")
    print("Columns: " + " | ".join(["State"] + [t for _, t in fund_cols]))
    if fixed:
        print("Fixed state spellings: " + "; ".join(fixed))
    if unmatched:
        print("WARNING - no matching state name (kept as-is): " + ", ".join(unmatched))


if __name__ == "__main__":
    main()
