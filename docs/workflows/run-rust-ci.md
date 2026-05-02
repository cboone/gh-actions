# run-rust-ci

Run Rust tests, clippy linting, format checking, dependency auditing, and
spell checking. Each check runs as a separate job that can be toggled on or
off.

**Permissions:** `contents: read`

## Inputs

| Name                  | Type    | Default         | Description                                    |
| --------------------- | ------- | --------------- | ---------------------------------------------- |
| `rust-version`        | string  | `"stable"`      | Rust toolchain version to install              |
| `runs-on`             | string  | `ubuntu-latest` | Runner label (Windows is not supported)        |
| `run-test`            | boolean | `true`          | Run cargo test                                 |
| `use-nextest`         | boolean | `false`         | Use cargo-nextest instead of cargo test        |
| `nextest-version`     | string  | `"0.9.133"`     | cargo-nextest version to install               |
| `test-args`           | string  | `""`            | Additional arguments for cargo test or nextest |
| `run-lint`            | boolean | `true`          | Run cargo clippy                               |
| `clippy-args`         | string  | `"-D warnings"` | Arguments passed to clippy after `--`          |
| `run-format-check`    | boolean | `true`          | Run cargo fmt --check                          |
| `run-deny`            | boolean | `false`         | Run cargo deny check (requires deny.toml)      |
| `deny-version`        | string  | `"0.19.4"`      | cargo-deny version to install                  |
| `run-audit`           | boolean | `false`         | Run cargo audit                                |
| `audit-version`       | string  | `"0.22.1"`      | cargo-audit version to install                 |
| `run-typos`           | boolean | `false`         | Run typos spell checking                       |
| `cargo-features`      | string  | `""`            | Cargo features passed via --features           |
| `extra-components`    | string  | `""`            | Extra rustup components to install             |
| `coverage`            | boolean | `false`         | Generate coverage and upload to Codecov        |
| `codecov-cli-version` | string  | `"11.2.8"`      | Codecov CLI version to install                 |
| `codecov-files`       | string  | `lcov.info`     | Coverage file path                             |
| `timeout-minutes`     | number  | `15`            | Job timeout in minutes                         |

## Secrets

| Name            | Required | Description          |
| --------------- | -------- | -------------------- |
| `CODECOV_TOKEN` | No       | Codecov upload token |

## Usage

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/run-rust-ci.yml@v3.0.0
    with:
      run-deny: true
      run-audit: true
      run-typos: true
```

With cargo-nextest and coverage:

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/run-rust-ci.yml@v3.0.0
    with:
      use-nextest: true
      coverage: true
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```
