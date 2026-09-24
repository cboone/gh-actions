# run-zig-ci

Run Zig tests, format checking, build verification, cross-compilation
checks, and scrut CLI tests. Each check runs as a separate job that can be
toggled on or off.

With `run-scrut: true`, Linux arm64 and macOS x86-64 build Scrut v0.4.3 from
pinned source using Rust 1.97.1 and the repository's reviewed Cargo.lock.
The helper, lockfile and version script are fetched at the workflow's own
repository and commit; those source builds require GitHub.com job context.
Linux x86-64 and macOS arm64 use checksum-verified release binaries. See the
[investigation and removal criteria](../scrut-installation-investigation.md).

Unlike `run-go-ci.yml`, this workflow runs Zig commands directly (not via
Makefile targets) since Zig projects idiomatically use `build.zig` as their
build system.

Formatting checks `build.zig`, `build.zig.zon`, and `src` by default.
`zig fmt` formats ZON manifests as well as Zig sources. An unformatted or
missing manifest now fails the default check. Override `fmt-paths` for
other layouts or projects without a manifest. Paths are space-separated;
quoting, escaping, glob expansion, and paths containing spaces are not
supported. Supply at least one path on a single line.

Specify at most one of `zig-version` or `zig-version-file`. If both are set,
`zig-version` takes precedence. If neither is set, `mlugg/setup-zig` falls
back to its own auto-detection (reads `minimum_zig_version` from
`build.zig.zon`, or installs `latest` if no `build.zig.zon` is present).

**Permissions:** `contents: read`

Source builds run with a fresh Cargo home outside the consumer checkout,
reject ancestor Cargo configuration, and clear compiler, target and profile
overrides. Network proxy and certificate settings remain available.

The replacement build script reports `scrut 0.4.3` from package metadata;
the installer validates that exact version before exposing the executable.

`scrut-setup-cmd` and `scrut-build-cmd` run in the checked-out workspace, which
the workflow checks out with `persist-credentials: false`. Neither inherits a
Git credential from `.git/config`, so a command that has to authenticate to
GitHub needs a token of its own, through `gh` and `GH_TOKEN` or an explicit
remote.

## Inputs

| Name                | Type    | Default                       | Description                                          |
| ------------------- | ------- | ----------------------------- | ---------------------------------------------------- |
| `zig-version`       | string  | `""`                          | Zig version to install (e.g., `"0.15.2"`)            |
| `zig-version-file`  | string  | `""`                          | Path to a `.zon` file with `.minimum_zig_version`    |
| `runs-on`           | string  | `ubuntu-latest`               | Runner label (Windows is not supported)              |
| `run-test`          | boolean | `true`                        | Run `zig build test`                                 |
| `run-fmt`           | boolean | `true`                        | Run `zig fmt --check` on `fmt-paths`                 |
| `fmt-paths`         | string  | `build.zig build.zig.zon src` | Space-separated paths to format-check                |
| `run-build`         | boolean | `true`                        | Run `zig build`                                      |
| `run-cross-compile` | boolean | `false`                       | Build all cross-compilation targets                  |
| `cross-targets`     | string  | (see below)                   | Space-separated Zig target triples                   |
| `run-scrut`         | boolean | `false`                       | Run scrut CLI tests                                  |
| `scrut-build-cmd`   | string  | `zig build`                   | Command to build the binary for scrut tests          |
| `scrut-env`         | string  | `""`                          | Newline-delimited KEY=VALUE env vars for scrut tests |
| `scrut-test-dir`    | string  | `tests/`                      | Directory containing scrut test files                |
| `scrut-setup-cmd`   | string  | `""`                          | Optional shell command to run before scrut tests     |
| `timeout-minutes`   | number  | `20`                          | Job timeout in minutes                               |

Default `cross-targets`:

```text
x86_64-linux-gnu aarch64-linux-gnu x86_64-macos aarch64-macos x86_64-windows-gnu
```

`fmt-paths` and `cross-targets` are split on whitespace into separate values.
Quoting, escaping, glob expansion and variable expansion are not supported. A
value containing a newline fails the job rather than losing every line after
the first, and an empty value fails rather than checking or building nothing.

## Usage

With an explicit version:

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/run-zig-ci.yml@v4.1.0
    with:
      zig-version: "0.14.1"
      run-cross-compile: true
```

Reading the version from `build.zig.zon`:

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/run-zig-ci.yml@v4.1.0
    with:
      zig-version-file: build.zig.zon
      run-cross-compile: true
```

With additional source directories and a root-level Zig file:

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/run-zig-ci.yml@v4.1.0
    with:
      zig-version-file: build.zig.zon
      fmt-paths: "build.zig build.zig.zon src tools tests build_runner.zig"
```

With scrut CLI tests:

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/run-zig-ci.yml@v4.1.0
    with:
      zig-version-file: build.zig.zon
      run-scrut: true
      scrut-build-cmd: "zig build"
      scrut-env: |
        MY_BIN=./zig-out/bin/my-tool
```
