import io
from typing import Generator

import pdfplumber
import scrapelib
import tqdm

from scrapers.financial_disclosure import levenshtein_distance, parse_pdf


class FinancialDisclosureScraper(scrapelib.Scraper):
    def _filers(self) -> Generator[dict[str, dict], None, None]:
        PAGE_SIZE = 5000

        years = self.get(
            "https://login.cfis.sos.state.nm.us/api///SfiExploreFiler/GetFilerDetailsYear"
        ).json()

        payload = {
            "FilingYear": ",".join(str(year["FilingYear"]) for year in years),
            "ReportType": None,
            "OfficeID": None,
            "TownID": None,
            "DistrictID": None,
            "AgencyID": None,
            "pageNumber": 1,
            "pageSize": PAGE_SIZE,
            "sortDir": "ASC",
        }

        total = None

        with tqdm.tqdm() as pbar:
            while True:
                response = self.post(
                    "https://login.cfis.sos.state.nm.us/api///SfiExploreFiler/SearchFilers",
                    json=payload,
                )

                if total is None:
                    pbar.total = total = response.json()[0]["TotalRows"]
                    assert total >= 1721
                    pbar.refresh()

                for filer in response.json():
                    # setting "year" to filer["FilingYear"] gets us
                    # the most recent filing.
                    #
                    # if we want to get all, historical filings set
                    # "year" to 0.
                    params = {
                        "MemberID": filer["IDNumber"],
                        "MemberVersionID": filer["MemberVersionID"],
                        "year": filer["FilingYear"],
                        "pageNumber": 1,
                        "pageSize": PAGE_SIZE,
                        "sortBy": "ReportType",
                        "sortDir": "asc",
                    }

                    filer_detail_response = self.get(
                        "https://login.cfis.sos.state.nm.us/api///SfiFiling/GetFilerDetail",
                        params=params,
                    )

                    assert (
                        len(filer_detail_response.json()["FilterDetailList"])
                        <= PAGE_SIZE
                    ), f"More than {PAGE_SIZE} filings in this detail page, we may need to implement paging: {filer_detail_response.request.url}."

                    yield filer_detail_response.json()

                    pbar.update(1)

                if len(response.json()) < PAGE_SIZE:
                    assert pbar.n == pbar.total
                    break
                else:
                    payload["pageNumber"] += 1  # type: ignore[operator]

    def scrape(self) -> Generator[dict[str, dict], None, None]:
        for filer_data in self._filers():
            for filing in filer_data["FilterDetailList"]:
                response = self.get(
                    f"https://login.cfis.sos.state.nm.us//ReportsOutput//SFI/{filing['ReportFileName']}"
                )

                filing_pdf = pdfplumber.open(io.BytesIO(response.content))

                try:
                    pdf_info = parse_pdf.parse_pdf(filing_pdf)
                except Exception as err:
                    raise ValueError(f"Error on {response.request.url}") from err

                filing["extracted_info"] = pdf_info

            yield filer_data


if __name__ == "__main__":
    import csv

    with (
        open("data/intermediate/filer.csv", "w") as filer_file,
        open("data/intermediate/filing.csv", "w") as filing_file,
        open("data/intermediate/employer.csv", "w") as employer_file,
        open("data/intermediate/spouse_employer.csv", "w") as spouse_employer_file,
        open("data/intermediate/filing_status.csv", "w") as filing_status_file,
        open("data/intermediate/income.csv", "w") as income_file,
        open("data/intermediate/specializations.csv", "w") as specializations_file,
        open("data/intermediate/consulting.csv", "w") as consulting_file,
        open("data/intermediate/real_estate.csv", "w") as real_estate_file,
        open("data/intermediate/business.csv", "w") as business_file,
        open("data/intermediate/membership.csv", "w") as membership_file,
        open("data/intermediate/licenses.csv", "w") as licenses_file,
        open("data/intermediate/provisions.csv", "w") as provisions_file,
        open("data/intermediate/representation.csv", "w") as representation_file,
        open("data/intermediate/general.csv", "w") as general_file,
    ):
        filer_writer = csv.DictWriter(
            filer_file,
            ["FilerName", "FullAddress", "Phone", "DateRegistered", "FilerID"],
        )
        filing_writer = csv.DictWriter(
            filing_file,
            [
                "ReportType",
                "FilingRequirement",
                "FilingYear",
                "FiledDate",
                "TotalCount",
                "ReportFileName",
                "ReportTypeCode",
                "ScanFlag",
                "isCheckinFlag",
                "ReportStatus",
                "DocumentFileName",
                "ImageExists",
                "ReportVersionID",
                "ReportID",
                "Type",
                "Description",
                "Date",
                "Amount",
                "Balance",
                "Status",
                "MemberID",
                "Filed",
                "IsLateFiled",
                "FilerID",
            ],
        )
        employer_writer = csv.DictWriter(
            employer_file,
            [
                "Employer",
                "Employer's Phone Number",
                "P.O. Box or Street Address of Employer",
                "City State Zip",
                "Title or Position held by reporting individual",
                "Nature of business or occupation",
                "ReportID",
            ],
        )
        spouse_employer_writer = csv.DictWriter(
            spouse_employer_file,
            [
                "Last Name",
                "First Name",
                "Middle",
                "Name of Spouse’s Employer",
                "Address of Spouse’s Employer",
                "City",
                "State",
                "Zip",
                "Spouse’s title or position held Nature of business or occupation",
                "ReportID",
            ],
        )
        filing_status_writer = csv.DictWriter(
            filing_status_file,
            [
                "Reporting individual",
                "Office / Board or Commission / Agency Name",
                "Date Assumed Office, Employed, or Appointed",
                "ReportID",
            ],
        )
        income_writer = csv.DictWriter(
            income_file,
            [
                "Income source (*see pg. 4):",
                "Received by (list the name of the reporting individual or spouse):",
                "ReportID",
            ],
        )
        specializations_writer = csv.DictWriter(
            specializations_file,
            [
                "Describe the major areas of specialization or sources of income.",
                "Received by (list the name of the reporting individual or spouse):",
                "ReportID",
            ],
        )
        consulting_writer = csv.DictWriter(
            consulting_file,
            [
                "Client name & address:",
                "Represented by: List the name of the reporting individual’s firm or spouse’s firm",
                "ReportID",
            ],
        )
        real_estate_writer = csv.DictWriter(
            real_estate_file,
            ["Owner", "County", "General Description", "ReportID"],
        )
        business_writer = csv.DictWriter(
            business_file,
            [
                "Name of business:",
                "Position held:",
                "General statement of business purpose:",
                "Received by (list the name of the reporting individual or spouse):",
                "ReportID",
            ],
        )
        membership_writer = csv.DictWriter(
            membership_file,
            [
                "Name of business:",
                "Board member (list the name of the reporting individual or spouse):",
                "ReportID",
            ],
        )
        licenses_writer = csv.DictWriter(
            licenses_file,
            [
                "Type of license:",
                "Individual holding license (list the name of the reporting individual or spouse):",
                "ReportID",
            ],
        )
        provisions_writer = csv.DictWriter(
            provisions_file,
            [
                "State agency to which goods and/or services were provided:",
                "Individual providing goods or services (list the name of the reporting individual or spouse):",
                "ReportID",
            ],
        )
        representation_writer = csv.DictWriter(
            representation_file,
            [
                "State agency (other than a court):",
                "Individual assisting client (list the name of the reporting individual or spouse):",
                "ReportID",
            ],
        )
        general_writer = csv.DictWriter(
            general_file,
            ["Input", "ReportID"],
        )

        # pdf fields that return lists of similarly structured dicts
        mapping_dict = {
            "filing_status": {
                "file": filing_status_file,
                "writer": filing_status_writer,
                "corrector": levenshtein_distance.SpellingCorrector(
                    filing_status_writer.fieldnames
                ),
                "accessor": "current filing status",
            },
            "income": {
                "file": income_file,
                "writer": income_writer,
                "corrector": levenshtein_distance.SpellingCorrector(
                    income_writer.fieldnames
                ),
                "accessor": "income sources",
            },
            "specializations": {
                "file": specializations_file,
                "writer": specializations_writer,
                "corrector": levenshtein_distance.SpellingCorrector(
                    specializations_writer.fieldnames
                ),
                "accessor": "specializations",
            },
            "consulting": {
                "file": consulting_file,
                "writer": consulting_writer,
                "corrector": levenshtein_distance.SpellingCorrector(
                    consulting_writer.fieldnames
                ),
                "accessor": "consulting or lobbying",
            },
            "real_estate": {
                "file": real_estate_file,
                "writer": real_estate_writer,
                "corrector": levenshtein_distance.SpellingCorrector(
                    real_estate_writer.fieldnames
                ),
                "accessor": "real estate",
            },
            "business": {
                "file": business_file,
                "writer": business_writer,
                "corrector": levenshtein_distance.SpellingCorrector(
                    business_writer.fieldnames
                ),
                "accessor": "other business",
            },
            "membership": {
                "file": membership_file,
                "writer": membership_writer,
                "corrector": levenshtein_distance.SpellingCorrector(
                    membership_writer.fieldnames
                ),
                "accessor": "board membership",
            },
            "licenses": {
                "file": licenses_file,
                "writer": licenses_writer,
                "corrector": levenshtein_distance.SpellingCorrector(
                    licenses_writer.fieldnames
                ),
                "accessor": "professional licenses",
            },
            "provisions": {
                "file": provisions_file,
                "writer": provisions_writer,
                "corrector": levenshtein_distance.SpellingCorrector(
                    provisions_writer.fieldnames
                ),
                "accessor": "provisions to state agencies",
            },
            "representation": {
                "file": representation_file,
                "writer": representation_writer,
                "corrector": levenshtein_distance.SpellingCorrector(
                    representation_writer.fieldnames
                ),
                "accessor": "state agency representation",
            },
            "general": {
                "file": general_file,
                "writer": general_writer,
                "corrector": levenshtein_distance.SpellingCorrector(
                    general_writer.fieldnames
                ),
                "accessor": "general info",
            },
        }

        for pdf_field in mapping_dict.values():
            pdf_field["writer"].writeheader()

        filer_writer.writeheader()
        filing_writer.writeheader()
        employer_writer.writeheader()
        spouse_employer_writer.writeheader()

        employer_field_corrector = levenshtein_distance.SpellingCorrector(
            employer_writer.fieldnames
        )
        spouse_employer_field_corrector = levenshtein_distance.SpellingCorrector(
            spouse_employer_writer.fieldnames
        )

        scraper = FinancialDisclosureScraper()
        scraper.requests_per_minute = 0
        for filer in scraper.scrape():
            filer_writer.writerow(filer["FilerInfo"])
            filer_id = filer["FilerInfo"]["FilerID"]

            for filing in filer["FilterDetailList"]:
                extracted_info = filing.pop("extracted_info")

                # foreign key to filer
                filing["FilerID"] = filer_id
                filing_writer.writerow(filing)

                # push foreign key down into extracted tables
                report_id = filing["ReportID"]

                employer_data = {
                    employer_field_corrector.correct(k): v
                    for k, v in extracted_info["employer"].items()
                }
                employer_writer.writerow(employer_data | {"ReportID": report_id})

                spouse_employer_data = {
                    spouse_employer_field_corrector.correct(k): v
                    for k, v in extracted_info["spouse's employer"].items()
                }
                spouse_employer_writer.writerow(
                    spouse_employer_data | {"ReportID": report_id}
                )

                for pdf_field in mapping_dict.values():
                    accessor = pdf_field["accessor"]
                    corrector = pdf_field["corrector"]
                    writer = pdf_field["writer"]

                    for entry in extracted_info[accessor]:
                        field_data = {corrector.correct(k): v for k, v in entry.items()}
                        writer.writerow(field_data | {"ReportID": report_id})
