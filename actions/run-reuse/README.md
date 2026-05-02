# run-reuse

Install [reuse](https://reuse.software/) and run it (default: `reuse lint`)
for SPDX/REUSE compliance. Thin alternative to
[`fsfe/reuse-action`](https://github.com/fsfe/reuse-action). Installs reuse
from this repo's hash-pinned `requirements/reuse.txt` (every transitive
dependency is sha256-pinned via `uv pip compile --generate-hashes`).

## Inputs

| Name         | Type   | Default  | Description                                      |
| ------------ | ------ | -------- | ------------------------------------------------ |
| `uv-version` | string | `0.11.8` | uv version to install for the reuse install step |
| `args`       | string | `lint`   | Arguments to pass to `reuse`, one per line       |

## Usage

```yaml
- uses: cboone/gh-actions/actions/run-reuse@v3.0.0
```
