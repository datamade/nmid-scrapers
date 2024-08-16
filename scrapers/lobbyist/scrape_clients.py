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
        "ClientName",
        "ClientID",
        "ClientVersionID",
        "NumberOfLobbyists",
    ],
    extrasaction="ignore",
)

writer.writeheader()

s = scrapelib.Scraper(requests_per_minute=60, retry_attempts=3, verify=False)

payload = {
    "ElectionYear": "",
    "BusinessType": None,
    "TransactionType": None,
    "TransactionAmount": 0,
    "EmployerName": None,
    "LobbyistOver": None,
    "IsCompliance": None,
    "PageSize": 1000,
    "SortDir": "ASC",
    "SortedBy": "",
    "IsWidgetDisplay": 0,
}

page_number = 1
page_size = 1000
result_count = 1000

while result_count == page_size:
    logger.debug(f"Fetching page {page_number}")

    _payload = payload.copy()
    _payload.update({"PageNo": page_number})

    logger.debug(_payload)

    response = s.post(
        "https://login.cfis.sos.state.nm.us/api//ExploreClients/SearchClients",
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
        logger.error(f"Failed to fetch results:\n{response.content.decode('utf-8')}")
        sys.exit()
