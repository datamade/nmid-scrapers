from collections import deque
import csv
import json
import logging
import scrapelib
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def main(rpm=180, retries=3, verify=False):
    writer = csv.DictWriter(
        sys.stdout,
        fieldnames=[
            "LobbyistName",
            "ID",
            "MemberVersionID",
            "Clients",
            "Email",
            "AddressLines",
            "CityAddress",
            "LobbyPhone",
        ],
        extrasaction="ignore",
    )

    writer.writeheader()

    s = scrapelib.Scraper(
        requests_per_minute=rpm, retry_attempts=retries, verify=verify
    )

    payload = {
        "ElectionYear": "",
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
        "PageNo": 1,
        "PageSize": 1000,
        "SortOrder": "ASC",
    }

    page_number = 1
    page_size = 1000
    result_count = 1000
    seen_lobbyists = deque(maxlen=25)

    while result_count == page_size:
        logger.debug(f"Fetching page {page_number}")

        _payload = payload.copy()
        _payload.update({"PageNo": page_number})

        logger.debug(_payload)

        lobbyists = s.post(
            "https://login.cfis.sos.state.nm.us/api//SearchLobbyist/SearchLobbyist",
            data=json.dumps(_payload),
            headers={"Content-Type": "application/json"},
        ).json()

        for lobbyist in lobbyists:
            if lobbyist["ID"] in seen_lobbyists:
                continue

            lobbyist_details = s.get(
                "https://login.cfis.sos.state.nm.us/api//LobbyistDetails/GetLobbyistDetails",
                params={
                    "memberId": lobbyist["ID"],
                    "memberversionID": lobbyist["MemberVersionID"],
                },
            ).json()

            lobbyist.update(
                {
                    "Email": lobbyist_details["Email"],
                    "AddressLines": lobbyist_details["AddressLines"],
                    "CityAddress": lobbyist_details["CityAddress"],
                    "LobbyPhone": lobbyist_details["LobbyPhone"],
                }
            )

            writer.writerow(lobbyist)

            seen_lobbyists.append(lobbyist["ID"])

        result_count = len(lobbyists)

        logger.debug(f"Last page {page_number} had {result_count} results")

        page_number += 1


if __name__ == "__main__":
    main()
