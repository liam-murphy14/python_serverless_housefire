# Inventory stability fix report

## Summary

Commit `9d06bdb` updates `scripts/sync_agents_md.py` so the project/build-file inventory uses Git index entries (`git ls-files --cached`) and therefore ignores untracked root-level user data. If Git metadata is unavailable, it falls back to enumerating root-level files. Both paths always exclude `.git` and `AGENTS.md`.

## TDD evidence

Red command:

```text
python3 -m unittest housefire.test.test_sync_agents_md
```

Result: failed as expected. The current implementation rendered ``README.md`, `pld_from_site.csv``; the regression asserted that the untracked CSV must be absent.

Green command:

```text
python3 -m unittest housefire.test.test_sync_agents_md
```

Result: passed (`Ran 1 test ... OK`) after the production change.

The regression uses a temporary Git repository with staged `README.md` and untracked `pld_from_site.csv`, exercising `render_inventory()` against that real repository state.

## Final validation

```text
python3 -m unittest discover -s housefire/test -p 'test_*.py'
```

Passed: 61 tests, 0 failures.

```text
black --check housefire scripts
```

Passed: 39 files unchanged. An initial run correctly identified formatting needed in the new test; Black formatted it, and the final check passed.

```text
python3 scripts/sync_agents_md.py --check
```

Passed: exit code 0.

```text
git diff --check
```

Passed: exit code 0.

## Files

Committed in `9d06bdb`:

- `scripts/sync_agents_md.py` — tracked/staged Git inventory with non-Git fallback and exclusions.
- `housefire/test/test_sync_agents_md.py` — temporary-Git regression test.
- `AGENTS.md` — regenerated inventory including the staged regression test and excluding untracked CSV data.

This fix does not modify the property-facts implementation and does not touch or delete `pld_from_site.csv` in the main checkout.

## Concerns

- Git discovery depends on the `git` executable and the repository index; command failure intentionally selects the archive/non-Git fallback.
- The linked worktree required elevated permission for Git index staging/commit because its index is stored under the main checkout’s `.git/worktrees` directory.
- No live browser, website, Housefire API, or Google Maps integration checks were run; they are outside this deterministic inventory change.
