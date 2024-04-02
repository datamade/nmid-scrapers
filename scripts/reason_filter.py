import sys
import csv
import itertools
import pprint

reader = csv.DictReader(sys.stdin)
writer = csv.DictWriter(sys.stdout, fieldnames=reader.fieldnames)

writer.writeheader()

for _, group in itertools.groupby(reader, key=lambda x: x["ReportID"]):
    chosen = max(
        group, key=lambda item: item["Date Assumed Office, Employed, or Appointed"]
    )
    writer.writerow(chosen)
