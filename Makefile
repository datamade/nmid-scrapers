include lobbyists.mk disclosures.mk candidates.mk

.PHONY : all upload-to-s3 clean

all : data/processed/employer.csv data/processed/filing_status.csv \
  data/processed/lobbyist_expenditures.csv data/processed/lobbyist_contributions.csv \
  data/processed/lobbyist_employer.csv data/processed/offices.csv

upload-to-s3 : data/processed/employer.csv data/processed/filing_status.csv \
  data/processed/lobbyist_expenditures.csv data/processed/lobbyist_contributions.csv \
  data/processed/lobbyist_employer.csv data/processed/offices.csv

	@for file in $^; do aws s3 cp $$file $(S3BUCKET) --acl public-read; done

clean :
	rm data/intermediate/*

