# Financial disclosures
data/processed/disclosures.xlsx : data/processed/employment.csv			\
                                  data/processed/income.csv			\
                                  data/processed/specialization.csv		\
                                  data/processed/lobbying_clients.csv		\
                                  data/processed/real_estate.csv		\
                                  data/processed/other_business_interests.csv	\
                                  data/processed/state_agencies.csv
	python scripts/to_excel.py $^ $@

data/processed/employment.csv : data/intermediate/base.csv		\
                                data/intermediate/employer.csv		\
                                data/intermediate/spouse_employer.csv
	csvjoin -c ReportID --left data/intermediate/base.csv data/intermediate/employer.csv | \
            csvjoin --left -c ReportID - data/intermediate/spouse_employer.csv | \
            csvsort | \
            python scripts/uniq_csv.py | \
            python scripts/stack.py data/headers/employment.csv > $@


data/processed/income.csv : data/intermediate/base.csv data/intermediate/income.csv
	csvjoin -c ReportID --left data/intermediate/base.csv data/intermediate/income.csv | \
            csvsort | \
            python scripts/uniq_csv.py | \
            python scripts/stack.py data/headers/income.csv > $@


data/processed/specialization.csv : data/intermediate/base.csv			\
                                    data/intermediate/specializations.csv	\
                                    data/intermediate/licenses.csv		\
                                    data/intermediate/membership.csv		\
                                    data/intermediate/general.csv
	csvjoin --left -c ReportID data/intermediate/base.csv data/intermediate/specializations.csv | \
            csvjoin --left -c ReportID - data/intermediate/licenses.csv | \
            csvjoin --left -c ReportID - data/intermediate/membership.csv | \
            csvjoin --left -c ReportID - data/intermediate/general.csv | \
            csvsort | \
            python scripts/uniq_csv.py | \
            python scripts/stack.py data/headers/specialization.csv > $@

data/processed/lobbying_clients.csv : data/intermediate/base.csv	\
                                      data/intermediate/consulting.csv
	csvjoin -c ReportID $^ | \
           csvsort | \
	   csvcut -c 1,2,3,4,5,6,7,8,10,9 | \
           python scripts/uniq_csv.py | \
           python scripts/stack.py data/headers/lobbying_clients.csv > $@

data/processed/real_estate.csv : data/intermediate/base.csv		\
                                 data/intermediate/real_estate.csv
	csvjoin -c ReportID $^ | \
           csvsort | \
           python scripts/uniq_csv.py |\
           python scripts/stack.py data/headers/real_estate.csv > $@

data/processed/other_business_interests.csv : data/intermediate/base.csv	\
                                              data/intermediate/business.csv
	csvjoin -c ReportID $^ | \
           csvsort | \
           python scripts/uniq_csv.py | \
           python scripts/stack.py data/headers/other_business_interests.csv > $@

data/processed/state_agencies.csv : data/intermediate/base.csv			\
                                    data/intermediate/provisions.csv		\
                                    data/intermediate/representation.csv
	csvjoin --left -c ReportID data/intermediate/base.csv data/intermediate/provisions.csv | \
           csvjoin --left -c ReportID - data/intermediate/representation.csv | \
           csvsort | \
           python scripts/uniq_csv.py |\
           python scripts/stack.py data/headers/state_agencies.csv > $@



data/intermediate/base.csv : data/intermediate/filer.csv data/intermediate/filing.csv data/intermediate/filing_status.csv
	csvcut -c FilerID,ReportID,FilingYear,FiledDate data/intermediate/filing.csv | \
	   csvjoin -c FilerID data/intermediate/filer.csv - | \
           csvjoin -c ReportID - data/intermediate/filing_status.csv | \
           csvcut -C FullAddress,Phone,DateRegistered | \
           csvsort | \
           python scripts/uniq_csv.py | \
           python scripts/reason_filter.py > $@


data/intermediate/filer.csv data/intermediate/income.csv		\
data/intermediate/real_estate.csv data/intermediate/consulting.csv	\
data/intermediate/filing.csv data/intermediate/licenses.csv		\
data/intermediate/representation.csv					\
data/intermediate/filing_status.csv data/intermediate/membership.csv	\
data/intermediate/specializations.csv data/intermediate/employer.csv	\
data/intermediate/general.csv data/intermediate/provisions.csv		\
data/intermediate/spouse_employer.csv &:
	python -m scrapers.financial_disclosure.scrape_financial_disclosures

