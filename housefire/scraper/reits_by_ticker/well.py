from housefire.logger import get_logger
import nodriver as uc
import pandas as pd
from housefire.scraper.scraper import Scraper

logger = get_logger(__name__)

class WellScraper(Scraper):
    def __init__(self, driver: uc.Browser):
        super().__init__(driver)
        self.ticker = "well"

    async def execute_scrape(self) -> pd.DataFrame:
        start_url = "https://medicaloffice.welltower.com/search?address=USA&min=null&max=null&moveInTiming="
        tab = await self.driver.get(start_url)

        df_list = list()
        property_urls = await self._welltower_scrape_property_urls(tab)
        logger.debug(f"found property urls: {property_urls}")

        for property_url in property_urls:
            self._jiggle()
            property_tab = await self.driver.get(property_url, new_tab=True)
            try:
                df = await self._welltower_scrape_single_property(property_tab)
                df_list.append(df)
            except Exception as e:
                logger.warning(f"error scraping property: {property_url}, {e}")
            finally:
                await property_tab.close()

        return pd.concat(df_list)


    async def _welltower_scrape_property_urls(self, tab: uc.Tab) -> list[str]:
        self._wait(30)
        link_divs = await tab.query_selector_all("a[href]")
        links = [link.attrs["href"] for link in link_divs]
        links_without_https = list(filter(lambda link: link[:4] != "http", set(links)))
        return list(
            map(
                lambda endpoint: "https://medicaloffice.welltower.com" + endpoint,
                links_without_https,
            )
        )


    async def _welltower_scrape_single_property(self, tab: uc.Tab) -> pd.DataFrame:
        name_div = await tab.select(".chakra-heading")
        address_div = (await tab.query_selector_all(".chakra-text"))[1]
        name = name_div.text.strip()
        address_line_1 = address_div.text.strip()
        address_line_2 = address_div.text_all[len(address_line_1) :]
        city, state = tuple(map(lambda token: token.strip(), address_line_2.split(",")))
        country = "US"
        return pd.DataFrame(
            {
                "name": [name],
                "address": [f"{address_line_1}, {city}, {state}, {country}"],
            }
        )


    async def _debug_scrape(self):
        # WELL welltower scrape property links
        tab = await self.driver.get("https://medicaloffice.welltower.com/search?address=USA&min=null&max=null&moveInTiming=")
        logger.debug("SCRAPED PROPERTY URLS")
        logger.debug(await self._welltower_scrape_property_urls(tab))
        logger.debug("\n\n\n")

        # WELL welltower scrape single property
        tab = await self.driver.get("https://medicaloffice.welltower.com/450-south-kitsap-boulevard")
        logger.debug("SCRAPED SINGLE PROPERTY")
        logger.debug(await self._welltower_scrape_single_property(tab))
        logger.debug("\n\n\n")

