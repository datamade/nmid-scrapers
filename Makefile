.PHONY : all upload-to-s3 clean

all : data/processed/employer.csv data/processed/spouse_employer.csv \
	data/processed/filing_status.csv data/processed/lobbyist_expenditures.csv \
	data/processed/lobbyist_contributions.csv

upload-to-s3 : data/processed/employer.csv data/processed/spouse_employer.csv \
	data/processed/filing_status.csv data/processed/lobbyist_expenditures.csv \
	data/processed/lobbyist_contributions.csv
	@for file in $^; do aws s3 cp $$file $(S3BUCKET) --acl public-read; done

clean :
	rm data/intermediate/*

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
.PRECIOUS : data/intermediate/lobbyist_contributions.csv data/intermediate/lobbyist_expenditures.csv

data/processed/lobbyist_%.csv : data/intermediate/lobbyist_%.csv data/intermediate/filings.csv \
	data/intermediate/lobbyists.csv data/intermediate/clients.csv
	csvjoin -c Source,ReportFileName $< $(word 2, $^) | \
	csvjoin -c MemberID - $(word 3, $^) | \
	csvjoin -c ClientID - $(word 4, $^) > $@

data/intermediate/lobbyist_%.csv : filings
	python -m scrapers.lobbyist.extract_transactions $* > $@

filings : data/intermediate/filings.csv
	csvgrep -c ReportTypeCode -m "LNA" -i < $< | \
	python -m scrapers.lobbyist.download_filings

data/intermediate/lobbyists.csv : data/raw/lobbyists.csv
	csvsql --query "SELECT \
		ClientID, \
		MemberID,  \
		Phone,  \
		LobbyistName,  \
		LobbyistAddress, \
		Email \
	FROM ( \
		SELECT \
			ClientID, \
			MemberID, \
			MAX(MemberVersionID) AS MemberVersionID, \
			MAX(Year) AS Year \
		FROM STDIN \
		GROUP BY ClientID, MemberID \
	) AS lobbyists \
	JOIN STDIN \
	USING (ClientID, MemberID, MemberVersionID, Year)" < $< > $@

data/intermediate/clients.csv : data/raw/clients.csv
	csvsql --query "SELECT ClientID, MAX(ClientName) AS ClientName FROM STDIN GROUP BY ClientID" < $< > $@

data/intermediate/filings.csv : data/raw/lobbyists.csv
	csvsql --query "SELECT DISTINCT MemberID FROM STDIN" < $< | \
	python -m scrapers.lobbyist.scrape_filings > $@

data/raw/lobbyists.csv : data/intermediate/clients.csv
	python -m scrapers.lobbyist.scrape_lobbyists < $< > $@

data/raw/clients.csv :
	python -m scrapers.lobbyist.scrape_clients > $@
