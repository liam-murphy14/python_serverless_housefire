# Ensure REITs CLI Design

**Date:** 2026-08-07

## Goal

Add an idempotent Housefire CLI command that creates a REIT record for every
ticker registered by either the scraper factory or the transformer factory.
The command must leave existing REIT records unchanged and must never delete
REITs.

## Confirmed API contract

The sibling Svelte app's Prisma schema defines `Reit` with a unique `ticker`
field and no required name field. The API accepts a create body containing
only the ticker:

```json
{"ticker": "PLD"}
```

The existing `POST /api/reits` route requires the configured `x-api-key`.
The sibling app currently has no `GET /api/reits` route, so the API will gain
a read-all route to support a reliable existence check. Treating arbitrary
duplicate-create errors as success would hide genuine server failures and
would not reliably distinguish an existing REIT from another API problem.

## Command behavior

The Python CLI will add:

```text
nix run . -- sync-reits
```

The command loads the normal Housefire config, constructs the existing API
client, obtains the union of the lowercase ticker keys in the scraper and
transformer registries, uppercases and sorts them, and fetches existing REITs
from `GET /api/reits`. For each missing ticker it sends one
`POST /api/reits` request with `{"ticker": "TICKER"}`. It reports the
created and already-present tickers and exits successfully when there is
nothing to create.

The command is additive only: it does not delete REITs, modify existing REIT
records, scrape websites, create properties, or invoke Google Maps.

## Python implementation

`housefire/dependency/housefire_client/housefire_object.py` will gain a small
`Reit` data model with `ticker`, optional API metadata, `to_dict()`, and
`from_dict()` methods. The API client will gain `get_reits()` and
`post_reit()` methods following the existing request, response-status, and
serialization conventions.

The two factories will expose their registered ticker keys without requiring
browser startup or transformer execution. The CLI will use those accessors
to form the set union, ensuring a ticker present in only one registry is still
created. Registry keys remain lowercase internally; API payloads and returned
REIT comparisons use uppercase tickers.

## Svelte API implementation

`../svelte_app_housefire/src/routes/api/reits/+server.ts` will export a `GET`
handler that calls the existing `getAllReits()` query and returns the result as
JSON. The existing `POST` handler remains unchanged. A focused route test will
verify that the GET handler returns the query result; the existing API-key hook
continues to protect both methods.

## Error handling

The Python client will raise on unexpected non-success responses using the
same convention as its existing methods. A failed GET or POST stops the
command with an error rather than continuing and presenting a partial success
as complete. The CLI will not catch duplicate errors because the preflight
GET plus unique database constraint should make normal repeated runs
idempotent, while preserving visibility into unexpected server behavior.

## Testing

Python unit tests will cover:

- REIT serialization and deserialization;
- GET and POST request paths, headers, payloads, and response conversion;
- the union of scraper-only, transformer-only, and shared ticker keys;
- creating only missing uppercase tickers; and
- the CLI command's output/flow with the API client mocked.

The sibling app will add a focused GET `/api/reits` route test using the
existing test conventions. Tests will use mocks and fixtures only; no browser,
Google Maps, beta API, or production API calls will be made by the test suite.

## Documentation and validation

The Python README will document the new command and its additive behavior.
The Python repository inventory will be refreshed with
`python3 scripts/sync_agents_md.py`. The sibling app's route inventory will be
updated according to its repository workflow. Validation will include the
relevant Python unit tests, the full Python test suite, Black checks, and the
sibling app's focused test/typecheck commands if available.
