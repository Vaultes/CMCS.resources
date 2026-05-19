import argparse
import pathlib
import pandas

# Command line argument parsing
parser = argparse.ArgumentParser()

# Script Arguments:
#   - NADAC .xlsx file
#   - Production CSV file
#   - As of Date in YYYYMMDD format
parser.add_argument("-i","--input", help="Path to the NADAC Comparison Excel (.xlsx) file", type=pathlib.Path, required=True) 
parser.add_argument("-p","--prodExport", help="Path to the exported production CSV file", type=pathlib.Path, required=True) 
parser.add_argument("-sd","--startdate", help="Start Date in YYYYMMDD format", type=str, required=True)
parser.add_argument("-ed","--enddate", help="End Date in YYYYMMDD format", type=str, required=True)

args = parser.parse_args()

# Sanity Check
print("Parsing input file: ", args.input)
print("Parsing production export file: ", args.prodExport)
print("Using start date: ", args.startdate)
print("Using end date: ", args.enddate)

inputExists = args.input.is_file()
prodExportExists = args.prodExport.is_file()

if not inputExists:
    print("**** Error: Input file does not exist.")
    exit(1)

if not prodExportExists:
    print("**** Error: Production export file does not exist.")
    exit(1)

# As the parameter is required we should always have a valid path.
inputDataFrame = pandas.read_excel(args.input, skiprows=5)
prodDataFrame = pandas.read_csv(args.prodExport)

# Initial row counts
print("Input file contains ", len(inputDataFrame), " rows.")
print("Production export file contains ", len(prodDataFrame), " rows.")

inputRowCount = len(inputDataFrame)
prodRowCount = len(prodDataFrame)
expectedRowCount = inputRowCount + prodRowCount


inputDataFrame['NDC'] = inputDataFrame['NDC'].astype(str)
inputDataFrame['NDC'] = inputDataFrame['NDC'].str.rjust(11, "0")

inputDataFrame.rename({'Old NADAC\nPer Unit':'Old Nadac Per Unit','New NADAC\nPer Unit':'New NADAC Per Unit','New NADAC\nEffective\nDate':'Effective_Date'}, axis=1, inplace=True)

inputDataFrame['Percent Change'] = inputDataFrame['Percent Change']*100
inputDataFrame['Percent Change'] = inputDataFrame["Percent Change"].map('{:.2f}'.format)
inputDataFrame['Old Nadac Per Unit'] = inputDataFrame["Old Nadac Per Unit"].map('{:.5f}'.format)
inputDataFrame['New NADAC Per Unit'] = inputDataFrame["New NADAC Per Unit"].map('{:.5f}'.format)
inputDataFrame["Effective_Date"] = pandas.to_datetime(inputDataFrame.Effective_Date)

inputDataFrame.insert(7, "Start_Date", args.startdate)
inputDataFrame.insert(8, "End_Date", args.enddate)

inputDataFrame['Start_Date'] = pandas.to_datetime(inputDataFrame['Start_Date'], format='%Y%m%d').dt.strftime('%m/%d/%Y')
inputDataFrame['End_Date'] = pandas.to_datetime(inputDataFrame['End_Date'], format='%Y%m%d').dt.strftime('%m/%d/%Y')
inputDataFrame['Effective_Date'] = inputDataFrame['Effective_Date'].dt.strftime('%m/%d/%Y')

Column_Name = ['NDC Description','NDC','Old Nadac Per Unit','New NADAC Per Unit','Classification for Rate Setting','Percent Change','Primary Reason','Start_Date','End_Date','Effective_Date']
inputDataFrame = inputDataFrame.reindex(columns=Column_Name)
inputDataFrame.rename({'Start_Date':'Start Date','End_Date':'End Date','Effective_Date':'Effective Date'}, axis=1, inplace=True)

# Combine the files, and export
combinedDataFrame = pandas.concat([prodDataFrame, inputDataFrame], ignore_index=True)
combinedDataFrame.to_csv('NADAC_Weekly_Combined_File.csv', index=False)
combinedRowCount = len(combinedDataFrame)

# Output Results
print("Processing complete.")
print("Combined Output: ", combinedRowCount, " rows written to NADAC_Weekly_Combined_File.csv")
print("Expected Row Count: ", expectedRowCount, " Received: ", combinedRowCount, " Difference: ", expectedRowCount - combinedRowCount)