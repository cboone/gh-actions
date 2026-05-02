# lint-github-actions

Run actionlint to validate GitHub Actions workflow files.

**Permissions:** `contents: read`

## Inputs

| Name                 | Type   | Default    | Description                   |
| -------------------- | ------ | ---------- | ----------------------------- |
| `actionlint-version` | string | `"1.7.12"` | actionlint version to install |
| `timeout-minutes`    | number | `10`       | Job timeout in minutes        |

## Usage

```yaml
jobs:
  github:
    uses: cboone/gh-actions/.github/workflows/lint-github-actions.yml@v3.0.0
```
