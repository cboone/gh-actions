# analyze-with-codeql

Run GitHub CodeQL security analysis. SHA-pins all `github/codeql-action`
sub-actions internally and conditionally sets up Go when the language list
includes it.

**Permissions:** `contents: read`, `security-events: write`

## Inputs

| Name              | Type   | Default                | Description                                                |
| ----------------- | ------ | ---------------------- | ---------------------------------------------------------- |
| `languages`       | string | `go`                   | Comma-separated CodeQL languages to analyze                |
| `queries`         | string | `security-and-quality` | CodeQL query suite to run                                  |
| `go-version`      | string | `""`                   | Go version to install. When set, overrides go-version-file |
| `go-version-file` | string | `go.mod`               | File to read the Go version from                           |
| `category-prefix` | string | `/language:`           | Prefix for the CodeQL analysis category                    |
| `runs-on`         | string | `macos-latest`         | Runner label                                               |
| `timeout-minutes` | number | `30`                   | Job timeout in minutes                                     |

## Usage

```yaml
jobs:
  codeql:
    uses: cboone/gh-actions/.github/workflows/analyze-with-codeql.yml@v3.0.0
    with:
      languages: go
      go-version: "1.25"
    permissions:
      contents: read
      security-events: write
```
