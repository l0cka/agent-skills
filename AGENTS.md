# Repository instructions

This repository is the canonical source for the user's custom Codex and Claude
Code skills and dual-host plugins.

## Rules

- Store plugin-backed skills once at
  `plugins/<plugin-name>/skills/<skill-name>/`.
- Keep `skills/<skill-name>` only as a compatibility symlink to its canonical
  plugin-backed skill. Never edit through a deployed agent directory.
- Keep skill names lowercase and hyphenated; the directory and frontmatter `name` must match.
- Use the installed `skill-creator` instructions whenever creating or materially revising a skill.
- Use the installed `plugin-creator` instructions whenever creating or
  materially revising a Codex plugin.
- Keep `SKILL.md` concise and put detailed optional material in directly linked `references/`.
- Require provenance and preserve upstream attribution when importing external material.
- Never edit deployed copies under agent discovery directories as the source of truth.
- Do not overwrite a conflicting installed skill during sync.
- Update `skills.json` when adding, renaming, or versioning a skill.
- Keep shared runtime code host-neutral. Use thin `.codex-plugin` and
  `.claude-plugin` manifests when product schemas differ.
- Validate both plugin manifests and both marketplace catalogs before release.

## Completion gate

Run:

```bash
python3 scripts/validate_skills.py
python3 scripts/sync_skills.py
```

The first command must pass. The second must report only planned installs or synchronized targets, with no unexplained conflicts.
