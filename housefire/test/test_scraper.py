import asyncio
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from housefire.scraper.scraper import ScrapeResult, Scraper


class FakeScraper(Scraper):

    def __init__(self):
        super().__init__()
        self.results = [ScrapeResult({"address_input": "1 Main Street"})]

    async def execute_scrape(self):
        return self.results

    async def _debug_scrape(self):
        return self.results[:1]


class TestScraper(unittest.TestCase):

    def setUp(self):
        self.scraper = FakeScraper()
        self.scraper.ticker = "pld"
        self.scraper.logger = Mock()
        self.scraper.driver = Mock()
        self.scraper.driver.wait = AsyncMock()

    def test_scrape_executes_and_returns_results(self):
        results = asyncio.run(self.scraper.scrape())

        self.assertEqual(results, self.scraper.results)
        self.scraper.logger.debug.assert_any_call("Scraping data for REIT: pld")
        self.scraper.logger.debug.assert_any_call("Scraped data for REIT: pld")

    def test_wait_waits_for_requested_seconds(self):
        result = asyncio.run(self.scraper._wait(4))

        self.assertEqual(result, 4)
        self.scraper.driver.wait.assert_awaited_once_with(4)

    @patch("housefire.scraper.scraper.r.randint", return_value=17)
    def test_jiggle_waits_for_random_seconds(self, randint):
        result = asyncio.run(self.scraper._jiggle())

        self.assertEqual(result, 17)
        randint.assert_called_once_with(10, 70)
        self.scraper.driver.wait.assert_awaited_once_with(17)

    def test_scrape_result_csv_round_trip_preserves_union_of_columns(self):
        results = [
            ScrapeResult({"address_input": "1 Main Street", "city": "New York"}),
            ScrapeResult({"address_input": "2 Main Street", "state": "NY"}),
        ]

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scrape-results.csv"
            ScrapeResult.to_csv(results, path)
            with open(path, "r") as file:
                headers = next(csv.reader(file))
            loaded = ScrapeResult.from_csv(path)

        self.assertEqual(set(headers), {"address_input", "city", "state"})
        self.assertEqual(loaded[0].property_info["address_input"], "1 Main Street")
        self.assertEqual(loaded[0].property_info["state"], "")
        self.assertEqual(loaded[1].property_info["city"], "")


if __name__ == "__main__":
    unittest.main()
