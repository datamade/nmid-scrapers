import csv
import sys

writer = csv.writer(sys.stdout)

with open(sys.argv[1]) as header_file:
    header_reader = csv.reader(header_file)
    writer.writerows(header_reader)

data_reader = csv.reader(sys.stdin)
next(data_reader)
writer.writerows(data_reader)
