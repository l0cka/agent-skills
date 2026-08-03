---
name: plan-release
description: "Create a bounded software release plan with an evidence-based version, exact candidate scope, publication destinations, preflight gates, authority boundaries, rollback or repair actions, and post-release checks. Use when asked what a release should contain, what version to choose, how to publish safely, or what must pass before release."
---

# Plan Release

Produce a release contract that another agent can execute without rediscovering scope or guessing what success means. Do not publish, tag, archive, or delete anything while planning.

## Inspect

Read [release-gates.md](../../references/release-gates.md) and the relevant section of [ecosystem-checks.md](../../references/ecosystem-checks.md).

1. Read repository instructions and release documentation.
2. Inspect the current branch, commit, working tree, existing tags, version metadata, changelog, CI, tests, build configuration, and registry or marketplace destinations.
3. Identify consumer-visible changes and breaking behavior. Derive the version from the repository's policy; do not invent a semantic-version bump without evidence.
4. Separate required destinations from optional announcements or mirrors.
5. Identify irreversible or difficult-to-reverse steps and the authority required for each.

## Write the contract

Specify:

- release subject and excluded work;
- candidate commit and single version source of truth;
- expected tag, artifact names, registries, marketplaces, and release page;
- ordered pre-publication gates with exact commands or checks;
- publication order, authority boundary, and partial-failure repair path;
- consumer-side checks and the evidence required for completion;
- archival actions, only when separately requested.

Use `UNKNOWN` for facts that live inspection cannot establish. A plan with an unresolved required fact is `PLANNED`, not `READY`.

## Handoff

Create or update the structure in [evidence-record.md](../../references/evidence-record.md). End with one of:

- `PLANNED`: executable contract is complete;
- `BLOCKED`: a decision or prerequisite prevents a safe contract.

Name the first command or check for `verify-release-candidate`.
