import pytest
import requests
import pdfplumber
import io

from parse_pdf import parse_pdf

@pytest.mark.parametrize("pdf_file", ['20c47c8e-b780-48d9-8d88-d40828061c82.pdf'])
def test_custom_addition(pdf_file):
    url = f'https://login.cfis.sos.state.nm.us//ReportsOutput//SFI/{pdf_file}'

    response = requests.get(url)

    filing_pdf = pdfplumber.open(io.BytesIO(response.content))

    parse_pdf(filing_pdf)
