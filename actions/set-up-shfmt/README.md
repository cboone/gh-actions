# set-up-shfmt

Install shfmt binary with a pinned version.

shfmt releases from v3.13.0 on ship no checksum file (mvdan/sh#1283,
mvdan/sh#1309), so the SHA-256 of each release binary is committed as the
`checksums` default. To install another version, pass its checksums with it;
overriding `version` alone fails with
`No checksum entry for shfmt_v<version>_<os>_<arch>`. Built on
[install-pinned-tool](../install-pinned-tool/README.md).

## Inputs

| Name        | Type   | Default              | Description                                       |
| ----------- | ------ | -------------------- | ------------------------------------------------- |
| `version`   | string | `3.13.1`             | shfmt version to install                          |
| `checksums` | string | the v3.13.1 binaries | `sha256sum`-format lines, one per platform binary |

## Usage

```yaml
- uses: cboone/gh-actions/actions/set-up-shfmt@v3.1.1
- run: shfmt -d .
```

Another version, with its checksums:

```yaml
- uses: cboone/gh-actions/actions/set-up-shfmt@v3.1.1
  with:
    version: 3.14.1
    checksums: |
      76e77641faa025814b77f153b29796b8e6fa2fca03e0c76a691608b86c7ea7bf  shfmt_v3.14.1_linux_amd64
      5f2db09dae91fca848f7adbdd014632e921a383863a2ad7e0450ad3aba0c6489  shfmt_v3.14.1_linux_arm64
      d33eee0da0f92835b3562e9767a05cee7e4eaeef47daa03bfd09da17b4b590a6  shfmt_v3.14.1_darwin_amd64
      b7c872db63553ccffc7253aba3ed7d4885a27d83f1ba567b1138c6315a5847e5  shfmt_v3.14.1_darwin_arm64
```

Those digests come from the release's asset metadata; drop any lines for
platforms your jobs never run on:

```bash
gh api repos/mvdan/sh/releases/tags/v3.14.1 \
  --jq '.assets[] | "\(.digest | sub("^sha256:"; ""))  \(.name)"'
```
