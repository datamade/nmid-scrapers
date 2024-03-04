.PHONY : all upload-to-s3 clean

all : data/processed/employer.csv data/processed/filing_status.csv \
  data/processed/lobbyist_expenditures.csv data/processed/lobbyist_contributions.csv \
  data/processed/lobbyist_employer.csv data/processed/offices.csv

upload-to-s3 : data/processed/employer.csv data/processed/filing_status.csv \
  data/processed/lobbyist_expenditures.csv data/processed/lobbyist_contributions.csv \
  data/processed/lobbyist_employer.csv data/processed/offices.csv

	@for file in $^; do aws s3 cp $$file $(S3BUCKET) --acl public-read; done

clean :
	rm data/intermediate/*

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

# Offices
data/processed/offices.csv :
	python -m scrapers.office.scrape_offices > $@

data/processed/candidate_committees.csv :
	python -m scrapers.office.scrape_search candidates > $@

data/processed/committees.csv :
	python -m scrapers.office.scrape_search committees > $@


# Lobbyist expenditures and contributions
.PRECIOUS : data/intermediate/lobbyist_contributions.csv data/intermediate/lobbyist_expenditures.csv

data/processed/lobbyist_employer.csv : data/raw/lobbyists.csv data/intermediate/clients.csv
	csvsql --query "SELECT \
		ClientID, \
		MemberID,  \
		Phone,  \
		LobbyistName,  \
		LobbyistAddress, \
		Email, \
		StartYear, \
		EndYear \
	FROM ( \
		SELECT \
			ClientID, \
			MemberID, \
			MAX(MemberVersionID) AS MemberVersionID, \
			MAX(Year) AS Year, \
			MIN(Year) AS StartYear, \
			MAX(Year) AS EndYear \
		FROM STDIN \
		GROUP BY ClientID, MemberID \
	) AS lobbyists \
	JOIN STDIN \
	USING (ClientID, MemberID, MemberVersionID, Year)" < $< | \
	csvjoin -c ClientID - $(word 2, $^) > $@

data/processed/lobbyist_%.csv : data/intermediate/lobbyist_%.csv data/intermediate/filings.csv \
	data/intermediate/lobbyists.csv
	csvjoin --left -c Source,ReportFileName $< $(word 2, $^) | \
	csvjoin --left -c MemberID - $(word 3, $^) > $@

data/intermediate/lobbyist_%.csv : filings
	python -m scrapers.lobbyist.extract_transactions $* > $@

filings : data/intermediate/filings.csv
	csvgrep -c ReportTypeCode -m "LNA" -i < $< | \
	python -m scrapers.lobbyist.download_filings

data/intermediate/lobbyists.csv : data/raw/lobbyists.csv
	csvsql --query "SELECT \
		MemberID,  \
		Phone,  \
		LobbyistName,  \
		LobbyistAddress, \
		Email \
	FROM ( \
		SELECT \
			MemberID, \
			MAX(MemberVersionID) AS MemberVersionID, \
			MAX(Year) AS Year, \
			MAX(ClientID) AS ClientID \
		FROM STDIN \
		GROUP BY MemberID \
	) AS lobbyists \
	JOIN STDIN \
	USING (MemberID, MemberVersionID, Year, ClientID)" < $< > $@

data/intermediate/clients.csv : data/raw/clients.csv
	csvsql --query "SELECT ClientID, ClientVersionID, MAX(ClientName) AS ClientName FROM STDIN GROUP BY ClientID" < $< > $@

data/intermediate/filings.csv : data/raw/lobbyists.csv
	csvsql --query "SELECT DISTINCT MemberID, MemberVersionID FROM STDIN" < $< | \
	python -m scrapers.lobbyist.scrape_filings > $@

data/raw/lobbyists.csv : data/intermediate/clients.csv
	python -m scrapers.lobbyist.scrape_lobbyists < $< > $@

data/raw/clients.csv :
	python -m scrapers.lobbyist.scrape_clients > $@
