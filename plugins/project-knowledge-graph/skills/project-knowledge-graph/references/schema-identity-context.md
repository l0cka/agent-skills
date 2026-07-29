# Schema, identity, context & lightweight inference — distilled from Hogan et al., *Knowledge Graphs* (2021), ch. 3–4

Read this when: designing or revising `schema.json`, deciding how to mint IDs, handling duplicate/ambiguous entities, recording provenance, or adding inference rules.

## 1. Schema, three ways (§3.1)

**Semantic schema** (§3.1.1) — defines what terms *mean* and licenses inference. Core vocabulary: *class* (node type), *sub-class* hierarchy, *property* (edge label), *sub-property*, *domain* (type implied for an edge's source), *range* (type implied for its target). The four core inference conditions:
- `x type c` + `c subclass_of d` ⇒ `x type d`
- `x p y` + `p subproperty_of q` ⇒ `x q y`
- `x p y` + `p domain c` ⇒ `x type c`
- `x p y` + `p range c` ⇒ `y type c`

**Open World Assumption (OWA)**: a missing edge is *unknown*, not false. A project KG over partially-scanned sources is inherently OWA — never conclude "no dependency exists" from an absent edge unless that source is declared fully indexed (*Local Closed World*, per-scope completeness claims via the manifest).

**Validating schema** (§3.1.2) — *shapes*: a shape targets a node set (e.g. all nodes of type `Decision`) and imposes constraints: required properties, cardinalities, value datatypes. Key contrast: semantic schema **infers** new edges; validating schema **reports violations**. They compose — infer first, then validate. Crucially, **shapes catch missing data where ontology axioms cannot** (under OWA an axiom just infers the missing value "exists somewhere"). Keep shapes **open** (extra properties allowed) — agents encounter the unforeseen.

**Emergent schema** (§3.1.3) — structure *discovered* from data (graph summarisation). Practical form: periodically tally actual types/relations/property co-occurrence and diff against `schema.json`; surprises become schema updates or flagged data bugs. Discovery informs the schema; it never silently rewrites it.

**Mapping to `schema.json`**: `node_types` (description, `subtype_of`, expected properties with required/recommended cardinality — semantic + validating merged), `edge_types` (description, `domain`, `range`, plus inference flags below), conditional `shapes`, and executable `competency_questions`. The prose `description` per term IS the ontology — a formal *convention* about meaning only works if every future session can read it (§4.1).

## 2. Identity (§3.2)

**Persistent identifiers** (§3.2.1). Ambiguous names cause *naming clashes* when sources merge (two "Santiago"s collapse wrongly). Rules for IDs:
- Convention: `type:slug` — `person:jane-doe`, `module:auth`, `decision:2026-07-choose-sqlite`, `file:src/auth.py`.
- Mint once, never rename, never reuse. If the referent renames in the world, keep the ID, change the `label` (the book's Eswatini lesson: opaque `Q1050` survived the Swaziland→Eswatini rename untouched).
- **Distinguish the entity from the document about it**: `file:docs/auth-design.md` (the file) vs `module:auth` (the thing it describes) are different nodes.

**External identity links** (§3.2.2). Ground identity by (a) storing *uniquely-identifying attributes* on the node (path, email, canonical URL), and (b) `same_as` edges to coreferent nodes. Policy: one canonical node per entity; on discovering a duplicate, `merge` it — rewrite edges onto the canonical ID, keep the duplicate's label as an alias.

**Datatypes** (§3.2.3). Scalars (dates, numbers, strings) are *literals* — store as property values on nodes/edges, never as nodes. ISO-8601 dates so comparison works mechanically.

**Lexicalization** (§3.2.4). IDs carry no semantics; humans and matching need lexical handles: `label` (one canonical), `aliases` (every alternate surface form encountered), `description` (enough to disambiguate from same-named things). **Lookup and entity-matching run over label+aliases; joins and reasoning run over IDs.** Every mention-time variant ("auth module", "authentication service") lands in `aliases` of the one canonical node rather than spawning a new node.

**Existential nodes** (§3.2.5). *Blank nodes* express "something exists but is unidentified". Ration them: only when the shared-existence itself is the fact ("X and Y depend on the same unnamed vendor"); mint `unknown:<n>` with a `placeholder: true` prop; resolve later. Otherwise omit the edge and note the gap.

## 3. Context & provenance (§3.3)

*Context* = the scope of truth of a fact: temporal, geographic, and **provenance** (which source says so, recorded when). Four representations in the book — direct (context as extra nodes/edges), reification (statement nodes), higher-arity (named graphs / property-graph edge annotations), and algebraic annotations. **For JSONL, property-graph-style inline annotation wins**: each edge line is already an object, so per-edge context is free:

```json
{"id":"a:9d6f1f...","from":"module:auth","rel":"depends_on","to":"module:db",
 "source":"docs/architecture.md#L120","recorded":"2026-07-29","props":{"confidence":"high"}}
```

Design points:
- **Every edge gets a content-derived `id`** — buys reification's power (corrections/retractions can reference the exact assertion) while preventing concurrent sequence collisions.
- `source` doubles as a **named-graph key**: re-ingesting or deleting a source file invalidates its assertions wholesale. Node existence and attributes use a `sources` list so their support can also be audited and surgically removed.
- Assertion identity is `(from, relation, to, source, anchor)`, represented by a content-derived ID. Preserve independent corroborating sources even when the displayed triple is the same.
- **Tombstone, don't delete**: superseded facts get `"gone": "YYYY-MM-DD"` (or removal at re-ingest); history stays queryable. Store absolute values that don't decay (dates, versions), never indexicals ("currently", "next week", ages).
- When a fact itself needs participants/time/place (an event, a decision with actors and dates), promote it to a **node** of its own with edges to participants — direct representation — rather than overloading edge props.

## 4. Ontology-lite & inference (§4.1–4.2)

An **ontology** is a formal *convention* about meaning; its value depends entirely on consistent adoption. In an agent KG the parties to the convention are the extraction workflow, the query tool, and future sessions — so it must live in `schema.json` descriptions, or it doesn't exist.

**Assumption stance**: OWA for facts; **Unique Name Assumption within your own minted namespace** — two local IDs are different entities unless `same_as` says otherwise (you minted the names; ambiguity buys nothing locally).

**Ontology features that pay their way** (as flags in `schema.json` `edge_types`):
- `domain` / `range` — validation expectation + type inference in one.
- `inverse` (`contains` ↔ `part_of`): **store one canonical direction only**; answer the other at query time. Never store both.
- `transitive` (`part_of`, `depends_on`, `imports`, `subclass_of`): query with closure (`rel+`), don't materialise chains.
- `symmetric` (`related_to`, `conflicts_with`): store once, match both ways.
- `functional` (at most one value, e.g. `defined_in`): two distinct values ⇒ conflict flag — a free contradiction detector.
- `key` properties (path, email, URL): equal key values ⇒ auto-propose `same_as` — the entity-resolution trigger.

Skip (cost exceeds payoff): class complement/union axioms, cardinality class axioms, property chains, formal DL reasoning. The entire useful "reasoner" is ~six rules (subclass/subproperty instance + transitivity, domain, range) plus the declared closures.

**Materialise vs rewrite** (§4.2.1): apply inference **at query time** (rewriting/closure inside the query tool); graph files store only ground facts. If a consumer needs flattened derived edges, mark them `"inferred": true` and treat as regenerable cache, never hand-edited, never authoritative.

**Vocabulary** (§4.2.2, useful mental model): A-Box (assertions — `nodes.jsonl` + `edges.jsonl`), T-Box (type definitions — `node_types`), R-Box (relation definitions — `edge_types` + rules).

## 5. Recommendations distilled

1. One `schema.json`: node_types (+ `subtype_of`, expected props), edge_types (+ `domain`, `range`, `inverse`, `transitive`, `symmetric`, `functional` flags), prose descriptions as the convention. (§3.1, §4.1)
2. Validate staged updates before installation and use `validate --strict` as the completion gate; keep shapes open to extra properties while enforcing declared minimum contracts. (§3.1.2)
3. Periodic emergent-schema diff: actual vocabulary vs declared; propose, don't auto-rewrite. (§3.1.3)
4. IDs `type:slug`, minted once, immutable; renames touch `label` only; entity ≠ document about it. (§3.2.1)
5. Every node: `label` + `aliases`; match lexically, join on IDs. (§3.2.4)
6. Key attributes on nodes; equal keys ⇒ propose merge. (§3.2.2)
7. Scalars as property values, never nodes; ISO-8601. (§3.2.3)
8. Placeholders rationed: `unknown:*` + `placeholder` prop; hygiene pass resolves. (§3.2.5)
9. Every node has `sources`; every edge has content-derived `id`, `source`, `recorded`; source = named-graph key; tombstones over deletes. (§3.3)
10. OWA outside the manifest's declared scope; UNA inside your namespace. (§3.1.1, §4.1.1)
11. Inference by query-time closure over schema flags; materialised inferences are marked, regenerable cache. (§4.2)
