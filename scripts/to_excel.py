import pandas as pd
import os
import sys


def csv_to_excel(csv_files, output_excel):
    with pd.ExcelWriter(output_excel) as writer:
        for csv_file in csv_files:
            sheet_name = os.path.basename(csv_file).split(".")[
                0
            ]  # Use file name as sheet name
            df = pd.read_csv(csv_file)
            df.to_excel(writer, sheet_name=sheet_name, index=False)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python csv_to_excel.py <csv_file1> <csv_file2> ... <output_excel>"
        )
        sys.exit(1)

    csv_files = sys.argv[1:-1]
    output_excel = sys.argv[-1]

    csv_to_excel(csv_files, output_excel)
