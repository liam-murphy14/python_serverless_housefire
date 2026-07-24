# DLR Detail-Page Scraping and Transformation Design

**Status:** Approved for implementation on 2026-07-24

## Goal

Extend the Digital Realty (DLR) pipeline so it follows the existing region and metro navigation to each data-center detail page, captures the detail page's property-specific facts, and preserves those facts through transformation and transformed CSV output without changing the Housefire API/domain model.

## Scope

The scraper will capture data-center-specific content from the detail page, including identity, description, address, brochure link, capability descriptions and values, compliance certifications, sustainability certifications and energy metric, and security/infrastructure features. Global navigation, footer content, generic calls to action, and unrelated related-resource cards are outside the property record.

The existing `Property` API model remains unchanged in this change. The API/model agent can map the transformed DLR facts into its expanded fields later.

## Architecture and data flow

The crawl will follow this sequence:

```text
https://www.digitalrealty.com/data-centers
  → region links (.region)
  → metro pages
  → data-center detail links (.a-metro-map-link)
  → detail-page facts
  → ScrapeResult CSV
  → geocoded Property + DLR additional_info
  → transformed CSV
```

`DlrScraper.execute_scrape()` will retain the current region discovery, add a metro-page step that extracts individual detail URLs, and then scrape each detail URL in a new tab. Detail and metro tabs will be closed in `finally` blocks. URLs will be converted to absolute URLs and de-duplicated while preserving discovery order.

The detail scraper will use scoped, label-aware extraction for the page's capabilities rather than relying on positional indexes. It will produce the existing standard fields plus a complete JSON string under `capabilities` so optional labels or new capability facts are not silently discarded. Flat fields provide stable inputs for transformation and future API mapping.

## Scraped field contract

Every value remains a string because `ScrapeResult.property_info` and its CSV boundary are string-based. Optional fields are omitted when the page does not contain them.

| Field | Meaning |
| --- | --- |
| `name` | Detail-page facility name, such as `Charlotte CLT10` |
| `facility_code` | Facility code, such as `CLT10` |
| `description` | Detail-page introductory description |
| `address_input` | Full address shown below the facility identity |
| `facility_brochure_url` | Absolute brochure URL when present |
| `building_structure` | Space capability value, such as `3 stories` |
| `total_building_size` | Complete displayed size, such as `29,000 ft² (2,700 m²)` |
| `square_footage` | Square-foot portion of total building size, isolated for the existing area parser |
| `ups_redundancy` | Power capability value, such as `2N` or `N+2` |
| `cooling_redundancy` | Cooling capability value, such as `N+1` |
| `compliance_certifications` | JSON array of displayed compliance certifications |
| `sustainability_certifications` | JSON array of displayed sustainability certifications |
| `sustainability_energy_label` | Displayed sustainability energy metric label, such as `Renewable Energy %` or `Carbon-Free Energy %` |
| `sustainability_energy_value` | Displayed energy metric value, such as `100%` |
| `security_infrastructure` | JSON array of displayed security/infrastructure features |
| `capabilities` | JSON object containing every extracted capability section, description, label, and value in page order |

The JSON values preserve ordering and are encoded with standard-library `json.dumps`, so they remain valid through CSV serialization. The flat fields are derived from the same capability object and do not replace it.

## Transformation contract

`DlrTransformer` will continue to subclass `GeocodeTransformer` and will:

1. Geocode each `address_input` using the existing injected client.
2. Set the standard `Property.name` from the DLR detail-page name.
3. Parse the isolated `square_footage` field into the existing numeric `Property.square_footage` field.
4. Preserve the remaining DLR-specific fields in a new generic `TransformResult.additional_info` dictionary, using normalized snake-case keys and JSON strings for list/object values.
5. Leave missing optional facts absent from `additional_info`; malformed present area values continue to raise instead of becoming plausible numeric data.

`TransformResult` will gain `additional_info: dict[str, str]` with an empty-dictionary default. `TransformResult.to_csv()` will write the standard property dictionary plus the union of additional-info keys across rows. `TransformResult.from_csv()` will reconstruct standard `Property` fields and place unknown columns back into `additional_info`. Existing non-DLR callers and the existing property CSV contract will continue to work.

The API upload path will continue sending only `TransformResult.property` until the separate API/model change consumes `additional_info` and adds the new wire fields.

## Error handling and pacing

- A missing or malformed individual detail page will be logged and skipped, matching the existing DLR scraper's per-page failure behavior.
- A missing optional capability will not fail the facility record.
- A missing address will remain subject to the existing geocode transform behavior and will be skipped with an error log.
- The existing random inter-page jiggle remains in place; the detail page wait will occur after navigation before querying rendered content.
- No live website, Google Maps, or Housefire API calls will be made by unit tests.

## Tests

Tests will use deterministic fake tabs/elements and mocked geocoding:

- Region/metro traversal extracts absolute, de-duplicated detail URLs.
- A representative detail-page fixture extracts CLT10-like identity, address, brochure URL, capabilities, lists, and both square-foot and metric size values.
- A page with a different sustainability label, such as `Carbon-Free Energy %`, preserves that label/value rather than assuming `Renewable Energy %`.
- DLR transformation sets the property name, geocodes the address, parses square footage, and preserves all additional facts.
- Transformed CSV round-tripping preserves `additional_info` while retaining existing property fields.
- Existing scraper, transformer, factory, and full unit tests remain green.

## Files

- Modify `housefire/scraper/reits_by_ticker/dlr.py` for region → metro → detail traversal and detail-page extraction.
- Modify `housefire/transformer/reits_by_ticker/dlr.py` for DLR-specific normalization.
- Modify `housefire/transformer/transformer.py` for generic transformed-fact preservation and CSV round-tripping.
- Modify `housefire/test/test_scraper.py` with DLR traversal/detail fixtures.
- Modify `housefire/test/test_transformer.py` with DLR normalization and CSV coverage.
- Run `python3 scripts/sync_agents_md.py` after edits and inspect the generated inventory diff.
