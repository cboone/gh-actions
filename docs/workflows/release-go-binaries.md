# release-go-binaries

Run GoReleaser to build and publish a Go release.

**Permissions:** `contents: write`

## Inputs

| Name                 | Type   | Default           | Description                          |
| -------------------- | ------ | ----------------- | ------------------------------------ |
| `go-version-file`    | string | `go.mod`          | File to read the Go version from     |
| `runs-on`            | string | `ubuntu-latest`   | Runner label (Windows not supported) |
| `goreleaser-version` | string | `"2.18.2"`        | GoReleaser version to install        |
| `goreleaser-args`    | string | `release --clean` | Arguments to pass to goreleaser      |
| `timeout-minutes`    | number | `30`              | Job timeout in minutes               |

`goreleaser-args` is split on whitespace into separate arguments. Quoting,
escaping, glob expansion and variable expansion are not supported, and a value
containing a newline fails the job rather than losing every line after the
first.

## Secrets

| Name                 | Required | Description                    |
| -------------------- | -------- | ------------------------------ |
| `HOMEBREW_TAP_TOKEN` | No       | Token for Homebrew tap updates |

## Usage

```yaml
jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/release-go-binaries.yml@v4.0.0
    with:
      goreleaser-version: "2.18.2"
    secrets:
      HOMEBREW_TAP_TOKEN: ${{ secrets.HOMEBREW_TAP_TOKEN }}
```
