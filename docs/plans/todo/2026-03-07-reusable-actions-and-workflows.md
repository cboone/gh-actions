# Reusable Actions and Workflows for CI/CD Consolidation

## Context

Across 26 non-archived, non-fork repositories, CI/CD pipelines use 17+ third-party GitHub Actions with inconsistent versions, duplicated configuration, and unnecessary supply-chain exposure. Each third-party action is a potential attack vector and maintenance burden.

This plan centralizes common CI/CD patterns into reusable workflows and composite actions in the `gh-actions` repo, so that consuming repos can replace 50+ line workflow files with single `uses:` calls. The goals are:

1. **Security**: Eliminate third-party action dependencies where possible; install tools directly with pinned versions
2. **Simplicity**: Each consuming repo needs minimal workflow config
3. **Consistency**: Standardize versions, permissions, and patterns across all repos

---

## Action Inventory and Assessment

### Repos Surveyed (26 total, 27 repos had workflows but github-multi-desktop was excluded as a fork)

**Go projects (10):** snappy, bopca, gh-problemas, right-round, fm, crawler, stipple, xylem, quod, tracker
**Non-Go projects with workflows (16):** gh-actions, cboone-cc-plugins, compbox, homebrew-tap, cboone, snappy-sh-site, pb-bug, pbcopy2, tmux-default-bindings, claude-dotfiles, dotfiles, cboone.github.io, bopca-sh-site, tmux-binding-help, cboone-alpine-plugins, cboone-tailwind-plugins

### Third-Party Actions by Usage

| Action | Repos | Assessment |
|--------|-------|------------|
| `golangci/golangci-lint-action` | 8 | **Replace.** Just installs a binary and runs it. Direct install with pinned version is equivalent and eliminates the dependency. |
| `goreleaser/goreleaser-action` | 8 | **Replace.** Installs goreleaser and runs it. Direct install is straightforward. |
| `gitleaks/gitleaks-action` | 5 | **Replace.** Installs gitleaks binary and runs scan. Direct install eliminates the action's `pull-requests: write` permission requirement. |
| `raven-actions/actionlint` | 4 | **Replace.** Just runs actionlint. Direct binary install is trivial. |
| `rhysd/actionlint` (container) | 1 | **Replace.** Container action in gh-actions repo. Replace with binary install. |
| `trufflehog` (container) | 1 | **Replace.** Container action. Replace with binary install. |
| `codecov/codecov-action` | 1 | **Replace.** Uploads coverage file. Direct `codecov` CLI upload is equivalent. |
| `mfinelli/setup-shfmt` | 1 | **Replace.** Just installs shfmt. `go install` or binary download works. |
| `streetsidesoftware/cspell-action` | 1 | **Replace.** Just runs `npx cspell`. Inline command is identical. |
| `stefanzweifel/git-auto-commit-action` | 1 | **Replace.** Three git commands: add, commit, push. |
| `astral-sh/setup-uv` | 1 | **Replace.** Installs uv. Direct install script is equivalent. |
| `dtolnay/rust-toolchain` | 1 | **Replace.** Runs `rustup`. Direct command works. |
| `peter-evans/create-pull-request` | 1 | **Replace.** `gh pr create` is equivalent for the use case. |
| `peter-evans/repository-dispatch` | 1 | **Replace.** `gh api` call is equivalent. |
| `github/codeql-action/*` | 1 | **Keep.** Deeply integrated with GitHub's security infrastructure. No practical alternative. |
| `charmbracelet/readme-scribe` | 1 | **Keep.** Unique template engine for profile READMEs. Single use, low risk. |

### Official GitHub Actions (keep all)

`actions/checkout`, `actions/setup-go`, `actions/setup-node`, `actions/upload-artifact`, `actions/download-artifact`, `actions/upload-pages-artifact`, `actions/deploy-pages`, `actions/configure-pages`

---

## What to Build

### Reusable Workflows

Reusable workflows live in `.github/workflows/` and are called by consuming repos at the job level. Each one encapsulates a complete CI/CD pattern.

#### 1. `go-ci.yml` (covers 10 repos)

Replaces: `golangci/golangci-lint-action`, `raven-actions/actionlint`, `codecov/codecov-action`, `astral-sh/setup-uv`, ad-hoc scrut installation

Inputs:
- `go-version` (string, default: read from go.mod via `go-version-file`)
- `runs-on` (string, default: `ubuntu-latest`; some repos need `macos-latest`)
- `run-lint` (bool, default: true) -- golangci-lint
- `golangci-lint-version` (string, default: latest stable)
- `run-scrut` (bool, default: false)
- `run-actionlint` (bool, default: false)
- `run-format-check` (bool, default: false) -- gofmt/goimports
- `run-build` (bool, default: false)
- `build-flags` (string, default: empty)
- `test-flags` (string, default: `-race`)
- `coverage` (bool, default: false) -- upload to codecov
- `timeout-minutes` (number, default: 15)

Jobs: test, lint (conditional), build (conditional), test-scrut (conditional)

#### 2. `go-release.yml` (covers 8 repos)

Replaces: `goreleaser/goreleaser-action`

Inputs:
- `go-version-file` (string, default: `go.mod`)
- `runs-on` (string, default: `macos-latest`; all current release workflows use macOS)
- `goreleaser-version` (string, default: latest v2)
- `goreleaser-args` (string, default: `release --clean`)
- `timeout-minutes` (number, default: 30)

Secrets:
- `GITHUB_TOKEN` (required)
- `HOMEBREW_TAP_TOKEN` (optional)

#### 3. `secret-scan.yml` (covers 5+ repos)

Replaces: `gitleaks/gitleaks-action`, `trufflehog` container action

Inputs:
- `tool` (string, default: `gitleaks`; options: `gitleaks`, `trufflehog`, `both`)
- `gitleaks-version` (string, default: pinned latest)
- `trufflehog-version` (string, default: pinned latest)
- `timeout-minutes` (number, default: 15)

#### 4. `lint.yml` (covers 4+ repos)

Replaces: `raven-actions/actionlint`, `rhysd/actionlint`, `mfinelli/setup-shfmt`, `streetsidesoftware/cspell-action`

Inputs:
- `node-version` (string, default: `22`)
- `run-markdownlint` (bool, default: true)
- `run-prettier` (bool, default: true)
- `run-cspell` (bool, default: false)
- `run-yamllint` (bool, default: false)
- `run-actionlint` (bool, default: false)
- `run-shellcheck` (bool, default: false)
- `run-shfmt` (bool, default: false)
- `timeout-minutes` (number, default: 10)

#### 5. `pages-deploy.yml` (covers 3 repos)

Uses official GitHub Pages actions (kept as dependencies). Provides a standard build-then-deploy pattern.

Inputs:
- `build-command` (string, required)
- `artifact-path` (string, default: `./_site`)
- `runs-on` (string, default: `ubuntu-latest`)
- `setup-go` (bool, default: false)
- `go-version-file` (string, default: `go.mod`)
- `setup-node` (bool, default: false)
- `node-version` (string, default: `22`)
- `timeout-minutes` (number, default: 15)

#### 6. `npm-publish.yml` (covers 2 repos)

Inputs:
- `node-version` (string, default: `20`)
- `registry-url` (string, default: `https://npm.pkg.github.com`)
- `timeout-minutes` (number, default: 10)

Secrets:
- `NODE_AUTH_TOKEN` (required)

### Composite Actions

Composite actions live in `actions/<name>/action.yml` and are building blocks used by the reusable workflows above (and available for direct use by any repo).

#### 1. `actions/setup-golangci-lint/action.yml`

Installs golangci-lint binary with pinned version and checksum verification.

Inputs: `version` (default: latest stable)

#### 2. `actions/setup-goreleaser/action.yml`

Installs goreleaser binary with pinned version.

Inputs: `version` (default: latest v2)

#### 3. `actions/setup-scrut/action.yml`

Installs scrut CLI testing tool. Currently done ad-hoc in 5+ repos with varying install methods (curl installer script, gh release download, pip install).

Inputs: `version` (default: latest)

#### 4. `actions/setup-actionlint/action.yml`

Installs actionlint binary with pinned version.

Inputs: `version` (default: latest)

#### 5. `actions/run-gitleaks/action.yml`

Installs gitleaks binary and runs a scan. No `pull-requests: write` needed (unlike the third-party action).

Inputs: `version` (default: pinned latest), `args` (default: `detect --source .`)

#### 6. `actions/run-trufflehog/action.yml`

Installs trufflehog binary and runs a scan.

Inputs: `version` (default: pinned latest), `args` (default: `filesystem --directory .`)

#### 7. `actions/setup-shfmt/action.yml`

Installs shfmt binary with pinned version.

Inputs: `version` (default: latest)

---

## Out of Scope

These workflows are project-specific and not worth generalizing:

- **`cboone` profile README** (`update-readme.yaml`): Uses `charmbracelet/readme-scribe` (kept) + `stefanzweifel/git-auto-commit-action` (can be replaced with git commands in a one-off fix, not a reusable workflow)
- **`tmux-default-bindings` auto-update** (`update-defaults.yml`): Complex project-specific automation
- **`bopca` benchmark** (`benchmark.yml`): Project-specific performance testing
- **`bopca` docs dispatch** (`dispatch-docs-update.yaml`): Cross-repo trigger, can be replaced with `gh api` in a one-off fix
- **`homebrew-tap` README update** (`update-readme.yml`): Simple project-specific script
- **`pbcopy2` Swift CI and release**: Only 1 Swift repo. Low ROI for a reusable workflow. Can be cleaned up independently (replace `raven-actions/actionlint` with the composite action).
- **`tmux-binding-help` scrut workflow**: Only uses `dtolnay/rust-toolchain` + scrut. Can use the `setup-scrut` composite action directly.

---

## Directory Structure

```
gh-actions/
├── actions/
│   ├── setup-golangci-lint/
│   │   └── action.yml
│   ├── setup-goreleaser/
│   │   └── action.yml
│   ├── setup-scrut/
│   │   └── action.yml
│   ├── setup-actionlint/
│   │   └── action.yml
│   ├── setup-shfmt/
│   │   └── action.yml
│   ├── run-gitleaks/
│   │   └── action.yml
│   └── run-trufflehog/
│       └── action.yml
├── .github/
│   └── workflows/
│       ├── ci.yml              (this repo's own CI)
│       ├── gitleaks.yml        (this repo's own scanning, migrated to use reusable workflow)
│       ├── trufflehog.yml      (this repo's own scanning, migrated to use reusable workflow)
│       ├── go-ci.yml           (reusable workflow)
│       ├── go-release.yml      (reusable workflow)
│       ├── secret-scan.yml     (reusable workflow)
│       ├── lint.yml            (reusable workflow)
│       ├── pages-deploy.yml    (reusable workflow)
│       └── npm-publish.yml     (reusable workflow)
├── docs/
├── Makefile
├── package.json
└── ...
```

---

## Implementation Phases

### Phase 1: Foundation (composite actions)

Build the atomic building blocks first, since the reusable workflows depend on them.

1. `actions/setup-golangci-lint/action.yml`
2. `actions/setup-goreleaser/action.yml`
3. `actions/setup-scrut/action.yml`
4. `actions/setup-actionlint/action.yml`
5. `actions/setup-shfmt/action.yml`
6. `actions/run-gitleaks/action.yml`
7. `actions/run-trufflehog/action.yml`

### Phase 2: High-Impact Reusable Workflows

Build the workflows that cover the most repos.

1. `go-ci.yml` (10 repos)
2. `go-release.yml` (8 repos)
3. `secret-scan.yml` (5+ repos)

### Phase 3: Medium-Impact Reusable Workflows

4. `lint.yml` (4+ repos)
5. `npm-publish.yml` (2 repos)
6. `pages-deploy.yml` (3 repos)

### Phase 4: Self-Hosting

Migrate this repo's own workflows to use its own reusable workflows and composite actions:
- `gitleaks.yml` calls `secret-scan.yml`
- `ci.yml` uses `actions/setup-actionlint`

### Phase 5: Consuming Repo Migration

Migrate consuming repos one at a time, starting with simpler ones:

**Pilot repos (simplest, good for validating the workflows):**
- `crawler` (Go CI only, no release)
- `right-round` (Go CI + release, minimal config)
- `claude-dotfiles` / `dotfiles` (secret scanning only)

**Then Go repos with standard patterns:**
- `gh-problemas`, `fm`, `stipple`, `tracker`, `quod`

**Then complex Go repos:**
- `snappy` (matrix OS, scrut, actionlint, Node.js tooling)
- `bopca` (5 workflows, coverage, CodeQL)
- `xylem` (Go matrix, scrut, Node.js tooling)

**Then non-Go repos:**
- `cboone-alpine-plugins`, `cboone-tailwind-plugins` (npm publish)
- `snappy-sh-site`, `bopca-sh-site`, `cboone.github.io` (Pages deploy)
- `compbox`, `cboone-cc-plugins` (lint)

**One-off cleanups (not reusable workflow migrations):**
- `pbcopy2`: Replace `raven-actions/actionlint` with `actions/setup-actionlint` composite action
- `tmux-binding-help`: Replace `dtolnay/rust-toolchain` with `rustup`, use `actions/setup-scrut`
- `cboone` profile: Replace `stefanzweifel/git-auto-commit-action` with git commands
- `bopca` dispatch: Replace `peter-evans/repository-dispatch` with `gh api`

---

## Example: Before and After

### Before (current `crawler` CI, ~25 lines)

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
      - name: Go vet
        run: go vet ./...
      - name: Run tests
        run: go test -v -race ./...
      - name: Install scrut
        run: curl ... | sh
      - name: Run scrut tests
        run: scrut test tests/
```

### After (~10 lines)

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/go-ci.yml@v1
    with:
      run-scrut: true
```

---

## Security Improvements

1. **14 third-party actions eliminated** across the portfolio
2. **Tool versions pinned** with known-good defaults in composite actions
3. **Minimal permissions** enforced by reusable workflows (consuming repos inherit)
4. **Single update point**: Bumping a tool version in `gh-actions` updates it everywhere
5. **No `pull-requests: write`** needed for secret scanning (gitleaks-action required this)
6. **Audit surface reduced**: Only need to review `gh-actions` repo for supply-chain risks

---

## Verification

For each reusable workflow and composite action:

1. **Unit test the composite actions**: Create a test workflow in this repo that exercises each composite action (install tool, verify binary exists, check version output)
2. **Integration test the reusable workflows**: Call each reusable workflow from this repo's CI with representative inputs
3. **Pilot migration**: Migrate 2-3 simple repos (crawler, right-round, dotfiles) and verify CI passes
4. **Gradual rollout**: Migrate remaining repos one at a time, verifying CI passes before proceeding

For the `go-ci.yml` workflow specifically:
- Test with `runs-on: ubuntu-latest` and `runs-on: macos-latest`
- Test with `run-scrut: true` and `run-scrut: false`
- Test with `run-lint: true` using a repo with `.golangci.yml`
- Test with `coverage: true` and verify upload

For the `secret-scan.yml` workflow:
- Test with `tool: gitleaks`, `tool: trufflehog`, and `tool: both`
- Verify it detects a known test secret in a test fixture

---

## Third-Party Action Elimination Summary

| Current Action | Replaced By | Repos Affected |
|---|---|---|
| `golangci/golangci-lint-action` | `actions/setup-golangci-lint` composite + `go-ci.yml` | 8 |
| `goreleaser/goreleaser-action` | `actions/setup-goreleaser` composite + `go-release.yml` | 8 |
| `gitleaks/gitleaks-action` | `actions/run-gitleaks` composite + `secret-scan.yml` | 5 |
| `raven-actions/actionlint` | `actions/setup-actionlint` composite + `lint.yml` | 4 |
| `rhysd/actionlint` (container) | `actions/setup-actionlint` composite | 1 |
| `trufflehog` (container) | `actions/run-trufflehog` composite + `secret-scan.yml` | 1 |
| `codecov/codecov-action` | Direct codecov CLI in `go-ci.yml` | 1 |
| `mfinelli/setup-shfmt` | `actions/setup-shfmt` composite + `lint.yml` | 1 |
| `streetsidesoftware/cspell-action` | `npx cspell` in `lint.yml` | 1 |
| `astral-sh/setup-uv` | Direct install in `go-ci.yml` (for scrut) | 1 |
| `stefanzweifel/git-auto-commit-action` | Direct git commands (one-off fix) | 1 |
| `peter-evans/repository-dispatch` | `gh api` call (one-off fix) | 1 |
| `peter-evans/create-pull-request` | `gh pr create` (one-off fix) | 1 |
| `dtolnay/rust-toolchain` | `rustup` commands (one-off fix) | 1 |

**Kept (justified):**
- All `actions/*` official GitHub actions (first-party, well-maintained, necessary)
- `github/codeql-action/*` (deeply integrated with GitHub security, no alternative)
- `charmbracelet/readme-scribe` (unique functionality, single use, used at `master` tag for profile repo only)
