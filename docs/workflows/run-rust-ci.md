# run-rust-ci

Run Rust tests, clippy linting, format checking, dependency auditing, and
spell checking. Each check runs as a separate job that can be toggled on or
off.

The Rust toolchain is resolved from `rust-version` if set; otherwise the
workflow reads the channel from `rust-toolchain-file` (default
`rust-toolchain.toml`); otherwise it falls back to a legacy `rust-toolchain`
file at the repo root. At least one of these must resolve to a value or the
workflow fails fast.

cargo-deny and cargo-nextest verify their downloads against a checksum file
their upstreams publish, so overriding `deny-version` or `nextest-version`
needs nothing else. cargo-audit and cargo-llvm-cov publish no such file, so
this workflow carries their digests in `audit-checksums` and
`llvm-cov-checksums`. Overriding either version means passing that version's
lines too:

```text
<sha256>  <version>  <target triple>
```

Entries are keyed by version as well as target because cargo-llvm-cov's
archive name carries no version, so a file name alone cannot tell two
releases apart. A version with no matching line is refused before anything is
downloaded, rather than verified against another release's digest. The four
supported targets are `x86_64-unknown-linux-gnu`,
`aarch64-unknown-linux-gnu`, `x86_64-apple-darwin` and
`aarch64-apple-darwin`.

**Permissions:** `contents: read`

## Inputs

| Name                  | Type    | Default               | Description                                               |
| --------------------- | ------- | --------------------- | --------------------------------------------------------- |
| `rust-version`        | string  | `""`                  | Rust toolchain version to install (overrides file)        |
| `rust-toolchain-file` | string  | `rust-toolchain.toml` | Path to a `rust-toolchain.toml` in the consumer repo      |
| `runs-on`             | string  | `ubuntu-latest`       | Runner label (Windows is not supported)                   |
| `run-test`            | boolean | `true`                | Run cargo test                                            |
| `use-nextest`         | boolean | `false`               | Use cargo-nextest instead of cargo test                   |
| `nextest-version`     | string  | `"0.9.145"`           | cargo-nextest version to install                          |
| `test-args`           | string  | `""`                  | Additional arguments for cargo test or nextest            |
| `run-lint`            | boolean | `true`                | Run cargo clippy                                          |
| `clippy-args`         | string  | `"-D warnings"`       | Arguments passed to clippy after `--`                     |
| `run-format-check`    | boolean | `true`                | Run cargo fmt --check                                     |
| `run-deny`            | boolean | `false`               | Run cargo deny check (requires deny.toml)                 |
| `deny-version`        | string  | `"0.20.2"`            | cargo-deny version to install                             |
| `run-audit`           | boolean | `false`               | Run cargo audit                                           |
| `audit-version`       | string  | `"0.22.2"`            | cargo-audit version to install                            |
| `audit-checksums`     | string  | the v0.22.2 archives  | `<sha256>  <version>  <target>` lines for cargo-audit     |
| `run-typos`           | boolean | `false`               | Run typos spell checking                                  |
| `cargo-features`      | string  | `""`                  | Cargo features passed via --features                      |
| `extra-components`    | string  | `""`                  | Extra rustup components to install                        |
| `coverage`            | boolean | `false`               | Generate coverage and upload to Codecov                   |
| `codecov-cli-version` | string  | `"11.3.1"`            | Codecov CLI version to install                            |
| `codecov-files`       | string  | `lcov.info`           | Coverage file path (used for llvm-cov and Codecov upload) |
| `llvm-cov-version`    | string  | `"0.9.1"`             | cargo-llvm-cov version to install (used when `coverage`)  |
| `llvm-cov-checksums`  | string  | the v0.9.1 archives   | `<sha256>  <version>  <target>` lines for cargo-llvm-cov  |
| `timeout-minutes`     | number  | `15`                  | Job timeout in minutes                                    |

`test-args`, `clippy-args` and `extra-components` are split on whitespace into
separate arguments. Quoting, escaping, glob expansion and variable expansion
are not supported, and a value containing a newline fails the job rather than
losing every line after the first. `cargo-features` and `codecov-files` are
single values and are not split.

## Secrets

| Name            | Required | Description          |
| --------------- | -------- | -------------------- |
| `CODECOV_TOKEN` | No       | Codecov upload token |

## Usage

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/run-rust-ci.yml@v4.0.0
    with:
      run-deny: true
      run-audit: true
      run-typos: true
```

With cargo-nextest and coverage:

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/run-rust-ci.yml@v4.0.0
    with:
      use-nextest: true
      coverage: true
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```
