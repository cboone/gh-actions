# run-reuse

Install [reuse](https://reuse.software/) and run it (default: `reuse lint`)
for SPDX/REUSE compliance. Thin alternative to
[`fsfe/reuse-action`](https://github.com/fsfe/reuse-action). Installs reuse
from this repo's hash-pinned `requirements/reuse.txt` (every transitive
dependency is sha256-pinned via `uv pip compile --generate-hashes`).

uv itself is installed through
[install-pinned-tool](../install-pinned-tool/README.md) and verified against
the per-asset `.sha256` upstream publishes, on Linux and macOS, amd64 and
arm64.

## Inputs

| Name         | Type   | Default   | Description                                      |
| ------------ | ------ | --------- | ------------------------------------------------ |
| `uv-version` | string | `0.12.17` | uv version to install for the reuse install step |
| `args`       | string | `lint`    | Arguments to pass to `reuse`, one per line       |

## Usage

```yaml
- uses: cboone/gh-actions/actions/run-reuse@v4.1.0
```
