# -*- coding: utf-8 -*-
import pandas as pd
import glob
import os
import re
import sys

# --------------------------------------------------------------------------
# Find the monthly xlsx file automatically, e.g. "062026_MonthlyAMP_RNR.xlsx"
# --------------------------------------------------------------------------
xlsx_candidates = glob.glob('*_MonthlyAMP_RNR.xlsx')
if not xlsx_candidates:
    sys.exit("Could not find a file matching '*_MonthlyAMP_RNR.xlsx' in this folder.")
if len(xlsx_candidates) > 1:
    sys.exit(f"Found more than one match for '*_MonthlyAMP_RNR.xlsx': {xlsx_candidates}. "
              f"Please remove the old one and try again.")
xlsx_file = xlsx_candidates[0]

# Pull the MMYYYY prefix out of the xlsx filename
match = re.match(r'^(\d{2})(\d{4})_MonthlyAMP_RNR\.xlsx$', xlsx_file)
if not match:
    sys.exit(f"'{xlsx_file}' doesn't match the expected 'MMYYYY_MonthlyAMP_RNR.xlsx' naming pattern.")
month, year = match.group(1), match.group(2)

# --------------------------------------------------------------------------
# Find the prod CSV automatically, e.g. "DrugAMPReportingMonthly062026.csv"
# --------------------------------------------------------------------------
csv_candidates = glob.glob('DrugAMPReportingMonthly??????.csv')
if not csv_candidates:
    sys.exit("Could not find a file matching 'DrugAMPReportingMonthlyMMYYYY.csv' in this folder.")
if len(csv_candidates) > 1:
    sys.exit(f"Found more than one match for 'DrugAMPReportingMonthlyMMYYYY.csv': {csv_candidates}. "
              f"Please remove the old one and try again.")
source_file = csv_candidates[0]

print(f"Using xlsx file: {xlsx_file}")
print(f"Using prod CSV:  {source_file}")
print(f"Detected month/year: {month}/{year}")

# --------------------------------------------------------------------------
# Read and clean up the xlsx file
# --------------------------------------------------------------------------
df = pd.read_excel(xlsx_file, skiprows=0)

# Normalize header names to match the prod CSV, regardless of how the
# monthly file happens to label them (e.g. "NDC-11" -> "NDC", "AMP" -> "Status")
df.rename(columns={
    'NDC-11': 'NDC',
    'AMP': 'Status',
}, inplace=True)

# Add month and year columns, pulled from the xlsx filename itself
df['Year'] = int(year)
df['Month'] = int(month)

# Reorder columns to match existing CSV
df = df[['Labeler Name', 'NDC', 'FDA Product Name', 'Status', 'Year', 'Month']]

# --------------------------------------------------------------------------
# Combine with the existing prod CSV and write a new, separate output file
# --------------------------------------------------------------------------
output_file = f'DrugAMPReportingMonthly{month}{year}.csv'

if os.path.exists(source_file):
    existing_df = pd.read_csv(source_file, encoding='utf-8-sig')
    combined_df = pd.concat([existing_df, df], ignore_index=True)
    combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Combined {len(existing_df)} existing rows with {len(df)} new rows -> {output_file}")
else:
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"{source_file} not found. Created {output_file} with {len(df)} rows")
