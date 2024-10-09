# Lobbyist expenditures and contributions
DATA_DIR=data/lobbyist

.PRECIOUS : $(DATA_DIR)/raw/lobbyist.csv \
	$(DATA_DIR)/intermediate/lobbyist_contributions.csv \
	$(DATA_DIR)/intermediate/lobbyist_expenditures.csv

$(DATA_DIR)/processed/lobbyist.xlsx : $(DATA_DIR)/processed/lobbyist_employer.csv      \
								$(DATA_DIR)/processed/lobbyist_contributions.csv \
								$(DATA_DIR)/processed/lobbyist_expenditures.csv
	python scripts/to_excel.py $^ $@

$(DATA_DIR)/processed/lobbyist_employer.csv : $(DATA_DIR)/raw/lobbyist.csv \
	$(DATA_DIR)/intermediate/client.csv
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

$(DATA_DIR)/processed/lobbyist_%.csv : $(DATA_DIR)/intermediate/lobbyist_%.csv \
	$(DATA_DIR)/intermediate/filings.csv \
	$(DATA_DIR)/intermediate/lobbyist.csv
	csvjoin --left -c Source,ReportFileName $< $(word 2, $^) | \
	csvjoin --left -c MemberID - $(word 3, $^) > $@

$(DATA_DIR)/intermediate/lobbyist_%.csv : lobbyist_filings
	python -m scrapers.lobbyist.extract_transactions $* $(DATA_DIR) > $@

lobbyist_filings : $(DATA_DIR)/intermediate/filings.csv
	python -m scrapers.lobbyist.download_filings $(DATA_DIR) < $<

$(DATA_DIR)/intermediate/lobbyist.csv : $(DATA_DIR)/raw/lobbyist.csv
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

$(DATA_DIR)/intermediate/filings.csv : $(DATA_DIR)/raw/lobbyist.csv
	csvsql --query "SELECT DISTINCT MemberID AS id, MemberVersionID AS version FROM STDIN" < $< | \
	head -n 25 | \
	python -m scrapers.lobbyist.scrape_filings > $@

$(DATA_DIR)/raw/lobbyist.csv : $(DATA_DIR)/intermediate/client.csv
	python -m scrapers.lobbyist.scrape_lobbyists < $< > $@

$(DATA_DIR)/intermediate/client.csv : $(DATA_DIR)/raw/client.csv
	csvsql --query "SELECT ClientID, ClientVersionID, MAX(ClientName) AS ClientName FROM STDIN GROUP BY ClientID" < $< > $@

$(DATA_DIR)/raw/client.csv : lobbyist_data_dirs
	python -m scrapers.lobbyist.scrape_clients > $@
