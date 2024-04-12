import pdfplumber

Row = tuple[str | None, ...]
Rows = tuple[Row, ...]


def parse_pdf(pdf: pdfplumber.PDF) -> dict[str, dict[str, str | None]]:
    table_settings = {
        "intersection_tolerance": 6,
    }

    result = {}
    for page in pdf.pages:
        for table in page.extract_tables(table_settings=table_settings):
            if len(table[0]) == 3:
                result.update({row[1]: row[2] for row in table})

                headers = {(row[0], row[1]) for row in table}
                if (
                    "h.",
                    "Total In-Kind Contributions this Reporting Period (Form B2)",
                ) in headers:
                    return result
