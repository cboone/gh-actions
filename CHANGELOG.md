# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Versioning strategy now uses only exact version tags (e.g., `v2.2.0`);
  floating major tags (`v1`, `v2`) are discontinued

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

[unreleased]: https://github.com/cboone/gh-actions/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/cboone/gh-actions/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/cboone/gh-actions/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/cboone/gh-actions/releases/tag/v1.0.0
