# Task 1 Report: Add failing DLR scraper fixture tests

## Status

DONE_WITH_CONCERNS. The requested test-only task is complete. The tests intentionally remain RED until the later DLR scraper implementation task.

## Files changed

- `housefire/test/test_scraper.py`
  - Added deterministic `FakeElement`, `FakeTab`, and `FakeDriver` browser doubles.
  - Added three `TestDlrScraper` tests covering detail URL normalization/deduplication, the CH1 detail-page field contract, and detail-tab lifecycle.
- `.superpowers/sdd/2026-08-07-dlr-property-facts/task-1-report.md`
  - This report.

No production code was changed. `python3 scripts/sync_agents_md.py` completed successfully and produced no `AGENTS.md` diff.

## Commits

- `29914e6 test: add failing DLR detail scraper fixtures`
- The report is committed separately after the test commit.

## TDD RED evidence

The focused tests were run independently before any production implementation:

```text
python3 -m unittest housefire.test.test_scraper.TestDlrScraper.test_detail_urls_are_absolute_and_deduplicated_in_discovery_order
E ... AttributeError: 'DlrScraper' object has no attribute '_digital_realty_scrape_detail_urls'
Ran 1 test ... FAILED (errors=1)

python3 -m unittest housefire.test.test_scraper.TestDlrScraper.test_detail_page_extracts_identity_capabilities_and_repeated_sections
E ... AttributeError: 'DlrScraper' object has no attribute '_digital_realty_scrape_single_detail'
Ran 1 test ... FAILED (errors=1)

python3 -m unittest housefire.test.test_scraper.TestDlrScraper.test_execute_scrape_visits_detail_tabs_and_closes_tabs
F ... AssertionError: 0 != 1
Ran 1 test ... FAILED (failures=1)
```

The full suite confirms the expected state: `Ran 67 tests ... FAILED (failures=1, errors=2)`, with failures limited to the three new DLR tests.

## Test commands and output

- `python3 -m unittest housefire.test.test_scraper.TestScraper` — PASS, 4 tests.
- `python3 -m unittest discover -s housefire/test -p 'test_*.py'` — expected RED: 67 tests, 1 failure and 2 errors, all in `TestDlrScraper`.
- `git diff --check` — PASS.
- `black --target-version py314 --check housefire/test/test_scraper.py` — PASS.
- `python3 scripts/sync_agents_md.py` — PASS; no inventory change.

## Self-review

- The expected values are hand-written from the task brief; the scraper is not used to compute assertions.
- Fakes expose only the async selector and tab-close methods needed by the fixture contract.
- Tests do not launch a browser, access the network, or mutate the API.
- The change is limited to test fixtures and assertions; no transformer or `Property` behavior was added.
- `git diff --check` passed, and the changed test file passes Black with the environment’s Python 3.14 target.

## Concerns

- The required RED state means the full test suite is not green by design; later implementation work must make these three tests pass.
- Plain `black --check housefire/test/test_scraper.py` reported a Python 3.14/3.15 target-version parsing mismatch in the installed Black environment. The equivalent explicit `--target-version py314` check passed for the changed file.
- `black --target-version py314 --check housefire scripts` still reports a pre-existing formatting issue in `scripts/sync_agents_md.py`; that unrelated file was not changed.
