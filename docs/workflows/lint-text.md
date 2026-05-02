# lint-text

Run Markdown linting, Prettier formatting checks, cspell spelling checks,
and yamllint YAML validation. Each tool can be toggled independently.

**Permissions:** `contents: read`

## Inputs

| Name                    | Type    | Default     | Description                                                                  |
| ----------------------- | ------- | ----------- | ---------------------------------------------------------------------------- |
| `node-version`          | string  | `"24.15.0"` | Node.js version to install                                                   |
| `run-markdownlint`      | boolean | `true`      | Run markdownlint-cli2                                                        |
| `run-prettier`          | boolean | `true`      | Run Prettier format check                                                    |
| `run-cspell`            | boolean | `false`     | Run cspell spell checker                                                     |
| `run-yamllint`          | boolean | `false`     | Run yamllint                                                                 |
| `preset`                | string  | `""`        | Optional preset config bundle (see below)                                    |
| `use-consumer-versions` | boolean | `false`     | Install npm-based lint tools from the consumer's own lockfile (see below)    |
| `timeout-minutes`       | number  | `10`        | Job timeout in minutes                                                       |

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
  `run-cspell`) must be listed as a `devDependency` in the consumer's
  `package.json`. The workflow fails fast with a clear error if either
  file is missing; if a tool is missing from `devDependencies`, the
  corresponding run step fails with `command not found`.

`yamllint` is unaffected by this input (Python tool, installed via
`uv pip install --require-hashes` from this repo's
`requirements/yamllint.txt`).

## Usage

```yaml
jobs:
  text:
    uses: cboone/gh-actions/.github/workflows/lint-text.yml@v3.0.0
    with:
      run-cspell: true
```

Academic Markdown repo with the `lean-math` preset:

```yaml
jobs:
  text:
    uses: cboone/gh-actions/.github/workflows/lint-text.yml@v3.0.0
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
    uses: cboone/gh-actions/.github/workflows/lint-text.yml@v3.0.0
    with:
      run-cspell: true
      use-consumer-versions: true
```
