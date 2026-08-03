---
name: release-assurance
description: "Govern a software release from scope and version selection through candidate verification, publication, consumer-side checks, and optional retirement of a superseded project. Use for end-to-end releases, release readiness, package or plugin publication, Git tags and GitHub releases, partial-release recovery, or coordinated release-and-archive work."
---

# Release Assurance

Treat a release as a chain of claims that must each have current evidence. Do not infer success from a command returning zero.

## Route the work

| Need | Skill |
| --- | --- |
| Fix scope, version, destinations, gates, and recovery | `plan-release` |
| Decide whether the exact candidate is publishable | `verify-release-candidate` |
| Publish an authorised candidate and prove every destination | `publish-release` |
| Retire a replaced repository or distribution safely | `archive-superseded-project` |

Use the narrowest skill that covers the request. For a complete release, use them in that order and carry one release evidence record throughout.

## Shared contract

Read [release-gates.md](../../references/release-gates.md) before making a readiness or completion claim. Read [ecosystem-checks.md](../../references/ecosystem-checks.md) for the detected package or plugin type. Read [evidence-record.md](../../references/evidence-record.md) when work spans publication or archival.

1. Resolve the release subject, repository root, candidate commit, version source of truth, and intended destinations.
2. Start read-only. Run `python3 ../../scripts/release_preflight.py <root> --version <version>` from this skill directory when a versioned candidate exists.
3. Treat validation of the source tree and validation of the built or downloaded artifact as separate gates.
4. Treat an explicit instruction to publish or release a named version to named destinations as authority for those actions. Ask at the mutation boundary when version, destination, or archival scope remains unclear.
5. Verify each external destination independently. If only some destinations succeed, stop expanding scope and report a partial release with a repair path.

Never print credentials, upload tokens, signing material, full process environments, or authenticated registry URLs. Never rewrite an existing public tag or package version to make a failed release look complete.

## Completion states

- `PLANNED`: scope and gates are fixed; nothing was published.
- `READY`: the exact candidate passed every pre-publication gate.
- `BLOCKED`: at least one required gate failed or remains unknown.
- `PUBLISHED_VERIFIED`: every required destination was checked from the consumer side.
- `PUBLISHED_PARTIAL`: at least one destination succeeded and another failed or remains unknown.
- `ARCHIVED_VERIFIED`: the approved retirement actions are visible and the replacement path works.

Report the exact commit, version, destinations, evidence, and remaining risk with the final state.
