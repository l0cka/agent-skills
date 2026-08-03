# Release Assurance

Release Assurance provides five workflows for planning, checking, publishing,
verifying, and safely retiring software releases.

The plugin treats release completion as an evidence claim. It checks the exact
candidate and built artifact, requires scoped authority for publication and
archival, verifies every destination from the consumer side, and records
partial releases without rewriting immutable history.

## Skills

- `release-assurance`: route and govern an end-to-end release.
- `plan-release`: fix scope, version, destinations, gates, and recovery.
- `verify-release-candidate`: test the exact candidate and built artifact.
- `publish-release`: publish an authorised candidate and verify destinations.
- `archive-superseded-project`: retire a replaced project without losing evidence.

## Preflight helper

Run the offline candidate check from the plugin root:

```bash
python3 scripts/release_preflight.py /path/to/release-root --version 1.2.3
```

The helper reports Git state, local tag collisions, and supported version
metadata. It deliberately performs no network or publication actions.
