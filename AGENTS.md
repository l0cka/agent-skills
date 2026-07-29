# Repository instructions

This repository is the canonical source for the user's custom Codex and Claude Code skills.

## Rules

- Store each skill once at `skills/<skill-name>/`.
- Keep skill names lowercase and hyphenated; the directory and frontmatter `name` must match.
- Use the installed `skill-creator` instructions whenever creating or materially revising a skill.
- Keep `SKILL.md` concise and put detailed optional material in directly linked `references/`.
- Require provenance and preserve upstream attribution when importing external material.
- Never edit deployed copies under agent discovery directories as the source of truth.
- Do not overwrite a conflicting installed skill during sync.
- Update `skills.json` when adding, renaming, or versioning a skill.

## Completion gate

Run:

```bash
python3 scripts/validate_skills.py
python3 scripts/sync_skills.py
```

The first command must pass. The second must report only planned installs or synchronized targets, with no unexplained conflicts.
