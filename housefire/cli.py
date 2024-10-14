import click
import nodriver as uc

from housefire.dependency.housefire_api import HousefireAPI
from housefire.scraper.scraper_factory import ScraperFactory
from housefire.transformer.transformer_factory import TransformerFactory

@click.group()
def main():
    # TODO: get configs from file or env vars ??
    pass

@main.command()
@click.argument("ticker", required=True)
def run_data_pipeline(ticker: str):
    """
    Run the full data pipeline for scraping the TICKER website and uploading to housefire.
    """
    uc.loop().run_until_complete(run_data_pipeline_main(ticker))

async def run_data_pipeline_main(ticker: str):
    scraper_factory = ScraperFactory()
    scraper = await scraper_factory.get_scraper(ticker)
    scraped_data = await scraper.scrape()

    transformer_factory = TransformerFactory()
    transformer = transformer_factory.get_transformer(ticker)
    transformed_data = transformer.transform(scraped_data)

    housefire_api = HousefireAPI()

    housefire_api.update_properties_by_ticker(ticker.upper(), HousefireAPI.df_to_request(transformed_data))


@main.command()
@click.argument("ticker", required=True)
@click.option("--debug", default=False, is_flag=True, help="Run the scraper debugger function instead of the full scraper.")
def scrape(ticker: str, debug: bool):
    """
    Scrapes the TICKER website for property data.
    """
    uc.loop().run_until_complete(scrape_main(ticker, debug))

async def scrape_main(ticker: str, debug: bool):
    scraper_factory = ScraperFactory()
    scraper = await scraper_factory.get_scraper(ticker)
    if debug:
        await scraper._debug_scrape()
    else:
        click.echo("This feature is not yet implemented. To test scraping on its own, use the --debug flag.")
        # NOT CURRENTLY USED
        # TODO: use this once i have implemented some caching/magic resilience for the scraper
        # return await scraper.scrape()


# NOT CURRENTLY USED
# TODO: implement this once i have implemented some local caching/magic resilience for the scraper and modularized the scrape and transforms to save to files separately
# @main.command()
# @click.argument("ticker", required=True)
# @click.option("--debug", default=False, is_flag=True, help="Run the transformer debugger function instead of the full transformer.")
# def transform(ticker: str, debug: bool):
#     """
#     Transforms the TICKER scraped data into a standardized format.
#     """
#     transformer_factory = TransformerFactory()
#     transformer = transformer_factory.get_transformer(ticker)
#     if debug:
#         transformer._debug_transform()
#     else:
#         click.echo("This feature is not yet implemented. To test transforming on its own, use the --debug flag.")

# TODO: write an uploader as well


