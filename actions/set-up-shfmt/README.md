# set-up-shfmt

Install shfmt binary with a pinned version.

Only the pinned version is supported; overriding `version` requires updating
the hardcoded SHA-256 checksums in `actions/set-up-shfmt/action.yml` first.

## Inputs

| Name      | Type   | Default  | Description              |
| --------- | ------ | -------- | ------------------------ |
| `version` | string | `3.13.1` | shfmt version to install |

## Usage

```yaml
- uses: cboone/gh-actions/actions/set-up-shfmt@v3.0.0
- run: shfmt -d .
```
