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

s = scrapelib.Scraper(requests_per_minute=10)

ALPHABET = "abcdefghijklmnopqrstuvwxyz"

payload = {
    "searchText": "a",
    "searchType": "Candidate/Officeholder",
    "pageNumber": 1,
    "pageSize": 1000,
    "sortDir": "asc",
    "sortedBy": "",
}

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

        response = s.get(
            "https://login.cfis.sos.state.nm.us/api///Search/GetPublicSiteBasicSearchResult",
            params=_payload,
        )

        if response.ok:
            results = response.json()["CandidateInformationslist"]
            writer.writerows(results)
            result_count = len(results)

            logger.debug(f"Last page {page_number} had {result_count} results")

            page_number += 1
        else:
            logger.error(
                f"Failed to fetch results:\n{response.content.decode('utf-8')}"
            )
            sys.exit()
