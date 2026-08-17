import pandas as pd
import os
import sys
import requests
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
EXCEL_FILE = 'DrugProduct.xlsx'
PROD_FILE  = 'drugproducts-prod.csv'
PROD_URL   = 'https://download.medicaid.gov/data/drug-products-in-the-medicaid-drug-rebate-program.csv'

COLUMNS = ['Labeler Name', 'Labeler Code', 'Product Code', 'Package Size Code', 'Drug Category',
           'Drug Type Indicator', 'Termination Date', 'Unit Type', 'Units Per Pkg Size',
           'FDA Approval Date', 'Market Date', 'FDA Therapeutic Equivalence Code', 'FDA Product Name',
           'Clotting Factor Indicator', 'Pediatric Indicator', 'Package Size Intro Date',
           'Purchased Product Date', 'COD Status', 'FDA Application Number', 'Reactivation Date',
           'Line Extension Drug Indicator']

DATE_COLS = ['Termination Date', 'FDA Approval Date', 'Market Date',
             'Package Size Intro Date', 'Purchased Product Date', 'Reactivation Date']

print(f"\n{'='*60}")
print(f"  DRUG PRODUCT PIPELINE")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"{'='*60}\n")

# ── STEP 1: CHECK INPUT FILE ──────────────────────────────────────────────────
print("STEP 1: Checking input file...")
if not os.path.exists(EXCEL_FILE):
    print(f"ERROR: {EXCEL_FILE} not found in current folder.")
    print(f"Please rename your downloaded file to {EXCEL_FILE} and try again.")
    sys.exit(1)
print(f"  ✅ Found {EXCEL_FILE}")

# ── STEP 2: READ AND PROCESS EXCEL ───────────────────────────────────────────
print("\nSTEP 2: Reading and processing Excel file...")
df = pd.read_excel(EXCEL_FILE, header=None, dtype=str)

# Remove header row if present
if df.iloc[0].tolist()[0].strip().lower() in ['labeler name', 'labeler_name']:
    df = df.iloc[1:].reset_index(drop=True)
    print("  Removed header row from Excel file")

df.columns = COLUMNS

# Reformat date columns
for col in DATE_COLS:
    df[col] = df[col].astype(str).str.replace(r'(\d{2})(\d{2})(\d{4})', r'\1/\2/\3', regex=True)
    df[col] = df[col].str.replace('00/00/0000', '', regex=False)

# Create NDC column
df["NDC"] = df["Labeler Code"] + df["Product Code"] + df["Package Size Code"]
ndc_col = df.pop('NDC')
df.insert(1, 'NDC', ndc_col)

# Add Year and Quarter
yr   = int(input("  Enter year: "))
qutr = int(input("  Enter quarter: "))
df.insert(0, "Year", yr)
df.insert(1, "Quarter", qutr)

print(f"  ✅ Processed {len(df):,} rows")

# ── STEP 3: DOWNLOAD PROD FILE IF NEEDED ─────────────────────────────────────
print(f"\nSTEP 3: Checking production file...")
if not os.path.exists(PROD_FILE):
    print(f"  {PROD_FILE} not found — downloading from data.medicaid.gov...")
    print(f"  This may take a few minutes...")
    try:
        response = requests.get(PROD_URL, stream=True)
        with open(PROD_FILE, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  ✅ Downloaded {PROD_FILE}")
    except Exception as e:
        print(f"  ⚠️  Could not download: {e}")
        print(f"  Please manually download from:")
        print(f"  {PROD_URL}")
        print(f"  Save as {PROD_FILE} and run again.")
        sys.exit(1)
else:
    print(f"  ✅ Found existing {PROD_FILE}")

# ── STEP 4: APPEND TO PROD FILE ──────────────────────────────────────────────
print(f"\nSTEP 4: Appending to production file...")
df.to_csv(PROD_FILE, mode='a', index=False, encoding='utf-8-sig', header=False)

with open(PROD_FILE, 'r', encoding='utf-8-sig') as f:
    total_rows = sum(1 for _ in f) - 1

print(f"  ✅ Appended {len(df):,} rows")
print(f"  Total rows in {PROD_FILE}: {total_rows:,}")

print(f"\n{'='*60}")
print(f"  PIPELINE COMPLETE")
print(f"  Upload {PROD_FILE} to Akamai NetStorage")
print(f"{'='*60}\n")
