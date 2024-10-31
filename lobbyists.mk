LOBBYIST_DATA_DIR=data/lobbyist

.PRECIOUS : $(LOBBYIST_DATA_DIR)/raw/lobbyist.csv \
	$(LOBBYIST_DATA_DIR)/raw/filings.csv \
	$(LOBBYIST_DATA_DIR)/raw/lobbyist_client.csv \
	$(LOBBYIST_DATA_DIR)/intermediate/lobbyist_contributions.csv \
	$(LOBBYIST_DATA_DIR)/intermediate/lobbyist_expenditures.csv

data/processed/lobbyist.xlsx : $(LOBBYIST_DATA_DIR)/raw/lobbyist.csv      \
								$(LOBBYIST_DATA_DIR)/raw/lobbyist_client.csv \
								$(LOBBYIST_DATA_DIR)/processed/lobbyist_contributions.csv \
								$(LOBBYIST_DATA_DIR)/processed/lobbyist_expenditures.csv
	python scripts/to_excel.py $^ $@

$(LOBBYIST_DATA_DIR)/raw/lobbyist_client.csv : $(LOBBYIST_DATA_DIR)/raw/lobbyist.csv
	python scrapers/lobbyist/cli.py scrape-lobbyist-clients < $< > $@

$(LOBBYIST_DATA_DIR)/processed/lobbyist_%.csv : $(LOBBYIST_DATA_DIR)/intermediate/lobbyist_%.csv \
	$(LOBBYIST_DATA_DIR)/raw/filings.csv \
	$(LOBBYIST_DATA_DIR)/raw/lobbyist.csv
	csvjoin --left -c Source,ReportFileName $< $(word 2, $^) | \
	csvjoin --left -c MemberID,ID - $(word 3, $^) > $@

$(LOBBYIST_DATA_DIR)/intermediate/lobbyist_%.csv : lobbyist_filings
	python scrapers/lobbyist/cli.py extract-transactions -t $* -d $(LOBBYIST_DATA_DIR)/assets > $@

lobbyist_filings : $(LOBBYIST_DATA_DIR)/raw/filings.csv
	python scrapers/lobbyist/cli.py download-filings -d $(LOBBYIST_DATA_DIR)/assets < $<

$(LOBBYIST_DATA_DIR)/raw/filings.csv : $(LOBBYIST_DATA_DIR)/raw/lobbyist.csv
	python scrapers/lobbyist/cli.py scrape-filings < $< > $@

$(LOBBYIST_DATA_DIR)/raw/lobbyist.csv : lobbyist_data_dirs
	python scrapers/lobbyist/cli.py scrape-lobbyists > $@
