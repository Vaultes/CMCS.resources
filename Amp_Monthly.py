# -*- coding: utf-8 -*-
import pandas as pd
import os

# Read Excel
df = pd.read_excel('AmpMonthly.xlsx', skiprows=0)

# Rename AMP to Status
df.rename(columns={'AMP': 'Status'}, inplace=True)

# Add month and year columns
df['Year'] = int(input("Enter year: "))
df['Month'] = int(input('Enter month: '))

# Reorder columns to match existing CSV
df = df[['Labeler Name', 'NDC', 'FDA Product Name', 'Status', 'Year', 'Month']]

# Append to existing CSV if it exists, otherwise create new
output_file = 'DrugAMPReportingMonthly.csv'
if os.path.exists(output_file):
    df.to_csv(output_file, mode='a', index=False, encoding='utf-8-sig', header=False)
    print(f"Appended {len(df)} rows to {output_file}")
else:
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Created {output_file} with {len(df)} rows")
