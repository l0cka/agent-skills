---
name: publish-project-graph
description: Prepare, export, package, document, or publish a project knowledge graph for people or machines with provenance, licensing, privacy, access, and reuse controls. Use when generating HTML, GraphML, Mermaid, or CSV exports; sharing a graph outside its project; designing lookup, dump, or query access; assessing FAIR or linked-data-style readiness; or deciding what graph subset is safe and authorized to expose.
---

# Publish Project Graph

Publication is a separate approval boundary. Read
[publication-controls.md](references/publication-controls.md) before sharing a
graph beyond its current project or trust boundary.

## Preflight

1. Define audience, purpose, allowed scope, and distribution channel.
2. Run `$validate-project-graph`.
3. Review every included source's license, confidentiality, personal data,
   secret risk, and downstream usage restrictions.
4. Select the minimum graph or subgraph needed. Internal provenance paths may
   themselves be sensitive.
5. Record the graph hash, export time, tool version, schema version, license,
   and known coverage limitations.

## Export

```bash
python3 kg/kg.py --kg kg export --format html
python3 kg/kg.py --kg kg export --format graphml
python3 kg/kg.py --kg kg export --format mermaid
python3 kg/kg.py --kg kg export --format csv
```

Use HTML for bounded human exploration, GraphML for graph tools, Mermaid for
small diagrams, and CSV for tabular interchange. Inspect the output for
truncation, hidden sensitive fields, and broken labels.

## Handoff

Publish data together with:

- purpose and scope.
- schema or vocabulary description.
- provenance and graph hash.
- generation instructions.
- license and usage policy.
- access method and expected stability.
- quality, timeliness, and coverage caveats.

Do not infer permission to publish from the ability to export. Protect the graph
with encryption, anonymization, access control, or a private distribution
channel when the risk requires it.
