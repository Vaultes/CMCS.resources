# -*- coding: utf-8 -*-
import pandas as pd
import os

# Read Excel
df = pd.read_excel('QuarterlyAMPPR.xlsx', header=None, dtype=str)
df.columns = ['Labeler Name', 'NDC', 'FDA Product Name', 'Status']

# Add Year and Quarter
df['Year'] = int(input("Enter year: "))
df['Quarter'] = int(input("Enter quarter: "))

# Append to existing CSV if it exists, otherwise create new
prod_file = 'DrugAMPReportingQuarterly-PROD.csv'
if os.path.exists(prod_file):
    df.to_csv(prod_file, mode='a', index=False, encoding='utf-8-sig', header=False)
    print(f"Appended {len(df):,} rows to {prod_file}")
else:
    df.to_csv(prod_file, index=False, encoding='utf-8-sig')
    print(f"Created {prod_file} with {len(df):,} rows")

# Report total row count
with open(prod_file, 'r', encoding='utf-8-sig') as f:
    total_rows = sum(1 for _ in f) - 1
print(f"Total rows in {prod_file}: {total_rows:,}")
