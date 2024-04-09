import pdfplumber

Row = tuple[str | None, ...]
Rows = tuple[Row, ...]


def parse_pdf(pdf: pdfplumber.PDF) -> dict[str, dict[str, str | None]]:
    table_settings = {
        "intersection_tolerance": 6,
    }

    filing_table_rows = pdf.pages[0].extract_table(table_settings=table_settings)

    result = {row[1]: row[2] for row in filing_table_rows[1:]}

    return result
