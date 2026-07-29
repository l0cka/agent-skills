---
name: ingest-project-graph
description: Extract, map, stage, ingest, enrich, refresh, or remove source-backed nodes and assertions in an existing project knowledge graph. Use when reading project documents, code, tables, JSON, XML, prior graphs, decisions, incidents, or research records into kg/; resolving mentions to stable entities; refreshing a changed source; or maintaining manifest hashes without bypassing provenance and secret controls.
---

# Ingest Project Graph

Ingest one source at a time. Read
[ingestion-methods.md](references/ingestion-methods.md) before processing
structured data, ambiguous entities, or a new source class.

## Safety and source policy

Resolve the canonical project root. Exclude credentials, `.env*`, keys, wallets,
certificates, VCS internals, dependencies, caches, binaries, generated files,
oversized files, and runtime state unless explicitly approved. Never store a
secret excerpt.

External sources require `--allow-external`. Runtime sources require
`--allow-runtime` and a freshness contract.

## Extraction loop

For each coherent document section or structured record:

1. Identify named, recurrent entities.
2. Search IDs, labels, and aliases before creating a node.
3. Resolve ambiguous mentions using source context and existing neighbours.
4. Align relations to the declared vocabulary.
5. Store scalars as properties.
6. Promote higher-arity facts to nodes when roles, dates, rationale, or outcome
   matter.
7. Cite every node and edge with `path#anchor`.

For small changes:

```bash
python3 kg/kg.py --kg kg mark-ingested docs/architecture.md
python3 kg/kg.py --kg kg add-node \
  --id component:auth --type Component --label "Auth service" \
  --source "docs/architecture.md#authentication"
python3 kg/kg.py --kg kg add-edge \
  --from component:auth --rel depends_on --to component:db \
  --source "docs/architecture.md#L120"
```

For source replacement, write staged JSONL outside `kg/`, then:

```bash
python3 kg/kg.py --kg kg refresh-source docs/architecture.md \
  --nodes /tmp/architecture.nodes.jsonl \
  --edges /tmp/architecture.edges.jsonl \
  --dry-run
python3 kg/kg.py --kg kg refresh-source docs/architecture.md \
  --nodes /tmp/architecture.nodes.jsonl \
  --edges /tmp/architecture.edges.jsonl
```

Preview source removal with `remove-source PATH --dry-run`. Do not bulk append
or manually rewrite assertion IDs.

Finish with `$validate-project-graph`. A successful command is not proof that
the extraction is complete or semantically accurate.
