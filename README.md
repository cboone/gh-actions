# Gh Actions

A collection of reusable GitHub Actions for CI/CD workflows.

**Design goals:**

- **Security** -- pinned tool versions with SHA-256 checksum verification on
  every download.
- **Simplicity** -- one workflow call replaces dozens of lines of duplicated
  YAML.
- **Consistency** -- the same tool versions and flags across all consuming
  repositories.

## Table of Contents

- [Quick Start](#quick-start)
- [Composite Actions](#composite-actions)
  - [setup-golangci-lint](#setup-golangci-lint)
  - [setup-goreleaser](#setup-goreleaser)
  - [setup-scrut](#setup-scrut)
  - [setup-actionlint](#setup-actionlint)
  - [setup-shfmt](#setup-shfmt)
  - [run-gitleaks](#run-gitleaks)
  - [run-trufflehog](#run-trufflehog)
- [Reusable Workflows](#reusable-workflows)
  - [go-ci](#go-ci)
  - [go-release](#go-release)
  - [secret-scan](#secret-scan)
  - [text-lint](#text-lint)
  - [shell-lint](#shell-lint)
  - [github-lint](#github-lint)
  - [pages-deploy](#pages-deploy)
  - [npm-publish](#npm-publish)
- [Versioning](#versioning)
- [License](#license)

## Quick Start

A typical Go project CI workflow shrinks from ~25 lines of setup to a single
workflow call:

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  go:
    uses: cboone/gh-actions/.github/workflows/go-ci.yml@main
    with:
      run-lint: true
      coverage: true
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

> Use `@main` until v1.0.0 is tagged. After that, use `@v1`.

## Composite Actions

### setup-golangci-lint

Install golangci-lint binary with a pinned version.

#### Inputs

| Name      | Description                      | Required | Default  |
| --------- | -------------------------------- | -------- | -------- |
| `version` | golangci-lint version to install | No       | `2.11.2` |

#### Usage

```yaml
- uses: cboone/gh-actions/actions/setup-golangci-lint@main
  with:
    version: "2.11.2"
- run: golangci-lint run ./...
```

### setup-goreleaser

Install GoReleaser binary with a pinned version.

#### Inputs

| Name      | Description                   | Required | Default  |
| --------- | ----------------------------- | -------- | -------- |
| `version` | GoReleaser version to install | No       | `2.14.2` |

#### Usage

```yaml
- uses: cboone/gh-actions/actions/setup-goreleaser@main
  with:
    version: "2.14.2"
- run: goreleaser release --clean
```

### setup-scrut

Install scrut CLI testing tool with a pinned version.

#### Inputs

| Name      | Description              | Required | Default |
| --------- | ------------------------ | -------- | ------- |
| `version` | scrut version to install | No       | `0.4.3` |

#### Usage

```yaml
- uses: cboone/gh-actions/actions/setup-scrut@main
- run: scrut test tests/
```

### setup-actionlint

Install actionlint binary with a pinned version.

#### Inputs

| Name      | Description                   | Required | Default  |
| --------- | ----------------------------- | -------- | -------- |
| `version` | actionlint version to install | No       | `1.7.11` |

#### Usage

```yaml
- uses: cboone/gh-actions/actions/setup-actionlint@main
- run: actionlint
```

### setup-shfmt

Install shfmt binary with a pinned version.

#### Inputs

| Name      | Description              | Required | Default  |
| --------- | ------------------------ | -------- | -------- |
| `version` | shfmt version to install | No       | `3.12.0` |

#### Usage

```yaml
- uses: cboone/gh-actions/actions/setup-shfmt@main
- run: shfmt -d .
```

### run-gitleaks

Install gitleaks binary and run a scan.

#### Inputs

| Name      | Description                   | Required | Default             |
| --------- | ----------------------------- | -------- | ------------------- |
| `version` | gitleaks version to install   | No       | `8.30.0`            |
| `args`    | Arguments to pass to gitleaks | No       | `detect --source .` |

#### Usage

```yaml
- uses: cboone/gh-actions/actions/run-gitleaks@main
```

### run-trufflehog

Install trufflehog binary and run a scan.

#### Inputs

| Name      | Description                     | Required | Default                    |
| --------- | ------------------------------- | -------- | -------------------------- |
| `version` | trufflehog version to install   | No       | `3.93.7`                   |
| `args`    | Arguments to pass to trufflehog | No       | `filesystem --directory .` |

#### Usage

```yaml
- uses: cboone/gh-actions/actions/run-trufflehog@main
```

## Reusable Workflows

### go-ci

Run Go tests, linting, build verification, scrut CLI tests, and format checking.
Each check runs as a separate job that can be toggled on or off.

**Permissions:** `contents: read`

#### Inputs

| Name                    | Type    | Default         | Description                                                |
| ----------------------- | ------- | --------------- | ---------------------------------------------------------- |
| `go-version`            | string  | `""`            | Go version to install. When set, overrides go-version-file |
| `go-version-file`       | string  | `go.mod`        | File to read the Go version from                           |
| `runs-on`               | string  | `ubuntu-latest` | Runner label (Windows is not supported)                    |
| `run-lint`              | boolean | `true`          | Run golangci-lint                                          |
| `golangci-lint-version` | string  | `"2.11.2"`      | golangci-lint version to install                           |
| `run-scrut`             | boolean | `false`         | Run scrut CLI tests                                        |
| `run-format-check`      | boolean | `false`         | Run gofmt/goimports format check                           |
| `run-build`             | boolean | `false`         | Run go build                                               |
| `build-flags`           | string  | `""`            | Additional flags for go build                              |
| `test-flags`            | string  | `"-race"`       | Flags for go test                                          |
| `coverage`              | boolean | `false`         | Generate coverage and upload to Codecov                    |
| `codecov-cli-version`   | string  | `"10.4.0"`      | Codecov CLI version to install                             |
| `codecov-files`         | string  | `coverage.out`  | Coverage file path for Codecov upload                      |
| `timeout-minutes`       | number  | `15`            | Job timeout in minutes                                     |

#### Secrets

| Name            | Required | Description          |
| --------------- | -------- | -------------------- |
| `CODECOV_TOKEN` | No       | Codecov upload token |

#### Usage

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/go-ci.yml@main
    with:
      run-lint: true
      run-format-check: true
      coverage: true
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

### go-release

Run GoReleaser to build and publish a Go release.

**Permissions:** `contents: write`

#### Inputs

| Name                 | Type   | Default           | Description                          |
| -------------------- | ------ | ----------------- | ------------------------------------ |
| `go-version-file`    | string | `go.mod`          | File to read the Go version from     |
| `runs-on`            | string | `ubuntu-latest`   | Runner label (Windows not supported) |
| `goreleaser-version` | string | `"2.14.2"`        | GoReleaser version to install        |
| `goreleaser-args`    | string | `release --clean` | Arguments to pass to goreleaser      |
| `timeout-minutes`    | number | `30`              | Job timeout in minutes               |

#### Secrets

| Name                 | Required | Description                        |
| -------------------- | -------- | ---------------------------------- |
| `GITHUB_TOKEN`       | Yes      | Token for creating GitHub releases |
| `HOMEBREW_TAP_TOKEN` | No       | Token for Homebrew tap updates     |

#### Usage

```yaml
jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/go-release.yml@main
    with:
      goreleaser-version: "2.14.2"
    secrets:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### secret-scan

Run gitleaks, trufflehog, or both to scan for leaked secrets. Supports
full-history and working-tree scan scopes.

**Permissions:** `contents: read`

#### Inputs

| Name                 | Type   | Default        | Description                                      |
| -------------------- | ------ | -------------- | ------------------------------------------------ |
| `tool`               | string | `gitleaks`     | Which tool to run: gitleaks, trufflehog, or both |
| `scan-scope`         | string | `full-history` | Scan scope: full-history or working-tree         |
| `gitleaks-version`   | string | `"8.30.0"`     | gitleaks version to install                      |
| `trufflehog-version` | string | `"3.93.7"`     | trufflehog version to install                    |
| `fetch-depth`        | number | `0`            | Git fetch depth (0 for full history)             |
| `allowlist-config`   | string | `""`           | Path to a gitleaks allowlist config file         |
| `timeout-minutes`    | number | `15`           | Job timeout in minutes                           |

#### Usage

```yaml
jobs:
  scan:
    uses: cboone/gh-actions/.github/workflows/secret-scan.yml@main
    with:
      tool: both
```

### text-lint

Run Markdown linting, Prettier formatting checks, cspell spelling checks,
and yamllint YAML validation. Each tool can be toggled independently.

**Permissions:** `contents: read`

#### Inputs

| Name               | Type    | Default | Description                |
| ------------------ | ------- | ------- | -------------------------- |
| `node-version`     | string  | `"22"`  | Node.js version to install |
| `run-markdownlint` | boolean | `true`  | Run markdownlint-cli2      |
| `run-prettier`     | boolean | `true`  | Run Prettier format check  |
| `run-cspell`       | boolean | `false` | Run cspell spell checker   |
| `run-yamllint`     | boolean | `false` | Run yamllint               |
| `timeout-minutes`  | number  | `10`    | Job timeout in minutes     |

#### Usage

```yaml
jobs:
  text:
    uses: cboone/gh-actions/.github/workflows/text-lint.yml@main
    with:
      run-cspell: true
```

### shell-lint

Run ShellCheck and shfmt on shell scripts. Automatically discovers scripts
by file extension and MIME type.

**Permissions:** `contents: read`

#### Inputs

| Name              | Type    | Default    | Description              |
| ----------------- | ------- | ---------- | ------------------------ |
| `run-shellcheck`  | boolean | `true`     | Run ShellCheck           |
| `run-shfmt`       | boolean | `true`     | Run shfmt format check   |
| `shfmt-version`   | string  | `"3.12.0"` | shfmt version to install |
| `timeout-minutes` | number  | `10`       | Job timeout in minutes   |

#### Usage

```yaml
jobs:
  shell:
    uses: cboone/gh-actions/.github/workflows/shell-lint.yml@main
```

### github-lint

Run actionlint to validate GitHub Actions workflow files.

**Permissions:** `contents: read`

#### Inputs

| Name                 | Type   | Default    | Description                   |
| -------------------- | ------ | ---------- | ----------------------------- |
| `actionlint-version` | string | `"1.7.11"` | actionlint version to install |
| `timeout-minutes`    | number | `10`       | Job timeout in minutes        |

#### Usage

```yaml
jobs:
  github:
    uses: cboone/gh-actions/.github/workflows/github-lint.yml@main
```

### pages-deploy

Build a static site and deploy it to GitHub Pages. Optionally sets up Go
and/or Node.js before running the build command.

**Permissions:** `contents: read`, `pages: write`, `id-token: write`

#### Inputs

| Name              | Type    | Default         | Description                          |
| ----------------- | ------- | --------------- | ------------------------------------ |
| `build-command`   | string  |                 | Command to build the site (required) |
| `artifact-path`   | string  | `./_site`       | Path to the built site directory     |
| `runs-on`         | string  | `ubuntu-latest` | Runner label                         |
| `setup-go`        | boolean | `false`         | Set up Go before building            |
| `go-version-file` | string  | `go.mod`        | File to read the Go version from     |
| `setup-node`      | boolean | `false`         | Set up Node.js before building       |
| `node-version`    | string  | `"22"`          | Node.js version to install           |
| `timeout-minutes` | number  | `15`            | Job timeout in minutes               |

#### Usage

```yaml
jobs:
  pages:
    uses: cboone/gh-actions/.github/workflows/pages-deploy.yml@main
    with:
      build-command: "npm run build"
      artifact-path: ./dist
      setup-node: true
```

### npm-publish

Publish an npm package to a registry. Detects lockfile presence to choose
between `npm ci` and `npm install`.

**Permissions:** `contents: read`, `packages: write`

#### Inputs

| Name              | Type   | Default                      | Description                |
| ----------------- | ------ | ---------------------------- | -------------------------- |
| `node-version`    | string | `"22"`                       | Node.js version to install |
| `registry-url`    | string | `https://npm.pkg.github.com` | npm registry URL           |
| `timeout-minutes` | number | `10`                         | Job timeout in minutes     |

#### Secrets

| Name              | Required | Description                               |
| ----------------- | -------- | ----------------------------------------- |
| `NODE_AUTH_TOKEN` | Yes      | Authentication token for the npm registry |

#### Usage

```yaml
jobs:
  publish:
    uses: cboone/gh-actions/.github/workflows/npm-publish.yml@main
    secrets:
      NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Versioning

This project uses [Semantic Versioning](https://semver.org/). Once v1.0.0 is
tagged, a floating `v1` tag will track the latest v1.x.y release.

Use `@main` until v1.0.0 is tagged. After that, use `@v1` for stability.

A **breaking change** is any modification that requires callers to update their
workflow files: renaming or removing an input, changing a default in a way that
alters behavior, or removing an action or workflow.

## License

[MIT License](./LICENSE). TL;DR: Do whatever you want with this software, just
keep the copyright notice included. The authors aren't liable if something goes
wrong.
