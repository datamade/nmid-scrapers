import csv
import os
import sys

import pdfplumber

writer = csv.writer(sys.stdout)

for file_index, file in enumerate(os.listdir("data/pdfs")):
    pdf = pdfplumber.open(os.path.join("data/pdfs", file))

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

    for row_index, row in enumerate(rows):
        # Don't endlessly add the header
        if file_index > 0 and row_index == 0:
            continue

        if row_index == 0:
            row.append("Source")
        else:
            row.append(file)

        writer.writerow(map(lambda x: x.replace("\n", " "), row))
