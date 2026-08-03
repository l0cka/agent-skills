#!/usr/bin/env python3
"""Run bounded, offline preflight checks for a release candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


VERSION_LINE = re.compile(r"^\s*version\s*=\s*['\"]([^'\"]+)['\"]\s*(?:#.*)?$")


def run_git(root: Path, *args: str) -> tuple[int, str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result.returncode, result.stdout.strip()


def toml_version(path: Path, sections: set[str]) -> str | None:
    current = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            continue
        if current in sections:
            match = VERSION_LINE.match(raw)
            if match:
                return match.group(1)
    return None


def json_version(path: Path) -> str | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    version = value.get("version") if isinstance(value, dict) else None
    return version if isinstance(version, str) and version else None


def discover_versions(root: Path) -> list[dict[str, str]]:
    candidates: list[tuple[Path, str, Any]] = [
        (
            root / "pyproject.toml",
            "python",
            lambda path: toml_version(path, {"project", "tool.poetry"}),
        ),
        (root / "package.json", "node", json_version),
        (
            root / "Cargo.toml",
            "rust",
            lambda path: toml_version(path, {"package"}),
        ),
        (root / ".codex-plugin" / "plugin.json", "codex-plugin", json_version),
        (root / ".claude-plugin" / "plugin.json", "claude-plugin", json_version),
    ]
    found = []
    for path, kind, reader in candidates:
        if not path.is_file():
            continue
        version = reader(path)
        if version:
            found.append(
                {
                    "kind": kind,
                    "path": str(path.relative_to(root)),
                    "version": version,
                }
            )
    return found


def inspect(root: Path, expected_version: str | None) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    versions = discover_versions(root)

    git_code, git_root = run_git(root, "rev-parse", "--show-toplevel")
    is_git = git_code == 0
    commit = None
    branch = None
    changes: list[str] = []
    remotes: list[str] = []
    colliding_tags: list[str] = []

    if not is_git:
        blockers.append(
            {"code": "not_git_repository", "message": "Release root is not in a Git repository."}
        )
    else:
        _, commit = run_git(root, "rev-parse", "HEAD")
        _, branch = run_git(root, "branch", "--show-current")
        _, status = run_git(root, "status", "--porcelain=v1", "--untracked-files=all")
        changes = [line for line in status.splitlines() if line]
        if changes:
            blockers.append(
                {
                    "code": "dirty_worktree",
                    "message": f"Working tree has {len(changes)} changed or untracked path(s).",
                }
            )
        if not branch:
            warnings.append(
                {
                    "code": "detached_head",
                    "message": "HEAD is detached; confirm that the release contract permits this context.",
                }
            )
        _, remote_output = run_git(root, "remote")
        remotes = sorted(line for line in remote_output.splitlines() if line)
        if expected_version:
            candidates = sorted({expected_version, f"v{expected_version}"})
            _, tags_output = run_git(root, "tag", "--list", *candidates)
            colliding_tags = sorted(line for line in tags_output.splitlines() if line)
            if colliding_tags:
                blockers.append(
                    {
                        "code": "tag_collision",
                        "message": "Local release tag already exists: " + ", ".join(colliding_tags),
                    }
                )

    unique_versions = sorted({item["version"] for item in versions})
    if not versions:
        warnings.append(
            {
                "code": "no_version_metadata",
                "message": "No supported version metadata was found at the release root.",
            }
        )
    elif len(unique_versions) > 1:
        blockers.append(
            {
                "code": "inconsistent_versions",
                "message": "Version metadata disagrees: " + ", ".join(unique_versions),
            }
        )

    if expected_version:
        mismatches = [
            item for item in versions if item["version"] != expected_version
        ]
        if mismatches:
            blockers.append(
                {
                    "code": "expected_version_mismatch",
                    "message": "Expected version does not match: "
                    + ", ".join(
                        f"{item['path']}={item['version']}" for item in mismatches
                    ),
                }
            )

    return {
        "status": "ready" if not blockers else "blocked",
        "release_root": str(root),
        "git_root": git_root if is_git else None,
        "commit": commit,
        "branch": branch,
        "remote_names": remotes,
        "working_tree_changes": changes,
        "expected_version": expected_version,
        "version_metadata": versions,
        "colliding_local_tags": colliding_tags,
        "blockers": blockers,
        "warnings": warnings,
        "network_checks_performed": False,
    }


def render_text(report: dict[str, Any]) -> str:
    lines = [
        f"status: {report['status']}",
        f"release_root: {report['release_root']}",
        f"commit: {report['commit'] or 'UNKNOWN'}",
        f"branch: {report['branch'] or 'DETACHED_OR_UNKNOWN'}",
        f"expected_version: {report['expected_version'] or 'UNSPECIFIED'}",
    ]
    for item in report["version_metadata"]:
        lines.append(f"version: {item['path']}={item['version']} ({item['kind']})")
    for item in report["blockers"]:
        lines.append(f"BLOCKER {item['code']}: {item['message']}")
    for item in report["warnings"]:
        lines.append(f"WARNING {item['code']}: {item['message']}")
    lines.append("network_checks_performed: false")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="release subject root")
    parser.add_argument("--version", help="expected release version")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        parser.error(f"release root is not a directory: {root}")
    report = inspect(root, args.version)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
