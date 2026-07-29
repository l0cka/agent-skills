---
name: analyze-project-graph
description: Analyze an existing project knowledge graph using schema-aware traversal, entailment, topology, centrality, communities, similarity, and structural-gap detection while separating explicit facts, deductive consequences, and inductive candidates. Use when finding key entities, clusters, dependency reachability, unusual islands, possible missing links, likely duplicates, inferred types, or graph-derived project insights.
---

# Analyze Project Graph

Read [reasoning-and-analytics.md](references/reasoning-and-analytics.md) before
presenting graph-derived conclusions.

## Evidence classes

Label every result as one of:

- **asserted:** directly stored with source provenance;
- **entailed:** follows deterministically from declared schema behavior;
- **candidate:** suggested by topology, similarity, or a statistical pattern.

Only asserted relationships have source evidence. Entailments must name the
rule. Candidates require verification before graph mutation.

## Workflow

1. Check health and coverage with `kg_health` or `validate --strict`.
2. Use query and path operations for deterministic analysis:

```bash
python3 kg/kg.py --kg kg query "?x depends_on+ component:database"
python3 kg/kg.py --kg kg path component:web component:database --directed
```

3. Use structural analytics:

```bash
python3 kg/kg.py --kg kg important
python3 kg/kg.py --kg kg communities
python3 kg/kg.py --kg kg orphans
python3 kg/kg.py --kg kg similar
python3 kg/kg.py --kg kg dupes
```

4. Reopen source-backed context for any asserted relationship included in the
   answer.
5. Explain method, scope, and uncertainty. Centrality is not importance in every
   business sense; community membership is not ontology; similarity is not
   identity.
6. Route actionable candidates to `$refine-project-graph`.

Do not write predicted edges directly. A plausible graph pattern is not source
evidence.
