# lint-shell

Run ShellCheck and shfmt on shell scripts. Automatically discovers scripts
by file extension and MIME type.

Only the pinned `shfmt-version` is supported; overriding it requires
updating the hardcoded SHA-256 checksums in
`.github/workflows/lint-shell.yml` first.

**Permissions:** `contents: read`

## Inputs

| Name              | Type    | Default    | Description              |
| ----------------- | ------- | ---------- | ------------------------ |
| `run-shellcheck`  | boolean | `true`     | Run ShellCheck           |
| `run-shfmt`       | boolean | `true`     | Run shfmt format check   |
| `shfmt-version`   | string  | `"3.13.1"` | shfmt version to install |
| `timeout-minutes` | number  | `10`       | Job timeout in minutes   |

## Usage

```yaml
jobs:
  shell:
    uses: cboone/gh-actions/.github/workflows/lint-shell.yml@v3.0.0
```
