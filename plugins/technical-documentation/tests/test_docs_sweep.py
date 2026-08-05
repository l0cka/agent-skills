#!/usr/bin/env python3
"""Contract tests for the Docs Sweep skill."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PLUGIN_ROOT / "skills" / "docs-sweep"
STE_ROOT = PLUGIN_ROOT / "skills" / "apply-simplified-technical-english"
SKILL_TEXT = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
GRAPH_TEXT = (
    SKILL_ROOT / "references" / "project-graph-integration.md"
).read_text(encoding="utf-8")


class DocsSweepContractTest(unittest.TestCase):
    def test_graph_refresh_is_a_completion_gate(self):
        self.assertIn(
            "Do not report `COMPLETE` while any changed graph-tracked document remains stale",
            SKILL_TEXT,
        )
        self.assertIn("COMPLETE WITH PRE-EXISTING GRAPH DEBT", SKILL_TEXT)
        self.assertIn("Refresh unavailable or unverified", GRAPH_TEXT)
        self.assertIn("`PARTIAL` or `BLOCKED`, never", GRAPH_TEXT)

    def test_graph_plugin_and_standalone_skill_names_are_supported(self):
        for name in (
            "query-project-graph",
            "ingest-project-graph",
            "refine-project-graph",
            "validate-project-graph",
        ):
            self.assertIn(f"project-knowledge-graph:{name}", GRAPH_TEXT)
            self.assertIn(name, GRAPH_TEXT)

    def test_read_only_mcp_does_not_disable_write_workflow(self):
        self.assertIn("MCP interface is intentionally read-only", GRAPH_TEXT)
        self.assertIn(
            "not evidence that graph write tooling is unavailable",
            GRAPH_TEXT,
        )
        self.assertIn("Never use `mark-ingested` by itself", GRAPH_TEXT)

    def test_plugin_manifest_versions_match(self):
        versions = {
            json.loads(path.read_text(encoding="utf-8"))["version"]
            for path in (
                PLUGIN_ROOT / ".codex-plugin" / "plugin.json",
                PLUGIN_ROOT / ".claude-plugin" / "plugin.json",
            )
        }
        self.assertEqual(
            len(versions),
            1,
            f"host manifests disagree on version: {sorted(versions)}",
        )

    def test_simplified_technical_english_is_a_completion_gate(self):
        normalized = " ".join(SKILL_TEXT.split())
        self.assertIn(
            "technical-documentation:apply-simplified-technical-english",
            SKILL_TEXT,
        )
        self.assertIn("`apply-simplified-technical-english`", SKILL_TEXT)
        self.assertIn("Either gate can prevent a complete sweep", normalized)
        self.assertIn("Do not claim ASD-STE100 certification", normalized)

    def test_standard_has_provenance_without_redistributed_pdf(self):
        reference = (
            STE_ROOT / "references" / "asd-ste100-issue-9.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Issue 9, 15 January 2025", reference)
        self.assertIn(
            "40d66f0cea84d1fff67f36d560c04eab4034c6bcf64014d43bd6d4c19795f3f0",
            reference,
        )
        self.assertEqual(list(STE_ROOT.rglob("*.pdf")), [])


if __name__ == "__main__":
    unittest.main()
