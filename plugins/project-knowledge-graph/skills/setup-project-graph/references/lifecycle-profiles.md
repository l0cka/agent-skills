# Lifecycle completeness profiles

Read this when choosing or extending conditional shapes. These are optional contracts, not universal ontology.

## Research

Model:

```text
Experiment -> evaluated_by -> Gate
Experiment -> concluded_by -> Decision or Lesson
Experiment -> produced -> Lesson
Strategy -> tested_by -> Experiment
```

Recommended shapes:

- An open experiment requires a frozen success bar and next-decision date.
- A closed/completed experiment requires at least one fresh `concluded_by` assertion.
- A conclusion requires an absolute date.
- A reusable lesson must cite the experiment or decision that produced it.

Generic rule: every closed experiment must lead to a dated terminal decision or reusable lesson.

## Strategy

Model:

```text
Strategy -> evaluated_by -> Gate
Strategy -> promoted_by -> Decision
Strategy -> killed_by -> Decision
```

Recommended shapes:

- `candidate`: at least one evaluation gate.
- `live`: promotion decision plus complete, fresh gate provenance.
- `killed` or `retired`: terminal decision with fresh evidence.

Do not encode a transient ranking as a durable strategy property unless its source and date are explicit.

## Operations

Model:

```text
Incident -> diagnosed_by -> Diagnosis
Diagnosis -> remediated_by -> Remediation
Remediation -> evaluated_by -> Gate
```

Recommended shapes:

- A resolved incident requires diagnosis plus remediation or a documented acceptance decision.
- A remediation requires a verification gate.
- An open incident requires an owner and next checkpoint.

Preserve incident history. Supersede or tombstone assertions rather than rewriting the past as if the first diagnosis was correct.

## Architecture

Model:

```text
Component -> depends_on -> Component/Technology
Component -> owned_by -> Person/Organization
Component -> governed_by -> Decision
```

Recommended shapes:

- Production components require an owner.
- External dependencies require a source-backed rationale or governing decision.
- Superseded components require a replacement or terminal decision.

Keep the component distinct from the file that defines or describes it.

## Runtime observations

Keep the committed durable graph and observation overlay separate:

```text
Durable entity <- observes - Observation
```

An observation requires:

- `props.observed_at` as an absolute ISO timestamp;
- a shape with `freshness.path` and `max_age_days`;
- deliberate `mark-ingested --allow-runtime`;
- no secret, credential, wallet, or private-key material.

Prefer regenerable, ignored observation files. Never let a stale observation satisfy a durable lifecycle gate.

## Basis

These profiles are project-governance extensions to the general lifecycle in
Aidan Hogan et al., *Knowledge Graphs* (Morgan & Claypool, 2021): incremental
creation and enrichment, quality assessment, refinement, and publication. They
are optional local shapes, not claims that the textbook defines these project
domains.
