# NADAC (National Average Drug Aquisition Cost)

## Necessary Dependencies
* pandas (python3 -m pip install pandas)
* openpyxl (python3 -m pip install openpyxl)

## Weekly Updated Date Feed

[Weekly NADAC Feed URL](https://data.medicaid.gov/dataset/fbb83258-11c7-47f5-8b18-5f8e79f7e704#data-table)

## Script Execution

The command below shows how to execute the Weekly NADAC file. The input Excel file should be downloaded from the appropriate ticket and the production CSV file exported from the feed URL above.

*Note:* The following assumes a Python virtual environment has been created and the dependencies listed above have been installed.

```
python3 .\NADACWeekly.py -i .\sample.files\20260506_NADAC_Weekly.xlsx -p .\sample.files\nadac-national-average-drug-acquisition-cost-05-13-2026.csv -d 05/19/2026
```

### Script Output

```
Parsing input file:  sample.files\20260506_NADAC_Weekly.xlsx
Parsing production export file:  sample.files\nadac-national-average-drug-acquisition-cost-05-13-2026.csv
Using As of Date:  20260519
Input file contains  30220  rows.
Production export file contains  2184398  rows.
Processing complete.
Combined Output:  2214618  rows written to NADAC_Weekly_Combined_File.csv
Expected Row Count:  2214618  Received:  2214618  Difference:  0
```

## Weekly Comparison Feed

## Script Execution

The command below shows how to execute the Weekly NADAC file. The input Excel file should be downloaded from the appropriate ticket and the production CSV file exported from the feed URL above.

*Note:* The following assumes a Python virtual environment has been created and the dependencies listed above have been installed.

```
python3 .\NADACWeeklyComparison.py -i .\sample.files\20260506_NADAC_Weekly_Comparison.xlsx -p .\sample.files\nadac-comparison-05-06-2026.csv -sd 05/01/2026 -ed 05/19/2026
```

### Script Output

```
Parsing input file:  sample.files\20260506_NADAC_Weekly_Comparison.xlsx
Parsing production export file:  sample.files\nadac-comparison-05-06-2026.csv
Using start date:  05/01/2026
Using end date:  05/19/2026
Input file contains  3  rows.
Production export file contains  3319829  rows.
Processing complete.
Combined Output:  3319832  rows written to NADAC_Weekly_Combined_File.csv
Expected Row Count:  3319832  Received:  3319832  Difference:  0
```