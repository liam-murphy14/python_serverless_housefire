from housefire.logger import get_logger
import nodriver as uc
import pandas as pd
from housefire.scraper.scraper import Scraper

logger = get_logger(__name__)


class DlrScraper(Scraper):
    def __init__(self, driver: uc.Browser):
        super().__init__(driver)
        self.ticker = "dlr"

    async def execute_scrape(self) -> pd.DataFrame:
        start_url = "https://www.digitalrealty.com/data-centers"
        tab = await self.driver.get(start_url)

        df_list = list()
        property_urls = await self._digital_realty_scrape_region_urls(tab)
        logger.debug(f"found property urls: {property_urls}")

        for property_url in property_urls:
            self._jiggle()
            property_tab = await self.driver.get(property_url, new_tab=True)
            try:
                df = await self._digital_realty_scrape_single_region(property_tab)
                df_list.append(df)
            except Exception as e:
                logger.warning(f"error scraping property: {property_url}, {e}")
            finally:
                await property_tab.close()

        return pd.concat(df_list)

    async def _digital_realty_scrape_region_urls(self, tab: uc.Tab) -> list[str]:
        link_elements = await tab.query_selector_all(".region")
        base_url = "https://www.digitalrealty.com"
        return [base_url + element.attrs["href"] for element in link_elements]

    async def _digital_realty_scrape_single_region(self, tab: uc.Tab) -> pd.DataFrame:
        self._wait(30)
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
        return pd.DataFrame(
            {
                "name": names,
                "address": address_inputs,
                "squareFootage": sq_footage_parts,
            }
        )

    async def _debug_scrape(self):
        start_url = "https://www.digitalrealty.com/data-centers/americas/chicago"
        logger.debug(f"debug scraping for {self.ticker} at {start_url}")
        tab = await self.driver.get(start_url)
        df = await self._digital_realty_scrape_single_region(tab)
        logger.debug(f"SCRAPED SINGLE REGION DF")
        logger.debug(df)
        logger.debug("\n\n\n")
