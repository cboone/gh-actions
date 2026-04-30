# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Dependabot config (`.github/dependabot.yml`) covering both
  `github-actions` (workflows + composite actions with external `uses:`)
  and `npm` (devDependencies). Minor/patch updates are grouped weekly;
  major updates open individual PRs
- Scheduled `check-tool-versions.yml` workflow that runs weekly, queries
  upstream releases for every tool Dependabot does not track (binary
  downloads, hardcoded checksum tables, yamllint, Node LTS), and opens
  or updates a single tracking issue when something is outdated. Closes
  the issue automatically when versions are current
- `scripts/check-tool-versions.py`: uv-managed Python script that powers
  the scheduled check. Hardcodes the current pinned versions and notes
  which bumps require regenerating SHA-256 checksums or hash files
- `requirements/yamllint.txt`: hash-pinned (`uv pip compile
  --generate-hashes`) requirements for yamllint and its transitive
  dependencies
- `.github/actionlint.yaml`: ignore-pattern for the
  `github.job_workflow_sha` context property, which actionlint v1.7.12
  does not yet recognise but GitHub provides at runtime in reusable
  workflows

### Changed

- **Hardening** `cargo-llvm-cov` install in `rust-ci.yml`: replace
  `cargo install cargo-llvm-cov@0.8.5 --locked` (which trusted crates.io
  registry integrity) with a checksum-verified binary download from
  `taiki-e/cargo-llvm-cov` releases. Hardcoded SHA-256 table mirrors
  the scrut / cargo-audit / shfmt pattern; new `llvm-cov-version`
  input. Eliminates the registry-only trust path for coverage runs.
- **Hardening** yamllint in `text-lint.yml` and the local `make
  lint-yaml`: switch from `uv tool run --from "yamllint==X.Y.Z"`
  (PyPI-registry-only trust) to `uv pip install --require-hashes -r
  requirements/yamllint.txt` against a hash-pinned manifest. The
  workflow downloads the manifest from this repo at the workflow's own
  SHA (`github.job_workflow_sha`), so a tampered registry response
  cannot pass the per-package hash check. Every transitive dep of
  yamllint is hash-pinned.
- **Hardening** npm tool installs in `text-lint.yml`: replace `npm
  install --global "<pkg>@<version>"` (no integrity check) with `npm ci`
  against this repo's checked-in `package-lock.json`, fetched at the
  workflow's own SHA. Per-package sha512 integrity is now enforced for
  markdownlint-cli2, prettier, and cspell.
- **rust-version pinning**: `rust-ci.yml` and `rust-release.yml`
  default `rust-version` to empty and add a `rust-toolchain-file`
  input (default `rust-toolchain.toml`). A new pre-step resolves the
  toolchain by reading the consumer's `rust-toolchain.toml` channel
  value when `rust-version` is empty. At least one of the two must
  resolve; otherwise the workflow fails fast with a clear error. This
  matches dtolnay/rust-toolchain's lack of native toolchain-file
  support and lets the consumer repo (e.g. `ke`) pin the Rust
  toolchain in the standard idiomatic place.
- **README**: replace every `cboone/gh-actions/...@main` example with
  `@v2.1.4` (the current released tag) and remove `@main` from the
  Pinning section. Branch refs are no longer suggested as a "for
  testing" option; consumers must pin to a release tag.
- Pin `package.json` devDependencies to exact versions (no `^`/`~`) so a
  fresh `npm install` cannot float
- Annotate `dtolnay/rust-toolchain` SHA pins with the upstream commit
  date (the action does not publish semver tags)
- Move default `node-version` from major-only `"22"` to a specific Node
  24 LTS release `"24.15.0"` in `text-lint.yml`, `npm-publish.yml`, and
  `pages-deploy.yml`
- Bump pinned tool defaults to current latest stable releases:
  - actionlint 1.7.11 → 1.7.12
  - golangci-lint 2.11.3 → 2.11.4
  - gitleaks 8.30.0 → 8.30.1
  - trufflehog 3.93.8 → 3.95.2
  - GoReleaser 2.14.3 → 2.15.4
  - cargo-deny 0.19.0 → 0.19.4
  - cargo-nextest 0.9.132 → 0.9.133
  - shfmt 3.13.0 → 3.13.1 (new hardcoded SHA-256 checksums; upstream
    still does not publish a checksum file)
  - yamllint 1.37.1 → 1.38.0
  - codecov CLI 10.4.0 → 11.2.8 (major bump)
  - uv 0.10.9 → 0.11.8
  - cspell 9.7.0 → 10.0.0 (major bump)
  - markdownlint-cli2 0.21.0 → 0.22.1
  - prettier 3.8.1 → 3.8.3
- Bump pinned third-party action SHAs to current latest releases:
  - actions/setup-node v6 → v6.4.0
  - actions/setup-go v6 → v6.4.0
  - actions/upload-artifact v7 → v7.0.1
  - github/codeql-action v4 → v4.35.2
  - crate-ci/typos v1.44.0 → v1.45.2
  - peter-evans/create-pull-request v7 → v8.1.1 (Node 20 → 24 runtime;
    no input changes)
  - softprops/action-gh-release v2 → v3.0.0 (Node 20 → 24 runtime; no
    input changes)
- Disable `MD060` (table-column-style) in `.markdownlint-cli2.jsonc`.
  This rule is new in markdownlint v0.40 (shipped with markdownlint-cli2
  0.22.1) and we don't enforce table-pipe alignment
- Convert one emphasis-as-heading line in
  `docs/plans/done/2026-03-27-add-zig-workflows.md` to a real `####`
  heading so MD036 stays enabled

### Documentation

- Add **Pinning Policy and Trust Model** section to `AGENTS.md`
  describing how each kind of dependency is pinned (commit SHA, archive
  checksum, registry exact version, lockfile integrity). Document the
  Rust toolchain as the one explicit version-pinning exception:
  `rust-version` defaults to empty and `rust-toolchain-file` (default
  `rust-toolchain.toml`) lets the consumer repo control whether the
  channel is pinned (e.g., `"1.84.0"`) or floats with rustup
  (`"stable"`). `node-version` defaults to an exact `"24.15.0"` and is
  not a floating default; callers may override

## [2.1.4] - 2026-04-27

### Fixed

- Hardcode SHA-256 checksums for shfmt v3.13.0 in `setup-shfmt` action and
  `shell-lint.yml` workflow. shfmt upstream stopped publishing
  `sha256sums.txt` starting with v3.13.0 (mvdan/sh#1283, mvdan/sh#1309),
  which broke installation with `curl: (22) ... 404` for every consumer
  pinned to the default version (#38)

### Changed

- Update README defaults for `setup-shfmt` and `shell-lint.yml` from
  `3.12.0` to `3.13.0` to match the actual action and workflow defaults
- Document in README that only the pinned `shfmt` version is supported by
  `setup-shfmt` and `shell-lint.yml`, and that overriding it requires
  updating the hardcoded SHA-256 checksums first (#39)
- Add Copilot instruction documenting shfmt's hardcoded checksum approach,
  version-bump procedure, and asset name + digest cross-check command

## [2.1.3] - 2026-03-30

### Fixed

- Replace `--version` check with executable test (`test -x`) in run-markscribe
  action (#33)

### Changed

- Add Copilot instruction for markscribe `test -x` verification

## [2.1.2] - 2026-03-28

### Fixed

- Extract only markscribe binary from archive instead of entire tarball contents
- Use `--strip-components=1` for markscribe tar extraction to match expected
  install layout

## [2.1.1] - 2026-03-27

### Fixed

- Use exact version in major bump example and soften release wording

### Changed

- Versioning strategy now uses only exact version tags (e.g., `v2.2.0`);
  floating major tags (`v1`, `v2`) are discontinued
- Add single instructions file rule to Copilot instructions

## [2.1.0] - 2026-03-27

### Added

- Reusable workflows `rust-ci.yml` for Rust test, clippy, fmt, deny, audit,
  and typos checking, and `rust-release.yml` for Rust binary releases with
  matrix builds (#21)
- Reusable workflow `zig-ci.yml` for Zig test, format, build, cross-compile,
  and scrut testing (#22)
- Reusable workflow `zig-release.yml` for Zig cross-compile releases with
  GitHub Release artifact uploads (#22)
- Reusable workflow `create-release.yml` for creating GitHub Releases from
  changelog files in Keep a Changelog format
- Self-hosting workflow `release.yml` to create releases on version tag pushes
- Composite action `run-markscribe` to install and run the markscribe README
  template generator with SHA-256 checksum verification
- Composite action `create-pull-request` as a SHA-pinned wrapper around
  peter-evans/create-pull-request for centralized version management
- Reusable workflow `codeql.yml` for GitHub CodeQL security analysis with
  conditional Go setup and SHA-pinned action references
- Reusable workflow `scrut.yml` for standalone scrut CLI snapshot testing
  without Go dependencies
- Exclude `.md` files from Prettier formatting, rely on markdownlint-cli2
  instead

### Changed

- SHA-pin all external action references (`actions/checkout`,
  `actions/setup-go`, `actions/setup-node`, `actions/configure-pages`,
  `actions/upload-pages-artifact`, `actions/deploy-pages`) across all
  reusable workflows
- Bump pinned tool versions across all actions and workflows
- Update GitHub Actions (`actions/checkout`, `actions/setup-go`, etc.) to
  latest major versions
- Bump `picomatch` and `flatted` dev dependencies

### Fixed

- Validate `scrut-env` KEY=VALUE format in `zig-ci.yml`
- SHA-pin `actions/checkout` in `create-release.yml`
- Match markscribe checksum by exact filename to avoid false matches
- Validate `SCRUT_ENV` format in reusable workflows
- Clarify `category-prefix` input description for single-language use
- Address Copilot PR review feedback for Rust workflows and other workflows

## [2.0.0] - 2026-03-09

### Changed

- go-ci.yml now requires consuming repos to have a Makefile with targets:
  `vet`, `test`, and optionally `lint`, `build`, `fmt` (matching enabled jobs)
- go-ci.yml test job runs `make vet` and `make test` instead of direct Go
  commands
- go-ci.yml lint job runs `make lint` instead of `golangci-lint run ./...`
- go-ci.yml build job runs `make build` instead of `go build`
- go-ci.yml format-check job runs `make fmt` instead of inline gofmt/goimports
- go-ci.yml `test-flags` input now only applies when `coverage` is enabled
- Updated `actions/setup-go` from v5 to v6 across go-ci.yml and go-release.yml

### Removed

- go-ci.yml `use-makefile` input (Makefile is now the only execution mode)
- go-ci.yml `build-flags` input (build flags belong in each repo's Makefile)

## [1.0.0] - 2026-03-08

### Added

- Composite action `setup-golangci-lint` to install golangci-lint with a pinned version
- Composite action `setup-goreleaser` to install GoReleaser with a pinned version
- Composite action `setup-scrut` to install scrut CLI testing tool with a pinned version
- Composite action `setup-actionlint` to install actionlint with a pinned version
- Composite action `setup-shfmt` to install shfmt with a pinned version
- Composite action `run-gitleaks` to install and run gitleaks secret scanner
- Composite action `run-trufflehog` to install and run trufflehog secret scanner
- Reusable workflow `go-ci.yml` for Go testing, linting, building, scrut tests, and format checking
- Reusable workflow `go-release.yml` for GoReleaser-based releases
- Reusable workflow `secret-scan.yml` for gitleaks and/or trufflehog scanning
- Reusable workflow `text-lint.yml` for markdownlint, Prettier, cspell, and yamllint
- Reusable workflow `shell-lint.yml` for ShellCheck and shfmt
- Reusable workflow `github-lint.yml` for actionlint
- Reusable workflow `pages-deploy.yml` for GitHub Pages build and deploy
- Reusable workflow `npm-publish.yml` for npm package publishing
- SHA-256 checksum verification for all tool downloads (except scrut, which lacks upstream checksums)
- Cross-platform support for Linux and macOS runners
- Codecov coverage upload support in go-ci workflow
- gofmt and goimports format checking in go-ci workflow
- Scrut inputs for custom build commands (`scrut-build-cmd`), environment variables (`scrut-env`), test directories (`scrut-test-dir`), and setup commands (`scrut-setup-cmd`)
- Self-hosting workflows (`ci.yml`, `gitleaks.yml`, `trufflehog.yml`) as integration tests
- Linter and formatter configuration (markdownlint, Prettier, cspell, editorconfig)

### Fixed

- Install tools to `RUNNER_TEMP` and add to `GITHUB_PATH` instead of writing to system paths
- Extract scrut binary with `--strip-components=1` for correct tarball layout
- Resolve relative paths in `scrut-env` values to absolute paths
- Use `github.token` directly in go-release workflow instead of requiring callers to pass `GITHUB_TOKEN`
- Split composite action args with `read -r -a` using newline-delimited inputs
- Make reusable workflows self-contained (no references to local composite actions)
- Pin all tool versions to exact patch releases with SHA-256 checksum verification
- Avoid running tests twice when coverage is enabled
- Install Codecov CLI for the correct runner OS

[unreleased]: https://github.com/cboone/gh-actions/compare/v2.1.4...HEAD
[2.1.4]: https://github.com/cboone/gh-actions/compare/v2.1.3...v2.1.4
[2.1.3]: https://github.com/cboone/gh-actions/compare/v2.1.2...v2.1.3
[2.1.2]: https://github.com/cboone/gh-actions/compare/v2.1.1...v2.1.2
[2.1.1]: https://github.com/cboone/gh-actions/compare/v2.1.0...v2.1.1
[2.1.0]: https://github.com/cboone/gh-actions/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/cboone/gh-actions/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/cboone/gh-actions/releases/tag/v1.0.0
