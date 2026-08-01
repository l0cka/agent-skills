---
name: refine-project-graph
description: Review and safely apply knowledge graph completion, correction, deduplication, consolidation, source-refresh, and inconsistency-repair work. Use when validating possible missing links or types, resolving duplicate identities, correcting unsupported or stale assertions, merging nodes, replacing one source's assertions, removing a source, migrating an older graph, or turning analysis candidates into evidence-backed graph changes.
---

# Refine Project Graph

Refinement improves an existing graph. Read
[refinement-methods.md](references/refinement-methods.md) before changing
identity or resolving contradictions.

## Rule

Analytics produce candidates. Sources justify mutations. Never convert a
similarity score, centrality result, inferred type, or learned rule directly
into an authoritative assertion.

## Workflow

1. Capture the current graph hash and run `$validate-project-graph`.
2. Generate bounded candidates:

```bash
python3 kg/kg.py --kg kg similar
python3 kg/kg.py --kg kg dupes
python3 kg/kg.py --kg kg orphans
```

3. Verify each proposed completion or correction against canonical source
   anchors.
4. For duplicates, choose the stable canonical ID and preview:

```bash
python3 kg/kg.py --kg kg merge duplicate:id canonical:id --dry-run
```

Resolve conflicting descriptions or properties explicitly with a reviewed
manual edit or `--prefer canon|dup`. Never silently concatenate them.

5. For changed sources, use source-scoped `refresh-source --dry-run` before
   applying. Preview removal with `remove-source PATH --dry-run`.
6. Use `migrate --dry-run` before migrating an older graph format.
7. Re-run strict validation and competency tests.
8. Review the diff. Confirm unrelated assertions and independent corroborating
   sources remain intact.

When the evidence cannot identify the correct repair, record the ambiguity and
leave the graph unchanged.
