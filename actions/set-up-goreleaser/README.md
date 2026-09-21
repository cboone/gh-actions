# set-up-goreleaser

Install GoReleaser binary with a pinned version.

## Inputs

| Name      | Type   | Default  | Description                   |
| --------- | ------ | -------- | ----------------------------- |
| `version` | string | `2.18.2` | GoReleaser version to install |

## Usage

```yaml
- uses: cboone/gh-actions/actions/set-up-goreleaser@v4.0.0
  with:
    version: "2.18.2"
- run: goreleaser release --clean
```
