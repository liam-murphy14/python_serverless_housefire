# Python Property Facts Upload Design

**Status:** Approved for implementation on 2026-07-31

## Goal

Extend the Python Housefire client so property records can upload and preserve
the unstructured property facts accepted by the Svelte Housefire API.

## Scope

- Add an optional ordered `facts` collection to the Python `Property` model.
- Include facts in the existing `post_properties()` payload without adding a
  new API endpoint or client upload path.
- Read facts returned by the API into `Property` objects.
- Preserve facts through the existing property CSV boundary.
- Keep existing properties without facts and existing scalar CSV behavior
  backward compatible.

The Svelte API currently accepts facts through `POST /api/properties` as part
of each property object. Its fact contract is an ordered JSON array of strict
objects containing non-empty string `label` and `value` fields. The Python
client will use a JSON-compatible `list[dict[str, str]]` representation and
will leave shape validation to the API, which remains the source of truth.

## Non-goals

- No facts-specific endpoint or separate upload method.
- No client-side validation or coercion that could diverge from the API.
- No delete-and-recreate behavior for existing properties whose facts change;
  the current API has no update endpoint.
- No changes to scrapers or transformers in this client-model change.

## Design

### Property model and API flow

Add `facts: Optional[list[dict[str, str]]] = None` to the `Property` dataclass.
`Property.to_dict()` includes `facts` when it is not `None`, keeping the value
as a native list of dictionaries. Because `HousefireClient.post_properties()`
already serializes each `Property` with `to_dict()`, it will upload facts on
new property records using the existing bulk endpoint.

`Property.from_dict()` reads an API `facts` list when present and uses `None`
when older responses omit it. The `facts` field is included in `Property.keys()`
so it participates in declared CSV columns.

### CSV boundary

API dictionaries and CSV rows have different representations: facts must be a
native JSON list in an HTTP payload but are strings in CSV. Update the shared
`SerializableHousefireObject.to_csv()` implementation to JSON-encode list and
dictionary values before writing them. Update `Property.from_dict()` to parse a
string `facts` value as JSON when loading CSV, while accepting an already
decoded list from the API. Empty CSV fields remain backward-compatible and map
to `None`.

### Error handling

The client will not silently repair malformed fact mappings. The Svelte API
continues to validate the shape and returns HTTP 400 for invalid facts;
`post_properties()` continues to expose that response as `ValueError`. Other
HTTP failures retain the client’s existing exception behavior.

## Testing

Add focused unit coverage for:

- including facts in `Property.to_dict()` and the `post_properties()` JSON
  payload;
- reading facts from an API response and defaulting omitted facts to `None`;
- preserving fact order and values through property CSV write/read; and
- JSON-encoding nested values without changing existing scalar serialization.

Run the focused unittest modules, the full standard-library unittest suite,
Black’s check, the AGENTS synchronizer, and inspect the final status/diff.
No live Housefire API, browser, or network integration checks are required.
