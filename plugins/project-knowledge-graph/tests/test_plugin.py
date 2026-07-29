#!/usr/bin/env python3
"""Integration tests for the plugin bridge, hook, and MCP protocol."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
KG_CLI = (
    PLUGIN_ROOT
    / "skills"
    / "setup-project-graph"
    / "scripts"
    / "kg.py"
)
MCP_SERVER = PLUGIN_ROOT / "mcp" / "kg_mcp.py"
MCP_CONFIG = PLUGIN_ROOT / ".mcp.json"
SESSION_HOOK = PLUGIN_ROOT / "hooks" / "session_start.py"
GRAPH_FILES = ("nodes.jsonl", "edges.jsonl", "schema.json", "manifest.json")
EXPECTED_SKILLS = {
    "setup-project-graph",
    "model-project-graph",
    "ingest-project-graph",
    "query-project-graph",
    "analyze-project-graph",
    "validate-project-graph",
    "refine-project-graph",
    "publish-project-graph",
}
MODERN_PROTOCOL_VERSION = "2026-07-28"


class PluginIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "architecture.md").write_text(
            "# Architecture\n\nThe API depends on the database.\n",
            encoding="utf-8",
        )
        self.run_kg("init", "--project", "Integration fixture", "--profile", "generic")
        self.run_kg("mark-ingested", "architecture.md")
        self.run_kg(
            "add-node",
            "--id",
            "component:api",
            "--type",
            "Component",
            "--label",
            "API",
            "--source",
            "architecture.md#api",
        )
        self.run_kg(
            "add-node",
            "--id",
            "component:database",
            "--type",
            "Component",
            "--label",
            "Database",
            "--source",
            "architecture.md#database",
        )
        self.run_kg(
            "add-edge",
            "--from",
            "component:api",
            "--rel",
            "depends_on",
            "--to",
            "component:database",
            "--source",
            "architecture.md#dependency",
        )

    def tearDown(self):
        self.temp.cleanup()

    def run_kg(self, *args):
        return subprocess.run(
            ["python3", str(KG_CLI), "--kg", str(self.root / "kg"), *args],
            cwd=self.root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
        )

    def graph_hash(self):
        digest = hashlib.sha256()
        for name in GRAPH_FILES:
            digest.update((self.root / "kg" / name).read_bytes())
        return digest.hexdigest()

    def test_plugin_exposes_focused_skill_suite(self):
        skill_root = PLUGIN_ROOT / "skills"
        actual = {
            path.name
            for path in skill_root.iterdir()
            if path.is_dir() and (path / "SKILL.md").is_file()
        }
        self.assertEqual(actual, EXPECTED_SKILLS)
        self.assertNotIn("project-knowledge-graph", actual)
        self.assertTrue(KG_CLI.is_file())

    def run_mcp(self, messages):
        payload = "".join(
            json.dumps({"jsonrpc": "2.0", **message}) + "\n"
            for message in messages
        )
        env = dict(os.environ)
        env["CODEX_PROJECT_DIR"] = str(self.root)
        completed = subprocess.run(
            ["python3", str(MCP_SERVER)],
            input=payload,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=True,
        )
        self.assertEqual(completed.stderr, "")
        return [json.loads(line) for line in completed.stdout.splitlines()]

    @staticmethod
    def modern_meta(version=MODERN_PROTOCOL_VERSION):
        return {
            "io.modelcontextprotocol/protocolVersion": version,
            "io.modelcontextprotocol/clientInfo": {
                "name": "project-knowledge-graph-tests",
                "version": "1.0.0",
            },
            "io.modelcontextprotocol/clientCapabilities": {},
        }

    def run_configured_mcp(self, *, claude, modern=False):
        config = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
        server = config["mcpServers"]["project-knowledge-graph"]
        env = dict(os.environ)
        env["CODEX_PROJECT_DIR"] = str(self.root)
        if claude:
            args = [
                arg.replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGIN_ROOT))
                for arg in server["args"]
            ]
            cwd = self.root
        else:
            args = server["args"]
            cwd = PLUGIN_ROOT
        request = (
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "server/discover",
                "params": {"_meta": self.modern_meta()},
            }
            if modern
            else {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18"},
            }
        )
        completed = subprocess.run(
            [server["command"], *args],
            input=json.dumps(request) + "\n",
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=True,
        )
        self.assertEqual(completed.stderr, "")
        return json.loads(completed.stdout)

    def test_shared_mcp_launcher_resolves_in_codex_and_claude(self):
        for claude in (False, True):
            for modern in (False, True):
                with self.subTest(
                    client="claude" if claude else "codex",
                    protocol="modern" if modern else "legacy",
                ):
                    response = self.run_configured_mcp(claude=claude, modern=modern)
                    server_info = (
                        response["result"]["_meta"][
                            "io.modelcontextprotocol/serverInfo"
                        ]
                        if modern
                        else response["result"]["serverInfo"]
                    )
                    self.assertEqual(server_info["name"], "project-knowledge-graph")

    def test_modern_mcp_discovers_lists_and_calls_without_initialize(self):
        before = self.graph_hash()
        responses = self.run_mcp(
            [
                {
                    "id": 1,
                    "method": "server/discover",
                    "params": {"_meta": self.modern_meta()},
                },
                {
                    "id": 2,
                    "method": "tools/list",
                    "params": {"_meta": self.modern_meta()},
                },
                {
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "kg_context",
                        "arguments": {"id": "component:api"},
                        "_meta": self.modern_meta(),
                    },
                },
            ]
        )
        discovery, tool_list, tool_call = (response["result"] for response in responses)
        self.assertEqual(discovery["resultType"], "complete")
        self.assertIn(MODERN_PROTOCOL_VERSION, discovery["supportedVersions"])
        self.assertEqual(discovery["cacheScope"], "public")
        self.assertGreater(discovery["ttlMs"], 0)
        self.assertEqual(
            discovery["_meta"]["io.modelcontextprotocol/serverInfo"]["version"],
            "0.3.0",
        )

        self.assertEqual(tool_list["resultType"], "complete")
        self.assertEqual(tool_list["cacheScope"], "public")
        self.assertGreater(tool_list["ttlMs"], 0)
        self.assertEqual(
            [tool["name"] for tool in tool_list["tools"]],
            [
                "kg_overview",
                "kg_health",
                "kg_search",
                "kg_context",
                "kg_query",
                "kg_path",
            ],
        )

        self.assertEqual(tool_call["resultType"], "complete")
        result = json.loads(tool_call["content"][0]["text"])
        self.assertTrue(result["ok"])
        self.assertEqual(before, self.graph_hash())

    def test_modern_mcp_rejects_unsupported_protocol_version(self):
        response = self.run_mcp(
            [
                {
                    "id": 1,
                    "method": "server/discover",
                    "params": {"_meta": self.modern_meta("2099-01-01")},
                }
            ]
        )[0]
        self.assertEqual(response["error"]["code"], -32022)
        self.assertEqual(response["error"]["data"]["requested"], "2099-01-01")
        self.assertIn(
            MODERN_PROTOCOL_VERSION,
            response["error"]["data"]["supported"],
        )

    def test_mcp_rejects_ambiguous_pre_initialize_request(self):
        response = self.run_mcp(
            [{"id": 1, "method": "tools/list", "params": {}}]
        )[0]
        self.assertEqual(response["error"]["code"], -32602)
        self.assertIn("server/discover", response["error"]["message"])

    def test_mcp_lists_six_read_only_tools_and_preserves_graph(self):
        before = self.graph_hash()
        responses = self.run_mcp(
            [
                {
                    "id": 1,
                    "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18"},
                },
                {"method": "notifications/initialized"},
                {"id": 2, "method": "tools/list", "params": {}},
                {
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "kg_context",
                        "arguments": {"id": "component:api"},
                    },
                },
            ]
        )
        self.assertEqual(responses[0]["result"]["serverInfo"]["name"], "project-knowledge-graph")
        self.assertNotIn("resultType", responses[1]["result"])
        names = {tool["name"] for tool in responses[1]["result"]["tools"]}
        self.assertEqual(
            names,
            {
                "kg_overview",
                "kg_health",
                "kg_search",
                "kg_context",
                "kg_query",
                "kg_path",
            },
        )
        tool_result = json.loads(responses[2]["result"]["content"][0]["text"])
        self.assertTrue(tool_result["ok"])
        self.assertEqual(
            tool_result["node_provenance"]["component:api"],
            ["architecture.md#api"],
        )
        self.assertIn(
            {
                "from": "component:api",
                "relation": "depends_on",
                "to": "component:database",
                "source": "architecture.md#dependency",
            },
            tool_result["assertion_provenance"],
        )
        self.assertEqual(before, self.graph_hash())

    def test_mcp_returns_bounded_error_when_graph_is_missing(self):
        env = dict(os.environ)
        env.pop("CODEX_PROJECT_DIR", None)
        completed = subprocess.run(
            ["python3", str(MCP_SERVER)],
            input=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "kg_overview",
                        "arguments": {"root": str(self.root / "missing")},
                        "_meta": self.modern_meta(),
                    },
                }
            )
            + "\n",
            cwd=self.root,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=True,
        )
        response = json.loads(completed.stdout)
        self.assertEqual(response["result"]["resultType"], "complete")
        self.assertTrue(response["result"]["isError"])
        error = json.loads(response["result"]["content"][0]["text"])
        self.assertFalse(error["ok"])
        self.assertIn("No complete kg/", error["error"])

    def test_session_start_brief_is_bounded_and_silent_without_graph(self):
        completed = subprocess.run(
            ["python3", str(SESSION_HOOK)],
            input=json.dumps({"cwd": str(self.root), "source": "startup"}),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=True,
        )
        self.assertEqual(completed.stderr, "")
        self.assertIn("Project knowledge graph", completed.stdout)
        self.assertIn("component:api", completed.stdout)
        self.assertLessEqual(len(completed.stdout), 2_500)

        with tempfile.TemporaryDirectory() as empty:
            completed = subprocess.run(
                ["python3", str(SESSION_HOOK)],
                input=json.dumps({"cwd": empty, "source": "startup"}),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,
                check=True,
            )
            self.assertEqual(completed.stdout, "")
            self.assertEqual(completed.stderr, "")


if __name__ == "__main__":
    unittest.main()
