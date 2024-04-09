import logging
import io
import scrapelib
import sys
import pdfplumber

from .parse_pdf import parse_pdf

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def update_not_null(d1, d2):

    for k, v in d2.items():
        if (d1.get(k) is None) or (v is not None):
            d1[k] = v
    return d1


class SearchScraper(scrapelib.Scraper):
    def __init__(self, search_type, result_key, id_key, detail_endpoint):
        super().__init__(requests_per_minute=60)
        self.search_type = search_type
        self.result_key = result_key
        self.detail_endpoint = (
            f"https://login.cfis.sos.state.nm.us/api///Organization/{detail_endpoint}"
        )
        self.id_key = id_key

    def _search_results(self, search_type, result_key, id_key):
        ALPHABET = "abcdefghijklmnopqrstuvwxyz"

        payload = {
            "searchText": "a",
            "searchType": search_type,
            "pageNumber": 1,
            "pageSize": 1000,
            "sortDir": "asc",
            "sortedBy": "",
        }

        seen = set()

        for letter in ALPHABET:
            page_number = 1
            page_size = 1000
            result_count = 1000

            while result_count == page_size:
                logger.debug(f"Fetching page {page_number} for {letter}")

                _payload = payload.copy()
                _payload.update(
                    {
                        "searchText": letter,
                        "pageNumber": page_number,
                    }
                )

                logger.debug(_payload)

                response = self.get(
                    "https://login.cfis.sos.state.nm.us/api///Search/GetPublicSiteBasicSearchResult",
                    params=_payload,
                )

                if response.ok:
                    results = response.json()[result_key]
                    for result in results:
                        id_number = result[id_key]
                        if id_number in seen:
                            continue
                        else:
                            yield result
                            seen.add(id_number)

                    result_count = len(results)
                    page_number += 1

                else:
                    logger.error(f"Failed to fetch results:\n{response.text}")
                    sys.exit()

        logger.debug(f"Last page {page_number} had {result_count} results")

    def scrape(self):
        for search_result in self._search_results(
            self.search_type, self.result_key, self.id_key
        ):
            response = self.get(
                self.detail_endpoint, params={"memberId": search_result[self.id_key]}
            )

            params = {
                "officeID": search_result["OfficeId"],
                "electionYear": "All",
                "districtId": search_result["DistrictId"],
                "electionId": int(search_result["ElectionId"]),
                "FilerNameLink": "exploreDetails",
                "pageNumber": 1,
                "pageSize": 100,
            }
            if self.search_type == "Committee":
                params["committeeID"] = search_result["IdNumber"]
            else:
                params["committeeID"] = search_result["IDNumber"]

            try:
                filings = self.get(
                    "https://login.cfis.sos.state.nm.us/api///Filing/GetFilings",
                    params=params,
                ).json()
            except scrapelib.HTTPError as e:
                logging.error(e, search_result)
                breakpoint()

            for filing in filings:
                pdf = self.get(
                    f"https://login.cfis.sos.state.nm.us//ReportsOutput//{filing['ReportFileName']}"
                )
                filing_pdf = pdfplumber.open(io.BytesIO(pdf.content))
                filing_table = parse_pdf(filing_pdf)
                print(filing_table)

            yearly_info = [
                update_not_null(search_result, year_data)
                for year_data in response.json()
            ]


if __name__ == "__main__":
    import csv

    writer = None

    if sys.argv[1] == "candidates":
        scraper = SearchScraper(
            "Candidate/Officeholder",
            "CandidateInformationslist",
            "IDNumber",
            "GetCandidatesInformation",
        )
    elif sys.argv[1] == "committees":
        scraper = SearchScraper(
            "Committee",
            "CommitteeInformationlist",
            "IdNumber",
            "GetCommitteeInformation",
        )

    for result in scraper.scrape():

        if writer is None:

            writer = csv.DictWriter(sys.stdout, fieldnames=result.keys())
            writer.writeheader()

        writer.writerow(result)
