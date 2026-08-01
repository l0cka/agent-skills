# Optional Project Knowledge Graph integration

Use this path only when the Project Knowledge Graph plugin is available or the
project already contains a governed graph at `kg/`.

## Before editing documentation

1. Resolve the canonical project root. Prefer the graph plugin's read-only
   `kg_health` or `kg_overview` tool; otherwise use the project's own
   `kg/kg.py` only when present.
2. Do not rely on a graph with validation errors, unresolved stale sources, or
   unknown coverage. Continue the repository inventory and report the graph's
   limitation.
3. Use `$query-project-graph`, `kg_search`, and `kg_context` to locate
   documentation, components, commands, decisions, and their exact source
   anchors before broad exploration.
4. Treat the graph as a navigation and provenance index, not as independent
   truth. Confirm material documentation claims against the cited source.
5. Treat a missing assertion as unknown, never as proof that a component or
   relationship does not exist.

Useful local equivalents are:

```bash
python3 kg/kg.py --kg kg stats
python3 kg/kg.py --kg kg find "documentation"
python3 kg/kg.py --kg kg context <entity-id>
```

## After editing documentation

1. Inspect `kg/manifest.json` and identify changed documentation paths already
   inside the graph's declared source boundary.
2. Leave the graph unchanged when no changed path is already tracked. Do not
   broaden graph coverage during a docs sweep without explicit user direction.
3. For each tracked changed source, use `$ingest-project-graph` or
   `$refine-project-graph`. Stage source-scoped assertions and preview
   `refresh-source --dry-run` before applying the refresh.
4. Preserve stable entity IDs and independent corroborating assertions. A new
   document heading or line number is not permission to rewrite unrelated graph
   identity or schema.
5. Use `$validate-project-graph` and require both commands to pass:

```bash
python3 kg/kg.py --kg kg validate --strict
python3 kg/kg.py --kg kg test-cq
```

If the write-capable graph skills are unavailable, report the tracked sources
that became stale and leave the graph untouched. If refresh requires a schema,
identity, or contradiction decision, keep that decision outside the docs sweep
and report it as a follow-up.
