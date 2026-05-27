import argparse
from datetime import datetime
import pathlib
import pandas
from collections import defaultdict
from NADAC.firstTime.schema import NADACFirstTimeSchema
from Shared.ValidateDataFrame import validateDataFrame

startTime = datetime.now()
print("Script started at: ", startTime)

# Command line argument parsing
parser = argparse.ArgumentParser()

# Script Arguments:
#   - NADAC .xlsx file
#   - Production CSV file
#   - As of Date in YYYYMMDD format
parser.add_argument("-i","--input", help="Path to the Weekly NADAC Excel (.xlsx) file", type=pathlib.Path, required=True) 
parser.add_argument("-p","--prodExport", help="Path to the exported production CSV file", type=pathlib.Path, required=True) 
parser.add_argument("-d","--asofdate", help="As of Date in MM/DD/YYYY format", type=str, required=True)
parser.add_argument("-v","--verbose", help="Increase output verbosity", action="store_true", required=False, default=False)

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

# Load the new XLSX file
inputDataFrame = pandas.read_excel(args.input)

# Load the production exported CSV. Load all columns as a string 'str'.
dtype_dict_str = defaultdict(lambda: 'str')
prodDataFrame = pandas.read_csv(args.prodExport, dtype=dtype_dict_str)

# Initial row counts
print("Input file contains ", len(inputDataFrame), " rows.")
print("Production export file contains ", len(prodDataFrame), " rows.")

inputRowCount = len(inputDataFrame)
prodRowCount = len(prodDataFrame)
expectedRowCount = inputRowCount + prodRowCount

inputDataFrame.rename({'Brief Indication Description':'Brief Indication/Description', 'Number of Active NDCs in Rate Group':'Number of Active NDCs Within The RateGroup That Are On The Covered Outpatient Drug File'}, axis = 1, inplace = True)
inputDataFrame['As of Date'] = inputDataFrame['As of Date'].dt.strftime('%m/%d/%Y')

# Combine the new file and production export.
combinedDataFrame = pandas.concat([prodDataFrame, inputDataFrame], ignore_index=True)
combinedRowCount = len(combinedDataFrame)

# As of Date: Format to MM/DD/YYYY.
combinedDataFrame['As of Date'] = \
    pandas.to_datetime(combinedDataFrame['As of Date'], format='mixed').dt.strftime('%m/%d/%Y')

# Column Data Types
combinedDataFrame['Package Size'] = combinedDataFrame['Package Size'].astype(str)

validateDataFrame(combinedDataFrame, NADACFirstTimeSchema, args.verbose)

# Output combined file
combinedDataFrame.to_csv('NADAC_First_Time_Combined_File.csv', index=False)

# Output Results
print("Processing complete.")
print("Combined Output: ", combinedRowCount, " rows written to NADAC_First_Time_Combined_File.csv")
print("Expected Row Count: ", expectedRowCount, " Received: ", combinedRowCount, " Difference: ", expectedRowCount - combinedRowCount)

endTime = datetime.now()
print("Script finished at: ", endTime)
print("Total processing time: ", endTime - startTime)