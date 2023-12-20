import csv
import itertools
import json
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

reader = csv.DictReader(sys.stdin)

s = scrapelib.Scraper(requests_per_minute=45)

payload = {
    "officeId": None,
    "year": 0,
    "districtId": None,
    "electionId": None,
    "jurisdictionId": "",
    "pageNumber": None,
    "pageSize": 100,
    "sortDir": "desc",
    "sortedBy": "sortedBy",
    "ElectionCycleId": "All",
}

group_func = lambda office: (
    office["OfficeId"],
    office["DistrictId"],
    office["ElectionId"],
)
for (office_id, district_id, election_id), _ in itertools.groupby(
    sorted(reader, key=group_func), key=group_func
):
    page_number = 1
    page_size = 100
    result_count = 100

    while result_count == page_size:
        logger.debug(f"Fetching page {page_number}")

        _payload = payload.copy()
        _payload.update(
            {
                "officeId": office_id,
                "districtId": district_id,
                "electionId": election_id,
                "pageNumber": page_number,
            }
        )

        logger.debug(_payload)

        response = s.get(
            "https://login.cfis.sos.state.nm.us/api///Organization/GetCandidateComparision",
            params=_payload,
        )

        if response.ok:
            results = response.json()
            writer.writerows((r["CandidateInformations"] for r in results))
            result_count = len(results)

            logger.debug(f"Last page {page_number} had {result_count} results")

            page_number += 1
        else:
            logger.error(
                f"Failed to fetch results:\n{response.content.decode('utf-8')}"
            )
            sys.exit()
