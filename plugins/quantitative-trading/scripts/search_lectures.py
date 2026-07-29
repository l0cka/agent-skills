#!/usr/bin/env python3
"""Search a cached QuantEcon lecture-python.myst checkout."""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from pathlib import Path

from quantecon_paths import default_repo_root


SEARCH_SUFFIXES = {".md", ".py", ".yml", ".yaml"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="+", help="Words that must all appear on a line.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=default_repo_root(),
        help="Path to a lecture-python.myst checkout.",
    )
    parser.add_argument("--limit", type=int, default=40, help="Maximum matches to print.")
    parser.add_argument("--case-sensitive", action="store_true")
    return parser.parse_args()


def iter_search_files(repo_root: Path) -> Iterable[Path]:
    lectures_root = repo_root / "lectures"
    if not lectures_root.is_dir():
        raise FileNotFoundError(
            f"Lectures not found: {lectures_root}. "
            "Run scripts/sync_quantecon.sh or pass --repo-root."
        )
    for path in sorted(lectures_root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SEARCH_SUFFIXES:
            yield path


def line_matches(line: str, terms: list[str], case_sensitive: bool) -> bool:
    haystack = line if case_sensitive else line.lower()
    needles = terms if case_sensitive else [term.lower() for term in terms]
    return all(term in haystack for term in needles)


def main() -> None:
    args = parse_args()
    if args.limit < 1:
        raise SystemExit("--limit must be at least 1")
    root = args.repo_root.expanduser().resolve()
    matches = 0
    try:
        paths = iter_search_files(root)
        for path in paths:
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(lines, start=1):
                if not line_matches(line, args.query, args.case_sensitive):
                    continue
                snippet = " ".join(line.strip().split())
                print(f"{path.relative_to(root)}:{line_number}: {snippet}")
                matches += 1
                if matches >= args.limit:
                    return
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
