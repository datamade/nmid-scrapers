import io
import itertools
import re

import pdfplumber
import scrapelib
import tqdm


class FinancialDisclosureScraper(scrapelib.Scraper):
    def _filers(self):

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
            "pageSize": 10,
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
                    pbar.refresh()

                for filer in response.json():
                    params = {
                        "MemberID": filer["IDNumber"],
                        "MemberVersionID": filer["MemberVersionID"],
                        "year": filer["FilingYear"],
                        "pageNumber": 1,
                        "pageSize": 10,
                        "sortBy": "ReportType",
                        "sortDir": "asc",
                    }

                    filer_detail_response = self.get(
                        "https://login.cfis.sos.state.nm.us/api///SfiFiling/GetFilerDetail",
                        params=params,
                    )

                    assert (
                        len(filer_detail_response.json()["FilterDetailList"]) <= 10
                    ), f"More than 10 filings in this detail page, we may need to implement paging: {filer_detail_response.request.url}."

                    yield filer_detail_response.json()

                    pbar.update(1)

                if len(response.json()) < 10:
                    break
                else:
                    payload["pageNumber"] += 1

    def scrape(self):

        for filer_data in self._filers():

            for filing in filer_data["FilterDetailList"]:

                response = self.get(
                    f"https://login.cfis.sos.state.nm.us//ReportsOutput//SFI/{filing['ReportFileName']}"
                )

                filing_pdf = pdfplumber.open(io.BytesIO(response.content))

                try:
                    pdf_info = parse_pdf(filing_pdf)
                except Exception as err:
                    raise ValueError(f"Error on {response.request.url}") from err

                filing["extracted_info"] = pdf_info

            yield filer_data


def is_section(row):
    return re.match(r"^\d+\. [A-Z]", row[0])


def group_rows(rows):
    key = None

    def key_function(row):
        nonlocal key
        if is_section(row):
            key = row[0]
        return key

    grouped_rows = itertools.groupby(rows, key=key_function)

    return {section: tuple(rows) for section, rows in grouped_rows}


def parse_value(value):

    results = value.split("\n", 1)
    if len(results) == 2:
        return results
    else:
        return results[0], None


def parse_employer(rows):

    header, *rows = rows

    result = dict(parse_value(value) for row in rows for value in row if value)

    return result


def parse_pdf(pdf):

    rows = (tuple(row) for page in pdf.pages for row in page.extract_table())

    grouped_rows = group_rows(rows)

    return {
        "employer": parse_employer(
            grouped_rows["3. REPORTING INDIVIDUAL - Employer Information"]
        ),
        "spouse's employer": parse_employer(
            grouped_rows["4. SPOUSE OF REPORTING INDIVIDUAL – Employer Information"]
        ),
    }


if __name__ == "__main__":
    import csv

    with (
        open("filer.csv", "w") as filer_file,
        open("filing.csv", "w") as filing_file,
        open("employer.csv", "w") as employer_file,
        open("spouse_employer.csv", "w") as spouse_employer_file,
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
        filer_writer.writeheader()
        filing_writer.writeheader()
        employer_writer.writeheader()
        spouse_employer_writer.writeheader()

        scraper = FinancialDisclosureScraper()
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
                employer_writer.writerow(
                    extracted_info["employer"] | {"ReportID": report_id}
                )
                spouse_employer_writer.writerow(
                    extracted_info["spouse's employer"] | {"ReportID": report_id}
                )
