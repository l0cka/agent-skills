---
name: docs-sweep
description: Audit and update project-wide documentation against current repository evidence, and keep changed documentation sources synchronized with an existing project knowledge graph. Use when a user invokes /docs-sweep, /docs-sweep:docs-sweep, or $docs-sweep; asks to refresh all docs after code or configuration changes; repairs stale READMEs, guides, examples, setup steps, API or CLI references; or checks documentation coverage across a repository. When an existing graph tracks changed docs, require a source-scoped graph refresh or report the sweep as incomplete.
---

# Docs Sweep

Bring the project's human-authored documentation into evidence-backed alignment
with its current code, configuration, tests, and operating instructions.

## Operating contract

- Treat an invocation without a narrower target as a whole-project sweep.
- Follow repository instructions and preserve unrelated or in-progress changes.
- Limit edits to documentation, documentation examples, and the templates or
  generators that own generated documentation. Report product defects instead
  of changing product behaviour merely to make an inaccurate document true.
- Treat refresh of changed graph-tracked documentation as part of completion.
  If it cannot be refreshed safely, preserve the docs work but report the sweep
  as `PARTIAL` or `BLOCKED`, never complete.
- Do not commit, push, publish, or alter release history unless explicitly
  requested.
- Finish the update and proportionate verification; do not stop after listing
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

- root `README*` files and the `docs/` tree;
- setup, deployment, operations, security, support, and contribution guides;
- user-facing examples, tutorials, API or CLI references, and configuration or
  environment-variable documentation;
- current release notes or an unreleased changelog section; preserve historical
  release records;
- documentation templates, generators, and doc-validation configuration.

For each surface, identify its authoritative repository evidence: manifests,
configuration schemas, executable entry points, CLI help, routes and public
interfaces, tests, workflows, deployment configuration, or accepted decisions.
Track `surface | evidence | status | action | validation` while working.

If a file declares that it is generated, edit its source and run the supported
generator. Do not hand-edit generated output.

### 3. Establish the graph baseline

If the project contains `kg/manifest.json`, read
[project-graph-integration.md](references/project-graph-integration.md) before
editing. Capture baseline graph health and identify inventory documents already
tracked by the manifest.

Use an installed Project Knowledge Graph plugin when available, but do not
require it when the project's own `kg/kg.py` provides the required operations.
Do not mistake a read-only graph MCP server for absence of write-capable graph
skills or CLI tooling.

When no project graph exists, continue without graph work. Never initialize a
graph as a side effect of a documentation sweep.

### 4. Reconcile the documentation

1. Update primary sources before summaries or derivative guides.
2. Correct stale commands, paths, versions, options, defaults, prerequisites,
   architecture descriptions, links, and examples only when repository or
   verified external evidence supports the change.
3. Keep terminology and cross-references consistent across the full inventory.
4. Create a new document only for a material coverage gap with a clear audience
   and authoritative source. Prefer improving an existing canonical document.
5. Preserve local voice, structure, accessibility, and deliberate historical
   context. Avoid mass reformatting or unrelated copy-editing.
6. When code and documentation conflict and the intended behaviour is unclear,
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
5. Apply the graph completion status defined in the graph integration reference.

## Completion report

State:

- overall status: `COMPLETE`, `COMPLETE WITH PRE-EXISTING GRAPH DEBT`,
  `PARTIAL`, or `BLOCKED`;
- documentation surfaces changed and what now matches;
- validation commands and results;
- graph baseline, changed tracked sources, refresh actions, and post-refresh
  delta, or that no project graph or affected tracked source existed;
- material gaps, ambiguous claims, or checks that could not run.

Do not claim that all documentation is current unless the inventory was covered
and the relevant documentation and graph gates completed.
