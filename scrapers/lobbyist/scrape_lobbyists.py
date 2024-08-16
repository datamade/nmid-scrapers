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
    ],
)

writer.writeheader()

s = scrapelib.Scraper(requests_per_minute=0, retry_attempts=3, verify=False)

payload = {
    "PageNo": 1,
    "PageSize": 1000,
    "ElectionYear": "",
    "SortDir": "ASC",
    "SortedBy": "",
    "ClientVersionID": "",
}

for row in tqdm(reader):
    _payload = payload.copy()
    _payload["ClientID"] = row["ClientID"]
    _payload["ClientVersionID"] = str(int(float(row["ClientVersionID"])))

    response = s.post(
        "https://login.cfis.sos.state.nm.us/api//ClientDetails/LobbyistsByClientList",
        data=json.dumps(_payload),
        headers={"Content-Type": "application/json"},
    )

    if response.ok:
        for record in response.json():
            record["ClientID"] = row["ClientID"]
            writer.writerow(record)
