import logging
import io
import scrapelib
import sys
import pdfplumber
import abc
import tqdm

from .parse_pdf import parse_pdf

logger = logging.getLogger(__name__)
# logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class SubstringDict:
    def __init__(self, d):
        self._d = d

    def __getitem__(self, target_key):
        (actual_key,) = [key for key in self._d.keys() if target_key in key]
        return self._d[actual_key]


def update_not_null(d1, d2):

    for k, v in d2.items():
        if (d1.get(k) is None) or (v is not None):
            d1[k] = v
    return d1


class SearchScraper(scrapelib.Scraper, abc.ABC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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

    @abc.abstractmethod
    def _filings(self, search_result):
        ...

    def _versions(self, filing):
        versions = [filing]
        if filing["ReportVersionID"] > 1:
            version_response = self.get(
                "https://login.cfis.sos.state.nm.us/api///Filing/GetFilingHistory",
                params={"reportID": filing["ReportVersionID"]},
            )
            versions.extend(version_response.json())

        return versions

    def _parse_filing_pdf(self, version):
        if version["ReportFileName"]:
            try:
                pdf = self.get(
                    f"https://login.cfis.sos.state.nm.us//ReportsOutput//{version['ReportFileName']}"
                )
            except scrapelib.HTTPError:
                return {}
            else:
                version_pdf = pdfplumber.open(io.BytesIO(pdf.content))
                version_table = SubstringDict(parse_pdf(version_pdf))
                return {
                    "opening_balance": version_table[
                        "OPENING BALANCE for reporting period"
                    ],
                    "closing_balance": version_table[
                        "Closing Balance this Reporting Period"
                    ],
                }
        else:
            return {}

    def scrape(self):
        for search_result in tqdm.tqdm(
            self._search_results(self.search_type, self.result_key, self.id_key)
        ):
            response = self.get(
                self.detail_endpoint, params={"memberId": search_result[self.id_key]}
            )

            data = {
                "filings": self._filings(search_result),
                "yearly_info": [
                    update_not_null(search_result, year_data)
                    for year_data in response.json()
                ],
            }

            yield data


class CandidateScraper(SearchScraper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_type = "Candidate/Officeholder"
        self.result_key = "CandidateInformationslist"
        self.id_key = "IDNumber"
        self.detail_endpoint = "https://login.cfis.sos.state.nm.us/api///Organization/GetCandidatesInformation"

    def _filings(self, search_result):
        payload = {
            "officeID": search_result["OfficeId"],
            "electionYear": "All",
            "districtId": search_result["DistrictId"] or "null",
            "electionId": int(search_result["ElectionId"]),
            "FilerNameLink": "exploreDetails",
            "committeeID": search_result[self.id_key],
            "pageNumber": 1,
            "pageSize": 100,
        }

        filings = self.get(
            "https://login.cfis.sos.state.nm.us/api///Filing/GetFilings",
            params=payload,
        ).json()

        data = []

        for filing in filings:
            for version in self._versions(filing):
                if version["FilerType"] in {"Candidate"}:
                    version = version | self._parse_filing_pdf(version)
                data.append(version)

        return data


class CommitteeScraper(SearchScraper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_type = "Committee"
        self.result_key = "CommitteeInformationlist"
        self.id_key = "IdNumber"
        self.detail_endpoint = "https://login.cfis.sos.state.nm.us/api///Organization/GetCommitteeInformation"

    def _filings(self, search_result):
        payload = {
            "officeID": 0,
            "electionYear": "All",
            "districtId": 0,
            "electionId": 0,
            "FilerNameLink": "exploreCommitteeDetails",
            "committeeID": search_result[self.id_key],
            "pageNumber": 1,
            "pageSize": 100,
        }

        filings = self.get(
            "https://login.cfis.sos.state.nm.us/api///Filing/GetFilings",
            params=payload,
        ).json()

        data = []

        for filing in filings:
            for version in self._versions(filing):
                if version["FilerType"] in {"Political Committee"}:
                    try:
                        version = version | self._parse_filing_pdf(version)
                    except:
                        breakpoint()
                data.append(version)

        return data


if __name__ == "__main__":
    import csv
    from scrapelib.cache import FileCache

    cache = FileCache("cache")

    if sys.argv[1] == "candidates":
        scraper_klass = CandidateScraper
        committee_file = open("candidate_committees.csv", "w")
        filing_file = open("candidate_committee_filings.csv", "w")

    elif sys.argv[1] == "committees":
        scraper_klass = CommitteeScraper
        committee_file = open("pac_committees.csv", "w")
        filing_file = open("pac_committee_filings.csv", "w")

    scraper = scraper_klass(requests_per_minute=0, retry_attempts=3)
    scraper.timeout = 10
    scraper.cache_storage = cache
    scraper.cache_write_only = False

    committee_writer = None
    filing_writer = None

    for result in scraper.scrape():
        years = result["yearly_info"]
        filings = result["filings"]

        if committee_writer is None and years:
            committee_writer = csv.DictWriter(
                committee_file, fieldnames=years[0].keys()
            )
            committee_writer.writeheader()

        if filing_writer is None and filings:

            filing_writer = csv.DictWriter(
                filing_file, fieldnames=["StateID"] + list(filings[0].keys())
            )
            filing_writer.writeheader()

        for year in years:
            committee_writer.writerow(year)

        state_id = years[0]["StateID"]

        for filing in filings:
            filing_writer.writerow(filing | {"StateID": state_id})
