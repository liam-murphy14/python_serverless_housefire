from abc import ABC, abstractmethod
import csv
from dataclasses import dataclass
from logging import Logger
import nodriver as uc
import random as r
from pathlib import Path


class Scraper(ABC):

    driver: uc.Browser
    temp_dir_path: str
    ticker: str
    logger: Logger

    def __init__(self):
        pass

    @abstractmethod
    async def execute_scrape(self) -> list["ScrapeResult"]:
        return NotImplemented

    @abstractmethod
    async def _debug_scrape(self) -> list["ScrapeResult"]:
        """
        debugging method to scrape data at a small scale, can be used for manual testing
        """
        pass

    async def scrape(self) -> list["ScrapeResult"]:
        """
        Scrape data and log
        """
        self.logger.debug(f"Scraping data for REIT: {self.ticker}")
        scraped_data = await self.execute_scrape()
        self.logger.debug(f"Scraped data for REIT: {self.ticker}")
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


@dataclass
class ScrapeResult:
    property_info: dict[str, str]

    @staticmethod
    def to_csv(data: list["ScrapeResult"], destination_file: Path) -> None:
        all_property_info_keys = {k for d in data for k in d.property_info.keys()}
        with open(destination_file, "w") as f:
            writer = csv.DictWriter(
                f, fieldnames=all_property_info_keys, dialect=csv.unix_dialect
            )
            writer.writeheader()
            for d in data:
                writer.writerow(d.property_info)

    @staticmethod
    def from_csv(file_path: Path) -> list["ScrapeResult"]:
        with open(file_path, "r") as f:
            reader = csv.DictReader(f, dialect=csv.unix_dialect)
            return [ScrapeResult(property_info=row) for row in reader]
