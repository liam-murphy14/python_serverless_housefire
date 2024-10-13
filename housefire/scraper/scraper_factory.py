from housefire.scraper.scraper import Scraper
from housefire.scraper.reits_by_ticker.pld import PldScraper
from housefire.scraper.reits_by_ticker.spg import SpgScraper
from housefire.scraper.reits_by_ticker.dlr import DlrScraper
from housefire.scraper.reits_by_ticker.well import WellScraper
from housefire.scraper.reits_by_ticker.eqix import EqixScraper
import nodriver as uc
import housefire.config as config

class ScraperFactory:
    """
    Factory class for creating Scraper instances
    """

    def __init__(self):
        self.scraper_map = {
                "pld": PldScraper,
                "spg": SpgScraper,
                "dlr": DlrScraper,
                "well": WellScraper,
                "eqix": EqixScraper,
                }

    async def get_scraper(self, ticker: str) -> Scraper:
        """
        Get a new instance of a Scraper subclass
        """
        if ticker not in self.scraper_map:
            raise ValueError(f"Unsupported ticker: {ticker}")

        driver = await self._init_driver_instance()
        return self.scraper_map[ticker](driver)

    async def _init_driver_instance(self) -> uc.Browser:
        """
        Get a new instance of the undetected_chromedriver Chrome driver
        """
        return await uc.start(
            headless=False,
            browser_executable_path=config.CHROME_PATH,
        )
