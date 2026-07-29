# Project Knowledge Graph plugin

An installable Codex and Claude Code plugin for governed, provenance-backed
project memory.

The plugin bundles:

- the `project-knowledge-graph` skill for graph construction and maintenance;
- six read-only MCP tools for bounded graph retrieval;
- a `SessionStart` hook that injects a compact, freshness-aware graph brief;
- the dependency-free `kg.py` JSONL graph engine.

Project graphs remain committed under each project’s `kg/` directory. The plugin
does not copy graph assertions into Codex or Claude native memory, contact a
remote service, or provide MCP mutation tools.

## MCP tools

- `kg_overview`
- `kg_health`
- `kg_search`
- `kg_context`
- `kg_query`
- `kg_path`

Every result includes the graph hash and bounded output. Node and matching edge
provenance are included where applicable. Use `kg_context` before citing a
relationship.

## Development verification

Run from the repository root:

```bash
python3 scripts/validate_skills.py
python3 plugins/project-knowledge-graph/tests/test_plugin.py -v
```
