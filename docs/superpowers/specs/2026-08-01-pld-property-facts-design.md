# PLD Property Facts Design

## Goal

Extend the PLD transformer so each transformed `Property` carries applicable
property/site facts from the PLD CSV in the existing ordered
`[{"label": ..., "value": ...}]` format.

## Scope

The transformer will parse only these PLD source fields:

- `Available Date`
- `Market Property Type`
- `Truck Court Depth`
- `Rail Served`
- `Key Feature 1` through `Key Feature 6`
- `Unit Name`
- `Unit Office Size`
- `# of Grade Level Doors`
- `Warehouse Lighting Type`
- `Clear Height`
- `Main Breaker Size (AMPS)`
- `Fire Suppression System`
- `# of Dock High Doors`

`Available Square Footage` remains the normalized `Property.square_footage`
field. URLs and broker/leasing-agent contact fields remain excluded from
facts.

## Design

`PldTransformer` will define an explicit, ordered facts field mapping and use a
small `_parse_facts()` helper. The helper will:

1. Read each allowlisted source field in the mapping order.
2. Skip missing or whitespace-only values.
3. Strip surrounding whitespace from retained values.
4. Skip case-insensitive `N/A` and `TBD` source placeholders.
5. Return facts as dictionaries with string `label` and `value` keys.
6. Return `None` when no applicable facts remain.

The resulting facts list will be passed to `Property(facts=...)`. Existing
field mappings, address construction, area parsing, and ticker behavior remain
unchanged.

## Data flow

```text
PLD ScrapeResult.property_info
  ├─ standard fields → Property scalar fields
  ├─ Available Square Footage → Property.square_footage
  └─ allowlisted site fields → Property.facts
```

Fact labels will use the source field names, except the two door-count labels
will omit the leading `# of` and use `Grade Level Doors` and `Dock High
Doors`. This keeps labels readable while preserving the source meaning.

## Testing

Add deterministic unit tests for `PldTransformer` that verify:

- representative property/site fields become ordered facts;
- blank, `N/A`, and `TBD` values are omitted while meaningful values remain;
- a property with no applicable fact fields has `facts is None`; and
- existing standard PLD field parsing remains intact.

No live scraper, browser, Google Maps, or Housefire API calls are required.
