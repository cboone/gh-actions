# set-up-scrut

Install scrut CLI testing tool with a pinned version.

## Inputs

| Name      | Type   | Default | Description              |
| --------- | ------ | ------- | ------------------------ |
| `version` | string | `0.4.3` | scrut version to install |

## Usage

```yaml
- uses: cboone/gh-actions/actions/set-up-scrut@v3.0.0
- run: scrut test tests/
```
