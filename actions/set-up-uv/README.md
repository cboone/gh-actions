# set-up-uv

Install the [uv](https://github.com/astral-sh/uv) binary with a pinned version and add it to `PATH`.

The release archive is verified against the per-asset `.sha256` file uv
publishes beside each platform's tarball. Built on
[install-pinned-tool](../install-pinned-tool/README.md), so it covers Linux and
macOS on amd64 and arm64.

Only `uv` is installed, not `uvx`. `uv tool run` is the equivalent, and a
second install would re-download the whole tarball for one more member.

## Inputs

| Name      | Type   | Default   | Description           |
| --------- | ------ | --------- | --------------------- |
| `version` | string | `0.12.17` | uv version to install |

## Usage

Composite action, within a job's `steps:`:

```yaml
- uses: cboone/gh-actions/actions/set-up-uv@v5.0.0
- run: uv run --script script.py
```

Reusable workflows in this repository cannot reach this action by a `./` path,
because such a path resolves against the caller's checkout. They fetch
`install-pinned-tool.sh` at their own commit instead; see
[run-scrut-tests](../../docs/workflows/run-scrut-tests.md) for that pattern.
