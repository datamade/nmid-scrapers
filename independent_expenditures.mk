.PHONY: independent_expenditures
independent_expenditures : data/processed/independent_expenditures.xlsx


data/processed/independent_expenditures.xlsx : data/intermediate/independent_expenditures.csv
	python scripts/to_excel.py $^ $@

data/intermediate/independent_expenditures.csv :
	python -m scrapers.financial_disclosure.scrape_independent_expenditures > $@
