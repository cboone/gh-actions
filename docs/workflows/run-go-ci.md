# run-go-ci

Run Go tests, linting, build verification, scrut CLI tests, and format
checking. Each check runs as a separate job that can be toggled on or off.

Consuming repos must provide a Makefile with targets matching each enabled
job: `vet`, `test`, `lint`, `build`, `fmt`. The `fmt` target must be a
format check (exit non-zero when files need formatting), not a write
operation.

With `run-scrut: true`, Linux arm64 and macOS x86-64 build Scrut v0.4.3 from
pinned source using Rust 1.97.1 and the repository's reviewed Cargo.lock.
The helper, lockfile and version script are fetched at the workflow's own
repository and commit; those source builds require GitHub.com job context.
Linux x86-64 and macOS arm64 use checksum-verified release binaries. See the
[investigation and removal criteria](../scrut-installation-investigation.md).

**Permissions:** `contents: read`

Source builds run with a fresh Cargo home outside the consumer checkout,
reject ancestor Cargo configuration, and clear compiler, target and profile
overrides. Network proxy and certificate settings remain available.

The replacement build script reports `scrut 0.4.3` from package metadata;
the installer validates that exact version before exposing the executable.

## Inputs

| Name                    | Type    | Default          | Description                                                |
| ----------------------- | ------- | ---------------- | ---------------------------------------------------------- |
| `go-version`            | string  | `""`             | Go version to install. When set, overrides go-version-file |
| `go-version-file`       | string  | `go.mod`         | File to read the Go version from                           |
| `runs-on`               | string  | `ubuntu-latest`  | Runner label (Windows is not supported)                    |
| `run-lint`              | boolean | `true`           | Run `make lint`                                            |
| `golangci-lint-version` | string  | `"2.13.2"`       | golangci-lint version to install                           |
| `run-scrut`             | boolean | `false`          | Run scrut CLI tests                                        |
| `scrut-build-cmd`       | string  | `go build ./...` | Command to build the binary for scrut tests                |
| `scrut-env`             | string  | `""`             | Newline-delimited KEY=VALUE env vars for scrut tests       |
| `scrut-test-dir`        | string  | `tests/`         | Directory containing scrut test files                      |
| `scrut-setup-cmd`       | string  | `""`             | Optional shell command to run before scrut tests           |
| `run-format-check`      | boolean | `false`          | Run `make fmt` format check                                |
| `run-build`             | boolean | `false`          | Run `make build`                                           |
| `test-flags`            | string  | `"-race"`        | Flags for go test (only used when coverage is enabled)     |
| `coverage`              | boolean | `false`          | Generate coverage and upload to Codecov                    |
| `codecov-cli-version`   | string  | `"11.3.1"`       | Codecov CLI version to install                             |
| `codecov-files`         | string  | `coverage.out`   | Coverage file path for Codecov upload                      |
| `timeout-minutes`       | number  | `15`             | Job timeout in minutes                                     |

`test-flags` is split on whitespace into separate arguments. Quoting,
escaping, glob expansion and variable expansion are not supported, and a value
containing a newline fails the job rather than losing every line after the
first. `codecov-files` is a single path and may contain spaces.

## Secrets

| Name            | Required | Description          |
| --------------- | -------- | -------------------- |
| `CODECOV_TOKEN` | No       | Codecov upload token |

## Usage

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/run-go-ci.yml@v4.1.0
    with:
      run-lint: true
      run-format-check: true
      coverage: true
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```
