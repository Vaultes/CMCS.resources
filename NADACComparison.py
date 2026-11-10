import argparse
from collections import defaultdict
from datetime import datetime
import pathlib
import pandas
from Shared.ValidateDataFrame import validateDataFrame
from NADAC.comparison.schema import NADACComparisonSchema
from Shared.Prompts import prompt_for_file, prompt_for_date, prompt_for_output

startTime = datetime.now()
print("Script started at: ", startTime)

# Command line argument parsing
parser = argparse.ArgumentParser()

# Script Arguments:
#   - NADAC .xlsx file
#   - Production CSV file
#   - As of Date in YYYYMMDD format
parser.add_argument("-i","--input", help="Path to the NADAC Comparison Excel (.xlsx) file", type=pathlib.Path) 
parser.add_argument("-p","--prodExport", help="Path to the exported production CSV file", type=pathlib.Path) 
parser.add_argument("-sd","--startdate", help="Start Date in MM/DD/YYYY format", type=str)
parser.add_argument("-ed","--enddate", help="End Date in MM/DD/YYYY format", type=str)
parser.add_argument("-o","--output", help="Path for the combined output CSV file", type=pathlib.Path)
parser.add_argument("-v","--verbose", help="Increase output verbosity", action="store_true", required=False, default=False)

args = parser.parse_args()

# If any required inputs are missing, we're in "interactive" mode and will prompt for them
interactive = (args.input is None or args.prodExport is None
               or args.startdate is None or args.enddate is None)

# Prompt for anything not provided on the command line
if args.input is None:
    args.input = prompt_for_file("NADAC Comparison Excel file (.xlsx)", ".xlsx")
if args.prodExport is None:
    args.prodExport = prompt_for_file("Production export file (.csv)", ".csv")
if args.startdate is None:
    args.startdate = prompt_for_date("Start Date")
if args.enddate is None:
    args.enddate = prompt_for_date("End Date")

# Output location: ask only in interactive mode, otherwise use the default
DEFAULT_OUTPUT = "NADAC_Comparison_Combined_File.csv"
if args.output is None:
    if interactive:
        args.output = prompt_for_output(DEFAULT_OUTPUT)
    else:
        args.output = pathlib.Path(DEFAULT_OUTPUT)

# Sanity Check
print("Parsing input file: ", args.input)
print("Parsing production export file: ", args.prodExport)
print("Using start date: ", args.startdate)
print("Using end date: ", args.enddate)

# Check if the date format is correct for the Start Date. We expect MM/DD/YYYY.
try:
    pandas.to_datetime(args.startdate, format='%m/%d/%Y')
except ValueError:
    print("**** Error: Start Date is not in the correct format. Please use MM/DD/YYYY.")
    exit(1)

# Check if the date format is correct for the End Date. We expect MM/DD/YYYY.
try:
    pandas.to_datetime(args.enddate, format='%m/%d/%Y')
except ValueError:
    print("**** Error: End Date is not in the correct format. Please use MM/DD/YYYY.")
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

# Load the comparison .xlsx file. Skip the top five rows as they're the title, and four blank rows.
inputDataFrame = pandas.read_excel(args.input, skiprows=5)

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
    'Old NADAC\nPer Unit':'Old NADAC Per Unit',
    'New NADAC\nPer Unit':'New NADAC Per Unit',
    'New NADAC\nEffective\nDate':'Effective Date'
    }, axis=1, inplace=True)

# Add new columns for the Start Date and End Date using the values provided in the command line arguments.
inputDataFrame.insert(7, "Start Date", args.startdate)
inputDataFrame.insert(8, "End Date", args.enddate)

inputDataFrame['Percent Change'] = inputDataFrame['Percent Change'].astype(float)
inputDataFrame['Percent Change'] = inputDataFrame['Percent Change']*100
inputDataFrame['Percent Change'] = inputDataFrame["Percent Change"].map('{:.2f}'.format)

# Reorder the onput columns to match the expected output format.
Column_Name = ['NDC Description','NDC','Old NADAC Per Unit','New NADAC Per Unit','Classification for Rate Setting','Percent Change','Primary Reason','Start Date','End Date','Effective Date']
inputDataFrame = inputDataFrame.reindex(columns=Column_Name)

# Combine the new file and production export.
combinedDataFrame = pandas.concat([prodDataFrame, inputDataFrame], ignore_index=True)
combinedRowCount = len(combinedDataFrame)

combinedDataFrame['NDC'] = combinedDataFrame['NDC'].astype(str)
combinedDataFrame['NDC'] = combinedDataFrame['NDC'].str.rjust(11, "0")

combinedDataFrame['Percent Change'] = combinedDataFrame['Percent Change'].astype(float)
combinedDataFrame['Percent Change'] = combinedDataFrame["Percent Change"].map('{:.2f}'.format)

combinedDataFrame['Old NADAC Per Unit'] = combinedDataFrame['Old NADAC Per Unit'].astype(float)
combinedDataFrame['Old NADAC Per Unit'] = combinedDataFrame["Old NADAC Per Unit"].map('{:.5f}'.format)

combinedDataFrame['New NADAC Per Unit'] = combinedDataFrame['New NADAC Per Unit'].astype(float)
combinedDataFrame['New NADAC Per Unit'] = combinedDataFrame["New NADAC Per Unit"].map('{:.5f}'.format)

combinedDataFrame['Start Date'] = pandas.to_datetime(combinedDataFrame['Start Date'], format='mixed').dt.strftime('%m/%d/%Y')
combinedDataFrame['End Date'] = pandas.to_datetime(combinedDataFrame['End Date'], format='mixed').dt.strftime('%m/%d/%Y')
combinedDataFrame["Effective Date"] = pandas.to_datetime(combinedDataFrame["Effective Date"], format='mixed').dt.strftime('%m/%d/%Y')

validateDataFrame(combinedDataFrame, NADACComparisonSchema, args.verbose)

# Export the combined and cormatted file
combinedDataFrame.to_csv(args.output, index=False)

# Output Results
print("Processing complete.")
print("Combined Output: ", combinedRowCount, " rows written to ", args.output)
print("Expected Row Count: ", expectedRowCount, " Received: ", combinedRowCount, " Difference: ", expectedRowCount - combinedRowCount)

endTime = datetime.now()
print("Script finished at: ", endTime)
print("Total processing time: ", endTime - startTime)