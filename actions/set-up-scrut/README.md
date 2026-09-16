# set-up-scrut

Install scrut CLI testing tool with a pinned version.

Linux arm64 builds v0.4.3 from source because the upstream arm64 archive
contains an x86-64 executable. The build pins the source commit and archive
SHA-256, Rust 1.97.1, and the dependency checksums in the committed
`Cargo.lock`. Other supported platforms install checksum-pinned release binaries.
Only version 0.4.3 is supported. See [the packaging investigation](https://github.com/cboone/gh-actions/issues/120).

Source builds run with a fresh Cargo home outside the consumer checkout,
reject ancestor Cargo configuration, and clear compiler, target and profile
overrides. Network proxy and certificate settings remain available.

Upstream's archive build reports a build timestamp in `scrut --version`,
which the installer validates. The pinned source commit and archive checksum,
rather than that timestamp, identify v0.4.3. This limitation is tracked in #120.

## Inputs

| Name      | Type   | Default | Description              |
| --------- | ------ | ------- | ------------------------ |
| `version` | string | `0.4.3` | scrut version to install |

## Usage

```yaml
- uses: cboone/gh-actions/actions/set-up-scrut@v3.2.0
- run: scrut test tests/
```
