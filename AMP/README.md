# Average Manufacturer Price (AMP)

## Quarterly Reporting

(AMP Quarterly Data Feed)[https://data.medicaid.gov/dataset/80956a7d-e343-54f3-94a7-45d41b34fc0b]

# Legacy Confluence Documentation
Created by Unknown User (vwhi), last updated byMahesh Babu Chitradaon23/Apr/26 8:46 AM 2 minute read




ABOUT PUBLISHING AVERAGE MANUFACTURER PRICES (AMP) DATA

Publishing Product Data for Newly Reported Drugs in the Medicaid Drug Rebate Program requires the following steps:
Prerequisites
Step 1: Prepare Data for Load into DKAN
Step 2: Load Data into DKAN
Step 3: Verify that New Links Work
Step 4: Notify CMCS
Reference URLs

Prerequisites


Login credentials for data.medicaid.gov with publishing or admin rights.
Excel installed on your local computer. 
Latest Product Data for Newly Reported Drugs in the Medicaid Drug Rebate Program data files.Each weekMichael Forman will make the files available as attachments to a Jira ticket.
Step 1: Prepare Data for Load into DKAN


Weekly data provided as a Excel file.
Download the files from JIRA/BOX as provided by content owner
Copy files to C:\Python\Scripts and rename the files as NewlyReportedDrug.xlsx
Download attached script to your local Python installed location. Example: C:\Python\Scripts\newly_reported_drugs_in_the_medicaid_drug_rebate_program.py
newly_reported_drugs_in_the_medicaid_drug_rebate_program.py
Launch windows command prompt, Navigate to C:\Python\Scripts, execute newly_reported_drugs_in_the_medicaid_drug_rebate_program.py
NDC_Report.csv file is generated in C:\Python\Scripts. Copy this file to xsv installation folder (Example: C:\xsv)
Now Launch the windows command prompt, Navigate to C:\xsv and execute the command as\xsv.exe count NDC_Report.csv to check the count of the number of rows in the final file is right or not
Now login to https://control.akamai.com, and upload the file into netstorage.
Back to Top

Step 2: Load Data into DKAN


Go tohttps://edit.data.medicaid.gov/user. You must have publish or admin rights.
Now login to https://edit.data.medicaid.gov/user, create new dataset and update the dataset with the new file that is uploaded in Akamai.
Change the last updated date to today's date and publish the content.
Back to Top



Step 3: Verify that New Links Work


Once the content change is published, verify that the link on the Medicaid Drug Rebate Program Data page navigates to the appropriate view.


Step 4: Notify CMCS

Send an email informing Michael Forman that the data has been posted.

Reference URLs

Medicaid Drug Rebate Program Data page:
https://www.medicaid.gov/medicaid/prescription-drugs/medicaid-drug-rebate-program/data/index.html