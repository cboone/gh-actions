# set-up-golangci-lint

Install golangci-lint binary with a pinned version.

## Inputs

| Name      | Type   | Default  | Description                      |
| --------- | ------ | -------- | -------------------------------- |
| `version` | string | `2.11.4` | golangci-lint version to install |

## Usage

```yaml
- uses: cboone/gh-actions/actions/set-up-golangci-lint@v3.0.0
  with:
    version: "2.11.4"
- run: golangci-lint run ./...
```
