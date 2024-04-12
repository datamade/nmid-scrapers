.PHONY: offices
offices : data/processed/candidate_committees.csv		\
          data/processed/candidate_committees_filings.csv	\
          data/processed/pac_committees.csv			\
          data/processed/pac_committees_filings.csv

data/processed/candidate_committees.csv			\
data/processed/candidate_committees_filings.csv &:
	python -m scrapers.office.scrape_search candidates > $@


data/processed/pac_committees.csv		\
data/processed/pac_committees_filings.csv &:
	python -m scrapers.office.scrape_search committees > $@
