# PLD Property Facts Parsing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Parse applicable PLD property/site attributes into each transformed `Property.facts` list.

**Architecture:** Keep the change inside `PldTransformer`. An explicit ordered source-to-label mapping will feed a helper that filters missing values and source placeholders, then passes the resulting list to the existing `Property` model. Existing normalized fields and API/CSV serialization remain unchanged.

**Tech Stack:** Python 3.10+, standard-library `unittest`, existing `Property`, `ScrapeResult`, and transformer classes.

## Global Constraints

- Parse only the approved PLD property/site fields; do not include URLs or broker/leasing-agent contact fields.
- Keep `Available Square Footage` as `Property.square_footage`, not as a duplicate fact.
- Skip missing, blank, case-insensitive `N/A`, and case-insensitive `TBD` values.
- Strip surrounding whitespace from retained fact values.
- Preserve fact order according to the explicit mapping.
- Return `facts=None` when no applicable facts remain.
- Keep tests deterministic; do not call live websites, browsers, Google Maps, or the Housefire API.

---

### Task 1: Add PLD fact parsing with fixture-style unit coverage

**Files:**
- Modify: `housefire/transformer/reits_by_ticker/pld.py:7-67`
- Modify: `housefire/test/test_transformer.py:111-143`

**Interfaces:**
- Consumes: `ScrapeResult.property_info: dict` from the existing PLD transformer path.
- Produces: `Property.facts: list[dict[str, str]] | None` on each `TransformResult` returned by `PldTransformer.execute_transform()`.

- [ ] **Step 1: Add a failing test for ordered property facts**

Add this method to `TestPldTransformer`:

```python
    def test_execute_transform_parses_ordered_property_facts(self):
        transformer = PldTransformer()
        transformer.ticker = "pld"
        result = ScrapeResult(
            {
                "Property Name": "Distribution Center",
                "Street Address 1": "1 Main Street",
                "City": "New York",
                "State": "NY",
                "Postal Code": "10001",
                "Country": "US",
                "Latitude": "40.0",
                "Longitude": "-73.0",
                "Available Date": "01/01/2027",
                "Market Property Type": "Building",
                "Truck Court Depth": "164.0000",
                "Rail Served": "No",
                "Key Feature 1": "30' Clear Height",
                "Key Feature 2": "89 Dock Doors",
                "Unit Name": "Hall A",
                "Unit Office Size": "17,555 SF",
                "# of Grade Level Doors": "12",
                "Warehouse Lighting Type": "LED",
                "Clear Height": "32 FT",
                "Main Breaker Size (AMPS)": "2,000",
                "Fire Suppression System": "ESFR",
                "# of Dock High Doors": "20",
            }
        )

        transformed = transformer.execute_transform([result])

        self.assertEqual(
            transformed[0].property.facts,
            [
                {"label": "Available Date", "value": "01/01/2027"},
                {"label": "Market Property Type", "value": "Building"},
                {"label": "Truck Court Depth", "value": "164.0000"},
                {"label": "Rail Served", "value": "No"},
                {"label": "Key Feature 1", "value": "30' Clear Height"},
                {"label": "Key Feature 2", "value": "89 Dock Doors"},
                {"label": "Unit Name", "value": "Hall A"},
                {"label": "Unit Office Size", "value": "17,555 SF"},
                {"label": "Grade Level Doors", "value": "12"},
                {"label": "Warehouse Lighting Type", "value": "LED"},
                {"label": "Clear Height", "value": "32 FT"},
                {"label": "Main Breaker Size (AMPS)", "value": "2,000"},
                {"label": "Fire Suppression System", "value": "ESFR"},
                {"label": "Dock High Doors", "value": "20"},
            ],
        )
```

- [ ] **Step 2: Run the focused test and verify it fails for the missing behavior**

Run:

```bash
python3 -m unittest housefire.test.test_transformer.TestPldTransformer.test_execute_transform_parses_ordered_property_facts
```

Expected: FAIL because `PldTransformer` currently leaves `Property.facts` as `None`.

- [ ] **Step 3: Add a failing test for filtering placeholders and empty fields**

Add this method to `TestPldTransformer`:

```python
    def test_execute_transform_omits_empty_and_placeholder_facts(self):
        transformer = PldTransformer()
        transformer.ticker = "pld"
        result = ScrapeResult(
            {
                "Latitude": "40.0",
                "Longitude": "-73.0",
                "Available Date": " ",
                "Truck Court Depth": " N/A ",
                "Rail Served": " No ",
                "Key Feature 1": "tBD",
                "Key Feature 2": "  Cross-dock loading  ",
                "Fire Suppression System": "",
            }
        )

        transformed = transformer.execute_transform([result])

        self.assertEqual(
            transformed[0].property.facts,
            [
                {"label": "Rail Served", "value": "No"},
                {"label": "Key Feature 2", "value": "Cross-dock loading"},
            ],
        )
```

- [ ] **Step 4: Run the focused test and verify it fails for the missing filtering behavior**

Run:

```bash
python3 -m unittest housefire.test.test_transformer.TestPldTransformer.test_execute_transform_omits_empty_and_placeholder_facts
```

Expected: FAIL because the transformer does not yet construct or filter facts.

- [ ] **Step 5: Add a failing test for properties with no applicable facts**

Add this method to `TestPldTransformer`:

```python
    def test_execute_transform_uses_none_when_no_property_facts_apply(self):
        transformer = PldTransformer()
        transformer.ticker = "pld"
        result = ScrapeResult({"Latitude": "40.0", "Longitude": "-73.0"})

        transformed = transformer.execute_transform([result])

        self.assertIsNone(transformed[0].property.facts)
```

- [ ] **Step 6: Run all three focused tests and verify the new behavior is absent**

Run:

```bash
python3 -m unittest \
  housefire.test.test_transformer.TestPldTransformer.test_execute_transform_parses_ordered_property_facts \
  housefire.test.test_transformer.TestPldTransformer.test_execute_transform_omits_empty_and_placeholder_facts \
  housefire.test.test_transformer.TestPldTransformer.test_execute_transform_uses_none_when_no_property_facts_apply
```

Expected: all three tests FAIL because no production fact parser exists yet.

- [ ] **Step 7: Implement the minimal ordered PLD fact parser**

In `PldTransformer`, define the ordered mapping and helper:

```python
    facts_field_map = (
        ("Available Date", "Available Date"),
        ("Market Property Type", "Market Property Type"),
        ("Truck Court Depth", "Truck Court Depth"),
        ("Rail Served", "Rail Served"),
        *((f"Key Feature {index}", f"Key Feature {index}") for index in range(1, 7)),
        ("Unit Name", "Unit Name"),
        ("Unit Office Size", "Unit Office Size"),
        ("# of Grade Level Doors", "Grade Level Doors"),
        ("Warehouse Lighting Type", "Warehouse Lighting Type"),
        ("Clear Height", "Clear Height"),
        ("Main Breaker Size (AMPS)", "Main Breaker Size (AMPS)"),
        ("Fire Suppression System", "Fire Suppression System"),
        ("# of Dock High Doors", "Dock High Doors"),
    )

    @classmethod
    def _parse_facts(cls, prop_info: dict) -> list[dict[str, str]] | None:
        facts = []
        for source_field, label in cls.facts_field_map:
            value = prop_info.get(source_field)
            if value is None:
                continue
            value = value.strip()
            if not value or value.upper() in {"N/A", "TBD"}:
                continue
            facts.append({"label": label, "value": value})
        return facts or None
```

Pass `facts=self._parse_facts(prop_info)` into the existing `Property`
constructor. Do not alter area parsing, latitude/longitude conversion,
address construction, or any excluded source-field behavior.

- [ ] **Step 8: Run the focused tests and verify they pass**

Run:

```bash
python3 -m unittest \
  housefire.test.test_transformer.TestPldTransformer.test_execute_transform_maps_fields_and_converts_area \
  housefire.test.test_transformer.TestPldTransformer.test_execute_transform_parses_ordered_property_facts \
  housefire.test.test_transformer.TestPldTransformer.test_execute_transform_omits_empty_and_placeholder_facts \
  housefire.test.test_transformer.TestPldTransformer.test_execute_transform_uses_none_when_no_property_facts_apply
```

Expected: PASS, including the existing PLD mapping test.

- [ ] **Step 9: Commit the implementation and tests**

Run:

```bash
git add housefire/transformer/reits_by_ticker/pld.py housefire/test/test_transformer.py
git commit -m "feat: parse PLD property facts"
```

### Task 2: Run repository-level validation and synchronize agent inventory

**Files:**
- Modify: `AGENTS.md` only if `scripts/sync_agents_md.py` reports an inventory change.

**Interfaces:**
- Consumes: the committed PLD transformer and unit tests from Task 1.
- Produces: verified repository state with no generated artifacts, secrets, or unrelated changes.

- [ ] **Step 1: Run the complete unit test suite**

Run:

```bash
python3 -m unittest discover -s housefire/test -p 'test_*.py'
```

Expected: all tests pass without network or browser access.

- [ ] **Step 2: Run the formatter check**

Run:

```bash
black --check housefire scripts
```

Expected: Black reports that files would be left unchanged.

- [ ] **Step 3: Run the AGENTS synchronizer and inspect its diff**

Run:

```bash
python3 scripts/sync_agents_md.py
git diff -- AGENTS.md
```

Expected: the generated inventory is stable; if the new plan/spec files are not part of the inventory, `AGENTS.md` remains unchanged.

- [ ] **Step 4: Check the final worktree and diff hygiene**

Run:

```bash
git status --short
git diff --check HEAD~1..HEAD
```

Expected: only the intended implementation, tests, and any synchronizer-generated documentation are present; no CSVs, logs, credentials, browser profiles, or build output are added.
