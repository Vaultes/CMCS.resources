import argparse
import pathlib
import pandas
from collections import defaultdict
from Shared.ValidateDataFrame import validateDataFrame
from NADAC.weekly.schema import NADACWeeklySchema

# Command line argument parsing
parser = argparse.ArgumentParser()

# Script Arguments:
#   - NADAC .xlsx file
#   - Production CSV file
#   - As of Date in YYYYMMDD format
parser.add_argument("-i","--input", help="Path to the Weekly NADAC Excel (.xlsx) file", type=pathlib.Path, required=True) 
parser.add_argument("-p","--prodExport", help="Path to the exported production CSV file", type=pathlib.Path, required=True) 
parser.add_argument("-d","--asofdate", help="As of Date in MM/DD/YYYY format", type=str, required=True)

args = parser.parse_args()

# Sanity Check
print("Parsing input file: ", args.input)
print("Parsing production export file: ", args.prodExport)
print("Using As of Date: ", args.asofdate)

# Check if the date format is correct for the As of Date. We expect MM/DD/YYYY.
try:
    pandas.to_datetime(args.asofdate, format='%m/%d/%Y')
except ValueError:
    print("**** Error: As of Date is not in the correct format. Please use MM/DD/YYYY.")
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

# As the parameter is required we should always have a valid path.
#   We skip the top three rows as they're the title, and two blank rows.
inputDataFrame = pandas.read_excel(args.input, skiprows=3)

# Load the production exported CSV. Load all columns as a string 'str'.
dtype_dict_str = defaultdict(lambda: 'str')
prodDataFrame = pandas.read_csv(args.prodExport, dtype=dtype_dict_str)

# Initial row counts
print("Input file contains ", len(inputDataFrame), " rows.")
print("Production export file contains ", len(prodDataFrame), " rows.")

inputRowCount = len(inputDataFrame)
prodRowCount = len(prodDataFrame)
expectedRowCount = inputRowCount + prodRowCount

# Input .xlsx columns need to be converted to match the columns in the production export.
inputDataFrame.rename({
    'NADAC\nPer Unit':'NADAC Per Unit',
    'Effective\nDate':'Effective Date',
    'Pricing\nUnit':'Pricing Unit',
    'Pharmacy\nType\nIndicator':'Pharmacy Type Indicator',
    'Explanation\nCode':'Explanation Code',
    'Classification\nfor Rate\nSetting':'Classification for Rate Setting',
    'Corresponding\nGeneric Drug\nNADAC\nPer Unit':'Corresponding Generic Drug NADAC Per Unit',
    'Corresponding\nGeneric Drug\nEffective\nDate':'Corresponding Generic Drug Effective Date'}, 
    axis=1, inplace=True)

# Add a new column to the inputDataFrame for the "As of Date" using the value provided in the command line argument.
# Format the "As of Date" to MM/DD/YYYY inline with the Data Dictionary specifications.
inputDataFrame.insert(11, "As of Date", args.asofdate)

# Combine the new file and production export.
combinedDataFrame = pandas.concat([prodDataFrame, inputDataFrame], ignore_index=True)
combinedRowCount = len(combinedDataFrame)

# Apply column formatting inline with the Data Dictionary specifications:
# NDC: 11 characters, padding with leading zeros as needed.
combinedDataFrame['NDC'] = combinedDataFrame['NDC'].astype(str)
combinedDataFrame['NDC'] = combinedDataFrame['NDC'].str.rjust(11, "0")

# Set Column Types:
combinedDataFrame['Corresponding Generic Drug NADAC Per Unit'] = combinedDataFrame['Corresponding Generic Drug NADAC Per Unit'].astype(float)

# NADAC Per Unit: 5 decimal places.
combinedDataFrame['NADAC Per Unit'] = combinedDataFrame['NADAC Per Unit'].astype(float)
combinedDataFrame['NADAC Per Unit'] = combinedDataFrame["NADAC Per Unit"].map('{:.5f}'.format)

# Corresponding Generic Drug Effective Date: Format to MM/DD/YYYY.
combinedDataFrame['Corresponding Generic Drug Effective Date'] = \
    pandas.to_datetime(combinedDataFrame['Corresponding Generic Drug Effective Date'], format='mixed').dt.strftime('%m/%d/%Y')

# Effective Date: Format to MM/DD/YYYY.
combinedDataFrame["Effective Date"] = \
    pandas.to_datetime(combinedDataFrame["Effective Date"], format='mixed').dt.strftime('%m/%d/%Y')

# As of Date: Format to MM/DD/YYYY.
combinedDataFrame['As of Date'] = \
    pandas.to_datetime(combinedDataFrame['As of Date'], format='mixed').dt.strftime('%m/%d/%Y')

validateDataFrame(combinedDataFrame, NADACWeeklySchema)

# Output combined file
combinedDataFrame.to_csv('NADAC_Weekly_Combined_File.csv', index=False)

# Output Results
print("Processing complete.")
print("Combined Output: ", combinedRowCount, " rows written to NADAC_Weekly_Combined_File.csv")
print("Expected Row Count: ", expectedRowCount, " Received: ", combinedRowCount, " Difference: ", expectedRowCount - combinedRowCount)