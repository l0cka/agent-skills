#!/usr/bin/env python3
"""Read-only bridge between an active project and the bundled kg.py tool."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
KG_CLI = (
    PLUGIN_ROOT
    / "skills"
    / "project-knowledge-graph"
    / "scripts"
    / "kg.py"
)
GRAPH_FILES = ("nodes.jsonl", "edges.jsonl", "schema.json", "manifest.json")
MAX_TOOL_OUTPUT_CHARS = 12_000
MAX_BRIEF_CHARS = 2_400


class GraphBridgeError(RuntimeError):
    """A bounded, user-facing graph bridge failure."""


def _has_graph(root: Path) -> bool:
    kg = root / "kg"
    return kg.is_dir() and all((kg / name).is_file() for name in GRAPH_FILES)


def _walk_candidates(start: Path):
    current = start.resolve()
    if current.is_file():
        current = current.parent
    if current.name == "kg" and all((current / name).is_file() for name in GRAPH_FILES):
        yield current.parent
    yield current
    yield from current.parents


def find_project_root(explicit: str | None = None) -> Path:
    """Find the nearest parent with a complete kg/ directory."""
    if explicit:
        candidate = Path(explicit).expanduser().resolve()
        if candidate.name == "kg" and all(
            (candidate / name).is_file() for name in GRAPH_FILES
        ):
            candidate = candidate.parent
        if _has_graph(candidate):
            return candidate
        raise GraphBridgeError(
            f"No complete kg/ graph found at explicit project root {candidate}. "
            "Expected nodes.jsonl, edges.jsonl, schema.json, and manifest.json."
        )

    starts: list[Path] = []
    for key in ("CLAUDE_PROJECT_DIR", "CODEX_PROJECT_DIR"):
        value = os.environ.get(key)
        if value:
            starts.append(Path(value).expanduser())
    starts.append(Path.cwd())
    seen: set[Path] = set()
    for start in starts:
        for candidate in _walk_candidates(start):
            if candidate in seen:
                continue
            seen.add(candidate)
            if _has_graph(candidate):
                return candidate

    raise GraphBridgeError(
        "No complete kg/ graph found under the active project or its parents. "
        "Expected nodes.jsonl, edges.jsonl, schema.json, and manifest.json."
    )


def graph_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for name in GRAPH_FILES:
        path = root / "kg" / name
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GraphBridgeError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GraphBridgeError(f"Expected a JSON object in {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError("record is not an object")
                rows.append(value)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise GraphBridgeError(f"Cannot read {path}: {exc}") from exc
    return rows


def truncate_text(text: str, limit: int = MAX_TOOL_OUTPUT_CHARS) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    suffix = "\n… output truncated; narrow the query or inspect a specific node."
    return text[: max(0, limit - len(suffix))] + suffix, True


def run_kg(root: Path, *arguments: str, timeout: int = 20) -> dict[str, Any]:
    """Run a read-only kg.py command and return a bounded result envelope."""
    command = ["python3", str(KG_CLI), "--kg", str(root / "kg"), *arguments]
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise GraphBridgeError(f"kg.py timed out after {timeout} seconds") from exc
    output, truncated = truncate_text(completed.stdout.strip())
    return {
        "ok": completed.returncode == 0,
        "exit_code": completed.returncode,
        "project_root": str(root),
        "graph_dir": str(root / "kg"),
        "graph_sha256": graph_digest(root),
        "truncated": truncated,
        "output": output,
    }


def node_provenance(root: Path, output: str) -> dict[str, list[str]]:
    """Attach node provenance for IDs present in a textual CLI result."""
    provenance: dict[str, list[str]] = {}
    for node in load_jsonl(root / "kg" / "nodes.jsonl"):
        node_id = node.get("id")
        if not isinstance(node_id, str) or node_id not in output:
            continue
        sources = list(node.get("sources") or [])
        if node.get("source"):
            sources.append(node["source"])
        provenance[node_id] = list(dict.fromkeys(str(value) for value in sources))
    return provenance


def edge_provenance(root: Path, output: str) -> list[dict[str, str]]:
    """Attach exact assertion provenance for edges whose endpoints appear."""
    assertions = []
    for edge in load_jsonl(root / "kg" / "edges.jsonl"):
        source = edge.get("source")
        left = edge.get("from")
        right = edge.get("to")
        if not all(isinstance(value, str) for value in (source, left, right)):
            continue
        if left in output and right in output:
            assertions.append(
                {
                    "from": left,
                    "relation": str(edge.get("rel", "")),
                    "to": right,
                    "source": source,
                }
            )
        if len(assertions) >= 100:
            break
    return assertions


def enrich_result(root: Path, result: dict[str, Any]) -> dict[str, Any]:
    output = str(result.get("output") or "")
    result["node_provenance"] = node_provenance(root, output)
    result["assertion_provenance"] = edge_provenance(root, output)
    return result


def build_session_brief(root: Path) -> str:
    """Build a small deterministic brief suitable for SessionStart context."""
    manifest = load_json(root / "kg" / "manifest.json")
    schema = load_json(root / "kg" / "schema.json")
    nodes = load_jsonl(root / "kg" / "nodes.jsonl")
    edges = load_jsonl(root / "kg" / "edges.jsonl")
    health = run_kg(root, "validate", "--strict", timeout=8)

    degree: dict[str, int] = {str(node.get("id")): 0 for node in nodes}
    for edge in edges:
        for key in ("from", "to"):
            node_id = edge.get(key)
            if node_id in degree:
                degree[str(node_id)] += 1
    by_id = {str(node.get("id")): node for node in nodes}
    important = sorted(
        degree,
        key=lambda node_id: (-degree[node_id], node_id),
    )[:6]

    status = "VALID" if health["ok"] else "NOT VALID"
    lines = [
        "## Project knowledge graph",
        (
            f"A governed graph is available at `kg/` for "
            f"**{manifest.get('project') or schema.get('project') or root.name}**."
        ),
        (
            f"Graph `{health['graph_sha256'][:12]}` · {len(nodes)} nodes · "
            f"{len(edges)} assertions · {len(manifest.get('sources') or {})} sources · "
            f"status **{status}**."
        ),
    ]
    if important:
        summary = ", ".join(
            f"{by_id[node_id].get('label', node_id)} (`{node_id}`)"
            for node_id in important
        )
        lines.append(f"Best-connected entities: {summary}.")
    if not health["ok"]:
        findings = [
            line
            for line in str(health.get("output") or "").splitlines()
            if re.match(r"^(ERROR|WARN)", line)
        ][:4]
        if findings:
            lines.append("Validation findings: " + " | ".join(findings))
    lines.extend(
        [
            (
                "Use the `project-knowledge-graph` MCP tools for bounded retrieval. "
                "Call `kg_context` before citing a relationship so the exact assertion "
                "source is present."
            ),
            (
                "The graph is open-world: missing assertions are unknown, not false. "
                "If validation is not clean, do not present affected assertions as current."
            ),
        ]
    )
    brief, _ = truncate_text("\n\n".join(lines), MAX_BRIEF_CHARS)
    return brief
