# run-scrut-tests

Run scrut CLI snapshot tests. Designed for non-Go projects (e.g., shell
plugins) that need scrut testing without Go setup or build steps. Installs
scrut with SHA-256 checksum verification and runs tests against the
specified directory.

Linux arm64 builds v0.4.3 from source because the upstream arm64 archive
contains an x86-64 executable. The build pins the source commit and archive
SHA-256, Rust 1.97.1, and a committed `Cargo.lock` with dependency checksums.
The build script and lockfile are fetched from the workflow's own repository
and commit, rather than the consumer checkout. Other supported platforms
install checksum-pinned release binaries. Only version 0.4.3 is supported.
See [the packaging investigation](https://github.com/cboone/gh-actions/issues/120).

Linux arm64 source builds require the workflow repository and commit contexts,
which are unavailable on GitHub Enterprise Server (GHES). The workflow rejects
that case with a targeted error. GHES callers can install Scrut using the
`set-up-scrut` composite action instead.

**Permissions:** `contents: read`

## Inputs

| Name              | Type    | Default         | Description                                                             |
| ----------------- | ------- | --------------- | ----------------------------------------------------------------------- |
| `scrut-version`   | string  | `"0.4.3"`       | scrut version to install (checksums pinned to this)                     |
| `scrut-shell`     | string  | `""`            | Shell for `--shell` flag (e.g., "zsh", "bash")                          |
| `scrut-test-dir`  | string  | `"tests/"`      | Directory containing scrut test files                                   |
| `scrut-env`       | string  | `""`            | Newline-delimited KEY=VALUE env vars for scrut tests                    |
| `scrut-setup-cmd` | string  | `""`            | Shell command to run before scrut tests; runs after the uv install step |
| `setup-uv`        | boolean | `false`         | Install uv and add it to `PATH` before `scrut-setup-cmd` runs           |
| `uv-version`      | string  | `"0.11.8"`      | uv version to install when `setup-uv` is true                           |
| `runs-on`         | string  | `ubuntu-latest` | Runner label (Windows is not supported)                                 |
| `timeout-minutes` | number  | `10`            | Job timeout in minutes                                                  |

### Installing uv

A CLI written in an interpreted language needs its runtime on `PATH` before
scrut can execute anything, and `scrut-setup-cmd` is a `run:` string, so it
cannot take a `uses:` step. `setup-uv` covers the uv case directly: it
downloads the pinned uv release, verifies it against the SHA-256 that upstream
publishes alongside the asset, and adds it to `PATH`. Linux and macOS runners,
amd64 and arm64.

uv lands before `scrut-setup-cmd`, so that command can call `uv sync`,
`uv run`, or `uv tool run`. Only `uv` is installed, not `uvx`; `uv tool run` is
the equivalent.

`setup-uv` needs `job.workflow_repository` and `job.workflow_sha` to fetch its
pinned installer, and neither is populated on GitHub Enterprise Server. Leave
`setup-uv` at `false` there and install uv from `scrut-setup-cmd` instead.

## Usage

```yaml
jobs:
  scrut:
    uses: cboone/gh-actions/.github/workflows/run-scrut-tests.yml@v3.2.0
```

With a custom shell and environment variables:

```yaml
jobs:
  scrut:
    uses: cboone/gh-actions/.github/workflows/run-scrut-tests.yml@v3.2.0
    with:
      scrut-shell: zsh
      scrut-env: |
        MY_PLUGIN_DIR=./src
      scrut-setup-cmd: "make build"
```

For a CLI shipped as PEP 723 scripts with
`#!/usr/bin/env -S uv run --script` shebangs:

```yaml
jobs:
  scrut:
    uses: cboone/gh-actions/.github/workflows/run-scrut-tests.yml@v3.2.0
    with:
      setup-uv: true
      scrut-test-dir: "tests/scrut/"
      scrut-env: |
        MY_TOOL_BIN=./tools/my-tool/my-tool.py
```
