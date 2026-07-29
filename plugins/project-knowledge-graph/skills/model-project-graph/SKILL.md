---
name: model-project-graph
description: Design or revise the data model, vocabulary, schema, stable identities, provenance, contextual assertions, shapes, and lightweight reasoning rules for a project knowledge graph. Use when deciding node versus property, relation direction, domain and range, aliases and duplicate identity, n-ary event or decision modelling, open-world versus local closed-world semantics, competency-question contracts, or schema.json changes.
---

# Model Project Graph

Model for durable queries and evidence, not for visual neatness. Read
[model-design.md](references/model-design.md) before non-routine schema or
identity changes.

## Invariants

- Mint IDs once as `type:slug`; change labels and aliases, not IDs.
- Distinguish an entity from a document about it.
- Keep scalar values in `props`; create nodes for named, recurrent,
  cross-source referents.
- Require `sources` on nodes and one exact `source` on every edge.
- Treat assertion identity as `(from, relation, to, source, anchor)`.
- Preserve corroborating assertions from independent sources.
- Use a closed, documented vocabulary. Propose schema changes before writing
  undeclared types or relations.
- Treat missing facts as unknown unless a bounded source is explicitly complete.

## Workflow

1. Read the competency questions and inspect actual vocabulary with:

```bash
python3 kg/kg.py --kg kg stats
```

2. Choose the smallest useful directed edge-labelled model.
3. Define node types and relation types in `schema.json`, including operational
   descriptions, domain, range, and only justified inference flags.
4. Add open shapes for required properties, evidence policies, cardinality, and
   freshness. Shapes may require fields while still allowing unforeseen ones.
5. Represent decisions, incidents, experiments, and other higher-arity facts as
   nodes when participants, time, rationale, or outcome must attach to the fact.
6. Review identity keys, labels, aliases, and likely collisions.
7. Update executable competency questions when schema changes alter expected
   answers.
8. Run:

```bash
python3 kg/kg.py --kg kg validate --strict
python3 kg/kg.py --kg kg test-cq
```

Use query-time inverse, symmetric, subtype, and transitive behavior where
supported. Do not materialize inferred edges as authoritative source facts.
