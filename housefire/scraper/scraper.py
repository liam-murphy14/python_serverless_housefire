from abc import ABC, abstractmethod
from logging import Logger
import pandas as pd
import nodriver as uc
import random as r
import time


class Scraper(ABC):

    driver: uc.Browser
    temp_dir_path: str
    ticker: str
    logger: Logger

    def __init__(self):
        pass

    @abstractmethod
    async def execute_scrape(self) -> pd.DataFrame:
        return NotImplemented

    @abstractmethod
    async def _debug_scrape(self) -> pd.DataFrame:
        """
        debugging method to scrape data at a small scale, can be used for manual testing
        """
        pass

    async def scrape(self) -> pd.DataFrame:
        """
        Scrape data and log
        """
        self.logger.debug(f"Scraping data for REIT: {self.ticker}")
        scraped_data = await self.execute_scrape()
        self.logger.debug(f"Scraped data for REIT: {self.ticker}, df: {scraped_data}")
        return scraped_data

    async def _jiggle(self):
        """
        pauses for a random amount of seconds between 10 and 70

        returns the amount of time jiggled
        """
        jiggle_time = r.randint(10, 70)
        self.logger.debug(f"Jiggling for {jiggle_time} seconds")
        await self.driver.wait(jiggle_time)
        return jiggle_time

    async def _wait(self, seconds: int):
        """
        pauses for a given amount of seconds

        returns the amount of time waited
        """
        self.logger.debug(f"Waiting for {seconds} seconds")
        await self.driver.wait(seconds)
        return seconds
