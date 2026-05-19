# -*- coding: utf-8 -*-
import argparse
import pathlib
import pandas

# Command line argument parsing
parser = argparse.ArgumentParser()

# Script Arguments:
#   - AMP Quarterly .xlsx file
#   - Production CSV file
#   - As of Date in YYYYMMDD format
parser.add_argument("-i","--input", help="Path to the Weekly NADAC Excel (.xlsx) file", type=pathlib.Path, required=True) 
parser.add_argument("-p","--prodExport", help="Path to the exported production CSV file", type=pathlib.Path, required=True) 
parser.add_argument("-y","--year", help="Current year in YYYY format", type=str, required=True)
parser.add_argument("-m","--month", help="Current month in MM format", type=str, required=True)

args = parser.parse_args()

# Sanity Check
print("Parsing input file: ", args.input)
print("Parsing production export file: ", args.prodExport)
print("Using Year: ", args.year)
print("Using Month: ", args.month)

# Read Excel 
df = pandas.read_excel(args.input, skiprows = 4)
df['NDC-11'] = df['NDC-11'].astype(str)
df['NDC-11'] = df['NDC-11'].str.rjust(11, "0")

df.rename({'NDC-11':'NDC', 'Product Name':'FDA Product Name', 'AMP':'Status'}, axis = 1, inplace = True)

# Add month and year column  
df['Year'] = int(args.year)
df['Month'] = int(args.month)
df.head()

# Export as CSV
df.to_csv('DrugAMPReportingMonthly.csv', index=False, encoding = 'utf-8-sig')
