from housefire.logger import HousefireLoggerFactory
from housefire.scraper.scraper import Scraper
from housefire.scraper.reits_by_ticker.pld import PldScraper
from housefire.scraper.reits_by_ticker.spg import SpgScraper
from housefire.scraper.reits_by_ticker.dlr import DlrScraper
from housefire.scraper.reits_by_ticker.well import WellScraper
from housefire.scraper.reits_by_ticker.eqix import EqixScraper
import nodriver as uc


class ScraperFactory:
    """
    Factory class for creating Scraper instances
    """

    def __init__(
        self,
        logger_factory: HousefireLoggerFactory,
        chrome_path: str,
    ):
        self.logger_factory = logger_factory
        self.logger = logger_factory.get_logger(ScraperFactory.__name__)
        self.chrome_path = chrome_path
        self.scraper_map = {
            "pld": PldScraper,
            "spg": SpgScraper,
            "dlr": DlrScraper,
            "well": WellScraper,
            "eqix": EqixScraper,
        }

    async def get_scraper(self, ticker: str, temp_dir_path: str) -> Scraper:
        """
        Get a new instance of a Scraper subclass
        """
        if ticker not in self.scraper_map:
            raise ValueError(f"Unsupported ticker: {ticker}")

        scraper = self.scraper_map[ticker]()
        scraper.driver = await self._init_driver_instance(temp_dir_path)
        scraper.temp_dir_path = temp_dir_path
        scraper.ticker = ticker
        scraper.logger = self.logger_factory.get_logger(scraper.__class__.__name__)

        return scraper

    async def _init_driver_instance(self, temp_dir_path: str) -> uc.Browser:
        """
        Get a new instance of the undetected_chromedriver Chrome driver
        """
        browser = await uc.start(
            headless=False,
            browser_executable_path=self.chrome_path,
            browser_args=["--disable-gpu"]
        )
        # hack because i am not sure how to send CDP command thru browser
        tab = await browser.get("https://www.google.com")
        await tab.send(
            uc.cdp.browser.set_download_behavior(
                behavior="allowAndName", download_path=temp_dir_path
            )
        )
        return browser
