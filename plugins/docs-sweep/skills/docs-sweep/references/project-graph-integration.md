# Existing Project Knowledge Graph integration

Use this path when the project already contains `kg/manifest.json`. The graph
plugin remains optional; synchronization of changed tracked sources does not.

## Capture the baseline

Before editing documentation:

1. Resolve the canonical project root and inspect `kg/manifest.json` for
   documentation sources inside the sweep inventory.
2. Record the graph hash, validation errors and warnings, stale-source paths,
   and competency-question result. Run the project's CLI when present:

```bash
python3 kg/kg.py --kg kg validate --strict
python3 kg/kg.py --kg kg test-cq
```

Capture non-zero results as baseline evidence instead of aborting. A failing
baseline means the graph is not healthy, but does not authorize broad repair.

3. Query the graph before broad exploration. For a plugin install, use
   `project-knowledge-graph:query-project-graph`; for a standalone install, use
   `query-project-graph`. Prefer `kg_health`, `kg_overview`, `kg_search`, and
   `kg_context` when the read-only MCP tools are available.
4. Treat the graph as a navigation and provenance index, not as independent
   truth. Confirm material claims against cited sources. Missing assertions are
   unknown, not false.

## Resolve a write-capable path

For plugin installations, load these namespaced skills as needed:

- `project-knowledge-graph:ingest-project-graph`;
- `project-knowledge-graph:refine-project-graph`;
- `project-knowledge-graph:validate-project-graph`.

Accept `ingest-project-graph`, `refine-project-graph`, and
`validate-project-graph` as standalone fallbacks. Prefer the project's
`kg/kg.py`; otherwise use the CLI bundled with the loaded graph skill. Confirm
that the resolved CLI supports `refresh-source`, `validate --strict`, and
`test-cq` before relying on it. Do not hardcode an agent cache path.

The graph MCP interface is intentionally read-only. A read-only MCP result is
not evidence that graph write tooling is unavailable.

## Refresh changed tracked sources

After the documentation diff is stable:

1. Intersect changed documentation paths with sources already present in
   `kg/manifest.json`. If the intersection is empty, record `graph unaffected`
   and leave graph files unchanged.
2. For every changed tracked source, use the ingest or refine skill to extract
   source-backed nodes and assertions into staged JSONL outside `kg/`.
3. Preview each replacement before applying it:

```bash
python3 kg/kg.py --kg kg refresh-source <source-path> \
  --nodes <staged-nodes.jsonl> \
  --edges <staged-edges.jsonl> \
  --dry-run
```

4. Review the preview for the exact source boundary, stable entity IDs,
   independent corroborating assertions, and unrelated changes. Apply the same
   command without `--dry-run` only when that review passes.
5. Never use `mark-ingested` by itself to clear staleness after source content
   changed. Updating only the manifest hash can conceal stale assertions.
6. Re-run strict validation and competency tests, then inspect the graph diff.

If extraction requires a schema, identity, or contradiction decision that the
source cannot resolve, leave that source stale and report the sweep as
`PARTIAL` or `BLOCKED` with the exact decision required.

## Apply the completion gate

- **No graph:** report graph integration as not applicable.
- **Graph unaffected:** permit `COMPLETE` when no changed documentation source
  is tracked by the manifest.
- **Healthy baseline:** permit `COMPLETE` only when every changed tracked source
  was refreshed, strict validation has zero errors and warnings, and competency
  tests pass.
- **Unhealthy baseline:** permit `COMPLETE WITH PRE-EXISTING GRAPH DEBT` only
  when every changed tracked source was refreshed, none remains stale, no new
  error or warning was introduced, competency coverage did not regress, and
  unrelated assertions remain intact. Report before-and-after counts and keep
  the graph itself labelled `NOT VALID`.
- **Refresh unavailable or unverified:** report `PARTIAL` or `BLOCKED`, never
  `COMPLETE`. State the missing skill, CLI, permission, evidence, or decision;
  make graph remediation the next action rather than merely suggesting diff
  review.

An explicit user instruction to exclude graph mutation narrows the delivered
scope; report that exclusion and any resulting stale tracked sources. Never
silently treat exclusion as successful graph synchronization.
