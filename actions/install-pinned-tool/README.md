# install-pinned-tool

Install a release binary pinned to an exact version and SHA-256, and add it
to `PATH`. The asset is downloaded to a file and verified before anything
reads it, then installed as-is or, for an archive, extracted one named
member at a time.

The logic lives in `install-pinned-tool.sh` next to this file, configured
through environment variables named after the inputs (`url-template` is
`URL_TEMPLATE`). A reusable workflow cannot reach this action through a `./`
path, which resolves against the caller's checkout, so
[lint-github-actions](../../docs/workflows/lint-github-actions.md),
[lint-shell](../../docs/workflows/lint-shell.md),
[lint-text](../../docs/workflows/lint-text.md) and
[run-scrut-tests](../../docs/workflows/run-scrut-tests.md) fetch the script at
their own commit and run it with those variables instead. The
[set-up-actionlint](../set-up-actionlint/README.md),
[set-up-shellcheck](../set-up-shellcheck/README.md),
[set-up-shfmt](../set-up-shfmt/README.md), [set-up-uv](../set-up-uv/README.md)
and [run-reuse](../run-reuse/README.md) actions run the same script through
a path relative to their own directory. The same `./` restriction applies
between two composite actions, which is why `run-reuse` runs the script
itself rather than reaching for `set-up-uv`.

- **Platforms.** Linux and macOS runners, amd64 and arm64. Any other OS or
  architecture fails the step.
- **Placeholders.** `url-template`, `checksums-url-template` and
  `archive-member` take `{version}`, `{os}` and `{arch}`. `{os}` is `linux` or
  `darwin` and `{arch}` is `amd64` or `arm64`, the names Go release tooling
  uses; `os-names` and `arch-names` rename them for upstreams that spell them
  differently. Any other `{...}` fails the step, so a misspelled placeholder
  cannot reach a URL.
- **Exactly one checksum source.** `checksum` is one digest applied on every
  platform, which suits callers whose jobs all run on one OS and architecture.
  `checksums` holds one `sha256sum`-format line per platform asset; its names
  are literal, so a version bumped without its checksums fails with
  `No checksum entry for <asset>` rather than matching a stale entry.
  `checksums-url-template` reads an upstream checksum file.
- **Committed or upstream checksums.** A committed `checksum` or `checksums`
  pins the bytes someone reviewed. An upstream checksum file is served by the
  same release as the asset, so it proves the asset matches what that release
  serves at install time; a release whose asset and checksum file were both
  replaced still passes. Prefer committed checksums where upstream allows it.
- **Producing checksums.** Run `shasum -a 256` on each downloaded asset, or
  read the digests GitHub records for release assets. Those print as
  `sha256:<hex>`, so this command strips the prefix and emits
  `sha256sum`-format lines ready to paste into `checksums`:

  ```bash
  gh api repos/mvdan/sh/releases/tags/v3.14.1 \
    --jq '.assets[] | "\(.digest | sub("^sha256:"; ""))  \(.name)"'
  ```

- **Archives.** `archive-member` names the binary inside a tar archive; tar
  detects gzip, xz and bzip2 compression itself. Spell it exactly as
  `tar -tf` lists it: GNU tar on Linux runners treats `./typos` and `typos`
  as different members, while bsdtar on macOS accepts either, so a spelling
  that works on one platform can fail on the other. The member must be a
  regular file, not a symlink or a hard link, named by a relative path that
  neither starts with `-` nor contains `..`. Only that member is
  extracted, so documentation and man pages packed beside the binary never
  land on disk. Leave it empty when the asset is the binary itself.
- **Install location.** The binary is installed as `<install-dir>/<tool>`,
  where `install-dir` is `$RUNNER_TEMP/<tool>-bin`, recreated on every run.
  Downloads use `https://` only, and a redirect to plain `http://` fails the
  step.

## Inputs

| Name                     | Type   | Default  | Description                                                     |
| ------------------------ | ------ | -------- | --------------------------------------------------------------- |
| `tool`                   | string | required | Binary name; installed as `<install-dir>/<tool>`                |
| `version`                | string | required | Exact version, substituted for `{version}`                      |
| `url-template`           | string | required | `https://` URL of the release asset                             |
| `checksum`               | string | `""`     | One SHA-256, applied on every platform                          |
| `checksums`              | string | `""`     | `sha256sum`-format lines, one per platform asset                |
| `checksums-url-template` | string | `""`     | `https://` URL of an upstream checksum file                     |
| `archive-member`         | string | `""`     | The binary's path inside a tar archive; empty for a bare binary |
| `os-names`               | string | `""`     | Renames for `{os}`, e.g. `darwin=macos`                         |
| `arch-names`             | string | `""`     | Renames for `{arch}`, e.g. `amd64=x86_64 arm64=aarch64`         |

## Outputs

| Name          | Description                                                         |
| ------------- | ------------------------------------------------------------------- |
| `install-dir` | Directory holding the binary (`$RUNNER_TEMP/<tool>-bin`), on `PATH` |

## Usage

A bare binary with committed per-platform checksums:

```yaml
- uses: cboone/gh-actions/actions/install-pinned-tool@v5.0.0
  with:
    tool: shfmt
    version: 3.14.1
    url-template: https://github.com/mvdan/sh/releases/download/v{version}/shfmt_v{version}_{os}_{arch}
    checksums: |
      76e77641faa025814b77f153b29796b8e6fa2fca03e0c76a691608b86c7ea7bf  shfmt_v3.14.1_linux_amd64
      5f2db09dae91fca848f7adbdd014632e921a383863a2ad7e0450ad3aba0c6489  shfmt_v3.14.1_linux_arm64
      d33eee0da0f92835b3562e9767a05cee7e4eaeef47daa03bfd09da17b4b590a6  shfmt_v3.14.1_darwin_amd64
      b7c872db63553ccffc7253aba3ed7d4885a27d83f1ba567b1138c6315a5847e5  shfmt_v3.14.1_darwin_arm64
- run: shfmt -d .
```

An archive verified against the upstream checksum file:

```yaml
- uses: cboone/gh-actions/actions/install-pinned-tool@v5.0.0
  with:
    tool: actionlint
    version: 1.7.12
    url-template: https://github.com/rhysd/actionlint/releases/download/v{version}/actionlint_{version}_{os}_{arch}.tar.gz
    checksums-url-template: https://github.com/rhysd/actionlint/releases/download/v{version}/actionlint_{version}_checksums.txt
    archive-member: actionlint
```

Rust target-triple asset names and a `./`-prefixed member, with one committed
checksum for a job that only runs on `ubuntu-latest`:

```yaml
- uses: cboone/gh-actions/actions/install-pinned-tool@v5.0.0
  with:
    tool: typos
    version: 1.50.1
    url-template: https://github.com/crate-ci/typos/releases/download/v{version}/typos-v{version}-{arch}-{os}.tar.gz
    os-names: linux=unknown-linux-musl darwin=apple-darwin
    arch-names: amd64=x86_64 arm64=aarch64
    archive-member: ./typos
    checksum: edf0545109aee6a22751d04ddecb97c45be47d3aa0409564fb895eeeace91b1e
```

A nested member and a per-asset `.sha256` file:

```yaml
- uses: cboone/gh-actions/actions/install-pinned-tool@v5.0.0
  with:
    tool: uv
    version: 0.12.17
    url-template: https://github.com/astral-sh/uv/releases/download/{version}/uv-{arch}-{os}.tar.gz
    checksums-url-template: https://github.com/astral-sh/uv/releases/download/{version}/uv-{arch}-{os}.tar.gz.sha256
    os-names: linux=unknown-linux-gnu darwin=apple-darwin
    arch-names: amd64=x86_64 arm64=aarch64
    archive-member: uv-{arch}-{os}/uv
```
