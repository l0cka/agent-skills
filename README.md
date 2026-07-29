# Agent skills

Canonical source repository for custom skills shared by Codex and Claude Code.

Each skill lives once under `skills/<skill-name>/`. Local agent directories receive symlinks by default, so a Git pull updates both agents without duplicating skill content.

Public repository: [github.com/l0cka/agent-skills](https://github.com/l0cka/agent-skills)

## Repository layout

```text
agent-skills/
├── skills/
│   └── project-knowledge-graph/
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

## Sync to Codex and Claude Code

Preview:

```bash
python3 scripts/sync_skills.py
```

Install symlinks into `~/.codex/skills` and `~/.claude/skills`:

```bash
python3 scripts/sync_skills.py --apply
```

The sync refuses to overwrite an existing directory or a link to another source. Resolve that conflict deliberately, then rerun. Use `--mode copy` only where symlinks are unsuitable; copied installs require rerunning the command after repository updates.

For another machine, clone this repository there and run the same validation and sync commands. Git is the cross-machine transport; agent discovery directories are deployment targets, not source repositories.

```bash
git clone https://github.com/l0cka/agent-skills.git
cd agent-skills
python3 scripts/validate_skills.py
python3 scripts/sync_skills.py --apply
```

## Add a skill

1. Create `skills/<lowercase-hyphen-name>/SKILL.md` with only `name` and `description` in frontmatter.
2. Put deterministic tools in `scripts/`, on-demand guidance in `references/`, and output resources in `assets/`.
3. Add `agents/openai.yaml` for Codex UI metadata.
4. Add or update the entry in `skills.json`.
5. Run `python3 scripts/validate_skills.py`.
6. Commit the canonical skill and sync it to each local agent.

Do not maintain separate Codex and Claude copies in this repository.
