# Completion and correction

## Completion

Completion proposes missing links, types, or identity links. Candidate
techniques include declared inverse/symmetric/transitive behavior, shared
neighbours, relation signatures, rule mining, and other predictive methods.

All candidates need source verification. A high plausibility score is not a
durable project fact.

## Identity consolidation

Combine lexical evidence such as labels and aliases with contextual evidence
such as shared neighbours and stable keys. Use blocking by type or normalized
name to avoid broad pairwise comparison.

After confirming identity, merge edges onto one stable canonical ID and retain
alternate names as aliases. Do not merge merely because labels are similar.

## Correction

Reopen the cited source and test whether it still supports the assertion.
Multiple independent sources can provide stronger support, but source count
does not override a newer canonical source or a clearly scoped policy.

Detecting inconsistency does not prove which assertion should be removed. Prefer
the smallest evidence-backed repair. Check that inference rules will not
recreate a removed contradiction.

## Source-scoped maintenance

Replace or remove assertions by their source key. This preserves unrelated
sources and allows a changed document to invalidate exactly the claims it
previously supported.

## Source

Paraphrased from Aidan Hogan et al., *Knowledge Graphs* (Morgan & Claypool,
2021), Chapter 8, covering graph completion, link/type/identity prediction,
fact validation, and inconsistency repair.
