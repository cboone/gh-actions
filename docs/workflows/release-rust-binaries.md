# release-rust-binaries

Build Rust binaries for multiple targets and publish them as a GitHub
Release. Supports matrix builds across different runners and optional
Homebrew formula updates.

The Rust toolchain is resolved from `rust-version` if set; otherwise the
workflow reads the channel from `rust-toolchain-file` (default
`rust-toolchain.toml`); otherwise it falls back to a legacy `rust-toolchain`
file at the repo root. At least one of these must resolve to a value or the
workflow fails fast.

**Permissions:** `contents: write`

## Inputs

| Name                    | Type    | Default               | Description                                                  |
| ----------------------- | ------- | --------------------- | ------------------------------------------------------------ |
| `targets`               | string  |                       | JSON array of `{"target","runner"}` objects (required)       |
| `binary-name`           | string  | `""`                  | Binary name (extracted from Cargo.toml if empty)             |
| `rust-version`          | string  | `""`                  | Rust toolchain version to install (overrides file)           |
| `rust-toolchain-file`   | string  | `rust-toolchain.toml` | Path to a `rust-toolchain.toml` in the consumer repo         |
| `build-args`            | string  | `""`                  | Additional arguments for cargo build                         |
| `archive-prefix`        | string  | `""`                  | Override archive prefix (default: {binary}-{version})        |
| `update-homebrew`       | boolean | `false`               | Update a Homebrew formula after releasing                    |
| `homebrew-tap`          | string  | `""`                  | Homebrew tap repository (e.g. user/homebrew-tap)             |
| `homebrew-formula-path` | string  | `""`                  | Path to the formula in the tap repo (e.g. Formula/mytool.rb) |
| `homebrew-license`      | string  | `"MIT"`               | SPDX license identifier for the Homebrew formula             |
| `timeout-minutes`       | number  | `30`                  | Job timeout in minutes                                       |

## Secrets

| Name                 | Required | Description                    |
| -------------------- | -------- | ------------------------------ |
| `HOMEBREW_TAP_TOKEN` | No       | Token for Homebrew tap updates |

## Usage

```yaml
jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/release-rust-binaries.yml@v3.0.0
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
    uses: cboone/gh-actions/.github/workflows/release-rust-binaries.yml@v3.0.0
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
