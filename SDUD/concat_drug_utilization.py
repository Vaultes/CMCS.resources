#!/usr/bin/env python3
"""
sdud_to_csv.py

Convert raw CMS State Drug Utilization Data (SDUD) files into a single CSV.

Reads every pipe-delimited text file in a folder (default: "Drug Utilization"),
then for each row:
  - builds the 11-digit NDC from zero-padded labeler, product, and package codes
  - splits the combined year-quarter value (e.g. 20204) into Year and Quarter
  - flags suppressed rows and blanks their numeric fields
  - removes stray leading quotes from drug names (internal apostrophes are kept)

The output is named by the years found in the data, e.g. sdud2020.csv or
sdud2018-2020.csv.

Usage:
    python sdud_to_csv.py
    python sdud_to_csv.py --folder "path/to/Drug Utilization" --out-dir "path/to/csv"
    python sdud_to_csv.py --master "master.txt" --strip-names
"""

import argparse
import csv
import os
import sys
from pathlib import Path

HEADERS = [
    "Utilization Type", "State", "NDC", "Labeler Code", "Product Code",
    "Package Size", "Year", "Quarter", "Suppression Used", "Product Name",
    "Units Reimbursed", "Number of Prescriptions", "Total Amount Reimbursed",
    "Medicaid Amount Reimbursed", "Non Medicaid Amount Reimbursed",
]
MIN_FIELDS = 12


def find_files(folder, pattern, recursive):
    folder = Path(folder)
    if not folder.is_dir():
        sys.exit(f"Folder not found: '{folder}'")

    search = folder.rglob if recursive else folder.glob
    files = sorted(
        p for p in search(pattern)
        if p.is_file() and not p.name.startswith(".")
    )
    if not files:
        sys.exit(f"No files matching '{pattern}' found in '{folder}'.")
    return files


def convert_row(fields, strip_names):
    """Turn one list of raw SDUD fields into an output row.

    Returns (row, year, name_was_cleaned).
    """
    record_type  = fields[0].strip()
    state        = fields[1].strip()
    labeler_code = fields[2].strip().zfill(5)
    product_code = fields[3].strip().zfill(4)
    pkg_size     = fields[4].strip().zfill(2)
    year_quarter = fields[5].strip()
    drug_name    = fields[6]  # trailing spaces preserved unless --strip-names
    units        = fields[7].strip()
    num_rx       = fields[8].strip()
    total_reimb  = fields[9].strip()
    medicaid     = fields[10].strip()
    non_medicaid = fields[11].strip()

    # Remove leading quotes only; keep internal ones (e.g. CHILDREN'S)
    cleaned_name = drug_name.lstrip('"')
    name_was_cleaned = cleaned_name != drug_name
    drug_name = cleaned_name.rstrip() if strip_names else cleaned_name

    ndc = f"{labeler_code}{product_code}{pkg_size}"

    year = year_quarter[:4]
    quarter = year_quarter[4:]

    suppressed = "*" in units
    if suppressed:
        units = num_rx = total_reimb = medicaid = non_medicaid = ""

    row = [
        record_type, state, ndc, labeler_code, product_code, pkg_size,
        year, quarter, "true" if suppressed else "false", drug_name,
        units, num_rx, total_reimb, medicaid, non_medicaid,
    ]
    return row, (year if year.isdigit() else None), name_was_cleaned


def main():
    parser = argparse.ArgumentParser(
        description="Convert raw SDUD pipe-delimited files into one CSV."
    )
    parser.add_argument("--folder", default="Drug Utilization",
                        help='Folder with raw SDUD files (default: "Drug Utilization").')
    parser.add_argument("--out-dir", default="Drug Utilization CSV",
                        help='Folder for the CSV output (default: "Drug Utilization CSV").')
    parser.add_argument("--pattern", default="*.txt",
                        help="Which files to read from the folder (default: *.txt).")
    parser.add_argument("-r", "--recursive", action="store_true",
                        help="Include files in subfolders too.")
    parser.add_argument("--master", metavar="PATH",
                        help="Also save the combined raw text to this path.")
    parser.add_argument("--strip-names", action="store_true",
                        help="Remove trailing spaces from drug names.")
    parser.add_argument("--show-skipped", type=int, default=5, metavar="N",
                        help="Print up to N skipped lines for review (default: 5).")
    parser.add_argument("--encoding", default="utf-8",
                        help="Encoding of the input files (default: utf-8).")
    args = parser.parse_args()

    files = find_files(args.folder, args.pattern, args.recursive)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = out_dir / ".sdud_in_progress.csv"

    print(f"Found {len(files)} file(s) in '{args.folder}'.")

    rows_written = rows_skipped = cleaned_count = 0
    skipped_samples = []
    years_found = set()
    master_out = open(args.master, "w", encoding="utf-8") if args.master else None

    try:
        with open(tmp_path, "w", encoding="utf-8", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(HEADERS)

            for path in files:
                file_rows = 0
                with open(path, encoding=args.encoding, errors="replace") as infile:
                    for line_no, raw in enumerate(infile, 1):
                        if master_out:
                            master_out.write(raw if raw.endswith("\n") else raw + "\n")

                        line = raw.rstrip("\r\n").replace("\r", "")
                        if not line.strip():
                            continue

                        fields = line.split("|")
                        if len(fields) < MIN_FIELDS:
                            rows_skipped += 1
                            if len(skipped_samples) < args.show_skipped:
                                skipped_samples.append(f"{path.name}, line {line_no}: {line[:120]}")
                            continue

                        row, year, cleaned = convert_row(fields, args.strip_names)
                        writer.writerow(row)
                        if year:
                            years_found.add(year)
                        cleaned_count += cleaned
                        rows_written += 1
                        file_rows += 1

                print(f"  {path.name}: {file_rows} row(s)")
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise
    finally:
        if master_out:
            master_out.close()

    if not years_found:
        tmp_path.unlink(missing_ok=True)
        sys.exit("No valid years detected in the data. Check that the files are raw SDUD text.")

    year_label = (min(years_found) if len(years_found) == 1
                  else f"{min(years_found)}-{max(years_found)}")
    output_path = out_dir / f"sdud{year_label}.csv"
    os.replace(tmp_path, output_path)

    print(f"\nYears detected: {', '.join(sorted(years_found))}")
    print(f"Done! {rows_written} rows written, {rows_skipped} rows skipped.")
    print(f"Cleaned {cleaned_count} drug name(s) with leading quotes.")
    if skipped_samples:
        print(f"\nFirst {len(skipped_samples)} skipped line(s):")
        for sample in skipped_samples:
            print(f"  {sample}")
    if args.master:
        print(f"Combined raw text: {args.master}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()