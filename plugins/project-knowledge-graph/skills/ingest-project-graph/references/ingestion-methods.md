# Creation and enrichment methods

## Text and code

Treat extraction as a joint loop:

- preprocess by coherent section, function, class, or decision record.
- recognize node-worthy entities.
- link mentions to existing identities.
- extract typed relations with exact evidence.

Headings, symbols, imports, links, and tables carry structure. Preserve that
structure instead of flattening everything into prose.

Create nodes for named, recurrent, cross-source referents. Keep one-off values
and ordinary scalar attributes in properties. Search before creating. Alias
splitting is a common source of duplicate nodes.

## Structured sources

Map tables using stable primary keys and foreign-key links. Omit empty cells
rather than creating null nodes. Map JSON and XML to domain entities and
relations, not literal parent-child syntax. Import only relevant subgraphs from
other graphs, then align both identity and vocabulary.

## Human review

Automated or agent extraction can be wrong, biased, or incomplete. Use human
review for ambiguous identities, schema changes, disputed facts, and
high-impact assertions. Independent sources supporting one triple remain
separate assertions.

## Incremental enrichment

Begin with the core needed for current competency questions. Refresh assertions
by source so source changes can replace exactly what they previously supported.
Do not let the ease of extraction expand the graph beyond its declared scope.

## Source

Paraphrased from Aidan Hogan et al., *Knowledge Graphs* (Morgan & Claypool,
2021), Chapter 6. The chapter covers collaborative creation, text extraction,
markup and structured mappings, and ontology engineering using an incremental
pay-as-you-go approach.
