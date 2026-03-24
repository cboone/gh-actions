# Centralize Third-Party Actions and SHA-Pin Dependencies

## Context

The `cboone/gh-actions` repo serves as the centralized GitHub Actions library for
26+ downstream repos. An audit of all repos in `~/Development` found four
third-party actions still referenced directly by consuming repos instead of going
through gh-actions. Additionally, all external action references in gh-actions'
own workflows use tag versions (`@v6`) instead of SHA-pinned refs, creating
supply-chain risk.

This plan eliminates direct third-party action usage in consuming repos by
providing gh-actions equivalents, and SHA-pins every external action reference
in the gh-actions repo itself.

## Inventory of Third-Party Actions

| Action                            | Repo                  | File                | Ref              | Disposition                                |
| --------------------------------- | --------------------- | ------------------- | ---------------- | ------------------------------------------ |
| `gitleaks/gitleaks-action`        | private-cc-plugins    | gitleaks.yml        | `@v2`            | Replace with existing `secret-scan.yml`    |
| `charmbracelet/readme-scribe`     | cboone                | update-readme.yaml  | `@master`        | Replace with new `run-markscribe` action   |
| `peter-evans/create-pull-request` | tmux-default-bindings | update-defaults.yml | `@22a908...` (v7)| Wrap with new `create-pull-request` action |
| `github/codeql-action/*`          | bopca                 | codeql.yml          | `@v4`            | Wrap with new `codeql.yml` workflow        |

GitHub official actions in gh-actions needing SHA-pinning:

- `actions/checkout@v6` (9 workflows)
- `actions/setup-go@v6` (3 workflows)
- `actions/setup-node@v6` (3 workflows)
- `actions/configure-pages@v5` (1 workflow)
- `actions/upload-pages-artifact@v4` (1 workflow)
- `actions/deploy-pages@v4` (1 workflow)

## Implementation

### Step 1: SHA-pin all external action references in gh-actions

Convert every `uses: actions/<name>@v<N>` to `uses: actions/<name>@<sha> # v<N>`
across all 9 reusable workflow files. Look up current tag-to-SHA mappings via
`gh api repos/<owner>/<repo>/git/ref/tags/v<N>` at implementation time.

**Files to modify:**

- `.github/workflows/go-ci.yml` (checkout, setup-go)
- `.github/workflows/go-release.yml` (checkout, setup-go)
- `.github/workflows/github-lint.yml` (checkout)
- `.github/workflows/secret-scan.yml` (checkout)
- `.github/workflows/text-lint.yml` (checkout, setup-node)
- `.github/workflows/shell-lint.yml` (checkout)
- `.github/workflows/pages-deploy.yml` (checkout, setup-go, setup-node, configure-pages, upload-pages-artifact, deploy-pages)
- `.github/workflows/scrut.yml` (checkout)
- `.github/workflows/npm-publish.yml` (checkout, setup-node)

Self-hosting workflows (ci.yml, gitleaks.yml, trufflehog.yml) use local workflow
refs only; no changes needed.

### Step 2: Create `actions/run-markscribe/action.yml`

Custom composite action replacing `charmbracelet/readme-scribe@master`.

The upstream action is Docker-based with no version tags (pinned to `@master`),
making it impossible to SHA-pin. The underlying tool `charmbracelet/markscribe`
publishes Go binaries with `checksums.txt` in the exact pattern used by existing
actions.

**Pattern:** Follow `actions/run-gitleaks/action.yml` (download, verify SHA-256
checksum, install, run).

**Inputs:**

- `version` (default: latest stable, e.g. `0.8.1`)
- `template` (default: `README.md.tpl`)
- `write-to` (default: `README.md`)

**Steps:**

1. Detect OS/arch via `uname`. Asset names use capitalized OS (`Linux`, `Darwin`)
   and arch (`x86_64`, `arm64`).
2. Download `markscribe_${VERSION}_${os}_${arch}.tar.gz` from
   `charmbracelet/markscribe` GitHub releases.
3. Verify SHA-256 against `checksums.txt`.
4. Extract binary, add to `GITHUB_PATH`.
5. Run `markscribe -write "${WRITE_TO}" "${TEMPLATE}"`.

Callers must set `GITHUB_TOKEN` in the step's `env:` for GitHub API access.

### Step 3: Create `actions/create-pull-request/action.yml`

Wrapper composite action around `peter-evans/create-pull-request`. Too complex
to reimplement (Node.js action with substantial git/GitHub API logic).

**Upstream ref:** SHA-pinned to current v7 release.

**Inputs** (10 passthrough + version):

- Currently used by tmux-default-bindings: `branch`, `commit-message`, `title`,
  `body`, `labels`, `delete-branch`
- Common extras: `token`, `base`, `assignees`, `draft`

**Outputs** (all 5): `pull-request-number`, `pull-request-url`,
`pull-request-operation`, `pull-request-head-sha`, `pull-request-branch`

**Structure:** Single `uses:` step delegating to the upstream action with input
and output forwarding.

### Step 4: Create `.github/workflows/codeql.yml`

Reusable workflow wrapping `github/codeql-action` (init, autobuild, analyze).
Multi-step coordination requires a workflow rather than a composite action.

**Inputs:**

- `languages` (string, default: `go`)
- `queries` (string, default: `security-and-quality`)
- `go-version` (string, default: `""`)
- `go-version-file` (string, default: `go.mod`)
- `runs-on` (string, default: `macos-latest`)
- `category-prefix` (string, default: `/language:`)

**Permissions:** `contents: read`, `security-events: write`

**Steps:**

1. `actions/checkout@<sha> # v6`
2. `actions/setup-go@<sha> # v6` (conditional:
   `if: contains(inputs.languages, 'go')`)
3. `github/codeql-action/init@<sha> # v4` with languages, queries
4. `github/codeql-action/autobuild@<sha> # v4`
5. `github/codeql-action/analyze@<sha> # v4` with category

All `github/codeql-action` sub-actions use the same SHA (they share a monorepo
tag).

### Step 5: Update documentation

- `CHANGELOG.md`: Add entries under `[Unreleased]` for all three new
  actions/workflows and the SHA-pinning change.
- `README.md`: Add sections for `run-markscribe`, `create-pull-request`, and
  `codeql.yml`.
- `CLAUDE.md`: Update repository structure to include the new entries.

### Step 6: Create migration issues in consuming repos

Each issue describes the changes needed after the gh-actions release.

**A. `cboone/private-cc-plugins`**: Replace `gitleaks/gitleaks-action@v2` with
`cboone/gh-actions/.github/workflows/secret-scan.yml`. Delete the custom
`gitleaks.yml` workflow and replace with a caller workflow matching the pattern
used in other repos (e.g., gh-actions' own `gitleaks.yml`). Note: the current
workflow grants `pull-requests: write` for gitleaks PR annotations, which
`secret-scan.yml` does not provide.

**B. `cboone/cboone`**: Replace `charmbracelet/readme-scribe@master` with
`cboone/gh-actions/actions/run-markscribe`. Update the workflow to pass
`GITHUB_TOKEN` via `env:` and use the `template` / `write-to` inputs.

**C. `cboone/tmux-default-bindings`**: Replace direct
`peter-evans/create-pull-request@<sha>` with
`cboone/gh-actions/actions/create-pull-request`. Pass through existing inputs
(`branch`, `commit-message`, `title`, `body`, `labels`, `delete-branch`) and use
the `pull-request-number` output.

**D. `cboone/bopca`**: Replace inline CodeQL workflow with
`cboone/gh-actions/.github/workflows/codeql.yml`. Pass `go-version: "1.25"` and
`queries: security-and-quality`.

### Step 7: Release v2.1.0

All changes are additive (new actions, new workflow) or internal (SHA-pinning).
No breaking changes for existing callers. Minor version bump is appropriate.

Use the `/release` skill to tag v2.1.0 and force-update the floating v2 tag.

## Key Reference Files

- `actions/run-gitleaks/action.yml`: Pattern for `run-markscribe` (download,
  checksum, install, run)
- `.github/workflows/go-ci.yml`: Largest SHA-pinning target; reference for
  conditional `setup-go` pattern to replicate in `codeql.yml`
- `.github/workflows/pages-deploy.yml`: Most diverse set of actions to SHA-pin
- `CHANGELOG.md`: Update with all additions under `[Unreleased]`

## Verification

1. Run `make lint` (actionlint) on all modified and new workflow files
2. Verify SHA pins match expected versions:
   `gh api repos/<owner>/<repo>/git/ref/tags/v<N> --jq '.object.sha'`
3. Verify self-hosting workflows (ci.yml, gitleaks.yml, trufflehog.yml) still
   pass after SHA-pinning
4. Validate new composite action YAML syntax with actionlint
5. Validate new reusable workflow YAML syntax with actionlint
6. Confirm each consuming-repo issue includes a working sample workflow
