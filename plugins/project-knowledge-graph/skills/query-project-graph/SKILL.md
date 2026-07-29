---
name: query-project-graph
description: Retrieve bounded, provenance-backed answers from an existing project knowledge graph using the read-only MCP tools or kg.py. Use when locating an entity by ID, label, or alias; inspecting its neighbourhood; answering joined graph-pattern questions; finding dependency or relationship paths; checking graph health before reliance; or citing the exact source behind a project relationship.
---

# Query Project Graph

Prefer the plugin's read-only MCP tools. Read
[query-patterns.md](references/query-patterns.md) for joins, optional patterns,
anti-joins, filters, and paths.

## Retrieval protocol

1. Call `kg_overview` or `kg_health` before relying on the graph.
2. Resolve entities with `kg_search`.
3. Call `kg_context` before citing a relationship; it returns adjacent
   assertions and exact provenance.
4. Use `kg_query` for joined triple patterns and `kg_path` for shortest paths.
5. Cite the returned assertion source, not merely the graph.
6. State coverage limits. Missing assertions are unknown, not false.

If MCP cannot find the graph, pass the canonical project root. Do not treat
truncated output as complete.

CLI equivalents:

```bash
python3 kg/kg.py --kg kg stats
python3 kg/kg.py --kg kg find "billing"
python3 kg/kg.py --kg kg context component:billing
python3 kg/kg.py --kg kg neighbors component:billing --depth 2
python3 kg/kg.py --kg kg path person:sam concept:gst
python3 kg/kg.py --kg kg query \
  "?component type Component" \
  "?component depends_on component:db"
```

If the graph cannot answer, inspect manifest coverage and report the evidence
gap. Do not silently fill it from model memory.
