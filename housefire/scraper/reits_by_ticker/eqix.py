from housefire.logger import get_logger
import nodriver as uc
import pandas as pd
from housefire.scraper.scraper import Scraper

logger = get_logger(__name__)


class EqixScraper(Scraper):
    def __init__(self, driver: uc.Browser):
        super().__init__(driver)
        self.ticker = "eqix"

    async def execute_scrape(self) -> pd.DataFrame:
        start_url = "https://www.equinix.com/data-centers"
        tab = await self.driver.get(start_url)

        df_list = list()
        city_urls = await self._eqix_scrape_city_urls(tab)
        logger.debug(f"found city urls: {city_urls}")
        property_urls = list()
        for city_url in city_urls:
            self._jiggle()
            city_tab = await self.driver.get(city_url, new_tab=True)
            try:
                property_urls.extend(
                    await self._eqix_scrape_single_city_property_urls(city_tab)
                )
            except Exception as e:
                logger.warning(f"error scraping city: {city_url}, {e}")
            finally:
                await city_tab.close()
        logger.debug(f"found property urls: {property_urls}")

        for property_url in property_urls:
            self._jiggle()
            property_tab = await self.driver.get(property_url, new_tab=True)
            try:
                df = await self._eqix_scrape_single_property(property_tab)
                df_list.append(df)
            except Exception as e:
                logger.warning(f"error scraping property: {property_url}, {e}")
            finally:
                await property_tab.close()

        return pd.concat(df_list)

    async def _eqix_scrape_city_urls(self, tab: uc.Tab) -> list[str]:
        tab_content = await tab.select(".tabs-content")
        link_elements = await tab_content.query_selector_all(".regions_metro-link")
        logger.debug(f"found link elements: {link_elements}")
        return [link_element.attrs["href"] for link_element in link_elements]

    async def _eqix_scrape_single_city_property_urls(self, tab: uc.Tab) -> list[str]:
        urls_to_scrape = list()
        try:
            dropdown_menu_button = await tab.select("#dropdownMenuButton")
            logger.debug(f"dropdown_menu_button: {dropdown_menu_button}")
            dropdown_menu_list = (
                (await tab.select(".ibx-dropdown")).children[0].children
            )
            logger.debug(f"found dropdown_menu_list: {dropdown_menu_list}")
            urls_to_scrape = [item.attrs["href"] for item in dropdown_menu_list]
        except TimeoutError as e:
            logger.debug("no dropdown menu button, looking for primary button")
            primary_button_list = await tab.select_all(".btn-primary")
            logger.debug(f"primary_button_list: {primary_button_list}")
            primary_buttons_with_real_href = list(
                filter(
                    lambda button: "href" in button.attrs
                    and button.attrs["href"] != "#",
                    primary_button_list,
                )
            )
            primary_button = (
                primary_buttons_with_real_href[0]
                if len(primary_buttons_with_real_href) > 0
                else None
            )
            logger.debug(f"primary_button: {primary_button}")
            if primary_button is None:
                raise Exception("could not find primary button")
            urls_to_scrape.append(primary_button.attrs["href"])

        return urls_to_scrape

    async def _eqix_scrape_single_property(self, tab: uc.Tab) -> pd.DataFrame:
        name_div = await tab.select(".hero-slice-sub-headline")
        short_name_div = await tab.select(".hero-slice-headline")
        logger.debug(f"name divs: {name_div}\n\n {short_name_div}")
        name = f"{short_name_div.text.strip()} - {name_div.text.strip()}"
        logger.debug(f"scraping property with name: {name}")

        contact_div = await tab.select(".ibx-contact")
        logger.debug(f"contact div: {contact_div}")

        address_div = contact_div.children[0].children[0].children[0]
        logger.debug(f"address_div: {address_div}")

        # some properties only have address line 2
        address_line_1_div, address_line_2_div = None, None
        if len(address_div.children) > 2:
            address_line_1_div = address_div.children[1]
            logger.debug(f"address_line_1_div: {address_line_1_div}")
            address_line_2_div = address_div.children[2]
            logger.debug(f"address_line_2_div: {address_line_2_div}")
        elif len(address_div.children) == 2:
            logger.debug("address_div has 2 children, assuming only address line 2")
            address_line_2_div = address_div.children[1]
            logger.debug(f"address_line_2_div: {address_line_2_div}")
        else:
            raise Exception("could not find address div children")

        address_part_list = address_line_2_div.text.strip().split(",")
        logger.debug(f"address parts: {address_part_list}")
        zip_code = address_part_list[-1].strip()
        country = address_part_list[-2].strip()
        city = address_part_list[0].strip()
        state = None
        if len(address_part_list) >= 4:
            state = address_part_list[1].strip()

        address = (
            address_line_1_div.text.strip() if address_line_1_div is not None else None
        )

        return pd.DataFrame(
            {
                "name": [name],
                "address": [f"{address}, {city}, {state}, {zip_code}, {country}"],
            }
        )

    async def _debug_scrape(self):
        start_url = "https://www.equinix.com/data-centers/asia-pacific-colocation/australia-colocation/brisbane-data-centers/br1"
        logger.debug(f"debug scraping for {self.ticker} at {start_url}")
        tab = await self.driver.get(start_url)
        df = await self._eqix_scrape_single_property(tab)
        logger.debug("SCRAPED ONE ADDRESS LINE DF")
        logger.debug(df)
        logger.debug("\n\n\n")

        tab = await self.driver.get(
            "https://www.equinix.com/data-centers/americas-colocation/united-states-colocation/chicago-data-centers/ch2"
        )
        df = await self._eqix_scrape_single_property(tab)
        logger.debug("SCRAPED TWO ADDRESS LINE DF")
        logger.debug(df)
        logger.debug("\n\n\n")

        tab = await self.driver.get("https://www.equinix.com/data-centers")
        df = await self._eqix_scrape_city_urls(tab)
        logger.debug("SCRAPED CITY URLS")
        logger.debug(df)
        logger.debug("\n\n\n")

        tab = await self.driver.get(
            "https://www.equinix.com/data-centers/americas-colocation/canada-colocation/calgary-data-centers"
        )
        df = await self._eqix_scrape_single_city_property_urls(tab)
        logger.debug("SCRAPED MULTIPLE PROPERTY URLS")
        logger.debug(df)
        logger.debug("\n\n\n")

        tab = await self.driver.get(
            "https://www.equinix.com/data-centers/asia-pacific-colocation/australia-colocation/brisbane-data-centers"
        )
        df = await self._eqix_scrape_single_city_property_urls(tab)
        logger.debug("SCRAPED SINGLE PROPERTY URL")
        logger.debug(df)
        logger.debug("\n\n\n")
