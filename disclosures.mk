# Financial disclosures
data/processed/disclosures.zip : data/intermediate/employer.csv		\
	                         data/intermediate/filer.csv		\
	                         data/intermediate/filing.csv
	zip $@ $^

data/processed/employer.csv : data/intermediate/filer.csv
	csvjoin -c FilerID data/intermediate/filer.csv data/intermediate/filing.csv | csvjoin -c ReportID - data/intermediate/employer.csv | csvjoin -c ReportID - data/intermediate/spouse_employer.csv > $@

data/processed/filing_status.csv : data/intermediate/filer.csv
	csvjoin -c FilerID data/intermediate/filer.csv data/intermediate/filing.csv | csvjoin -c ReportID data/intermediate/filing_status.csv > $@

data/intermediate/filer.csv :
	python -m scrapers.financial_disclosure.scrape_financial_disclosures


