# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Self-hosting workflows (`ci.yml`, `gitleaks.yml`, `trufflehog.yml`) as integration tests
- Linter and formatter configuration (markdownlint, Prettier, cspell, editorconfig)
- Copilot review instructions for repository-specific conventions
