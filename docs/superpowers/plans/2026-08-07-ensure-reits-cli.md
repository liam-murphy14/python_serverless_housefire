# Ensure REITs CLI Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Add an idempotent sync-reits CLI command that creates missing REIT rows for the union of scraper and transformer tickers.

**Architecture:** Add a small Reit API model and GET /reits and POST /reits client methods to the Python package. Expose registry keys from both factories, then let the CLI fetch existing REITs and post only missing uppercase tickers. Add the matching read route to the sibling Svelte API so existence checks are reliable.

**Tech Stack:** Python, standard-library unittest, Click, requests, dataclasses, SvelteKit, TypeScript, Vitest, and Prisma query helpers.

## Global Constraints

- The REIT API payload is exactly {"ticker": "PLD"}; the Prisma Reit.ticker field is unique.
- sync-reits is additive only: it must not delete or modify REITs, properties, or geocodes.
- Tickers are lowercase in Python factory registries and uppercase at the API boundary.
- Tests must not contact browsers, Google Maps, PostgreSQL, beta, or production APIs.
- Preserve existing dependency injection and request-status handling conventions.
- Keep secrets, generated output, logs, and local environment files out of commits.

---

### Task 1: Add the Python REIT model and API client methods

**Files:**

- Modify: housefire/dependency/housefire_client/housefire_object.py
- Modify: housefire/dependency/housefire_client/client.py
- Test: housefire/test/test_housefire_object.py
- Test: housefire/test/test_client.py

**Interfaces:**

- Produce Reit(ticker, id=None, created_at=None, updated_at=None).
- Produce HousefireClient.get_reits() -> list[Reit] using GET /reits.
- Produce HousefireClient.post_reit(reit: Reit) -> Reit using POST /reits.

- [ ] Step 1: Write failing model tests.

Import Reit and datetime, then add to test_housefire_object.py:

~~~python
def test_reit_to_dict_omits_api_metadata(self):
    reit = Reit(
        ticker="PLD",
        id="reit-1",
        created_at=datetime.fromisoformat("2026-01-01T00:00:00"),
    )
    self.assertEqual(reit.to_dict(), {"ticker": "PLD"})

def test_reit_from_dict_reads_api_metadata(self):
    reit = Reit.from_dict(
        {
            "id": "reit-1",
            "createdAt": "2026-01-01T00:00:00",
            "updatedAt": "2026-01-02T00:00:00",
            "ticker": "PLD",
        }
    )
    self.assertEqual(reit.ticker, "PLD")
    self.assertEqual(reit.id, "reit-1")
    self.assertEqual(
        reit.created_at,
        datetime.fromisoformat("2026-01-01T00:00:00"),
    )
~~~

- [ ] Step 2: Run the model tests and verify the expected failure.

Run:

~~~bash
python3 -m unittest housefire.test.test_housefire_object
~~~

Expected: test collection fails because Reit is not defined.

- [ ] Step 3: Implement the minimal Reit model.

Add a dataclass in housefire_object.py with a required ticker, optional id/created_at/updated_at fields, to_dict returning {"ticker": self.ticker}, and from_dict parsing id, createdAt, updatedAt, and ticker with the same datetime convention as Geocode and Property.

- [ ] Step 4: Run the model tests and verify they pass.

~~~bash
python3 -m unittest housefire.test.test_housefire_object
~~~

Expected: PASS.

- [ ] Step 5: Write failing client tests.

Import Reit in test_client.py and add:

~~~python
def test_get_reits_returns_objects(self):
    response = self.get_response(200, [{"ticker": "PLD"}, {"ticker": "DLR"}])
    with patch.object(self.client, "_get", return_value=response) as get:
        reits = self.client.get_reits()
    get.assert_called_once_with("/reits")
    self.assertEqual([reit.ticker for reit in reits], ["PLD", "DLR"])

def test_post_reit_sends_ticker_and_returns_object(self):
    reit = Reit(ticker="PLD")
    response = self.get_response(200, {"id": "reit-1", "ticker": "PLD"})
    with patch.object(self.client, "_post", return_value=response) as post:
        result = self.client.post_reit(reit)
    post.assert_called_once_with("/reits", {"ticker": "PLD"})
    self.assertEqual(result.ticker, "PLD")
~~~

- [ ] Step 6: Run the client tests and verify the expected failure.

~~~bash
python3 -m unittest housefire.test.test_client
~~~

Expected: FAIL because get_reits and post_reit do not exist.

- [ ] Step 7: Implement the client methods.

Import Reit and add get_reits beside the existing resource methods. It must call _get("/reits"), raise on any error response, and convert every response JSON object with Reit.from_dict. Add post_reit, which calls _post("/reits", reit.to_dict()), raises ValueError for status 400, raises Exception for other error statuses, and converts the response with Reit.from_dict.

- [ ] Step 8: Run the client tests.

~~~bash
python3 -m unittest housefire.test.test_client
~~~

Expected: PASS.

- [ ] Step 9: Commit the Python API contract.

~~~bash
git add housefire/dependency/housefire_client/housefire_object.py housefire/dependency/housefire_client/client.py housefire/test/test_housefire_object.py housefire/test/test_client.py
git commit -m "feat: add REIT API client support"
~~~

---

### Task 2: Expose ticker registries without runtime setup

**Files:**

- Modify: housefire/scraper/scraper_factory.py
- Modify: housefire/transformer/transformer_factory.py
- Test: housefire/test/test_factory.py

**Interfaces:**

- Produce ScraperFactory.supported_tickers() -> set[str].
- Produce TransformerFactory.supported_tickers() -> set[str].

- [ ] Step 1: Write failing registry tests.

Add to test_factory.py:

~~~python
def test_supported_tickers_returns_scraper_registry_keys(self):
    self.assertEqual(
        ScraperFactory.supported_tickers(),
        {"pld", "spg", "dlr", "well", "eqix"},
    )

def test_supported_tickers_returns_transformer_registry_keys(self):
    self.assertEqual(
        TransformerFactory.supported_tickers(),
        {"pld", "spg", "dlr", "well", "eqix"},
    )
~~~

- [ ] Step 2: Run the factory tests and verify the expected failure.

~~~bash
python3 -m unittest housefire.test.test_factory
~~~

Expected: FAIL because the class methods do not exist.

- [ ] Step 3: Implement the accessors.

Move each factory's current map to a class attribute so it remains available to existing instance methods. Add a classmethod to each factory returning set(cls.scraper_map) or set(cls.transformer_map). Do not initialize a browser, instantiate a transformer, or change any existing factory error behavior.

- [ ] Step 4: Run the factory tests.

~~~bash
python3 -m unittest housefire.test.test_factory
~~~

Expected: PASS.

- [ ] Step 5: Commit the registry accessors.

~~~bash
git add housefire/scraper/scraper_factory.py housefire/transformer/transformer_factory.py housefire/test/test_factory.py
git commit -m "refactor: expose registered REIT tickers"
~~~

---

### Task 3: Add the sibling Svelte GET /api/reits route

**Files:**

- Modify: ../svelte_app_housefire/src/routes/api/reits/+server.ts
- Create: ../svelte_app_housefire/src/routes/api/reits/reits.test.ts
- Modify: ../svelte_app_housefire/AGENTS.md

**Interfaces:**

- Produce GET /api/reits returning the array from getAllReits() as JSON.
- Preserve the existing POST /api/reits handler and API-key protection.

- [ ] Step 1: Write the failing route test.

Create reits.test.ts using the sibling app's Vitest convention:

~~~typescript
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { getAllReits, createReit } = vi.hoisted(() => ({
  getAllReits: vi.fn(),
  createReit: vi.fn(),
}));

vi.mock('$lib/server/db/reitQueries', () => ({
  getAllReits,
  createReit,
}));

import { GET } from './+server';

describe('GET /api/reits', () => {
  beforeEach(() => getAllReits.mockReset());

  it('returns all REIT records from the query helper', async () => {
    const reits = [{ id: 'reit-1', ticker: 'PLD' }];
    getAllReits.mockResolvedValue(reits);

    const response = await GET({} as Parameters<typeof GET>[0]);

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(reits);
  });
});
~~~

- [ ] Step 2: Run the focused route test and verify the expected failure.

From ../svelte_app_housefire run:

~~~bash
npm run test:unit -- src/routes/api/reits/reits.test.ts
~~~

Expected: FAIL because GET is not exported from +server.ts.

- [ ] Step 3: Implement the GET handler.

Import getAllReits beside createReit. Add a RequestHandler that returns json(await getAllReits()) and catches unexpected errors by logging and calling error(500, { message: "Something went wrong" }), matching the existing POST route convention.

- [ ] Step 4: Run the focused test and type check.

~~~bash
npm run test:unit -- src/routes/api/reits/reits.test.ts
npm run check
~~~

Expected: the focused test passes and svelte-check reports no errors or warnings.

- [ ] Step 5: Update the sibling route inventory and commit.

Add a GET /api/reits row to the API route table in ../svelte_app_housefire/AGENTS.md with behavior "Return all REIT records." Then run:

~~~bash
git -C ../svelte_app_housefire diff --check
git -C ../svelte_app_housefire add src/routes/api/reits/+server.ts src/routes/api/reits/reits.test.ts AGENTS.md
git -C ../svelte_app_housefire commit -m "feat: expose REIT listing API"
~~~

---

### Task 4: Add the sync-reits CLI command

**Files:**

- Modify: housefire/cli.py
- Create: housefire/test/test_cli.py
- Modify: README.md

**Interfaces:**

- Produce _get_supported_tickers() -> list[str] with uppercase sorted union semantics.
- Produce sync_reits_main(config: HousefireConfig) -> tuple[list[str], list[str]], returning existing and created ticker lists.
- Add the Click command sync-reits.

- [ ] Step 1: Write failing helper and command-flow tests.

Create test_cli.py:

~~~python
import unittest
from unittest.mock import Mock, patch

from housefire.cli import _get_supported_tickers, sync_reits_main
from housefire.dependency.housefire_client.housefire_object import Reit


class TestReitSync(unittest.TestCase):
    @patch(
        "housefire.cli.TransformerFactory.supported_tickers",
        return_value={"pld", "eqix"},
    )
    @patch(
        "housefire.cli.ScraperFactory.supported_tickers",
        return_value={"pld", "spg"},
    )
    def test_get_supported_tickers_returns_sorted_uppercase_union(
        self, scraper, transformer
    ):
        self.assertEqual(_get_supported_tickers(), ["EQIX", "PLD", "SPG"])

    @patch("housefire.cli.HousefireClient")
    @patch(
        "housefire.cli._get_supported_tickers",
        return_value=["EQIX", "PLD", "SPG"],
    )
    def test_sync_reits_creates_only_missing_tickers(
        self, supported, client_class
    ):
        client = client_class.return_value
        client.get_reits.return_value = [Reit(ticker="PLD")]
        client.post_reit.side_effect = lambda reit: reit

        existing, created = sync_reits_main(Mock())

        self.assertEqual(existing, ["PLD"])
        self.assertEqual(created, ["EQIX", "SPG"])
        client.post_reit.assert_any_call(Reit(ticker="EQIX"))
        client.post_reit.assert_any_call(Reit(ticker="SPG"))
        self.assertEqual(client.post_reit.call_count, 2)
~~~

- [ ] Step 2: Run the new CLI tests and verify the expected failure.

~~~bash
python3 -m unittest housefire.test.test_cli
~~~

Expected: test collection fails because the helper functions do not yet exist.

- [ ] Step 3: Implement the helper, sync function, and command.

Import Reit. Add:

~~~python
def _get_supported_tickers() -> list[str]:
    ticker_set = (
        ScraperFactory.supported_tickers()
        | TransformerFactory.supported_tickers()
    )
    return sorted(ticker.upper() for ticker in ticker_set)


def sync_reits_main(config: HousefireConfig) -> tuple[list[str], list[str]]:
    housefire_api = HousefireClient(
        config.housefire_api_key,
        config.housefire_base_url,
    )
    supported_tickers = _get_supported_tickers()
    existing_tickers = sorted(
        reit.ticker.upper() for reit in housefire_api.get_reits()
    )
    existing_ticker_set = set(existing_tickers)
    created_tickers = []
    for ticker in supported_tickers:
        if ticker in existing_ticker_set:
            continue
        housefire_api.post_reit(Reit(ticker=ticker))
        created_tickers.append(ticker)
    return existing_tickers, created_tickers
~~~

Add the Click command after init:

~~~python
@housefire.command(name="sync-reits")
@click.pass_context
def sync_reits(ctx):
    """Create missing REIT records for registered scraper/transformer tickers."""
    existing_tickers, created_tickers = sync_reits_main(ctx.obj["CONFIG"])
    for ticker in created_tickers:
        click.echo(f"Created REIT {ticker}.")
    click.echo(
        f"REIT sync complete: created {len(created_tickers)}, "
        f"already present {len(existing_tickers)}."
    )
~~~

- [ ] Step 4: Run the CLI tests.

~~~bash
python3 -m unittest housefire.test.test_cli
~~~

Expected: PASS.

- [ ] Step 5: Document the command.

Add this usage to README.md:

~~~text
Ensure REIT rows exist for every registered scraper or transformer:

nix run . -- sync-reits
~~~

State that the command only creates missing REIT rows and never deletes or modifies existing records.

- [ ] Step 6: Run the Python unit suite and formatting check.

~~~bash
python3 -m unittest discover -s housefire/test -p 'test_*.py'
black --check housefire scripts
~~~

Expected: all unit tests pass and Black reports no formatting changes.

- [ ] Step 7: Refresh the Python inventory and inspect the diff.

~~~bash
python3 scripts/sync_agents_md.py
git diff --check
git status --short
~~~

Confirm the inventory includes housefire/test/test_cli.py and no credentials, logs, CSVs, or build output appear.

- [ ] Step 8: Commit the Python CLI change.

~~~bash
git add housefire/cli.py housefire/test/test_cli.py README.md AGENTS.md
git commit -m "feat: sync registered REIT records"
~~~

---

### Task 5: Final cross-repository verification

**Files:**

- No new files.

- [ ] Step 1: Run the Python focused checks.

~~~bash
python3 -m unittest housefire.test.test_client housefire.test.test_factory housefire.test.test_cli
~~~

- [ ] Step 2: Run sibling focused tests and checks.

From ../svelte_app_housefire run:

~~~bash
npm run test:unit -- src/routes/api/reits/reits.test.ts
npm run check
npm run lint
~~~

- [ ] Step 3: Review both repository statuses.

~~~bash
git status --short
git -C ../svelte_app_housefire status --short
~~~

Confirm only intended commits/files are present. Do not run sync-reits against beta or production as automated verification.

