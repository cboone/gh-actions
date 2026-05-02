# set-up-goreleaser

Install GoReleaser binary with a pinned version.

## Inputs

| Name      | Type   | Default  | Description                   |
| --------- | ------ | -------- | ----------------------------- |
| `version` | string | `2.15.4` | GoReleaser version to install |

## Usage

```yaml
- uses: cboone/gh-actions/actions/set-up-goreleaser@v3.0.0
  with:
    version: "2.15.4"
- run: goreleaser release --clean
```
