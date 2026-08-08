import asyncio
import unittest
from unittest.mock import AsyncMock, Mock, patch

import nodriver as uc

from housefire.scraper.reits_by_ticker.dlr import DlrScraper
from housefire.scraper.scraper_factory import ScraperFactory
from housefire.transformer.reits_by_ticker.dlr import DlrTransformer
from housefire.transformer.reits_by_ticker.pld import PldTransformer
from housefire.transformer.transformer_factory import TransformerFactory


class TestTransformerFactory(unittest.TestCase):

    def setUp(self):
        self.logger_factory = Mock()
        self.logger_factory.get_logger.return_value = Mock()
        self.google_geocode_api_client = Mock()
        self.factory = TransformerFactory(
            self.logger_factory, self.google_geocode_api_client
        )

    def test_get_transformer_configures_ticker_logger_and_geocode_client(self):
        transformer = self.factory.get_transformer("dlr")

        self.assertIsInstance(transformer, DlrTransformer)
        self.assertEqual(transformer.ticker, "dlr")
        self.assertIs(
            transformer.google_geocode_api_client, self.google_geocode_api_client
        )
        self.logger_factory.get_logger.assert_called_once_with("DlrTransformer")

    def test_get_transformer_returns_non_geocode_transformer(self):
        transformer = self.factory.get_transformer("pld")

        self.assertIsInstance(transformer, PldTransformer)
        self.assertEqual(transformer.ticker, "pld")
        self.assertFalse(hasattr(transformer, "google_geocode_api_client"))

    def test_get_transformer_rejects_unsupported_ticker(self):
        with self.assertRaises(ValueError):
            self.factory.get_transformer("unknown")

    def test_supported_tickers_returns_transformer_registry_keys(self):
        self.assertEqual(
            TransformerFactory.supported_tickers(),
            {"pld", "spg", "dlr", "well", "eqix"},
        )


class TestScraperFactory(unittest.TestCase):

    def setUp(self):
        self.logger_factory = Mock()
        self.logger_factory.get_logger.return_value = Mock()
        self.factory = ScraperFactory(self.logger_factory, "/path/to/chrome")

    def test_get_scraper_configures_driver_ticker_and_logger(self):
        driver = Mock()
        self.factory._init_driver_instance = AsyncMock(return_value=driver)

        scraper = asyncio.run(self.factory.get_scraper("dlr", "/tmp/housefire"))

        self.assertIsInstance(scraper, DlrScraper)
        self.assertIs(scraper.driver, driver)
        self.assertEqual(scraper.temp_dir_path, "/tmp/housefire")
        self.assertEqual(scraper.ticker, "dlr")
        self.logger_factory.get_logger.assert_any_call("DlrScraper")

    def test_get_scraper_rejects_unsupported_ticker(self):
        with self.assertRaises(ValueError):
            asyncio.run(self.factory.get_scraper("unknown", "/tmp/housefire"))

    def test_supported_tickers_returns_scraper_registry_keys(self):
        self.assertEqual(
            ScraperFactory.supported_tickers(),
            {"pld", "spg", "dlr", "well", "eqix"},
        )

    @patch("housefire.scraper.scraper_factory.uc.cdp.browser.set_download_behavior")
    @patch("housefire.scraper.scraper_factory.uc.start", new_callable=AsyncMock)
    def test_init_driver_starts_browser_and_configures_downloads(
        self, start, set_download_behavior
    ):
        browser = Mock()
        tab = Mock()
        browser.get = AsyncMock(return_value=tab)
        tab.send = AsyncMock()
        start.return_value = browser
        set_download_behavior.return_value = "download-command"

        result = asyncio.run(self.factory._init_driver_instance("/tmp/housefire"))

        self.assertIs(result, browser)
        start.assert_awaited_once_with(
            headless=False,
            browser_executable_path="/path/to/chrome",
            browser_args=["--disable-gpu"],
        )
        browser.get.assert_awaited_once_with("https://www.google.com")
        set_download_behavior.assert_called_once_with(
            behavior="allowAndName", download_path="/tmp/housefire"
        )
        tab.send.assert_awaited_once_with("download-command")


if __name__ == "__main__":
    unittest.main()
