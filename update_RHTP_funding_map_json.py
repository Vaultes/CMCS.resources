import json
import openpyxl
import os

BASE = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE  = os.path.join(BASE, "rhtp-funding.xlsx")
JSON_FILE   = os.path.join(BASE, "rhtpautomationsvg-map.json")
OUTPUT_FILE = os.path.join(BASE, "svg-map-updated.json")

# ── Load Excel data ───────────────────────────────────────────────────────────
wb = openpyxl.load_workbook(EXCEL_FILE)
ws = wb.active

funding_data = {}
headers = None
for row in ws.iter_rows(values_only=True):
    if headers is None:
        headers = row
        continue
    if row[0] is None:
        continue
    state_name = row[0]
    baseline   = row[1]
    workload   = row[2]
    total      = row[3]
    if state_name and baseline is not None:
        funding_data[state_name] = {
            "baseline": baseline,
            "workload": workload,
            "total":    total
        }

print(f"Loaded funding data for {len(funding_data)} states from Excel.")

# ── Load JSON ─────────────────────────────────────────────────────────────────
with open(JSON_FILE, 'r') as f:
    map_json = json.load(f)

# ── Update each state ─────────────────────────────────────────────────────────
updated = 0
not_found = []

for state in map_json["stateData"]:
    name = state["stateName"]

    # Set colors for all states
    state["initialStateColor"] = "046791"
    state["stateOverColor"]    = "17415F"
    state["stateSelectedColor"] = "17415F"

    # Set text from Excel if available
    if name in funding_data:
        d = funding_data[name]
        state["text"] = [
            f"Baseline Funding: ${d['baseline']:,.2f}",
            f"Workload Funding: ${d['workload']:,.2f}",
            f"Budget Period 1 Total Funding: ${d['total']:,.2f}"
        ]
        updated += 1
    else:
        not_found.append(name)

# ── Write output ──────────────────────────────────────────────────────────────
with open(OUTPUT_FILE, 'w') as f:
    json.dump(map_json, f, indent=2)

print(f"Updated {updated} states with funding data.")
if not_found:
    print(f"No Excel data found for: {', '.join(not_found)} (colors updated, text left unchanged)")
print(f"Output written to: {OUTPUT_FILE}")
