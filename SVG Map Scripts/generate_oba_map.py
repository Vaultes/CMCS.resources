import json
import openpyxl
import os
import sys

# ── CONFIG ────────────────────────────────────────────────────────────────────
BASE        = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE  = os.path.join(BASE, "ks_is_red_Medicaid_gov_Compliance_Mock-up_Data.xlsx")
SHEET_NAME  = "OBA Data"
JSON_FILE   = os.path.join(BASE, "svg-default-2023.json")
OUTPUT_FILE = os.path.join(BASE, "svg-map-oba.json")

# ── COLORS ────────────────────────────────────────────────────────────────────
# Fill color per OBA Assessment. Hover/selected colors stay the single dark
# navy used across the base template, matching its existing convention.
STATUS_COLORS = {
    "Blue":   "046791",
    "Yellow": "FFD700",
    "Red":    "B3261E",
}
NO_DATA_COLOR = "862074"
# Any state with data in "Compliance Issue Type(s)" (column F) is colored this
# red, overriding whatever its OBA Assessment (column C) says.
ISSUE_COLOR = "5D1116"
# Global abbreviation text color, written to mapSettings (not per-state).
ABBR_COLOR_DEFAULT = "ffffff"

# Popup formatting: state name gets underlined, every text line gets a bullet.
BULLET = "\u2022 "

# Some spreadsheet state names don't match the base JSON's stateName exactly.
NAME_ALIASES = {
    "Virgin Islands": "US Virgin Islands",
}

# ── LOAD EXCEL ────────────────────────────────────────────────────────────────
try:
    wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
except Exception as e:
    print(f"ERROR: Could not load Excel file. Details: {e}")
    sys.exit(1)

if SHEET_NAME not in wb.sheetnames:
    print(f"ERROR: Sheet '{SHEET_NAME}' not found in {EXCEL_FILE}")
    sys.exit(1)

ws = wb[SHEET_NAME]

# ── READ COMPLIANCE DATA ───────────────────────────────────────────────────────
# Columns: A State | B Reporting Period (unused) | C OBA Assessment
#          D Number of Criteria Below Target | E Criteria Below Target | F Compliance Issue Type(s)
oba_data = {}
for row in ws.iter_rows(min_row=2, values_only=True):
    state = row[0]
    if not state or str(state).strip() == "":
        continue
    state = str(state).strip()

    # Skip summary/total rows (e.g. "Blue States/Meeting Target") which have
    # a number instead of a Blue/Yellow/Red string in the assessment column.
    if row[2] is not None and not isinstance(row[2], str):
        continue

    assessment = (row[2] or "").strip().capitalize() if row[2] else "Blue"
    count      = row[3]
    criteria   = (row[4] or "").strip() if row[4] else ""
    issues     = (row[5] or "").strip() if row[5] else ""
    oba_data[state] = {
        "assessment": assessment,
        "count": count,
        "criteria": criteria,
        "issues": issues,
    }
    # Also index under any alias that maps TO this name, so lookups by the
    # base JSON's stateName succeed regardless of which side has the alias.

print(f"Loaded {len(oba_data)} states/territories from '{SHEET_NAME}'")

def lookup(state_name):
    """Find compliance data for a base-JSON stateName, accounting for aliases."""
    if state_name in oba_data:
        return oba_data[state_name]
    for spreadsheet_name, json_name in NAME_ALIASES.items():
        if json_name == state_name and spreadsheet_name in oba_data:
            return oba_data[spreadsheet_name]
    return None

# ── BUILD POPUP TEXT ──────────────────────────────────────────────────────────
def criteria_noun(count):
    """'Criterion' for exactly 1, 'Criteria' otherwise."""
    return "Criterion" if count == 1 else "Criteria"

def build_state_text(record):
    if record is None:
        return ["No data reported for this reporting period."]

    assessment = record["assessment"]
    issues     = record["issues"]
    count      = record["count"]
    criteria   = record["criteria"]

    has_issues       = bool(issues)
    has_below_target = bool(count)  # 0/None/"" are all falsy -> no below-target criteria

    # No compliance issues and no below-target criteria: fully meets targets.
    if not has_issues and not has_below_target:
        return ["No Compliance Issues",
                "Meets OBA Targets"]

    if has_issues:
        # Compliance issue(s) reported. If there's no below-target count to go
        # with it, the second line is "Meets OBA Targets" instead of "0 ...".
        if not has_below_target:
            criteria_line = "Meets OBA Targets"
        else:
            criteria_display = criteria if criteria else "\u2014"
            criteria_line = f"{count} {criteria_noun(count)} Below Targets: {criteria_display}"
        return [
            f"Compliance Issue Type(s): {issues}",
            criteria_line,
        ]

    # No compliance issues, but below-target criteria exist (Yellow/Red).
    # "Below Targets" stays plural regardless of count — only the noun
    # (Criterion/Criteria) changes with the number.
    criteria_display = criteria if criteria else "\u2014"
    return [
        "No Compliance Issues",
        f"{count} {criteria_noun(count)} Below Targets: {criteria_display}",
    ]

# ── LOAD BASE JSON AND UPDATE ──────────────────────────────────────────────────
if not os.path.exists(JSON_FILE):
    print(f"ERROR: Base JSON file not found at {JSON_FILE}")
    sys.exit(1)

with open(JSON_FILE, "r") as f:
    map_json = json.load(f)

# Keep a global default abbreviationColor in mapSettings (used as a fallback
# by whatever renders this JSON), in addition to the per-state one below.
map_json.setdefault("mapSettings", {})
map_json["mapSettings"]["abbreviationColor"] = ABBR_COLOR_DEFAULT

updated = 0
no_data = []

for state in map_json.get("stateData", []):
    name = state["stateName"]
    record = lookup(name)

    if record is not None:
        if record["issues"]:
            color = ISSUE_COLOR
        else:
            color = STATUS_COLORS.get(record["assessment"], NO_DATA_COLOR)
        updated += 1
    else:
        color = NO_DATA_COLOR
        no_data.append(name)

    state["initialStateColor"]  = color
    state["stateOverColor"]     = color
    state["stateSelectedColor"] = color
    state["stateName"] = f"{name}"
    state["text"] = [f"{BULLET}{line}" for line in build_state_text(record)]

# ── WRITE OUTPUT ──────────────────────────────────────────────────────────────
with open(OUTPUT_FILE, "w") as f:
    json.dump(map_json, f, indent=2)

print(f"\nDone! Updated {updated} states/territories.")
if no_data:
    print(f"No Excel data for (fell back to '{NO_DATA_COLOR}'): {', '.join(no_data)}")
print(f"Output: {OUTPUT_FILE}")
