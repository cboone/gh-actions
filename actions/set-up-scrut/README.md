# set-up-scrut

Install scrut CLI testing tool with a pinned version.

Only v0.4.3 is supported. Linux x86-64 and macOS arm64 use checksum-verified
release binaries. Linux arm64 and macOS x86-64 build from pinned source with
Rust 1.97.1 and a committed Cargo.lock because upstream's assets contain the
wrong architecture. Source builds report the package version consistently.
See the [investigation and removal criteria](../../docs/scrut-installation-investigation.md)
and [source-build trust model](../../docs/development.md#pinning-policy-and-trust-model).

## Inputs

| Name      | Type   | Default | Description              |
| --------- | ------ | ------- | ------------------------ |
| `version` | string | `0.4.3` | scrut version to install |

## Usage

```yaml
- uses: cboone/gh-actions/actions/set-up-scrut@v4.1.0
- run: scrut test tests/
```
