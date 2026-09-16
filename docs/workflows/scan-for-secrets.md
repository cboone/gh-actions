# scan-for-secrets

Run gitleaks, trufflehog, or both to scan for leaked secrets. Supports
full-history and working-tree scan scopes.

TruffleHog findings fail the job (exit code 183). Its scan reports verified
credentials and unknown results caused by verification errors. Unverified
results are excluded to limit noise from invalid credentials, so revoked
credentials and detections without verification are outside the TruffleHog gate.

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
    uses: cboone/gh-actions/.github/workflows/scan-for-secrets.yml@v3.2.0
    with:
      tool: both
```
