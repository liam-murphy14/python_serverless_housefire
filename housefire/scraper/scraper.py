from abc import ABC, abstractmethod
import pandas as pd
import nodriver as uc
import housefire.config as config
from housefire.logger import get_logger
import random as r
import time

logger = get_logger(__name__)


class Scraper(ABC):
    def __init__(self, driver: uc.Browser):
        self.driver = driver
        self.temp_dir_path = config.TEMP_DIR_PATH
        self.ticker = str()

    @abstractmethod
    async def execute_scrape(self) -> pd.DataFrame:
        return NotImplemented

    @abstractmethod
    async def _debug_scrape(self) -> None:
        """
        debugging method to scrape data at a small scale, can be used for manual testing
        """
        pass

    async def scrape(self) -> pd.DataFrame:
        """
        Scrape data and log
        """
        logger.debug(f"Scraping data for REIT: {self.ticker}")
        scraped_data = await self.execute_scrape()
        logger.debug(f"Scraped data for REIT: {self.ticker}, df: {scraped_data}")
        return scraped_data

    def _jiggle(self):
        """
        pauses for a random amount of seconds between 10 and 70

        returns the amount of time jiggled
        """
        jiggle_time = r.randint(10, 70)
        logger.debug(f"Jiggling for {jiggle_time} seconds")
        time.sleep(jiggle_time)
        return jiggle_time

    def _wait(self, seconds: int):
        """
        pauses for a given amount of seconds

        returns the amount of time waited
        """
        logger.debug(f"Waiting for {seconds} seconds")
        time.sleep(seconds)
        return seconds
