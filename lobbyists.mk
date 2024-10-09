# Lobbyist expenditures and contributions
LOBBYIST_DATA_DIR=data/lobbyist

.PRECIOUS : $(LOBBYIST_DATA_DIR)/raw/lobbyist.csv \
	$(LOBBYIST_DATA_DIR)/intermediate/lobbyist_contributions.csv \
	$(LOBBYIST_DATA_DIR)/intermediate/lobbyist_expenditures.csv

data/processed/lobbyist.xlsx : $(LOBBYIST_DATA_DIR)/processed/lobbyist_employer.csv      \
								$(LOBBYIST_DATA_DIR)/processed/lobbyist_contributions.csv \
								$(LOBBYIST_DATA_DIR)/processed/lobbyist_expenditures.csv
	python scripts/to_excel.py $^ $@

$(LOBBYIST_DATA_DIR)/processed/lobbyist_employer.csv : $(LOBBYIST_DATA_DIR)/raw/lobbyist.csv \
	$(LOBBYIST_DATA_DIR)/intermediate/client.csv
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

$(LOBBYIST_DATA_DIR)/processed/lobbyist_%.csv : $(LOBBYIST_DATA_DIR)/intermediate/lobbyist_%.csv \
	$(LOBBYIST_DATA_DIR)/intermediate/filings.csv \
	$(LOBBYIST_DATA_DIR)/intermediate/lobbyist.csv
	csvjoin --left -c Source,ReportFileName $< $(word 2, $^) | \
	csvjoin --left -c MemberID - $(word 3, $^) > $@

$(LOBBYIST_DATA_DIR)/intermediate/lobbyist_%.csv : lobbyist_filings
	python -m scrapers.lobbyist.extract_transactions $* $(LOBBYIST_DATA_DIR) > $@

lobbyist_filings : $(LOBBYIST_DATA_DIR)/intermediate/filings.csv
	python -m scrapers.lobbyist.download_filings $(LOBBYIST_DATA_DIR) < $<

$(LOBBYIST_DATA_DIR)/intermediate/lobbyist.csv : $(LOBBYIST_DATA_DIR)/raw/lobbyist.csv
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

$(LOBBYIST_DATA_DIR)/intermediate/filings.csv : $(LOBBYIST_DATA_DIR)/raw/lobbyist.csv
	csvsql --query "SELECT DISTINCT MemberID AS id, MemberVersionID AS version FROM STDIN" < $< | \
	python -m scrapers.lobbyist.scrape_filings > $@

$(LOBBYIST_DATA_DIR)/raw/lobbyist.csv : $(LOBBYIST_DATA_DIR)/intermediate/client.csv
	python -m scrapers.lobbyist.scrape_lobbyists < $< > $@

$(LOBBYIST_DATA_DIR)/intermediate/client.csv : $(LOBBYIST_DATA_DIR)/raw/client.csv
	csvsql --query "SELECT ClientID, ClientVersionID, MAX(ClientName) AS ClientName FROM STDIN GROUP BY ClientID" < $< > $@

$(LOBBYIST_DATA_DIR)/raw/client.csv : lobbyist_data_dirs
	python -m scrapers.lobbyist.scrape_clients > $@
