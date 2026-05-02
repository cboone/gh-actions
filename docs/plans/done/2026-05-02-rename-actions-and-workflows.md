# Rename Actions and Workflows

Date: 2026-05-02

## Goal

Rename this repository's composite actions and workflows so their public names
use imperative phrasing:

```text
IMPERATIVE[-PREPOSITION]-NOUN[-DETAILS]
```

Every local action or workflow name beginning with `setup-` should instead
begin with `set-up-`.

This is a public API change because consumers reference composite action
directories and reusable workflow filenames directly through `uses:` strings.
Existing release tags keep the old paths available for older consumers, but the
next release that includes this rename should be treated as breaking unless
legacy aliases are intentionally added. This plan recommends not adding legacy
aliases because keeping old action directories or workflow files would leave
nonconforming names in the active tree.

## Scope

Rename local composite action directories under `actions/`.

Rename local workflow files under `.github/workflows/`.

Update each affected `name:` field so the GitHub UI uses the same imperative
language as the path.

Update in-repository workflow call sites that reference renamed reusable
workflows with `uses: ./.github/workflows/...`.

Update living documentation and agent guidance: `README.md`, `AGENTS.md`,
`.github/copilot-instructions.md`, and the `Unreleased` section of
`CHANGELOG.md`.

Leave historical changelog entries and completed plan documents historically
accurate unless a reference is part of current user-facing documentation. Old
names in `docs/plans/done/` and older `CHANGELOG.md` release sections are
evidence of the project history, not active API surface.

Do not rename external GitHub Actions such as `actions/setup-go` or
`actions/setup-node`.

Do not rename workflow inputs such as `setup-go`, `setup-node`, or
`scrut-setup-cmd` as part of this pass. They are public inputs, not action or
workflow names, and changing them would expand the migration surface.

## Proposed Composite Action Renames

| Current action path | New action path | New `name:` | Rationale |
| --- | --- | --- | --- |
| `actions/gh-release` | `actions/create-gh-release` | `Create GitHub Release` | Matches the requested `gh-release` to `create-gh-release` direction. |
| `actions/setup-actionlint` | `actions/set-up-actionlint` | `Set up actionlint` | Applies the `setup-` to `set-up-` rule. |
| `actions/setup-golangci-lint` | `actions/set-up-golangci-lint` | `Set up golangci-lint` | Applies the `setup-` to `set-up-` rule. |
| `actions/setup-goreleaser` | `actions/set-up-goreleaser` | `Set up GoReleaser` | Applies the `setup-` to `set-up-` rule. |
| `actions/setup-scrut` | `actions/set-up-scrut` | `Set up scrut` | Applies the `setup-` to `set-up-` rule. |
| `actions/setup-shfmt` | `actions/set-up-shfmt` | `Set up shfmt` | Applies the `setup-` to `set-up-` rule. |

These action paths already conform and should stay unchanged:

- `actions/create-pull-request`
- `actions/run-cspell`
- `actions/run-gitleaks`
- `actions/run-markscribe`
- `actions/run-reuse`
- `actions/run-trufflehog`

## Proposed Reusable Workflow Renames

| Current workflow file | New workflow file | New `name:` | Rationale |
| --- | --- | --- | --- |
| `.github/workflows/create-release.yml` | `.github/workflows/create-gh-release-from-changelog.yml` | `Create GitHub Release from changelog` | Distinguishes the changelog-driven reusable workflow from the lower-level `create-gh-release` composite action. |
| `.github/workflows/go-ci.yml` | `.github/workflows/run-go-ci.yml` | `Run Go CI` | Matches the requested `go-ci` to `run-go-ci` direction. |
| `.github/workflows/go-release.yml` | `.github/workflows/release-go-binaries.yml` | `Release Go binaries` | Starts with the imperative verb `release` and describes the GoReleaser-backed result. |
| `.github/workflows/rust-ci.yml` | `.github/workflows/run-rust-ci.yml` | `Run Rust CI` | Keeps CI workflows parallel across languages. |
| `.github/workflows/rust-release.yml` | `.github/workflows/release-rust-binaries.yml` | `Release Rust binaries` | Starts with the imperative verb `release` and preserves the binary-release meaning. |
| `.github/workflows/secret-scan.yml` | `.github/workflows/scan-for-secrets.yml` | `Scan for secrets` | Matches the requested `secret-scan` to `scan-for-secrets` direction. |
| `.github/workflows/text-lint.yml` | `.github/workflows/lint-text.yml` | `Lint text` | Starts with the imperative verb `lint`. |
| `.github/workflows/shell-lint.yml` | `.github/workflows/lint-shell.yml` | `Lint shell` | Starts with the imperative verb `lint`. |
| `.github/workflows/github-lint.yml` | `.github/workflows/lint-github-actions.yml` | `Lint GitHub Actions` | Makes the noun specific to workflow and action metadata. |
| `.github/workflows/pages-deploy.yml` | `.github/workflows/deploy-to-pages.yml` | `Deploy to Pages` | Uses the imperative-preposition-noun pattern. |
| `.github/workflows/codeql.yml` | `.github/workflows/analyze-with-codeql.yml` | `Analyze with CodeQL` | Uses the imperative-preposition-noun pattern. |
| `.github/workflows/scrut.yml` | `.github/workflows/run-scrut-tests.yml` | `Run scrut tests` | Describes the reusable workflow's snapshot-test behavior. |
| `.github/workflows/npm-publish.yml` | `.github/workflows/publish-to-npm.yml` | `Publish to npm` | Matches the requested `npm-publish` to `publish-to-npm` direction. |
| `.github/workflows/zig-ci.yml` | `.github/workflows/run-zig-ci.yml` | `Run Zig CI` | Keeps CI workflows parallel across languages. |
| `.github/workflows/zig-release.yml` | `.github/workflows/release-zig-binaries.yml` | `Release Zig binaries` | Starts with the imperative verb `release` and preserves the binary-release meaning. |

## Proposed Self-Hosting Workflow Renames

| Current workflow file | New workflow file | New `name:` | Required local `uses:` update |
| --- | --- | --- | --- |
| `.github/workflows/ci.yml` | `.github/workflows/run-ci.yml` | `Run CI` | Change `uses: ./.github/workflows/github-lint.yml` to `uses: ./.github/workflows/lint-github-actions.yml`. |
| `.github/workflows/release.yml` | `.github/workflows/create-gh-release-on-tag.yml` | `Create GitHub Release on tag` | Change `uses: ./.github/workflows/create-release.yml` to `uses: ./.github/workflows/create-gh-release-from-changelog.yml`. |
| `.github/workflows/gitleaks.yml` | `.github/workflows/scan-for-secrets-with-gitleaks.yml` | `Scan for secrets with gitleaks` | Change `uses: ./.github/workflows/secret-scan.yml` to `uses: ./.github/workflows/scan-for-secrets.yml`. |
| `.github/workflows/trufflehog.yml` | `.github/workflows/scan-for-secrets-with-trufflehog.yml` | `Scan for secrets with trufflehog` | Change `uses: ./.github/workflows/secret-scan.yml` to `uses: ./.github/workflows/scan-for-secrets.yml`. |

The `check-tool-versions.yml` workflow already starts with an imperative verb
and should stay as `.github/workflows/check-tool-versions.yml` with
`name: Check tool versions`.

## Implementation Plan

### 1. Lock the Rename Map

Review the tables above before implementation. The main naming decision is the
intentional distinction between `actions/create-gh-release` and
`.github/workflows/create-gh-release-from-changelog.yml`.

Confirm that no legacy alias directories or workflow files will be kept in the
active tree. If compatibility aliases are later required, add them as a separate
explicit decision because they conflict with the goal that all active actions
and workflows follow the new naming form.

### 2. Rename Composite Action Directories

Use `git mv` for each changed action path:

- `actions/gh-release` to `actions/create-gh-release`
- `actions/setup-actionlint` to `actions/set-up-actionlint`
- `actions/setup-golangci-lint` to `actions/set-up-golangci-lint`
- `actions/setup-goreleaser` to `actions/set-up-goreleaser`
- `actions/setup-scrut` to `actions/set-up-scrut`
- `actions/setup-shfmt` to `actions/set-up-shfmt`

Update the top-level `name:` value in each moved `action.yml`.

Audit comments and hardcoded path references in the moved action files. For
example, the `gh-release` action currently writes
`${RUNNER_TEMP}/gh-release-notes.md`; that temporary filename can remain because
it is internal, but changing it to `create-gh-release-notes.md` would make logs
and temporary files align with the new action name.

### 3. Rename Workflow Files

Use `git mv` for every workflow file listed in the reusable and self-hosting
workflow tables.

Update each workflow's top-level `name:` value.

Update self-hosting call sites in the renamed local workflow files:

- `run-ci.yml` calls `lint-github-actions.yml`.
- `create-gh-release-on-tag.yml` calls
  `create-gh-release-from-changelog.yml`.
- `scan-for-secrets-with-gitleaks.yml` calls `scan-for-secrets.yml`.
- `scan-for-secrets-with-trufflehog.yml` calls `scan-for-secrets.yml`.

Keep job IDs stable unless a job ID itself is misleading. Job IDs are not part
of the requested action and workflow rename, and changing them would alter
status check names for consumers.

### 4. Update Living Documentation

Update `README.md`:

- Rename table-of-contents entries and section headings.
- Update every `uses: cboone/gh-actions/actions/...` example.
- Update every `uses: cboone/gh-actions/.github/workflows/...` example.
- Update cross-links such as references from cspell documentation to the text
  lint workflow.
- Add a migration table from old public paths to new public paths.
- Document that old paths remain available only on older tags that predate the
  rename.

Update `AGENTS.md`:

- Rename the repository structure entries.
- Replace the `setup-*` naming convention with the `set-up-*` convention.
- Update references to CI, release, lint, scan, and setup workflow names.
- Update the testing section to reference the new self-hosting workflow names.

Update `.github/copilot-instructions.md`:

- Replace checksum path references for scrut and shfmt.
- Replace references to `go-ci.yml`, `zig-ci.yml`, `scrut.yml`,
  `shell-lint.yml`, `create-release.yml`, and related workflow names.
- Keep guidance about external actions such as `actions/setup-go` unchanged.

Update `CHANGELOG.md`:

- Add an `Unreleased` entry describing the breaking rename.
- Include the old-to-new mapping or point to the README migration table.
- Do not rewrite older release sections except to correct current-documentation
  references if any are discovered outside historical prose.

### 5. Update Tooling and Metadata

Review `.github/dependabot.yml`. The current `github-actions` configuration
scans `/` and `/actions/create-pull-request`; the renamed setup actions do not
currently contain external `uses:` references. No directory update is expected
unless implementation discovers an external action reference in a renamed
composite action.

Review `Makefile`, `package.json`, `.github/actionlint.yaml`, and scripts for
hardcoded workflow or action paths. No changes are expected from the initial
scan, but this should be verified after the renames.

Check whether repository branch protection or required status checks reference
old workflow names such as `CI`. Those settings live outside this repository's
files, but renaming workflows can change the labels shown in GitHub.

### 6. Search Passes

Run targeted searches after the file moves and documentation updates:

```sh
rg -n "actions/(setup-|gh-release)" README.md AGENTS.md .github actions scripts package.json
rg -n "\\.github/workflows/(create-release|go-ci|go-release|rust-ci|rust-release|secret-scan|text-lint|shell-lint|github-lint|pages-deploy|codeql|scrut|npm-publish|zig-ci|zig-release)\\.yml" README.md AGENTS.md .github actions scripts package.json
rg -n "uses: \\./\\.github/workflows/(create-release|secret-scan|github-lint)\\.yml" .github/workflows
rg -n "^name: (CI|Release|gitleaks|trufflehog|Go CI|Go Release|Rust CI|Rust Release|Secret Scan|Text Lint|Shell Lint|GitHub Lint|Pages Deploy|CodeQL|Scrut|npm Publish|Zig CI|Zig Release)$" .github/workflows actions
```

Then run a broader search and intentionally classify remaining old-name hits:

```sh
rg -n "setup-|gh-release|go-ci|go-release|rust-ci|rust-release|secret-scan|text-lint|shell-lint|github-lint|pages-deploy|npm-publish|zig-ci|zig-release" README.md AGENTS.md .github actions CHANGELOG.md docs/plans/todo
```

Expected remaining hits after implementation:

- External action names such as `actions/setup-go` and `actions/setup-node`.
- Input names such as `setup-go`, `setup-node`, and `scrut-setup-cmd`.
- Historical prose in older changelog sections if the broad search includes
  all of `CHANGELOG.md`.
- Historical completed plans under `docs/plans/done/` if they are searched.

### 7. Verification

Run the repository's local checks:

```sh
make format-check
make lint
make lint-yaml
make lint-md
make spell
```

If Prettier reports formatting changes, run:

```sh
make format
make format-check
```

If markdownlint or cspell reports expected new words, update project spelling or
Markdown formatting deliberately rather than suppressing the checks globally.

### 8. Commit Boundaries

Use signed conventional commits. Suggested logical commits:

```text
refactor: rename composite actions
refactor: rename reusable workflows
docs: document action and workflow renames
```

If the implementation naturally splits self-hosting workflow changes from
reusable workflow changes, use a separate signed commit such as:

```text
ci: rename self-hosting workflows
```

### 9. Downstream Migration Notes

Consumers must update `uses:` strings when moving to the first release tag that
contains this rename. Examples:

```yaml
- uses: cboone/gh-actions/actions/set-up-scrut@vNEXT

jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/run-go-ci.yml@vNEXT
```

Recommended migration documentation:

- Tell consumers to update both action paths and reusable workflow filenames in
  the same PR.
- Tell consumers not to change external action references such as
  `actions/setup-go`.
- Tell consumers to update branch protection rules if required status checks
  changed labels after workflow renames.
- Tell consumers pinned to older release tags that their current old paths keep
  working on those older tags.
