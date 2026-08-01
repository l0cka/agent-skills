#!/usr/bin/env python3
"""Tests for the ASD-STE100 structural checker."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    PLUGIN_ROOT
    / "skills"
    / "apply-simplified-technical-english"
    / "scripts"
    / "check_ste.py"
)
SPEC = importlib.util.spec_from_file_location("check_ste", SCRIPT)
CHECKER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


class SteCheckerTest(unittest.TestCase):
    def rules(self, text, mode="auto"):
        return {item.rule for item in CHECKER.check_text("example.md", text, mode)}

    def test_clean_descriptive_text_passes(self):
        text = "The service stores each record. The service also records the source."
        self.assertEqual(CHECKER.check_text("example.md", text, "descriptive"), [])

    def test_detects_semicolon_contraction_and_long_procedure(self):
        text = (
            "## Procedure\n\n"
            "Don't start the service; remove every obsolete configuration file from "
            "the local application directory before you connect the service to the "
            "new production database."
        )
        self.assertTrue({"STE-4.2", "STE-5.1", "STE-8.1"} <= self.rules(text))

    def test_detects_long_descriptive_paragraph(self):
        text = "One. Two. Three. Four. Five. Six. Seven."
        self.assertIn("STE-6.6", self.rules(text, "descriptive"))

    def test_ignores_code_fences_inline_code_and_link_targets(self):
        text = (
            "Use `value;other` for this setting. Read [the guide](https://example.com/a;b).\n\n"
            "```text\nDon't use this; it is code.\n```\n"
        )
        self.assertNotIn("STE-8.1", self.rules(text, "descriptive"))
        self.assertNotIn("STE-4.2", self.rules(text, "descriptive"))

    def test_warns_for_passive_voice(self):
        findings = CHECKER.check_text(
            "example.md", "The file was removed by the service.", "descriptive"
        )
        self.assertIn("STE-3.6", {item.rule for item in findings})


if __name__ == "__main__":
    unittest.main()
