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
| `version`   | string | `3.14.1`             | shfmt version to install                          |
| `checksums` | string | the v3.14.1 binaries | `sha256sum`-format lines, one per platform binary |

## Usage

```yaml
- uses: cboone/gh-actions/actions/set-up-shfmt@v3.2.0
- run: shfmt -d .
```

Another version, with its checksums:

```yaml
- uses: cboone/gh-actions/actions/set-up-shfmt@v3.2.0
  with:
    version: 3.13.1
    checksums: |
      fb096c5d1ac6beabbdbaa2874d025badb03ee07929f0c9ff67563ce8c75398b1  shfmt_v3.13.1_linux_amd64
      32d92acaa5cd8abb29fc49dac123dc412442d5713967819d8af2c29f1b3857c7  shfmt_v3.13.1_linux_arm64
      6feedafc72915794163114f512348e2437d080d0047ef8b8fa2ec63b575f12af  shfmt_v3.13.1_darwin_amd64
      9680526be4a66ea1ffe988ed08af58e1400fe1e4f4aef5bd88b20bb9b3da33f8  shfmt_v3.13.1_darwin_arm64
```

Those digests come from the release's asset metadata; drop any lines for
platforms your jobs never run on:

```bash
gh api repos/mvdan/sh/releases/tags/v3.13.1 \
  --jq '.assets[] | "\(.digest | sub("^sha256:"; ""))  \(.name)"'
```
