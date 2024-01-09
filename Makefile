data/processed/disclosures.zip : data/intermediate/employer.csv \
	data/intermediate/filer.csv \
	data/intermediate/filing.csv \
	data/intermediate/spouse_employer.csv \
	data/intermediate/filing_status.csv \
	zip $@ $^

.PHONY: upload-to-s3
upload-to-s3: data/processed/employer.csv data/processed/spouse_employer.csv
	@for file in $^; do aws s3 cp $$file $(S3BUCKET) --acl public-read; done

.PHONY: all
all: data/processed/employer.csv data/processed/spouse_employer.csv

data/processed/employer.csv : data/intermediate/filer.csv
	csvjoin -c FilerID data/intermediate/filer.csv data/intermediate/filing.csv | csvjoin -c ReportID data/intermediate/employer.csv > $@

data/processed/spouse_employer.csv : data/intermediate/filer.csv
	csvjoin -c FilerID data/intermediate/filer.csv data/intermediate/filing.csv | csvjoin -c ReportID data/intermediate/spouse_employer.csv > $@

data/intermediate/filer.csv :
	python -m scrapers.financial_disclosure.scrape_financial_disclosures

data/processed/offices.csv :
	python -m scrapers.office.scrape_offices > $@
