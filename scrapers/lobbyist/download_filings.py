import csv
import os
import requests
import sys

from tqdm import tqdm


reader = csv.DictReader(sys.stdin)

for row in tqdm(reader):
    filing_url = f"https://login.cfis.sos.state.nm.us//ReportsOutput//{row['ReportTypeCode']}/{row['ReportFileName']}"

    response = requests.get(filing_url)

    if response.ok:
        # LAR - Quarterly, LCD - 48-hour, LNA - No expenditures
        with open(
            os.path.join(
                "data", "pdfs", row["ID"], row["ReportTypeCode"], row["ReportFileName"]
            ),
            "wb",
        ) as f:
            f.write(response.content)

    else:
        print(f"Could not retrieve {filing_url}:\n{response.content.decode('utf-8')}")
