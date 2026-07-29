# Publication and usage controls

## Reuse principles

A reusable graph should be findable, accessible under a stated protocol,
interoperable through documented formats and vocabulary, and reusable under
clear provenance and licensing. These goals apply to metadata as well as data.

Stable identifiers and machine-readable exports improve reuse, but public Web
identifiers are not required for a private project graph.

## Access patterns

Choose the smallest interface that serves the audience:

- downloadable dumps for reproducible snapshots;
- node lookups for entity-centric access;
- edge-pattern access for simple traversal;
- graph-pattern queries for complex joins;
- a static human-readable export for review.

Document rate, stability, version, and freshness expectations when an interface
is long-lived.

## Usage control

Check licenses for every source and for the compiled output. Apply policy at the
graph or subgraph level. Consider confidentiality, personal information,
commercial sensitivity, contractual restrictions, and whether provenance paths
reveal internal structure.

Anonymization can reduce but not eliminate re-identification risk in richly
connected graphs. Use access controls or avoid publication where risk remains.

## Source

Paraphrased from Aidan Hogan et al., *Knowledge Graphs* (Morgan & Claypool,
2021), Chapter 9, which covers FAIR and Linked Data principles, access
protocols, licensing, usage policies, encryption, and anonymization.
