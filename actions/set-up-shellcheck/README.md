# set-up-shellcheck

Install shellcheck binary with a pinned version.

shellcheck releases ship no checksum file and publish no digests in their
release notes, so the SHA-256 of each release archive is committed as the
`checksums` default. To install another version, pass its checksums with it;
overriding `version` alone fails with
`No checksum entry for shellcheck-v<version>.<os>.<arch>.tar.xz`. Built on
[install-pinned-tool](../install-pinned-tool/README.md).

Pair this with [set-up-actionlint](../set-up-actionlint/README.md): actionlint
shells out to shellcheck for every `run:` block, and skips them all silently
if it cannot find one.

## Inputs

| Name        | Type   | Default              | Description                                        |
| ----------- | ------ | -------------------- | -------------------------------------------------- |
| `version`   | string | `0.11.0`             | shellcheck version to install                      |
| `checksums` | string | the v0.11.0 archives | `sha256sum`-format lines, one per platform archive |

## Usage

```yaml
- uses: cboone/gh-actions/actions/set-up-shellcheck@v3.1.1
- run: shellcheck script.sh
```

Another version, with the checksum for the one platform this job runs on:

```yaml
- uses: cboone/gh-actions/actions/set-up-shellcheck@v3.1.1
  with:
    version: 0.10.0
    checksums: |
      6c881ab0698e4e6ea235245f22832860544f17ba386442fe7e9d629f8cbedf87  shellcheck-v0.10.0.linux.x86_64.tar.xz
```

Drop any lines for platforms your jobs never run on. Digests for a recent
release come from its asset metadata:

```bash
gh api repos/koalaman/shellcheck/releases/tags/v0.11.0 \
  --jq '.assets[] | select(.name | endswith(".tar.xz")) | "\(.digest | sub("^sha256:"; ""))  \(.name)"'
```

GitHub records no digest for older release assets and reports `null` for them,
so a release that predates asset digests needs `shasum -a 256` over the
downloaded archive instead.
