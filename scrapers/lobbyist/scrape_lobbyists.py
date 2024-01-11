import csv
import json
import logging
import sys

import scrapelib
from tqdm import tqdm

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

reader = csv.DictReader(sys.stdin)
writer = csv.DictWriter(
    sys.stdout,
    fieldnames=[
        "LobbyistID",
        "LobbyistVersionID",
        "TerminationDate",
        "MemberID",
        "Phone",
        "MemberVersionID",
        "Year",
        "LobbyingEfforts",
        "LobbyistType",
        "LobbyistName",
        "LobbyistAddress",
        "LobbyingFirm",
        "PrincipalContact",
        "EmploymentDate",
        "EmailAddress",
        "TotalRows",
        "RowNumber",
        "ReportFileName",
        "RegistrationID",
        "IsPastRegistrationExists",
        "Email",
        "CompensatedStatus",
        "LobbyingSourceFunds",
        "AddressLines",
        "City",
        "StateCode",
        "CountryCode",
        "ZipCode",
        "CityAddress",
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
        "ClientID",
        "ClientVersionID",
    ],
)

writer.writeheader()

s = scrapelib.Scraper(requests_per_minute=60, retry_attempts=3)

payload = {
    "PageNo": 1,
    "PageSize": 10,
    "ElectionYear": "",
    "SortDir": "ASC",
    "SortedBy": "",
}

for row in tqdm(reader):
    _payload = payload.copy()
    _payload.update(
        {
            "ClientID": row["ClientID"],
            "ClientVersionID": row["ClientVersionID"],
        }
    )

    response = s.post(
        "https://login.cfis.sos.state.nm.us/api//ClientDetails/LobbyistsByClientList",
        data=json.dumps(_payload),
        headers={"Content-Type": "application/json"},
    )

    if response.ok:
        for record in response.json():
            # Add the client ID and version to the lobbyist record
            record.update(
                {
                    "ClientID": row["ClientID"],
                    "ClientVersionID": row["ClientVersionID"],
                }
            )
            writer.writerow(record)
