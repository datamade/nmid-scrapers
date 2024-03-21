.PHONY: offices
offices : data/processed/offices.csv data/processed/candidate_committees.csv data/processed/committees.csv

# Offices
data/processed/offices.csv :
	python -m scrapers.office.scrape_offices > $@

data/processed/candidate_committees.csv :
	python -m scrapers.office.scrape_search candidates > $@

data/processed/committees.csv :
	python -m scrapers.office.scrape_search committees > $@

