# run-scrut-tests

Run scrut CLI snapshot tests. Designed for non-Go projects (e.g., shell
plugins) that need scrut testing without Go setup or build steps. Installs
scrut with SHA-256 checksum verification and runs tests against the
specified directory.

**Permissions:** `contents: read`

## Inputs

| Name              | Type   | Default         | Description                                          |
| ----------------- | ------ | --------------- | ---------------------------------------------------- |
| `scrut-version`   | string | `"0.4.3"`       | scrut version to install (checksums pinned to this)  |
| `scrut-shell`     | string | `""`            | Shell for `--shell` flag (e.g., "zsh", "bash")       |
| `scrut-test-dir`  | string | `"tests/"`      | Directory containing scrut test files                |
| `scrut-env`       | string | `""`            | Newline-delimited KEY=VALUE env vars for scrut tests |
| `scrut-setup-cmd` | string | `""`            | Shell command to run before scrut tests              |
| `runs-on`         | string | `ubuntu-latest` | Runner label (Windows is not supported)              |
| `timeout-minutes` | number | `10`            | Job timeout in minutes                               |

## Usage

```yaml
jobs:
  scrut:
    uses: cboone/gh-actions/.github/workflows/run-scrut-tests.yml@v3.0.0
```

With a custom shell and environment variables:

```yaml
jobs:
  scrut:
    uses: cboone/gh-actions/.github/workflows/run-scrut-tests.yml@v3.0.0
    with:
      scrut-shell: zsh
      scrut-env: |
        MY_PLUGIN_DIR=./src
      scrut-setup-cmd: "make build"
```
