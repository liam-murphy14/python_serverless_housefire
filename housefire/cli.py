import sys
import dotenv
import housefire.config as config
from housefire.scraper.scraper_factory import ScraperFactory
import nodriver as uc

dotenv.load_dotenv()
from housefire.scraper import (
    SCRAPERS,
    scrape_wrapper,
)
from housefire.transformer import (
    TRANSFORMERS,
    transform_wrapper,
)
import nodriver as uc
from housefire.utils import (
    get_env_nonnull_dir,
    get_env_nonnull_file,
    get_env_nonnull,
    df_to_request,
)
from housefire.dependency import HousefireAPI
from housefire.logger import get_logger


logger = get_logger(__name__)


async def get_chromedriver_instance() -> uc.Browser:
    """
    Get a new instance of the undetected_chromedriver Chrome driver
    """
    CHROME_PATH = get_env_nonnull_file("CHROME_PATH")

    return await uc.start(
        headless=False,
        browser_executable_path=CHROME_PATH,
    )


async def scrape_main():


    try:
        scraper = await ScraperFactory().get_scraper("pld")
    except Exception as e:
        logger.critical(f"Failed to create chromedriver instance: {e}")
        raise e

    try:
        if len(sys.argv) != 2:
            raise Exception("Usage: python main.py <ticker>")
        
        ticker = sys.argv[1].lower()
        logger.info(f"Scraping data for ticker: {ticker}")

        if ticker not in SCRAPERS or ticker not in TRANSFORMERS:
            raise ValueError(f"Unsupported ticker: {ticker}")

        properties_dataframe = await scrape_wrapper(driver, ticker, TEMP_DIR_PATH)
        logger.debug(f"Scraped properties data: {properties_dataframe}")
        transformed_dataframe = transform_wrapper(properties_dataframe, ticker)
        logger.debug(f"Transformed properties data: {transformed_dataframe}")
        
        housefire_api = HousefireAPI(HOUSEFIRE_API_KEY)
        
        created_properties = housefire_api.update_properties_by_ticker(
            ticker.upper(), df_to_request(transformed_dataframe)
        )
        logger.info(f"Created properties: {created_properties}")
        logger.info("Scraping data")
        scraped_data = await scraper.scrape()
        logger.info(f"Scraped data: {scraped_data}")

    finally:
        scraper.driver.stop()

def main():
    uc.loop().run_until_complete(scrape_main())

if __name__ == "__main__":
    main()