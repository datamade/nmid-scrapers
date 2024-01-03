.PHONY : filings clean

data/processed/disclosures.zip : data/intermediate/employer.csv \
	data/intermediate/filer.csv \
	data/intermediate/filing.csv \
	data/intermediate/spouse_employer.csv
	zip $@ $^

data/intermediate/%.csv :
	python -m scrapers.financial_disclosure.scrape_financial_disclosures

data/processed/offices.csv :
	python -m scrapers.office.scrape_offices > $@

data/intermediate/expenditures.csv :
	python -m scrapers.lobbyist.extract_expenditures > $@

filings : data/intermediate/filings.csv
	python -m scrapers.lobbyist.download_filings < $<

data/intermediate/filings.csv : data/intermediate/lobbyists.csv
	csvgrep -c TotalExpenditures -r "^0.0$$" -i $< | \
	python -m scrapers.lobbyist.scrape_filings > $@

data/intermediate/lobbyists.csv :
	python -m scrapers.lobbyist.scrape_lobbyists > $@

clean :
	rm data/intermediate/*