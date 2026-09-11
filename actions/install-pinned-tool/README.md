# install-pinned-tool

Install a release binary pinned to an exact version and SHA-256, and add it
to `PATH`. The asset is downloaded to a file and verified before anything
reads it, then installed as-is or, for an archive, extracted one named
member at a time.

The logic lives in `install-pinned-tool.sh` next to this file, configured
through environment variables named after the inputs (`url-template` is
`URL_TEMPLATE`). A reusable workflow cannot reach this action through a `./`
path, which resolves against the caller's checkout, so
[lint-github-actions](../../docs/workflows/lint-github-actions.md) and
[lint-shell](../../docs/workflows/lint-shell.md) fetch the script at their
own commit and run it with those variables instead. The
[set-up-actionlint](../set-up-actionlint/README.md) and
[set-up-shfmt](../set-up-shfmt/README.md) actions run the same script through
a path relative to their own directory.

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
  read the digests GitHub records for release assets (they print as
  `sha256:<hex>`; drop the prefix):

  ```bash
  gh api repos/mvdan/sh/releases/tags/v3.13.1 \
    --jq '.assets[] | "\(.digest) \(.name)"'
  ```

- **Archives.** `archive-member` names the binary inside a tar archive; tar
  detects gzip, xz and bzip2 compression itself. Spell it exactly as
  `tar -tf` lists it: GNU tar on Linux runners treats `./typos` and `typos`
  as different members, while bsdtar on macOS accepts either, so a spelling
  that works on one platform can fail on the other. The member must be a
  regular file, not a symlink, named by a relative path that neither starts
  with `-` nor contains `..`. Only that member is
  extracted, so documentation and man pages packed beside the binary never
  land on disk. Leave it empty when the asset is the binary itself.
- **Install location.** The binary is installed as `<install-dir>/<tool>`,
  where `install-dir` is `$RUNNER_TEMP/<tool>-bin`. Downloads use `https://`
  only, and a redirect to plain `http://` fails the step.

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
- uses: cboone/gh-actions/actions/install-pinned-tool@v3.1.1
  with:
    tool: shfmt
    version: 3.13.1
    url-template: https://github.com/mvdan/sh/releases/download/v{version}/shfmt_v{version}_{os}_{arch}
    checksums: |
      fb096c5d1ac6beabbdbaa2874d025badb03ee07929f0c9ff67563ce8c75398b1  shfmt_v3.13.1_linux_amd64
      32d92acaa5cd8abb29fc49dac123dc412442d5713967819d8af2c29f1b3857c7  shfmt_v3.13.1_linux_arm64
      6feedafc72915794163114f512348e2437d080d0047ef8b8fa2ec63b575f12af  shfmt_v3.13.1_darwin_amd64
      9680526be4a66ea1ffe988ed08af58e1400fe1e4f4aef5bd88b20bb9b3da33f8  shfmt_v3.13.1_darwin_arm64
- run: shfmt -d .
```

An archive verified against the upstream checksum file:

```yaml
- uses: cboone/gh-actions/actions/install-pinned-tool@v3.1.1
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
- uses: cboone/gh-actions/actions/install-pinned-tool@v3.1.1
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
- uses: cboone/gh-actions/actions/install-pinned-tool@v3.1.1
  with:
    tool: uv
    version: 0.11.8
    url-template: https://github.com/astral-sh/uv/releases/download/{version}/uv-{arch}-{os}.tar.gz
    checksums-url-template: https://github.com/astral-sh/uv/releases/download/{version}/uv-{arch}-{os}.tar.gz.sha256
    os-names: linux=unknown-linux-gnu darwin=apple-darwin
    arch-names: amd64=x86_64 arm64=aarch64
    archive-member: uv-{arch}-{os}/uv
```
