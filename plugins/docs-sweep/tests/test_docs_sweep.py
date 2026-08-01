#!/usr/bin/env python3
"""Contract tests for the Docs Sweep skill."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PLUGIN_ROOT / "skills" / "docs-sweep"
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
        self.assertEqual(versions, {"0.1.1"})


if __name__ == "__main__":
    unittest.main()
