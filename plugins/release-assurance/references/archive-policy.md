# Archive policy

Archive only after the replacement and migration path are independently verified.

## Eligibility

Require evidence that:

- the replacement is published and works for a fresh consumer;
- ownership, licence, attribution, history, tags, releases, and provenance will remain accessible;
- active consumers and automation have migrated or have an explicit exception;
- open issues, pull requests, security reports, domains, services, package listings, and documentation have an owner or disposition;
- the requested archive action and any separate destructive actions are clearly scoped.

## Action classes

- **Reversible**: mark a repository read-only, disable a nonessential workflow, add a deprecation notice, or redirect documentation.
- **Repairable**: deprecate or yank a package version where the registry preserves history.
- **Destructive**: delete repositories, branches, tags, packages, releases, services, local clones, data, domains, or backups.

An archive request authorises only the ordinary reversible archive action for the named target. Obtain explicit authority for each destructive class and validate exact targets immediately before acting.

## Verification

Confirm the archive/read-only flag, replacement and migration links, package or plugin status, automation state, consumer path, and retained recovery evidence. Report what remains available and what, if anything, was removed.
