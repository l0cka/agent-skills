---
name: docs-sweep
description: Audit and update project-wide documentation against current repository evidence, apply ASD-STE100 Simplified Technical English to human-facing prose, and keep changed documentation sources synchronized with an existing project knowledge graph. Use when a user invokes /docs-sweep, /technical-documentation:docs-sweep, or $docs-sweep; asks to refresh all docs after code or configuration changes; repairs stale READMEs, guides, examples, setup steps, API or CLI references; or checks documentation coverage across a repository. Require the STE language gate for human-facing docs and a source-scoped graph refresh when an existing graph tracks changed docs, or report the sweep as incomplete.
---

# Docs Sweep

Bring the project's human-authored documentation into evidence-backed alignment
with its current code, configuration, tests, and operating instructions.

## Operating contract

- Treat an invocation without a narrower target as a whole-project sweep.
- Follow repository instructions and preserve unrelated or in-progress changes.
- Limit edits to documentation, documentation examples, and the templates or
  generators that own generated documentation. Report product defects instead
  of changing product behavior merely to make an inaccurate document true.
- Treat refresh of changed graph-tracked documentation as part of completion.
  If you cannot refresh it safely, preserve the docs work but report the sweep
  as `PARTIAL` or `BLOCKED`, never complete.
- Apply ASD-STE100 Issue 9 to all in-scope human-facing prose. If the STE manual
  gate is incomplete or a material language issue remains unresolved, preserve
  safe edits but report the sweep as `PARTIAL` or `BLOCKED`.
- Do not commit, push, publish, or alter release history unless explicitly
  requested.
- Finish the update and proportionate verification. Do not stop after you list
  stale files.

## Workflow

### 1. Resolve the project and protect working state

1. Resolve the canonical project root and read applicable `AGENTS.md`,
   `CLAUDE.md`, contribution guidance, and local documentation conventions.
2. Inspect version-control status before editing. Preserve all unrelated user
   changes and work around overlapping changes carefully.
3. Use the user's explicit path or topic as the scope. Otherwise, sweep the
   entire active project.
4. Exclude dependencies, VCS internals, caches, build outputs, vendored trees,
   secrets, credentials, binary assets, and generated files whose source is
   elsewhere.

### 2. Build an inventory and truth map

Prefer `git ls-files` in a Git project and `rg --files` otherwise. Inventory at
least:

- Root `README*` files and the `docs/` tree.
- Setup, deployment, operations, security, support, and contribution guides.
- User-facing examples, tutorials, API or CLI references, and configuration or
  environment-variable documentation.
- Current release notes or an unreleased changelog section. Preserve historical
  release records.
- Documentation templates, generators, and doc-validation configuration.

Identify authoritative repository evidence for each surface. Evidence can
include manifests, schemas, entry points, CLI help, public interfaces, tests,
workflows, deployment configuration, or accepted decisions. Track
`surface | evidence | status | action | validation` while you work.

If a file identifies its generator, edit the source and run that generator. Do
not hand-edit generated output.

Classify each human-facing surface as procedural, descriptive, safety, note,
quoted, or machine-facing for the Simplified Technical English review.

### 3. Establish the graph baseline

If the project contains `kg/manifest.json`, read
[project-graph-integration.md](references/project-graph-integration.md) before
editing. Capture baseline graph health and identify inventory documents already
tracked by the manifest.

Use an installed Project Knowledge Graph plugin when available. The project's
own `kg/kg.py` is sufficient when it provides the required operations.
Do not mistake a read-only graph MCP server for absence of write-capable graph
skills or CLI tooling.

When no project graph exists, continue without graph work. Never initialize a
graph as a side effect of a documentation sweep.

### 4. Reconcile the documentation

Load `technical-documentation:apply-simplified-technical-english` for a plugin
install or `apply-simplified-technical-english` for a standalone install. Read
its bundled Issue 9 reference before changing human-facing prose.

1. Update primary sources before summaries or derivative guides.
2. Correct stale commands, paths, versions, options, defaults, prerequisites,
   architecture descriptions, links, and examples only when repository or
   verified external evidence supports the change.
3. Keep terminology and cross-references consistent across the full inventory.
4. Create a new document only for a material coverage gap with a clear audience
   and authoritative source. Prefer improving an existing canonical document.
5. Apply ASD-STE100 to explanatory prose, instructions, notes, and safety text.
   Preserve code, commands, identifiers, quoted text, legal wording, local
   structure, accessibility, and deliberate historical context.
6. When code and documentation conflict and the intended behavior is unclear,
   leave the disputed claim unchanged or qualify it, and report the exact gap.

### 5. Refresh the affected graph sources

After the documentation diff is stable, follow the source-scoped refresh and
baseline-delta rules in
[project-graph-integration.md](references/project-graph-integration.md).

Do not report `COMPLETE` while any changed graph-tracked document remains stale,
its refresh was not applied, or post-refresh verification is unknown. Do not
repair unrelated pre-existing graph debt merely to make the docs sweep green.

### 6. Verify the sweep

1. Run repository-provided documentation format, build, link, spelling, and
   example checks that are safe and relevant.
2. Test changed commands or snippets in a non-destructive local context when
   practical. Never exercise production writes, credentials, or destructive
   examples merely to validate documentation.
3. Run the project's proportionate general validation when documentation is
   coupled to schemas, generated output, or executable examples.
4. Run `git diff --check`, inspect the complete diff, and reread every changed
   document for contradictions, broken navigation, or unintended churn.
5. Run the Simplified Technical English checker with the correct text mode and
   complete its manual dictionary, terminology, meaning, and safety gate.
6. Apply both the STE completion status and the graph completion status. Either
   gate can prevent a complete sweep.

## Completion report

State:

- Overall status: `COMPLETE`, `COMPLETE WITH PRE-EXISTING GRAPH DEBT`,
  `PARTIAL`, or `BLOCKED`.
- Documentation surfaces changed and what now matches.
- Validation commands and results.
- STE status, text types reviewed, checker result, manual checks, and exceptions.
- Graph baseline, changed tracked sources, refresh actions, and post-refresh
  delta, or that no project graph or affected tracked source existed.
- Material gaps, ambiguous claims, or checks that could not run.

Claim that all documentation is current only after the sweep covers the full
inventory. The documentation, STE, and graph gates must also be complete. Do
not claim ASD-STE100 certification from this workflow.
