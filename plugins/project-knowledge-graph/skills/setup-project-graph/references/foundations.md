# Foundations and setup decisions

Use this reference to decide what the graph is for and how large its initial
core should be.

## Conceptual basis

A project knowledge graph is a graph of project data intended to accumulate and
convey knowledge. Nodes represent entities of continuing interest; edges
represent relations between them. Schema, identity, context, provenance, and
limited reasoning turn a data graph into a knowledge graph.

The graph abstraction is useful when:

- sources are diverse, incomplete, or expected to evolve;
- relationships and paths matter as much as individual records;
- stable identity must survive labels, locations, or ownership changing;
- agents need bounded retrieval with inspectable evidence.

Prefer another representation when the task is a single flat table, a short
document, or transient telemetry with no durable entity relationships.

## Pay-as-you-go setup

Start with an initial core that satisfies the competency questions. Do not
front-load every possible source or ontology term. Add sources and schema as
new applications require them.

Competency questions are acceptance tests. Good examples:

- Which production components depend on this service?
- Who owns this decision, and where is that ownership recorded?
- Which experiments reached a terminal decision?

Each question should identify the expected entities, relations, and evidence
needed to answer it.

## Source boundary

Classify candidate inputs as canonical, supporting, observational, or excluded.
Record incomplete source coverage honestly. A manifest of ingested files is not
proof that the whole project is represented.

Keep durable source facts distinct from runtime observations. Observations need
an absolute timestamp, a freshness limit, and a deliberate ingestion decision.

## Source

Paraphrased from Aidan Hogan et al., *Knowledge Graphs* (Morgan & Claypool,
2021), especially Chapters 1-3, Chapter 6, and Chapter 11. The book motivates
flexible graph-based integration, competency-driven ontology engineering, and
incremental creation and enrichment.
