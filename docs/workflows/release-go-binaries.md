# release-go-binaries

Run GoReleaser to build and publish a Go release.

**Permissions:** `contents: write`

## Inputs

| Name                 | Type   | Default           | Description                          |
| -------------------- | ------ | ----------------- | ------------------------------------ |
| `go-version-file`    | string | `go.mod`          | File to read the Go version from     |
| `runs-on`            | string | `ubuntu-latest`   | Runner label (Windows not supported) |
| `goreleaser-version` | string | `"2.15.4"`        | GoReleaser version to install        |
| `goreleaser-args`    | string | `release --clean` | Arguments to pass to goreleaser      |
| `timeout-minutes`    | number | `30`              | Job timeout in minutes               |

## Secrets

| Name                 | Required | Description                    |
| -------------------- | -------- | ------------------------------ |
| `HOMEBREW_TAP_TOKEN` | No       | Token for Homebrew tap updates |

## Usage

```yaml
jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/release-go-binaries.yml@v3.0.0
    with:
      goreleaser-version: "2.15.4"
    secrets:
      HOMEBREW_TAP_TOKEN: ${{ secrets.HOMEBREW_TAP_TOKEN }}
```
