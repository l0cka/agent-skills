# Extraction, quality & refinement — distilled from Hogan et al., *Knowledge Graphs* (2021), §5.1, ch. 6–8

Read this when: extracting entities/relations from project sources (the build and update workflows), running quality checks, deduplicating, or deciding what the analytics commands mean.

The book's ML extraction pipeline translates directly to a disciplined agent reading loop — **you are the NER/EL/RE system**. Build an initial core and enrich incrementally, "pay-as-you-go".

## 1. Extraction pipeline for an agent (§6.2–6.4)

Four tasks — pre-processing, Named Entity Recognition (NER), Entity Linking (EL), Relation Extraction (RE) — run **jointly** per document (§6.2.5: joint runs mutually improve each other), not as separate passes over the corpus.

**Pre-processing (§6.2.1)**
- Resolve the canonical project root first. Exclude credentials, `.env*`, keys, wallets, VCS metadata, dependencies, caches, binaries, oversized files, and generated artifacts. Keep runtime state/logs out unless deliberately scoped with a TTL. External sources are opt-in.
- Chunk by document structure (sections, functions, classes), not fixed windows — extraction context should span a coherent unit so co-mentions are visible.
- Read markup *with* its structure (§6.3): headings name the section's protagonist; links are pre-resolved entity mentions; tables are structured data (map, don't read as prose).
- Word-sense discipline: when a term is ambiguous ("driver", "handler"), record the sense you resolved to (via which node you link), never the bare word.

**NER → what deserves a node (§6.2.2)**
- Node-worthy: named, recurrent, referable-across-files things — components/modules, people, organisations, external systems/dependencies, key decisions, domain concepts, milestones/events, significant files. NOT node-worthy: one-off values, generic nouns, anything you'd never query for. Attributes stay as properties, not nodes.
- Maintain the gazetteer: the label/alias index of existing nodes, matched against while reading. Explicit entity-worthiness rules beat vibes — rule-based NER survives because it is "controllable and predictable".
- A newly-seen entity (*emerging entity*) enters as a *candidate*; it becomes a node only after EL fails to find an existing home.

**EL → resolve before create (§6.2.3)** — the anti-duplication discipline. Two failure modes:
1. **Alias splitting** (multiple mentions, one entity — "Rapa Nui" vs "Easter Island"): creating a node per mention splits the entity's information across nodes. Fix: search ids + labels + aliases (normalised, abbreviation-aware) before creating; on match, append the new surface form to `aliases` — the index improves itself.
2. **Ambiguity** (one mention, several entities — "Santiago" ×3): gather candidates, rank by (a) **context** — co-mentioned entities boost candidates connected to them in the graph; (b) **prior** — what this mention usually means in this project; (c) **centrality** of candidates. Low confidence → create the new node but record the near-miss for the duplicate scan to revisit.

**RE → typed edges with evidence (§6.2.4)**
- Prefer the **closed setting**: a small fixed edge-type vocabulary. Free-form predicates ("has flights to") must be **aligned** to an existing edge type before writing, else the vocabulary fragments and queries miss edges. Unalignable predicates are schema-change candidates, not new edge types on the spot.
- Every node and edge carries provenance (repository path + anchor). Multiple independent sources supporting one triple remain separate assertions.
- *n-ary facts* (a decision with actors and dates; an event with time and place): promote to a node with role edges — but only when the context matters; unnecessary reification hurts conciseness (§7.4.2).

**Structured sources → map, don't read (§6.4)**
- CSV/tables (**direct mapping**, §6.4.1): one node per row (id from primary key); one edge per non-empty cell (row —column→ value); `type` edge from table name; **omit NULL/empty cells**; foreign keys link to the referenced *row node*, not the literal value — that's what makes the graph joinable. Custom-map when direct output is ugly; re-run on source change.
- JSON/XML trees (§6.4.2): never map the literal parent/child structure; write a custom mapping from the data's shape to meaningful nodes/edges.
- Prior KGs/exports (§6.4.3): import the relevant sub-graph only, then align entities and schema.

## 2. Schema: emergent + lightly curated (§6.5)

- Agile, not waterfall: schema evolves with the graph. Local additions cheap; changes to core vocabulary get a deliberate review.
- **Competency Questions (CQs)**: the natural-language questions the KG must answer ("what depends on module X?", "who decided Y and where is that recorded?"). CQs are the acceptance tests of the schema — after schema changes, check CQs remain answerable.
- Bottom-up vocabulary (§6.5.2): a recurring, domain-relevant term (*termhood*) that is cohesive as a phrase (*unithood*) earns type/edge-label status. Subclass harvesting: modifier patterns ("visitor visa" ⊑ "visa"), Hearst patterns ("X, such as Y").
- Curation pass: list types and edge labels with counts; merge near-synonyms (one property per purpose); demote 1–2-instance types; document every label.

## 3. Quality checklist (ch. 7)

Quality = *fitness for purpose*. `kg.py validate` runs the mechanical checks; the rest are review disciplines. Dimensions:

**Accuracy (§7.1)**
- *Syntactic* (§7.1.1): files parse; ids match scheme; dates ISO; edge endpoints exist (referential integrity); rels in vocabulary.
- *Semantic* (§7.1.2): facts true to their sources — spot-check a sample of edges by re-opening their `source` anchor and confirming it still supports the claim.
- *Timeliness* (§7.1.3): manifest stores each source's hash at ingest; changed hash ⇒ stale records, re-ingest. Store absolute values, never indexicals.

**Coverage (§7.2)**
- *Completeness* (§7.2.1): schema completeness (declared vocabulary actually used); property completeness (fraction of type-T nodes missing expected prop p); **population completeness** (manifest-vs-project diff = the gap list); linkability completeness (orphan scan).
- *Representativeness* (§7.2.2): bias check — is `src/` densely covered while `docs/` and decisions are barely represented?

**Coherency (§7.3)**
- *Consistency* (§7.3.1): no contradictions — functional-edge conflicts, disjoint types on one node, `same_as`+`different_from` pairs.
- *Validity* (§7.3.2): shape conformance — required props present, cardinalities respected. Shapes catch **missing** data that OWA reasoning never will.

**Succinctness (§7.4)**
- No out-of-domain junk; **no two nodes splitting one entity** (feeds the duplicate scan); no two relations serving one purpose; no stored derivables (duration when start/end exist); every node has `label` + enough `description` to disambiguate.

## 4. Refinement = maintenance routines (ch. 8)

Improve the existing graph without new sources: **completion** (find missing edges) and **correction** (fix wrong ones). All outputs are **candidates for verification against sources**, never auto-facts.

**Completion (§8.1)**
- *General link prediction*: closure rules (symmetric/inverse/transitive gaps) + **neighborhood overlap** (two nodes sharing many neighbors but no edge = candidate pair).
- *Type-link prediction* (§8.1.2): infer missing `type` from edge-label signature — propose, don't assert (the book's own example misfires).
- *Identity-link prediction* (§8.1.3) = duplicate detection. Combine **value matchers** (label/alias string similarity) with **context matchers** (neighborhood similarity — value matching alone misses "Easter Island"/"Rapa Nui"). Avoid O(n²) with **blocking**: only compare within buckets (same type + normalised name prefix). Confirmed duplicates → **consolidate**: merge edges onto the canonical node, keep the other label as alias, leave a redirect.

**Correction (§8.2)**
- *Fact validation* (§8.2.1): re-check an edge against its source anchor. Trust insight: facts backed by multiple independent sources > facts from one scratch note; maintain a source-kind trust ordering (e.g. code > docs > meeting notes) for arbitration.
- *Inconsistency repair* (§8.2.2): detecting a contradiction ≠ knowing what to remove. Remove the minimal, least-evidenced edge set that resolves it; confirm rules don't re-derive it; when unsure, flag for the user instead of deleting.

## 5. Analytics (§5.1) — what the commands mean

- **Centrality** (`important`): degree first, PageRank second — "key entities" summaries, result ranking, EL disambiguation prior.
- **Community detection** (`communities`): label propagation — clusters ≈ topics/modules; a node whose community mismatches its type is suspect.
- **Connectivity** (`orphans`): weakly connected components — disconnected islands are the linkability-incompleteness worklist.
- **Node similarity** (`similar`): shared-neighbor Jaccard — dual use: missing-link candidates and duplicate candidates.
- Labeled-graph caveat (§5.1.3): classic algorithms assume plain graphs; our commands project labels away (all edges equal). Record that assumption when reporting results.

## 6. Recommendations distilled

1. Extract jointly per document; search ids+labels+aliases before every node creation; append new surface forms to aliases. (§6.2)
2. Closed edge vocabulary; align free predicates or log as schema candidates. (§6.2.4)
3. Every record: source + anchor; manifest: source → hash. Stale = hash changed. Stage source-scoped updates, validate them, then install under the graph lock. (§7.1)
4. Manifest-vs-project diff = coverage gap list; check representativeness across project areas. (§7.2)
5. Shapes (required props) + consistency rules + orphan/duplicate/staleness scans = `validate`. (§7.3, §7.4)
6. Refinement loop: closure gaps + shared-neighbor candidates + blocked duplicate scan → verify against sources → consolidate with aliases+redirects. (§8)
7. CQs as schema acceptance tests; periodic vocabulary curation. (§6.5)
8. Trust ordering across source kinds for conflict arbitration. (§8.2.1)
