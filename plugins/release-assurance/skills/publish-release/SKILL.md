---
name: publish-release
description: "Publish an approved software release to specified Git, GitHub, package-registry, or agent-plugin destinations and verify the result from the consumer side. Use when the user explicitly asks to release, publish, tag, upload, promote, or complete a previously verified release, including recovery from a partial publication."
---

# Publish Release

Publish only the candidate that reached `READY`. Publication changes external state and some destinations are immutable.

## Authority gate

Read [release-gates.md](../../references/release-gates.md), [ecosystem-checks.md](../../references/ecosystem-checks.md), and [evidence-record.md](../../references/evidence-record.md).

Proceed when the user explicitly authorised the version and destinations, or when the current request unambiguously says to publish or release the already-fixed candidate. Otherwise ask once immediately before the first external mutation.

Do not infer authority to:

- overwrite an existing tag or package version;
- publish to an extra registry or marketplace;
- mark a release as latest;
- archive a repository;
- delete local or remote material.

## Publish

1. Recheck the candidate commit, clean tree, version consistency, gate results, credentials presence without printing values, and destination collisions.
2. Follow the release contract's destination order. Perform and verify one destination before starting the next.
3. Record the immutable identifier, URL or package coordinate, digest when available, timestamp, and command outcome for each destination.
4. If a destination succeeds and a later step fails, stop unrelated publication. Preserve the successful artifact and produce a repair-forward plan; do not rewrite history.

## Verify as a consumer

Do not trust the upload response alone.

1. Fetch registry or marketplace metadata without relying on a local build cache.
2. Download or install the published artifact in a fresh temporary environment.
3. Confirm version, digest or provenance when available, imports or entry points, and one representative public behavior.
4. Check the Git tag and release page target the candidate commit. Check latest/prerelease status only when the release contract requires it.
5. Record every check in the evidence record.

Return `PUBLISHED_VERIFIED` only when all required destinations pass. Return `PUBLISHED_PARTIAL` when any published destination remains failed or unknown, and identify the exact repair action.
