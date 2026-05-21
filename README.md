# CMCS.resources
## Introduction
This repo contains Python scripts for updating data files on data.medicaid.gov. It is managed by the CMCS Web and Content Management team, an AVB Digital joint venture between Vaultes and Bixal. 

## Virtual Environment Creation

A local virtual environment should be created in the cloned directory. It will be automatically excluded from Git.

```bash
# Create the virtual environment
python3 -m venv ./venv

# Activate the virtual environment
# On Mac:
source ./venv/bin/activate

# On PC
./venv/bin/Activate.ps1
```

## Initial Package Installation

Required packages must be downloaded once the virtual environment is activated in the terminal.

```bash
# Verify the venv is active
pip --version

# If the above returns a string ex: pip 25.1.1 from...
#   continue to the next step. Otherwise, verify the venv is active in the terminal

pip install pandas openpyxl, pandantic

# If pip requests an update feel free to upgrade pip. Ex:
# [notice] A new release of pip is available: 25.1.1 -> 26.1.1
# [notice] To update, run: pip install --upgrade pip
```