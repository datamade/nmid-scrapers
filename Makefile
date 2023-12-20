data/processed/disclosures.zip : data/intermediate/employer.csv \
	data/intermediate/filer.csv \
	data/intermediate/filing.csv \
	data/intermediate/spouse_employer.csv
	zip $@ $^

data/intermediate/%.csv :
	python -m scrapers.financial_disclosure.scrape_financial_disclosures

data/processed/offices.csv :
	python -m scrapers.office.scrape_offices > $@

data/processed/candidates.csv : data/processed/offices.csv
	cat $< | python -m scrapers.office.scrape_candidates > $@
