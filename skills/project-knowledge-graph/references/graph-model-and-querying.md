# Graph model & querying — distilled from Hogan et al., *Knowledge Graphs* (2021), ch. 1–2

Read this when: deciding how to model something unusual (n-ary facts, edge annotations, multiple sources), or when you need query capabilities beyond what `kg.py`'s built-in commands offer and want the underlying theory.

## 1. What a knowledge graph is (§1)

**Working definition:** *"a graph of data intended to accumulate and convey knowledge of the real world, whose nodes represent entities of interest and whose edges represent relations between these entities."*

- **Data graph**: the underlying graph of data. The KG = data graph + explicit knowledge layered on it (schema, identity, context).
- **Knowledge** comes in two kinds: **simple statements** ("auth depends on db") — stored directly as edges; **quantified statements** ("all modules are files") — need schema/rules.
- Because KGs are assembled from many diverse sources, three cross-cutting concerns matter: **schema** (structure), **identity** (which nodes refer to the same entity), **context** (when/where/per-whom a fact holds).
- A project KG is a tiny **enterprise knowledge graph**: "an ever-evolving shared substrate of knowledge" — here, shared between agent sessions and tools.

**When graph abstraction beats tables/trees:**
- Relational tables force an *upfront schema* that breaks on real data (multiple names, unknown dates). Decomposing into binary relations with minimal multiplicity assumptions *is already a graph*. Graphs let you assert any binary relation between any pair of entities at any time; schema can evolve later.
- Trees (XML/JSON) force a hierarchy (is `venue` parent, child, or sibling of `type`?) and cannot naturally represent or query **cycles** (import cycles, circular references between docs).
- **Incomplete knowledge is natural**: missing information = omitted edge. No NULLs. Absence of an edge means *unknown*, not false.
- Graph query languages add **navigational operators** (arbitrary-length path traversal, reachability) on top of relational ones — the killer feature over both SQL and document stores.

## 2. Graph data models compared (§2.1)

### Directed edge-labelled graph ("del graph", §2.1.1)
- Nodes + directed labelled edges; each edge is a **triple** `(subject, predicate, object)`. Also called a **multi-relational graph**. RDF is the standardised form (IRIs, literals, blank nodes).
- Set-friendly: a del graph is a set of triples, while a governed project graph stores a set of **source-scoped assertions**. Merge on `(from, relation, to, source, anchor)` so corroborating sources survive; deduplicate triples only in query/display results.

### Heterogeneous graph (§2.1.2)
- Every node/edge has **exactly one type** baked into the model. Clean for ML, but cannot express a node with zero or multiple types — too rigid for an evolving project KG. Keep types as data (a `type` field or edge), not as a structural constraint.

### Property graph (§2.1.3)
- Nodes AND edges are first-class objects with ids, labels, and **property–value pairs**. Motivation: annotating an edge (who says so, since when) without remodelling.
- Book's verdict: del graphs and property graphs are inter-convertible; "the choice of model will often be secondary to other practical factors."

**Our format is a pragmatic hybrid**: del-graph core (`from`, `rel`, `to` — pattern matching runs over these three only) with property-graph annotations (each edge has an `id` and metadata fields for provenance). This buys automatic mergeability AND per-edge context.

### Graph dataset / named graphs (§2.1.4)
- A **graph dataset** = multiple **named graphs** + a default graph. Why: refresh/trust each *source* independently; node IDs shared across graphs denote the same entity, so querying the union integrates them.
- Our version: the `source` field on every edge acts as a named-graph key — staged refresh replaces exactly the assertions recorded from it. Node `sources` provide existence/attribute provenance. The manifest is the default graph (metadata about sources).

### Graph stores (§2.1.6)
- Three classic layouts map to file layouts: **triple table** (one file of all edges — our `edges.jsonl`), **vertical partitioning** (one file per relation), **property tables** (one file per type). Adjacency indexes are rebuildable caches. At project scale, one JSONL pair + in-memory indexes (what `kg.py` builds on load) is enough.

## 3. Query capabilities (§2.2)

Under SPARQL/Cypher/Gremlin sit common primitives. `kg.py query` implements the useful core; know the theory so you can compose them.

### Basic graph patterns (§2.2.1)
- A pattern mirrors the data model but allows **variables** in any position: `?x depends_on ?y`. Evaluation finds every **mapping** of variables to constants such that the substituted pattern is a subgraph of the data. Output is **a table** (one column per variable, one row per match).
- Multiple patterns sharing a variable = **natural join** on that variable. `kg.py` uses homomorphism semantics (distinct variables may bind the same constant) — the simpler, more general choice.

### Complex graph patterns (§2.2.2)
Relational algebra over pattern results: **projection** (choose output variables), **selection/filters**, **union**, **difference/anti-join** ("...NOT in Santiago" — negation-as-failure), **join**, and crucially **optional (left-join)**: return a property *where available* without excluding entities that lack it. Essential under incomplete data — never let asking for a field silently drop entities missing it. Default to set semantics (DISTINCT).

### Navigational graph patterns (§2.2.3)
- **Path expressions**: regexes over edge labels — concatenation, disjunction `|`, **Kleene star** `*` / plus `+` (transitive closure), **inverse** `⁻` (traverse backwards).
- **Regular path query**: `(Arica, bus*, ?city)` = reachability, the capability tables fundamentally lack. In `kg.py`: `rel+` in a query pattern, and the `path`/`neighbors --depth` commands.
- **Cycle problem**: with cycles, infinitely many paths match. Return the **finite set of endpoint pairs** (SPARQL 1.1 semantics — cheapest, the default) or **shortest paths** when the route itself matters. Never enumerate all paths.

### Other features & interfaces (§2.2.4–2.2.5)
- **Aggregation** (counts per relation, node degree) powers maintenance: dangling nodes, over-connected hubs.
- Interaction patterns that transfer to agents: **faceted browsing** (search → inspect facets of results → restrict); **navigation-based question answering** (match question terms to nodes, then walk edges whose labels match the question intent). This is exactly how to answer user questions from the graph: `find` → `show` → `neighbors`/`path`.

## 4. Recommendations distilled

1. Core model: directed labelled assertions as JSONL; merge on assertion identity and deduplicate triples for display. (§2.1.1)
2. No upfront schema; missing field = missing edge, never null. (§1, §2.1)
3. Types are data (`type` field), not structure — nodes may gain types over time. (§2.1.2)
4. Stable opaque-ish IDs + human labels/aliases as data. (§2.1.1)
5. Edge annotations (provenance, dates, confidence) as property-graph-style fields; pattern matching stays over from/rel/to. (§2.1.3)
6. `source` field = named-graph key; refresh per-source independently. (§2.1.4)
7. Query tier: triple patterns + joins + filters + optional; navigation tier: reachability with endpoint-pair semantics + shortest path. (§2.2)
8. Answer questions navigation-style: locate entities by label/alias, then traverse. (§2.2.5)
