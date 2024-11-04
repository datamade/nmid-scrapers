.PHONY : all upload-to-s3 clean

all : data/processed/disclosures.xlsx \
	data/processed/candidate_committees.csv	\
	data/processed/candidate_committee_filings.csv \
	data/processed/pac_committees.csv \
	data/processed/pac_committee_filings.csv \
	data/processed/independent_expenditures.xlsx \
	data/processed/lobbyist.xlsx \
	data/processed/lobbyist_employer.xlsx

upload-to-s3 : data/processed/disclosures.xlsx \
		   data/processed/candidate_committees.csv \
		   data/processed/candidate_committee_filings.csv \
		   data/processed/pac_committees.csv \
		   data/processed/pac_committee_filings.csv \
		   data/processed/independent_expenditures.xlsx \
		   data/processed/lobbyist.xlsx \
		   data/processed/lobbyist_employer.xlsx

	for file in $^; do aws s3 cp $$file $(S3BUCKET) --acl public-read; done

%_data_dirs :
	mkdir -p $(patsubst %,data/$*/%,raw intermediate processed assets)

include lobbyists.mk \
	lobbyist_employer.mk \
	disclosures.mk \
	candidates.mk \
	independent_expenditures.mk
