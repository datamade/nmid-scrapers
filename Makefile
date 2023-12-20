disclosures.zip : employer.csv filer.csv filing.csv spouse_employer.csv
	zip $@ $^

%.csv :
	python scripts/financial_disclosures.py
