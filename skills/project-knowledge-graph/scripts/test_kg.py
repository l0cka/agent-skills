#!/usr/bin/env python3
"""End-to-end tests for the stdlib-only project knowledge graph tool."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("kg.py")


class KGToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="kg-test-")
        self.root = Path(self.temp.name)
        self.kg = self.root / "kg"

    def tearDown(self):
        self.temp.cleanup()

    def run_kg(self, *args, check=True):
        result = subprocess.run(
            ["python3", str(SCRIPT), "--kg", str(self.kg), *args],
            cwd=self.root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if check and result.returncode:
            self.fail(f"command failed ({result.returncode}): {' '.join(args)}\n{result.stdout}")
        return result

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def init(self, profile="generic"):
        self.run_kg("init", "--project", "fixture", "--profile", profile)

    def seed_two_nodes(self, source="docs/source.md"):
        self.write(source, "# Source\nA depends on B.\n")
        self.init()
        self.run_kg("mark-ingested", source)
        self.run_kg(
            "add-node", "--id", "component:a", "--type", "Component",
            "--label", "A", "--source", f"{source}#L2",
        )
        self.run_kg(
            "add-node", "--id", "component:b", "--type", "Component",
            "--label", "B", "--source", f"{source}#L2",
        )

    def test_init_versions_and_self_contained_tool(self):
        self.init()
        manifest = json.loads((self.kg / "manifest.json").read_text())
        schema = json.loads((self.kg / "schema.json").read_text())
        self.assertEqual(manifest["graph_format_version"], 2)
        self.assertEqual(schema["schema_version"], 2)
        self.assertTrue((self.kg / "kg.py").exists())
        self.assertIn("kg.py 2.0.0", self.run_kg("--version").stdout)

    def test_multi_source_assertions_are_preserved_and_query_deduplicates(self):
        self.write("docs/a.md", "# A\nA depends on B.\n")
        self.write("docs/b.md", "# B\nA also depends on B.\n")
        self.init()
        self.run_kg("mark-ingested", "docs/a.md", "docs/b.md")
        for nid, label in (("component:a", "A"), ("component:b", "B")):
            self.run_kg(
                "add-node", "--id", nid, "--type", "Component", "--label", label,
                "--source", "docs/a.md#L2", "--source", "docs/b.md#L2",
            )
        for source in ("docs/a.md#L2", "docs/b.md#L2"):
            self.run_kg(
                "add-edge", "--from", "component:a", "--rel", "depends_on",
                "--to", "component:b", "--source", source,
            )
        duplicate = self.run_kg(
            "add-edge", "--from", "component:a", "--rel", "depends_on",
            "--to", "component:b", "--source", "docs/a.md#L2", check=False,
        )
        self.assertNotEqual(duplicate.returncode, 0)
        self.assertIn("assertion already exists", duplicate.stdout)
        edges = [
            json.loads(line) for line in (self.kg / "edges.jsonl").read_text().splitlines()
        ]
        self.assertEqual(len(edges), 2)
        self.assertEqual(len({edge["id"] for edge in edges}), 2)
        query = self.run_kg("query", "?a depends_on ?b", "--ids-only")
        self.assertEqual(query.stdout.count("component:a\tcomponent:b"), 1)
        self.run_kg("validate", "--strict")

    def test_stale_source_and_corrupt_jsonl_fail_validation(self):
        self.seed_two_nodes()
        self.write("docs/source.md", "# Source\nChanged.\n")
        stale = self.run_kg("validate", check=False)
        self.assertNotEqual(stale.returncode, 0)
        self.assertIn("stale", stale.stdout)
        self.run_kg("mark-ingested", "docs/source.md")
        with (self.kg / "nodes.jsonl").open("a", encoding="utf-8") as f:
            f.write("{bad json\n")
        corrupt = self.run_kg("validate", check=False)
        self.assertNotEqual(corrupt.returncode, 0)
        self.assertIn("bad JSON", corrupt.stdout)

    def test_research_shape_and_executable_competency_question(self):
        self.write("research.md", "# Result\nStrategy S was killed by Decision D.\n")
        self.init("research")
        self.run_kg("mark-ingested", "research.md")
        self.run_kg(
            "add-node", "--id", "strategy:s", "--type", "Strategy", "--label", "S",
            "--props", '{"status":"killed"}', "--source", "research.md#L2",
        )
        self.run_kg(
            "add-node", "--id", "decision:d", "--type", "Decision", "--label", "D",
            "--props", '{"date":"2026-07-29","status":"final"}', "--source", "research.md#L2",
        )
        self.run_kg(
            "add-edge", "--from", "strategy:s", "--rel", "killed_by",
            "--to", "decision:d", "--source", "research.md#L2",
        )
        schema = json.loads((self.kg / "schema.json").read_text())
        schema["competency_questions"] = [{
            "id": "terminal-strategy-provenance",
            "question": "Why was each terminal strategy killed?",
            "query": "?s killed_by ?d",
            "assert": {
                "covers": {
                    "var": "?s",
                    "type": "Strategy",
                    "props.status": ["killed", "retired"],
                }
            },
        }]
        (self.kg / "schema.json").write_text(json.dumps(schema, indent=2) + "\n")
        self.run_kg("test-cq")
        self.run_kg("validate", "--strict")

    def test_merge_conflict_reports_without_writing(self):
        self.seed_two_nodes()
        nodes_path = self.kg / "nodes.jsonl"
        nodes = [json.loads(line) for line in nodes_path.read_text().splitlines()]
        nodes[0]["description"] = "Canonical description"
        nodes[1]["description"] = "Different description"
        nodes_path.write_text("\n".join(json.dumps(node) for node in nodes) + "\n")
        before = nodes_path.read_bytes()
        result = self.run_kg("merge", "component:b", "component:a", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('"status": "conflict"', result.stdout)
        self.assertEqual(nodes_path.read_bytes(), before)

    def test_refresh_rejects_conflict_transactionally(self):
        self.seed_two_nodes()
        self.run_kg(
            "add-edge", "--from", "component:a", "--rel", "depends_on",
            "--to", "component:b", "--source", "docs/source.md#L2",
        )
        staged_nodes = self.write(
            "stage/nodes.jsonl",
            json.dumps({
                "id": "component:a", "type": "Component", "label": "Conflicting A",
                "sources": ["docs/source.md#L2"],
            }) + "\n",
        )
        staged_edges = self.write("stage/edges.jsonl", "")
        before = {
            name: (self.kg / name).read_bytes()
            for name in ("nodes.jsonl", "edges.jsonl", "manifest.json")
        }
        result = self.run_kg(
            "refresh-source", "docs/source.md",
            "--nodes", str(staged_nodes), "--edges", str(staged_edges),
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        for name, content in before.items():
            self.assertEqual((self.kg / name).read_bytes(), content)

    def test_concurrent_assertions_do_not_race(self):
        self.seed_two_nodes()
        commands = []
        for index in range(8):
            commands.append(subprocess.Popen(
                [
                    "python3", str(SCRIPT), "--kg", str(self.kg), "add-edge",
                    "--from", "component:a", "--rel", "depends_on", "--to", "component:b",
                    "--source", f"docs/source.md#L{index + 1}",
                ],
                cwd=self.root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            ))
        outputs = [process.communicate() for process in commands]
        self.assertTrue(all(process.returncode == 0 for process in commands), outputs)
        edges = (self.kg / "edges.jsonl").read_text().splitlines()
        self.assertEqual(len(edges), 8)
        self.assertEqual(len({json.loads(line)["id"] for line in edges}), 8)

    def test_secret_and_environment_files_are_excluded(self):
        self.init()
        self.write(".env", "API_TOKEN=abcdefghijklmnop123456\n")
        result = self.run_kg("mark-ingested", ".env", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("secret", result.stdout.lower())

    def test_v1_migration_is_previewable_and_valid(self):
        self.seed_two_nodes()
        self.run_kg(
            "add-edge", "--from", "component:a", "--rel", "depends_on",
            "--to", "component:b", "--source", "docs/source.md#L2",
        )
        nodes_path = self.kg / "nodes.jsonl"
        nodes = [json.loads(line) for line in nodes_path.read_text().splitlines()]
        for node in nodes:
            node.pop("sources", None)
        nodes_path.write_text("\n".join(json.dumps(node) for node in nodes) + "\n")
        edges_path = self.kg / "edges.jsonl"
        edges = [json.loads(line) for line in edges_path.read_text().splitlines()]
        edges[0]["id"] = "e:0001"
        edges_path.write_text(json.dumps(edges[0]) + "\n")
        manifest_path = self.kg / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        for key in ("graph_format_version", "schema_version", "tool_version", "hash_algorithm"):
            manifest.pop(key, None)
        digest = hashlib.sha1((self.root / "docs/source.md").read_bytes()).hexdigest()
        manifest["sources"]["docs/source.md"] = {
            "sha1": digest,
            "ingested": "2026-07-29",
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        schema_path = self.kg / "schema.json"
        schema = json.loads(schema_path.read_text())
        schema.pop("schema_version", None)
        schema.pop("shapes", None)
        schema_path.write_text(json.dumps(schema, indent=2) + "\n")
        before = manifest_path.read_bytes()
        self.run_kg("migrate", "--dry-run")
        self.assertEqual(manifest_path.read_bytes(), before)
        self.run_kg("migrate")
        self.run_kg("validate", "--strict")


if __name__ == "__main__":
    unittest.main()
