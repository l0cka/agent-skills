---
name: verify-release-candidate
description: "Verify that an exact software release candidate is ready to publish by checking repository state, version consistency, tests, build outputs, package metadata, sensitive-content risks, provenance, and clean-install behavior. Use for release readiness reviews, pre-publish checks, dry runs, artifact inspection, or deciding whether a candidate is blocked."
---

# Verify Release Candidate

Verify the exact commit and the artifacts that will be published. Do not publish, push tags, create releases, or archive repositories.

## Preflight

Read [release-gates.md](../../references/release-gates.md) and the matching section of [ecosystem-checks.md](../../references/ecosystem-checks.md).

1. Resolve the candidate commit and expected version from the release contract.
2. Run:

```bash
python3 ../../scripts/release_preflight.py <release-root> --version <version> --json
```

3. Treat a dirty tree, inconsistent version metadata, or an existing local tag as a blocker unless the release contract explicitly explains why it is safe.
4. Check remote tag and destination-version collisions separately; the helper is deliberately offline.

## Validate source and artifact

1. Run the repository's documented tests, linters, type checks, policy checks, and release-specific gates.
2. Build into a clean temporary directory. Do not validate only the source checkout.
3. Inspect the artifact file list, metadata, version, license and provenance, dependency declarations, generated data, and accidental secrets or private paths.
4. Install or load the built artifact in a fresh environment and exercise its public entry point.
5. Record commands, exit status, artifact digest, and bounded output. Do not replace failed evidence with a narrative assertion.

## Decide

Use the record in [evidence-record.md](../../references/evidence-record.md).

- Return `READY` only when every required gate passed for the exact commit and artifact.
- Return `BLOCKED` when any required gate failed, was skipped, or remains unknown.

List blockers by location, cause, and fix. Do not weaken a gate merely to reach `READY`.
