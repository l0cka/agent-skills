#!/usr/bin/env python3
"""List chapters from a cached QuantEcon lecture-python.myst checkout."""

from __future__ import annotations

import argparse
from pathlib import Path

from quantecon_paths import default_repo_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=default_repo_root(),
        help="Path to a lecture-python.myst checkout.",
    )
    return parser.parse_args()


def list_lectures(toc_path: Path) -> list[tuple[str, str]]:
    lectures: list[tuple[str, str]] = []
    current_part = "Uncategorized"
    for raw_line in toc_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("- caption:"):
            current_part = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- file:"):
            slug = stripped.split(":", 1)[1].strip()
            if slug:
                lectures.append((current_part, slug))
    return lectures


def main() -> None:
    args = parse_args()
    toc_path = args.repo_root / "lectures" / "_toc.yml"
    if not toc_path.is_file():
        raise SystemExit(
            f"TOC not found: {toc_path}\n"
            "Run scripts/sync_quantecon.sh or pass --repo-root."
        )

    previous: str | None = None
    for part, slug in list_lectures(toc_path):
        if part != previous:
            if previous is not None:
                print()
            print(part)
            previous = part
        print(f"  {slug}")


if __name__ == "__main__":
    main()
