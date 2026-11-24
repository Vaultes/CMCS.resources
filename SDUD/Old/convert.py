import csv
import os
from collections import defaultdict

input_file = '/Users/grace.hobson/Downloads/datamg/DrugUtilization/3master/master.txt'
output_folder = '/Users/grace.hobson/Downloads/datamg/DrugUtilization/4 csv'

headers = [
    'Utilization Type', 'State', 'NDC', 'Labeler Code', 'Product Code',
    'Package Size', 'Year', 'Quarter', 'Suppression Used', 'Product Name',
    'Units Reimbursed', 'Number of Prescriptions', 'Total Amount Reimbursed',
    'Medicaid Amount Reimbursed', 'Non Medicaid Amount Reimbursed'
]

rows_written = 0
rows_skipped = 0
cleaned_count = 0

# First pass: detect year(s) in the data
years_found = set()
with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
    for line in f:
        line = line.strip().replace('\r', '')
        if not line:
            continue
        fields = line.split('|')
        if len(fields) >= 6:
            year = fields[5].strip()[:4]
            if year.isdigit():
                years_found.add(year)

if len(years_found) == 1:
    year_label = list(years_found)[0]
else:
    year_label = f"{min(years_found)}-{max(years_found)}"

output_file = os.path.join(output_folder, f"sdud{year_label}.csv")
print(f"Years detected: {', '.join(sorted(years_found))}")
print(f"Output file: {output_file}")

# Second pass: convert
with open(input_file, 'r', encoding='utf-8', errors='replace') as infile, \
     open(output_file, 'w', newline='') as outfile:
    writer = csv.writer(outfile)
    writer.writerow(headers)

    for line in infile:
        line = line.strip().replace('\r', '')
        if not line:
            continue

        fields = line.split('|')
        if len(fields) < 12:
            rows_skipped += 1
            continue

        record_type  = fields[0].strip()
        state        = fields[1].strip()
        labeler_code = fields[2].strip()
        product_code = fields[3].strip()
        pkg_size     = fields[4].strip()
        year_quarter = fields[5].strip()
        drug_name    = fields[6]  # preserve trailing spaces
        units        = fields[7].strip()
        num_rx       = fields[8].strip()
        total_reimb  = fields[9].strip()
        medicaid     = fields[10].strip()
        non_medicaid = fields[11].strip()

        # Only remove leading quotes, preserve internal ones (e.g. CHILDREN'S)
        cleaned_name = drug_name.lstrip('"')
        if cleaned_name != drug_name:
            cleaned_count += 1
            drug_name = cleaned_name

        # NDC = labeler + product + package, no dashes
        ndc = f"{labeler_code}{product_code}{pkg_size}"

        # Split year and quarter from e.g. 20204
        year = year_quarter[:4]
        quarter = year_quarter[4:] if len(year_quarter) > 4 else ''

        # Suppression: true if asterisks in units field
        suppressed = '*' in units
        suppression_used = 'true' if suppressed else 'false'

        # If suppressed, blank out numeric fields
        if suppressed:
            units = num_rx = total_reimb = medicaid = non_medicaid = ''

        writer.writerow([
            record_type, state, ndc, labeler_code, product_code, pkg_size,
            year, quarter, suppression_used, drug_name,
            units, num_rx, total_reimb, medicaid, non_medicaid
        ])
        rows_written += 1

print(f"Done! {rows_written} rows written, {rows_skipped} rows skipped.")
print(f"Cleaned {cleaned_count} drug name(s) with leading quotes.")
print(f"Output: {output_file}")
