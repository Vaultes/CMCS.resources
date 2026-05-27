# -*- coding: utf-8 -*-
import argparse
from collections import defaultdict
from datetime import datetime
import pathlib
import pandas

from AMP.monthly.schema import AMPMonthlySchema
from Shared.ValidateDataFrame import validateDataFrame

startTime = datetime.now()
print("Script started at: ", startTime)

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
parser.add_argument("-v","--verbose", help="Increase output verbosity", action="store_true", required=False, default=False)

args = parser.parse_args()

# Verify the year format.
try:
    pandas.to_datetime(args.year, format='%Y')
except ValueError:
    print("**** Error: Year is not in the correct format. Please use YYYY.")
    exit(1)

# Verify the month format.
try:
    pandas.to_datetime(args.month, format='%m')
except ValueError:
    print("**** Error: Month is not in the correct format. Please use MM.")
    exit(1)

# Check the files exist before we attempt to read them.
inputExists = args.input.is_file()
prodExportExists = args.prodExport.is_file()

if not inputExists:
    print("**** Error: Input file does not exist.")
    exit(1)

if not prodExportExists:
    print("**** Error: Production export file does not exist.")
    exit(1)

# Sanity Check
print("Parsing input file: ", args.input)
print("Parsing production export file: ", args.prodExport)
print("Using Year: ", args.year)
print("Using Month: ", args.month)

# Read Excel 
inputDataFrame = pandas.read_excel(args.input, skiprows = 4)

# Load the production exported CSV. Load all columns as a string 'str'.
dtype_dict_str = defaultdict(lambda: 'str')
prodDataFrame = pandas.read_csv(args.prodExport, dtype=dtype_dict_str)

# Initial row counts
print("Input file contains ", len(inputDataFrame), " rows.")
print("Production export file contains ", len(prodDataFrame), " rows.")

inputRowCount = len(inputDataFrame)
prodRowCount = len(prodDataFrame)
expectedRowCount = inputRowCount + prodRowCount

inputDataFrame['NDC-11'] = inputDataFrame['NDC-11'].astype(str)

inputDataFrame.rename({'NDC-11':'NDC', 'Product Name':'FDA Product Name', 'AMP':'Status'}, axis = 1, inplace = True)

# Add month and year column  
inputDataFrame['Year'] = int(args.year)
inputDataFrame['Month'] = int(args.month)
inputDataFrame.head()

# Combine the new file and production export.
combinedDataFrame = pandas.concat([prodDataFrame, inputDataFrame], ignore_index=True)
combinedDataFrame['NDC'] = combinedDataFrame['NDC'].str.rjust(11, "0")
combinedDataFrame['Month'] = combinedDataFrame['Month'].astype(str)
combinedDataFrame['Year'] = combinedDataFrame['Year'].astype(str)

combinedRowCount = len(combinedDataFrame)

validateDataFrame(combinedDataFrame, AMPMonthlySchema, args.verbose)

# Export as CSV
combinedDataFrame.to_csv('AMP_Monthly_Combined_File.csv', index=False, encoding = 'utf-8-sig')

# Output Results
print("Processing complete.")
print("Combined Output: ", combinedRowCount, " rows written to AMP_Monthly_Combined_File.csv")
print("Expected Row Count: ", expectedRowCount, " Received: ", combinedRowCount, " Difference: ", expectedRowCount - combinedRowCount)

endTime = datetime.now()
print("Script finished at: ", endTime)
print("Total processing time: ", endTime - startTime)