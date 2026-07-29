#!/usr/bin/env python3
"""Tests for the Quantitative Trading plugin helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PLUGIN_ROOT / "scripts"
FOCUSED_SKILLS = (
    "design-algorithmic-execution",
    "analyze-transaction-costs",
    "model-market-impact",
    "validate-trading-models",
    "forecast-market-volume",
    "model-execution-risk",
    "optimize-trade-schedules",
    "integrate-cost-aware-portfolios",
)


class QuantitativeTradingHelpersTest(unittest.TestCase):
    def run_script(self, name: str, *args: str, env: dict[str, str] | None = None):
        return subprocess.run(
            ["python3", str(SCRIPTS / name), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            check=False,
        )

    def test_profile_jsonl_reports_window_and_redacts(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            rows = [
                {
                    "ts": "2026-07-28T00:00:00Z",
                    "event": "fill",
                    "asset": "BTC",
                    "pnl": 2.5,
                    "api_token": "supersecret",
                    "wallet_address": "0x1234567890abcdef",
                },
                {
                    "ts": "2026-07-28T01:00:00Z",
                    "event": "fill",
                    "asset": "BTC",
                    "pnl": -1.0,
                },
            ]
            path.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            result = self.run_script(
                "profile_jsonl.py",
                str(path),
                "--group-by",
                "asset",
                "--metric",
                "pnl",
            )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("rows_parsed: 2", result.stdout)
        self.assertIn(
            "covered_window_utc: 2026-07-28T00:00:00Z .. 2026-07-28T01:00:00Z",
            result.stdout,
        )
        self.assertIn("BTC: rows=2", result.stdout)
        self.assertNotIn("supersecret", result.stdout)
        self.assertNotIn("wallet_address", result.stdout)

    def test_list_and_search_lectures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lectures = root / "lectures"
            lectures.mkdir()
            (lectures / "_toc.yml").write_text(
                "parts:\n"
                "  - caption: Trading models\n"
                "    chapters:\n"
                "      - file: inventory_dynamics\n",
                encoding="utf-8",
            )
            (lectures / "inventory_dynamics.md").write_text(
                "# Inventory\nDynamic inventory control for market makers.\n",
                encoding="utf-8",
            )
            listed = self.run_script("list_lectures.py", "--repo-root", str(root))
            searched = self.run_script(
                "search_lectures.py",
                "inventory",
                "control",
                "--repo-root",
                str(root),
            )
        self.assertEqual(listed.returncode, 0, listed.stdout)
        self.assertIn("Trading models", listed.stdout)
        self.assertIn("inventory_dynamics", listed.stdout)
        self.assertEqual(searched.returncode, 0, searched.stdout)
        self.assertIn("lectures/inventory_dynamics.md:2", searched.stdout)

    def test_cache_override_is_honored(self):
        with tempfile.TemporaryDirectory() as directory:
            env = os.environ.copy()
            env["QUANTITATIVE_TRADING_QUANTECON_ROOT"] = directory
            result = self.run_script("list_lectures.py", env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(str(Path(directory) / "lectures" / "_toc.yml"), result.stdout)

    def test_sync_script_has_valid_shell_syntax(self):
        result = subprocess.run(
            ["bash", "-n", str(SCRIPTS / "sync_quantecon.sh")],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_focused_skill_suite_is_complete_and_attributed(self):
        source_note = PLUGIN_ROOT / "references" / "method-provenance.md"
        source_text = source_note.read_text(encoding="utf-8")
        normalized_source = " ".join(source_text.split())
        self.assertIn("Academic Press / Elsevier, 2021", normalized_source)
        self.assertIn("does not bundle source text", normalized_source)

        skill_root = PLUGIN_ROOT / "skills"
        self.assertEqual(
            {
                path.name
                for path in skill_root.iterdir()
                if path.is_dir() and path.name != "quantitative-trading"
            },
            set(FOCUSED_SKILLS),
        )
        for name in FOCUSED_SKILLS:
            skill = skill_root / name
            skill_text = (skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertNotIn("[TODO", skill_text, name)
            self.assertIn(
                "../../references/method-provenance.md",
                skill_text,
                name,
            )
            self.assertTrue((skill / "agents" / "openai.yaml").is_file(), name)
            self.assertTrue(any((skill / "references").glob("*.md")), name)

    def test_plugin_does_not_redistribute_source_pdf(self):
        bundled = [
            path
            for path in PLUGIN_ROOT.rglob("*")
            if path.is_file() and path.suffix.casefold() == ".pdf"
        ]
        self.assertEqual(bundled, [])

    def test_public_metadata_excludes_private_identifiers(self):
        private_markers = (
            "daniel" + "kurdi0" + "@" + "gmail.com",
            "/home/" + "l0cka",
            "/Users/" + "l0cka",
            "ar" + "gus",
            "mm" + "-bot",
            "quantecon" + "-mm-quant",
        )
        paths = [
            path
            for path in PLUGIN_ROOT.rglob("*")
            if path.is_file()
            and path.suffix.lower() in {".json", ".md", ".py", ".sh", ".yaml", ".yml"}
        ]
        for parent in Path(__file__).resolve().parents:
            registry = parent / "skills.json"
            marketplace = parent / ".claude-plugin" / "marketplace.json"
            if registry.is_file() and marketplace.is_file():
                paths.extend([registry, marketplace])
                break
        for path in paths:
            text = path.read_text(encoding="utf-8").casefold()
            for marker in private_markers:
                self.assertNotIn(marker.casefold(), text, str(path))


if __name__ == "__main__":
    unittest.main()
