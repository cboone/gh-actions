# set-up-golangci-lint

Install golangci-lint binary with a pinned version.

## Inputs

| Name      | Type   | Default  | Description                      |
| --------- | ------ | -------- | -------------------------------- |
| `version` | string | `2.13.2` | golangci-lint version to install |

## Usage

```yaml
- uses: cboone/gh-actions/actions/set-up-golangci-lint@v4.1.0
  with:
    version: "2.13.2"
- run: golangci-lint run ./...
```
