# lint-text

Run Markdown linting, Prettier formatting checks, cspell spelling checks,
and yamllint YAML validation. Each tool can be toggled independently.

**Permissions:** `contents: read`

## Inputs

| Name               | Type    | Default     | Description                               |
| ------------------ | ------- | ----------- | ----------------------------------------- |
| `node-version`     | string  | `"24.15.0"` | Node.js version to install                |
| `run-markdownlint` | boolean | `true`      | Run markdownlint-cli2                     |
| `run-prettier`     | boolean | `true`      | Run Prettier format check                 |
| `run-cspell`       | boolean | `false`     | Run cspell spell checker                  |
| `run-yamllint`     | boolean | `false`     | Run yamllint                              |
| `preset`           | string  | `""`        | Optional preset config bundle (see below) |
| `timeout-minutes`  | number  | `10`        | Job timeout in minutes                    |

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
