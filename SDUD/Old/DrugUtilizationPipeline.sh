#!/bin/bash

echo "========================================"
echo "DRUG UTILIZATION PIPELINE"
echo "========================================"

# STEP 1: QA Check
echo ""
echo "STEP 1: Running QA check on raw txt files..."
python3 ./qa_check.py ./2txt

# STEP 2: Create master.txt
echo ""
echo "STEP 2: Creating master.txt..."
cat ./2txt/*.txt > ./3master/master.txt
echo "Done! master.txt created."

# STEP 3: Convert to CSV
echo ""
echo "STEP 3: Converting master.txt to CSV..."
python3 ./convert.py

echo ""
echo "========================================"
echo "PIPELINE COMPLETE"
echo "========================================"
