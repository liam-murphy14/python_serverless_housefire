# Python Property Facts Client Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Python Housefire client so `Property` facts can be uploaded through the existing bulk property API and preserved through API and CSV serialization.

**Architecture:** Add an optional `facts` list of JSON-compatible label/value dictionaries to the `Property` dataclass. The existing `HousefireClient.post_properties()` path will carry facts automatically through `Property.to_dict()`. Encode nested list/dictionary values only at the shared CSV boundary and decode the property facts column when reading.

**Tech Stack:** Python 3.9+, dataclasses, standard-library `json`, `requests`, and standard-library `unittest`.

## Global Constraints

- Facts are an ordered JSON array of objects containing string `label` and `value` fields.
- The Python client leaves fact-shape validation to the Svelte API.
- Facts are uploaded through the existing `POST /api/properties` path.
- No facts-specific endpoint or separate upload method is added.
- No delete-and-recreate behavior is added for existing properties whose facts change.
- Missing facts remain backward-compatible and deserialize as `None`.
- API payloads contain native lists/dictionaries; CSV rows contain JSON strings for nested values.
- No scraper, transformer, browser, or live-network changes are included.

---

### Task 1: Add and verify property facts serialization

**Files:**

- Modify: `housefire/dependency/housefire_client/housefire_object.py`
- Test: `housefire/test/test_housefire_object.py`
- Test: `housefire/test/test_client.py`

**Interfaces:**

- Produces `Property.facts: Optional[list[dict[str, str]]]`.
- Produces `Property.to_dict()` output with a native `facts` list when facts are present.
- Produces `Property.from_dict()` support for API lists, JSON-encoded CSV strings, and omitted facts.
- Produces property CSV round-tripping for ordered facts.
- Preserves the existing `HousefireClient.post_properties()` upload interface; its JSON payload gains the `facts` field through `Property.to_dict()`.

- [ ] **Step 1: Write failing object and client tests**

Add these tests to `housefire/test/test_housefire_object.py`:

```python
    def test_property_to_dict_includes_ordered_facts(self):
        facts = [
            {"label": "Year built", "value": "2022"},
            {"label": "Lease term", "value": "15 years"},
        ]
        property_object = Property(
            address_input="1 Main Street",
            reit_ticker="PLD",
            facts=facts,
        )

        self.assertEqual(property_object.to_dict()["facts"], facts)

    def test_property_from_dict_reads_facts_and_defaults_when_omitted(self):
        facts = [{"label": "Year built", "value": "2022"}]

        property_with_facts = Property.from_dict(
            {
                "addressInput": "1 Main Street",
                "reitTicker": "PLD",
                "facts": facts,
            }
        )
        property_without_facts = Property.from_dict(
            {
                "addressInput": "2 Main Street",
                "reitTicker": "PLD",
            }
        )

        self.assertEqual(property_with_facts.facts, facts)
        self.assertIsNone(property_without_facts.facts)

    def test_property_csv_round_trip_preserves_ordered_facts(self):
        facts = [
            {"label": "Year built", "value": "2022"},
            {"label": "Lease term", "value": "15 years"},
        ]
        property_object = Property(
            address_input="1 Main Street",
            reit_ticker="PLD",
            facts=facts,
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "properties.csv"
            Property.to_csv([property_object], path)
            properties = Property.from_csv(path)

        self.assertEqual(properties[0].facts, facts)
```

Add this test to `housefire/test/test_client.py`:

```python
    def test_post_properties_sends_facts_in_json_payload(self):
        property_object = Property(
            address_input="1 Main Street",
            reit_ticker="PLD",
            facts=[{"label": "Year built", "value": "2022"}],
        )
        response = self.get_response(
            201,
            [
                {
                    "addressInput": "1 Main Street",
                    "reitTicker": "PLD",
                    "facts": [{"label": "Year built", "value": "2022"}],
                }
            ],
        )
        with patch.object(self.client, "_post", return_value=response) as post:
            properties = self.client.post_properties([property_object])

        post.assert_called_once_with(
            "/properties",
            [
                {
                    "addressInput": "1 Main Street",
                    "reitTicker": "PLD",
                    "facts": [{"label": "Year built", "value": "2022"}],
                }
            ],
        )
        self.assertEqual(properties[0].facts, [{"label": "Year built", "value": "2022"}])
```

- [ ] **Step 2: Run the focused tests and verify they fail for the missing feature**

Run:

```bash
python3 -m unittest housefire.test.test_housefire_object housefire.test.test_client
```

Expected: the existing tests pass, while the new tests fail because `Property` has no `facts` field and its serializer does not include the new API field. This confirms the tests exercise missing behavior rather than a test-setup error.

- [ ] **Step 3: Add the optional facts field and native API serialization**

In `housefire/dependency/housefire_client/housefire_object.py`:

1. Import `json`.
2. In `SerializableHousefireObject.to_csv()`, convert only list and dictionary values to JSON strings before passing the row to `csv.DictWriter`:

```python
                data_dict = {
                    key: json.dumps(value) if isinstance(value, (list, dict)) else value
                    for key, value in d.to_dict().items()
                }
```

3. Add this dataclass field after `square_footage`:

```python
    facts: Optional[list[dict[str, str]]] = None
```

4. Add `"facts": self.facts` to `Property.to_dict()` before `reitTicker`; the existing `None` filtering must omit facts when absent.
5. In `Property.from_dict()`, parse the facts value before constructing the object:

```python
        facts = data.get("facts")
        if isinstance(facts, str):
            facts = json.loads(facts) if facts else None
```

Pass `facts=facts` to the `Property` constructor.
6. Add `"facts"` to `Property.keys()` before `"reitTicker"`.

Do not change `HousefireClient.post_properties()`: it already maps `Property.to_dict()` values into the JSON payload and maps API responses through `Property.from_dict()`.

- [ ] **Step 4: Run focused tests and verify the implementation passes**

Run:

```bash
python3 -m unittest housefire.test.test_housefire_object housefire.test.test_client
```

Expected: all tests in both modules pass, including native API payload assertions, API response facts, omitted-facts compatibility, and CSV round-tripping.

- [ ] **Step 5: Run repository validation and inspect the change**

Run:

```bash
python3 -m unittest discover -s housefire/test -p 'test_*.py'
black --check housefire scripts
python3 scripts/sync_agents_md.py
git diff --check
git status --short
```

Expected: the full unittest suite passes, Black reports no formatting changes, the synchronizer completes, `git diff --check` reports no whitespace errors, and status contains only the intended source/test/documentation changes plus the pre-existing untracked `pld_from_site.csv`.

- [ ] **Step 6: Commit the implementation**

```bash
git add housefire/dependency/housefire_client/housefire_object.py housefire/test/test_housefire_object.py housefire/test/test_client.py AGENTS.md
git commit -m "feat: support property facts uploads"
```
