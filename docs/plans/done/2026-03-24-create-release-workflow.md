# Create Release Workflow

## Context

Pushing a version tag (e.g., `v2.0.0`) does not automatically create a GitHub
Release. Releases v1.0.0, v1.1.0, and v1.2.0 all had to be created manually
after tags were pushed. This plan adds a reusable workflow that extracts release
notes from CHANGELOG.md and creates a GitHub Release, plus a self-hosting
workflow that triggers it on semver tag pushes. (Issue #18)

## Files to Create

### 1. `.github/workflows/create-release.yml` (reusable workflow)

Triggered via `workflow_call`. Checks out the repo, extracts the matching version
section from CHANGELOG.md, and creates a GitHub Release via `gh release create`.

**Inputs:**

| Name             | Type    | Default        | Description                        |
| ---------------- | ------- | -------------- | ---------------------------------- |
| `changelog-file` | string  | `CHANGELOG.md` | Path to the changelog file         |
| `draft`          | boolean | `false`        | Create the release as a draft      |
| `prerelease`     | boolean | `false`        | Mark the release as a prerelease   |
| `runs-on`        | string  | `ubuntu-latest`| Runner label (Windows unsupported) |
| `timeout-minutes`| number  | `10`           | Job timeout in minutes             |

**Permissions:** `contents: write` (same as `go-release.yml`)

**Steps:**

1. `actions/checkout@v6` (shallow clone, no need for full history)
2. "Extract release notes" shell step:
   - Derive version by stripping `v` prefix from `github.ref_name`
   - Validate it looks like semver (`X.Y.Z`)
   - Use `awk` to extract lines between `## [VERSION]` and the next `## [`
     heading
   - Trim leading/trailing blank lines
   - Fail with clear error if version not found or notes empty
   - Write notes to `${RUNNER_TEMP}/release-notes.md` and expose path via
     `GITHUB_OUTPUT`
3. "Create GitHub Release" shell step:
   - Build `gh release create` command as a bash array
   - Use `--notes-file` (not `--notes`) to avoid multiline quoting issues
   - Conditionally add `--draft` and `--prerelease` flags
   - Auth via `GITHUB_TOKEN: ${{ github.token }}`

**Key conventions followed:**

- Inputs passed to steps via `env:` mappings, not inline expressions
- `shell: bash` on all shell steps
- No tool installation needed (`gh` is pre-installed on runners)
- `runs-on` and `timeout-minutes` inputs match the pattern in every other
  reusable workflow

### 2. `.github/workflows/release.yml` (self-hosting workflow)

Triggered on push of semver tags only. Calls `create-release.yml` with defaults.

```yaml
name: Release

on:
  push:
    tags:
      - "v[0-9]+.[0-9]+.[0-9]+"

jobs:
  release:
    uses: ./.github/workflows/create-release.yml
```

**Key decisions:**

- Tag pattern `v[0-9]+.[0-9]+.[0-9]+` matches `v1.0.0` but NOT floating major
  tags like `v1` or `v2`
- No `concurrency` group needed (tag pushes are one-shot, unlike branch pushes)
- No `with:` block needed (all defaults are correct for this repo)
- Follows the same minimal pattern as `gitleaks.yml` and `trufflehog.yml`

## CHANGELOG Extraction Logic

The CHANGELOG uses Keep a Changelog format with headings like
`## [2.0.0] - 2026-03-09`. The `awk` script:

```bash
version="${TAG#v}"
notes="$(awk -v ver="${version}" '
  /^## \[/ {
    if (found) exit
    if (index($0, "## [" ver "]")) { found = 1; next }
  }
  found { print }
' "${CHANGELOG_FILE}")"
```

1. On any `## [` line: if we already found our section, exit (reached next
   version). If this line contains our version, set `found` and skip the heading.
2. While `found`, print all lines.

Edge case: for the last version in the file, the range extends to EOF, which
includes link reference definitions (e.g., `[1.0.0]: https://...`). These render
as invisible Markdown, so they are harmless in release notes.

## Files to Modify

### 3. `CHANGELOG.md`

Add under `## [Unreleased]` / `### Added`:

```markdown
- Reusable workflow `create-release.yml` for creating GitHub Releases from
  changelog files in Keep a Changelog format
- Self-hosting workflow `release.yml` to create releases on version tag pushes
```

### 4. `README.md`

Add a TOC entry `[create-release](#create-release)` alphabetically before
`go-ci`. Add a documentation section between "Reusable Workflows" heading and the
`go-ci` section, following the exact format of other workflow docs (description,
permissions badge, inputs table, usage example with `@main`).

### 5. `CLAUDE.md`

Add to the `.github/workflows/` section in the repository structure listing:

- `create-release.yml   # Reusable: create GitHub Release from changelog`
  (alphabetically before `go-ci.yml`)
- `release.yml          # Self-hosting: runs create-release on version tags`
  (alphabetically between `pages-deploy.yml` and `scrut.yml`)

### 6. `cspell.json`

Add `"prerelease"` to the words array (alphabetically between `"problemas"` and
`"rhysd"`).

### 7. `.github/copilot-instructions.md`

Add a PR review note:

> **create-release.yml uses `gh` (pre-installed)**: Unlike most workflows that
> download and checksum-verify tools, create-release.yml only uses the GitHub CLI
> (`gh`), which is pre-installed on all GitHub Actions runners. Do not suggest
> adding checksum verification or tool installation steps.

## Downstream Adoption: Create Issues in 7 Repos

After the workflow is merged, create GitHub issues in all repos that have a
CHANGELOG.md to adopt `create-release.yml`. Two groups with slightly different
issue templates:

### Group A: Already use cboone/gh-actions (straightforward adoption)

- **compbox** (`cboone/compbox`)
- **pb-bug** (`cboone/pb-bug`)
- **prompt.zsh** (`cboone/prompt.zsh`)
- **snappy-sh-site** (`cboone/snappy-sh-site`)

Issue template for Group A:

> **Title:** Add create-release workflow for automated GitHub Releases
>
> **Body:** The `cboone/gh-actions` repo now provides a reusable
> `create-release.yml` workflow that extracts release notes from CHANGELOG.md
> and creates a GitHub Release when a semver tag is pushed.
>
> This repo already uses `cboone/gh-actions` workflows and has a CHANGELOG.md.
> To adopt:
>
> 1. Create `.github/workflows/release.yml` that triggers on `v*` tag pushes
>    and calls `cboone/gh-actions/.github/workflows/create-release.yml@v2`
> 2. Tag your first release

### Group B: Don't yet use cboone/gh-actions (need broader setup)

- **maze-war-plus-plus** (`cboone/maze-war-plus-plus`)
- **private-cc-plugins** (`cboone/private-cc-plugins`)
- **writer-theme-vscode** (`cboone/writer-theme-vscode`)

Issue template for Group B:

> **Title:** Add create-release workflow for automated GitHub Releases
>
> **Body:** The `cboone/gh-actions` repo now provides a reusable
> `create-release.yml` workflow that extracts release notes from CHANGELOG.md
> and creates a GitHub Release when a semver tag is pushed.
>
> This repo has a CHANGELOG.md but does not currently reference
> `cboone/gh-actions`. To adopt:
>
> 1. Create `.github/workflows/release.yml` that triggers on `v*` tag pushes
>    and calls `cboone/gh-actions/.github/workflows/create-release.yml@v2`
> 2. Tag your first release

Issues are created via `gh issue create` in each repo.

## Verification

1. `make lint` to validate all workflow files with actionlint
2. `make lint-md` to check Markdown formatting
3. `make format-check` to verify Prettier compliance
4. `make spell` to check spelling
5. Manually verify the awk extraction against the actual CHANGELOG.md content
6. The self-hosting workflow cannot be tested until a semver tag is pushed (same
   as when `gitleaks.yml` was first added)
7. Verify all 7 issues were created successfully via `gh issue list`
