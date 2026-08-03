<p align="center">
  <img src="assets/logo.png" alt="Agent skills logo" width="160">
</p>

# Agent skills and plugins

Canonical source repository for custom skills and plugins shared by Codex and
Claude Code.

Plugin-backed skills live in one plugin. Compatibility symlinks under `skills/`
preserve standalone installation for older clients. Marketplace installs provide
the skill suite, MCP tools, and hooks as one versioned unit.

Public repository: [github.com/l0cka/agent-skills](https://github.com/l0cka/agent-skills)

## Repository layout

```text
agent-skills/
├── assets/
│   └── logo.png
├── .agents/plugins/marketplace.json
├── .claude-plugin/marketplace.json
├── plugins/
│   ├── technical-documentation/
│   │   ├── .codex-plugin/plugin.json
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/
│   │       ├── docs-sweep/
│   │       └── apply-simplified-technical-english/
│   ├── project-knowledge-graph/
│   │   ├── .codex-plugin/plugin.json
│   │   ├── .claude-plugin/plugin.json
│   │   ├── skills/
│   │   │   ├── setup-project-graph/
│   │   │   ├── model-project-graph/
│   │   │   ├── ingest-project-graph/
│   │   │   ├── query-project-graph/
│   │   │   ├── analyze-project-graph/
│   │   │   ├── validate-project-graph/
│   │   │   ├── refine-project-graph/
│   │   │   └── publish-project-graph/
│   │   ├── hooks/
│   │   ├── .mcp.json
│   │   └── mcp/
│   ├── quantitative-trading/
│   │   ├── .codex-plugin/plugin.json
│   │   ├── .claude-plugin/plugin.json
│   │   ├── skills/              # router plus eight focused workflows
│   │   ├── references/
│   │   ├── scripts/
│   │   └── tests/
│   └── release-assurance/
│       ├── .codex-plugin/plugin.json
│       ├── .claude-plugin/plugin.json
│       ├── skills/              # router plus four focused workflows
│       ├── references/
│       ├── scripts/
│       └── tests/
├── skills/                  # compatibility symlinks
├── scripts/
│   ├── sync_skills.py
│   └── validate_skills.py
├── AGENTS.md
└── skills.json
```

## Brand assets

Current brand assets:

- Repository: [assets/logo.png](assets/logo.png)
- Project Knowledge Graph: [plugins/project-knowledge-graph/assets/logo.png](plugins/project-knowledge-graph/assets/logo.png)
- Quantitative Trading: [plugins/quantitative-trading/assets/logo.png](plugins/quantitative-trading/assets/logo.png)
- Technical Documentation: [plugins/technical-documentation/assets/logo.png](plugins/technical-documentation/assets/logo.png)

## Validate

```bash
python3 scripts/validate_skills.py
```

This validates every `SKILL.md` and runs bundled `test_*.py` suites.

## Install as a plugin

Add this repository as a marketplace. Install the plugin independently in each
client:

```bash
codex plugin marketplace add l0cka/agent-skills
codex plugin add technical-documentation@l0cka-agent-skills
codex plugin add project-knowledge-graph@l0cka-agent-skills
codex plugin add quantitative-trading@l0cka-agent-skills
codex plugin add release-assurance@l0cka-agent-skills

claude plugin marketplace add l0cka/agent-skills
claude plugin install technical-documentation@l0cka-agent-skills --scope user
claude plugin install project-knowledge-graph@l0cka-agent-skills --scope user
claude plugin install quantitative-trading@l0cka-agent-skills --scope user
claude plugin install release-assurance@l0cka-agent-skills --scope user
```

The Technical Documentation plugin supplies the `docs-sweep` project-wide
maintenance workflow and a focused ASD-STE100 Simplified Technical English
workflow. The main sweep inventories documentation and reconciles it against
repository evidence. It applies STE Issue 9 to human-facing prose and validates
the changes. It also refreshes changed sources that an existing Project
Knowledge Graph tracks. An incomplete STE gate or a blocked graph refresh
prevents a complete result.

Invoke the main skill as
`/docs-sweep` in Claude Code or `$docs-sweep` in Codex. Invoke the focused skill
as `/apply-simplified-technical-english` or
`$apply-simplified-technical-english`. Claude Code namespaces the plugin forms
as `/technical-documentation:docs-sweep` and
`/technical-documentation:apply-simplified-technical-english`.

The knowledge-graph plugin supplies eight focused skills, a read-only local MCP
server, and a bounded `SessionStart` graph brief. The quantitative-trading
plugin supplies a governing router and eight focused workflows. These workflows
cover execution design, transaction costs, market impact, model validation,
volume, execution risk, schedule optimization, and cost-aware portfolios. Its
published-method provenance is explicit. Optional QuantEcon references remain
commit-pinned.

The Release Assurance plugin supplies a governing router and four focused
workflows. It fixes release scope and gates, verifies the exact candidate and
built artifact, publishes only with scoped authority, proves each destination
from the consumer side, and retires superseded projects without treating
archival as deletion. Its offline preflight helper checks Git state, local tag
collisions, and supported version metadata without publishing anything.

To update installed releases, run:

```bash
codex plugin marketplace upgrade l0cka-agent-skills
codex plugin add technical-documentation@l0cka-agent-skills
codex plugin add project-knowledge-graph@l0cka-agent-skills
codex plugin add quantitative-trading@l0cka-agent-skills
codex plugin add release-assurance@l0cka-agent-skills

claude plugin marketplace update l0cka-agent-skills
claude plugin update technical-documentation@l0cka-agent-skills
claude plugin update project-knowledge-graph@l0cka-agent-skills
claude plugin update quantitative-trading@l0cka-agent-skills
claude plugin update release-assurance@l0cka-agent-skills
```

## Standalone skill compatibility

Preview:

```bash
python3 scripts/sync_skills.py
```

Install symlinks into `~/.codex/skills` and `~/.claude/skills`:

```bash
python3 scripts/sync_skills.py --apply
```

The sync refuses to overwrite an existing directory or a link to another
source. Resolve that conflict deliberately, then rerun. Use this route only for
clients that cannot install the plugin. Prefer plugin installs because
standalone skills do not include MCP tools or hooks.

For another machine, clone this repository there and run the same validation
and sync commands. Git is the cross-machine transport. Agent discovery
directories are deployment targets, not source repositories.

```bash
git clone https://github.com/l0cka/agent-skills.git
cd agent-skills
python3 scripts/validate_skills.py
python3 scripts/sync_skills.py --apply
```

## Add a skill

1. Create or select a plugin under `plugins/<plugin-name>/`.
2. Create `plugins/<plugin-name>/skills/<lowercase-hyphen-name>/SKILL.md`
   with only `name` and `description` in frontmatter.
3. Add a compatibility symlink under `skills/` if standalone installation is
   still supported.
4. Put deterministic tools in `scripts/`, on-demand guidance in `references/`,
   and output resources in `assets/`.
5. Add `agents/openai.yaml` for Codex UI metadata.
6. Add or update the entry in `skills.json` and both marketplace catalogs.
7. Run `python3 scripts/validate_skills.py`.
8. Commit the canonical plugin and update each installed marketplace.

Do not maintain separate Codex and Claude copies in this repository.
