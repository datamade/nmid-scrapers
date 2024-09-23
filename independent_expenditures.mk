.PHONY: independent_expenditures
independent_expenditures : data/processed/independent_expenditures.csv

data/processed/independent_expenditures.csv :
	python -m scrapers.financial_disclosure.scrape_independent_expenditures > $@
