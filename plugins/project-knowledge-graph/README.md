# Project Knowledge Graph plugin

An installable Codex and Claude Code plugin for governed, provenance-backed
project memory.

The plugin bundles:

- eight focused skills spanning the graph lifecycle:
  - `setup-project-graph`
  - `model-project-graph`
  - `ingest-project-graph`
  - `query-project-graph`
  - `analyze-project-graph`
  - `validate-project-graph`
  - `refine-project-graph`
  - `publish-project-graph`
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

## Conceptual basis

The skill suite is a task-oriented synthesis of Aidan Hogan et al.,
*Knowledge Graphs* (Morgan & Claypool, 2021). It follows the book's progression
from graph models, schema, identity, context, and reasoning through creation,
quality assessment, refinement, and publication. The bundled references are
original paraphrases adapted to governed project memory; the textbook itself is
not redistributed.

## Development verification

Run from the repository root:

```bash
python3 scripts/validate_skills.py
python3 plugins/project-knowledge-graph/tests/test_plugin.py -v
```
