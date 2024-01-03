import csv
import json
import logging
import scrapelib
import sys

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
    ],
)

writer.writeheader()

s = scrapelib.Scraper(requests_per_minute=10, retry_attempts=3)

payload = {
    "PageNo": 1,
    "PageSize": 10,
    "SortDir": "ASC",
    "SortedBy": "",
}

for row in reader:
    _payload = payload.copy()
    _payload.update(
        {
            "LobbyistID": row["ID"],
            "LobbyistVersionID": row["MemberVersionID"],
            "ElectionYear": row["FilingYear"],
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
                    "PersonID": row["ID"],
                    "PersonVersionID": row["MemberVersionID"],
                }
            )
            writer.writerow(record)
