# Caller-provided extra cspell dictionaries

Issue: [#72](https://github.com/cboone/gh-actions/issues/72)

## Context

`lint-text.yml` installs markdownlint-cli2, Prettier and cspell from
**this repo's** `package.json` + `package-lock.json`, curled at
`job.workflow_sha` and installed with `npm ci`. That keeps per-package
sha512 integrity, but it also means the tool tree contains only what
gh-actions pins. cspell bundles no Portuguese dictionary, so a consumer
whose `cspell.json` says:

```jsonc
{ "import": ["@cspell/dict-pt-pt/cspell-ext.json"], "language": "en,pt-PT" }
```

fails with a configuration-loader error, because `@cspell/dict-pt-pt`
is in neither the tool tree nor the workspace. With `run-cspell: true`
and no Portuguese dictionary, cspell would otherwise flag essentially
every Portuguese word. This blocks `cboone/dicionario-ios` from using
the reusable workflow at all; it ships a bespoke inline `text-lint.yml`
instead.

The outcome: a caller can name extra cspell dictionary packages, pinned
to an exact version **and** to a sha512 the caller reviews and commits,
so the repo's standing guarantee still holds. From
[README.md](../../../README.md#trust-model-and-pinning) and
[AGENTS.md](../../../AGENTS.md#pinning-policy-and-trust-model): never
let an upstream registry be the sole integrity boundary for anything
that runs in CI.

### Two verified facts the design rests on

Both were checked against the pinned cspell 10.3.0 and the live
registry, not inferred.

1. **A dictionary installed as a sibling of `cspell-lib` resolves from a
   config file anywhere else in the tree.** `FileResolver`'s
   `tryImportResolve` step
   (`cspell-lib/dist/lib/util/resolveFile.js:184`) resolves a bare
   specifier against `[relativeTo, srcDirectory]`, where `srcDirectory`
   (`cspell-lib/dist/lib/pkg-info.mjs:6-14`) is cspell-lib's **own**
   install location. Node's package resolution then walks its ancestors
   and reaches `<install-dir>/node_modules/@cspell/dict-pt-pt`. So the
   consumer keeps the idiomatic bare `import` and nothing in their
   config has to know about runner paths.
2. **npm's published `dist.integrity` is reproducible from the tarball.**
   `curl <tarball> | openssl dgst -sha512 -binary | openssl base64 -A`
   returns exactly the `dist.integrity` string for
   `@cspell/dict-pt-pt@3.0.6`. The tarball URL is deterministic
   (`https://registry.npmjs.org/<name>/-/<unscoped-name>-<version>.tgz`),
   so no registry metadata call is needed and the registry is never
   trusted for anything but the bytes, which are then verified.

Three routes were rejected: `NODE_PATH` (cspell never reads it, and the
two `require.resolve` steps in `resolveFile.js` are dead code under
ESM); `cspell link add` / the global config (works, but applies to every
run, cannot be disabled, and writes outside the workspace);
`CSPELL_DEFAULT_CONFIG_PATH` (fires only when no config is found at all,
so it is dead the moment the consumer ships a `cspell.json`).

## Design

One new composite action holds the logic; `lint-text.yml` and
`run-cspell` both drive it. This mirrors `install-pinned-tool`: a
generic, separately testable installer plus thin callers.

Entry syntax, one per line, two whitespace-separated fields:

```yaml
extra-cspell-packages: |
  @cspell/dict-pt-pt@3.0.6  sha512-RT3EovAHK086ta4efTp+PxT9a2fZFHGrsf6AhX6LoFfxCn2RZAnITULSuVgkwpD/3Z/Di7oSXXNfeW9LKtGpGQ==
```

The caller gets the second field from
`npm view <name>@<version> dist.integrity`. Keying on the exact
`<name>@<version>` means a version bumped without its integrity fails
with a mismatch rather than verifying against a stale digest, the same
property `install-pinned-tool`'s literal `checksums` keys give.

### 1. `actions/install-cspell-dictionaries/` (new)

`install-cspell-dictionaries.sh`, driven entirely through environment
variables so the action, the reusable workflow and `run-cspell` all
invoke it identically:

| Variable      | Input         | Meaning                                                          |
| ------------- | ------------- | ---------------------------------------------------------------- |
| `PACKAGES`    | `packages`    | `<name>@<version>  sha512-<base64>` entries, one per line        |
| `INSTALL_DIR` | `install-dir` | npm project directory whose `node_modules/` already holds cspell |

Per run:

1. `require_runner_env RUNNER_TEMP`. Require `INSTALL_DIR` to be a
   directory containing `node_modules/cspell-lib`, so pointing it
   somewhere cspell cannot see fails with that sentence rather than with
   a dictionary that silently never loads.
1. Split `PACKAGES` on newlines only (the two fields are whitespace
   separated, so the `tr -s '[:space:]' '\n'` idiom from
   `install-pinned-tool.sh:179` does not apply here). Skip blank lines
   and `#` comments. Empty input installs nothing and exits 0.
1. Per entry, require exactly two fields, then validate:
   - spec against `^(@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*@[0-9]+\.[0-9]+\.[0-9]+([-+][0-9A-Za-z.-]+)*$`,
     which admits an exact version with optional prerelease or build
     metadata and rejects ranges, dist-tags, git, file and URL specs,
     and anything starting with `-`
   - integrity against `^sha512-[A-Za-z0-9+/]{86}==$` (a 64-byte digest
     is always 88 base64 characters)
1. Download
   `https://registry.npmjs.org/<name>/-/<name##*/>-<version>.tgz` with
   the same hardened `curl` flags as `install-pinned-tool.sh:229-231`
   (`--proto '=https'`, retries, `--retry-all-errors`).
1. Verify with `openssl dgst -sha512 -binary` piped through
   `openssl base64 -A`, which works on both GNU coreutils and LibreSSL
   (`base64 -w0` is GNU-only and this script also runs on macOS).
   Mismatch exits 65.
1. Read `package/package.json` out of the verified tarball and refuse
   the package if it declares runtime `dependencies`. This is what makes
   the guarantee airtight: only bytes the caller hashed are installed,
   with nothing pulled in behind them.
1. `npm install --ignore-scripts --no-audit --no-fund` the verified
   tarballs inside a throwaway `${RUNNER_TEMP}/cspell-dictionaries`
   holding a minimal `package.json`, so npm does the extraction and
   cannot reify, prune or otherwise disturb the pinned tree. Then `mv`
   each named package into `${INSTALL_DIR}/node_modules/<name>`.
1. Report each installed package and its verified digest.

Exit codes follow `install-pinned-tool.sh:50-54`: `64` invalid or
missing input, `65` malformed or mismatched integrity, `66` package
rejected (declares runtime dependencies), `69` download failed, `70`
`npm install` of a verified tarball failed. No platform detection: npm
dictionary packages are architecture independent, so there is no `71`.

Constraints to honor, because this script runs under `/bin/bash` 3.2 on
macOS runners exactly as `install-pinned-tool.sh` does: no associative
arrays, no `mapfile`, no `${var,,}`, and `"$@"` rather than `"${@}"`.
`escape_data`, `fail`, `cleanup`, `require_runner_env` and `download`
are deliberately duplicated from `install-pinned-tool.sh` rather than
factored out; each script is fetched standalone at a workflow's own
commit, and a shared library would double the fetch. Say so in the
header.

`action.yml` follows `actions/install-pinned-tool/action.yml`: bind the
script path in `env:` as `INSTALLER` (never inline
`${{ github.action_path }}` into `run:`, per
`.github/copilot-instructions.md:24`), pass the two inputs through
`env:`, `run: bash "${INSTALLER}"`.

`README.md` from the per-component template in
[AGENTS.md](../../../AGENTS.md), Usage example pinned `@v3.1.1`.

### 2. `.github/workflows/lint-text.yml`

- New `extra-cspell-packages` input (string, default `""`), declared
  after `use-consumer-versions` and before `timeout-minutes`.
- Both install steps publish the npm project directory cspell landed in:
  `CSPELL_INSTALL_DIR=${install_dir}` (the pinned path) or
  `CSPELL_INSTALL_DIR=${GITHUB_WORKSPACE}` (the consumer path), appended
  to `${GITHUB_ENV}`. The dictionary step then targets exactly where
  cspell is, in either mode, with no second copy of the path literal.
- `Fetch install-cspell-dictionaries`, copied from `lint-shell.yml:92-113`:
  guard `job.workflow_repository` / `job.workflow_sha`, curl the script
  from `raw.githubusercontent.com` into `RUNNER_TEMP`. The `job` context
  is only available on steps, so the bindings stay in this step's `env:`
  (`.github/copilot-instructions.md:51`).
- `Install extra cspell dictionaries`, gated on
  `inputs.run-cspell && inputs.extra-cspell-packages != ''`, with
  `INSTALL_DIR: ${{ env.CSPELL_INSTALL_DIR }}`. Both steps sit after
  `Validate consumer-installed lint tools` and before `Run markdownlint`,
  so a bad entry fails before any linter runs.
- The input is ignored when `run-cspell` is false, matching how the
  preset steps skip work for a disabled tool.

### 3. `actions/run-cspell/`

- New `extra-packages` input (string, default `""`). The shorter name
  matches how `set-up-shfmt`'s `checksums` relates to `lint-shell.yml`'s
  `shfmt-checksums`: the action is already cspell-scoped, the
  multi-tool workflow is not.
- An `Install extra cspell dictionaries` step after `Install cspell`,
  gated on `inputs.extra-packages != ''`, reaching the sibling script at
  `${{ github.action_path }}/../install-cspell-dictionaries/install-cspell-dictionaries.sh`
  bound in `env:` as `INSTALLER`, the way `set-up-shfmt/action.yml:37`
  reaches `install-pinned-tool.sh`. A `uses: ./` reference would resolve
  against the caller's workspace. `INSTALL_DIR` is
  `${{ github.action_path }}/../..`, the gh-actions checkout root where
  the preceding `npm ci` put cspell.

### 4. `.github/workflows/run-ci.yml`

Two additions, splitting the coverage the way the components split.

A matrix job over `ubuntu-latest`, `ubuntu-24.04-arm` and
`macos-latest` (macOS is what exercises bash 3.2 and LibreSSL), modeled
on the existing `install-pinned-tool` job:

- checkout, `actions/setup-node` pinned to the existing SHA
- write a fixture `cspell.json` importing
  `@cspell/dict-pt-pt/cspell-ext.json` plus a short Portuguese sample
  file into `${RUNNER_TEMP}`, so the fixtures never enter the repo tree
  where the repo's own linters would pick them up
- `uses: ./actions/run-cspell` with `config`, `files` and
  `extra-packages`. This is the end-to-end assertion: an unresolved
  import is a configuration error and unresolved Portuguese is a wall of
  unknown words, so a green step proves both the install and the
  `srcDirectory` resolution
- assert `node_modules/@cspell/dict-pt-pt/package.json` exists in the
  checkout
- rejection cases through a `check_rejection` helper lifted from
  `run-ci.yml:186-207`, running the script directly under `/bin/bash`
  with `env -i PATH RUNNER_TEMP INSTALL_DIR PACKAGES` so each case
  asserts an exit code and a message substring: wrong integrity (65),
  malformed integrity (64), version range (64), dist-tag (64), missing
  second field (64), `INSTALL_DIR` without cspell (64). Every case fails
  before npm runs, so `env -i` dropping `HOME` is harmless.

Plus a `text-extra-dicts` job calling `./.github/workflows/lint-text.yml`
with `run-cspell: true`, the other three tools off, and
`extra-cspell-packages` set. The action-level job cannot cover the
`job.workflow_*` fetch of the script; this one does. It uses the repo's
own root `cspell.json`, which imports nothing, so it asserts the
workflow wiring rather than resolution.

### 5. Documentation

- `docs/workflows/lint-text.md`: one Inputs row ending in `(see below)`;
  a new `### Extra cspell dictionaries` section (entry format, where the
  integrity comes from, the no-runtime-dependencies rule, that it works
  in both install modes, that it is ignored when `run-cspell` is false,
  and that `dictionaryDefinitions[].path` is the vendored-dictionary
  alternative but does **no** package resolution, so a bare specifier
  there cannot work); a fourth Usage example pinned `@v3.1.1`. Amend
  `### How the workflow reaches its own manifests` to list the script
  among the fetched files and to add `extra-cspell-packages: ""` to the
  GHES "fully working configuration".
- `actions/run-cspell/README.md`: the new input row, and extend the
  "same trust path as the lint-text reusable workflow" sentence to cover
  caller-named dictionaries.
- Root `README.md`: a Quick Reference row for
  `install-cspell-dictionaries` under "Linting and formatting"; extend
  the npm bullet under "Trust model and pinning". The intro's
  "no reliance on third-party registries as the sole integrity boundary"
  claim needs no weakening, which is the payoff of requiring the hash.
- `AGENTS.md`: add the action to the repository-structure tree; extend
  the npm-tools bullet under "Pinning Policy and Trust Model"; note the
  new self-tests under "Testing".
- `.github/copilot-instructions.md`: anti-patterns for the review
  suggestions this design invites, each stating the mechanism. The
  sha512 field is required, not ornamental; dictionaries install beside
  `cspell-lib` because of `srcDirectory`, not in the workspace, and not
  via `NODE_PATH` or `cspell link add`; a package specifier in
  `dictionaryDefinitions[].path` cannot resolve; the helper duplication
  between the two installer scripts is deliberate.
- `CHANGELOG.md`: entries under `[Unreleased]` → `### Added`, tagged
  `(#72)`. A new optional input is a minor bump.
- `cspell.json`: add any words the new prose introduces.

## Out of scope

- `yamllint .` traverses `node_modules` when `use-consumer-versions` is
  true, because the consumer's `npm ci` puts a tree in the workspace and
  yamllint has no default ignores. That is pre-existing and unrelated to
  dictionaries, which never land in the workspace. File it separately.
- A `registry` input for private mirrors. The URL is hardcoded to
  `https://registry.npmjs.org`; document that.

## Verification

1. `make lint` (actionlint), `make lint-md`, `make format-check`,
   `make spell`, `make lint-yaml`.
1. `shellcheck actions/install-cspell-dictionaries/install-cspell-dictionaries.sh`
   and `shfmt -d` on it, which is also what the `shell` job asserts in
   CI.
1. Drive the script locally the way `run-ci.yml` will, against a real
   `node_modules` holding cspell:

   ```bash
   npm ci
   RUNNER_TEMP=/tmp/cspell-dicts-test INSTALL_DIR="${PWD}" \
     PACKAGES='@cspell/dict-pt-pt@3.0.6  sha512-RT3EovAHK086ta4efTp+PxT9a2fZFHGrsf6AhX6LoFfxCn2RZAnITULSuVgkwpD/3Z/Di7oSXXNfeW9LKtGpGQ==' \
     bash actions/install-cspell-dictionaries/install-cspell-dictionaries.sh
   ```

   Then confirm resolution from a config outside the tree: write a
   `cspell.json` in a temporary directory that imports
   `@cspell/dict-pt-pt/cspell-ext.json`, put a Portuguese sentence
   beside it, and run the repo's `npx cspell` against it with `--config`.
   It must report no unknown words. Afterwards
   `rm -rf node_modules/@cspell/dict-pt-pt` so the working tree is not
   left with an unpinned package.

1. Run each rejection case by hand and check the exit code and message,
   before wiring them into `run-ci.yml`.
1. Push the branch and confirm in CI that the new matrix job passes on
   all three runners (bash 3.2 and LibreSSL on macOS are the parts a
   local Linux run cannot cover), and that `text-extra-dicts` passes,
   which is the only proof that the fetch-at-workflow-SHA path works.
1. After merge and release, migrate `cboone/dicionario-ios` off its
   inline `text-lint.yml` to the reusable workflow, which is the
   acceptance test the issue asks for.
