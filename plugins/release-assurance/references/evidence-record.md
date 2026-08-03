# Release evidence record

Keep one record per candidate. Store it in the location required by the repository; do not create a new permanent project file unless the user or project conventions call for one.

```yaml
release:
  subject: ""
  version: ""
  candidate_commit: ""
  source_of_truth: ""
  state: "PLANNED"
scope:
  included: []
  excluded: []
destinations:
  - name: ""
    expected_coordinate: ""
    immutable_id: ""
    status: "PENDING"
    evidence: []
gates:
  - name: "scope"
    status: "UNKNOWN"
    command_or_check: ""
    evidence: ""
artifacts:
  - path_or_coordinate: ""
    sha256: ""
    consumer_check: ""
authority:
  publication: ""
  archival: ""
repair_or_recovery:
  previous_known_good: ""
  next_action: ""
unknowns: []
```

## Recording rules

- Use exact commits, versions, coordinates, digests, timestamps, and destination identifiers.
- Summarise bounded outputs and retain the command that produced them.
- Record approval as the user's scoped instruction, not as a secret or an inferred blanket permission.
- Distinguish `FAIL` from `UNKNOWN`; a network timeout does not prove absence.
- Redact credentials, authenticated URLs, signing material, private keys, cookies, and full environments.
- Update the state only when its definition in the router skill is satisfied.
