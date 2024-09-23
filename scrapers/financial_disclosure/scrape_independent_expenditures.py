import csv
import json
import logging
import scrapelib
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class IndependentExpenditureScraper(scrapelib.Scraper):
    election_years = ("2021", "2022", "2023", "2024")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _get_donor_details(self, transaction_id):
        donor_details_resp = self.get(
            "https://login.cfis.sos.state.nm.us/api/Public/"
            f"GetIEDonors?transactionId={transaction_id}&transactionVersId=1"
        )

        if not donor_details_resp.ok:
            return None

        donor_details = donor_details_resp.json()
        if not donor_details:
            return [
                {
                    "DonorName": None,
                    "DonorAmount": None,
                    "DonorAddress": None,
                }
            ]

        return [
            {
                "DonorName": donor["DonorName"],
                "DonorAmount": donor["DonatedAmount"],
                "DonorAddress": donor["Donor"]["Address"]["CompleteAddress"],
            }
            for donor in donor_details
        ]

    def _expenditures(self, year):
        payload = {
            "TransactionType": "IE",
            "CommitteeType": None,
            "ElectionYear": year,
            "CommitteeName": None,
            "TransactionCategoryCode": None,
            "AmountType": None,
            "ContributorPayeeName": None,
            "TransactionBeginDate": None,
            "TransactionEndDate": None,
            "ValidationRequired": 0,
            "pageNumber": 1,
            "pageSize": 1000,
            "sortDir": "asc",
            "sortedBy": "",
            "TransactionAmount": None,
            "TransactionUnderAmount": None,
            "pacType": "",
            "Occupation": None,
            "StateCode": None,
            "city": None,
            "Zipcode": None,
            "ZipExt": None,
            "Reason": None,
            "Stance": "",
        }

        page_number = 1
        page_size = 1000
        result_count = 1000

        while result_count == page_size:
            logger.debug(f"Fetching page {page_number} for {year}")

            _payload = payload.copy()
            _payload.update({"PageNo": page_number})

            logger.debug(_payload)

            response = self.post(
                "https://login.cfis.sos.state.nm.us/api///"
                "Search/TransactionSearchInformation",
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
        for year in IndependentExpenditureScraper.election_years:
            for result in self._expenditures(year):
                transaction_id = result["TransactionId"]

                donors = self._get_donor_details(transaction_id)
                for donor in donors:
                    yield {
                        "ReportingEntityName": result["Name"],
                        "ReportingEntityType": result["CommitteeType"],
                        "Payee": result["ContributorPayeeName"],
                        "PayeeType": result["EntityTypeDescription"],
                        "PayeeAddress": result["Address"],
                        "TransactionDate": result["TransactionDate"],
                        "ExpenditureAmount": result["Amount"],
                        "ExpenditureDescription": result[
                            "TransactionPurposeDescription"
                        ],
                        "ElectionYear": result["ElectionYear"],
                        "ElectionType": result["ElectionPeriod"],
                        "Reason": result["Reason"],
                        "Stance": result["Stance"],
                        **donor,
                    }


if __name__ == "__main__":
    writer = csv.DictWriter(
        sys.stdout,
        fieldnames=[
            "TransactionDate",
            "ReportingEntityName",
            "ReportingEntityType",
            "Payee",
            "PayeeType",
            "PayeeAddress",
            "ExpenditureAmount",
            "ExpenditureDescription",
            "ElectionType",
            "ElectionYear",
            "Reason",
            "Stance",
            "DonorName",
            "DonorAddress",
            "DonorAmount",
        ],
        extrasaction="ignore",
    )

    writer.writeheader()

    scraper = IndependentExpenditureScraper(
        requests_per_minute=60, retry_attempts=3, verify=False
    )
    for result in scraper.scrape():
        writer.writerow(result)
