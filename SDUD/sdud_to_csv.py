#!/usr/bin/env python3
"""
sdud_to_csv.py

Convert raw CMS State Drug Utilization Data (SDUD) files into a single CSV,
then run QA checks on the data.

Conversion, for each row:
  - builds the 11-digit NDC from zero-padded labeler, product, and package codes
  - splits the combined year-quarter value (e.g. 20204) into Year and Quarter
  - flags suppressed rows and blanks their numeric fields
  - removes stray leading quotes from drug names (internal apostrophes are kept)

QA checks, collected during the same pass through the data:
  1. Years present versus the expected range
  2. Quarters present per year, with a gap check on the most recent year
  3. Redaction (suppressed rows) present
  4. States present for the most recent year (50 states + DC + XX national)
  5. Input file count

Output: sdud<years>.csv plus a matching sdud<years>_qa.txt report.

Usage:
    python sdud_to_csv.py
    python sdud_to_csv.py --folder "path/to/Drug Utilization" --out-dir "path/to/csv"
    python sdud_to_csv.py --qa-only
    python sdud_to_csv.py --master "master.txt" --strip-names
"""

import argparse
import csv
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HEADERS = [
    "Utilization Type", "State", "NDC", "Labeler Code", "Product Code",
    "Package Size", "Year", "Quarter", "Suppression Used", "Product Name",
    "Units Reimbursed", "Number of Prescriptions", "Total Amount Reimbursed",
    "Medicaid Amount Reimbursed", "Non Medicaid Amount Reimbursed",
]
MIN_FIELDS = 12

# 50 states + DC + XX (national totals). Any other code, such as PR, is
# reported as an extra state code rather than a failure.
EXPECTED_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN",
    "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV",
    "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN",
    "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC", "XX",
}
DEFAULT_EXPECTED_FILES = 52
FIRST_SDUD_YEAR = 1991


# ── FILES ────────────────────────────────────────────────────────────────────
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


# ── CONVERSION ───────────────────────────────────────────────────────────────
def convert_row(fields, strip_names):
    """Turn one list of raw SDUD fields into an output row.

    Returns (row, name_was_cleaned).
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
    return row, name_was_cleaned


# ── QA ───────────────────────────────────────────────────────────────────────
class QAStats:
    def __init__(self):
        self.years_quarters = defaultdict(set)
        self.states_by_year = defaultdict(set)
        self.total_rows = 0
        self.skipped_rows = 0
        self.redacted_rows = 0

    def add(self, row):
        state, year, quarter, suppressed = row[1], row[6], row[7], row[8]
        self.total_rows += 1
        self.years_quarters[year].add(quarter or "?")
        self.states_by_year[year].add(state)
        if suppressed == "true":
            self.redacted_rows += 1

    @property
    def valid_years(self):
        return sorted(y for y in self.years_quarters if y.isdigit() and len(y) == 4)


def run_qa(stats, folder, file_count, expected_files):
    """Build the QA report. Returns (report_lines, warning_count)."""
    lines = []
    out = lines.append
    warnings = 0
    bar, rule = "=" * 60, "─" * 60

    out(bar)
    out(f"QA CHECK: {folder}")
    out(f"Files found: {file_count}")
    out(bar)
    out("")
    pct = stats.redacted_rows / stats.total_rows * 100 if stats.total_rows else 0
    out(f"Total rows read:    {stats.total_rows:,}")
    out(f"Skipped (bad rows): {stats.skipped_rows:,}")
    out(f"Redacted rows:      {stats.redacted_rows:,}")
    out(f"Redacted %:         {pct:.1f}%")
    out("")

    # CHECK 1: YEARS
    out(rule)
    out("CHECK 1: Years present in data")
    out(rule)
    current_year = datetime.now().year
    all_years = stats.valid_years
    out(f"Years found: {', '.join(all_years)}")

    all_quarters = {q for qs in stats.years_quarters.values() for q in qs}
    if all_quarters == {"3"}:
        start = FIRST_SDUD_YEAR
        out(f"Q3 data detected: expected years {start}-{current_year}")
    else:
        start = current_year - 5
        out(f"Non-Q3 data: expected years {start}-{current_year}")

    expected_years = {str(y) for y in range(start, current_year + 1)}
    missing_years = expected_years - set(all_years)
    extra_years = set(all_years) - expected_years
    unreadable_years = sorted(y for y in stats.years_quarters if y not in all_years)

    if missing_years:
        warnings += 1
        out(f"  ⚠️  MISSING years: {', '.join(sorted(missing_years))}")
    else:
        out("  ✅ All expected years present")
    if extra_years:
        out(f"  ℹ️  Extra years found: {', '.join(sorted(extra_years))}")
    if unreadable_years:
        warnings += 1
        shown = ", ".join(repr(y) for y in unreadable_years[:10])
        out(f"  ⚠️  Unreadable year values: {shown}")

    # CHECK 2: QUARTERS
    out("")
    out(rule)
    out("CHECK 2: Quarters present per year")
    out(rule)
    for year in sorted(stats.years_quarters):
        out(f"  {year}: quarters {', '.join(sorted(stats.years_quarters[year]))}")

    most_recent = all_years[-1]
    found_quarters = sorted(stats.years_quarters[most_recent])
    out("")
    out(f"Most recent year ({most_recent}) has quarters: {', '.join(found_quarters)}")

    bad_quarters = [q for q in found_quarters if not (q.isdigit() and 1 <= int(q) <= 4)]
    nums = sorted(int(q) for q in found_quarters if q not in bad_quarters)
    gaps = [str(q) for q in range(1, max(nums) + 1) if q not in nums] if nums else []

    if nums and not gaps and not bad_quarters:
        out(f"  ✅ Quarters 1-{max(nums)} present with no gaps")
    else:
        warnings += 1
        if gaps:
            out(f"  ⚠️  Missing quarter(s) before Q{max(nums)}: {', '.join(gaps)}")
        if bad_quarters:
            out(f"  ⚠️  Unreadable quarter values: {', '.join(bad_quarters)}")
        if not nums:
            out("  ⚠️  No valid quarters found")

    # CHECK 3: REDACTION
    out("")
    out(rule)
    out("CHECK 3: Redaction check")
    out(rule)
    if stats.redacted_rows > 0:
        out(f"  ✅ Data has been redacted ({stats.redacted_rows:,} rows suppressed)")
    else:
        warnings += 1
        out("  ⚠️  NO redacted rows found: check if suppression was applied")

    # CHECK 4: STATES
    out("")
    out(rule)
    out(f"CHECK 4: States present for most recent year ({most_recent})")
    out(rule)
    found_states = stats.states_by_year[most_recent]
    missing_states = EXPECTED_STATES - found_states
    extra_states = found_states - EXPECTED_STATES

    out(f"  Expected: {len(EXPECTED_STATES)} (50 states + DC + XX national)")
    out(f"  Found:    {len(found_states)}")
    if missing_states:
        warnings += 1
        out(f"  ⚠️  MISSING states: {', '.join(sorted(missing_states))}")
    else:
        out(f"  ✅ All {len(EXPECTED_STATES)} expected states/territories present")
    if extra_states:
        out(f"  ℹ️  Extra state codes found: {', '.join(sorted(extra_states))}")

    # CHECK 5: FILE COUNT
    out("")
    out(rule)
    out("CHECK 5: File count")
    out(rule)
    out(f"  Files found: {file_count}")
    if file_count == expected_files:
        out(f"  ✅ Expected {expected_files} files")
    else:
        warnings += 1
        out(f"  ⚠️  Expected {expected_files} files, found {file_count}")

    out("")
    out(bar)
    out(f"QA COMPLETE: {warnings} warning(s)")
    out(bar)
    return lines, warnings


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Convert raw SDUD pipe-delimited files into one CSV and run QA checks."
    )
    parser.add_argument("--folder", default="Drug Utilization",
                        help='Folder with raw SDUD files (default: "Drug Utilization").')
    parser.add_argument("--out-dir", default="Drug Utilization CSV",
                        help='Folder for the CSV and QA report (default: "Drug Utilization CSV").')
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
    parser.add_argument("--qa-only", action="store_true",
                        help="Run the QA checks without writing a CSV.")
    parser.add_argument("--expected-files", type=int, default=DEFAULT_EXPECTED_FILES,
                        metavar="N", help=f"Expected input file count (default: {DEFAULT_EXPECTED_FILES}).")
    parser.add_argument("--fail-on-warnings", action="store_true",
                        help="Exit with status 1 if any QA check raises a warning.")
    args = parser.parse_args()

    files = find_files(args.folder, args.pattern, args.recursive)
    out_dir = Path(args.out_dir)
    tmp_path = out_dir / ".sdud_in_progress.csv"
    if not args.qa_only:
        out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Found {len(files)} file(s) in '{args.folder}'.")

    stats = QAStats()
    cleaned_count = 0
    skipped_samples = []
    master_out = open(args.master, "w", encoding="utf-8") if args.master else None
    outfile = None if args.qa_only else open(tmp_path, "w", encoding="utf-8", newline="")
    writer = csv.writer(outfile) if outfile else None

    try:
        if writer:
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
                        stats.skipped_rows += 1
                        if len(skipped_samples) < args.show_skipped:
                            skipped_samples.append(f"{path.name}, line {line_no}: {line[:120]}")
                        continue

                    row, cleaned = convert_row(fields, args.strip_names)
                    if writer:
                        writer.writerow(row)
                    stats.add(row)
                    cleaned_count += cleaned
                    file_rows += 1

            print(f"  {path.name}: {file_rows} row(s)")
    except BaseException:
        if outfile:
            outfile.close()
            tmp_path.unlink(missing_ok=True)
        raise
    finally:
        if master_out:
            master_out.close()
        if outfile and not outfile.closed:
            outfile.close()

    years = stats.valid_years
    if not years:
        if not args.qa_only:
            tmp_path.unlink(missing_ok=True)
        sys.exit("No valid years detected in the data. Check that the files are raw SDUD text.")

    year_label = years[0] if len(years) == 1 else f"{years[0]}-{years[-1]}"
    output_path = None
    if not args.qa_only:
        output_path = out_dir / f"sdud{year_label}.csv"
        os.replace(tmp_path, output_path)

    verb = "read" if args.qa_only else "written"
    print(f"\nDone! {stats.total_rows:,} rows {verb}, {stats.skipped_rows:,} rows skipped.")
    print(f"Cleaned {cleaned_count:,} drug name(s) with leading quotes.")
    if skipped_samples:
        print(f"\nFirst {len(skipped_samples)} skipped line(s):")
        for sample in skipped_samples:
            print(f"  {sample}")

    qa_lines, qa_warnings = run_qa(stats, args.folder, len(files), args.expected_files)
    print("\n" + "\n".join(qa_lines) + "\n")

    if output_path:
        report_path = out_dir / f"sdud{year_label}_qa.txt"
        report_path.write_text("\n".join(qa_lines) + "\n", encoding="utf-8")
        if args.master:
            print(f"Combined raw text: {args.master}")
        print(f"QA report: {report_path}")
        print(f"Output:    {output_path}")

    if args.fail_on_warnings and qa_warnings:
        sys.exit(1)


if __name__ == "__main__":
    main()