# run-cspell

Install cspell and run it with inline pull-request annotations. Thin
alternative to
[`streetsidesoftware/cspell-action`](https://github.com/streetsidesoftware/cspell-action).
Installs cspell from this repo's sha512-pinned `package-lock.json` (same
trust path as the [lint-text](../../docs/workflows/lint-text.md) reusable
workflow) and registers a problem matcher so cspell's default
`path:line:col - Unknown word` output surfaces as PR annotations. Extra
dictionaries named through `extra-packages` are pinned the same way, against
a sha512 the caller commits.

Node.js must be available on the runner; pair with `actions/setup-node` if it
is not already installed. For most projects, the
[lint-text](../../docs/workflows/lint-text.md) reusable workflow with
`run-cspell: true` is a better fit; reach for this action when you need
cspell standalone in a larger custom workflow.

## Inputs

| Name             | Type   | Default | Description                                               |
| ---------------- | ------ | ------- | --------------------------------------------------------- |
| `files`          | string | `.`     | Newline-delimited globs passed to cspell                  |
| `config`         | string | `""`    | Path to a cspell config file (auto-discovered when empty) |
| `args`           | string | `""`    | Extra arguments to pass to cspell, one per line           |
| `extra-packages` | string | `""`    | Extra cspell dictionary packages to install (see below)   |

### Extra dictionaries

cspell bundles English-family dictionaries and a few technical ones, so any
other natural language needs a package it does not ship. Each entry is two
whitespace-separated fields on one line:

```yaml
extra-packages: |
  @cspell/dict-pt-pt@3.0.6  sha512-RT3EovAHK086ta4efTp+PxT9a2fZFHGrsf6AhX6LoFfxCn2RZAnITULSuVgkwpD/3Z/Di7oSXXNfeW9LKtGpGQ==
```

The version must be exact and the sha512 is required; get it from
`npm view <name>@<version> dist.integrity`. The packages install beside the
cspell this action installed, which is what lets your config keep the
idiomatic `"import": ["@cspell/dict-pt-pt/cspell-ext.json"]`. See
[install-cspell-dictionaries](../install-cspell-dictionaries/README.md) for
the trust model and the rejection rules.

## Usage

```yaml
- uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
  with:
    node-version: "24.21.0"
- uses: cboone/gh-actions/actions/run-cspell@v5.0.0
```
