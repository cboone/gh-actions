# set-up-actionlint

Install actionlint binary with a pinned version.

The release archive is verified against the `checksums.txt` actionlint
publishes with each release. Built on
[install-pinned-tool](../install-pinned-tool/README.md).

## Inputs

| Name      | Type   | Default  | Description                   |
| --------- | ------ | -------- | ----------------------------- |
| `version` | string | `1.7.12` | actionlint version to install |

## Usage

```yaml
- uses: cboone/gh-actions/actions/set-up-actionlint@v3.1.1
- run: actionlint
```
