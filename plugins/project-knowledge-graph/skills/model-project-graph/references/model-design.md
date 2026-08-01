# Data, schema, identity, and context

## Data graph

Use nodes for entities and typed edges for relations. A property graph style is
appropriate here. JSONL edge objects can carry provenance and other context.
Queries can still match `from`, `rel`, and `to`.

Multiple patterns sharing variables form joins. This means modelling choices
should support stable joins: identities belong in IDs, human wording belongs in
labels and aliases.

## Three schema roles

- **Semantic schema:** defines meanings and supports limited entailment through
  subtype, subproperty, domain, range, inverse, symmetry, and transitivity.
- **Validating schema:** declares minimum shapes, datatypes, cardinalities, and
  evidence requirements.
- **Emergent schema:** summarizes vocabulary actually found in the graph. Review
  the result for drift.

Semantic rules infer. Shapes report violations. Do not confuse either with proof
that the represented sources are complete.

## Identity

Mint local IDs once and never reuse them. Keep one canonical node per entity.
Store alternate surface forms as aliases. Equal stable keys such as canonical
paths or URLs are merge candidates, not automatic proof of identity.

Use placeholder nodes sparingly and mark them explicitly. Use one only when the
only known fact is that an unknown entity exists. Otherwise record a gap.

## Context and provenance

Attach source and recorded date to each assertion. A source path plus anchor
defines which source makes the claim and allows source-scoped replacement.
Promote a fact to a node when multiple participants, roles, dates, or outcomes
must attach to it.

Prefer absolute dates and versions over indexicals such as "currently". Keep
durable facts separate from observations with a time-to-live.

## Reasoning boundary

Store ground assertions. Apply lightweight entailment during query where
supported. Mark any exported derived facts as inferred and regenerable.
Predictions from similarity, centrality, rules, embeddings, or other inductive
methods remain candidates until verified against evidence.

## Source

Paraphrased from Aidan Hogan et al., *Knowledge Graphs* (Morgan & Claypool,
2021), Chapters 2-5, covering graph models and queries, schema, identity,
context, ontologies, deductive knowledge, and inductive knowledge.
