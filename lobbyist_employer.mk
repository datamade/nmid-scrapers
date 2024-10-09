# Lobbyist expenditures and contributions
DATA_DIR=data/lobbyist_employer

.PRECIOUS : $(DATA_DIR)/raw/lobbyist_employer.csv \
	$(DATA_DIR)/intermediate/lobbyist_employer_contributions.csv \
	$(DATA_DIR)/intermediate/lobbyist_employer_expenditures.csv

$(DATA_DIR)/processed/lobbyist_employer.xlsx : $(DATA_DIR)/intermediate/lobbyist_employer.csv      \
								$(DATA_DIR)/processed/lobbyist_employer_contributions.csv \
								$(DATA_DIR)/processed/lobbyist_employer_expenditures.csv
	python scripts/to_excel.py $^ $@

$(DATA_DIR)/processed/lobbyist_employer_%.csv : $(DATA_DIR)/intermediate/lobbyist_employer_%.csv \
	$(DATA_DIR)/intermediate/lobbyist_employer_filings.csv \
	$(DATA_DIR)/intermediate/lobbyist_employer.csv
	csvjoin --left -c Source,ReportFileName $< $(word 2, $^) | \
	csvjoin --left -c MemberID,LobbyMemberID - $(word 3, $^) > $@

$(DATA_DIR)/intermediate/lobbyist_employer_%.csv : lobbyist_employer_filings
	python -m scrapers.lobbyist.extract_transactions $* $(DATA_DIR) > $@

lobbyist_employer_filings : $(DATA_DIR)/intermediate/lobbyist_employer_filings.csv
	python -m scrapers.lobbyist.download_filings $(DATA_DIR) < $<

$(DATA_DIR)/intermediate/lobbyist_employer_filings.csv : $(DATA_DIR)/raw/lobbyist_employer.csv
	csvsql --query "SELECT DISTINCT LobbyMemberID AS id, LobbyMemberversionid AS version FROM STDIN" < $< | \
	head -n 25 | \
	python -m scrapers.lobbyist.scrape_filings --employer > $@

$(DATA_DIR)/intermediate/lobbyist_employer.csv : $(DATA_DIR)/raw/lobbyist_employer.csv
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

$(DATA_DIR)/raw/lobbyist_employer.csv : lobbyist_employer_data_dirs
	python -m scrapers.lobbyist.scrape_employers > $@
