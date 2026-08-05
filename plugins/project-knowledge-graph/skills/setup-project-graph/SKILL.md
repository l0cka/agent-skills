---
name: setup-project-graph
description: Scope, design, initialize, and wire a governed project knowledge graph stored as committable JSONL. Use when Codex or Claude needs to create a new kg/ directory, decide whether a graph is appropriate, define the project boundary and competency questions, choose a generic or research lifecycle profile, seed the schema, establish source exclusions, or add graph instructions to AGENTS.md or CLAUDE.md.
---

# Setup Project Graph

Create the smallest graph that can answer agreed project questions. Treat setup
as a contract, not a corpus-wide extraction exercise.

Read [foundations.md](references/foundations.md) before choosing the boundary or
architecture. Read [lifecycle-profiles.md](references/lifecycle-profiles.md) when
the project involves research, strategy, operations, architecture, or runtime
observations.

## Workflow

1. Resolve the canonical project root.
2. Define the graph's purpose, audience, exclusions, and 2-5 competency
   questions.
3. Inventory candidate sources. Prefer canonical, dense sources and record known
   coverage gaps.
4. Exclude secrets, credentials, `.env*`, keys, VCS internals, dependencies,
   generated artifacts, binaries, caches, and runtime state unless explicitly
   scoped.
5. Initialize:

```bash
python3 <skill-root>/scripts/kg.py --kg <project>/kg init \
  --project "<name>" --profile generic
```

`<skill-root>` is this skill's own directory. Under Claude Code it resolves to
`${CLAUDE_PLUGIN_ROOT}/skills/setup-project-graph`.

Use `--profile research` only when Experiment, Gate, Decision, Lesson, and
Strategy lifecycles are central. `init` copies the dependency-free tool into
`kg/kg.py`.

6. Use the `model-project-graph` skill to curate `schema.json`. Do not accept a
   broad default vocabulary without reviewing it against the competency
   questions.
7. Use the `ingest-project-graph` skill to build the initial core source by
   source.
8. Use the `validate-project-graph` skill as the completion gate.

## Required output

The graph lives at `<project>/kg/`:

| File | Contract |
|---|---|
| `nodes.jsonl` | Stable entities with node-level provenance |
| `edges.jsonl` | Source-scoped relationship assertions |
| `schema.json` | Vocabulary, shapes, and executable competency questions |
| `manifest.json` | Source hashes and graph/schema/tool metadata |
| `kg.py` | Self-contained governance and query tool |
| `README.md` | Instructions for agents without the plugin |

Add a concise project instruction:

```markdown
## Knowledge graph
This project has a governed graph at `kg/`. Query it before broad exploration,
cite assertion sources, and treat missing assertions as unknown. After durable
source changes, refresh affected assertions and run `validate --strict` plus
`test-cq`.
```

Do not declare setup complete until the boundary, competency questions, source
policy, and initial schema have explicit owners or acceptance criteria.
