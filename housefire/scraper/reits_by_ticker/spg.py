import nodriver as uc
import pandas as pd
from housefire.scraper.scraper import Scraper


class SpgScraper(Scraper):
    def __init__(self):
        super().__init__()

    async def execute_scrape(self) -> pd.DataFrame:
        us_start_url = "https://www.simon.com/mall"
        international_start_url = "https://www.simon.com/mall/international"
        us_tab = await self.driver.get(us_start_url, new_tab=True)
        await self._jiggle()
        international_tab = await self.driver.get(international_start_url, new_tab=True)

        links, names, locations = await self._simon_scrape_property_mall(us_tab)
        int_links, int_names, int_locations = await self._simon_scrape_property_mall(
            international_tab
        )
        links.extend(int_links)
        names.extend(int_names)
        locations.extend(int_locations)

        geo_addresses = [
            f"{name}, {location}" for name, location in zip(names, locations)
        ]

        return pd.DataFrame(
            {
                "name": names,
                "address": geo_addresses,
            }
        )

    async def _simon_scrape_property_mall(
        self,
        tab: uc.Tab,
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Scrape the property links, names, and locations from the simon mall page
        returns tuple of (link, name, location)
        """

        properties_div = await tab.query_selector(".mall-list")
        property_link_elements = await properties_div.query_selector_all("a")
        property_links = [element.attrs["href"] for element in property_link_elements]
        self.logger.debug(f"found property links: {property_links}")

        property_names = [
            (await element.query_selector(".mall-list-item-name")).text
            for element in property_link_elements
        ]
        self.logger.debug(f"found property names: {property_names}")

        property_locations = [
            (await element.query_selector(".mall-list-item-location")).text
            for element in property_link_elements
        ]
        self.logger.debug(f"found property locations: {property_locations}")

        return property_links, property_names, property_locations

    async def _debug_scrape(self):
        start_url = "https://www.simon.com/mall"
        self.logger.debug(f"starting debug scrape for {self.ticker} on {start_url}")
        tab = await self.driver.get(start_url)
        self.logger.debug(await self._simon_scrape_property_mall(tab))
