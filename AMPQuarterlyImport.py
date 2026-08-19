# -*- coding: utf-8 -*-
import pandas as pd
import glob
import os
import re
import sys

# --------------------------------------------------------------------------
# Find the quarterly xlsx file automatically, e.g. "2Q2026AMPPR-NRFile2Q2026.xlsx"
# (also tolerates browser download suffixes like " (1)")
# --------------------------------------------------------------------------
xlsx_candidates = [
    f for f in glob.glob('*AMPPR-NRFile*.xlsx')
    if re.match(r'^\dQ\d{4}AMPPR-NRFile\dQ\d{4}( \(\d+\))?\.xlsx$', f)
]
if not xlsx_candidates:
    all_xlsx = glob.glob('*.xlsx')
    sys.exit(
        "Could not find a file matching 'QQYYYYAMPPR-NRFileQQYYYY.xlsx' in this folder.\n"
        f"XLSX files found here: {all_xlsx if all_xlsx else '(none)'}\n"
        "Check that the quarterly file hasn't been renamed and is in the same folder as this script."
    )
if len(xlsx_candidates) > 1:
    sys.exit(f"Found more than one match for the quarterly xlsx pattern: {xlsx_candidates}. "
              f"Please remove the old one and try again.")
xlsx_file = xlsx_candidates[0]

# Pull quarter/year out of the xlsx filename (uses the leading "QQYYYY")
match = re.match(r'^(\d)Q(\d{4})AMPPR-NRFile', xlsx_file)
quarter, year = match.group(1), match.group(2)

# --------------------------------------------------------------------------
# Find the prod CSV automatically, e.g. "DrugAMPReportingQuarterly-1q2026.csv"
# (also tolerates browser download suffixes like " (1)")
# --------------------------------------------------------------------------
csv_candidates = [
    f for f in glob.glob('DrugAMPReportingQuarterly-*.csv')
    if re.match(r'^DrugAMPReportingQuarterly-\d[Qq]\d{4}( \(\d+\))?\.csv$', f)
]
if not csv_candidates:
    all_csvs = glob.glob('*.csv')
    sys.exit(
        "Could not find a file matching 'DrugAMPReportingQuarterly-QqYYYY.csv' in this folder.\n"
        f"CSV files found here: {all_csvs if all_csvs else '(none)'}\n"
        "Check that the prod CSV hasn't been renamed and is in the same folder as this script."
    )
if len(csv_candidates) > 1:
    sys.exit(f"Found more than one match for the prod CSV pattern: {csv_candidates}. "
              f"Please remove the old one and try again.")
source_file = csv_candidates[0]

print(f"Using xlsx file: {xlsx_file}")
print(f"Using prod CSV:  {source_file}")
print(f"Detected quarter/year: Q{quarter} {year}")

# --------------------------------------------------------------------------
# Read the xlsx file. Some quarterly files arrive with a real header row
# ("Labeler Name", "NDC-11", ...), others arrive with no header at all -
# detect which one this is rather than assuming.
# --------------------------------------------------------------------------
raw = pd.read_excel(xlsx_file, header=None, dtype=str)
first_row = [str(v).strip() for v in raw.iloc[0].tolist()]
header_like = {'labeler name', 'ndc', 'ndc-11', 'fda product name', 'amp', 'status'}
has_header_row = any(v.lower() in header_like for v in first_row)

if has_header_row:
    df = raw.iloc[1:].reset_index(drop=True)
else:
    df = raw

df.columns = ['Labeler Name', 'NDC', 'FDA Product Name', 'Status']

# Normalize header names/values just in case (handles NDC-11 -> NDC style
# variations if column order or naming ever shifts)
df.rename(columns={'NDC-11': 'NDC', 'AMP': 'Status'}, inplace=True)

# Add Year and Quarter, pulled from the xlsx filename itself
df['Year'] = int(year)
df['Quarter'] = int(quarter)

# --------------------------------------------------------------------------
# Combine with the existing prod CSV and write a new, separate output file
# --------------------------------------------------------------------------
output_file = f'DrugAMPReportingQuarterly-{quarter}Q{year}.csv'

if os.path.exists(source_file):
    existing_df = pd.read_csv(source_file, encoding='utf-8-sig', dtype=str, low_memory=False)
    combined_df = pd.concat([existing_df, df], ignore_index=True)
    combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Combined {len(existing_df):,} existing rows with {len(df):,} new rows -> {output_file}")
else:
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"{source_file} not found. Created {output_file} with {len(df):,} rows")

# Report total row count
with open(output_file, 'r', encoding='utf-8-sig') as f:
    total_rows = sum(1 for _ in f) - 1
print(f"Total rows in {output_file}: {total_rows:,}")
