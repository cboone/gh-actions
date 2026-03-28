# GitHub Actions

There are many, these are mine.

- [Composite Actions](#composite-actions)
  - [setup-golangci-lint](#setup-golangci-lint)
  - [setup-goreleaser](#setup-goreleaser)
  - [setup-scrut](#setup-scrut)
  - [setup-actionlint](#setup-actionlint)
  - [setup-shfmt](#setup-shfmt)
  - [run-gitleaks](#run-gitleaks)
  - [run-trufflehog](#run-trufflehog)
  - [run-markscribe](#run-markscribe)
  - [create-pull-request](#create-pull-request)
- [Reusable Workflows](#reusable-workflows)
  - [create-release](#create-release)
  - [go-ci](#go-ci)
  - [go-release](#go-release)
  - [rust-ci](#rust-ci)
  - [rust-release](#rust-release)
  - [secret-scan](#secret-scan)
  - [text-lint](#text-lint)
  - [shell-lint](#shell-lint)
  - [github-lint](#github-lint)
  - [pages-deploy](#pages-deploy)
  - [codeql](#codeql)
  - [scrut](#scrut)
  - [npm-publish](#npm-publish)
  - [zig-ci](#zig-ci)
  - [zig-release](#zig-release)
- [Versioning](#versioning)
- [License](#license)

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

### run-markscribe

Install markscribe binary and generate a file from a Go template. Replaces
`charmbracelet/readme-scribe` with a direct binary download and SHA-256
checksum verification.

Callers must set `GITHUB_TOKEN` in the step's `env:` for GitHub API access in
templates.

#### Inputs

| Name       | Description                           | Required | Default         |
| ---------- | ------------------------------------- | -------- | --------------- |
| `version`  | markscribe version to install         | No       | `0.8.1`         |
| `template` | Path to the Go template file          | No       | `README.md.tpl` |
| `write-to` | Output file path (empty for stdout)   | No       | `README.md`     |

#### Usage

```yaml
- uses: cboone/gh-actions/actions/run-markscribe@main
  env:
    GITHUB_TOKEN: ${{ secrets.PERSONAL_GITHUB_TOKEN }}
  with:
    template: "templates/README.md.tpl"
    write-to: "README.md"
```

### create-pull-request

SHA-pinned wrapper around
[peter-evans/create-pull-request](https://github.com/peter-evans/create-pull-request).
Centralizes version management so downstream repos do not pin the upstream action
individually.

#### Inputs

| Name             | Description                                        | Required | Default                                |
| ---------------- | -------------------------------------------------- | -------- | -------------------------------------- |
| `token`          | GITHUB_TOKEN or a personal access token            | No       | `${{ github.token }}`                  |
| `branch`         | The pull request branch name                       | No       | `create-pull-request/patch`            |
| `delete-branch`  | Delete the branch when the PR is merged or closed  | No       | `false`                                |
| `base`           | Pull request base branch                           | No       | Branch checked out in the workflow     |
| `commit-message` | The commit message for the changes                 | No       | `[create-pull-request] automated ...`  |
| `title`          | The title of the pull request                      | No       | `Changes by create-pull-request ...`   |
| `body`           | The body of the pull request                       | No       | `""`                                   |
| `labels`         | Comma or newline-separated labels                  | No       | `""`                                   |
| `assignees`      | Comma or newline-separated assignees               | No       | `""`                                   |
| `draft`          | Create the pull request as a draft                 | No       | `false`                                |

#### Outputs

| Name                      | Description                                          |
| ------------------------- | ---------------------------------------------------- |
| `pull-request-number`     | The pull request number                              |
| `pull-request-url`        | The URL of the pull request                          |
| `pull-request-operation`  | Operation performed: created, updated, closed, none  |
| `pull-request-head-sha`   | The commit SHA of the pull request branch            |
| `pull-request-branch`     | The branch name of the pull request                  |

#### Usage

```yaml
- uses: cboone/gh-actions/actions/create-pull-request@main
  with:
    branch: chore/update-data
    commit-message: "chore: update generated data"
    title: "chore: update generated data"
    body: "Automated update."
    labels: automation
    delete-branch: true
```

## Reusable Workflows

### create-release

Create a GitHub Release from a version tag, extracting release notes from a
changelog file in Keep a Changelog format.

**Permissions:** `contents: write`

#### Inputs

| Name              | Type    | Default          | Description                          |
| ----------------- | ------- | ---------------- | ------------------------------------ |
| `changelog-file`  | string  | `CHANGELOG.md`   | Path to the changelog file           |
| `draft`           | boolean | `false`          | Create the release as a draft        |
| `prerelease`      | boolean | `false`          | Mark the release as a prerelease     |
| `runs-on`         | string  | `ubuntu-latest`  | Runner label (Windows not supported) |
| `timeout-minutes` | number  | `10`             | Job timeout in minutes               |

#### Usage

```yaml
jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/create-release.yml@main
```

### go-ci

Run Go tests, linting, build verification, scrut CLI tests, and format checking.
Each check runs as a separate job that can be toggled on or off.

Consuming repos must provide a Makefile with targets matching each enabled job:
`vet`, `test`, `lint`, `build`, `fmt`. The `fmt` target must be a format check
(exit non-zero when files need formatting), not a write operation.

**Permissions:** `contents: read`

#### Inputs

| Name                    | Type    | Default          | Description                                                |
| ----------------------- | ------- | ---------------- | ---------------------------------------------------------- |
| `go-version`            | string  | `""`             | Go version to install. When set, overrides go-version-file |
| `go-version-file`       | string  | `go.mod`         | File to read the Go version from                           |
| `runs-on`               | string  | `ubuntu-latest`  | Runner label (Windows is not supported)                    |
| `run-lint`              | boolean | `true`           | Run `make lint`                                            |
| `golangci-lint-version` | string  | `"2.11.2"`       | golangci-lint version to install                           |
| `run-scrut`             | boolean | `false`          | Run scrut CLI tests                                        |
| `scrut-build-cmd`       | string  | `go build ./...` | Command to build the binary for scrut tests                |
| `scrut-env`             | string  | `""`             | Newline-delimited KEY=VALUE env vars for scrut tests       |
| `scrut-test-dir`        | string  | `tests/`         | Directory containing scrut test files                      |
| `scrut-setup-cmd`       | string  | `""`             | Optional shell command to run before scrut tests           |
| `run-format-check`      | boolean | `false`          | Run `make fmt` format check                                |
| `run-build`             | boolean | `false`          | Run `make build`                                           |
| `test-flags`            | string  | `"-race"`        | Flags for go test (only used when coverage is enabled)     |
| `coverage`              | boolean | `false`          | Generate coverage and upload to Codecov                    |
| `codecov-cli-version`   | string  | `"10.4.0"`       | Codecov CLI version to install                             |
| `codecov-files`         | string  | `coverage.out`   | Coverage file path for Codecov upload                      |
| `timeout-minutes`       | number  | `15`             | Job timeout in minutes                                     |

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

| Name                 | Required | Description                    |
| -------------------- | -------- | ------------------------------ |
| `HOMEBREW_TAP_TOKEN` | No       | Token for Homebrew tap updates |

#### Usage

```yaml
jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/go-release.yml@main
    with:
      goreleaser-version: "2.14.2"
    secrets:
      HOMEBREW_TAP_TOKEN: ${{ secrets.HOMEBREW_TAP_TOKEN }}
```

### rust-ci

Run Rust tests, clippy linting, format checking, dependency auditing, and spell
checking. Each check runs as a separate job that can be toggled on or off.

**Permissions:** `contents: read`

#### Inputs

| Name                 | Type    | Default          | Description                                              |
| -------------------- | ------- | ---------------- | -------------------------------------------------------- |
| `rust-version`       | string  | `"stable"`       | Rust toolchain version to install                        |
| `runs-on`            | string  | `ubuntu-latest`  | Runner label (Windows is not supported)                  |
| `run-test`           | boolean | `true`           | Run cargo test                                           |
| `use-nextest`        | boolean | `false`          | Use cargo-nextest instead of cargo test                  |
| `nextest-version`    | string  | `"0.9.132"`      | cargo-nextest version to install                         |
| `test-args`          | string  | `""`             | Additional arguments for cargo test or nextest           |
| `run-lint`           | boolean | `true`           | Run cargo clippy                                         |
| `clippy-args`        | string  | `"-D warnings"`  | Arguments passed to clippy after `--`                    |
| `run-format-check`   | boolean | `true`           | Run cargo fmt --check                                    |
| `run-deny`           | boolean | `false`          | Run cargo deny check (requires deny.toml)                |
| `deny-version`       | string  | `"0.19.0"`       | cargo-deny version to install                            |
| `run-audit`          | boolean | `false`          | Run cargo audit                                          |
| `audit-version`      | string  | `"0.22.1"`       | cargo-audit version to install                           |
| `run-typos`          | boolean | `false`          | Run typos spell checking                                 |
| `cargo-features`     | string  | `""`             | Cargo features passed via --features                     |
| `extra-components`   | string  | `""`             | Extra rustup components to install                       |
| `coverage`           | boolean | `false`          | Generate coverage and upload to Codecov                  |
| `codecov-cli-version`| string  | `"10.4.0"`       | Codecov CLI version to install                           |
| `codecov-files`      | string  | `lcov.info`      | Coverage file path                                       |
| `timeout-minutes`    | number  | `15`             | Job timeout in minutes                                   |

#### Secrets

| Name            | Required | Description          |
| --------------- | -------- | -------------------- |
| `CODECOV_TOKEN` | No       | Codecov upload token |

#### Usage

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/rust-ci.yml@main
    with:
      run-deny: true
      run-audit: true
      run-typos: true
```

With cargo-nextest and coverage:

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/rust-ci.yml@main
    with:
      use-nextest: true
      coverage: true
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

### rust-release

Build Rust binaries for multiple targets and publish them as a GitHub Release.
Supports matrix builds across different runners and optional Homebrew formula
updates.

**Permissions:** `contents: write`

#### Inputs

| Name                    | Type    | Default    | Description                                                       |
| ----------------------- | ------- | ---------- | ----------------------------------------------------------------- |
| `targets`               | string  |            | JSON array of `{"target","runner"}` objects (required)            |
| `binary-name`           | string  | `""`       | Binary name (extracted from Cargo.toml if empty)                  |
| `rust-version`          | string  | `"stable"` | Rust toolchain version to install                                 |
| `build-args`            | string  | `""`       | Additional arguments for cargo build                              |
| `archive-prefix`        | string  | `""`       | Override archive prefix (default: {binary}-{version})             |
| `update-homebrew`       | boolean | `false`    | Update a Homebrew formula after releasing                         |
| `homebrew-tap`          | string  | `""`       | Homebrew tap repository (e.g. user/homebrew-tap)                  |
| `homebrew-formula-path` | string  | `""`       | Path to the formula in the tap repo (e.g. Formula/mytool.rb)      |
| `homebrew-license`      | string  | `"MIT"`    | SPDX license identifier for the Homebrew formula                  |
| `timeout-minutes`       | number  | `30`       | Job timeout in minutes                                            |

#### Secrets

| Name                 | Required | Description                    |
| -------------------- | -------- | ------------------------------ |
| `HOMEBREW_TAP_TOKEN` | No       | Token for Homebrew tap updates |

#### Usage

```yaml
jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/rust-release.yml@main
    with:
      targets: >-
        [
          {"target": "aarch64-apple-darwin", "runner": "macos-latest"},
          {"target": "x86_64-apple-darwin", "runner": "macos-latest"},
          {"target": "x86_64-unknown-linux-gnu", "runner": "ubuntu-latest"}
        ]
```

With Homebrew formula updates:

```yaml
jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/rust-release.yml@main
    with:
      targets: >-
        [
          {"target": "aarch64-apple-darwin", "runner": "macos-latest"},
          {"target": "x86_64-unknown-linux-gnu", "runner": "ubuntu-latest"}
        ]
      update-homebrew: true
      homebrew-tap: myuser/homebrew-tap
      homebrew-formula-path: Formula/mytool.rb
    secrets:
      HOMEBREW_TAP_TOKEN: ${{ secrets.HOMEBREW_TAP_TOKEN }}
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

### codeql

Run GitHub CodeQL security analysis. SHA-pins all `github/codeql-action`
sub-actions internally and conditionally sets up Go when the language list
includes it.

**Permissions:** `contents: read`, `security-events: write`

#### Inputs

| Name              | Type   | Default                  | Description                                                |
| ----------------- | ------ | ------------------------ | ---------------------------------------------------------- |
| `languages`       | string | `go`                     | Comma-separated CodeQL languages to analyze                |
| `queries`         | string | `security-and-quality`   | CodeQL query suite to run                                  |
| `go-version`      | string | `""`                     | Go version to install. When set, overrides go-version-file |
| `go-version-file` | string | `go.mod`                 | File to read the Go version from                           |
| `category-prefix` | string | `/language:`             | Prefix for the CodeQL analysis category                    |
| `runs-on`         | string | `macos-latest`           | Runner label                                               |
| `timeout-minutes` | number | `30`                     | Job timeout in minutes                                     |

#### Usage

```yaml
jobs:
  codeql:
    uses: cboone/gh-actions/.github/workflows/codeql.yml@main
    with:
      languages: go
      go-version: "1.25"
    permissions:
      contents: read
      security-events: write
```

### scrut

Run scrut CLI snapshot tests. Designed for non-Go projects (e.g., shell plugins)
that need scrut testing without Go setup or build steps. Installs scrut with
SHA-256 checksum verification and runs tests against the specified directory.

**Permissions:** `contents: read`

#### Inputs

| Name              | Type   | Default         | Description                                          |
| ----------------- | ------ | --------------- | ---------------------------------------------------- |
| `scrut-version`   | string | `"0.4.3"`       | scrut version to install (checksums pinned to this)  |
| `scrut-shell`     | string | `""`            | Shell for `--shell` flag (e.g., "zsh", "bash")       |
| `scrut-test-dir`  | string | `"tests/"`      | Directory containing scrut test files                |
| `scrut-env`       | string | `""`            | Newline-delimited KEY=VALUE env vars for scrut tests |
| `scrut-setup-cmd` | string | `""`            | Shell command to run before scrut tests              |
| `runs-on`         | string | `ubuntu-latest` | Runner label (Windows is not supported)              |
| `timeout-minutes` | number | `10`            | Job timeout in minutes                               |

#### Usage

```yaml
jobs:
  scrut:
    uses: cboone/gh-actions/.github/workflows/scrut.yml@main
```

With a custom shell and environment variables:

```yaml
jobs:
  scrut:
    uses: cboone/gh-actions/.github/workflows/scrut.yml@main
    with:
      scrut-shell: zsh
      scrut-env: |
        MY_PLUGIN_DIR=./src
      scrut-setup-cmd: "make build"
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

### zig-ci

Run Zig tests, format checking, build verification, cross-compilation checks,
and scrut CLI tests. Each check runs as a separate job that can be toggled on or
off.

Unlike go-ci.yml, this workflow runs Zig commands directly (not via Makefile
targets) since Zig projects idiomatically use `build.zig` as their build system.

**Permissions:** `contents: read`

#### Inputs

| Name                | Type    | Default         | Description                                          |
| ------------------- | ------- | --------------- | ---------------------------------------------------- |
| `zig-version`       | string  |                 | Zig version to install (required)                    |
| `runs-on`           | string  | `ubuntu-latest` | Runner label (Windows is not supported)              |
| `run-test`          | boolean | `true`          | Run `zig build test`                                 |
| `run-fmt`           | boolean | `true`          | Run `zig fmt --check src/ build.zig`                 |
| `run-build`         | boolean | `true`          | Run `zig build`                                      |
| `run-cross-compile` | boolean | `false`         | Build all cross-compilation targets                  |
| `cross-targets`     | string  | (see below)     | Space-separated Zig target triples                   |
| `run-scrut`         | boolean | `false`         | Run scrut CLI tests                                  |
| `scrut-build-cmd`   | string  | `zig build`     | Command to build the binary for scrut tests          |
| `scrut-env`         | string  | `""`            | Newline-delimited KEY=VALUE env vars for scrut tests |
| `scrut-test-dir`    | string  | `tests/`        | Directory containing scrut test files                |
| `scrut-setup-cmd`   | string  | `""`            | Optional shell command to run before scrut tests     |
| `timeout-minutes`   | number  | `20`            | Job timeout in minutes                               |

Default `cross-targets`:

```text
x86_64-linux-gnu aarch64-linux-gnu x86_64-macos aarch64-macos x86_64-windows-gnu
```

#### Usage

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/zig-ci.yml@main
    with:
      zig-version: "0.14.1"
      run-cross-compile: true
```

With scrut CLI tests:

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/zig-ci.yml@main
    with:
      zig-version: "0.14.1"
      run-scrut: true
      scrut-build-cmd: "zig build"
      scrut-env: |
        MY_BIN=./zig-out/bin/my-tool
```

### zig-release

Build a Zig binary for multiple targets and create a GitHub Release with
packaged artifacts and SHA-256 checksums. Leverages Zig's native
cross-compilation from a single runner (no matrix, no macOS runners).

**Permissions:** `contents: write`

#### Inputs

| Name              | Type   | Default         | Description                          |
| ----------------- | ------ | --------------- | ------------------------------------ |
| `zig-version`     | string |                 | Zig version to install (required)    |
| `binary-name`     | string |                 | Name of the binary (required)        |
| `targets`         | string | (see below)     | Space-separated Zig target triples   |
| `optimize`        | string | `ReleaseSafe`   | Zig optimization level               |
| `runs-on`         | string | `ubuntu-latest` | Runner label (Windows not supported) |
| `timeout-minutes` | number | `30`            | Job timeout in minutes               |

Default `targets`:

```text
x86_64-linux-gnu aarch64-linux-gnu x86_64-macos aarch64-macos x86_64-windows-gnu
```

#### Usage

```yaml
jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/zig-release.yml@main
    with:
      zig-version: "0.14.1"
      binary-name: "my-tool"
```

## Versioning

This project uses [Semantic Versioning](https://semver.org/). Use `@v2` for
stability (or `@v1` if your repo has not yet migrated to Makefile targets).

### Version bumps

- **Patch** (e.g., v1.0.0 to v1.0.1): bug fixes, tool version bumps that do not
  change behavior, documentation updates.
- **Minor** (e.g., v1.0.0 to v1.1.0): new optional inputs, new actions or
  workflows, additive changes that do not affect existing callers.
- **Major** (e.g., v1 to v2): breaking changes. A **breaking change** is any
  modification that requires callers to update their workflow files: renaming or
  removing an input, changing a default in a way that alters behavior, or
  removing an action or workflow.

### Release process

Releases are created with the `/release` skill, which analyzes conventional
commits, recommends a version bump, updates CHANGELOG.md, creates a release
commit, and tags it. The process produces two tags:

1. **Exact version tag** (e.g., `v1.2.0`): a permanent, immutable tag pointing
   to the release commit.
1. **Floating major tag** (e.g., `v1`): force-updated to point to the same
   commit as the latest exact tag in that major version. Callers who reference
   `@v1` automatically pick up non-breaking updates.

After tagging locally, push both tags:

```bash
git push origin main v1.2.0 v1
```

### Pinning options for callers

- `@v2`: tracks the latest v2.x.y release (recommended, requires Makefile targets).
- `@v1`: tracks the latest v1.x.y release (for repos not yet migrated to Makefile targets).
- `@v2.0.0`: pinned to an exact release for stricter control.
- `@main`: latest development (for testing).

## License

[MIT License](./LICENSE). TL;DR: Do whatever you want with this software, just
keep the copyright notice included. The authors aren't liable if something goes
wrong.
