from abc import ABC, abstractmethod

import csv
import json
import logging
import scrapelib
import sys
import click

from tqdm import tqdm


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class LobbyistScraper(ABC, scrapelib.Scraper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    @abstractmethod
    def url(self):
        pass

    @abstractmethod
    def _get_payload(self, id, version):
        pass

    def scrape(self, id, version):
        payload = self._get_payload(id, version)

        response = self.post(
            self.url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            verify=False,
        )

        if response.ok:
            for record in response.json():
                # Add the lobbyist ID and version to the filing record
                record["MemberID"] = id
                yield record


class LobbyistEmployerScraper(LobbyistScraper):
    @property
    def url(self):
        return "https://login.cfis.sos.state.nm.us/api//ExploreClients/Disclosures"

    def _get_payload(self, id, version):
        return {
            "PageNumber": 1,
            "PageSize": 1000,
            "SortDir": "ASC",
            "SortedBy": "",
            "Year": "",
            "ClientID": id,
            "ClientVersionID": version,
        }


class IndividualLobbyistScraper(LobbyistScraper):
    @property
    def url(self):
        return "https://login.cfis.sos.state.nm.us/api//ExploreClients/Fillings"

    def _get_payload(self, id, version):
        return {
            "PageNo": 1,
            "PageSize": 1000,
            "SortDir": "ASC",
            "SortedBy": "",
            "ElectionYear": "",
            "LobbyistID": id,
            "LobbyistVersionID": version,
        }


def main(rpm=190, retries=3, verify=False, is_employer_scrape=False):
    scraper_opts = {
        "requests_per_minute": rpm,
        "retry_attempts": retries,
        "verify": verify,
    }

    if is_employer_scrape:
        scraper = LobbyistEmployerScraper(**scraper_opts)
    else:
        scraper = IndividualLobbyistScraper(**scraper_opts)

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
        ],
    )

    writer.writeheader()

    for row in tqdm(reader):
        id, version = (
            row["LobbyMemberID" if is_employer_scrape else "ID"],
            row["LobbyMemberversionid" if is_employer_scrape else "MemberVersionID"],
        )
        results = scraper.scrape(id, version)
        if results:
            writer.writerows(results)


if __name__ == "__main__":
    main()
