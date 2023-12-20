disclosures.zip : employer.csv filer.csv filing.csv spouse_employer.csv
	zip $@ $^

%.csv :
	python scripts/financial_disclosures.py

data/processed/offices.csv :
	python -m scrapers.office.scrape_offices > $@

data/processed/candidates.csv : data/processed/offices.csv
	cat $< | python -m scrapers.office.scrape_candidates > $@
