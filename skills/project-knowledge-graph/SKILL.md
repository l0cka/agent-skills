---
name: project-knowledge-graph
description: Build, govern, query, validate, refresh, and maintain a provenance-backed project knowledge graph stored as committable JSONL. Use when Codex or Claude needs to map a codebase, folder, research program, architecture, operations history, decisions, ownership, dependencies, or project memory; answer questions from an existing kg/ directory; enforce lifecycle completeness and freshness rules; detect stale or unsupported assertions; or visualize and deduplicate a project graph.
---

# Project Knowledge Graph

Create a durable graph that another agent can trust without rereading the whole project. Store it at `<project>/kg/`:

| File | Purpose |
|---|---|
| `nodes.jsonl` | Stable entities with node-level provenance |
| `edges.jsonl` | Source-scoped relationship assertions |
| `schema.json` | Vocabulary, conditional shapes, executable competency questions |
| `manifest.json` | Source hashes, graph/schema/tool versions, freshness metadata |
| `kg.py` | Self-contained stdlib-only governance and query tool |
| `README.md` | Instructions for agents that do not have this skill |

Preserve these invariants:

- Mint node IDs once as `type:slug`; rename only `label` and retain old names as aliases.
- Require every node to have one or more `sources`; require every edge to have one `source`.
- Write evidence as a repository-relative `path#anchor`. A source must be in the manifest and hash-fresh at completion.
- Treat an assertion as `(from, relation, to, source, anchor)`. Keep corroborating sources as separate assertions; deduplicate triples only for display.
- Use the closed type and relation vocabulary. Declare a new term before using it.
- Treat missing edges as unknown, not false, unless a deliberately bounded local-closed-world rule says otherwise.
- Keep runtime observations separate from the durable graph and enforce a TTL when deliberately ingested.

Read the relevant reference before making non-routine modelling choices:

- [schema-identity-context.md](references/schema-identity-context.md): schema, shapes, stable identity, provenance, inference.
- [graph-model-and-querying.md](references/graph-model-and-querying.md): multiple sources, n-ary facts, optional and negative queries.
- [extraction-quality-refinement.md](references/extraction-quality-refinement.md): source extraction, security, quality, deduplication.
- [lifecycle-completeness.md](references/lifecycle-completeness.md): research, operations, strategy, architecture, and runtime profiles.

## Governed workflow

### 1. Establish the boundary

Resolve the canonical project root. Agree on the graph’s scope, core sources, exclusions, and 2–5 questions it must answer.

Exclude by default:

- `.env*`, credentials, private keys, wallets, certificates, and secret-bearing files;
- `.git`, caches, dependencies, generated artifacts, binaries, and oversized files;
- logs, databases, runtime state, and temporary files unless deliberately scoped;
- paths outside the canonical root.

Never store a secret excerpt. `mark-ingested` runs a path, binary, size, and secret-pattern preflight. External source ingestion requires `--allow-external`; runtime ingestion requires `--allow-runtime` and a freshness bound.

### 2. Initialize a profile

Run:

```bash
python3 <skill>/scripts/kg.py --kg <project>/kg init \
  --project "<name>" --profile generic
```

Use `--profile research` for Experiment → Gate → Decision/Lesson and Strategy → Decision lifecycles. `init` writes the current `kg.py` into the graph.

### 3. Define contracts before extraction

Curate `schema.json`:

- Keep only domain-relevant node and edge types.
- Give every term a one-line operational description.
- Declare required type properties.
- Add conditional `shapes`.
- Store competency questions as executable objects, not prose.

Shape example:

```json
{
  "id": "terminal-strategy-decision",
  "target": {
    "type": "Strategy",
    "props.status": ["killed", "retired"]
  },
  "require_edges": [
    {
      "rel": "killed_by",
      "direction": "out",
      "min": 1,
      "source_policy": "canonical-fresh"
    }
  ]
}
```

Shapes may use:

- `target`: exact matches on `type`, `id`, top-level fields, or `props.<key>`;
- `require_props`: property paths required on each target;
- `require_edges`: relation, direction, minimum/maximum cardinality, and `canonical-fresh` evidence policy;
- `freshness`: `path` plus `max_age_days` for observation nodes.

Competency question example:

```json
{
  "id": "terminal-strategy-provenance",
  "question": "Why was each terminal strategy killed?",
  "query": "?s killed_by ?d",
  "assert": {
    "covers": {
      "var": "?s",
      "type": "Strategy",
      "props.status": ["killed", "retired"]
    }
  }
}
```

`assert` supports `min_results`, `max_results`, and `covers`.

### 4. Survey and rank sources

Inventory before extracting. Prefer dense canonical sources: README and architecture docs, decisions, requirements, manifests, meeting records, then key entry-point code. Map structured data explicitly; do not interpret tables or JSON trees as prose.

Build the smallest core that can satisfy the competency questions. Record coverage gaps rather than pretending the manifest is complete.

### 5. Extract source by source into staging

For each source:

1. Search existing IDs, labels, and aliases with `find`.
2. Create nodes only for named, recurrent, cross-source referents.
3. Keep scalar values in `props`.
4. Align relationships to the closed vocabulary.
5. Cite every node and edge with `path#anchor`.
6. Promote decisions, events, experiments, and other n-ary facts to nodes so actors, dates, gates, and outcomes attach cleanly.

For small edits, use guarded commands:

```bash
python3 kg/kg.py --kg kg mark-ingested docs/architecture.md
python3 kg/kg.py --kg kg add-node \
  --id component:auth --type Component --label "Auth service" \
  --source "docs/architecture.md#authentication"
python3 kg/kg.py --kg kg add-edge \
  --from component:auth --rel depends_on --to component:db \
  --source "docs/architecture.md#L120"
```

For a build or refresh, write source-scoped staged JSONL outside `kg/`, then validate and install it atomically:

```bash
python3 kg/kg.py --kg kg refresh-source docs/architecture.md \
  --nodes /tmp/architecture.nodes.jsonl \
  --edges /tmp/architecture.edges.jsonl \
  --dry-run

python3 kg/kg.py --kg kg refresh-source docs/architecture.md \
  --nodes /tmp/architecture.nodes.jsonl \
  --edges /tmp/architecture.edges.jsonl
```

Do not bypass staging with bulk appends. Mutations use advisory locking; assertion IDs are content-derived. A conflicting node update or invalid staged record aborts without changing graph files.

### 6. Validate provenance and lifecycle completeness

Run:

```bash
python3 kg/kg.py --kg kg validate --strict
```

Treat this as the completion gate. Validation errors include:

- corrupt JSONL or duplicate IDs/assertions;
- missing node or edge provenance;
- malformed or non-canonical sources;
- source absent from the manifest, missing, or hash-stale;
- undeclared types or relations;
- missing required properties;
- invalid domain/range or functional cardinality;
- shape and freshness violations;
- prose-only competency questions.

Warnings also fail under `--strict`.

### 7. Execute competency tests

Run:

```bash
python3 kg/kg.py --kg kg test-cq
```

Use queries to inspect failures. The query engine supports:

```bash
kg.py query "?e type Experiment" --not "?e concluded_by ?x"
kg.py query "?s type Strategy" --optional "?s killed_by ?d"
kg.py query "?s type Strategy" --filter "?s.props.status=killed,retired"
kg.py query "?x depends_on ?y" --count-by "?x"
kg.py query "?x depends_on+ component:db"
```

`prop.<key>` is also a virtual relation, for example `"?e prop.status closed"`.

### 8. Review quality, then install

Before declaring success:

1. Get `validate --strict` to zero errors and warnings.
2. Get `test-cq` to full pass.
3. Spot-check at least five source anchors against their claims.
4. Run `dupes` and review merge candidates against evidence.
5. Run `orphans` and justify or connect islands.
6. Check source coverage and representation across code, decisions, people, and process.
7. Confirm every lifecycle story reaches its required conclusion.

Use `merge DUP CANON --dry-run` first. Conflicting descriptions or properties must be resolved explicitly with a manual edit or `--prefer canon|dup`; never silently concatenate them.

### 9. Wire the graph into the project

Add this to `AGENTS.md`, `CLAUDE.md`, or the project-equivalent:

```markdown
## Knowledge graph
This project has a governed knowledge graph at `kg/`. Before broad exploration,
run `python3 kg/kg.py --kg kg stats`, then use `find`, `context`, `query`, or
`path`. Cite the graph assertion's source in answers. If validation reports stale
or incomplete evidence, do not treat the affected assertion as current.
When work creates a durable fact, stage a source-scoped update, run
`validate --strict` and `test-cq`, then commit the graph with its source change.
```

## Use and maintenance

Start a session with:

```bash
python3 kg/kg.py --kg kg stats
python3 kg/kg.py --kg kg validate --strict
```

Answer by locating, inspecting, traversing, and citing:

```bash
kg.py find "billing"
kg.py context component:billing
kg.py neighbors component:billing --depth 2
kg.py path person:sam concept:gst
kg.py query "?c type Component" "?c depends_on component:db"
```

If the graph cannot answer, inspect manifest coverage, read the missing canonical source, and stage the durable fact. Do not fill silence with a closed-world assumption.

Refresh changed sources with `refresh-source`. Preview removal with `remove-source PATH --dry-run`; removal also prunes the matching node evidence and may expose unsupported nodes. Migrate older graphs with `migrate --dry-run`, then `migrate`, `validate --strict`, and `test-cq`.

Export for people or other tools:

```bash
kg.py export --format html
kg.py export --format graphml
kg.py export --format mermaid
kg.py export --format csv
```

## Tool verification

After modifying the bundled tool or schema profiles, run:

```bash
python3 scripts/test_kg.py -v
python3 <skill-creator>/scripts/quick_validate.py <skill>
```
