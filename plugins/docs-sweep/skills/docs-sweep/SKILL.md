---
name: docs-sweep
description: Audit and update project-wide documentation against current repository evidence. Use when a user invokes /docs-sweep, /docs-sweep:docs-sweep, or $docs-sweep; asks to refresh all docs after code or configuration changes; repairs stale READMEs, guides, examples, setup steps, API or CLI references; or checks documentation coverage across a repository. Integrate with an existing Project Knowledge Graph installation when present without requiring it.
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

### 3. Use an existing project graph when available

If the project contains `kg/manifest.json` or the Project Knowledge Graph skills
or `kg_*` tools are available, read
[project-graph-integration.md](references/project-graph-integration.md) and
follow its optional integration path.

Continue normally when the graph plugin or a project graph is absent. Never
initialize a graph as a side effect of a documentation sweep.

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

### 5. Verify the sweep

1. Run repository-provided documentation format, build, link, spelling, and
   example checks that are safe and relevant.
2. Test changed commands or snippets in a non-destructive local context when
   practical. Never exercise production writes, credentials, or destructive
   examples merely to validate documentation.
3. Run the project's proportionate general validation when documentation is
   coupled to schemas, generated output, or executable examples.
4. Run `git diff --check`, inspect the complete diff, and reread every changed
   document for contradictions, broken navigation, or unintended churn.
5. If an existing graph was refreshed, require strict graph validation and its
   competency tests to pass before calling that refresh healthy.

## Completion report

State:

- documentation surfaces changed and what now matches;
- validation commands and results;
- material gaps, ambiguous claims, or checks that could not run;
- graph queries or refreshes performed, or that graph integration was not
  applicable.

Do not claim that all documentation is current unless the inventory was covered
and the relevant checks completed.
