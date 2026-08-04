# Project maintenance review rubric

Use this rubric to keep findings evidence-backed and proposals proportionate.

## Finding threshold

Include a finding only when all four statements are true:

1. Current repository or verified external evidence shows a concrete mismatch,
   risk, recurring cost, or missing safeguard.
2. The affected behavior, audience, or maintenance burden is identifiable.
3. A bounded change can improve the condition without speculative redesign.
4. A check can verify the change or clearly reduce the uncertainty.

Do not treat code age, personal style, file length, dependency age, `TODO`
comments, or unfamiliar architecture as debt without evidence of impact.

## Severity

| Level | Use when |
| --- | --- |
| Critical | Credible present risk of data loss, security compromise, or severe production failure |
| High | Broken supported workflow, material correctness risk, or actively misleading safety or operations guidance |
| Medium | Repeated maintenance cost, missing regression protection, or stale documentation likely to block a user |
| Low | Local friction or bounded cleanup with a demonstrated but limited benefit |

Severity describes impact, not implementation effort. Do not inflate severity
to improve priority.

## Confidence

| Level | Evidence standard |
| --- | --- |
| High | Reproduced behavior or direct contradiction between authoritative sources |
| Medium | Multiple consistent signals with one material fact still unverified |
| Low | Plausible signal that needs investigation before an edit can be proposed |

Only `High` and `Medium` confidence findings can be proposed for change. Label
`Low` confidence findings `INVESTIGATE` and state the next diagnostic.

## Priority

Order proposals by:

1. Correctness and safety impact.
2. Broken user or operator workflow.
3. Compounding maintenance cost or blocked delivery.
4. Documentation truth and discoverability.
5. Cosmetic consistency with demonstrated value.

Raise priority when one small root-cause fix resolves several verified
symptoms. Lower priority for broad churn, uncertain ownership, or high rollback
cost.

## Technical-debt evidence

Useful signals include:

- A failing or missing regression check tied to a supported behavior.
- Duplicate implementations that have already diverged.
- Dead paths proven unreachable by references, configuration, tests, and build
  entry points.
- Compatibility code whose documented removal condition is now satisfied.
- Unsupported dependencies proven by official lifecycle or registry evidence.
- Repeated incidents, workarounds, or manual steps linked to a specific design.

Search results alone do not prove dead code. A newer dependency version alone
does not prove that an upgrade is safe or valuable.

## Documentation evidence

Compare human-facing claims with manifests, schemas, CLI help, tests, workflows,
runtime defaults, and accepted decisions. Preserve historical release notes and
quoted material. Change generated documentation through its source.

Classify a missing document as debt only when there is a defined audience and
an authoritative source for the content.

## Approval boundaries

Give separate IDs to changes that differ in any of these ways:

- One can ship safely without the other.
- One needs a migration, dependency update, deletion, or public API change.
- They have different validation or rollback paths.
- The evidence supports one change but only an investigation for the other.

An approval covers the described files, behavior, risk, and validation. It does
not cover newly discovered implementation work outside that boundary.
