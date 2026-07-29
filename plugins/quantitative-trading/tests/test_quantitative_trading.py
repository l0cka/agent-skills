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


if __name__ == "__main__":
    unittest.main()
