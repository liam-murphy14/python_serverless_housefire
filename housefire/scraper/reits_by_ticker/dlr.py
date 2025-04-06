import nodriver as uc
from housefire.scraper.scraper import Scraper, ScrapeResult
from housefire.dependency.housefire_client.housefire_object import Property


class DlrScraper(Scraper):
    def __init__(self):
        super().__init__()

    async def execute_scrape(self) -> list[ScrapeResult]:
        start_url = "https://www.digitalrealty.com/data-centers"
        tab = await self.driver.get(start_url)

        results: list[ScrapeResult] = list()
        property_urls = await self._digital_realty_scrape_region_urls(tab)
        self.logger.debug(f"found property urls: {property_urls}")

        for property_url in property_urls:
            await self._jiggle()
            property_tab = await self.driver.get(property_url, new_tab=True)
            try:
                scrape_results = await self._digital_realty_scrape_single_region(
                    property_tab
                )
                results.extend(scrape_results)
            except Exception as e:
                self.logger.warning(f"error scraping property: {property_url}, {e}")
            finally:
                await property_tab.close()

        return results

    async def _digital_realty_scrape_region_urls(self, tab: uc.Tab) -> list[str]:
        link_elements = await tab.query_selector_all(".region")
        base_url = "https://www.digitalrealty.com"
        return [base_url + element.attrs["href"] for element in link_elements]

    async def _digital_realty_scrape_single_region(
        self, tab: uc.Tab
    ) -> list[ScrapeResult]:
        await self._wait(30)
        property_divs = await tab.query_selector_all(".a-metro-map-link")
        names = [
            (await div.query_selector(".title")).text_all.strip()
            for div in property_divs
        ]
        address_inputs = [
            (await div.query_selector(".sub-title")).text.strip()
            for div in property_divs
        ]
        sq_footage_parts = [
            (await div.query_selector(".bottom-part")).children[0].text.strip()
            for div in property_divs
        ]
        property_infos = [
            {
                "name": name,
                "address_input": address_input,
                "square_footage": sq_footage,
            }
            for name, address_input, sq_footage in zip(
                names, address_inputs, sq_footage_parts
            )
        ]
        return [ScrapeResult(property_info) for property_info in property_infos]

    async def _debug_scrape(self):
        start_url = "https://www.digitalrealty.com/data-centers/americas/chicago"
        self.logger.debug(f"debug scraping for {self.ticker} at {start_url}")
        tab = await self.driver.get(start_url)
        results = await self._digital_realty_scrape_single_region(tab)
        self.logger.debug(f"SCRAPED SINGLE REGION DF")
        self.logger.debug(results)
        self.logger.debug("\n\n\n")
        return results
