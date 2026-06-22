#!/bin/bash

echo "========================================"
echo "DRUG UTILIZATION PIPELINE"
echo "========================================"

# STEP 1: QA Check
echo ""
echo "STEP 1: Running QA check on raw txt files..."
python3 /Users/grace.hobson/Downloads/datamg/DrugUtilization/qa_check.py /Users/grace.hobson/Downloads/datamg/DrugUtilization/2txt

# STEP 2: Create master.txt
echo ""
echo "STEP 2: Creating master.txt..."
cat /Users/grace.hobson/Downloads/datamg/DrugUtilization/2txt/*.txt > /Users/grace.hobson/Downloads/datamg/DrugUtilization/3master/master.txt
echo "Done! master.txt created."

# STEP 3: Convert to CSV
echo ""
echo "STEP 3: Converting master.txt to CSV..."
python3 /Users/grace.hobson/Downloads/datamg/DrugUtilization/convert.py

echo ""
echo "========================================"
echo "PIPELINE COMPLETE"
echo "========================================"
