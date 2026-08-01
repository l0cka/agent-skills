# Deductive and inductive analysis

## Deductive results

Deduction produces logical consequences from explicit assertions plus declared
rules. In this plugin, useful bounded forms include subtype, inverse, symmetric,
domain/range, and transitive behavior where the schema and query tool support
them.

Report the premises and rule that license an entailed result. Do not attach a
source citation to an inferred edge as though the source asserted it.

## Inductive results

Induction generalizes from observed patterns and can be wrong. Treat outputs as
candidates with a method and confidence rationale:

- degree or PageRank identifies structurally central nodes.
- community detection finds dense topological clusters.
- shared neighbours suggest possible relatedness, missing links, or duplicates.
- type and relation signatures suggest possible classifications.
- learned rules or embeddings, if used externally, predict plausibility rather
  than truth.

Topology can reflect ingestion bias. A source-heavy area may look central
because it is better represented, not because it is more important.

## Analysis report

For each finding, include:

1. result class: asserted, entailed, or candidate.
2. graph hash and scope.
3. method or rule.
4. relevant source provenance for asserted premises.
5. coverage or quality limitations.
6. verification action for candidates.

## Source

Paraphrased from Aidan Hogan et al., *Knowledge Graphs* (Morgan & Claypool,
2021), Chapters 4-5. The book distinguishes deductive consequences from
fallible inductive predictions and surveys graph analytics, embeddings, graph
neural networks, and symbolic learning.
