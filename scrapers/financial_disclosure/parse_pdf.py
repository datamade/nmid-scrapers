import itertools
import re
from typing import Iterable

import pdfplumber

Row = tuple[str | None, ...]
Rows = tuple[Row, ...]


class SubstringDict:
    def __init__(self, d):
        self._d = d

    def __getitem__(self, target_key):
        (actual_key,) = [key for key in self._d.keys() if target_key in key]
        return self._d[actual_key]


def _is_section(row: Row) -> bool:
    return (
        re.match(r"^\d+\. ?[A-Z]", row[0]) is not None  # type: ignore[arg-type]
        or row[0].startswith("*Pursuant to NMSA 1978 §")  # ensure signature is its own section
    )


def _group_rows(rows: Iterable[Row]) -> dict[str, Rows]:
    key = None

    def key_function(row: Row):
        nonlocal key
        if _is_section(row):
            key = row[0]
        return key

    grouped_rows = itertools.groupby(rows, key=key_function)

    return {section: tuple(rows) for section, rows in grouped_rows}


def _parse_value(value: str) -> tuple[str, str | None]:

    results = tuple(value.split("\n", 1))
    if len(results) == 2:
        return results
    else:
        return results[0], None


def _parse_employer(rows: Rows) -> dict[str, str | None]:

    header, *body = rows

    result = dict(_parse_value(value) for row in body for value in row if value)

    return result


def _parse_filing_status(rows: Rows) -> dict[str, str | None]:

    header, title_row, *body = rows

    fields = [
        " ".join(value.split()) for value in title_row if value
    ]  # Remove extra whitespace from field names
    table_rows = [[value for value in row if value] for row in body]
    result = [
        {field: val for field, val in zip(fields, table_row)}
        for table_row in table_rows
    ]

    return result


def _parse_general_info(rows: Rows) -> dict[str, str | None]:

    header, *body = rows

    result = [{"Input": val[0]} for val in body]
    
    return result


def parse_pdf(pdf: pdfplumber.PDF) -> dict[str, dict[str, str | None]]:

    rows = [tuple(row) for page in pdf.pages for row in page.extract_table()]  # type: ignore[union-attr]

    grouped_rows = SubstringDict(_group_rows(rows))

    result = {
        "employer": _parse_employer(
            grouped_rows["REPORTING INDIVIDUAL - Employer Information"]
        ),
        "spouse's employer": _parse_employer(
            grouped_rows["SPOUSE OF REPORTING INDIVIDUAL – Employer Information"]
        ),
        "current filing status": _parse_filing_status(
            grouped_rows["REPORTING INDIVIDUAL – Current Filing Status"]
        ),
        "income sources": _parse_filing_status(
            grouped_rows["REPORTING INDIVIDUAL & REPORTING INDIVIDUAL’S SPOUSE – Income Source(s)"]
        ),
        "specializations": _parse_filing_status(
            grouped_rows["REPORTING INDIVIDUAL & REPORTING INDIVIDUAL’S SPOUSE - Areas of Specialization"]
        ),
        "consulting or lobbying": _parse_filing_status(
            grouped_rows["REPORTING INDIVIDUAL & REPORTING INDIVIDUAL’S SPOUSE - Consulting and/or Lobbying"]
        ),
        "real estate": _parse_filing_status(
            grouped_rows["REPORTING INDIVIDUAL & REPORTING INDIVIDUAL’S SPOUSE – Real Estate"]
        ),
        "other business": _parse_filing_status(
            grouped_rows["REPORTING INDIVIDUAL & REPORTING INDIVIDUAL’S SPOUSE – Other Business"]
        ),
        "board membership": _parse_filing_status(
            grouped_rows["REPORTING INDIVIDUAL & REPORTING INDIVIDUAL’S SPOUSE\nBoard Membership"]
        ),
        "professional licenses": _parse_filing_status(
            grouped_rows["REPORTING INDIVIDUAL & REPORTING INDIVIDUAL’S SPOUSE – Professional License(s)"]
        ),
        "provisions to state agencies": _parse_filing_status(
            grouped_rows["REPORTING INDIVIDUAL & REPORTING INDIVIDUAL’S SPOUSE\nGoods and/or Services Provided to State Agencies"]
        ),
        "state agency representation": _parse_filing_status(
            grouped_rows["REPORTING INDIVIDUAL & REPORTING INDIVIDUAL’S SPOUSE\nState Agency Representation"]
        ),
    }

    try:
        result["general info"] = _parse_general_info(
            grouped_rows["REPORTING INDIVIDUAL & REPORTING INDIVIDUAL’S SPOUSE – General Information"]
        )
    except ValueError:
        # this table may appear by itself on a page as a single cell if empty.
        # pdfplumber will ignore it in this case, so this adds an empty input
        result["general info"] = []

    return result
