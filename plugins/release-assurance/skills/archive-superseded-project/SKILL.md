---
name: archive-superseded-project
description: "Retire or archive a superseded repository, package, plugin, service, or project after its replacement is verified, while preserving provenance, migration guidance, recovery paths, and consumer safety. Use when asked to deprecate, make read-only, archive, sunset, or remove an obsolete project after a release or consolidation."
---

# Archive Superseded Project

Treat archival as a separate lifecycle change, not an automatic side effect of releasing a replacement.

## Establish scope

Read [archive-policy.md](../../references/archive-policy.md) and [evidence-record.md](../../references/evidence-record.md).

1. Resolve the exact repository, package, plugin, service, local checkout, branch, or data surface the user means.
2. Verify that the replacement is `PUBLISHED_VERIFIED` and that the migration path works for a fresh consumer.
3. Inventory open issues, pull requests, automation, dependants, package metadata, documentation, domains, secrets, and retained evidence.
4. Distinguish reversible read-only archival from deletion, unpublishing, branch removal, service shutdown, or data destruction.

An instruction to archive a named repository authorises that repository's supported archive/read-only action. It does not authorise deleting clones, packages, tags, branches, releases, services, domains, or data unless the user names those actions too.

## Retire safely

1. Add replacement and migration guidance before changing discoverability when the destination supports it.
2. Disable or redirect automation only when the replacement covers the same purpose and the release contract includes the change.
3. Preserve tags, releases, licence and attribution, provenance, and the minimum evidence needed to explain the transition.
4. Apply only the approved actions. Prefer reversible settings over deletion.
5. Verify the archived state, replacement links, consumer migration, and absence of unexpected active automation.

Return `ARCHIVED_VERIFIED` only when every approved action is visible and the recovery path is recorded. Otherwise return `BLOCKED` or a precise partial state. Never describe retained material as deleted.
