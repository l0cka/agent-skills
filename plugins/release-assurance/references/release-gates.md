# Release gates

Apply every gate that is relevant to the release contract. A required gate is `PASS`, `FAIL`, or `UNKNOWN`; never silently omit it.

## Universal gates

1. **Scope**: Name the release subject, included changes, excluded work, candidate commit, and intended consumers.
2. **Source**: Require the expected repository, branch or detached-CI context, clean candidate tree, reviewed diff, and passing repository instructions.
3. **Version**: Use one authoritative version and reconcile every duplicated manifest, tag, lockfile, catalog, and generated metadata surface.
4. **Validation**: Run the project's documented tests and release-specific policy gates against the exact candidate.
5. **Artifact**: Build once from the candidate; inspect and test the artifact that will be published, including a fresh install or load.
6. **Supply chain**: Check dependencies, generated data, licence and attribution, provenance, accidental credentials, private paths, and unexpected files.
7. **Destination**: Check authentication presence without exposing values, naming ownership, existing tag or version collisions, destination policy, and publication order.
8. **Authority**: Map each external or destructive action to the user's explicit request. Do not expand destinations or archival scope by convenience.
9. **Post-release**: Fetch through the consumer path, verify version and integrity, run a smoke test, and check release-page or marketplace state.
10. **Evidence**: Record commands, commit, version, artifact digests, destination identifiers, results, unknowns, and repair or recovery steps.

## Failure handling

- Before publication, a failed or unknown required gate means `BLOCKED`.
- After any successful publication, preserve immutable history. Classify the result as `PUBLISHED_PARTIAL` and repair forward.
- Do not delete a successful artifact merely because a later destination failed.
- Do not reuse a published version for changed bytes.
- Do not mark a release complete while consumer-side verification is pending.

## Minimum rollback or repair thinking

For reversible deployment-style releases, identify how to restore the previous known-good version. For immutable packages and tags, identify the next corrective version, yanking or deprecation options, communication surface, and consumer migration. Never promise rollback where the destination only supports repair forward.
