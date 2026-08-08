# DLR Property Facts Scraping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scrape Digital Realty detail pages and preserve their property-specific facts in the existing Property.facts upload contract.

**Architecture:** Keep the live browser workflow in DlrScraper: discover region pages, extract .metro.a-metro-map-link detail URLs, then extract each detail page with stable scoped selectors. Keep normalization in DlrTransformer: geocode the detail address, parse square footage, and map ordered scalar/list source fields into {label, value} facts. Tests use deterministic fake tabs and elements at the scraper boundary and mocked geocoding at the external API boundary.

**Tech Stack:** Python 3.10+, nodriver, standard-library json/re/urllib.parse, standard-library unittest, existing Housefire ScrapeResult, Property, and transformer classes.

## Global Constraints

- Treat Digital Realty navigation and detail pages as live integration operations; unit tests must not contact the site, Google Maps, or the Housefire API.
- Preserve the existing DLR region discovery and randomized pacing behavior while adding the region → metro → detail traversal.
- Use absolute, de-duplicated detail URLs while preserving discovery order.
- Keep name, address_input, and square_footage as standard fields; convert other retained DLR detail values into ordered Property.facts entries.
- Preserve repeated certifications and security features in source/page order, and preserve the source label for sustainability metrics such as Carbon-Free Energy %.
- Emit strings from ScrapeResult.property_info; encode repeated source values as JSON strings with json.dumps.
- Close opened metro/detail tabs in finally blocks and log/skip malformed individual detail pages.
- Do not change the Housefire API/domain model or introduce a new CSV boundary type.
- Run the repository’s required test, Black, AGENTS synchronizer, and worktree hygiene checks before handoff.

---

### Task 1: Add failing DLR scraper fixture tests

**Files:**
- Modify: housefire/test/test_scraper.py

**Interfaces:**
- Consumes: the existing DlrScraper class and fake nodriver-style tabs/elements.
- Produces: failing tests that define _digital_realty_scrape_detail_urls(tab) -> list[str], _digital_realty_scrape_single_detail(tab) -> ScrapeResult, and the detail-page field contract used by the implementation.

- [ ] **Step 1: Add deterministic fake browser elements and tabs**

Add test-only helpers near the imports. They must implement only the async methods the scraper uses, while keeping selector responses explicit:

~~~python
class FakeElement:
    def __init__(self, text="", text_all=None, attrs=None, children=None, selectors=None):
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
~~~

Keep these helpers in the test module because they model browser inputs and are not production behavior.

- [ ] **Step 2: Write the failing detail-link extraction test**

Add a test to a new TestDlrScraper class:

~~~python
    def test_detail_urls_are_absolute_and_deduplicated_in_discovery_order(self):
        scraper = DlrScraper()
        tab = FakeTab(
            selectors={
                ".a-metro-map-link": [
                    FakeElement(attrs={"href": "/data-centers/americas/chicago/ch1"}),
                    FakeElement(attrs={"href": "https://www.digitalrealty.com/data-centers/americas/chicago/ch2"}),
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
~~~

- [ ] **Step 3: Run the link test and verify the intended failure**

Run:

~~~bash
python3 -m unittest housefire.test.test_scraper.TestDlrScraper.test_detail_urls_are_absolute_and_deduplicated_in_discovery_order
~~~

Expected: FAIL because DlrScraper does not yet define _digital_realty_scrape_detail_urls.

- [ ] **Step 4: Write the failing representative CH1 detail fixture test**

Build fake nested elements using these real page boundaries:

~~~python
    def test_detail_page_extracts_identity_capabilities_and_repeated_sections(self):
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
                            ".sub-accordion-item-text": [FakeElement(text="Energy Star")],
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
                "#facility-template .hero-title": FakeElement(
                    text_all="Chicago\nCH1"
                ),
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
                ".facility-accordion .accordion": [compliance, sustainability, security],
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
~~~

Import json, DlrScraper, and ScrapeResult at the top of the test module. The literal expected dictionary must remain hand-written; do not compute it with scraper helpers.

- [ ] **Step 5: Run the detail fixture test and verify the intended failure**

Run:

~~~bash
python3 -m unittest housefire.test.test_scraper.TestDlrScraper.test_detail_page_extracts_identity_capabilities_and_repeated_sections
~~~

Expected: FAIL because the new detail extraction method does not yet exist.

- [ ] **Step 6: Write the failing tab-lifecycle test**

Add a focused async-flow test with this deterministic driver setup:

~~~python
class FakeDriver:
    def __init__(self, tabs):
        self.tabs = iter(tabs)
        self.calls = []

    async def get(self, url, new_tab=False):
        self.calls.append((url, new_tab))
        return next(self.tabs)

root_tab = FakeTab()
metro_tab = FakeTab(selectors={
    ".a-metro-map-link": [FakeElement(attrs={"href": "/data-centers/americas/chicago/ch1"})]
})
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
        ("https://www.digitalrealty.com/data-centers/americas/chicago", True),
        ("https://www.digitalrealty.com/data-centers/americas/chicago/ch1", True),
    ],
)
self.assertTrue(metro_tab.closed)
self.assertTrue(detail_tab.closed)
self.assertTrue(root_tab.closed)
~~~

Patch _jiggle() and _wait() with AsyncMock so the test is deterministic. Assert that the detail URL is visited with new_tab=True, one ScrapeResult is returned, and both the metro and detail tabs are closed after normal extraction.

Also include a detail-tab failure case whose _digital_realty_scrape_single_detail raises ValueError; assert that the exception is logged and the failed detail is skipped while the tab still closes. This catches the live-crawl failure mode without contacting the site.

- [ ] **Step 7: Run the new scraper tests and confirm they fail for missing production behavior**

Run:

~~~bash
python3 -m unittest housefire.test.test_scraper.TestDlrScraper
~~~

Expected: the new tests fail because the detail URL and detail extraction workflow are not implemented; existing generic scraper tests remain green.

- [ ] **Step 8: Commit the red scraper tests**

Run:

~~~bash
git add housefire/test/test_scraper.py
git commit -m "test: specify DLR detail page scraping"
~~~

### Task 2: Implement DLR region → metro → detail scraping

**Files:**
- Modify: housefire/scraper/reits_by_ticker/dlr.py

**Interfaces:**
- Consumes: nodriver tabs exposing query_selector, query_selector_all, .text, .text_all, .attrs, and .close().
- Produces: DlrScraper._digital_realty_scrape_detail_urls(tab) -> list[str], DlrScraper._digital_realty_scrape_single_detail(tab) -> ScrapeResult, and DlrScraper.execute_scrape() -> list[ScrapeResult].

- [ ] **Step 1: Add URL normalization and detail-link extraction**

Import json, re, and urljoin. Add a class constant:

~~~python
base_url = "https://www.digitalrealty.com"
~~~

Implement _digital_realty_scrape_detail_urls(tab) by querying .a-metro-map-link, reading each non-empty href, applying urljoin(self.base_url, href), and returning a list with the first occurrence of each URL preserved. Keep _digital_realty_scrape_region_urls() on the same absolute/de-duplicated URL behavior, using urljoin instead of string concatenation.

- [ ] **Step 2: Add scoped identity, brochure, and capability extraction helpers**

Implement these small helpers in DlrScraper:

~~~python
async def _query_text(self, tab_or_element, selector, *, text_all=False) -> str | None:
    element = await tab_or_element.query_selector(selector)
    if element is None:
        return None
    raw_text = element.text_all if text_all else element.text
    normalized = " ".join(raw_text.split())
    return normalized or None

async def _scrape_detail_specifications(self, tab) -> dict[str, str]:
    specifications = {}
    for element in await tab.query_selector_all(".facility-table .table-specification"):
        label = await self._query_text(element, ".specification-name")
        value = await self._query_text(element, ".specification-value")
        if label and value:
            specifications[label.rstrip(":").strip()] = value
    return specifications

async def _scrape_detail_accordion_sections(
    self, tab
) -> dict[str, uc.Element]:
    sections = {}
    for accordion in await tab.query_selector_all(".facility-accordion .accordion"):
        title = await self._query_text(accordion, "h3.accordion-title")
        if title:
            sections[title] = accordion
    return sections
~~~

Use these stable selectors confirmed on the supplied detail pages:

- #facility-template .hero-title for the displayed facility identity;
- #facility-template .marker for the facility code;
- #facility-template .hero-description for the description;
- .main-marketo.cta-bar.location .headline for the address;
- .main-marketo.cta-bar.location .a-cta-bar-button and its href for the brochure;
- .facility-table .table-specification, with .specification-name and .specification-value children, for label-aware scalar capabilities;
- .facility-accordion .accordion, h3.accordion-title, .accordion-item-text, .sub-accordion .heading-item, .heading-title, and .sub-accordion-item-text for compliance, sustainability, and security sections.

Normalize displayed labels by stripping whitespace and a trailing colon. Normalize text values with .strip(). For sustainability, preserve the nested heading label as the energy metric label and its nested item as the value. Treat a Certifications nested heading as sustainability certifications; retain other nested sustainability headings as a dynamic label/value pair.

- [ ] **Step 3: Add square-footage isolation from total building size**

Implement a helper that extracts the square-foot portion from the total building size with a strict regular expression such as r"([\d,]+\s*ft²?)", case-insensitive. Return the matched text stripped. If a Total building size value is present but contains no square-foot portion, raise ValueError so malformed source data is not silently converted. Leave the field absent when the whole specification is absent.

- [ ] **Step 4: Implement _digital_realty_scrape_single_detail()**

Build a string-valued property_info dictionary with the standard fields and known detail fields. Use the hero title’s normalized whitespace for name; use the marker for facility_code; and add square_footage from the total building size. Serialize repeated lists with json.dumps in their page order. Omit absent optional fields rather than storing None.

For the three accordion sections, emit:

~~~python
"compliance_certifications": json.dumps(compliance_values),
"sustainability_certifications": json.dumps(sustainability_values),
"sustainability_energy_label": "Carbon-Free Energy %",
"sustainability_energy_value": "100%",
"security_infrastructure": json.dumps(security_values),
~~~

Return ScrapeResult(property_info). Do not scrape footer or generic CTA text.

- [ ] **Step 5: Refactor execute_scrape() to crawl each detail page**

Keep the root page and region discovery, then for each region URL:

1. jiggle;
2. open the region/metro URL in a new tab;
3. wait for the rendered metro content;
4. collect detail URLs with _digital_realty_scrape_detail_urls(); and
5. close the metro tab in finally.

Replace the old _digital_realty_scrape_single_region() property-card parser with the metro URL collector; it must no longer emit the summary-card records that lack detail-page facts. Then iterate detail URLs, jiggle, open each detail URL in a new tab, wait for rendered content, call _digital_realty_scrape_single_detail(), append the result, log and skip exceptions, and close the detail tab in finally. Close the initial root tab in a final cleanup block if the browser returns a closable tab. Preserve the existing per-property warning style and return all successful results.

- [ ] **Step 6: Update _debug_scrape() to use a representative detail page**

Keep the debug command small and live-browser oriented: navigate to https://www.digitalrealty.com/data-centers/americas/chicago/ch1, wait for the page, call _digital_realty_scrape_single_detail(), log the result, return it in a one-item list, and close the tab in a finally block. Do not make the debug path download a CSV.

- [ ] **Step 7: Run the scraper tests and verify they pass**

Run:

~~~bash
python3 -m unittest housefire.test.test_scraper.TestDlrScraper housefire.test.test_scraper.TestScraper
~~~

Expected: PASS with no network or browser startup.

- [ ] **Step 8: Commit the scraper implementation**

Run:

~~~bash
git add housefire/scraper/reits_by_ticker/dlr.py housefire/test/test_scraper.py
git commit -m "feat: scrape DLR detail page facts"
~~~

### Task 3: Add failing DLR transformer fact tests

**Files:**
- Modify: housefire/test/test_transformer.py

**Interfaces:**
- Consumes: DlrTransformer.transform() and ScrapeResult values produced by Task 2.
- Produces: failing tests that define the DLR fact labels, order, JSON list decoding, and dynamic sustainability label behavior.

- [ ] **Step 1: Add a failing representative DLR fact transformation test**

Extend TestDlrTransformer with a complete ScrapeResult containing an address, name, square footage, scalar fields, JSON list fields, and Carbon-Free Energy %. Mock only geocode_addresses() to return a real Geocode object, as the existing tests do. Assert the transformed property has:

~~~python
self.assertEqual(transformed[0].property.name, "Chicago CH1")
self.assertEqual(transformed[0].property.square_footage, 485000.0)
self.assertEqual(
    transformed[0].property.facts,
    [
        {"label": "Facility Code", "value": "CH1"},
        {"label": "Description", "value": "This center supports large deployments."},
        {"label": "Facility Brochure", "value": "https://go2.digitalrealty.com/ch1.pdf"},
        {"label": "Building Structure", "value": "1 Story"},
        {"label": "Total Building Size", "value": "485,000 ft² (45,050 m²)"},
        {"label": "UPS Redundancy", "value": "N+2"},
        {"label": "Cooling Redundancy", "value": "N+1"},
        {"label": "Compliance Certification", "value": "SOC1"},
        {"label": "Compliance Certification", "value": "ISO 27001"},
        {"label": "Sustainability Certification", "value": "Energy Star"},
        {"label": "Carbon-Free Energy %", "value": "100%"},
        {"label": "Security & Infrastructure", "value": "24x7 onsite security personnel"},
        {"label": "Security & Infrastructure", "value": "CCTV with 90 day backup"},
    ],
)
~~~

- [ ] **Step 2: Add failing omission and malformed-input tests**

Add this test helper to TestDlrTransformer so every behavior test uses a real Geocode result and only mocks the external geocoding call:

~~~python
    def get_transformer_with_geocode(self):
        transformer = DlrTransformer()
        transformer.ticker = "dlr"
        transformer.logger = Mock()
        transformer.google_geocode_api_client = Mock()
        transformer.google_geocode_api_client.geocode_addresses.return_value = {
            "1 Main Street": Geocode("1 Main Street", 40.0, -73.0)
        }
        return transformer
~~~

Then add these independently named behaviors:

~~~python
    def test_execute_transform_omits_missing_optional_dlr_facts(self):
        transformer = self.get_transformer_with_geocode()
        result = ScrapeResult(
            {"name": "CH1", "address_input": "1 Main Street", "square_footage": "100 SF"}
        )

        transformed = transformer.transform([result])

        self.assertIsNone(transformed[0].property.facts)

    def test_execute_transform_preserves_dynamic_sustainability_label(self):
        transformer = self.get_transformer_with_geocode()
        result = ScrapeResult(
            {
                "name": "CH1",
                "address_input": "1 Main Street",
                "square_footage": "100 SF",
                "sustainability_energy_label": "Renewable Energy %",
                "sustainability_energy_value": "14%",
            }
        )

        transformed = transformer.transform([result])

        self.assertIn(
            {"label": "Renewable Energy %", "value": "14%"},
            transformed[0].property.facts,
        )

    def test_execute_transform_rejects_malformed_dlr_fact_json(self):
        transformer = self.get_transformer_with_geocode()
        result = ScrapeResult(
            {
                "name": "CH1",
                "address_input": "1 Main Street",
                "square_footage": "100 SF",
                "security_infrastructure": "not-json",
            }
        )

        with self.assertRaises(ValueError):
            transformer.transform([result])
~~~

The test setup must instantiate DlrTransformer, set ticker/logger, and return a real Geocode from the mocked geocode client so these tests exercise the transformer rather than a mock.

- [ ] **Step 3: Run the focused transformer tests and verify the intended failure**

Run:

~~~bash
python3 -m unittest housefire.test.test_transformer.TestDlrTransformer
~~~

Expected: the existing square-footage test remains green, while the new fact tests fail because DlrTransformer does not yet set the name or facts.

- [ ] **Step 4: Commit the red transformer tests**

Run:

~~~bash
git add housefire/test/test_transformer.py
git commit -m "test: specify DLR property fact transformation"
~~~

### Task 4: Implement DLR fact normalization

**Files:**
- Modify: housefire/transformer/reits_by_ticker/dlr.py

**Interfaces:**
- Consumes: ScrapeResult.property_info scalar strings and JSON-encoded repeated fields from Task 2.
- Produces: TransformResult values with geocoded standard fields, Property.name, parsed square_footage, and ordered Property.facts.

- [ ] **Step 1: Add strict JSON list decoding and ordered fact parsing**

Import json. Add an explicit scalar field map:

~~~python
facts_field_map = (
    ("facility_code", "Facility Code"),
    ("description", "Description"),
    ("facility_brochure_url", "Facility Brochure"),
    ("building_structure", "Building Structure"),
    ("total_building_size", "Total Building Size"),
    ("ups_redundancy", "UPS Redundancy"),
    ("cooling_redundancy", "Cooling Redundancy"),
)
~~~

Implement _parse_facts(prop_info) with this algorithm:

~~~python
    @classmethod
    def _parse_facts(cls, prop_info):
        facts = []
        for source_field, label in cls.facts_field_map:
            value = prop_info.get(source_field)
            normalized = value.strip() if value is not None else ""
            if normalized and normalized.upper() not in {"N/A", "TBD"}:
                facts.append({"label": label, "value": normalized})

        list_fields = (
            ("compliance_certifications", "Compliance Certification"),
            ("sustainability_certifications", "Sustainability Certification"),
        )
        for source_field, label in list_fields:
            encoded_values = prop_info.get(source_field)
            if encoded_values is None:
                continue
            values = json.loads(encoded_values)
            if not isinstance(values, list):
                raise ValueError(f"Expected a list for {source_field}")
            for value in values:
                if not isinstance(value, str):
                    raise ValueError(f"Expected string values for {source_field}")
                if value.strip():
                    facts.append({"label": label, "value": value.strip()})

        energy_label = prop_info.get("sustainability_energy_label")
        energy_value = prop_info.get("sustainability_energy_value")
        if energy_label is not None or energy_value is not None:
            if not energy_label or not energy_value:
                raise ValueError("Incomplete sustainability energy fact")
            facts.append({"label": energy_label.strip(), "value": energy_value.strip()})

        encoded_security_values = prop_info.get("security_infrastructure")
        if encoded_security_values is not None:
            security_values = json.loads(encoded_security_values)
            if not isinstance(security_values, list):
                raise ValueError("Expected a list for security_infrastructure")
            for value in security_values:
                if not isinstance(value, str):
                    raise ValueError("Expected string values for security_infrastructure")
                if value.strip():
                    facts.append({"label": "Security & Infrastructure", "value": value.strip()})
        return facts or None
~~~

Raise ValueError for malformed JSON, a present non-list JSON value, or an energy label without a value. Strip surrounding whitespace and skip case-insensitive N/A/TBD, matching the PLD fact behavior.

- [ ] **Step 2: Attach name and facts in execute_transform()**

After _geocode_transform(data) returns results, set each property’s name from result.scrape_result.property_info.get("name"), assign _parse_facts(result.scrape_result.property_info), and parse square_footage exactly as the current implementation does. Leave the geocode client interaction and missing-address behavior unchanged.

- [ ] **Step 3: Run the focused transformer tests and verify they pass**

Run:

~~~bash
python3 -m unittest housefire.test.test_transformer.TestDlrTransformer housefire.test.test_transformer.TestGeocodeTransformer
~~~

Expected: PASS, including the existing square-footage and geocode behavior.

- [ ] **Step 4: Commit the transformer implementation**

Run:

~~~bash
git add housefire/transformer/reits_by_ticker/dlr.py housefire/test/test_transformer.py
git commit -m "feat: transform DLR property facts"
~~~

### Task 5: Run repository validation and synchronize agent inventory

**Files:**
- Modify: AGENTS.md only if scripts/sync_agents_md.py reports an inventory change.

**Interfaces:**
- Consumes: the tested DLR scraper and transformer from Tasks 1–4.
- Produces: a verified worktree with no generated artifacts, secrets, logs, CSVs, or unrelated changes.

- [ ] **Step 1: Run the complete unit test suite**

Run:

~~~bash
python3 -m unittest discover -s housefire/test -p 'test_*.py'
~~~

Expected: all tests pass without network or browser access.

- [ ] **Step 2: Run the formatter check**

Run:

~~~bash
black --check housefire scripts
~~~

Expected: Black reports that files would be left unchanged.

- [ ] **Step 3: Run the AGENTS synchronizer and inspect its diff**

Run:

~~~bash
python3 scripts/sync_agents_md.py
git diff -- AGENTS.md
~~~

Expected: the inventory remains accurate and only changes if the synchronizer discovers a relevant tracked file.

- [ ] **Step 4: Review the final diff and worktree hygiene**

Run:

~~~bash
git status --short
git diff --check main..HEAD
~~~

Confirm there are no credentials, logs, generated CSVs, browser profiles, or unrelated edits.

- [ ] **Step 5: Record intentionally unrun integration checks**

Do not run the full live dlr scrape as ordinary validation: it launches visible Chrome, traverses many live pages, and depends on current site behavior and rate limits. Report that manual live validation was not run unless the user explicitly requests it with configured credentials/display.
