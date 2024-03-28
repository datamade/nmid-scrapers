.PHONY: offices
offices : data/processed/candidate_committees.csv

data/processed/candidate_committees.csv :
	python -m scrapers.office.scrape_search candidates > $@
