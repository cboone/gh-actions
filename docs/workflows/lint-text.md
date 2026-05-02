# lint-text

Run Markdown linting, Prettier formatting checks, cspell spelling checks,
and yamllint YAML validation. Each tool can be toggled independently.

**Permissions:** `contents: read`

## Inputs

| Name               | Type    | Default     | Description                |
| ------------------ | ------- | ----------- | -------------------------- |
| `node-version`     | string  | `"24.15.0"` | Node.js version to install |
| `run-markdownlint` | boolean | `true`      | Run markdownlint-cli2      |
| `run-prettier`     | boolean | `true`      | Run Prettier format check  |
| `run-cspell`       | boolean | `false`     | Run cspell spell checker   |
| `run-yamllint`     | boolean | `false`     | Run yamllint               |
| `timeout-minutes`  | number  | `10`        | Job timeout in minutes     |

## Usage

```yaml
jobs:
  text:
    uses: cboone/gh-actions/.github/workflows/lint-text.yml@v3.0.0
    with:
      run-cspell: true
```
