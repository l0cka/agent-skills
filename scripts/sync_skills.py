#!/usr/bin/env python3
"""Deploy canonical repository skills to Codex and Claude Code."""

import argparse
import filecmp
import os
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
TARGETS = {
    "codex": Path.home() / ".codex" / "skills",
    "claude": Path.home() / ".claude" / "skills",
}


def skill_dirs():
    return sorted(path for path in SKILLS.iterdir() if path.is_dir() and (path / "SKILL.md").is_file())


def same_tree(left, right):
    comparison = filecmp.dircmp(left, right, ignore=["__pycache__", ".DS_Store"])
    if comparison.left_only or comparison.right_only or comparison.diff_files or comparison.funny_files:
        return False
    return all(same_tree(Path(left) / name, Path(right) / name) for name in comparison.common_dirs)


def target_state(source, destination, mode):
    if destination.is_symlink():
        return "synced" if destination.resolve() == source.resolve() else "conflict-link"
    if not destination.exists():
        return "missing"
    if mode == "copy" and destination.is_dir() and same_tree(source, destination):
        return "synced-copy"
    return "conflict-existing"


def deploy(source, destination, mode):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if mode == "symlink":
        destination.symlink_to(source, target_is_directory=True)
    else:
        shutil.copytree(source, destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="perform missing installs")
    parser.add_argument("--mode", choices=["symlink", "copy"], default="symlink")
    parser.add_argument("--target", choices=["both", *TARGETS], default="both")
    args = parser.parse_args()

    selected = TARGETS if args.target == "both" else {args.target: TARGETS[args.target]}
    conflicts = 0
    changes = 0
    for skill in skill_dirs():
        for target_name, target_root in selected.items():
            destination = target_root / skill.name
            state = target_state(skill, destination, args.mode)
            label = f"{target_name}:{skill.name}"
            if state == "missing":
                changes += 1
                if args.apply:
                    deploy(skill, destination, args.mode)
                    print(f"INSTALLED {label} -> {destination}")
                else:
                    print(f"PLAN      {label} -> {destination}")
            elif state.startswith("synced"):
                print(f"OK        {label} ({state})")
            else:
                conflicts += 1
                print(f"CONFLICT  {label}: {destination} ({state}; not overwritten)")

    if not args.apply and changes:
        print(f"\nPreview only: {changes} install(s) pending. Re-run with --apply.")
    elif args.apply:
        print(f"\nApplied {changes} install(s).")
    if conflicts:
        print(f"{conflicts} conflict(s) require deliberate resolution.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
