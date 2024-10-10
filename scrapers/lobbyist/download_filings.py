import csv
import os
import requests
import sys

from tqdm import tqdm


_, subdir = sys.argv


def get_file_name(report_type_code, member_id, report_file_name):
    report_path = os.path.join(subdir, "assets", report_type_code, member_id)
    os.makedirs(report_path, exist_ok=True)
    return os.path.join(report_path, report_file_name)


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

    try:
        response = requests.get(filing_url, verify=False)
    except Exception as e:
        print(f"Could not retrieve {filing_url}: {e}")
        continue

    if response.ok:
        # LAR - Quarterly, LCD - 48-hour, LNA - No expenditures
        with open(outfile, "wb") as f:
            f.write(response.content)

    else:
        print(f"Could not retrieve {filing_url}:\n{response.content.decode('utf-8')}")
