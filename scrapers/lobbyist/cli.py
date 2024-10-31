import functools

import click


def scrapelib_opts(f):
    @click.option("--rpm", default=180, show_default=True)
    @click.option("--retries", default=3, show_default=True)
    @click.option("--verify/--no-verify", default=False, show_default=True)
    @functools.wraps(f)
    def wrapped_func(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapped_func


@click.group()
def scrape():
    ...


@scrape.command()
@scrapelib_opts
def scrape_lobbyist_clients(rpm, retries, verify):
    import scrape_lobbyist_clients

    scrape_lobbyist_clients.main(rpm=rpm, retries=retries, verify=verify)


@scrape.command()
@scrapelib_opts
def scrape_lobbyists(rpm, retries, verify):
    import scrape_lobbyists

    scrape_lobbyists.main(rpm=rpm, retries=retries, verify=verify)


@scrape.command()
@scrapelib_opts
def scrape_employers(rpm, retries, verify):
    import scrape_employers

    scrape_employers.main(rpm=rpm, retries=retries, verify=verify)


@scrape.command()
@scrapelib_opts
@click.option("--employer", "is_employer_scrape", is_flag=True)
def scrape_filings(rpm, retries, verify, is_employer_scrape):
    import scrape_filings

    scrape_filings.main(
        rpm=rpm, retries=retries, verify=verify, is_employer_scrape=is_employer_scrape
    )


@scrape.command()
@click.option("-d", "--asset-directory", "asset_directory")
def download_filings(asset_directory):
    import download_filings

    download_filings.main(asset_directory)


@scrape.command()
@click.option("-t", "--transaction-type", "transaction_type")
@click.option("-d", "--asset-directory", "asset_directory")
def extract_transactions(transaction_type, asset_directory):
    import extract_transactions

    extract_transactions.main(transaction_type, asset_directory)


if __name__ == "__main__":
    scrape()
