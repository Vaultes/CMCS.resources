# -*- coding: utf-8 -*-
"""
First Time NADAC Rates - Combine Script
=========================================

Combines the newly published "First Time NADAC" Excel file with the
existing production export CSV, and writes a single combined CSV.

USAGE (Windows command prompt):

    Just run it - no arguments needed:

        python first_time_nadac_rates.py

    Put the newly posted NADAC Excel file AND the production export CSV in
    the same folder as this script (whatever they're named) and run the
    command above. The script automatically finds both files for you:

      - The new NADAC Excel file arrives with a long, date-stamped name
        (e.g. "20260819_First_Time_NADACs_Posting_-_August_2026.xlsx").
        The script picks the .xlsx file in the folder automatically.
      - The production export CSV is auto-detected too: the script picks
        the .csv file in the folder that isn't one of its own previous
        output files.
      - If more than one candidate is found for either file, it picks the
        most recently modified one and tells you which file it chose, so
        you can double check that's the right one.

    You can still override either file explicitly if you ever need to:

    -i / --input        (optional) Path to the new NADAC Excel (.xlsx) file.
                          If omitted, auto-detected from the current folder.
    -p / --prodExport    (optional) Path to the production export (.csv) file.
                          If omitted, auto-detected from the current folder.
    -o / --output        (optional) Output CSV filename.
                          Defaults to "first-time-nadac-MMDDYYYY.csv"
    -x / --xsv            (optional) Path to xsv.exe, if not on your PATH.
"""

import argparse
import pathlib
import shutil
import subprocess
import sys
from datetime import datetime

import pandas as pd

# ---------------------------------------------------------------------------
# Defaults - edit these if you want to hardcode either file instead of
# relying on auto-detection.
# ---------------------------------------------------------------------------
DEFAULT_INPUT = None  # leave as None to auto-detect the .xlsx file
DEFAULT_PROD_EXPORT = None  # leave as None to auto-detect the .csv file

# Prefix used for this script's own output files, so auto-detection knows
# to ignore them when looking for the production export CSV.
OUTPUT_FILENAME_PREFIX = "first-time-nadac-"


def find_input_excel(search_dir: pathlib.Path) -> pathlib.Path:
    """
    Auto-detect the newly posted NADAC Excel file in search_dir, since it
    arrives with a long, date-stamped name that changes every time
    (e.g. "20260819_First_Time_NADACs_Posting_-_August_2026.xlsx").

    Ignores Excel lock files (starting with '~$'). If multiple .xlsx files
    are found, picks the most recently modified one.
    """
    candidates = [
        f for f in search_dir.glob("*.xlsx")
        if not f.name.startswith("~$")
    ]
    if not candidates:
        print(f"**** Error: No .xlsx file found in {search_dir.resolve()}.")
        print("     Place the newly posted NADAC Excel file in this folder, "
              "or specify it explicitly with -i <path>.")
        sys.exit(1)

    if len(candidates) > 1:
        candidates.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        print(f"Note: multiple .xlsx files found in {search_dir.resolve()}:")
        for f in candidates:
            print(f"    {f.name}")
        print(f"Using the most recently modified one: {candidates[0].name}")
        print("(If that's not the right file, re-run with -i <path> to specify it directly.)")

    return candidates[0]


def find_prod_csv(search_dir: pathlib.Path) -> pathlib.Path:
    """
    Auto-detect the production export CSV in search_dir. The production
    export is always named like "nadac_first_time_07232026.csv" or
    "nadac_first_time_07232026 (1).csv" - the date changes each time, and
    a " (1)", " (2)", etc. suffix may be added by the browser if the file
    was downloaded more than once.

    Prefers files whose name starts with "nadac_first_time" (case
    insensitive). Falls back to any other .csv file in the folder (that
    isn't one of this script's own output files) if no such match is found.

    If multiple candidates are found, picks the most recently modified one.
    """
    all_csvs = [
        f for f in search_dir.glob("*.csv")
        if not f.name.startswith(OUTPUT_FILENAME_PREFIX)
    ]

    candidates = [f for f in all_csvs if f.stem.lower().startswith("nadac_first_time")]

    if not candidates:
        # Fall back to any other CSV in the folder, in case the naming
        # pattern changes in the future.
        candidates = all_csvs

    if not candidates:
        print(f"**** Error: No production export .csv file found in {search_dir.resolve()}.")
        print("     Place the production export CSV (e.g. \"nadac_first_time_07232026.csv\") "
              "in this folder, or specify it explicitly with -p <path>.")
        sys.exit(1)

    if len(candidates) > 1:
        candidates.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        print(f"Note: multiple candidate .csv files found in {search_dir.resolve()}:")
        for f in candidates:
            print(f"    {f.name}")
        print(f"Using the most recently modified one: {candidates[0].name}")
        print("(If that's not the right file, re-run with -p <path> to specify it directly.)")

    return candidates[0]


def parse_args():
    parser = argparse.ArgumentParser(description="Combine new NADAC First Time rates with production export.")
    parser.add_argument(
        "-i", "--input",
        type=pathlib.Path,
        default=pathlib.Path(DEFAULT_INPUT) if DEFAULT_INPUT else None,
        help="Path to the new NADAC Excel (.xlsx) file. If omitted, auto-detected from the current folder.",
    )
    parser.add_argument(
        "-p", "--prodExport",
        type=pathlib.Path,
        default=pathlib.Path(DEFAULT_PROD_EXPORT) if DEFAULT_PROD_EXPORT else None,
        help="Path to the existing production export (.csv) file. If omitted, auto-detected from the current folder.",
    )
    parser.add_argument(
        "-o", "--output",
        type=pathlib.Path,
        default=None,
        help="Output CSV filename (default: 'first-time-nadac-MMDDYYYY.csv')",
    )
    parser.add_argument(
        "-x", "--xsv",
        type=pathlib.Path,
        default=None,
        help="Path to xsv.exe, if it's not already on your PATH",
    )
    return parser.parse_args()


def main():
    startTime = datetime.now()
    print("Script started at:", startTime)

    args = parse_args()

    # -----------------------------------------------------------------
    # Auto-detect the input Excel file if one wasn't specified, since it
    # arrives with a long, date-stamped name that changes every time.
    # -----------------------------------------------------------------
    if args.input is None:
        args.input = find_input_excel(pathlib.Path.cwd())

    # -----------------------------------------------------------------
    # Auto-detect the production export CSV if one wasn't specified.
    # -----------------------------------------------------------------
    if args.prodExport is None:
        args.prodExport = find_prod_csv(pathlib.Path.cwd())

    # -----------------------------------------------------------------
    # Validate inputs exist
    # -----------------------------------------------------------------
    if not args.input.is_file():
        print(f"**** Error: Input file not found: {args.input}")
        sys.exit(1)

    if not args.prodExport.is_file():
        print(f"**** Error: Production export file not found: {args.prodExport}")
        sys.exit(1)

    print("New NADAC file:      ", args.input)
    print("Production export:   ", args.prodExport)

    # -----------------------------------------------------------------
    # Load new NADAC Excel file
    # -----------------------------------------------------------------
    newDataFrame = pd.read_excel(args.input)

    # Rename columns to match production schema
    newDataFrame.rename(
        {
            "Brief Indication Description": "Brief Indication/Description",
            "Number of Active NDCs in Rate Group":
                "Number of Active NDCs Within The RateGroup That Are On The Covered Outpatient Drug File",
        },
        axis=1,
        inplace=True,
    )

    # Format As of Date as MM/DD/YYYY (source column is a real datetime)
    newDataFrame["As of Date"] = pd.to_datetime(newDataFrame["As of Date"]).dt.strftime("%m/%d/%Y")

    # -----------------------------------------------------------------
    # Load production export CSV (everything as string to avoid dtype surprises)
    # -----------------------------------------------------------------
    prodDataFrame = pd.read_csv(args.prodExport, dtype=str)

    # Normalize As of Date formatting in case of mixed formats (e.g. "9/25/20")
    prodDataFrame["As of Date"] = pd.to_datetime(
        prodDataFrame["As of Date"], format="mixed"
    ).dt.strftime("%m/%d/%Y")

    newRowCount = len(newDataFrame)
    prodRowCount = len(prodDataFrame)
    expectedRowCount = newRowCount + prodRowCount

    print(f"New file contains:        {newRowCount} rows")
    print(f"Production file contains: {prodRowCount} rows")

    # -----------------------------------------------------------------
    # Combine
    # -----------------------------------------------------------------
    missing_in_new = set(prodDataFrame.columns) - set(newDataFrame.columns)
    missing_in_prod = set(newDataFrame.columns) - set(prodDataFrame.columns)
    if missing_in_new or missing_in_prod:
        print("**** Warning: column mismatch between files.")
        if missing_in_new:
            print("    Columns in production but not in new file:", missing_in_new)
        if missing_in_prod:
            print("    Columns in new file but not in production:", missing_in_prod)

    combinedDataFrame = pd.concat([prodDataFrame, newDataFrame], ignore_index=True)
    combinedRowCount = len(combinedDataFrame)

    # Keep Package Size as text (avoid "30" vs "30.0" inconsistencies)
    combinedDataFrame["Package Size"] = combinedDataFrame["Package Size"].astype(str)

    # -----------------------------------------------------------------
    # Row count check
    # -----------------------------------------------------------------
    difference = expectedRowCount - combinedRowCount
    if difference != 0:
        print(f"**** Warning: Row count mismatch! Expected {expectedRowCount}, got {combinedRowCount} "
              f"(difference: {difference}).")
    else:
        print("Row count check passed: combined file has the expected number of rows.")

    # -----------------------------------------------------------------
    # Write output
    # -----------------------------------------------------------------
    if args.output:
        outputPath = args.output
    else:
        outputPath = pathlib.Path(f"first-time-nadac-{startTime.strftime('%m%d%Y')}.csv")

    combinedDataFrame.to_csv(outputPath, index=False, encoding="utf-8-sig")
    print("Combined file written to:", outputPath.resolve())

    # -----------------------------------------------------------------
    # Auto-run xsv count as a second, independent row-count check
    # -----------------------------------------------------------------
    xsv_path = str(args.xsv) if args.xsv else shutil.which("xsv") or shutil.which("xsv.exe")
    if xsv_path:
        try:
            result = subprocess.run(
                [xsv_path, "count", str(outputPath)],
                capture_output=True, text=True, check=True,
            )
            xsv_count = result.stdout.strip()
            print(f"xsv count reports: {xsv_count} data rows (+1 header row = {int(xsv_count) + 1} total lines)")
            if int(xsv_count) != combinedRowCount:
                print("**** Warning: xsv count does not match pandas row count. Investigate the output file.")
            else:
                print("xsv count matches pandas row count.")
        except Exception as e:
            print(f"**** Note: could not run xsv automatically ({e}). "
                  f"You can run it manually: xsv count \"{outputPath}\"")
    else:
        print("Note: xsv.exe not found on PATH. To verify the row count manually, run:")
        print(f'    xsv count "{outputPath}"')
        print("(Or pass its location with -x, e.g. -x C:\\xsv\\xsv.exe)")

    endTime = datetime.now()
    print("Script finished at:", endTime)
    print("Total processing time:", endTime - startTime)


if __name__ == "__main__":
    main()
