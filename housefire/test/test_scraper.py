import asyncio
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from housefire.scraper.reits_by_ticker.dlr import DlrScraper
from housefire.scraper.scraper import ScrapeResult, Scraper


class FakeElement:
    def __init__(
        self, text="", text_all=None, attrs=None, children=None, selectors=None
    ):
        self.text = text
        self.text_all = text if text_all is None else text_all
        self.attrs = attrs or {}
        self.children = children or []
        self.selectors = selectors or {}

    async def query_selector(self, selector):
        return self.selectors.get(selector)

    async def query_selector_all(self, selector):
        return self.selectors.get(selector, [])


class FakeTab(FakeElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.closed = False

    async def close(self):
        self.closed = True


class FakeDriver:
    def __init__(self, tabs):
        self.tabs = iter(tabs)
        self.calls = []

    async def get(self, url, new_tab=False):
        self.calls.append((url, new_tab))
        return next(self.tabs)


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


class TestDlrScraper(unittest.TestCase):

    def test_detail_urls_are_absolute_and_deduplicated_in_discovery_order(self):
        scraper = DlrScraper()
        tab = FakeTab(
            selectors={
                ".a-metro-map-link": [
                    FakeElement(attrs={"href": "/data-centers/americas/chicago/ch1"}),
                    FakeElement(
                        attrs={
                            "href": "https://www.digitalrealty.com/data-centers/americas/chicago/ch2"
                        }
                    ),
                    FakeElement(attrs={"href": "/data-centers/americas/chicago/ch1"}),
                ]
            }
        )

        result = asyncio.run(scraper._digital_realty_scrape_detail_urls(tab))

        self.assertEqual(
            result,
            [
                "https://www.digitalrealty.com/data-centers/americas/chicago/ch1",
                "https://www.digitalrealty.com/data-centers/americas/chicago/ch2",
            ],
        )

    def test_detail_page_extracts_identity_capabilities_and_repeated_sections(self):
        scraper = DlrScraper()
        specification = lambda label, value: FakeElement(
            selectors={
                ".specification-name": FakeElement(text=f"{label}:"),
                ".specification-value": FakeElement(text=value),
            }
        )
        compliance = FakeElement(
            selectors={
                "h3.accordion-title": FakeElement(text="Compliance"),
                ".accordion-item-text": [
                    FakeElement(text="SOC1"),
                    FakeElement(text="ISO 27001"),
                ],
                ".sub-accordion .heading-item": [],
            }
        )
        sustainability = FakeElement(
            selectors={
                "h3.accordion-title": FakeElement(text="Sustainability"),
                ".accordion-item-text": [],
                ".sub-accordion .heading-item": [
                    FakeElement(
                        selectors={
                            ".heading-title": FakeElement(text="Certifications"),
                            ".sub-accordion-item-text": [
                                FakeElement(text="Energy Star")
                            ],
                        }
                    ),
                    FakeElement(
                        selectors={
                            ".heading-title": FakeElement(text="Carbon-Free Energy %"),
                            ".sub-accordion-item-text": [FakeElement(text="100%")],
                        }
                    ),
                ],
            }
        )
        security = FakeElement(
            selectors={
                "h3.accordion-title": FakeElement(text="Security & Infrastructure"),
                ".accordion-item-text": [
                    FakeElement(text="24x7 onsite security personnel"),
                    FakeElement(text="CCTV with 90 day backup"),
                ],
                ".sub-accordion .heading-item": [],
            }
        )
        tab = FakeTab(
            selectors={
                "#facility-template .hero-title": FakeElement(text_all="Chicago\nCH1"),
                "#facility-template .marker": FakeElement(text="CH1"),
                "#facility-template .hero-description": FakeElement(
                    text="This center supports large deployments."
                ),
                ".main-marketo.cta-bar.location .headline": FakeElement(
                    text="2200 Busse Road, Elk Grove Village, IL 60007"
                ),
                ".main-marketo.cta-bar.location .a-cta-bar-button": FakeElement(
                    attrs={"href": "https://go2.digitalrealty.com/ch1.pdf"}
                ),
                ".facility-table .table-specification": [
                    specification("Building structure", "1 Story"),
                    specification("Total building size", "485,000 ft² (45,050 m²)"),
                    specification("UPS redundancy", "N+2"),
                    specification("Cooling redundancy", "N+1"),
                ],
                ".facility-accordion .accordion": [
                    compliance,
                    sustainability,
                    security,
                ],
            }
        )

        result = asyncio.run(scraper._digital_realty_scrape_single_detail(tab))

        self.assertEqual(
            result.property_info,
            {
                "name": "Chicago CH1",
                "facility_code": "CH1",
                "description": "This center supports large deployments.",
                "address_input": "2200 Busse Road, Elk Grove Village, IL 60007",
                "facility_brochure_url": "https://go2.digitalrealty.com/ch1.pdf",
                "building_structure": "1 Story",
                "total_building_size": "485,000 ft² (45,050 m²)",
                "square_footage": "485,000 ft²",
                "ups_redundancy": "N+2",
                "cooling_redundancy": "N+1",
                "compliance_certifications": json.dumps(["SOC1", "ISO 27001"]),
                "sustainability_certifications": json.dumps(["Energy Star"]),
                "sustainability_energy_label": "Carbon-Free Energy %",
                "sustainability_energy_value": "100%",
                "security_infrastructure": json.dumps(
                    ["24x7 onsite security personnel", "CCTV with 90 day backup"]
                ),
            },
        )

    def test_execute_scrape_visits_detail_tabs_and_closes_tabs(self):
        scraper = DlrScraper()
        scraper.logger = Mock()
        root_tab = FakeTab()
        metro_tab = FakeTab(
            selectors={
                ".a-metro-map-link": [
                    FakeElement(attrs={"href": "/data-centers/americas/chicago/ch1"})
                ]
            }
        )
        detail_tab = FakeTab()
        scraper.driver = FakeDriver([root_tab, metro_tab, detail_tab])
        scraper._jiggle = AsyncMock()
        scraper._wait = AsyncMock()
        scraper._digital_realty_scrape_single_detail = AsyncMock(
            return_value=ScrapeResult({"address_input": "2200 Busse Road"})
        )
        scraper._digital_realty_scrape_region_urls = AsyncMock(
            return_value=["https://www.digitalrealty.com/data-centers/americas/chicago"]
        )

        results = asyncio.run(scraper.execute_scrape())

        self.assertEqual(len(results), 1)
        self.assertEqual(
            scraper.driver.calls,
            [
                ("https://www.digitalrealty.com/data-centers", False),
                (
                    "https://www.digitalrealty.com/data-centers/americas/chicago",
                    True,
                ),
                (
                    "https://www.digitalrealty.com/data-centers/americas/chicago/ch1",
                    True,
                ),
            ],
        )
        self.assertTrue(metro_tab.closed)
        self.assertTrue(detail_tab.closed)
        self.assertTrue(root_tab.closed)


if __name__ == "__main__":
    unittest.main()
