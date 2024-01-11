import csv
import json
import logging
import scrapelib
import sys

from tqdm import tqdm


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

reader = csv.DictReader(sys.stdin)
writer = csv.DictWriter(
    sys.stdout,
    fieldnames=[
        "ClientID",
        "ReportName",
        "ReportFileName",
        "ReportTypeCode",
        "ReportType",
        "PeriodStart",
        "PeriodEnd",
        "DueDate",
        "SubmittedDate",
        "TotalRows",
        "ReportID",
        "ReportVersionID",
        "Status",
        "IncidentalLobbying",
        "ReportStatus",
        "IsAfterDueDate",
        "CreatedBy",
        "CreatedDate",
        "CreatedIPAddress",
        "LobbyistClientID",
        "LobbyistClientVersionID",
        "LastModifiedBy",
        "LastModifiedDate",
        "LastModifiedIPAddress",
        "Message",
        "IsSuccess",
        "Action",
        "IsDirty",
        "PersonID",
        "PersonVersionID",
        "MemberID",
        "MemberVersionID",
    ],
)

writer.writeheader()

s = scrapelib.Scraper(requests_per_minute=0, retry_attempts=3)

payload = {
    "PageNo": 1,
    "PageSize": 100,
    "SortDir": "ASC",
    "SortedBy": "",
    "ElectionYear": "",
    "LobbyistVersionID": "",
}

for row in tqdm(reader):
    _payload = payload.copy()
    _payload.update(
        {
            "LobbyistID": row["MemberID"],
        }
    )

    response = s.post(
        "https://login.cfis.sos.state.nm.us/api//ExploreClients/Fillings",
        data=json.dumps(_payload),
        headers={"Content-Type": "application/json"},
    )

    if response.ok:
        for record in response.json():
            # Add the lobbyist ID and version to the filing record
            record.update(
                {
                    "MemberID": row["MemberID"],
                    "MemberVersionID": None,
                }
            )
            writer.writerow(record)
