# Add Rust Reusable Workflows (CI and Release)

Issue: #21

## Context

This repository provides reusable GitHub Actions workflows for CI/CD. It has Go
equivalents (`go-ci.yml`, `go-release.yml`) but nothing for Rust. The `ke`
project (cboone/ke) and future Rust projects need reusable Rust workflows that
follow the same patterns: pinned versions, checksum-verified tool downloads,
configurable jobs, and minimal permissions.

## Deliverables

1. `.github/workflows/rust-ci.yml` -- reusable CI workflow
2. `.github/workflows/rust-release.yml` -- reusable release workflow
3. Documentation updates (CLAUDE.md, README.md)

## 1. `rust-ci.yml`

Analogous to `go-ci.yml`. Six independently toggleable jobs plus Rust caching.

### Third-party actions (SHA-pinned)

- `actions/checkout` (reuse existing SHA `de0fac2...`)
- `dtolnay/rust-toolchain` -- toolchain and component installation (analogous to
  `actions/setup-go`)
- `Swatinem/rust-cache@v2` -- build artifact caching (issue requirement)
- `crate-ci/typos` -- spell checking (issue requirement)

Look up current commit SHAs for `dtolnay/rust-toolchain`, `Swatinem/rust-cache`,
and `crate-ci/typos` at implementation time.

### Inputs

| Input                 | Type    | Default            | Notes                                      |
| --------------------- | ------- | ------------------ | ------------------------------------------ |
| `rust-version`        | string  | `"stable"`         | Passed to `dtolnay/rust-toolchain`         |
| `runs-on`             | string  | `"ubuntu-latest"`  | Runner label                               |
| `run-test`            | boolean | `true`             | Toggle test job                            |
| `use-nextest`         | boolean | `false`            | Use cargo-nextest instead of cargo test    |
| `nextest-version`     | string  | pinned             | cargo-nextest version (checksum verified)  |
| `test-args`           | string  | `""`               | Extra args for cargo test/nextest          |
| `run-lint`            | boolean | `true`             | Toggle clippy job                          |
| `clippy-args`         | string  | `"-- -D warnings"` | Arguments for cargo clippy                 |
| `run-format-check`    | boolean | `true`             | Toggle fmt check job                       |
| `run-deny`            | boolean | `false`            | Toggle cargo-deny (needs deny.toml)        |
| `deny-version`        | string  | pinned             | cargo-deny version (checksum verified)     |
| `run-audit`           | boolean | `false`            | Toggle cargo-audit                         |
| `audit-version`       | string  | pinned             | cargo-audit version (checksum verified)    |
| `run-typos`           | boolean | `false`            | Toggle typos spell check                   |
| `cargo-features`      | string  | `""`               | Passed to test/clippy via `--features`     |
| `extra-components`    | string  | `""`               | Extra rustup components                    |
| `coverage`            | boolean | `false`            | Generate coverage + upload to Codecov      |
| `codecov-cli-version` | string  | `"10.4.0"`         | Codecov CLI version (from go-ci.yml)       |
| `codecov-files`       | string  | `"lcov.info"`      | Coverage file path                         |
| `timeout-minutes`     | number  | `15`               | Job timeout                                |

Secrets: `CODECOV_TOKEN` (optional)

### Jobs

**test** (`if: inputs.run-test`): Checkout, setup Rust toolchain + cache,
optionally install cargo-nextest (with checksum verification, following the same
uname-based OS/arch detection and download pattern as golangci-lint in
go-ci.yml). Run `cargo nextest run` or `cargo test`. When `coverage` is enabled,
use `cargo llvm-cov` with lcov output and upload via Codecov CLI (same pattern as
go-ci.yml).

**lint** (`if: inputs.run-lint`): Checkout, setup Rust toolchain (with clippy
component) + cache. Run `cargo clippy` with configurable args.

**format-check** (`if: inputs.run-format-check`): Checkout, setup Rust toolchain
(with rustfmt component). Run `cargo fmt -- --check`.

**deny** (`if: inputs.run-deny`): Checkout, install cargo-deny binary (checksum
verified download). Run `cargo deny check`.

**audit** (`if: inputs.run-audit`): Checkout, install cargo-audit binary
(checksum verified download). Run `cargo audit`.

**typos** (`if: inputs.run-typos`): Checkout, run `crate-ci/typos` action
(SHA-pinned).

### Tool installation pattern

For cargo-nextest, cargo-deny, and cargo-audit: follow the same pattern used by
golangci-lint in go-ci.yml:

1. Detect OS: `case "$(uname -s)" in Linux) ... Darwin) ... *) error`
2. Detect arch: `case "$(uname -m)" in x86_64) ... arm64|aarch64) ... *) error`
3. Download binary from GitHub releases to `RUNNER_TEMP`
4. Download checksums file, extract expected hash
5. Verify SHA-256 (sha256sum with shasum fallback)
6. Install to `RUNNER_TEMP/<tool>-bin`, add to `GITHUB_PATH`

## 2. `rust-release.yml`

Analogous to `go-release.yml`. Two required jobs (build matrix + release) plus an
optional Homebrew job.

### Architecture

Unlike Go's GoReleaser (single tool handles everything), Rust releases require
multi-step orchestration:

1. **build** (matrix): each target compiles on its own runner
2. **release**: collects artifacts, generates checksums, creates/updates GitHub
   Release
3. **homebrew** (optional): updates a Homebrew formula in a tap repo

### Third-party actions (SHA-pinned)

- `actions/checkout` (reuse existing SHA)
- `dtolnay/rust-toolchain`
- `actions/upload-artifact@v4`
- `actions/download-artifact@v4`

### Inputs

| Input                   | Type    | Default    | Notes                                                        |
| ----------------------- | ------- | ---------- | ------------------------------------------------------------ |
| `targets`               | string  | required   | JSON array: `[{"target":"...","runner":"..."}]`              |
| `binary-name`           | string  | `""`       | Extracted from Cargo.toml if empty                           |
| `rust-version`          | string  | `"stable"` | Rust toolchain version                                       |
| `build-args`            | string  | `""`       | Extra args for cargo build                                   |
| `archive-prefix`        | string  | `""`       | Override archive name prefix (default: `{binary}-{version}`) |
| `update-homebrew`       | boolean | `false`    | Toggle Homebrew formula update                               |
| `homebrew-tap`          | string  | `""`       | Tap repo (e.g., `cboone/homebrew-tap`)                       |
| `homebrew-formula-path` | string  | `""`       | Formula path in tap repo                                     |
| `timeout-minutes`       | number  | `30`       | Job timeout                                                  |

Secrets: `HOMEBREW_TAP_TOKEN` (optional)

Permissions: `contents: write`

### Job: build

```yaml
strategy:
  matrix:
    include: ${{ fromJSON(inputs.targets) }}
  fail-fast: true
runs-on: ${{ matrix.runner }}
```

Steps:

1. Checkout (fetch-depth: 0 for version derivation)
2. Setup Rust toolchain with target: `rustup target add ${{ matrix.target }}`
3. Detect binary name from Cargo.toml if not provided (via `cargo metadata`)
4. Derive version from `github.ref_name` (strip `v` prefix)
5. Build: `cargo build --release --target <target>`
6. Package: tar.gz archive with binary
7. Upload artifact via `actions/upload-artifact`

Archive naming: `{binary}-{version}-{target}.tar.gz`

### Job: release

`needs: build`, runs on `ubuntu-latest`.

Steps:

1. Download all build artifacts via `actions/download-artifact` (merge-multiple)
2. Generate `checksums.txt` with SHA-256 for all archives
3. Create or update GitHub Release:
   - If release exists (e.g., from `create-release.yml`): upload artifacts
   - If not: create with `--generate-notes`

### Job: homebrew (optional)

`if: inputs.update-homebrew`, `needs: release`.

Steps:

1. Checkout tap repo using `HOMEBREW_TAP_TOKEN`
2. Download release checksums
3. Generate/update formula mapping target triples to Homebrew OS/arch blocks
4. Commit and push to tap repo

## 3. Documentation updates

- **CLAUDE.md**: add `rust-ci.yml` and `rust-release.yml` to the repository
  structure listing
- **README.md**: add documentation sections for both workflows (inputs, example
  usage)

## Implementation order

1. Create `rust-ci.yml` (simpler, can be tested independently)
2. Create `rust-release.yml`
3. Update documentation
4. Run `make lint` + `make format-check` + `make spell` to validate

## Verification

- `make lint` (actionlint validates workflow syntax)
- `make lint-md` (markdownlint on updated docs)
- `make format-check` (Prettier compliance)
- `make spell` (cspell)
- Manual review of workflow structure against go-ci.yml and go-release.yml for
  pattern consistency

## Key files

- `.github/workflows/go-ci.yml` -- primary structural template for rust-ci.yml
- `.github/workflows/go-release.yml` -- primary structural template for
  rust-release.yml
- `.github/workflows/create-release.yml` -- reference for `gh release create`
  pattern
- `.github/workflows/scrut.yml` -- reference for standalone tool installation
- `CLAUDE.md` -- repository structure to update
- `README.md` -- documentation to update
