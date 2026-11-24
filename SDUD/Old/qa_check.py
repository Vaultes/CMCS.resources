import sys
import os
import glob
from datetime import datetime
from collections import defaultdict

# ── CONFIG ──────────────────────────────────────────────────────────────────
# Pass a folder path as argument, or use default
input_folder = sys.argv[1] if len(sys.argv) > 1 else \
    '/Users/grace.hobson/Downloads/datamg/DrugUtilization/2txt'

txt_files = sorted(glob.glob(os.path.join(input_folder, '*.txt')))

if not txt_files:
    print(f"No .txt files found in {input_folder}")
    sys.exit(1)

# Expected 50 states + DC + national
EXPECTED_STATES = {
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN',
    'IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV',
    'NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN',
    'TX','UT','VT','VA','WA','WV','WI','WY','DC','XX'
}  # 52 total (50 states + DC + XX national)

# ── READ DATA ────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"QA CHECK: {input_folder}")
print(f"Files found: {len(txt_files)}")
print(f"{'='*60}\n")

years_quarters = defaultdict(set)
states_by_year = defaultdict(set)
redacted_count = 0
total_rows = 0
skipped_rows = 0

for filepath in txt_files:
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip().replace('\r', '')
            if not line:
                continue
            fields = line.split('|')
            if len(fields) < 12:
                skipped_rows += 1
                continue

            total_rows += 1
            state        = fields[1].strip()
            year_quarter = fields[5].strip()
            units        = fields[7].strip()

            year    = year_quarter[:4]
            quarter = year_quarter[4:] if len(year_quarter) > 4 else '?'

            years_quarters[year].add(quarter)
            states_by_year[year].add(state)

            if '*' in units:
                redacted_count += 1

print(f"Total rows read:    {total_rows:,}")
print(f"Skipped (bad rows): {skipped_rows:,}")
print(f"Redacted rows:      {redacted_count:,}")
print(f"Redacted %:         {redacted_count/total_rows*100:.1f}%\n")

# ── CHECK 1: YEARS ───────────────────────────────────────────────────────────
print(f"{'─'*60}")
print("CHECK 1: Years present in data")
print(f"{'─'*60}")
current_year = datetime.now().year
all_years = sorted(years_quarters.keys())
print(f"Years found: {', '.join(all_years)}")

all_quarters = set(q for qs in years_quarters.values() for q in qs)
is_q3_data = '3' in all_quarters and len(all_quarters) == 1

if is_q3_data:
    expected_years = [str(y) for y in range(1991, current_year + 1)]
    print(f"Q3 data detected — expected years: 1991–{current_year}")
else:
    expected_years = [str(y) for y in range(current_year - 5, current_year + 1)]
    print(f"Non-Q3 data — expected years: {current_year-5}–{current_year}")

missing_years = set(expected_years) - set(all_years)
extra_years   = set(all_years) - set(expected_years)

if missing_years:
    print(f"  ⚠️  MISSING years: {', '.join(sorted(missing_years))}")
else:
    print(f"  ✅ All expected years present")
if extra_years:
    print(f"  ℹ️  Extra years found: {', '.join(sorted(extra_years))}")

# ── CHECK 2: QUARTERS ────────────────────────────────────────────────────────
print(f"\n{'─'*60}")
print("CHECK 2: Quarters present per year")
print(f"{'─'*60}")
for year in sorted(years_quarters.keys()):
    quarters = sorted(years_quarters[year])
    print(f"  {year}: quarters {', '.join(quarters)}")

most_recent_year = max(years_quarters.keys())
found_quarters = sorted(years_quarters[most_recent_year])
print(f"\nMost recent year ({most_recent_year}) has quarters: {', '.join(found_quarters)}")
if found_quarters == sorted(found_quarters):
    print(f"  ✅ Quarters are sequential")
else:
    print(f"  ⚠️  Quarters may be out of order or missing")

# ── CHECK 3: REDACTION ───────────────────────────────────────────────────────
print(f"\n{'─'*60}")
print("CHECK 3: Redaction check")
print(f"{'─'*60}")
if redacted_count > 0:
    print(f"  ✅ Data has been redacted ({redacted_count:,} rows suppressed)")
else:
    print(f"  ⚠️  NO redacted rows found — check if suppression was applied")

# ── CHECK 4: STATES ──────────────────────────────────────────────────────────
print(f"\n{'─'*60}")
print(f"CHECK 4: States present for most recent year ({most_recent_year})")
print(f"{'─'*60}")
found_states   = states_by_year[most_recent_year]
missing_states = EXPECTED_STATES - found_states
extra_states   = found_states - EXPECTED_STATES

print(f"  Expected: {len(EXPECTED_STATES)} (50 states + DC + XX national)")
print(f"  Found:    {len(found_states)}")

if missing_states:
    print(f"  ⚠️  MISSING states: {', '.join(sorted(missing_states))}")
else:
    print(f"  ✅ All 52 expected states/territories present")
if extra_states:
    print(f"  ℹ️  Extra state codes found: {', '.join(sorted(extra_states))}")

# ── CHECK 5: FILE COUNT ──────────────────────────────────────────────────────
print(f"\n{'─'*60}")
print("CHECK 5: File count")
print(f"{'─'*60}")
print(f"  Files found: {len(txt_files)}")
if len(txt_files) == 52:
    print(f"  ✅ Expected 52 files")
else:
    print(f"  ⚠️  Expected 52 files, found {len(txt_files)}")

print(f"\n{'='*60}")
print("QA COMPLETE")
print(f"{'='*60}\n")
