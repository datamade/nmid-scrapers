import sys
import csv


reader = csv.DictReader(sys.stdin)
writer = csv.DictWriter(sys.stdout, fieldnames=reader.fieldnames)

writer.writeheader()

previous_row = None
for row in reader:
    if row != previous_row:
        writer.writerow(row)
        previous_row = row
