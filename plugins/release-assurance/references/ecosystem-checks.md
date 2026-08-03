# Ecosystem checks

Discover and follow repository-owned commands first. Use these checks to fill gaps, not to override a project's release policy.

## Python distributions

- Reconcile `pyproject.toml`, generated version modules, package metadata, tags, and changelog.
- Build with the repository's supported backend, commonly `python -m build`.
- Inspect both sdist and wheel contents. Run `python -m twine check dist/*` when Twine is part of the supported toolchain.
- Install the wheel in a fresh virtual environment and exercise imports, CLI entry points, packaged data, and one public behavior.
- After publication, fetch the exact version from the intended index without a local cache and repeat the smoke test.
- Confirm the distribution name is the intended package; import names and similarly named public packages can differ.

## Node packages

- Reconcile `package.json`, lockfile, generated version surfaces, tags, and changelog.
- Run repository tests and build steps, then inspect `npm pack --dry-run` or the produced tarball.
- Verify `files`, exports, entry points, types, licence, lifecycle scripts, and absence of private configuration.
- Install the tarball into a fresh temporary consumer before publishing. Fetch and test the exact registry version afterwards.

## Rust crates

- Reconcile `Cargo.toml`, lockfile policy, tags, and changelog.
- Run formatting, lint and tests required by the repository.
- Inspect `cargo package --list` and use `cargo publish --dry-run` when supported.
- Test the packaged crate rather than relying only on the workspace checkout.

## Git tags and GitHub releases

- Verify the tag name and target commit before pushing.
- Check local and remote collisions. Never force-update a public release tag as routine recovery.
- Verify release title, notes, assets, prerelease/latest intent, and asset digests where applicable.
- Open the resulting release metadata independently after creation and confirm it targets the candidate commit.

## Agent skills and plugins

- Reconcile the canonical skill directories, compatibility links, registry, Codex and Claude manifests, and both marketplace catalogs.
- Validate every skill and plugin manifest. Run bundled tests and link checks.
- Preview installation or synchronisation before applying it; preserve conflicting installed variants.
- Verify the supported install flow in a new Codex task and Claude session because existing sessions may not hot-reload.
- For this repository, run `python3 scripts/validate_skills.py` and `python3 scripts/sync_skills.py` as the minimum completion gate.

## Containers and deployed services

- Record the current version, configuration shape, health, and rollback target before deployment.
- Build or pull the exact digest. Avoid floating-tag evidence.
- Run pre-deploy health checks, apply the approved change, then verify service health, expected port or endpoint, and bounded logs.
- Keep publication of an image distinct from deployment of that image.
