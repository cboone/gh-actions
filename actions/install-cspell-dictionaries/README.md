# install-cspell-dictionaries

Install cspell dictionary packages from npm, each pinned to an exact version
and verified against a caller-supplied sha512, beside an existing cspell
installation. cspell bundles English-family dictionaries and a few technical
ones, so any other natural language needs a package it does not ship.

Installing beside cspell is what makes the dictionaries reachable. cspell
resolves a bare `import` specifier against `cspell-lib`'s own directory as
well as the config file's, so a consumer keeps writing the idiomatic form and
never learns where CI put the tools:

```jsonc
{ "import": ["@cspell/dict-pt-pt/cspell-ext.json"], "language": "en,pt-PT" }
```

Node.js and npm must be available on the runner, as they already are wherever
cspell is installed. Linux and macOS runners only.

Most callers do not use this action directly. The
[lint-text](../../docs/workflows/lint-text.md) reusable workflow drives it
through `extra-cspell-packages`, and [run-cspell](../run-cspell/README.md)
through `extra-packages`. Reach for it when cspell is installed by something
else and the dictionaries have to follow.

## Trust model

Every tarball is downloaded from its deterministic registry URL and verified
against the caller's integrity before npm reads it, so the registry is never
the integrity boundary: it supplies bytes, and those bytes must match a
digest reviewed and committed in the calling repository. Keying on the exact
`<name>@<version>` means a version bumped without its integrity fails with a
mismatch rather than verifying against a stale digest.

A package that declares dependencies is refused, in any of `dependencies`,
`optionalDependencies` and `peerDependencies`. npm installs optional ones by
default and resolves peers on its own from version 7, so all three would
reach the registry unverified, and nothing may reach `node_modules` that the
caller did not hash. The unpack step passes `--omit=dev --omit=optional
--omit=peer` as well, so that holds even for a tarball that somehow gets past
the manifest check. Dictionary packages ship data and normally declare none.

## Inputs

| Name          | Type   | Default | Description                                                           |
| ------------- | ------ | ------- | --------------------------------------------------------------------- |
| `packages`    | string | none    | `<name>@<version>  sha512-<base64>` entries, one per line (see below) |
| `install-dir` | string | none    | npm project directory whose `node_modules/` already holds cspell      |

Both inputs are required.

### Entry format

Two whitespace-separated fields per line. Blank lines and `#` comments are
ignored, and an empty `packages` installs nothing. Each package may be named
only once, since its integrity pins one version.

```text
@cspell/dict-pt-pt@3.0.6  sha512-RT3EovAHK086ta4efTp+PxT9a2fZFHGrsf6AhX6LoFfxCn2RZAnITULSuVgkwpD/3Z/Di7oSXXNfeW9LKtGpGQ==
```

The version must be exact. A range (`^3.0.6`), a dist-tag (`latest`), and a
git, file or URL spec are all rejected, since the integrity pins one
published tarball. Get the second field from npm:

```bash
npm view @cspell/dict-pt-pt@3.0.6 dist.integrity
```

Packages are fetched from `https://registry.npmjs.org`, which is not
configurable.

## Exit codes

| Code | Meaning                                                           |
| ---- | ----------------------------------------------------------------- |
| `0`  | Installed, or nothing to install                                  |
| `64` | Invalid or missing input                                          |
| `65` | Integrity malformed or mismatched                                 |
| `66` | Package tarball rejected: unreadable, or it declares dependencies |
| `69` | Download failed                                                   |
| `70` | npm failed to install a verified tarball                          |

## Usage

```yaml
- uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
  with:
    node-version: "24.21.0"
- run: npm ci
- uses: cboone/gh-actions/actions/install-cspell-dictionaries@v3.2.0
  with:
    install-dir: ${{ github.workspace }}
    packages: |
      @cspell/dict-pt-pt@3.0.6  sha512-RT3EovAHK086ta4efTp+PxT9a2fZFHGrsf6AhX6LoFfxCn2RZAnITULSuVgkwpD/3Z/Di7oSXXNfeW9LKtGpGQ==
```
