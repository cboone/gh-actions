# run-zig-ci

Run Zig tests, format checking, build verification, cross-compilation
checks, and scrut CLI tests. Each check runs as a separate job that can be
toggled on or off.

Unlike `run-go-ci.yml`, this workflow runs Zig commands directly (not via
Makefile targets) since Zig projects idiomatically use `build.zig` as their
build system.

Specify at most one of `zig-version` or `zig-version-file`. If both are set,
`zig-version` takes precedence. If neither is set, `mlugg/setup-zig` falls
back to its own auto-detection (reads `minimum_zig_version` from
`build.zig.zon`, or installs `latest` if no `build.zig.zon` is present).

**Permissions:** `contents: read`

## Inputs

| Name                | Type    | Default         | Description                                          |
| ------------------- | ------- | --------------- | ---------------------------------------------------- |
| `zig-version`       | string  | `""`            | Zig version to install (e.g., `"0.15.2"`)            |
| `zig-version-file`  | string  | `""`            | Path to a `.zon` file with `.minimum_zig_version`    |
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

## Usage

With an explicit version:

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/run-zig-ci.yml@v3.0.0
    with:
      zig-version: "0.14.1"
      run-cross-compile: true
```

Reading the version from `build.zig.zon`:

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/run-zig-ci.yml@v3.0.0
    with:
      zig-version-file: build.zig.zon
      run-cross-compile: true
```

With scrut CLI tests:

```yaml
jobs:
  ci:
    uses: cboone/gh-actions/.github/workflows/run-zig-ci.yml@v3.0.0
    with:
      zig-version-file: build.zig.zon
      run-scrut: true
      scrut-build-cmd: "zig build"
      scrut-env: |
        MY_BIN=./zig-out/bin/my-tool
```
