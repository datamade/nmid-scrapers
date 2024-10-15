import csv
import itertools
import os
import sys

import pdfplumber
from tqdm import tqdm


def extract_transactions(pdf_obj, table_start_signature, table_end_signature):
    found_table = False
    transactions = []

    for page in pdf_obj.pages:
        if page.search(table_start_signature):
            transactions.extend(page.extract_table())
            found_table = True
            continue

        # Once we've found the table, continue to add records from
        # subsequent pages until we reach the next table.
        if found_table:
            if table_end_signature and page.search(table_end_signature):
                break

            table = page.extract_table()

            try:
                assert table and (len(table[0]) == len(transactions[0]))
            except AssertionError:
                break

            transactions.extend(table)

    return transactions


def main(transaction_type, asset_directory):
    if transaction_type == "expenditures":
        column_names = [
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
        table_start_signature = "FORM B\nEXPENDITURES"
        table_end_signature = "FORM C\nSPECIAL EVENTS"

    else:
        column_names = [
            "Date",
            "Name of candidate, public official or ballot question supported or opposed",
            "Contribution On Behalf Of",
            "Amount",
            "Source",
            "File path",
        ]
        table_start_signature = "FORM D\nPOLITICAL CONTRIBUTIONS"
        table_end_signature = None

    writer = csv.writer(sys.stdout)
    writer.writerow(column_names)

    try:
        null_file = open(f"empty_{transaction_type}_filings.csv", "w")
        null_writer = csv.writer(null_file)
        null_writer.writerow(["Source", "File path"])

        for root, _, files in tqdm(
            itertools.chain(
                os.walk(os.path.join(asset_directory, "LAR")),
                os.walk(os.path.join(asset_directory, "LCD")),
                os.walk(os.path.join(asset_directory, "LNA")),
            )
        ):
            for file in files:
                if not file.endswith(".pdf"):
                    continue

                pdf = pdfplumber.open(os.path.join(root, file))

                transactions = extract_transactions(
                    pdf, table_start_signature, table_end_signature
                )

                if not transactions or len(transactions) == 1:
                    null_writer.writerow([file, os.path.join(root, file)])
                    continue

                for row in transactions[1:]:  # Skip the header row
                    row.extend([file, os.path.join(root, file)])
                    writer.writerow(map(lambda x: x.replace("\n", " "), row))

    finally:
        null_file.close()


if __name__ == "__main__":
    main("expenditures", "assets")
