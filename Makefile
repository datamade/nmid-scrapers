include lobbyists.mk disclosures.mk candidates.mk

.PHONY : all upload-to-s3 clean

all : data/processed/disclosures.xlsx			\
      data/processed/candidate_committees.csv		\
      data/processed/candidate_committee_filings.csv	\
      data/processed/pac_committees.csv			\
      data/processed/pac_committee_filings.csv

upload-to-s3 : data/processed/disclosures.xlsx			\
               data/processed/candidate_committees.csv		\
               data/processed/candidate_committee_filings.csv	\
               data/processed/pac_committees.csv		\
               data/processed/pac_committee_filings.csv

	for file in $^; do aws s3 cp $$file $(S3BUCKET) --acl public-read; done

clean :
	rm data/intermediate/*

