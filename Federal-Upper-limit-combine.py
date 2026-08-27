import argparse
import pathlib
import sys
import pandas
from collections import defaultdict
from datetime import datetime

startTime = datetime.now()
print("Script started at: ", startTime)

parser = argparse.ArgumentParser(
    description="ACA Federal Upper Limit pipeline: read the new monthly extract "
                 "(.xlsx or .csv), fix the known Year/Month column swap, validate "
                 "columns against the production CSV, and combine the two."
)
parser.add_argument("-i", "--input", help="Path to the new monthly data file (.xlsx or .csv)",
                     type=pathlib.Path, required=True)
parser.add_argument("-p", "--prodExport", help="Path to the existing production CSV file "
                     "to append the new monthly data onto", type=pathlib.Path, required=True)
parser.add_argument("-o", "--output", help="Path to the final combined output CSV. If omitted, "
                     "defaults to 'aca-federal-upper-limits-MMDDYYYY.csv' (today's date) in the "
                     "current directory.", type=pathlib.Path, default=None)
parser.add_argument("-s", "--sheet", help="Sheet name/index to read when --input is an "
                     "Excel file (default: first sheet)", default=0)
parser.add_argument("--dedupe", help="Drop exact-duplicate rows from the combined output",
                     action="store_true")
args = parser.parse_args()

dtype_dict_str = defaultdict(lambda: 'str')


# ------------------------------------------------------------------------
# Number formatting to match the production CSV's conventions
# ------------------------------------------------------------------------
def format_number_like_production(series: "pandas.Series") -> "pandas.Series":
    def fmt(value):
        if pandas.isna(value):
            return ""
        if isinstance(value, str):
            return value.strip()
        rounded = round(float(value), 6)
        if rounded == int(rounded):
            return str(int(rounded))
        text = f"{rounded:.6f}".rstrip("0").rstrip(".")
        return text
    return series.map(fmt)


# ------------------------------------------------------------------------
# Fix the Year/Month columns.
# The source file labels its last two columns "Year"/"Month" but (as of the
# August 2026 extract) the VALUES are swapped -- the "Year" column holds the
# month number (e.g. 8) and the "Month" column holds the year (e.g. 2026).
# We auto-detect this rather than assuming it's always swapped, so the script
# keeps working correctly if a future extract already has it right.
# ------------------------------------------------------------------------
def fix_year_month_columns(df: "pandas.DataFrame") -> "pandas.DataFrame":
    if "Year" not in df.columns or "Month" not in df.columns:
        print("**** Warning: Could not find both 'Year' and 'Month' columns to check/fix.")
        return df

    year_vals = pandas.to_numeric(df["Year"], errors="coerce")
    month_vals = pandas.to_numeric(df["Month"], errors="coerce")

    year_looks_like_month = year_vals.dropna().between(1, 12).all()
    month_looks_like_year = month_vals.dropna().gt(1900).all()

    if year_looks_like_month and month_looks_like_year:
        print("Detected swapped Year/Month columns -- correcting (Year<->Month).")
        df["Year"], df["Month"] = df["Month"].copy(), df["Year"].copy()
    else:
        print("Year/Month columns already look correct; no swap applied.")

    return df


def load_input_file(path: pathlib.Path, sheet) -> "pandas.DataFrame":
    suffix = path.suffix.lower()

    if suffix == ".csv":
        try:
            df = pandas.read_csv(path, dtype=dtype_dict_str, encoding="utf-8")
        except UnicodeDecodeError:
            print("**** Note: input CSV is not UTF-8 encoded; retrying as latin-1.")
            df = pandas.read_csv(path, dtype=dtype_dict_str, encoding="latin-1")
        df.columns = [str(c).strip() for c in df.columns]
        return df

    elif suffix in (".xlsx", ".xlsm", ".xls"):
        raw = pandas.read_excel(path, sheet_name=sheet, engine="openpyxl" if suffix != ".xls" else None)
        raw.columns = [str(c).strip() for c in raw.columns]

        numeric_like_cols = raw.select_dtypes(include="number").columns
        for col in numeric_like_cols:
            raw[col] = format_number_like_production(raw[col])
        for col in raw.columns.difference(numeric_like_cols):
            raw[col] = raw[col].map(lambda v: "" if pandas.isna(v) else str(v).strip())
        return raw

    else:
        print(f"**** Error: Unsupported input file type '{suffix}'. Expected .csv or .xlsx.")
        sys.exit(1)


# ------------------------------------------------------------------------
# Main pipeline
# ------------------------------------------------------------------------
if not args.input.is_file():
    print(f"**** Error: Input file does not exist: {args.input}")
    sys.exit(1)
if not args.prodExport.is_file():
    print(f"**** Error: Production export file does not exist: {args.prodExport}")
    sys.exit(1)

if args.output is None:
    args.output = pathlib.Path(f"aca-federal-upper-limits-{startTime.strftime('%m%d%Y')}.csv")
    print(f"No output path given; using default: {args.output}")

inputDataFrame = load_input_file(args.input, args.sheet)
inputDataFrame = fix_year_month_columns(inputDataFrame)

print("Input file contains ", len(inputDataFrame), " rows.")

# ---- Load production file ----
try:
    prodDataFrame = pandas.read_csv(args.prodExport, dtype=dtype_dict_str, encoding="utf-8")
except UnicodeDecodeError:
    print("**** Note: production CSV is not UTF-8 encoded; retrying as latin-1.")
    prodDataFrame = pandas.read_csv(args.prodExport, dtype=dtype_dict_str, encoding="latin-1")
prodDataFrame.columns = [str(c).strip() for c in prodDataFrame.columns]
print("Production file contains ", len(prodDataFrame), " rows.")

# ---- Validate columns line up ----
input_cols = list(inputDataFrame.columns)
prod_cols = list(prodDataFrame.columns)

if set(input_cols) != set(prod_cols):
    only_in_input = set(input_cols) - set(prod_cols)
    only_in_prod = set(prod_cols) - set(input_cols)
    print("**** Error: Column mismatch between input and production files.")
    if only_in_input:
        print("    Columns only in input: ", sorted(only_in_input))
    if only_in_prod:
        print("    Columns only in production: ", sorted(only_in_prod))
    sys.exit(1)

inputDataFrame = inputDataFrame[prod_cols]

# ---- Append input onto production ----
combinedDataFrame = pandas.concat([prodDataFrame, inputDataFrame], ignore_index=True)

if args.dedupe:
    before = len(combinedDataFrame)
    combinedDataFrame = combinedDataFrame.drop_duplicates()
    print(f"Removed {before - len(combinedDataFrame)} exact-duplicate row(s).")

# ---- Write output ----
combinedDataFrame.to_csv(args.output, index=False)

print("Done. ", len(combinedDataFrame), " rows written to ", args.output)

endTime = datetime.now()
print("Total processing time: ", endTime - startTime)
