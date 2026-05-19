import argparse
import pathlib
import pandas

# Command line argument parsing
parser = argparse.ArgumentParser()

# Script Arguments:
#   - NADAC .xlsx file
#   - Production CSV file
#   - As of Date in YYYYMMDD format
parser.add_argument("-i","--input", help="Path to the Weekly NADAC Excel (.xlsx) file", type=pathlib.Path, required=True) 
parser.add_argument("-p","--prodExport", help="Path to the exported production CSV file", type=pathlib.Path, required=True) 
parser.add_argument("-d","--asofdate", help="As of Date in YYYYMMDD format", type=str, required=True)

args = parser.parse_args()

# Sanity Check
print("Parsing input file: ", args.input)
print("Parsing production export file: ", args.prodExport)
print("Using As of Date: ", args.asofdate)

inputExists = args.input.is_file()
prodExportExists = args.prodExport.is_file()

if not inputExists:
    print("**** Error: Input file does not exist.")
    exit(1)

if not prodExportExists:
    print("**** Error: Production export file does not exist.")
    exit(1)

# As the parameter is required we should always have a valid path.
#   TODO: We should likely check the file exists.
#   We skip the top three rows as they're the title, and two blank rows.
inputDataFrame = pandas.read_excel(args.input, skiprows=3)
prodDataFrame = pandas.read_csv(args.prodExport)

# Initial row counts
print("Input file contains ", len(inputDataFrame), " rows.")
print("Production export file contains ", len(prodDataFrame), " rows.")

inputRowCount = len(inputDataFrame)
prodRowCount = len(prodDataFrame)
expectedRowCount = inputRowCount + prodRowCount

# Select the "NDC" column, convert the values to a string, 
# and ensure they're all 11 characters long by padding with leading zeros as needed.
inputDataFrame['NDC'] = inputDataFrame['NDC'].astype(str)
inputDataFrame['NDC'] = inputDataFrame['NDC'].str.rjust(11, "0")

# Standardize the column names by removing newlines and replacing them with underscores.
inputDataFrame.rename({
    'NADAC\nPer Unit':'NADAC_Per_Unit',
    'Effective\nDate':'Effective_Date',
    'Pricing\nUnit':'Pricing_Unit',
    'Pharmacy\nType\nIndicator':'Pharmacy_Type_Indicator',
    'Explanation\nCode':'Explanation_Code',
    'Classification\nfor Rate\nSetting':'Classification_for_Rate_Setting',
    'Corresponding\nGeneric Drug\nNADAC\nPer Unit':'Corresponding_Generic_Drug_NADAC_Per_Unit',
    'Corresponding\nGeneric Drug\nEffective\nDate':'Corresponding_Generic_Drug_Effective_Date'}, 
    axis=1, inplace=True)

# Select the "NADAC_Per_Unit" column and format it to have 5 decimal places.
inputDataFrame['NADAC_Per_Unit'] = inputDataFrame["NADAC_Per_Unit"].map('{:.5f}'.format)

# Read the effective date, convert to a date, format, and replace.
#   Note: This field is not always populated.
inputDataFrame["Corresponding_Generic_Drug_Effective_Date"] = \
    pandas.to_datetime(inputDataFrame.Corresponding_Generic_Drug_Effective_Date).dt.strftime('%m/%d/%Y')

# Add a new column for the "As of Date" using the value provided in the command line argument.
inputDataFrame.insert(11, "As_of_Date", args.asofdate)

# Format the "Effective_Date" and "As_of_Date" columns to match the expected output format.
inputDataFrame['Effective_Date'] = inputDataFrame['Effective_Date'].dt.strftime('%m/%d/%Y')
inputDataFrame['As_of_Date'] = pandas.to_datetime(inputDataFrame['As_of_Date'], format='%Y%m%d').dt.strftime('%m/%d/%Y')

# Rename the "As_of_Date" column to "As of Date" to match the expected output.
#   Not sure why we do this after setting the value as As_of_Date above, but we'll keep it consistent with the original script.
inputDataFrame.rename({"As_of_Date":"As of Date"}, axis=1, inplace=True)

# Combine the files, and export
combinedDataFrame = pandas.concat([prodDataFrame, inputDataFrame], ignore_index=True)
combinedDataFrame.to_csv('NADAC_Weekly_Combined_File.csv', index=False)
combinedRowCount = len(combinedDataFrame)

# Output Results
print("Processing complete.")
print("Combined Output: ", combinedRowCount, " rows written to NADAC_Weekly_Combined_File.csv")
print("Expected Row Count: ", expectedRowCount, " Received: ", combinedRowCount, " Difference: ", expectedRowCount - combinedRowCount)