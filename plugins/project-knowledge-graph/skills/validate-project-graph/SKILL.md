---
name: validate-project-graph
description: Assess a project knowledge graph's integrity, provenance, freshness, schema conformance, competency-question coverage, accuracy, representativeness, coherency, succinctness, and fitness for purpose. Use before relying on, committing, publishing, or declaring a graph complete; after source, schema, or tool changes; or when investigating stale evidence, orphaned nodes, duplicate identities, contradictions, lifecycle gaps, or incomplete project coverage.
---

# Validate Project Graph

Quality means fitness for the declared purpose. Read
[quality-model.md](references/quality-model.md) before producing a quality
judgement.

## Mechanical gate

Run:

```bash
python3 kg/kg.py --kg kg validate --strict
python3 kg/kg.py --kg kg test-cq
```

Strict validation must have zero errors and warnings before declaring the graph
healthy. It checks parsing, IDs, endpoint integrity, vocabulary, domain/range,
required properties, shapes, evidence, source hashes, freshness, orphans, and
duplicates.

## Human review

Mechanical success is necessary but insufficient:

1. Spot-check at least five material assertions against their source anchors.
2. Compare the manifest with the declared source boundary and list unrepresented
   canonical sources.
3. Check representation across code, decisions, people, operations, and process
   where relevant.
4. Review `orphans` and `dupes`. Justify real islands and resolve identity
   splits.
5. Confirm lifecycle shapes reach their required decisions, outcomes, or
   verification gates.
6. Check that labels and descriptions make ambiguous entities understandable.

## Report

State:

- graph hash and validation time.
- supported intended uses.
- blocked uses and why.
- errors, warnings, stale sources, and coverage gaps.
- spot-check sample and result.
- exact remediation owner or next action.

Do not interpret a green validator as proof of complete real-world knowledge.
