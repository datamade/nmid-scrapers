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
