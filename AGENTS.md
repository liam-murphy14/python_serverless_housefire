# AGENTS.md

This file is the working agreement for agents and developers changing Housefire. It is intentionally repository-specific: when the code and this guide disagree, inspect the code first and then update the guide in the same change.

## Mission and product boundary

Housefire is a personal Python CLI that collects real-estate investment trust (REIT) property data from public websites, normalizes it, enriches incomplete addresses through Google Maps, and synchronizes the result with the Housefire API.

The application is not a general web service. Most of its production behavior depends on:

- `nodriver` launching a visible Chrome/Chromium browser and interacting with live sites;
- external REIT pages retaining roughly the DOM and URLs expected by each scraper;
- valid Housefire and Google Maps credentials in a local config file; and
- network/API rate limits, including a deliberate 72-second Google geocoding delay.

Treat live scraping and uploading as integration operations. Keep unit tests deterministic and do not make tests call real websites or mutate the production API.

## Repository map

<!-- BEGIN AUTO-GENERATED REPOSITORY INVENTORY. Do not edit this block by hand. -->
### Current repository inventory

This inventory is refreshed by `python3 scripts/sync_agents_md.py` and by the repository hook described below.

- Source package: `housefire/`
- Scraper base/factory: `housefire/scraper/scraper.py`, `housefire/scraper/scraper_factory.py`
- Transformer base/factory: `housefire/transformer/transformer.py`, `housefire/transformer/transformer_factory.py`
- API/domain dependencies: `housefire/dependency/`
- CLI and orchestration: `housefire/cli.py`
- Configuration and logging: `housefire/config.py`, `housefire/logger.py`
- Scraper modules present: `dlr`, `eqix`, `pld`, `spg`, `well`
- Transformer modules present: `dlr`, `eqix`, `pld`, `spg`, `well`
- Test modules: `housefire/test/test_client.py`, `housefire/test/test_config.py`, `housefire/test/test_factory.py`, `housefire/test/test_google_maps.py`, `housefire/test/test_housefire_object.py`, `housefire/test/test_logger.py`, `housefire/test/test_scraper.py`, `housefire/test/test_transformer.py`
- Project/build files: `.envrc`, `.git`, `.gitignore`, `README.md`, `default.nix`, `flake.lock`, `flake.nix`, `pyproject.toml`
- Contributor documentation: `docs/zero_to_hundred.md`

<!-- END AUTO-GENERATED REPOSITORY INVENTORY. -->

The important runtime relationships are:

```text
housefire CLI
  ├─ init                  writes ~/.config/housefire/default.ini (or --config-path)
  ├─ scrape                ScraperFactory → nodriver → ScrapeResult CSV
  ├─ transform             TransformerFactory → Property/TransformResult CSV
  ├─ upload                HousefireClient → Housefire API
  └─ run-data-pipeline     scrape → geocode/transform → update API → cleanup
```

### Key modules

- `housefire/cli.py` owns Click commands, config loading, browser setup through factories, temporary directories, and the end-to-end pipeline. Keep network orchestration here rather than in model classes.
- `housefire/config.py` maps the `[HOUSEFIRE]` INI section into `HousefireConfig`. Nix substitutes the Chrome path placeholder in packaged builds.
- `housefire/scraper/scraper.py` defines the async `Scraper` lifecycle and the `ScrapeResult` CSV boundary. Ticker scrapers live in `housefire/scraper/reits_by_ticker/`.
- `housefire/scraper/scraper_factory.py` is the scraper registry and injects the browser, ticker, temporary path, and logger.
- `housefire/transformer/transformer.py` defines normalization, duplicate-address removal, ticker uppercasing, area parsing, and `TransformResult` CSV conversion. Ticker transformers live in `housefire/transformer/reits_by_ticker/`.
- `housefire/transformer/geocode_transformer.py` fills address fields from cached Housefire geocodes or Google Maps. It is used by `spg`, `dlr`, `well`, and `eqix`; `pld` supplies address/geocode fields directly.
- `housefire/transformer/transformer_factory.py` is the transformer registry and injects the logger, ticker, and geocoding client.
- `housefire/dependency/housefire_client/housefire_object.py` contains the `Geocode` and `Property` data models and their API/CSV serialization rules.
- `housefire/dependency/housefire_client/client.py` wraps Housefire REST calls and implements ticker synchronization: existing properties not present in the new scrape are deleted, and new ones are posted.
- `housefire/dependency/google_maps.py` caches geocodes through Housefire before calling Google Maps, then posts newly found geocodes.
- `housefire/logger.py` configures the `housefire` logger, rotating file output, optional development console output, and uncaught-exception logging.

## Toolchain and environment

The declared package name is `housefire`, with a console entry point of `housefire = housefire.cli:main`. Python dependencies are declared in `pyproject.toml` and mirrored in `flake.nix`/`default.nix`.

Preferred setup:

```bash
direnv allow                 # .envrc loads `use flake .`
nix develop                  # enter the flake development shell
```

The flake supplies Python dependencies, Black, and Chromium/Xvfb on non-Darwin systems. macOS uses `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`; Linux uses the flake’s Chromium path. Do not hard-code a new browser path into application code without also considering `default.nix` substitution.

The project declares `requires-python = ">=3.9"`, but the source uses annotations such as `Geocode | None` that require Python 3.10 or newer when evaluated normally. Verify the actual interpreter before changing compatibility claims; either make the code genuinely 3.9-compatible or raise the declared minimum as a deliberate change.

## Configuration and secrets

`housefire` defaults to `$HOME/.config/housefire/default.ini`. Run `housefire init` (or `nix run . -- init`) to create it interactively. `--config-path` can point elsewhere. The required `[HOUSEFIRE]` values are:

- `TEMP_DIR_PATH`: writable location for per-run browser downloads and CSVs;
- `HOUSEFIRE_API_KEY`: API credential sent as `x-api-key`;
- `GOOGLE_MAPS_API_KEY`: Google Maps credential;
- `HOUSEFIRE_BASE_URL`: API base URL, normally ending in `/api/`;
- `DEPLOY_ENV`: `development` enables debug logging and console output; other values use info-level file logging;
- `LOG_DIR_PATH`: writable directory containing `housefire.log`.

Never commit credentials, generated CSVs, logs, browser profiles, or local `.env` files. Use environment-specific test values and temporary directories. Be especially careful with `upload` and `run-data-pipeline`: they make remote API changes and are not safe as casual smoke tests.

## CLI behavior

The Click group exits with a helpful message when the config file is absent or uninitialized, except for `init`:

```bash
nix run . -- init
nix run . -- scrape --debug <ticker>
nix run . -- scrape --save-output <ticker>
nix run . -- transform <ticker> <scraped.csv> --save-output
nix run . -- upload <ticker> <transformed.csv>
nix run . -- run-data-pipeline <ticker> --save-output
```

Ticker names are currently lowercase (`pld`, `spg`, `dlr`, `well`, `eqix`). Factories reject an unsupported ticker; when adding one, update both the scraper and transformer registries and add focused tests. The CLI currently passes ticker strings through to the factories, so do not assume case normalization happens before lookup.

Temporary run directories are created below `TEMP_DIR_PATH` with the ticker, timestamp, and UUID in the name. Scrape and pipeline commands delete them unless `--save-output` is set. The cleanup helper assumes files rather than nested directories, so browser/download changes that introduce subdirectories require a corresponding cleanup change and test.

For headless Linux runs, use the existing project convention:

```bash
xvfb-run -d -s "-screen 0 2560x1600x24" COMMAND
```

## Data contracts

### Scraping

Implement a ticker scraper as an async subclass of `Scraper` in `housefire/scraper/reits_by_ticker/<ticker>.py`:

- `execute_scrape()` performs the complete live scrape and returns `list[ScrapeResult]`;
- `_debug_scrape()` performs a small, representative scrape for manual debugging;
- each `ScrapeResult.property_info` is a dictionary of source-site field names to strings;
- use `self._jiggle()`/`self._wait()` and logging for pacing and diagnostics;
- close extra tabs in `finally` blocks when a scraper opens them;
- keep selectors, URLs, and source-specific parsing inside the ticker module.

`ScrapeResult.to_csv()` unions keys across rows and writes Unix-dialect CSV. Its `from_csv()` returns dictionaries with CSV string values, so conversion belongs in the transformer.

### Transformation

Implement a ticker transformer in `housefire/transformer/reits_by_ticker/<ticker>.py` and return `TransformResult(property=..., scrape_result=...)` values. In the common `Transformer.transform()` wrapper:

- the ticker is uppercased on the `Property`;
- duplicate `address_input` values are dropped, retaining the first result;
- area helpers parse digit-only values, average a simple `a-b` range, and convert acres to square feet using `43,560` square feet per acre;
- malformed/unsupported source values raise rather than silently producing a plausible wrong value.

Use `GeocodeTransformer` when the scraper emits an `address_input` but lacks reliable normalized address/coordinates. It first asks Housefire for an existing geocode, then calls Google Maps and persists a new result. Account for the 5-second cached-result delay and 72-second uncached request delay in manual runs.

`Property.to_dict()` emits API field names (`addressInput`, `squareFootage`, `reitTicker`, etc.) and omits `None`, IDs, and timestamps. `Property.from_dict()` expects `addressInput` and `reitTicker`; numeric fields are converted to floats. Preserve these wire-format names when changing the API boundary.

### Adding a ticker

Use this order:

1. Study the closest existing scraper and transformer, especially its output keys and debug path.
2. Add the scraper module and implement both async methods.
3. Add the scraper import and lowercase ticker entry to `ScraperFactory.scraper_map`.
4. Add the transformer module, choosing `Transformer` or `GeocodeTransformer` based on the source data.
5. Add the transformer import and ticker entry to `TransformerFactory.transformer_map`.
6. Add fixture-driven tests for parsing and output contracts; do not use live websites in the test suite.
7. Update `docs/zero_to_hundred.md` if the contributor workflow changes, then run the AGENTS synchronizer.

## Testing and validation

Run the narrowest relevant checks first, then the full local checks:

```bash
python3 -m unittest discover -s housefire/test -p 'test_*.py'
black --check housefire scripts
nix flake check
```

The committed tests are standard-library `unittest` tests. `test_config.py` validates initialized/missing configuration behavior. `test_logger.py` creates temporary log directories and checks production/development handlers. Tests should clean up temporary resources and reset global logging state when they alter it.

Do not require network access for ordinary validation. Browser/API commands are opt-in integration checks and need credentials, a configured Chrome executable, a display or Xvfb, and awareness that sites/rate limits can make them slow or flaky.

There is currently no configured formatter/linter command in `pyproject.toml`; Black is supplied by the Nix development shell. Keep formatting changes scoped, and do not reformat unrelated legacy files while changing behavior.

## Change guidance and risk areas

- Preserve the dependency injection pattern in the two factories. It makes scraper/transformer behavior testable and keeps browser/API setup out of domain code.
- Avoid importing or instantiating browser, Google Maps, or API clients at module import time.
- Mock `requests`, `googlemaps`, `nodriver`, sleeps, and log destinations in unit tests rather than contacting live services.
- Check URL joining in `HousefireClient._construct_url()` when changing endpoints; the configured base URL and endpoint leading slash are intentionally handled together.
- Treat API synchronization as destructive: `update_properties_by_ticker()` removes remote properties absent from the latest input and rejects empty uploads.
- Keep secrets outside source, and inspect `git diff` before committing generated output or config files.
- Preserve Nix inputs and update `flake.lock` only when dependency/toolchain changes require it.
- If a source-site DOM or URL changes, update the ticker scraper’s debug sample and add a regression fixture for the changed parsing assumption.
- If a behavior or directory changes, update this file’s prose and run `python3 scripts/sync_agents_md.py`; the generated inventory must never be edited manually.

## Self-healing AGENTS.md workflow

The tracked `.githooks/pre-commit` hook runs `scripts/sync_agents_md.py` before each commit. The synchronizer refreshes only the marked inventory block above, so it can add newly discovered scraper/transformer/test/project files without overwriting the hand-maintained guidance. If it changes `AGENTS.md`, the hook stages that file into the same commit.

Enable the tracked hook once per clone:

```bash
git config core.hooksPath .githooks
```

Agents should also run the synchronizer directly after any agent-authored change, especially when working without an enabled Git hook:

```bash
python3 scripts/sync_agents_md.py
git diff -- AGENTS.md
```

The hook is intentionally commit-scoped: Git has no portable hook that observes arbitrary editor writes. It therefore repairs the inventory before a commit and the agent workflow asks for the direct command immediately after edits. If the synchronizer fails, fix the documentation or script error rather than bypassing the hook; use `SKIP_AGENTS_SYNC=1` only for deliberate emergency recovery and explain the follow-up in the commit.

## Definition of done for an agent change

Before handing off a change:

1. Confirm the diff is limited to the requested behavior and its tests/docs.
2. Run the relevant unit tests and formatting check; run `nix flake check` when Nix/build files or packaging are affected.
3. Run `python3 scripts/sync_agents_md.py` and inspect the resulting `AGENTS.md` diff.
4. Check `git status --short` for secrets, logs, CSVs, build output, or unrelated edits.
5. Summarize tests that ran and any live-network/browser checks that were intentionally not run.
