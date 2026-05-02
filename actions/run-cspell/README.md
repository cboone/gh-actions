# run-cspell

Install cspell and run it with inline pull-request annotations. Thin
alternative to
[`streetsidesoftware/cspell-action`](https://github.com/streetsidesoftware/cspell-action).
Installs cspell from this repo's sha512-pinned `package-lock.json` (same
trust path as the [lint-text](../../docs/workflows/lint-text.md) reusable
workflow) and registers a problem matcher so cspell's default
`path:line:col - Unknown word` output surfaces as PR annotations.

Node.js must be available on the runner; pair with `actions/setup-node` if it
is not already installed. For most projects, the
[lint-text](../../docs/workflows/lint-text.md) reusable workflow with
`run-cspell: true` is a better fit; reach for this action when you need
cspell standalone in a larger custom workflow.

## Inputs

| Name     | Type   | Default | Description                                               |
| -------- | ------ | ------- | --------------------------------------------------------- |
| `files`  | string | `.`     | Newline-delimited globs passed to cspell                  |
| `config` | string | `""`    | Path to a cspell config file (auto-discovered when empty) |
| `args`   | string | `""`    | Extra arguments to pass to cspell, one per line           |

## Usage

```yaml
- uses: actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e # v6.4.0
  with:
    node-version: "24.15.0"
- uses: cboone/gh-actions/actions/run-cspell@v3.0.0
```
