import csv
import json
import logging
import sys

import scrapelib
from tqdm import tqdm

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def main(rpm=180, retries=3, verify=False):
    reader = csv.DictReader(sys.stdin)
    writer = csv.DictWriter(
        sys.stdout,
        fieldnames=[
            "LobbyistID",
            "Year",
            "ClientName",
            "ClientAddress",
            "ClientNatureofBusiness",
            "LobbyingEfforts",
            "EmploymentDate",
            "TerminationDate",
            "CompensatedStatus",
        ],
        extrasaction="ignore",
    )

    writer.writeheader()

    s = scrapelib.Scraper(
        requests_per_minute=rpm, retry_attempts=retries, verify=verify
    )

    payload = {
        "ElectionYear": "",
        "PageNo": 1,
        "PageSize": 1000,
    }

    for row in tqdm(reader):
        _payload = payload.copy()
        _payload["LobbyistID"] = row["ID"]
        _payload["LobbyistVersionID"] = row["MemberVersionID"]

        response = s.post(
            "https://login.cfis.sos.state.nm.us/api//LobbyistDetails/LobbyistClientList",
            data=json.dumps(_payload),
            headers={"Content-Type": "application/json"},
        )

        if response.ok:
            for record in response.json():
                record["LobbyistID"] = row["ID"]
                writer.writerow(record)


if __name__ == "__main__":
    main()
