<p align="center">
  <img src="assets/logo.png" alt="Agent skills logo" width="160">
</p>

# Agent skills and plugins

Canonical source repository for custom skills and plugins shared by Codex and
Claude Code.

Every skill lives exactly once, inside the plugin that owns it. Four plugins
currently ship 25 skills. Compatibility symlinks under `skills/` preserve
standalone installation for older clients. Marketplace installs provide each
plugin's skill suite, MCP tools, and hooks as one versioned unit.

Public repository: [github.com/l0cka/agent-skills](https://github.com/l0cka/agent-skills)

## Repository layout

```text
agent-skills/
├── assets/
│   └── logo.png
├── .agents/plugins/marketplace.json
├── .claude-plugin/marketplace.json
├── plugins/
│   ├── technical-documentation/     # 3 skills
│   │   ├── .codex-plugin/plugin.json
│   │   ├── .claude-plugin/plugin.json
│   │   ├── skills/
│   │   │   ├── docs-sweep/
│   │   │   ├── review-project-maintenance/
│   │   │   └── apply-simplified-technical-english/
│   │   ├── assets/
│   │   ├── tests/
│   │   └── README.md
│   ├── project-knowledge-graph/     # 8 skills
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
│   │   ├── .mcp.json
│   │   ├── mcp/
│   │   ├── lib/
│   │   ├── hooks/
│   │   ├── assets/
│   │   ├── tests/
│   │   └── README.md
│   ├── quantitative-trading/        # router plus 8 focused workflows
│   │   ├── .codex-plugin/plugin.json
│   │   ├── .claude-plugin/plugin.json
│   │   ├── skills/
│   │   ├── references/
│   │   ├── scripts/
│   │   ├── assets/
│   │   ├── tests/
│   │   └── README.md
│   └── release-assurance/           # router plus 4 focused workflows
│       ├── .codex-plugin/plugin.json
│       ├── .claude-plugin/plugin.json
│       ├── skills/
│       ├── references/
│       ├── scripts/
│       ├── tests/
│       └── README.md
├── skills/                  # compatibility symlinks, one per skill
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

The Technical Documentation plugin supplies an approval-gated project
maintenance review, the `docs-sweep` project-wide documentation workflow, and
a focused ASD-STE100 Simplified Technical English workflow. The maintenance
review finds evidence-backed stale documentation and technical debt. It
presents bounded proposal IDs and does not edit until the user approves `ALL`
or named IDs. The documentation sweep applies STE Issue 9. It also refreshes
changed sources that an existing Project Knowledge Graph tracks. An incomplete
STE gate or a blocked graph refresh prevents a complete documentation result.

Invoke the approval-gated review as `/review-project-maintenance` in Claude
Code or `$review-project-maintenance` in Codex. Invoke the documentation skills
as `/docs-sweep`, `$docs-sweep`, `/apply-simplified-technical-english`, or
`$apply-simplified-technical-english`. Claude Code namespaces the plugin forms
under `/technical-documentation:`.

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
3. Add `agents/openai.yaml` beside `SKILL.md` for Codex UI metadata.
4. Put deterministic tools in `scripts/`, on-demand guidance in `references/`,
   and output resources in `assets/`.
5. Add a compatibility symlink under `skills/` if standalone installation is
   still supported.
6. Cover any bundled script with a `test_*.py` suite under the plugin's
   `tests/`. `validate_skills.py` discovers and runs these.
7. Bump the plugin version in both `.claude-plugin/plugin.json` and
   `.codex-plugin/plugin.json`, then mirror it into `skills.json`
   (`plugin_version`) and `.claude-plugin/marketplace.json`. Register the skill
   itself in `skills.json` and, for a new plugin, in both marketplace catalogs.
8. Update the plugin's `README.md` and this file's skill counts.
9. Run `python3 scripts/validate_skills.py` and `python3 scripts/sync_skills.py`.
10. Commit the canonical plugin and update each installed marketplace.

Do not maintain separate Codex and Claude copies in this repository.
