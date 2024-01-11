.PHONY : all filings upload-to-s3 clean

all : data/processed/employer.csv data/processed/spouse_employer.csv \
	data/processed/filing_status.csv data/processed/lobbyist_expenditures.csv

upload-to-s3 : data/processed/employer.csv data/processed/spouse_employer.csv \
	data/processed/filing_status.csv data/processed/lobbyist_expenditures.csv
	@for file in $^; do aws s3 cp $$file $(S3BUCKET) --acl public-read; done

# Financial disclosures
data/processed/disclosures.zip : data/intermediate/employer.csv \
	data/intermediate/filer.csv \
	data/intermediate/filing.csv \
	data/intermediate/spouse_employer.csv
	zip $@ $^

data/processed/employer.csv : data/intermediate/filer.csv
	csvjoin -c FilerID data/intermediate/filer.csv data/intermediate/filing.csv | csvjoin -c ReportID data/intermediate/employer.csv > $@

data/processed/spouse_employer.csv : data/intermediate/filer.csv
	csvjoin -c FilerID data/intermediate/filer.csv data/intermediate/filing.csv | csvjoin -c ReportID data/intermediate/spouse_employer.csv > $@

data/processed/filing_status.csv : data/intermediate/filer.csv
	csvjoin -c FilerID data/intermediate/filer.csv data/intermediate/filing.csv | csvjoin -c ReportID data/intermediate/filing_status.csv > $@

data/intermediate/filer.csv :
	python -m scrapers.financial_disclosure.scrape_financial_disclosures

# Offices
data/processed/offices.csv :
	python -m scrapers.office.scrape_offices > $@

# Lobbyist expenditures and contributions
data/processed/lobbyist_expenditures.csv :
	python -m scrapers.lobbyist.extract_expenditures > $@

filings : data/intermediate/filings.csv
	csvgrep -c ReportTypeCode -m "LNA" -i < $< | \
	python -m scrapers.lobbyist.download_filings

data/intermediate/filings.csv : data/intermediate/lobbyists.csv
	csvsql --query "SELECT DISTINCT MemberID FROM STDIN" < $< | \
	python -m scrapers.lobbyist.scrape_filings > $@

data/intermediate/lobbyists.csv : data/intermediate/clients.csv
	csvsql --query "SELECT ClientID, MAX(ClientVersionID) AS ClientVersionID FROM STDIN WHERE NumberOfLobbyists > 0 GROUP BY ClientID" < $< | \
	python -m scrapers.lobbyist.scrape_lobbyists > $@

data/intermediate/clients.csv :
	python -m scrapers.lobbyist.scrape_clients > $@

clean :
	rm data/intermediate/*