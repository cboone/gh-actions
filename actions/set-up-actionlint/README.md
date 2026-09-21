# set-up-actionlint

Install actionlint binary with a pinned version.

The release archive is verified against the `checksums.txt` actionlint
publishes with each release. Built on
[install-pinned-tool](../install-pinned-tool/README.md).

actionlint shells out to `shellcheck` for every `run:` block, which is the
only thing that lints the embedded shell in a workflow file. With no
`shellcheck` on `PATH` it skips all of them and still exits 0, so a job that
installs only actionlint passes vacuously on any runner image without one.
Use [set-up-shellcheck](../set-up-shellcheck/README.md) alongside this action;
each reports the version it installed, so the log shows actionlint had
something to shell out to.

## Inputs

| Name      | Type   | Default  | Description                   |
| --------- | ------ | -------- | ----------------------------- |
| `version` | string | `1.7.12` | actionlint version to install |

## Usage

```yaml
- uses: cboone/gh-actions/actions/set-up-shellcheck@v4.1.0
- uses: cboone/gh-actions/actions/set-up-actionlint@v4.1.0
- run: actionlint
```
