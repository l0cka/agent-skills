#!/usr/bin/env python3
"""Validate every repository skill and run its bundled unit tests."""

import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter")
    try:
        block = text.split("---\n", 2)[1]
    except IndexError as exc:
        raise ValueError("unterminated YAML frontmatter") from exc
    fields = {}
    current = None
    for line in block.splitlines():
        if line.startswith((" ", "\t")) and current:
            fields[current] += " " + line.strip()
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        current = key.strip()
        fields[current] = value.strip().strip("\"'")
    return fields


def validate_skill(path):
    errors = []
    try:
        fields = parse_frontmatter(path / "SKILL.md")
    except (OSError, ValueError) as exc:
        return [str(exc)]
    extra = set(fields) - {"name", "description"}
    if extra:
        errors.append(f"unsupported frontmatter fields: {sorted(extra)}")
    name = fields.get("name")
    if name != path.name:
        errors.append(f"frontmatter name {name!r} does not match directory")
    if not name or not NAME_RE.match(name):
        errors.append("name must be lowercase hyphen-case")
    if not fields.get("description"):
        errors.append("description is required")
    if not (path / "agents" / "openai.yaml").is_file():
        errors.append("agents/openai.yaml is required in this repository")
    return errors


def main():
    registry = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))
    registered = {entry["name"]: entry for entry in registry.get("skills", [])}
    skills = sorted(path for path in SKILLS.iterdir() if path.is_dir())
    failures = 0
    for skill in skills:
        errors = validate_skill(skill)
        if skill.name not in registered:
            errors.append("missing skills.json registry entry")
        if errors:
            failures += 1
            for error in errors:
                print(f"FAIL {skill.name}: {error}")
            continue
        print(f"PASS {skill.name}: structure")
        for test in sorted((skill / "scripts").glob("test_*.py")) if (skill / "scripts").is_dir() else []:
            result = subprocess.run(
                ["python3", str(test), "-v"],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            if result.returncode:
                failures += 1
                print(f"FAIL {skill.name}: {test.name}\n{result.stdout}")
            else:
                count = result.stdout.count(" ... ok")
                print(f"PASS {skill.name}: {test.name} ({count} tests)")
    untracked = sorted(set(registered) - {path.name for path in skills})
    for name in untracked:
        failures += 1
        print(f"FAIL {name}: registry path is missing")
    if failures:
        print(f"\nValidation failed: {failures} failure(s).")
        return 1
    print(f"\nValidated {len(skills)} skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
