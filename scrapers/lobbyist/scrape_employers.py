from collections import deque
import csv
import json
import logging
import scrapelib
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class LobbyistEmployerScraper(scrapelib.Scraper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _employers(self):
        payload = {
            "FilerType": "CR",
            "ExpenditureType": None,
            "ElectionYear": "",
            "AmountType": "Over",
            "pageNumber": 1,
            "pageSize": 1000,
            "sortDir": "ASC",
            "sortedBy": "",
        }

        page_number = 1
        page_size = 1000
        result_count = 1000

        while result_count == page_size:
            logger.debug(f"Fetching page {page_number}")

            _payload = {**payload, "pageNumber": page_number}
            logger.debug(_payload)

            response = self.post(
                "https://login.cfis.sos.state.nm.us/api///"
                "Search/LobbyistExpenditureSearchInformation",
                data=json.dumps(_payload),
                headers={"Content-Type": "application/json"},
                verify=False,
            )

            if response.ok:
                results = response.json()

                yield from results

                result_count = len(results)

                logger.debug(f"Last page {page_number} had {result_count} results")

                page_number += 1
            else:
                logger.error(
                    f"Failed to fetch results:\n{response.content.decode('utf-8')}"
                )
                sys.exit()

    def scrape(self):
        seen_employers = deque(maxlen=25)

        for result in self._employers():
            if result["LobbyMemberID"] not in seen_employers:
                yield {
                    "Name": result["Name"],
                    "LobbyMemberID": result["LobbyMemberID"],
                    "LobbyMemberversionid": result["LobbyMemberversionid"],
                }

                seen_employers.append(result["LobbyMemberID"])


def main(rpm=180, retries=3, verify=False):
    writer = csv.DictWriter(
        sys.stdout,
        fieldnames=[
            "Name",
            "LobbyMemberID",
            "LobbyMemberversionid",
        ],
        extrasaction="ignore",
    )

    writer.writeheader()

    scraper = LobbyistEmployerScraper(
        requests_per_minute=rpm, retry_attempts=retries, verify=verify
    )
    for result in scraper.scrape():
        writer.writerow(result)


if __name__ == "__main__":
    main()
