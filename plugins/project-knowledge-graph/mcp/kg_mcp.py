#!/usr/bin/env python3
"""Dependency-free, read-only MCP server for governed project graphs."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from lib.kg_bridge import (  # noqa: E402
    GraphBridgeError,
    enrich_result,
    find_project_root,
    run_kg,
)


SERVER_NAME = "project-knowledge-graph"
SERVER_VERSION = "0.1.4"
INSTRUCTIONS = (
    "Use kg_overview or kg_health before relying on graph assertions. "
    "Use kg_context before citing relationships because it returns exact provenance. "
    "The graph is open-world: missing assertions are unknown, not false. "
    "If validation fails, do not present affected assertions as current. "
    "All tools are read-only and outputs may be truncated."
)


ROOT_PROPERTY = {
    "root": {
        "type": "string",
        "description": (
            "Optional canonical project root. Omit to discover the nearest parent "
            "containing a complete kg/ directory."
        ),
    }
}


def schema(properties=None, required=None):
    merged = dict(ROOT_PROPERTY)
    merged.update(properties or {})
    value: dict[str, Any] = {
        "type": "object",
        "properties": merged,
        "additionalProperties": False,
    }
    if required:
        value["required"] = required
    return value


TOOLS = [
    {
        "name": "kg_overview",
        "description": (
            "Summarize graph size, vocabulary, freshness, validation state, and graph hash. "
            "Use first when a project graph may answer the task."
        ),
        "inputSchema": schema(),
    },
    {
        "name": "kg_health",
        "description": (
            "Run strict integrity, provenance, schema, freshness, and optional competency checks "
            "without changing graph assertions."
        ),
        "inputSchema": schema(
            {
                "test_competency_questions": {
                    "type": "boolean",
                    "default": False,
                }
            }
        ),
    },
    {
        "name": "kg_search",
        "description": (
            "Find graph nodes by ID, label, or alias. Returns bounded results plus node provenance."
        ),
        "inputSchema": schema(
            {
                "text": {"type": "string", "minLength": 1},
                "type": {"type": "string"},
                "deep": {"type": "boolean", "default": False},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 15},
            },
            ["text"],
        ),
    },
    {
        "name": "kg_context",
        "description": (
            "Return a node briefing, adjacent assertions, and exact node/edge provenance. "
            "Use before citing a graph relationship."
        ),
        "inputSchema": schema(
            {
                "id": {"type": "string", "minLength": 1},
                "depth": {"type": "integer", "enum": [1, 2], "default": 1},
            },
            ["id"],
        ),
    },
    {
        "name": "kg_query",
        "description": (
            "Run joined triple patterns such as '?component depends_on ?dependency'. "
            "Supports optional patterns, anti-joins, filters, transitive relation+, and counts."
        ),
        "inputSchema": schema(
            {
                "patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 12,
                },
                "optional": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 8,
                    "default": [],
                },
                "not": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 8,
                    "default": [],
                },
                "filters": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 8,
                    "default": [],
                },
                "count_by": {"type": "string"},
                "ids_only": {"type": "boolean", "default": False},
            },
            ["patterns"],
        ),
    },
    {
        "name": "kg_path",
        "description": (
            "Find the shortest graph path between two node IDs, labels, or aliases."
        ),
        "inputSchema": schema(
            {
                "from": {"type": "string", "minLength": 1},
                "to": {"type": "string", "minLength": 1},
                "relations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 20,
                },
                "directed": {"type": "boolean", "default": False},
            },
            ["from", "to"],
        ),
    },
]


def _text_result(value: dict[str, Any], is_error=False):
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(value, ensure_ascii=False, indent=2),
            }
        ],
        "isError": is_error,
    }


def _bool(value: Any, default=False) -> bool:
    return value if isinstance(value, bool) else default


def call_tool(name: str, arguments: dict[str, Any]):
    root_arg = arguments.get("root")
    if root_arg is not None and not isinstance(root_arg, str):
        raise GraphBridgeError("root must be a string")
    root = find_project_root(root_arg)

    if name == "kg_overview":
        stats = run_kg(root, "stats")
        health = run_kg(root, "validate", "--strict")
        result = {
            **stats,
            "validation_ok": health["ok"],
            "validation": health["output"],
        }
        return enrich_result(root, result)

    if name == "kg_health":
        validation = run_kg(root, "validate", "--strict")
        if _bool(arguments.get("test_competency_questions")):
            competency = run_kg(root, "test-cq")
            validation["competency_questions_ok"] = competency["ok"]
            validation["competency_questions"] = competency["output"]
            validation["ok"] = validation["ok"] and competency["ok"]
        return enrich_result(root, validation)

    if name == "kg_search":
        text = arguments.get("text")
        if not isinstance(text, str) or not text.strip():
            raise GraphBridgeError("text is required")
        limit = arguments.get("limit", 15)
        if not isinstance(limit, int):
            raise GraphBridgeError("limit must be an integer")
        command = ["find", text, "--limit", str(max(1, min(50, limit)))]
        node_type = arguments.get("type")
        if node_type is not None:
            if not isinstance(node_type, str):
                raise GraphBridgeError("type must be a string")
            command.extend(["--type", node_type])
        if _bool(arguments.get("deep")):
            command.append("--deep")
        return enrich_result(root, run_kg(root, *command))

    if name == "kg_context":
        node_id = arguments.get("id")
        if not isinstance(node_id, str) or not node_id:
            raise GraphBridgeError("id is required")
        depth = arguments.get("depth", 1)
        if depth not in (1, 2):
            raise GraphBridgeError("depth must be 1 or 2")
        return enrich_result(root, run_kg(root, "context", node_id, "--depth", str(depth)))

    if name == "kg_query":
        patterns = arguments.get("patterns")
        if (
            not isinstance(patterns, list)
            or not patterns
            or not all(isinstance(pattern, str) for pattern in patterns)
        ):
            raise GraphBridgeError("patterns must be a non-empty string array")
        command = ["query", *patterns]
        for key, flag in (("optional", "--optional"), ("not", "--not"), ("filters", "--filter")):
            values = arguments.get(key) or []
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                raise GraphBridgeError(f"{key} must be a string array")
            for value in values:
                command.extend([flag, value])
        count_by = arguments.get("count_by")
        if count_by is not None:
            if not isinstance(count_by, str):
                raise GraphBridgeError("count_by must be a string")
            command.extend(["--count-by", count_by])
        if _bool(arguments.get("ids_only")):
            command.append("--ids-only")
        return enrich_result(root, run_kg(root, *command))

    if name == "kg_path":
        start, end = arguments.get("from"), arguments.get("to")
        if not isinstance(start, str) or not isinstance(end, str) or not start or not end:
            raise GraphBridgeError("from and to are required")
        command = ["path", start, end]
        relations = arguments.get("relations")
        if relations is not None:
            if not isinstance(relations, list) or not all(
                isinstance(relation, str) for relation in relations
            ):
                raise GraphBridgeError("relations must be a string array")
            command.extend(["--rel", ",".join(relations)])
        if _bool(arguments.get("directed")):
            command.append("--directed")
        return enrich_result(root, run_kg(root, *command))

    raise GraphBridgeError(f"Unknown tool {name!r}")


def send(message: dict[str, Any]):
    sys.stdout.write(json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def handle(message: dict[str, Any]):
    method = message.get("method")
    request_id = message.get("id")
    if method == "initialize":
        requested = (message.get("params") or {}).get("protocolVersion")
        return {
            "protocolVersion": requested or "2025-06-18",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            "instructions": INSTRUCTIONS,
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(name, str) or not isinstance(arguments, dict):
            raise GraphBridgeError("tools/call requires a tool name and object arguments")
        return _text_result(call_tool(name, arguments))
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if request_id is None:
        return None
    raise GraphBridgeError(f"Unsupported MCP method {method!r}")


def main():
    for raw_line in sys.stdin:
        if not raw_line.strip():
            continue
        request_id = None
        try:
            message = json.loads(raw_line)
            if not isinstance(message, dict):
                raise ValueError("message must be an object")
            request_id = message.get("id")
            result = handle(message)
            if request_id is not None and result is not None:
                send({"jsonrpc": "2.0", "id": request_id, "result": result})
        except GraphBridgeError as exc:
            if request_id is not None:
                if isinstance(message, dict) and message.get("method") == "tools/call":
                    send(
                        {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": _text_result({"ok": False, "error": str(exc)}, True),
                        }
                    )
                else:
                    send(
                        {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {"code": -32602, "message": str(exc)},
                        }
                    )
        except (json.JSONDecodeError, ValueError) as exc:
            send(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32700, "message": str(exc)},
                }
            )
        except Exception as exc:  # defensive boundary: never print protocol noise
            if request_id is not None:
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32603, "message": f"Internal error: {exc}"},
                    }
                )


if __name__ == "__main__":
    main()
