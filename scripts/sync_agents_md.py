#!/usr/bin/env python3
"""Refresh the generated repository inventory embedded in AGENTS.md.

The script deliberately uses only the Python standard library so it can run
before the Nix development environment is available.
"""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
AGENTS_PATH = ROOT / "AGENTS.md"
START_MARKER = "<!-- BEGIN AUTO-GENERATED REPOSITORY INVENTORY. Do not edit this block by hand. -->"
END_MARKER = "<!-- END AUTO-GENERATED REPOSITORY INVENTORY. -->"


def _relative_files(directory: Path, pattern: str) -> list[str]:
    if not directory.exists():
        return []
    return sorted(
        path.relative_to(ROOT).as_posix()
        for path in directory.rglob(pattern)
        if "__pycache__" not in path.parts
    )


def _ticker_modules(directory: Path, suffix: str) -> list[str]:
    if not directory.exists():
        return []
    return sorted(
        path.stem for path in directory.glob(f"*.{suffix}") if path.stem != "__init__"
    )


def _bullet_list(items: list[str], empty: str = "(none)") -> str:
    return ", ".join(f"`{item}`" for item in items) if items else empty


def _project_files() -> list[str]:
    excluded = {"AGENTS.md", ".git"}
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "--cached"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return sorted(
            path.name
            for path in ROOT.iterdir()
            if path.is_file() and path.name not in excluded
        )

    return sorted(
        Path(name).name
        for name in result.stdout.splitlines()
        if len(Path(name).parts) == 1 and Path(name).name not in excluded
    )


def render_inventory() -> str:
    scrapers = _ticker_modules(ROOT / "housefire/scraper/reits_by_ticker", "py")
    transformers = _ticker_modules(ROOT / "housefire/transformer/reits_by_ticker", "py")
    tests = _relative_files(ROOT / "housefire/test", "test_*.py")
    project_files = _project_files()

    return "\n".join(
        [
            START_MARKER,
            "### Current repository inventory",
            "",
            "This inventory is refreshed by `python3 scripts/sync_agents_md.py` and by the repository hook described below.",
            "",
            "- Source package: `housefire/`",
            "- Scraper base/factory: `housefire/scraper/scraper.py`, `housefire/scraper/scraper_factory.py`",
            "- Transformer base/factory: `housefire/transformer/transformer.py`, `housefire/transformer/transformer_factory.py`",
            "- API/domain dependencies: `housefire/dependency/`",
            "- CLI and orchestration: `housefire/cli.py`",
            "- Configuration and logging: `housefire/config.py`, `housefire/logger.py`",
            f"- Scraper modules present: {_bullet_list(scrapers)}",
            f"- Transformer modules present: {_bullet_list(transformers)}",
            f"- Test modules: {_bullet_list(tests)}",
            f"- Project/build files: {_bullet_list(project_files)}",
            "- Contributor documentation: `docs/zero_to_hundred.md`",
            "",
            END_MARKER,
        ]
    )


def _updated_contents() -> tuple[str, str]:
    if not AGENTS_PATH.exists():
        raise SystemExit(f"missing {AGENTS_PATH}")

    current = AGENTS_PATH.read_text(encoding="utf-8")
    start = current.find(START_MARKER)
    end = current.find(END_MARKER)
    if start == -1 or end == -1 or end < start:
        raise SystemExit(
            "AGENTS.md is missing a valid generated inventory block; restore both markers"
        )

    end += len(END_MARKER)
    updated = current[:start] + render_inventory() + current[end:]
    return current, updated


def sync() -> bool:
    current, updated = _updated_contents()
    if updated == current:
        return False

    AGENTS_PATH.write_text(updated, encoding="utf-8")
    return True


def main(argv: list[str]) -> int:
    if argv == ["--check"]:
        current, updated = _updated_contents()
        if updated != current:
            print("AGENTS.md inventory is stale", file=sys.stderr)
            return 1
        return 0
    if argv:
        print(f"usage: {Path(__file__).name} [--check]", file=sys.stderr)
        return 2

    if sync():
        print("Updated AGENTS.md repository inventory")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
