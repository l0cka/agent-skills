#!/usr/bin/env python3
"""Validate every repository skill and run its bundled unit tests."""

import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
PLUGINS = ROOT / "plugins"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


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


def load_object(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"{path.relative_to(ROOT)}: {exc}"]
    if not isinstance(value, dict):
        return None, [f"{path.relative_to(ROOT)}: expected a JSON object"]
    return value, []


def validate_plugins(registry):
    errors = []
    plugin_entries = {
        entry.get("plugin"): entry
        for entry in registry.get("skills", [])
        if entry.get("plugin")
    }
    for relative, entry in sorted(plugin_entries.items()):
        plugin = ROOT / relative
        name = plugin.name
        if not plugin.is_dir():
            errors.append(f"{relative}: plugin directory is missing")
            continue
        manifests = [
            plugin / ".codex-plugin" / "plugin.json",
            plugin / ".claude-plugin" / "plugin.json",
        ]
        versions = set()
        for manifest_path in manifests:
            manifest, manifest_errors = load_object(manifest_path)
            errors.extend(manifest_errors)
            if manifest is None:
                continue
            if manifest.get("name") != name:
                errors.append(
                    f"{manifest_path.relative_to(ROOT)}: name must be {name!r}"
                )
            version = manifest.get("version")
            if not isinstance(version, str) or not SEMVER_RE.match(version):
                errors.append(
                    f"{manifest_path.relative_to(ROOT)}: version must be strict semver"
                )
            else:
                versions.add(version)
            skill_root = plugin / "skills"
            if not skill_root.is_dir():
                errors.append(f"{relative}: skills/ is missing")
        expected_version = entry.get("plugin_version")
        if versions != {expected_version}:
            errors.append(
                f"{relative}: manifest versions {sorted(versions)} do not match "
                f"skills.json plugin_version {expected_version!r}"
            )
        compatibility = ROOT / entry["path"]
        canonical = plugin / "skills" / entry["name"]
        if not compatibility.is_symlink():
            errors.append(f"{entry['path']}: expected a compatibility symlink")
        elif compatibility.resolve() != canonical.resolve():
            errors.append(
                f"{entry['path']}: compatibility symlink does not target {canonical.relative_to(ROOT)}"
            )

        for test in sorted((plugin / "tests").glob("test_*.py")):
            result = subprocess.run(
                ["python3", str(test), "-v"],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            if result.returncode:
                errors.append(f"{relative}: {test.name}\n{result.stdout}")
            else:
                count = result.stdout.count(" ... ok")
                print(f"PASS {name}: {test.name} ({count} tests)")
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
    for error in validate_plugins(registry):
        failures += 1
        print(f"FAIL plugin: {error}")
    if failures:
        print(f"\nValidation failed: {failures} failure(s).")
        return 1
    print(f"\nValidated {len(skills)} skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
