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
	python scrapers/lobbyist/cli.py extract-transactions -t $* -d $(LOBBYIST_EMPLOYER_DATA_DIR)/assets > $@

lobbyist_employer_filings : $(LOBBYIST_EMPLOYER_DATA_DIR)/intermediate/lobbyist_employer_filings.csv
	python scrapers/lobbyist/cli.py download-filings -d $(LOBBYIST_EMPLOYER_DATA_DIR)/assets < $<

$(LOBBYIST_EMPLOYER_DATA_DIR)/intermediate/lobbyist_employer_filings.csv : $(LOBBYIST_EMPLOYER_DATA_DIR)/raw/lobbyist_employer.csv
	python scrapers/lobbyist/cli.py scrape-filings --employer < $< > $@

$(LOBBYIST_EMPLOYER_DATA_DIR)/raw/lobbyist_employer.csv : lobbyist_employer_data_dirs
	python scrapers/lobbyist/cli.py scrape-employers > $@
