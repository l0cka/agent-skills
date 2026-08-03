#!/usr/bin/env python3
"""Tests for the Release Assurance plugin."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = PLUGIN_ROOT / "scripts" / "release_preflight.py"
SKILLS = {
    "release-assurance",
    "plan-release",
    "verify-release-candidate",
    "publish-release",
    "archive-superseded-project",
}


class ReleaseAssuranceTest(unittest.TestCase):
    def git(self, root: Path, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(root), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
        )

    def init_repo(self, root: Path) -> None:
        self.git(root, "init", "-q")
        self.git(root, "config", "user.name", "Release Test")
        self.git(root, "config", "user.email", "release-test@example.invalid")

    def commit_all(self, root: Path) -> None:
        self.git(root, "add", ".")
        self.git(root, "commit", "-qm", "candidate")

    def preflight(self, root: Path, version: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = subprocess.run(
            ["python3", str(PREFLIGHT), str(root), "--version", version, "--json"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        return result, json.loads(result.stdout)

    def test_clean_python_candidate_is_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repo(root)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"example\"\nversion = \"1.2.3\"\n",
                encoding="utf-8",
            )
            self.commit_all(root)
            result, report = self.preflight(root, "1.2.3")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["version_metadata"][0]["version"], "1.2.3")
        self.assertFalse(report["network_checks_performed"])

    def test_dirty_tree_blocks_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repo(root)
            package = root / "package.json"
            package.write_text('{"name":"example","version":"2.0.0"}\n', encoding="utf-8")
            self.commit_all(root)
            package.write_text('{"name":"example","version":"2.0.1"}\n', encoding="utf-8")
            result, report = self.preflight(root, "2.0.1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dirty_worktree", {item["code"] for item in report["blockers"]})

    def test_tag_collision_blocks_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repo(root)
            (root / "Cargo.toml").write_text(
                "[package]\nname = \"example\"\nversion = \"3.1.4\"\n",
                encoding="utf-8",
            )
            self.commit_all(root)
            self.git(root, "tag", "v3.1.4")
            result, report = self.preflight(root, "3.1.4")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("tag_collision", {item["code"] for item in report["blockers"]})

    def test_dual_plugin_manifests_must_agree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repo(root)
            for product, version in ((".codex-plugin", "0.4.0"), (".claude-plugin", "0.5.0")):
                target = root / product
                target.mkdir()
                (target / "plugin.json").write_text(
                    json.dumps({"name": "example", "version": version}),
                    encoding="utf-8",
                )
            self.commit_all(root)
            result, report = self.preflight(root, "0.5.0")
        self.assertNotEqual(result.returncode, 0)
        codes = {item["code"] for item in report["blockers"]}
        self.assertIn("inconsistent_versions", codes)
        self.assertIn("expected_version_mismatch", codes)

    def test_remote_credentials_are_not_reported(self):
        secret = "not-for-output"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repo(root)
            (root / "package.json").write_text(
                '{"name":"example","version":"1.0.0"}\n',
                encoding="utf-8",
            )
            self.commit_all(root)
            self.git(root, "remote", "add", "origin", f"https://user:{secret}@example.invalid/repo.git")
            result, report = self.preflight(root, "1.0.0")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn(secret, result.stdout)
        self.assertEqual(report["remote_names"], ["origin"])

    def test_skill_suite_is_complete(self):
        skill_root = PLUGIN_ROOT / "skills"
        self.assertEqual(
            {path.name for path in skill_root.iterdir() if path.is_dir()},
            SKILLS,
        )
        for name in SKILLS:
            text = (skill_root / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertNotIn("[TODO", text, name)
            self.assertTrue((skill_root / name / "agents" / "openai.yaml").is_file())


if __name__ == "__main__":
    unittest.main()
