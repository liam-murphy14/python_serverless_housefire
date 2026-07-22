# Housefire

Housefire is a Python CLI for collecting property data from REIT websites,
normalizing and geocoding it, and synchronizing the result with the Housefire
API. Scraping uses a visible Chrome/Chromium browser, so live commands need a
working browser, network access, and initialized API credentials.

## Quick start

The recommended development environment uses [Nix](https://nixos.org/) and
`direnv`. The longer, beginner-friendly setup and scraper-development guide is
in [`docs/zero_to_hundred.md`](docs/zero_to_hundred.md).

Clone the repository, enter it, and allow the project environment to load:

```bash
git clone https://github.com/liam-murphy14/python_serverless_housefire.git
cd python_serverless_housefire
direnv allow
```

If you do not use `direnv`, enter the same Nix development shell manually:

```bash
nix develop
```

Initialize the local configuration:

```bash
nix run . -- init
```

This creates `~/.config/housefire/default.ini` and prompts for the temporary
directory, Housefire API key, Google Maps API key, API base URL, deployment
environment, and log directory. Keep this file private. To use another
configuration file, pass the group option before the command:

```bash
nix run . -- --config-path /path/to/housefire.ini init
```

Run `nix run . -- --help` for the complete command help. Supported tickers are
currently `pld`, `spg`, `dlr`, `well`, and `eqix`.

## CLI workflow

Run a small scraper debug path first:

```bash
nix run . -- scrape --debug pld
```

Run a complete scrape and retain its CSV output:

```bash
nix run . -- scrape --save-output pld
```

Transform a scraped CSV and retain the transformed output:

```bash
nix run . -- transform pld /path/to/pld_scraped.csv --save-output
```

Upload a transformed CSV to the Housefire API:

```bash
nix run . -- upload pld /path/to/pld_transformed.csv
```

To run scraping, geocoding, transformation, and upload together:

```bash
nix run . -- run-data-pipeline pld --save-output
```

Commands that contact websites or upload data are integration operations. The
pipeline can update and delete remote properties for the selected ticker when
they are absent from the latest input. Google geocoding may also take time due
to its cache and rate-limit delays, so use debug or saved-output runs while
developing.

## Headless Linux runs

For headless run with

```
xvfb-run -d -s "-screen 0 2560x1600x24" COMMAND
```

For example:

```bash
xvfb-run -d -s "-screen 0 2560x1600x24" nix run . -- scrape --debug pld
```

The Nix development shell provides Chromium and Xvfb on non-Darwin systems.
On macOS, the project expects Google Chrome at its standard application path.

## Contributing

For a new REIT scraper, start with
[`docs/zero_to_hundred.md`](docs/zero_to_hundred.md), then:

1. Add an async scraper in `housefire/scraper/reits_by_ticker/<ticker>.py`,
   including both the full scrape and a representative debug scrape.
2. Register it in `ScraperFactory` and add a matching transformer under
   `housefire/transformer/reits_by_ticker/`.
3. Register the transformer in `TransformerFactory`.
4. Add deterministic fixture-driven tests for parsing and output contracts.
   Tests must not contact live websites, Google Maps, or the production API.
5. Keep selectors and source-specific parsing in the ticker module, and use
   the existing dependency-injection patterns in the factories.

Before opening a change, run the relevant tests and checks:

```bash
python3 -m unittest discover -s housefire/test -p 'test_*.py'
black --check housefire scripts
python3 scripts/sync_agents_md.py
nix flake check
```

Inspect `git diff` and `git status --short` before committing. Do not commit
credentials, local configuration, logs, generated CSVs, browser profiles, or
other generated output. The tracked pre-commit hook keeps the generated
repository inventory in `AGENTS.md` up to date; enable it once per clone with:

```bash
git config core.hooksPath .githooks
```

## Project layout

- `housefire/cli.py` — Click commands and pipeline orchestration
- `housefire/scraper/` — browser-based scrapers and scraper factory
- `housefire/transformer/` — normalization, geocoding, and transformer factory
- `housefire/dependency/` — Housefire API and Google Maps clients
- `housefire/test/` — deterministic unit tests
- `docs/zero_to_hundred.md` — detailed contributor guide for adding scrapers
