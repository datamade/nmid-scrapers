# Lobbyist expenditures and contributions
LOBBYIST_EMPLOYER_DATA_DIR=data/lobbyist_employer

.PRECIOUS : $(LOBBYIST_EMPLOYER_DATA_DIR)/raw/lobbyist_employer.csv \
	$(LOBBYIST_EMPLOYER_DATA_DIR)/intermediate/lobbyist_employer_contributions.csv \
	$(LOBBYIST_EMPLOYER_DATA_DIR)/intermediate/lobbyist_employer_expenditures.csv

data/processed/lobbyist_employer.xlsx : $(LOBBYIST_EMPLOYER_DATA_DIR)/intermediate/lobbyist_employer.csv      \
								$(LOBBYIST_EMPLOYER_DATA_DIR)/processed/lobbyist_employer_contributions.csv \
								$(LOBBYIST_EMPLOYER_DATA_DIR)/processed/lobbyist_employer_expenditures.csv
	python scripts/to_excel.py $^ $@

$(LOBBYIST_EMPLOYER_DATA_DIR)/processed/lobbyist_employer_%.csv : $(LOBBYIST_EMPLOYER_DATA_DIR)/intermediate/lobbyist_employer_%.csv \
	$(LOBBYIST_EMPLOYER_DATA_DIR)/intermediate/lobbyist_employer_filings.csv \
	$(LOBBYIST_EMPLOYER_DATA_DIR)/intermediate/lobbyist_employer.csv
	csvjoin --left -c Source,ReportFileName $< $(word 2, $^) | \
	csvjoin --left -c MemberID,LobbyMemberID - $(word 3, $^) > $@

$(LOBBYIST_EMPLOYER_DATA_DIR)/intermediate/lobbyist_employer_%.csv : lobbyist_employer_filings
	python -m scrapers.lobbyist.extract_transactions $* $(LOBBYIST_EMPLOYER_DATA_DIR) > $@

lobbyist_employer_filings : $(LOBBYIST_EMPLOYER_DATA_DIR)/intermediate/lobbyist_employer_filings.csv
	python -m scrapers.lobbyist.download_filings $(LOBBYIST_EMPLOYER_DATA_DIR) < $<

$(LOBBYIST_EMPLOYER_DATA_DIR)/intermediate/lobbyist_employer_filings.csv : $(LOBBYIST_EMPLOYER_DATA_DIR)/raw/lobbyist_employer.csv
	csvsql --query "SELECT DISTINCT LobbyMemberID AS id, LobbyMemberversionid AS version FROM STDIN" < $< | \
	python -m scrapers.lobbyist.scrape_filings --employer | \
	csvsql --query 'select ReportFileName, ReportTypeCode, MAX(MemberID) as MemberID from STDIN group by ReportFileName, ReportTypeCode' > $@

$(LOBBYIST_EMPLOYER_DATA_DIR)/intermediate/lobbyist_employer.csv : $(LOBBYIST_EMPLOYER_DATA_DIR)/raw/lobbyist_employer.csv
	csvsql --query "SELECT DISTINCT \
		LobbyMemberID,  \
		Name \
	FROM ( \
		SELECT \
			LobbyMemberID, \
			MAX(LobbyMemberversionid) AS LobbyMemberversionid \
		FROM STDIN \
		GROUP BY LobbyMemberID \
	) AS lobbyists \
	JOIN STDIN \
	USING (LobbyMemberID, LobbyMemberversionid)" < $< > $@

$(LOBBYIST_EMPLOYER_DATA_DIR)/raw/lobbyist_employer.csv : lobbyist_employer_data_dirs
	python -m scrapers.lobbyist.scrape_employers > $@
