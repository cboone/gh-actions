# Add Standalone Scrut Reusable Workflow

## Context

Issue #12 requests extracting the scrut test job from `go-ci.yml` into a
standalone reusable workflow. The primary use case is non-Go projects (such as
zsh plugins) that use scrut for CLI snapshot testing but cannot use `go-ci.yml`
because it requires Go setup and a Go build step. The new workflow provides the
same scrut binary installation with checksum verification, minus the Go
dependencies.

## Files to Create/Modify

### 1. Create `.github/workflows/scrut.yml`

New standalone reusable workflow. Structure follows existing patterns from
`shell-lint.yml`, `github-lint.yml`, etc.

**Inputs** (7, matching issue specification):

| Name              | Type   | Default         | Description                                         |
| ----------------- | ------ | --------------- | --------------------------------------------------- |
| `scrut-version`   | string | `"0.4.3"`       | Scrut version to install (checksums pinned to this) |
| `scrut-shell`     | string | `""`            | Shell for `--shell` flag (e.g., "zsh", "bash")      |
| `scrut-test-dir`  | string | `"tests/"`      | Directory containing scrut test files               |
| `scrut-env`       | string | `""`            | Newline-delimited KEY=VALUE env vars                |
| `scrut-setup-cmd` | string | `""`            | Pre-test setup command                              |
| `runs-on`         | string | `ubuntu-latest` | Runner label                                        |
| `timeout-minutes` | number | `10`            | Job timeout                                         |

**Permissions:** `contents: read`

**Job steps:**

1. `actions/checkout@v6`
2. Scrut test setup (conditional, runs `scrut-setup-cmd` if non-empty)
3. Install scrut (inlined from `actions/setup-scrut/action.yml` pattern):
   - OS/arch detection via `uname` case statements
   - `supported_version` guard (appropriate here because VERSION comes from a
     workflow input, per `copilot-instructions.md` line 13 reasoning)
   - Hardcoded SHA-256 checksums for 4 platform combos (same values as
     `go-ci.yml` and `actions/setup-scrut/action.yml`)
   - Download, verify checksum, extract to `RUNNER_TEMP/scrut-bin`
4. Run scrut tests:
   - Parse `SCRUT_ENV` with `while IFS= read -r` loop (same as `go-ci.yml`)
   - Resolve `./` relative paths to absolute
   - Build args array; conditionally add `--shell` when `SCRUT_SHELL` is
     non-empty
   - Execute `scrut "${args[@]}"`

**Key differences from go-ci.yml scrut job:**

- No Go setup or build steps
- No `scrut-build-cmd` input
- Adds `scrut-version` input (was hardcoded in go-ci.yml)
- Adds `scrut-shell` / `--shell` flag support (new capability)
- Includes `supported_version` guard (since version comes from input)

### 2. Update `README.md`

- Add `[scrut](#scrut)` to the TOC under Reusable Workflows (alphabetically
  between `pages-deploy` and `secret-scan`, at line 17)
- Add a `### scrut` section between `pages-deploy` and `secret-scan` sections
  (after line 371), following the established pattern: description, permissions,
  inputs table, usage examples

### 3. Update `CLAUDE.md`

- Add `scrut.yml` to the repository structure listing under `.github/workflows/`
  (between `secret-scan.yml` and `shell-lint.yml`):
  `scrut.yml               # Reusable: scrut CLI snapshot tests`

### 4. Update `.github/copilot-instructions.md`

- Line 11: Add `.github/workflows/scrut.yml` to the list of files with
  duplicated scrut checksums (currently lists `actions/setup-scrut/action.yml`
  and `.github/workflows/go-ci.yml`; becomes three files)
- Line 13: Update the note about `supported_version` guards to mention that
  `scrut.yml` does include a guard (like the composite action) because its
  VERSION comes from a workflow input

### 5. Update `CHANGELOG.md`

Add under `## [Unreleased]`:

```markdown
### Added

- Reusable workflow `scrut.yml` for standalone scrut CLI snapshot testing
  without Go dependencies
```

## Implementation Order

1. Create `.github/workflows/scrut.yml`
2. Update `README.md`
3. Update `CLAUDE.md`
4. Update `.github/copilot-instructions.md`
5. Update `CHANGELOG.md`
6. Commit each logical change

## Verification

1. Run `make lint` to validate the new workflow with actionlint
2. Run `make lint-md` to check Markdown formatting
3. Run `make format-check` to verify Prettier compliance
4. Run `make spell` to check spelling
