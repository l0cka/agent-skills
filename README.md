# Agent skills and plugins

Canonical source repository for custom skills and plugins shared by Codex and
Claude Code.

Plugin-backed skills live once inside their plugin. Compatibility symlinks under
`skills/` preserve standalone installation for older clients, while marketplace
installs provide the skill suite, MCP tools, and hooks as one versioned unit.

Public repository: [github.com/l0cka/agent-skills](https://github.com/l0cka/agent-skills)

## Repository layout

```text
agent-skills/
├── .agents/plugins/marketplace.json
├── .claude-plugin/marketplace.json
├── plugins/
│   └── project-knowledge-graph/
│       ├── .codex-plugin/plugin.json
│       ├── .claude-plugin/plugin.json
│       ├── skills/
│       │   ├── setup-project-graph/
│       │   ├── model-project-graph/
│       │   ├── ingest-project-graph/
│       │   ├── query-project-graph/
│       │   ├── analyze-project-graph/
│       │   ├── validate-project-graph/
│       │   ├── refine-project-graph/
│       │   └── publish-project-graph/
│       ├── hooks/
│       ├── .mcp.json
│       └── mcp/
├── skills/                  # compatibility symlinks
├── scripts/
│   ├── sync_skills.py
│   └── validate_skills.py
├── AGENTS.md
└── skills.json
```

## Validate

```bash
python3 scripts/validate_skills.py
```

This validates every `SKILL.md` and runs bundled `test_*.py` suites.

## Install as a plugin

Add this repository as a marketplace and install the plugin independently in
each client:

```bash
codex plugin marketplace add l0cka/agent-skills
codex plugin add project-knowledge-graph@l0cka-agent-skills

claude plugin marketplace add l0cka/agent-skills
claude plugin install project-knowledge-graph@l0cka-agent-skills --scope user
```

The plugin supplies eight focused skills, a read-only local MCP server, and a bounded
`SessionStart` graph brief. Project `kg/` files remain the canonical memory;
native Codex and Claude memories remain supplementary recall layers.

Update installed releases with:

```bash
codex plugin marketplace upgrade l0cka-agent-skills
codex plugin add project-knowledge-graph@l0cka-agent-skills

claude plugin marketplace update l0cka-agent-skills
claude plugin update project-knowledge-graph@l0cka-agent-skills
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
clients that cannot install the plugin. Plugin installs are preferred because
standalone skills do not include MCP tools or hooks.

For another machine, clone this repository there and run the same validation and sync commands. Git is the cross-machine transport; agent discovery directories are deployment targets, not source repositories.

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
