import unittest
from unittest.mock import Mock, patch

from housefire.cli import _get_supported_tickers, sync_reits_main
from housefire.dependency.housefire_client.housefire_object import Reit


class TestReitSync(unittest.TestCase):
    @patch(
        "housefire.cli.TransformerFactory.supported_tickers",
        return_value={"pld", "eqix"},
    )
    @patch(
        "housefire.cli.ScraperFactory.supported_tickers",
        return_value={"pld", "spg"},
    )
    def test_get_supported_tickers_returns_sorted_uppercase_union(
        self, scraper, transformer
    ):
        self.assertEqual(_get_supported_tickers(), ["EQIX", "PLD", "SPG"])

    @patch("housefire.cli.HousefireClient")
    @patch(
        "housefire.cli._get_supported_tickers",
        return_value=["EQIX", "PLD", "SPG"],
    )
    def test_sync_reits_creates_only_missing_tickers(self, supported, client_class):
        client = client_class.return_value
        client.get_reits.return_value = [Reit(ticker="PLD")]
        client.post_reit.side_effect = lambda reit: reit

        existing, created = sync_reits_main(Mock())

        self.assertEqual(existing, ["PLD"])
        self.assertEqual(created, ["EQIX", "SPG"])
        client.post_reit.assert_any_call(Reit(ticker="EQIX"))
        client.post_reit.assert_any_call(Reit(ticker="SPG"))
        self.assertEqual(client.post_reit.call_count, 2)
