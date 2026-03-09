# Gh Actions

## Overview

A collection of reusable GitHub Actions composite actions and reusable workflows
for CI/CD pipelines. All tool downloads use pinned versions with SHA-256 checksum
verification. The repository is consumed by 26+ downstream repos.

## Repository Structure

```text
actions/
  run-gitleaks/          # Install and run gitleaks secret scanner
  run-trufflehog/        # Install and run trufflehog secret scanner
  setup-actionlint/      # Install actionlint
  setup-golangci-lint/   # Install golangci-lint
  setup-goreleaser/      # Install GoReleaser
  setup-scrut/           # Install scrut CLI test runner
  setup-shfmt/           # Install shfmt
.github/
  workflows/
    go-ci.yml            # Reusable: Go test, lint, build, scrut, format check
    go-release.yml       # Reusable: GoReleaser release
    secret-scan.yml      # Reusable: gitleaks and/or trufflehog scanning
    text-lint.yml        # Reusable: markdownlint, Prettier, cspell, yamllint
    shell-lint.yml       # Reusable: ShellCheck and shfmt
    github-lint.yml      # Reusable: actionlint
    pages-deploy.yml     # Reusable: GitHub Pages build and deploy
    npm-publish.yml      # Reusable: npm publish to registry
    ci.yml               # Self-hosting: runs github-lint on this repo
    gitleaks.yml         # Self-hosting: runs secret-scan with gitleaks
    trufflehog.yml       # Self-hosting: runs secret-scan with trufflehog
  copilot-instructions.md
docs/plans/              # Plan documents (todo/ and done/)
```

## Key Conventions

### Composite Actions vs. Reusable Workflows

Composite actions live in `actions/` and are referenced as
`cboone/gh-actions/actions/<name>@<ref>`. Reusable workflows live in
`.github/workflows/` and are called via `workflow_call`. Workflows intentionally
duplicate tool installation logic from actions because callers in other
repositories cannot reference local composite actions.

### Naming

- `setup-*` actions install a tool and add it to `GITHUB_PATH` (install only).
- `run-*` actions install a tool and then execute it (install and run).

### SHA-256 Checksum Verification

Every tool download verifies its SHA-256 checksum against upstream-published
checksum files. The one exception is scrut, whose upstream does not publish
checksums.

### Version Pinning

All tool versions are pinned to exact patch releases (no floating versions).
The one exception is Node.js, which uses a major version string (e.g., `"22"`).

### Platform Support

Only Linux and macOS runners are supported. Each installer uses a `uname -s`
case statement with `Linux)` and `Darwin)` branches, plus a `*)` catch-all
that exits with an error. Windows is not supported.

### Shell Conventions

- Arguments from `args` inputs are split with `read -r -a` into arrays. This
  handles simple space-delimited flags; quoting and escaping are not supported.
- Inputs are passed to shell steps via `env:` mappings, not inline expressions.
- Tools are installed to `RUNNER_TEMP` and added to `GITHUB_PATH`.

## Adding a New Action

1. Create `actions/<name>/action.yml` with `using: composite`.
1. Accept a `version` input with a pinned default.
1. Detect OS and architecture with `uname -s` / `uname -m` case statements.
1. Download the tool, verify SHA-256 checksum, install to `RUNNER_TEMP`.
1. Append the install directory to `GITHUB_PATH`.
1. For `run-*` actions, add a second step that executes the tool.

## Adding a New Workflow

1. Create `.github/workflows/<name>.yml` with an `on: workflow_call` trigger.
1. Define inputs with types and defaults; keep permissions minimal.
1. Inline tool installation (do not reference local composite actions).
1. Follow the same checksum verification pattern used by existing workflows.

## Releasing

This repository has no GoReleaser config or release workflow for itself. Releases
are pure Git tags. Use the `/release` skill, which analyzes conventional commits,
recommends a version bump, updates CHANGELOG.md, creates a release commit, and
tags it locally. Then push the commit and both tags (exact + floating major).

The floating major tag (e.g., `v1`) is force-updated on each release so that
callers referencing `@v1` automatically pick up non-breaking changes. See the
README Versioning section for full details.

## Testing

The repository self-hosts its own workflows as integration tests. The `ci.yml`,
`gitleaks.yml`, and `trufflehog.yml` files call the reusable workflows from this
same repository. There is no unit test framework.

## Local Development

- `make help` lists available targets.
- `make lint` runs actionlint on workflow files.
- `make lint-md` runs markdownlint-cli2 on Markdown files.
- `make format` runs Prettier in write mode.
- `make format-check` runs Prettier in check mode.
- `make spell` runs cspell.
- `make lint-yaml` runs yamllint.
