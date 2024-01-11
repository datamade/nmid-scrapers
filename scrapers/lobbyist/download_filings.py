import csv
import os
import requests
import sys

from tqdm import tqdm


def get_file_name(report_type_code, member_id, report_file_name):
    os.makedirs(
        os.path.join("data", "pdfs", report_type_code, member_id), exist_ok=True
    )

    return os.path.join(
        "data",
        "pdfs",
        report_type_code,
        member_id,
        report_file_name,
    )


reader = csv.DictReader(sys.stdin)

for row in tqdm(reader):
    outfile = get_file_name(
        row["ReportTypeCode"],
        row["MemberID"],
        row["ReportFileName"],
    )

    if os.path.exists(outfile):
        continue

    filing_url = f"https://login.cfis.sos.state.nm.us//ReportsOutput//{row['ReportTypeCode']}/{row['ReportFileName']}"

    response = requests.get(filing_url)

    if response.ok:
        # LAR - Quarterly, LCD - 48-hour, LNA - No expenditures
        with open(outfile, "wb") as f:
            f.write(response.content)

    else:
        print(f"Could not retrieve {filing_url}:\n{response.content.decode('utf-8')}")
