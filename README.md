# GitHub Actions

There are many, these are mine.

Per-component reference docs are linked from the Quick Reference table
(coming next). Composite actions live at `actions/<name>/README.md`;
reusable workflows live at `docs/workflows/<name>.md`.

## Migration

See [docs/migrations/v3.md](docs/migrations/v3.md) for the v3 path renames.

## Versioning

This project uses [Semantic Versioning](https://semver.org/) with exact version
tags. Pin to a specific version (e.g., `@v3.0.0`) for production use.

### Version bumps

- **Patch** (e.g., v2.1.3 to v2.1.4): bug fixes, tool version bumps that do not
  change behavior, documentation updates.
- **Minor** (e.g., v2.1.1 to v2.2.0): new optional inputs, new actions or
  workflows, additive changes that do not affect existing callers.
- **Major** (e.g., v2.2.0 to v3.0.0): breaking changes. A **breaking change** is any
  modification that requires callers to update their workflow files: renaming or
  removing an input, changing a default in a way that alters behavior, or
  removing an action or workflow.

### Release process

Releases are created with the `/release` skill, which analyzes conventional
commits, recommends a version bump, updates CHANGELOG.md, creates a release
commit, and tags it. The recommended outcome for each release is a single
exact version tag (e.g., `v3.0.0`) pointing to the release commit.

After tagging locally, push:

```bash
git push origin main v3.0.0
```

### Pinning for callers

Always pin to an exact release tag (e.g. `@v3.0.0`). Branch refs like
`@main` are not supported: they float, they bypass our SHA-pin and
checksum contract, and the supply-chain risk is not worth the
convenience.

## License

[MIT License](./LICENSE). TL;DR: Do whatever you want with this software, just
keep the copyright notice included. The authors aren't liable if something goes
wrong.
