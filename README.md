# GitHub Actions

A collection of reusable GitHub Actions composite actions and reusable
workflows for CI/CD pipelines, in active use across 26+ downstream repos.
Every tool download is pinned to an exact version and verified against an
SHA-256 (or sha512, for npm) checksum, with no reliance on third-party
registries as the sole integrity boundary.

Composite actions live under `actions/<name>/`. Reusable workflows live
under `.github/workflows/<name>.yml`. Each component's full reference docs
(description, inputs, outputs, usage examples) are linked from the Quick
Reference table below.

## Quick reference

Each row links to the per-component doc with full inputs, outputs, and
usage examples.

### Linting and formatting

| Component                                                                  | Type     | What it does                                                |
| -------------------------------------------------------------------------- | -------- | ----------------------------------------------------------- |
| [lint-text](docs/workflows/lint-text.md)                                   | workflow | markdownlint, Prettier, cspell, yamllint                    |
| [lint-shell](docs/workflows/lint-shell.md)                                 | workflow | ShellCheck and shfmt                                        |
| [lint-github-actions](docs/workflows/lint-github-actions.md)               | workflow | actionlint on workflow files                                |
| [run-cspell](actions/run-cspell/README.md)                                 | action   | cspell with PR annotations                                  |
| [run-reuse](actions/run-reuse/README.md)                                   | action   | REUSE/SPDX compliance                                       |
| [set-up-shfmt](actions/set-up-shfmt/README.md)                             | action   | install shfmt                                               |
| [set-up-actionlint](actions/set-up-actionlint/README.md)                   | action   | install actionlint                                          |
| [set-up-golangci-lint](actions/set-up-golangci-lint/README.md)             | action   | install golangci-lint                                       |

### Testing and CI

| Component                                                  | Type     | What it does                                              |
| ---------------------------------------------------------- | -------- | --------------------------------------------------------- |
| [run-go-ci](docs/workflows/run-go-ci.md)                   | workflow | Go test, lint, build, scrut, format check                 |
| [run-rust-ci](docs/workflows/run-rust-ci.md)               | workflow | Rust test, clippy, fmt, deny, audit, typos                |
| [run-zig-ci](docs/workflows/run-zig-ci.md)                 | workflow | Zig test, format, build, cross-compile, scrut             |
| [run-scrut-tests](docs/workflows/run-scrut-tests.md)       | workflow | scrut CLI snapshot tests for non-Go projects              |
| [set-up-scrut](actions/set-up-scrut/README.md)             | action   | install scrut CLI test runner                             |

### Releasing and publishing

| Component                                                                              | Type     | What it does                                            |
| -------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------- |
| [create-gh-release](actions/create-gh-release/README.md)                               | action   | create a GitHub Release with `gh`                       |
| [create-gh-release-from-changelog](docs/workflows/create-gh-release-from-changelog.md) | workflow | release notes extracted from a Keep-a-Changelog file    |
| [release-go-binaries](docs/workflows/release-go-binaries.md)                           | workflow | GoReleaser build and publish                            |
| [release-rust-binaries](docs/workflows/release-rust-binaries.md)                       | workflow | Rust matrix build, optional Homebrew formula update     |
| [release-zig-binaries](docs/workflows/release-zig-binaries.md)                         | workflow | Zig cross-compile from a single runner, GitHub Release  |
| [publish-to-npm](docs/workflows/publish-to-npm.md)                                     | workflow | publish an npm package to a registry                    |
| [set-up-goreleaser](actions/set-up-goreleaser/README.md)                               | action   | install GoReleaser                                      |

### Security and supply chain

| Component                                                  | Type     | What it does                                  |
| ---------------------------------------------------------- | -------- | --------------------------------------------- |
| [scan-for-secrets](docs/workflows/scan-for-secrets.md)     | workflow | gitleaks and/or trufflehog scanning           |
| [run-gitleaks](actions/run-gitleaks/README.md)             | action   | install gitleaks and run a scan               |
| [run-trufflehog](actions/run-trufflehog/README.md)         | action   | install trufflehog and run a scan             |
| [analyze-with-codeql](docs/workflows/analyze-with-codeql.md) | workflow | GitHub CodeQL security analysis             |

### Repository chores

| Component                                                  | Type     | What it does                                              |
| ---------------------------------------------------------- | -------- | --------------------------------------------------------- |
| [create-pull-request](actions/create-pull-request/README.md) | action  | SHA-pinned wrapper for peter-evans/create-pull-request    |
| [deploy-to-pages](docs/workflows/deploy-to-pages.md)       | workflow | build a static site and deploy to GitHub Pages            |
| [run-markscribe](actions/run-markscribe/README.md)         | action   | generate a file from a Go template (e.g. README rendering) |

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
