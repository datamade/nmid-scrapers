import csv
import itertools
import os
import sys

import pdfplumber

writer = csv.writer(sys.stdout)
writer.writerow(
    [
        "Date",
        "Name of payee",
        "Beneficiary",
        "Type",
        "Purpose for which made or incurred",
        "Expenditure On Behalf Of",
        "Amount",
        "Source",
        "File path",
    ]
)

null_file = open("empty_filings.csv", "w")
null_writer = csv.writer(null_file)
null_writer.writerow(["Source", "File path"])

try:
    for root, _, files in itertools.chain(
        os.walk("data/pdfs/LAR"), os.walk("data/pdfs/LCD")
    ):
        for file_index, file in enumerate(files):
            if not file.endswith(".pdf"):
                continue

            pdf = pdfplumber.open(os.path.join(root, file))

            found_table = False
            rows = []

            for page in pdf.pages:
                if page.search("FORM B\nEXPENDITURES"):
                    rows.extend(page.extract_table())
                    found_table = True
                    continue

                # Once we've found the table, continue to add records from
                # subsequent pages provided the table has the same number of
                # columns and we have not hit Form C.
                if found_table:
                    if page.search("FORM C\nSPECIAL EVENTS"):
                        break

                    table = page.extract_table()

                    try:
                        assert table and (len(table[0]) == len(rows[0]))
                    except AssertionError:
                        break

                    rows.extend(table)

            if not found_table:
                null_writer.writerow([file, os.path.join(root, file)])

            for row_index, row in enumerate(rows):
                if row_index == 0:
                    continue

                row.extend([file, os.path.join(root, file)])

                writer.writerow(map(lambda x: x.replace("\n", " "), row))

finally:
    null_file.close()
