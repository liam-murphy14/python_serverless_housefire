# DLR Property Facts Scraping Design

**Status:** Approved for implementation on 2026-08-07

## Goal

Extend the Digital Realty (DLR) pipeline so it follows the existing region and
metro navigation to each data-center detail page, scrapes property-specific
facts from the rendered web page, and uploads those facts through the current
`Property.facts` API contract.

## Scope

The scraper will capture detail-page content that belongs to the individual
data center:

- facility identity and code;
- the detail-page description;
- the displayed address;
- the facility brochure URL;
- building structure and total building size;
- UPS and cooling redundancy;
- compliance certifications;
- sustainability certifications and the displayed sustainability energy
  metric, regardless of its label; and
- security and infrastructure features.

The standard `name`, `address_input`, and `square_footage` fields remain
separate from facts. All other retained detail-page fields become ordered
`Property.facts` entries with `{label, value}` string mappings. Global
navigation, footer content, generic calls to action, sales contacts, and
unrelated resource cards are excluded.

## Architecture and data flow

The crawl follows this sequence:

```text
https://www.digitalrealty.com/data-centers
  → region links (.region)
  → metro pages
  → data-center detail links (.a-metro-map-link)
  → detail-page fields and capability sections
  → ScrapeResult CSV
  → geocoded Property + ordered facts
  → transformed CSV or Housefire API upload
```

`DlrScraper.execute_scrape()` retains the current region discovery, adds a
metro-page step that extracts individual detail URLs, and opens each detail
URL in a new tab. URLs are converted to absolute URLs and de-duplicated while
preserving discovery order. Region and detail tabs are closed in `finally`
blocks. The existing randomized inter-page delay remains in place, and the
detail page is allowed to render before its elements are queried.

The detail scraper uses scoped, label-aware extraction. Known identity and
link selectors provide the standard fields; the capability area is parsed by
section and label rather than by positional indexes. Repeated certification
and security items are retained in page order. The scraper emits JSON strings
for repeated values at the `ScrapeResult` CSV boundary so every source value
remains a string.

## Scraped field contract

Optional fields are omitted when the page does not contain them. The values
below are the source-side names used in `ScrapeResult.property_info`:

| Field | Meaning |
| --- | --- |
| `name` | Detail-page facility name |
| `facility_code` | Facility code, such as `CH1` or `HKG11` |
| `description` | Detail-page introductory description |
| `address_input` | Full address shown below the facility identity |
| `facility_brochure_url` | Absolute brochure URL when present |
| `building_structure` | Space capability value, such as `1 Story` |
| `total_building_size` | Complete displayed size, including square feet and metric units |
| `square_footage` | Square-foot portion of total building size for area parsing |
| `ups_redundancy` | Power capability value, such as `N+2` |
| `cooling_redundancy` | Cooling capability value, such as `N+1` |
| `compliance_certifications` | JSON array of displayed compliance certifications |
| `sustainability_certifications` | JSON array of displayed sustainability certifications |
| `sustainability_energy_label` | Displayed sustainability energy metric label |
| `sustainability_energy_value` | Displayed sustainability energy metric value |
| `security_infrastructure` | JSON array of displayed security/infrastructure features |

The scraper may also retain the complete ordered capability section as a JSON
object when the page exposes labels that are not in the known flat fields. The
transformer converts those entries to facts so optional page content is not
silently discarded.

## Fact and transformation contract

`DlrTransformer` continues to subclass `GeocodeTransformer` and will:

1. geocode each `address_input` using the existing injected client;
2. set `Property.name` from the detail-page name;
3. parse the isolated `square_footage` field into
   `Property.square_footage`;
4. convert the remaining DLR detail fields into ordered
   `Property.facts` entries; and
5. omit missing, blank, and placeholder optional values without failing the
   property record.

The fact order is the page-oriented order: facility code, description,
brochure, building structure, total building size, UPS redundancy, cooling
redundancy, compliance certifications, sustainability certifications, the
dynamic sustainability energy label/value, and security/infrastructure
features. Repeated list values use the same human-readable label for each
entry. The sustainability metric keeps its source label, allowing both
`Renewable Energy %` and `Carbon-Free Energy %`.

Malformed present area values continue to raise through the existing area
parser rather than becoming plausible numeric data. Missing addresses retain
the existing geocode-transform behavior and are logged/skipped.

## Error handling

- A missing or malformed individual detail page is logged and skipped.
- A missing optional capability does not fail the facility record.
- Absolute URL construction handles both relative and absolute links.
- Detail and metro tabs close even when extraction raises.
- Unit tests do not contact Digital Realty, Google Maps, or the Housefire API.

## Testing

Add deterministic fake-tab and fake-element tests that verify:

- region/metro traversal extracts absolute, de-duplicated detail URLs;
- a representative detail-page fixture extracts identity, address, brochure,
  capability values, lists, and both square-foot and metric size values;
- a page with a different sustainability label preserves that label and
  value;
- DLR transformation geocodes the address, sets the name, parses square
  footage, and preserves all page-specific values as ordered facts; and
- existing scraper, transformer, factory, and full unit tests remain green.

No live browser, Google Maps, or Housefire API call is part of ordinary test
execution.

## Files

- Modify `housefire/scraper/reits_by_ticker/dlr.py` for region → metro → detail
  traversal and detail-page extraction.
- Modify `housefire/transformer/reits_by_ticker/dlr.py` for DLR fact mapping.
- Modify `housefire/test/test_scraper.py` with deterministic DLR traversal and
  detail-page fixtures.
- Modify `housefire/test/test_transformer.py` with DLR fact normalization.
- Run `python3 scripts/sync_agents_md.py` after edits and inspect the generated
  inventory diff.
