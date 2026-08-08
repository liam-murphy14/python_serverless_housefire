import json
import re
from urllib.parse import urljoin

import nodriver as uc

from housefire.scraper.scraper import Scraper, ScrapeResult


class DlrScraper(Scraper):
    base_url = "https://www.digitalrealty.com"

    async def execute_scrape(self) -> list[ScrapeResult]:
        start_url = f"{self.base_url}/data-centers"
        root_tab = None
        results: list[ScrapeResult] = []
        detail_urls: list[str] = []
        seen_detail_urls: set[str] = set()

        try:
            root_tab = await self.driver.get(start_url)
            region_urls = await self._digital_realty_scrape_region_urls(root_tab)
            self.logger.debug(f"found property urls: {region_urls}")

            for region_url in region_urls:
                await self._jiggle()
                metro_tab = None
                try:
                    metro_tab = await self.driver.get(region_url, new_tab=True)
                    await self._wait(30)
                    for detail_url in await self._digital_realty_scrape_detail_urls(
                        metro_tab
                    ):
                        if detail_url not in seen_detail_urls:
                            seen_detail_urls.add(detail_url)
                            detail_urls.append(detail_url)
                except Exception as error:
                    self.logger.warning(
                        f"error scraping property: {region_url}, {error}"
                    )
                finally:
                    if metro_tab is not None:
                        await metro_tab.close()

            for detail_url in detail_urls:
                await self._jiggle()
                detail_tab = None
                try:
                    detail_tab = await self.driver.get(detail_url, new_tab=True)
                    await self._wait(30)
                    results.append(
                        await self._digital_realty_scrape_single_detail(detail_tab)
                    )
                except Exception as error:
                    self.logger.warning(
                        f"error scraping property: {detail_url}, {error}"
                    )
                finally:
                    if detail_tab is not None:
                        await detail_tab.close()
        finally:
            if root_tab is not None and hasattr(root_tab, "close"):
                await root_tab.close()

        return results

    async def _digital_realty_scrape_region_urls(self, tab: uc.Tab) -> list[str]:
        urls: list[str] = []
        seen_urls: set[str] = set()
        for element in await tab.query_selector_all(".region"):
            href = element.attrs.get("href")
            if href:
                url = urljoin(self.base_url, href)
                if url not in seen_urls:
                    seen_urls.add(url)
                    urls.append(url)
        return urls

    async def _digital_realty_scrape_detail_urls(self, tab: uc.Tab) -> list[str]:
        urls: list[str] = []
        seen_urls: set[str] = set()
        for element in await tab.query_selector_all(".a-metro-map-link"):
            href = element.attrs.get("href")
            if href:
                url = urljoin(self.base_url, href)
                if url not in seen_urls:
                    seen_urls.add(url)
                    urls.append(url)
        return urls

    async def _query_text(
        self, tab_or_element, selector, *, text_all: bool = False
    ) -> str | None:
        element = await tab_or_element.query_selector(selector)
        if element is None:
            return None
        raw_text = element.text_all if text_all else element.text
        normalized = " ".join(raw_text.split())
        return normalized or None

    async def _scrape_detail_specifications(self, tab) -> dict[str, str]:
        specifications = {}
        for element in await tab.query_selector_all(
            ".facility-table .table-specification"
        ):
            label = await self._query_text(element, ".specification-name")
            value = await self._query_text(element, ".specification-value")
            if label and value:
                specifications[label.rstrip(":").strip()] = value
        return specifications

    async def _scrape_detail_accordion_sections(self, tab) -> dict[str, uc.Element]:
        sections = {}
        for accordion in await tab.query_selector_all(".facility-accordion .accordion"):
            title = await self._query_text(accordion, "h3.accordion-title")
            if title:
                sections[title] = accordion
        return sections

    @staticmethod
    def _extract_square_footage(total_building_size: str) -> str:
        match = re.search(r"([\d,]+\s*ft²?)", total_building_size, re.IGNORECASE)
        if match is None:
            raise ValueError(
                "Total building size has no square-foot portion: "
                f"{total_building_size}"
            )
        return match.group(1).strip()

    @staticmethod
    def _element_text(element) -> str | None:
        normalized = " ".join(element.text.split())
        return normalized or None

    async def _accordion_item_texts(self, accordion, selector) -> list[str]:
        values = []
        for element in await accordion.query_selector_all(selector):
            value = self._element_text(element)
            if value:
                values.append(value)
        return values

    async def _digital_realty_scrape_single_detail(self, tab: uc.Tab) -> ScrapeResult:
        property_info: dict[str, str] = {}
        detail_fields = (
            ("name", "#facility-template .hero-title", True),
            ("facility_code", "#facility-template .marker", False),
            ("description", "#facility-template .hero-description", False),
            ("address_input", ".main-marketo.cta-bar.location .headline", False),
        )
        for field, selector, text_all in detail_fields:
            value = await self._query_text(tab, selector, text_all=text_all)
            if value:
                property_info[field] = value

        brochure = await tab.query_selector(
            ".main-marketo.cta-bar.location .a-cta-bar-button"
        )
        if brochure is not None:
            href = brochure.attrs.get("href")
            if href:
                property_info["facility_brochure_url"] = urljoin(self.base_url, href)

        specifications = await self._scrape_detail_specifications(tab)
        specification_fields = {
            "Building structure": "building_structure",
            "Total building size": "total_building_size",
            "UPS redundancy": "ups_redundancy",
            "Cooling redundancy": "cooling_redundancy",
        }
        for label, field in specification_fields.items():
            value = specifications.get(label)
            if value:
                property_info[field] = value

        total_building_size = specifications.get("Total building size")
        if total_building_size:
            property_info["square_footage"] = self._extract_square_footage(
                total_building_size
            )

        sections = await self._scrape_detail_accordion_sections(tab)
        compliance = sections.get("Compliance")
        if compliance is not None:
            compliance_values = await self._accordion_item_texts(
                compliance, ".accordion-item-text"
            )
            if compliance_values:
                property_info["compliance_certifications"] = json.dumps(
                    compliance_values
                )

        sustainability = sections.get("Sustainability")
        if sustainability is not None:
            sustainability_certifications: list[str] = []
            for heading_item in await sustainability.query_selector_all(
                ".sub-accordion .heading-item"
            ):
                heading = await self._query_text(heading_item, ".heading-title")
                values = await self._accordion_item_texts(
                    heading_item, ".sub-accordion-item-text"
                )
                if not heading or not values:
                    continue
                if heading == "Certifications":
                    sustainability_certifications.extend(values)
                else:
                    property_info["sustainability_energy_label"] = heading
                    property_info["sustainability_energy_value"] = values[0]
            if sustainability_certifications:
                property_info["sustainability_certifications"] = json.dumps(
                    sustainability_certifications
                )

        security = sections.get("Security & Infrastructure")
        if security is not None:
            security_values = await self._accordion_item_texts(
                security, ".accordion-item-text"
            )
            if security_values:
                property_info["security_infrastructure"] = json.dumps(security_values)

        return ScrapeResult(property_info)

    async def _debug_scrape(self) -> list[ScrapeResult]:
        start_url = f"{self.base_url}/data-centers/americas/chicago/ch1"
        self.logger.debug(f"debug scraping for {self.ticker} at {start_url}")
        tab = await self.driver.get(start_url)
        try:
            await self._wait(30)
            result = await self._digital_realty_scrape_single_detail(tab)
            self.logger.debug("SCRAPED SINGLE DETAIL")
            self.logger.debug(result)
            self.logger.debug("\n\n\n")
            return [result]
        finally:
            await tab.close()
