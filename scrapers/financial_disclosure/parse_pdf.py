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
    return re.match(r"^\d+\. ?[A-Z]", row[0]) is not None  # type: ignore[arg-type]


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


def parse_pdf(pdf: pdfplumber.PDF) -> dict[str, dict[str, str | None]]:

    rows = [tuple(row) for page in pdf.pages if (table := page.extract_table()) for row in table]  # type: ignore[union-attr]

    grouped_rows = SubstringDict(_group_rows(rows))

    return {
        "employer": _parse_employer(
            grouped_rows["REPORTING INDIVIDUAL - Employer Information"]
        ),
        "spouse's employer": _parse_employer(
            grouped_rows["SPOUSE OF REPORTING INDIVIDUAL – Employer Information"]
        ),
        "current filing status": _parse_filing_status(
            grouped_rows["REPORTING INDIVIDUAL – Current Filing Status"]
        ),
    }
