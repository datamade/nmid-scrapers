import csv
import json
import logging
import scrapelib
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

writer = csv.DictWriter(
    sys.stdout,
    fieldnames=[
        "LobbyistName",
        "FilingYear",
        "FilingYearDesc",
        "LobbyistStatus",
        "ID",
        "LobbyistFirmName",
        "TotalRows",
        "Clients",
        "MemberVersionID",
        "LobbyistType",
        "Status",
        "NumberofClients",
        "NumberofLobbyists",
        "ClientBusinessorEntityType",
        "Lobbyists",
        "TotalContributions",
        "TotalExpenditures",
        "TotalCompensation",
        "EntitiesLobbied",
        "IsCompliant",
        "CompliantStatus",
        "Compliant",
    ],
)

writer.writeheader()

s = scrapelib.Scraper(requests_per_minute=10)

election_years = ("2022", "2023")
payload = {
    "Status": "",
    "TransactionType": None,
    "TransactionAmount": 0,
    "NumberofClients": None,
    "IsCompliance": None,
    "TotalCompensation": None,
    "LobbyistType": "",
    "NumberofLobbyists": None,
    "ClientBusinessorEntityType": None,
    "AgentType": "",
    "PageSize": 100,
    "SortOrder": "",
}

for year in election_years:
    page_number = 1
    page_size = 100
    result_count = 100

    while result_count == page_size:
        logger.debug(f"Fetching page {page_number} for {year}")

        _payload = payload.copy()
        _payload.update(
            {
                "ElectionYear": year,
                "PageNo": page_number,
            }
        )

        logger.debug(_payload)

        response = s.post(
            "https://login.cfis.sos.state.nm.us/api//SearchLobbyist/SearchLobbyist",
            data=json.dumps(_payload),
            headers={"Content-Type": "application/json"},
        )

        if response.ok:
            results = response.json()
            writer.writerows(results)
            result_count = len(results)

            logger.debug(f"Last page {page_number} had {result_count} results")

            page_number += 1
        else:
            logger.error(
                f"Failed to fetch results:\n{response.content.decode('utf-8')}"
            )
            sys.exit()
