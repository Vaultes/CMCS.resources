import pandas
from collections import defaultdict
from datetime import datetime
import os

startTime = datetime.now()
print("Script started at: ", startTime)

# ── CONFIG ───────────────────────────────────────────────────────────────────
# Update these paths if your files are in a different location
BASE = os.path.dirname(os.path.abspath(__file__))

PRODUCTION_FILE = os.path.join(BASE, "aca-federal-upper-limits-06302026.csv")
NEW_FILE        = os.path.join(BASE, "aca-federal-upper-limits-0720260804.csv")
OUTPUT_FILE     = os.path.join(BASE, "aca-federal-upper-limits-0726.csv")
# ─────────────────────────────────────────────────────────────────────────────

# Check files exist
if not os.path.isfile(PRODUCTION_FILE):
    print("**** Error: Production file not found:", PRODUCTION_FILE)
    exit(1)

if not os.path.isfile(NEW_FILE):
    print("**** Error: New file not found:", NEW_FILE)
    exit(1)

# Load both files as strings to preserve formatting
dtype_dict_str = defaultdict(lambda: 'str')
prodDataFrame  = pandas.read_csv(PRODUCTION_FILE, dtype=dtype_dict_str, on_bad_lines='skip')
inputDataFrame = pandas.read_csv(NEW_FILE, dtype=dtype_dict_str)

print("Production file contains ", len(prodDataFrame), " rows.")
print("New file contains ", len(inputDataFrame), " rows.")
expectedRowCount = len(prodDataFrame) + len(inputDataFrame)

# Append new file onto production
combinedDataFrame = pandas.concat([prodDataFrame, inputDataFrame], ignore_index=True)

# Write output
combinedDataFrame.to_csv(OUTPUT_FILE, index=False)

print("Done. ", len(combinedDataFrame), " rows written to ", OUTPUT_FILE)
print("Expected: ", expectedRowCount, " Received: ", len(combinedDataFrame), " Difference: ", expectedRowCount - len(combinedDataFrame))

endTime = datetime.now()
print("Total processing time: ", endTime - startTime)
