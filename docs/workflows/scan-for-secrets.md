# scan-for-secrets

Run gitleaks, trufflehog, or both to scan for leaked secrets. Supports
full-history and working-tree scan scopes.

**Permissions:** `contents: read`

## Inputs

| Name                 | Type   | Default        | Description                                      |
| -------------------- | ------ | -------------- | ------------------------------------------------ |
| `tool`               | string | `gitleaks`     | Which tool to run: gitleaks, trufflehog, or both |
| `scan-scope`         | string | `full-history` | Scan scope: full-history or working-tree         |
| `gitleaks-version`   | string | `"8.30.1"`     | gitleaks version to install                      |
| `trufflehog-version` | string | `"3.95.2"`     | trufflehog version to install                    |
| `fetch-depth`        | number | `0`            | Git fetch depth (0 for full history)             |
| `allowlist-config`   | string | `""`           | Path to a gitleaks allowlist config file         |
| `timeout-minutes`    | number | `15`           | Job timeout in minutes                           |

## Usage

```yaml
jobs:
  scan:
    uses: cboone/gh-actions/.github/workflows/scan-for-secrets.yml@v3.0.0
    with:
      tool: both
```
