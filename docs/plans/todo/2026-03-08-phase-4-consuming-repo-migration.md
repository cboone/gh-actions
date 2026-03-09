# Phase 4: Consuming Repo Migration

## Context

Phases 1-3 built 7 composite actions and 8 reusable workflows in gh-actions (now merged to main). Phase 4 migrates 21 consuming repos to use them, replacing third-party GitHub Actions with centralized, version-pinned alternatives. Each repo gets its own branch and PR.

## Prerequisites

- gh-actions reusable workflows are on main (confirmed)
- No version tags exist yet; consuming repos will reference `@main` for now
- Once migrations are validated, create `v1.0.0` and floating `v1` tag, then batch-update refs to `@v1`

## Conventions

- **Branch**: `chore/migrate-to-reusable-workflows`
- **Commit**: `chore: migrate CI workflows to gh-actions reusable workflows`
- **Ref**: `@main` (update to `@v1` after tagging)
- Preserve each repo's existing triggers, path filters, concurrency settings, and permissions
- Preserve existing runner choices (macOS vs ubuntu); runner reduction is a separate effort

---

## Group 1: Secret Scanning Only

Repos with only a gitleaks workflow. Replace `gitleaks/gitleaks-action@v2` with `secret-scan.yml`.

### claude-dotfiles

**File**: `.github/workflows/gitleaks.yml` (replace in place)

```yaml
name: gitleaks

on:
  pull_request:
  push:
  workflow_dispatch:
  schedule:
    - cron: "0 4 * * 1"

jobs:
  gitleaks:
    uses: cboone/gh-actions/.github/workflows/secret-scan.yml@main
    with:
      tool: gitleaks
```

### dotfiles

**File**: `.github/workflows/gitleaks.yml` (replace in place)

Same as claude-dotfiles (identical triggers and config).

### pb-bug

**File**: `.github/workflows/gitleaks.yml` (replace in place)

```yaml
name: Gitleaks

on:
  push:
    branches: [main]
  pull_request:

jobs:
  gitleaks:
    uses: cboone/gh-actions/.github/workflows/secret-scan.yml@main
    with:
      tool: gitleaks
```

Note: Drops `pull-requests: read` permission (no longer needed). The secret-scan.yml workflow sets `contents: read` internally.

---

## Group 2: Standard Go CI + Release

### right-round

**Files**: `.github/workflows/ci.yml`, `.github/workflows/release.yml`

Replaces: `golangci/golangci-lint-action@v9`

ci.yml:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/go-ci.yml@main
    with:
      go-version: "1.25.0"
      run-lint: true
      run-build: true
      test-flags: "-race -coverprofile=coverage.out"

  check-coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: "1.25.0"
      - run: go test ./... -race -coverprofile=coverage.out
      - run: bash scripts/check-coverage.sh
```

Note: The custom coverage check script can't run inside go-ci.yml, so it stays as a separate job. Tests run twice (once in go-ci.yml, once in coverage check). This can be optimized later if go-ci.yml adds artifact export.

release.yml:

```yaml
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  contents: write

jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/go-release.yml@main
    secrets:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Replaces: `goreleaser/goreleaser-action@v6` with `version: latest`

### gh-problemas

**Files**: `.github/workflows/ci.yml`, `.github/workflows/release.yml`

Replaces: `golangci/golangci-lint-action@v7`, `goreleaser/goreleaser-action@v6`

ci.yml:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/go-ci.yml@main
    with:
      run-lint: true
      run-format-check: true
```

release.yml:

```yaml
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  contents: write

jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/go-release.yml@main
    secrets:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      HOMEBREW_TAP_TOKEN: ${{ secrets.HOMEBREW_TAP_TOKEN }}
```

### stipple

**Files**: `.github/workflows/ci.yml`, `.github/workflows/release.yml`

Replaces: `golangci/golangci-lint-action@v9`, `goreleaser/goreleaser-action@v6`

Note: Currently has Go version matrix (1.24, 1.25). go-ci.yml does not support matrix. Migration drops matrix testing in favor of single-version testing from go.mod. This is acceptable since go.mod declares the minimum supported version.

ci.yml:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/go-ci.yml@main
    with:
      run-lint: true
      run-build: true
      run-format-check: true
```

release.yml:

```yaml
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  contents: write

jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/go-release.yml@main
    secrets:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Group 3: Go CI with Scrut

### fm

**Files**: `.github/workflows/ci.yml`, `.github/workflows/release.yml`, `.github/workflows/gitleaks.yml`

Replaces: `gitleaks/gitleaks-action@v2`, `goreleaser/goreleaser-action@v6`, curl-based scrut install

ci.yml:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/go-ci.yml@main
    with:
      run-scrut: true
```

release.yml:

```yaml
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  contents: write

jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/go-release.yml@main
    secrets:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      HOMEBREW_TAP_TOKEN: ${{ secrets.HOMEBREW_TAP_TOKEN }}
```

gitleaks.yml:

```yaml
name: gitleaks

on:
  push:
  pull_request:
  workflow_dispatch:
  schedule:
    - cron: "0 4 * * *"

jobs:
  gitleaks:
    uses: cboone/gh-actions/.github/workflows/secret-scan.yml@main
    with:
      tool: gitleaks
```

### tracker

**File**: `.github/workflows/test.yaml` (replace in place)

Replaces: `pip install scrut` with setup-scrut composite action via go-ci.yml

```yaml
name: Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/go-ci.yml@main
    with:
      run-scrut: true
      run-build: true
```

Note: go-ci.yml's scrut job runs `scrut test tests/` by default. Tracker's current test runs `scrut test tests/e2e/`. The scrut job in go-ci.yml discovers test files automatically (runs `scrut test tests/` if a `tests/` dir exists). Need to verify this finds tracker's `tests/e2e/` subdirectory.

### quod

**File**: `.github/workflows/ci.yml` (replace in place)

Replaces: `astral-sh/setup-uv@v5`, manual scrut download via `gh release download`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/go-ci.yml@main
    with:
      runs-on: macos-latest
      go-version: "1.23"
      run-scrut: true
```

Note: Preserves macos-latest runner. Uses pinned Go 1.23 (repo currently pins this).

---

## Group 4: Complex Go Repos

### xylem

**Files**: `.github/workflows/ci.yml`, `.github/workflows/release.yml`

Replaces: `golangci/golangci-lint-action@v9`, `raven-actions/actionlint@v2`, `goreleaser/goreleaser-action@v6`

ci.yml:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/go-ci.yml@main
    with:
      run-lint: true
      run-format-check: true

  text-lint:
    uses: cboone/gh-actions/.github/workflows/text-lint.yml@main

  github-lint:
    uses: cboone/gh-actions/.github/workflows/github-lint.yml@main
```

release.yml:

```yaml
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  contents: write

jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/go-release.yml@main
    secrets:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      HOMEBREW_TAP_TOKEN: ${{ secrets.HOMEBREW_TAP_TOKEN }}
```

### snappy

**Files**: `.github/workflows/ci.yml`, `.github/workflows/release.yml`

Replaces: `golangci/golangci-lint-action@v7`, `raven-actions/actionlint@v2`, `goreleaser/goreleaser-action@v6`, inline shfmt install, inline scrut download

ci.yml:

```yaml
name: CI

on:
  push:
    branches: [main]
    paths-ignore:
      - "**/CLAUDE.md"
      - "**/AGENTS.md"
      - ".claude/**"
      - ".editorconfig"
      - ".github/**/*.md"
      - ".github/ISSUE_TEMPLATE/**"
      - ".github/PULL_REQUEST_TEMPLATE/**"
      - "LICENSE"
  pull_request:
    branches: [main]
    paths-ignore:
      - "**/CLAUDE.md"
      - "**/AGENTS.md"
      - ".claude/**"
      - ".editorconfig"
      - ".github/**/*.md"
      - ".github/ISSUE_TEMPLATE/**"
      - ".github/PULL_REQUEST_TEMPLATE/**"
      - "LICENSE"

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/go-ci.yml@main
    with:
      run-lint: true
      run-build: true
      run-format-check: true

  text-lint:
    uses: cboone/gh-actions/.github/workflows/text-lint.yml@main

  shell-lint:
    uses: cboone/gh-actions/.github/workflows/shell-lint.yml@main

  github-lint:
    uses: cboone/gh-actions/.github/workflows/github-lint.yml@main

  test-scrut:
    name: Test CLI (Scrut)
    runs-on: macos-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-go@v6
        with:
          go-version-file: go.mod
      - uses: cboone/gh-actions/actions/setup-scrut@main
      - run: make test-scrut
      - run: make test-scrut-ez
      - run: make test-scrut-install
      - name: Lint man page
        run: make lint-man

  test-install:
    name: Test install.sh
    runs-on: macos-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v6
      - name: Run install.sh against a real release
        env:
          GITHUB_TOKEN: ${{ github.token }}
        run: make test-install
```

release.yml:

```yaml
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  contents: write

concurrency:
  group: ${{ github.repository }}-${{ github.workflow }}
  cancel-in-progress: false

jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/go-release.yml@main
    with:
      runs-on: macos-latest
    secrets:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      HOMEBREW_TAP_TOKEN: ${{ secrets.HOMEBREW_TAP_TOKEN }}
```

### bopca

**Files**: `.github/workflows/ci.yml`, `.github/workflows/release.yml`, `.github/workflows/dispatch-docs-update.yaml`

Replaces: `golangci/golangci-lint-action@v9`, `codecov/codecov-action@v5`, `gitleaks/gitleaks-action@v2`, `goreleaser/goreleaser-action@v6`, `peter-evans/repository-dispatch@v4`, curl-based scrut install

ci.yml:

```yaml
name: CI

on:
  push:
    branches: [main, "release/**"]
  pull_request:
    branches: [main, "release/**"]

permissions:
  contents: read

jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/go-ci.yml@main
    with:
      runs-on: macos-latest
      go-version: "1.25"
      run-lint: true
      run-scrut: true
      run-build: true
      coverage: true
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}

  gitleaks:
    uses: cboone/gh-actions/.github/workflows/secret-scan.yml@main
    with:
      tool: gitleaks
```

Note: go-ci.yml's lint job passes default args to golangci-lint. Bopca's current config uses `args: --timeout=5m`; this should be moved to `.golangci.yml` if not already there. The build job in go-ci.yml runs `go build ./...` (no custom ldflags); if bopca needs ldflags for CI builds, keep a separate custom build job.

release.yml:

```yaml
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  contents: write

jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/go-release.yml@main
    with:
      runs-on: macos-latest
    secrets:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      HOMEBREW_TAP_TOKEN: ${{ secrets.HOMEBREW_TAP_TOKEN }}
```

dispatch-docs-update.yaml (replace `peter-evans/repository-dispatch` with `gh api`):

```yaml
name: Dispatch docs update

on:
  push:
    branches:
      - main
    paths:
      - "docs/**"
      - "CONTRIBUTING.md"
      - "!docs/assessments/**"
      - "!docs/internal/**"
      - "!docs/plans/**"
      - "!docs/reviews/**"

jobs:
  dispatch:
    runs-on: ubuntu-latest
    steps:
      - name: Dispatch docs-updated event
        env:
          GH_TOKEN: ${{ secrets.DOCS_UPDATE_PAT }}
        run: |
          gh api repos/cboone/bopca-sh-site/dispatches \
            --method POST \
            --input - <<EOF
          {
            "event_type": "docs-updated",
            "client_payload": {
              "sha": "${{ github.sha }}",
              "ref": "${{ github.ref }}",
              "actor": "${{ github.actor }}"
            }
          }
          EOF
```

Keep unchanged: `benchmark.yml`, `codeql.yml`

---

## Group 5: npm Publish

### cboone-alpine-plugins

**File**: `.github/workflows/publish.yml` (replace in place)

```yaml
name: Publish to GitHub Packages

on:
  push:
    tags: ["v*"]

jobs:
  publish:
    uses: cboone/gh-actions/.github/workflows/npm-publish.yml@main
    with:
      node-version: "20"
    secrets:
      NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### cboone-tailwind-plugins

**File**: `.github/workflows/publish.yml` (replace in place)

Same as cboone-alpine-plugins.

---

## Group 6: Pages Deploy

### snappy-sh-site

**File**: `.github/workflows/deploy.yml` (replace in place)

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  deploy:
    uses: cboone/gh-actions/.github/workflows/pages-deploy.yml@main
    with:
      setup-go: true
      build-command: go run ./build.go
```

Note: Drops the PR trigger. The current workflow has a `deploy` job with `if: github.ref == 'refs/heads/main'` to skip deploy on PRs, but pages-deploy.yml always deploys. If PR build verification is needed, add a separate build-only workflow later.

### bopca-sh-site

**File**: `.github/workflows/deploy.yaml` (replace in place)

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  deploy:
    uses: cboone/gh-actions/.github/workflows/pages-deploy.yml@main
    with:
      build-command: "true"
      artifact-path: ./public
```

---

## Group 7: Text/GitHub Linting

### compbox

**File**: `.github/workflows/ci.yml` (replace in place)

Replaces: `streetsidesoftware/cspell-action@v6`, `raven-actions/actionlint@v2`

```yaml
name: CI

on:
  push:
    branches: [main]
    paths-ignore:
      - "LICENSE"
      - ".claude/**"
      - "**/CLAUDE.md"
      - "**/AGENTS.md"
  pull_request:
    branches: [main]
    paths-ignore:
      - "LICENSE"
      - ".claude/**"
      - "**/CLAUDE.md"
      - "**/AGENTS.md"

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  text-lint:
    uses: cboone/gh-actions/.github/workflows/text-lint.yml@main
    with:
      run-cspell: true

  github-lint:
    uses: cboone/gh-actions/.github/workflows/github-lint.yml@main
```

### cboone-cc-plugins

**File**: `.github/workflows/ci.yml` (modify in place)

Replaces: `mfinelli/setup-shfmt@v4`, `raven-actions/actionlint@v2`

Keep the single-job structure; swap only the two third-party action steps with composite actions:

- Replace `uses: mfinelli/setup-shfmt@v4` with `uses: cboone/gh-actions/actions/setup-shfmt@main`
- Replace `uses: raven-actions/actionlint@v2` with two steps: `uses: cboone/gh-actions/actions/setup-actionlint@main` then `run: actionlint`
- Keep yarn-based linting, shellcheck, JSON/plugin validation unchanged

---

## Group 8: One-off Cleanups

### pbcopy2

**File**: `.github/workflows/ci.yml` (modify in place)

Replaces: `raven-actions/actionlint@v2`, manual scrut gh-release-download

Two targeted step replacements:

1. Replace actionlint:

```yaml
# OLD:
- name: Actionlint
  uses: raven-actions/actionlint@v2
# NEW:
- uses: cboone/gh-actions/actions/setup-actionlint@main
- name: Actionlint
  run: actionlint
```

2. Replace scrut download (lines 32-40):

```yaml
# OLD: (gh release download + tar + cp block)
# NEW:
- uses: cboone/gh-actions/actions/setup-scrut@main
```

Keep everything else unchanged (Swift CI, markdownlint, prettier, release.yml).

### tmux-binding-help

**File**: `.github/workflows/scrut.yml` (replace in place)

Replaces: `dtolnay/rust-toolchain@stable`, `cargo install scrut`

```yaml
name: Scrut

on:
  push:
    branches: [main]
  pull_request:

jobs:
  scrut:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Rust toolchain
        run: |
          rustup update stable
          rustup default stable
      - uses: cboone/gh-actions/actions/setup-scrut@main
      - name: Run Scrut tests
        run: scrut test -w . tests
```

### cboone (profile README)

**File**: `.github/workflows/update-readme.yaml` (modify in place)

Replaces: `stefanzweifel/git-auto-commit-action@v7`

Keep `charmbracelet/readme-scribe@master` (justified in plan). Replace the auto-commit action with git commands, and restrict the `push` trigger to `main` (the old action had `branch: main`, so an unrestricted `push` trigger would change behavior):

```yaml
# OLD:
on:
  push:
  schedule:

- uses: stefanzweifel/git-auto-commit-action@v7
  with:
    commit_message: "docs: update generated README"
    branch: main
    commit_user_name: Christopher Boone
    commit_user_email: cboone@users.noreply.github.com
    commit_author: Christopher Boone <cboone@users.noreply.github.com>
# NEW:
on:
  push:
    branches: [main]
  schedule:

- name: Commit and push
  run: |
    git config user.name "Christopher Boone"
    git config user.email "cboone@users.noreply.github.com"
    git add README.md
    git diff --cached --quiet || git commit -m "docs: update generated README"
    git push
```

---

## Repos to Skip

| Repo | Reason |
| --- | --- |
| crawler | No third-party actions. CI requires tmux (go-ci.yml can't provide it). |
| cboone.github.io | No third-party actions. Hugo + Dart Sass + submodules too custom for pages-deploy.yml. |
| homebrew-tap | No third-party actions (uses only git commands). |
| tmux-default-bindings | Out of scope per plan (complex project-specific automation). |

---

## Implementation Order

Execute in this order (simplest first, validates reusable workflows before complex migrations):

1. claude-dotfiles, dotfiles, pb-bug (secret scan only, lowest risk)
2. right-round, gh-problemas (standard Go CI + release)
3. fm, tracker, quod (Go CI with scrut)
4. stipple (Go CI + release, drops matrix)
5. xylem (Go CI + text/github lint)
6. cboone-alpine-plugins, cboone-tailwind-plugins (npm publish)
7. snappy-sh-site, bopca-sh-site (pages deploy)
8. compbox (text/github lint)
9. cboone-cc-plugins (composite action swaps)
10. pbcopy2, tmux-binding-help, cboone (one-off cleanups)
11. snappy, bopca (complex Go, highest risk)

## Execution per Repo

For each repo:

1. `cd ~/Development/<repo>`
2. `git checkout main && git pull`
3. `git checkout -b chore/migrate-to-reusable-workflows`
4. Edit/replace workflow files per the spec above
5. `git add .github/workflows/` and commit
6. `git push -u origin chore/migrate-to-reusable-workflows`
7. `gh pr create`

---

## Verification

For each PR:

1. Push branch and confirm GitHub Actions workflows trigger
2. Verify all checks pass (test, lint, build, scan)
3. Confirm third-party actions no longer appear in workflow files
4. Spot-check that existing CI behavior is preserved (same tests run, same linters, same permissions)

Special attention:

- **tracker**: Verify scrut discovers `tests/e2e/` subdirectory
- **bopca**: Verify codecov upload works via CLI (previously used codecov-action)
- **bopca**: Verify `golangci-lint --timeout=5m` is in `.golangci.yml`
- **snappy**: Verify shell-lint.yml discovers shell files in expected locations
- **snappy/bopca release**: Verify macos-latest GoReleaser produces correct artifacts
- **pages deploys**: Verify site builds and deploys correctly

---

## Summary

| Group | Repos | Third-party actions replaced |
| --- | --- | --- |
| Secret scan | claude-dotfiles, dotfiles, pb-bug | gitleaks/gitleaks-action (3) |
| Standard Go | right-round, gh-problemas, stipple | golangci-lint-action (3), goreleaser-action (3) |
| Go + scrut | fm, tracker, quod | goreleaser-action (1), astral-sh/setup-uv (1), scrut installs (3) |
| Complex Go | xylem, snappy, bopca | golangci-lint-action (3), raven-actions/actionlint (2), goreleaser-action (3), codecov-action (1), repository-dispatch (1), scrut installs (2) |
| npm publish | cboone-alpine-plugins, cboone-tailwind-plugins | (none, but standardizes pattern) |
| Pages deploy | snappy-sh-site, bopca-sh-site | (none, but standardizes pattern) |
| Text/GitHub lint | compbox, cboone-cc-plugins | cspell-action (1), raven-actions/actionlint (2), mfinelli/setup-shfmt (1) |
| One-off | pbcopy2, tmux-binding-help, cboone | raven-actions/actionlint (1), dtolnay/rust-toolchain (1), git-auto-commit-action (1), scrut install (1) |

**Total: 21 repos, ~30 third-party action usages eliminated**
