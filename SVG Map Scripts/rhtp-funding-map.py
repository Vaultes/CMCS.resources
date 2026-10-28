import json
import os
import re
import openpyxl

BASE = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE    = os.path.join(BASE, "rhtp-funding.xlsx")
TEMPLATE_FILE = os.path.join(BASE, "svg-default-2023 copy.json")
OUTPUT_FILE   = os.path.join(BASE, "svg-map1-funding.json")

# ── Settings ──────────────────────────────────────────────────────────────────
FIRST_DATA_COL = 3          # 0-based index: 3 = column D. D, E, F... are used.
BULLET         = "\u2022"   # •  (written to the JSON file as \u2022)

INITIAL_COLOR  = "046791"
OVER_COLOR     = "17415F"
SELECTED_COLOR = "046791"

# States/territories that get a fixed message instead of funding data
NON_PARTICIPANTS = {
    "District of Columbia": "Does not participate.",
}


def clean_name(name):
    """Strip any <u></u> tags and whitespace so names match the Excel sheet."""
    return re.sub(r"</?u>", "", name or "").strip()


def format_value(value):
    """Format numbers as currency; pass text through unchanged."""
    if isinstance(value, (int, float)):
        return f"${value:,.2f}"
    return str(value).strip()


# ── Load Excel data ───────────────────────────────────────────────────────────
# data_only=True returns calculated values instead of formulas like "=B2+C2"
wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
ws = wb.active
rows = ws.iter_rows(values_only=True)

header_row = next(rows)
data_cols = [
    (i, str(h).strip())
    for i, h in enumerate(header_row)
    if i >= FIRST_DATA_COL and h not in (None, "")
]
print(f"Popup lines will use columns: {', '.join(h for _, h in data_cols)}")

funding_data = {}
for row in rows:
    if not row or row[0] is None:
        continue
    name = clean_name(str(row[0]))
    if not name or name.lower().startswith("all states"):
        continue  # skip blank rows and the totals row

    lines = []
    for i, header in data_cols:
        value = row[i] if i < len(row) else None
        if value is None:
            continue
        lines.append(f"{BULLET} {header}: {format_value(value)}")

    if lines:
        funding_data[name] = lines

print(f"Loaded funding data for {len(funding_data)} states from Excel.")

# ── Load template JSON ────────────────────────────────────────────────────────
with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
    map_json = json.load(f)

# ── Update each state ─────────────────────────────────────────────────────────
updated = 0
not_found = []
map_names = set()

for state in map_json["stateData"]:
    name = clean_name(state["stateName"])
    map_names.add(name)

    state["stateName"]          = f"<u>{name}</u>"
    state["initialStateColor"]  = INITIAL_COLOR
    state["stateOverColor"]     = OVER_COLOR
    state["stateSelectedColor"] = SELECTED_COLOR

    if name in NON_PARTICIPANTS:
        # Matches the existing funding map: no link, fixed message
        state.pop("url", None)
        state.pop("stateMode", None)
        state["text"] = [NON_PARTICIPANTS[name]]
    elif name in funding_data:
        state["text"] = funding_data[name]
        updated += 1
    else:
        state["text"] = []
        not_found.append(name)

# ── Write output ──────────────────────────────────────────────────────────────
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(map_json, f, indent=2)  # ensure_ascii default writes • as \u2022

print(f"Updated {updated} states with funding data.")
if not_found:
    print(f"No Excel data for: {', '.join(not_found)} (text left empty)")
unmatched = set(funding_data) - map_names
if unmatched:
    print(f"WARNING - Excel rows with no matching map state: {', '.join(sorted(unmatched))}")
print(f"Output written to: {OUTPUT_FILE}")
