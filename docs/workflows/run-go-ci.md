# run-go-ci

Run Go tests, linting, build verification, scrut CLI tests, and format
checking. Each check runs as a separate job that can be toggled on or off.

Consuming repos must provide a Makefile with targets matching each enabled
job: `vet`, `test`, `lint`, `build`, `fmt`. The `fmt` target must be a
format check (exit non-zero when files need formatting), not a write
operation.

**Permissions:** `contents: read`

## Inputs

| Name                    | Type    | Default          | Description                                                |
| ----------------------- | ------- | ---------------- | ---------------------------------------------------------- |
| `go-version`            | string  | `""`             | Go version to install. When set, overrides go-version-file |
| `go-version-file`       | string  | `go.mod`         | File to read the Go version from                           |
| `runs-on`               | string  | `ubuntu-latest`  | Runner label (Windows is not supported)                    |
| `run-lint`              | boolean | `true`           | Run `make lint`                                            |
| `golangci-lint-version` | string  | `"2.11.4"`       | golangci-lint version to install                           |
| `run-scrut`             | boolean | `false`          | Run scrut CLI tests                                        |
| `scrut-build-cmd`       | string  | `go build ./...` | Command to build the binary for scrut tests                |
| `scrut-env`             | string  | `""`             | Newline-delimited KEY=VALUE env vars for scrut tests       |
| `scrut-test-dir`        | string  | `tests/`         | Directory containing scrut test files                      |
| `scrut-setup-cmd`       | string  | `""`             | Optional shell command to run before scrut tests           |
| `run-format-check`      | boolean | `false`          | Run `make fmt` format check                                |
| `run-build`             | boolean | `false`          | Run `make build`                                           |
| `test-flags`            | string  | `"-race"`        | Flags for go test (only used when coverage is enabled)     |
| `coverage`              | boolean | `false`          | Generate coverage and upload to Codecov                    |
| `codecov-cli-version`   | string  | `"11.2.8"`       | Codecov CLI version to install                             |
| `codecov-files`         | string  | `coverage.out`   | Coverage file path for Codecov upload                      |
| `timeout-minutes`       | number  | `15`             | Job timeout in minutes                                     |

## Secrets

| Name            | Required | Description          |
| --------------- | -------- | -------------------- |
| `CODECOV_TOKEN` | No       | Codecov upload token |

## Usage

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/run-go-ci.yml@v3.0.0
    with:
      run-lint: true
      run-format-check: true
      coverage: true
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```
