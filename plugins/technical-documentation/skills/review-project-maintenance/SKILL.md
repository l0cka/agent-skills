---
name: review-project-maintenance
description: Review a software project for stale or missing documentation and evidence-backed technical debt, present a prioritized change proposal, wait for explicit approval, and apply only the approved items with verification. Use when a user asks for a project health check, maintainability audit, documentation and codebase review, technical-debt backlog, cleanup recommendations, or a review-then-fix workflow where edits must not begin before approval.
---

# Review Project Maintenance

Use two separate phases: `REVIEWED_AWAITING_APPROVAL`, then `APPLIED_VERIFIED`.
Never merge the phases merely because the initial request also says to fix the
findings.

## Operating contract

- Follow repository instructions and protect unrelated or in-progress changes.
- Default to both documentation and technical debt. Honor a narrower scope.
- Keep the review read-only. Do not edit files, install or update dependencies,
  run formatters, create a plan file, or change external state before approval.
- Require explicit approval of `ALL` proposed items or named proposal IDs.
  Silence, interest, or a request to explain a proposal is not approval.
- Apply only approved items. New or materially expanded work requires a new
  proposal and approval.
- Confirm again immediately before destructive changes, migrations, force
  operations, public API breaks, or irreversible external actions.
- Do not commit, push, publish, open pull requests, or create external tickets
  unless the user explicitly requests that action.

Read [review-rubric.md](references/review-rubric.md) before assigning severity,
confidence, or priority.

## Phase 1: review and propose

### 1. Resolve scope and working state

1. Resolve the canonical project root and applicable `AGENTS.md`, `CLAUDE.md`,
   contribution guidance, and local conventions.
2. Inspect version-control status. Record pre-existing changes and do not treat
   them as debt without supporting evidence.
3. Exclude VCS internals, dependencies, caches, build output, generated files,
   vendored code, secrets, credentials, and binary assets unless the user puts
   them in scope.

### 2. Build an evidence map

Use `git ls-files` in a Git project and `rg --files` otherwise. Review the
smallest authoritative surfaces that can prove or disprove a finding:

- Documentation, examples, changelogs, runbooks, configuration references,
  and their generators.
- Manifests, lockfiles, schemas, public interfaces, entry points, and current
  runtime configuration.
- Tests, coverage configuration, linters, type checks, build workflows, and
  existing maintenance automation.
- Recent repository history when it explains intentional compatibility code or
  a migration already in progress.

Run only safe diagnostics that do not modify tracked files or external state.
Capture the command, result, and affected path. Use official package-manager or
registry evidence before calling a dependency outdated. Do not infer debt from
age, style preference, a `TODO`, or an unfamiliar pattern alone.

For documentation review, use `technical-documentation:docs-sweep` as a
method reference when available, but do not execute its editing phase before
approval.

### 3. Prepare the proposal

Create one proposal ID per independently approvable change: `M01`, `M02`, and
so on. Merge symptoms with one root cause. Separate changes with different risk
or rollback boundaries.

For each proposal, state:

| Field | Required content |
| --- | --- |
| Finding | One precise problem, severity, and confidence |
| Evidence | Exact paths, lines, symbols, or diagnostic results |
| Change | Intended edit and affected files; no implementation yet |
| Value and risk | Concrete benefit, likely regression surface, and non-goals |
| Verification | Commands or checks that will prove the change |
| Effort | `<15 min`, `15-60 min`, `1-4 h`, or `>4 h` |

Prioritize correctness, safety, broken user workflows, and misleading
documentation before cosmetic cleanup. Mark uncertain items `INVESTIGATE`, not
as approved fixes. Omit low-value churn.

### 4. Stop at the approval gate

Report `REVIEWED_AWAITING_APPROVAL`, the review scope, diagnostics run, and the
ranked proposal IDs. End with one direct choice:

`Approve ALL, approve selected IDs (for example M01 M03), or reject the plan.`

Do not include an edit in the same turn as this gate. If the user changes a
proposal, restate its new boundary before treating it as approved.

## Phase 2: apply approved changes

### 1. Revalidate authority and evidence

1. Identify the exact approved IDs from the conversation or a user-supplied
   saved proposal.
2. Re-read repository status and the relevant source. Stop if overlapping user
   changes make an approved edit unsafe.
3. Record excluded and deferred IDs. Do not quietly expand the set.

### 2. Implement bounded changes

Apply approved items in dependency order. Prefer root-cause fixes over patches
to derived output. Preserve public behavior unless the approved proposal says
otherwise. Edit a generator rather than generated output.

For approved documentation items, follow the `docs-sweep` evidence, language,
graph-refresh, and verification gates within the approved file and claim scope.
For approved code debt, add or adjust regression tests where proportionate.

If implementation reveals a new file, migration, dependency update, destructive
step, public API change, or materially larger diff, stop that item and request
supplemental approval. Continue other independent approved items when safe.

### 3. Verify and report

Run the proposal's checks plus relevant repository validation. Inspect the full
diff and run `git diff --check` in Git projects. Confirm that pre-existing
unrelated changes remain intact.

Report:

- Status: `APPLIED_VERIFIED`, `APPLIED_PARTIAL`, or `BLOCKED`.
- Approved IDs applied, skipped, or blocked, with affected files.
- Validation commands and results.
- Any scope change that received supplemental approval.
- Remaining proposed or investigated debt without implying it was fixed.

Claim completion only when every applied ID has current verification. A clean
test run does not prove an unapproved or deferred proposal was completed.
