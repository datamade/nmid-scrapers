import csv
import logging
import scrapelib
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

writer = csv.DictWriter(
    sys.stdout,
    fieldnames=[
        "CandidateName",
        "OfficeName",
        "ElectionYear",
        "ElectionYearStr",
        "Party",
        "District",
        "Jurisdiction",
        "FinanceType",
        "Status",
        "Incumbent",
        "IDNumber",
        "TreasurerName",
        "CandidateAddress",
        "RegistrationDate",
        "LastFilingDate",
        "PublicPhoneNumber",
        "PoliticalPartyCommitteeName",
        "CandidateStatus",
        "JurisdictionType",
        "OfficerHolderStatus",
        "ElectionName",
        "NumberofCandidates",
        "OfficeId",
        "ElectionId",
        "DistrictId",
        "ElectionCycleId",
        "OfficeType",
        "JurisdictionId",
        "RegistrationId",
        "FinanceStatus",
        "RowNumber",
        "TotalRows",
        "UnregisteredCandidate",
        "StateID",
        "TotalContributions",
        "TotalExpenditures",
        "MemberID",
        "TerminationDate",
        "CandidateEmail",
        "CommitteeEmail",
        "IsCompliant",
        "CompliantStatus",
        "IsLegacy",
    ],
)

writer.writeheader()

s = scrapelib.Scraper(requests_per_minute=10, verify=False)

election_years = ("2021", "2022", "2023", "2024")
payload = {
    "jurisdiction": "",
    "jurisdictionType": "",
    "officeSought": "",
    "year": None,
    "district": "",
    "pageNumber": None,
    "pageSize": 1000,
    "sortDir": "asc",
    "sortedBy": "",
}

for year in election_years:
    page_number = 1
    page_size = 1000
    result_count = 1000

    while result_count == page_size:
        logger.debug(f"Fetching page {page_number} for {year}")

        _payload = payload.copy()
        _payload.update(
            {
                "year": year,
                "pageNumber": page_number,
            }
        )

        logger.debug(_payload)

        response = s.get(
            "https://login.cfis.sos.state.nm.us/api///Organization/GetOffices",
            params=_payload,
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
