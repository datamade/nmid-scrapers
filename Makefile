include lobbyists.mk disclosures.mk candidates.mk independent_expenditures.mk

.PHONY : all upload-to-s3 clean

all : data/processed/disclosures.xlsx			\
      data/processed/candidate_committees.csv		\
      data/processed/candidate_committee_filings.csv	\
      data/processed/pac_committees.csv			\
      data/processed/pac_committee_filings.csv		\
			data/intermediate/lobbyists.csv     \
			data/processed/lobbyist_employer.csv    \
      data/processed/independent_expenditures.xlsx

upload-to-s3 : data/processed/disclosures.xlsx			\
               data/processed/candidate_committees.csv		\
               data/processed/candidate_committee_filings.csv	\
               data/processed/pac_committees.csv		\
               data/processed/pac_committee_filings.csv  \
               data/intermediate/lobbyists.csv     \
               data/processed/lobbyist_employer.csv    \
               data/processed/independent_expenditures.xlsx

	for file in $^; do aws s3 cp $$file $(S3BUCKET) --acl public-read; done

clean :
	rm data/intermediate/*

