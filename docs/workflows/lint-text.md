# lint-text

Run Markdown linting, Prettier formatting checks, cspell spelling checks,
and yamllint YAML validation. Each tool can be toggled independently.

After setup succeeds, every enabled tool runs even if an earlier linter
fails, so the job reports all tools' findings in one run. The job fails
if any tool fails. Setup failures prevent the lint checks from running,
and cancellation stops subsequent checks.

**Permissions:** `contents: read`

## Inputs

| Name                    | Type    | Default     | Description                                                               |
| ----------------------- | ------- | ----------- | ------------------------------------------------------------------------- |
| `node-version`          | string  | `"24.21.0"` | Node.js version to install                                                |
| `run-markdownlint`      | boolean | `true`      | Run markdownlint-cli2                                                     |
| `run-prettier`          | boolean | `true`      | Run Prettier format check                                                 |
| `run-cspell`            | boolean | `false`     | Run cspell spell checker                                                  |
| `run-yamllint`          | boolean | `false`     | Run yamllint                                                              |
| `preset`                | string  | `""`        | Optional preset config bundle (see below)                                 |
| `use-consumer-versions` | boolean | `false`     | Install npm-based lint tools from the consumer's own lockfile (see below) |
| `extra-cspell-packages` | string  | `""`        | Extra cspell dictionary packages to install (see below)                   |
| `cspell-config`         | string  | `""`        | Path to a cspell config file (auto-discovered when empty)                 |
| `cspell-files`          | string  | `"."`       | Files and globs for cspell to check, one per line                         |
| `timeout-minutes`       | number  | `10`        | Job timeout in minutes                                                    |

### Preset configs

The `preset` input opts into a curated config bundle for markdownlint
and cspell. A local consumer config always wins; the preset is a
fallback for repos that don't ship their own. Valid values:

- `""` (default): no preset; tools use the consumer's local config or
  their built-in defaults.
- `"lean-math"`: Pandoc-flavored academic Markdown with LaTeX-math
  cspell ignores. Targets Lean + paper-backed formalization repos.

The `lean-math` preset relaxes markdownlint rules that conflict with
academic prose conventions (`MD013`, `MD025`, `MD033`, `MD040`,
`MD041`, `MD060`, plus tuned `MD010`, `MD024`, `MD026`) and ignores
`.lake/**`, `references/papers/**`, `references/papers.bib`,
`references/transcriptions/**`, and `docs/plans/done/**`. The cspell
preset adds regex ignores for inline and display math, raw `{=latex}`
fenced blocks, Pandoc citation groups, bare citekeys, and LaTeX
commands; it also wires up a `project-words` dictionary that points at
`./cspell-words.txt` in the consumer repo.

Precedence per tool:

1. If the consumer ships a local config file (e.g.
   `.markdownlint-cli2.jsonc`, `cspell.json`, `cspell.jsonc`, etc.),
   the local config is used and the preset is skipped for that tool.
2. Otherwise, if `preset` is set, the preset config is fetched from
   this repo at the workflow's own SHA and dropped into the workspace
   so auto-discovery picks it up.
3. Otherwise, the tool runs with its built-in defaults.

The full preset sources live at `presets/<name>/` in this repo.

Setting `cspell-config` sits above all three for cspell: an explicit
`--config` is the strongest form of a consumer config, so the cspell
preset is skipped without being fetched. The markdownlint preset is
unaffected, so `preset` plus `cspell-config` is a supported combination
for a repo that wants the preset's markdownlint rules and its own
spelling config.

### Tool versions: pinned vs. consumer

By default, the workflow installs markdownlint-cli2, Prettier, and
cspell from this repo's own pinned `package.json` and
`package-lock.json` (fetched at the workflow's own SHA, sha512-verified
by `npm ci`). This guarantees the same versions across every consumer
repo, but it can drift from the versions a consumer pins locally in
their own `package.json`. When the major versions diverge (e.g. cspell
v8 locally vs. cspell v10 in CI), default-dictionary differences can
cause linting to pass locally and fail in CI, or vice versa.

Set `use-consumer-versions: true` to install from the consumer's own
committed `package.json` + `package-lock.json` instead. The workflow
runs `npm ci` in the workspace, so npm still enforces per-package
sha512 integrity; the trust boundary becomes the consumer's reviewed
lockfile rather than this gh-actions repo. Requirements when
`use-consumer-versions: true`:

- The consumer must have `package.json` and `package-lock.json`
  committed at the repo root.
- Every enabled npm-based tool (`run-markdownlint`, `run-prettier`,
  `run-cspell`) must be present in the consumer's `package-lock.json`,
  typically declared as a `devDependency` in `package.json`. The
  workflow fails fast with a clear error if either file is missing.
  After `npm ci`, a validation step checks that each enabled tool's
  binary resolves on `PATH` and emits a targeted `::error::` annotation
  naming the missing tool and the fix (add it to `devDependencies` in
  `package.json` and commit the updated `package-lock.json`) before the
  run step would otherwise fail with `command not found`.

`yamllint` is unaffected by this input (Python tool, installed via
`uv pip install --require-hashes` from this repo's
`requirements/yamllint.txt`).

### cspell file coverage

By default the workflow runs `cspell .` using the consumer's cspell
config. `cspell-config` passes `--config <path>` instead of relying on
auto-discovery, and `cspell-files` replaces the `.` argument with
newline-delimited files and globs, so an argument containing spaces
survives:

```yaml
cspell-config: config/cspell.json
cspell-files: |
  docs
  README.md
```

cspell excludes dot-paths by default, including `.github/` and root
dot-config files. To include them and respect `.gitignore`, add these
settings to the consumer's `cspell.json`:

```json
{
  "enableGlobDot": true,
  "useGitignore": true
}
```

`useGitignore` keeps ignored local directories such as `.local/` and
`.workmux/` out of the scan. Configured `ignorePaths` still apply.

### Extra cspell dictionaries

cspell bundles English-family dictionaries and a few technical ones, so
any other natural language needs a package it does not ship. By default
this workflow installs only what this repo's lockfile pins, so a
consumer config importing such a package has nothing to resolve against.
`extra-cspell-packages` names the packages to add.

Each entry is two whitespace-separated fields on one line. Blank lines
and `#` comments are ignored, and the input is ignored entirely when
`run-cspell` is false.

```yaml
extra-cspell-packages: |
  @cspell/dict-pt-pt@3.0.6  sha512-RT3EovAHK086ta4efTp+PxT9a2fZFHGrsf6AhX6LoFfxCn2RZAnITULSuVgkwpD/3Z/Di7oSXXNfeW9LKtGpGQ==
```

The version must be exact: a range, a dist-tag such as `latest`, and a
git, file or URL spec are all rejected, since the integrity pins one
published tarball. Get the second field from npm:

```bash
npm view @cspell/dict-pt-pt@3.0.6 dist.integrity
```

Consumers keep writing the idiomatic import and never learn where CI put
the tools:

```jsonc
{ "import": ["@cspell/dict-pt-pt/cspell-ext.json"], "language": "en,pt-PT" }
```

That resolves because the packages are installed beside cspell, wherever
this workflow put it, and cspell searches `cspell-lib`'s own directory as
well as the config file's. It works the same under
`use-consumer-versions: true`, where cspell lives in the consumer's
workspace instead.

Each tarball is downloaded from its deterministic registry URL and
verified against the caller's integrity before npm reads it, so the
registry supplies bytes rather than trust: the digest is reviewed and
committed in the calling repository. Keying on the exact
`<name>@<version>` means a version bumped without its integrity fails
with a mismatch rather than verifying against a stale digest. A package
that declares dependencies is refused, in `dependencies`,
`optionalDependencies` or `peerDependencies` alike, because npm would
resolve all three from the registry unverified; dictionary packages ship
data and normally declare none. The
[install-cspell-dictionaries](../../actions/install-cspell-dictionaries/README.md)
action implements this and can be driven directly.

A dictionary that is not on npm is a different mechanism: commit the
`.txt` or `.trie.gz` file and point at it with a `dictionaryDefinitions`
entry in your own cspell config, whose `path` is resolved relative to
that config file. Note that `path` does no package resolution at all, so
a bare package specifier there cannot work; only `import` resolves
packages.

### How the workflow reaches its own manifests

The preset configs, `package.json` + `package-lock.json`,
`requirements/yamllint.txt`, and the dictionary installer
`actions/install-cspell-dictionaries/install-cspell-dictionaries.sh` all
live in this repo, not the consumer's. The workflow fetches them over
`raw.githubusercontent.com` from
`${{ job.workflow_repository }}` at `${{ job.workflow_sha }}`: the
repository and commit the workflow file itself came from, which is
whatever ref the caller pinned. That is what keeps the manifests and the
workflow logic on the same commit, so a tampered registry response
cannot pass the per-package integrity check.

Two limitations follow from it:

- **GitHub Enterprise Server.** The `job.workflow_*` properties are not
  available there, so any step that fetches fails with an `::error::`
  naming the constraint. A fully working configuration on GHES is
  `use-consumer-versions: true` with `preset: ""`,
  `extra-cspell-packages: ""` and `run-yamllint: false`: it fetches
  nothing and still gets per-package sha512 integrity from the
  consumer's own lockfile. A non-English repo there can vendor the
  dictionary file and reference it from `dictionaryDefinitions`, or add
  the dictionary package to its own `package.json` (which
  `use-consumer-versions: true` then installs into the workspace, where
  a bare `import` resolves).
- **Private forks of this repo.** `raw.githubusercontent.com` serves
  public repositories only. A private fork cannot supply its own
  manifests; use `use-consumer-versions: true` there as well, ship
  local markdownlint and cspell configs instead of a preset, and reach
  for the same two alternatives for dictionaries.

Consumers on `@v3.0.0` or `@v3.1.0` fail here on default inputs: those
releases read `github.job_workflow_sha`, which is not a real context
property and is always empty
([#83](https://github.com/cboone/gh-actions/issues/83)). On `@v3.0.0`
the failure is unconditional. On `@v3.1.0` the only configuration that
avoids it is `use-consumer-versions: true` with `preset: ""` and
`run-yamllint: false`. The fix ships in `v3.1.1`; pin `@v3.1.1` or
later.

## Usage

```yaml
jobs:
  text:
    uses: cboone/gh-actions/.github/workflows/lint-text.yml@v4.0.0
    with:
      run-cspell: true
```

Academic Markdown repo with the `lean-math` preset:

```yaml
jobs:
  text:
    uses: cboone/gh-actions/.github/workflows/lint-text.yml@v4.0.0
    with:
      run-cspell: true
      run-prettier: false
      preset: lean-math
```

Repo that wants CI to use its own pinned tool versions from
`package.json` (so local linting and CI agree):

```yaml
jobs:
  text:
    uses: cboone/gh-actions/.github/workflows/lint-text.yml@v4.0.0
    with:
      run-cspell: true
      use-consumer-versions: true
```

Repo whose prose is not in English. It adds a dictionary that cspell does
not bundle, and its own `cspell.json` imports it:

```yaml
jobs:
  text:
    uses: cboone/gh-actions/.github/workflows/lint-text.yml@v4.0.0
    with:
      run-cspell: true
      extra-cspell-packages: |
        @cspell/dict-pt-pt@3.0.6  sha512-RT3EovAHK086ta4efTp+PxT9a2fZFHGrsf6AhX6LoFfxCn2RZAnITULSuVgkwpD/3Z/Di7oSXXNfeW9LKtGpGQ==
```

Repo whose cspell config is not at a name cspell auto-discovers, and
which spell-checks only part of the tree:

```yaml
jobs:
  text:
    uses: cboone/gh-actions/.github/workflows/lint-text.yml@v4.0.0
    with:
      run-cspell: true
      cspell-config: config/cspell.json
      cspell-files: |
        docs
        README.md
```
