<!-- cspell:ignore Amostra ficheiro contém palavras portuguesas verificação dicionário europeu aceita -->

# A cspell-config input for lint-text

Issue: [#105](https://github.com/cboone/gh-actions/issues/105)

## Context

`lint-text.yml` runs a bare `cspell .` and lets cspell auto-discover its config. `actions/run-cspell` has both a `config` and a `files` input; the reusable workflow has neither. That asymmetry has a concrete cost.

The `text-extra-dicts` and `text-extra-dicts-consumer` self-tests in `run-ci.yml` spell-check this repository using its root `cspell.json`, which imports no extra dictionary. They therefore cannot tell a working dictionary install from one that never ran, because a skipped step is green. They do catch a fetch that 404s, an entry the installer rejects, a digest mismatch, and a wrong `CSPELL_INSTALL_DIR`. Copilot raised the gap twice on [#103](https://github.com/cboone/gh-actions/pull/103), and the comment at `.github/workflows/run-ci.yml:349-363` records it and names this issue as the fix.

Two new inputs close it. A self-contained fixture config that imports `@cspell/dict-pt-pt/cspell-ext.json`, checked against a committed Portuguese sample, fails the job whenever the dictionary is absent for any reason, a skipped install included. The assertion is sound because `@cspell/dict-pt-pt` is not in this repository's `package.json`: it can only be present because the install step put it there, whether beside the pinned cspell in `RUNNER_TEMP` or in the workspace under `use-consumer-versions: true`.

Two decisions were taken before planning:

- **Add `cspell-files` alongside `cspell-config`.** Without it, `--config <fixture> .` would spell-check the whole repository against a config carrying none of the root word list, and the job would fail for the wrong reason. Pointing cspell at the sample file is what makes a self-contained fixture possible, and it closes the same `run-cspell` asymmetry for `files`.
- **An explicit `cspell-config` suppresses the cspell preset.** This extends the rule the preset step already documents and implements, that a local consumer config always beats the preset. An explicit `--config` is the strongest form of that statement, and deferring to it avoids fetching a preset that `--config` would then ignore.

## Design

### 1. `.github/workflows/lint-text.yml`

Two new `workflow_call` inputs, after `extra-cspell-packages` and before `timeout-minutes`, which is always last in every workflow in this repository:

```yaml
cspell-config:
  description: |
    Path to a cspell config file, passed as `--config`. When empty,
    cspell auto-discovers `cspell.json` / `.cspell.json` /
    `cspell.config.*` from the working tree. Setting this suppresses
    the cspell half of `preset`, since an explicit config is the
    strongest form of a consumer config. Ignored when run-cspell is
    false.
  type: string
  default: ""
cspell-files:
  description: |
    Files and globs for cspell to check, one per line. Defaults to the
    whole workspace. Ignored when run-cspell is false.
  type: string
  default: "."
```

The `Run cspell` step (`lint-text.yml:397-399`) gains `env:` bindings and mirrors the argument assembly in `actions/run-cspell/action.yml:96-108`:

```yaml
- name: Run cspell
  if: ${{ !cancelled() && steps.lint-tools-ready.outcome == 'success' && inputs.run-cspell }}
  env:
    CSPELL_CONFIG: ${{ inputs.cspell-config }}
    CSPELL_FILES: ${{ inputs.cspell-files }}
  run: |
    args=()
    if [ -n "${CSPELL_CONFIG}" ]; then
      args+=(--config "${CSPELL_CONFIG}")
    fi
    files=()
    while IFS= read -r line; do
      [ -n "${line}" ] && files+=("${line}")
    done <<< "${CSPELL_FILES}"
    cspell "${args[@]}" "${files[@]}"
```

Both inputs reach the shell through `env:`, per the root `AGENTS.md` rule. The default `cspell-files: "."` preserves today's behavior exactly.

No step is added, and the step keeps its name and position. `tests/fixtures/generate-text-lint-scheduling.mjs:26-31` asserts that the steps after the `lint-tools-ready` barrier are exactly `Run markdownlint`, `Run Prettier check`, `Run cspell` and `Run yamllint`. That generator binds only inputs that appear in `if:` conditions (lines 46-51) and discards `env:` and non-barrier `run:` bodies, so neither new input reaches it and its `inputs` object at lines 37-41 needs no entry.

The `Apply cspell preset` step (`lint-text.yml:153-188`) gains the same `CSPELL_CONFIG` binding and an early exit ahead of the existing 13-filename probe:

```bash
if [ -n "${CSPELL_CONFIG}" ]; then
  echo "Explicit cspell-config set; skipping preset."
  exit 0
fi
```

`Apply markdownlint preset` is untouched, so `preset: lean-math` combined with an explicit `cspell-config` still gets the markdownlint half of the preset. The frozen 13-name detection list is not extended.

### 2. `tests/fixtures/cspell-extra-dict/` (new)

A self-contained `cspell.json`, mirroring the out-of-checkout fixture that `run-ci.yml:1010-1021` writes at runtime:

```json
{
  "version": "0.2",
  "language": "en,pt-PT",
  "import": ["@cspell/dict-pt-pt/cspell-ext.json"]
}
```

An `amostra.md` carrying the same prose the action-level job already proves passes with the dictionary installed:

```markdown
# Amostra

Este ficheiro contém palavras portuguesas que só uma
verificação com o dicionário europeu aceita.
```

No `--root` is needed here, unlike the action-level fixture: these files sit inside the workspace, so cspell's default glob root is already correct. The config deliberately does not import the root `cspell.json`, which keeps it independent of the repository's word list and makes the dictionary import the only thing it depends on.

### 3. Root `cspell.json`

`ignorePaths` gains `"tests/fixtures/cspell-extra-dict/"`, so the `text` job and `make spell` skip both the Portuguese sample and the fixture config. Prettier needs no exclusion (`proseWrap: "preserve"` leaves the prose alone), and markdownlint and yamllint need none either.

### 4. `.github/workflows/run-ci.yml`

Both `text-extra-dicts` and `text-extra-dicts-consumer` gain:

```yaml
cspell-config: tests/fixtures/cspell-extra-dict/cspell.json
cspell-files: tests/fixtures/cspell-extra-dict/amostra.md
```

These are literal relative paths with no expression, which keeps true the claim in `.github/copilot-instructions.md` that these two reusable-workflow calls reference no context at all.

Rewrite the comment block at lines 349-363. The two jobs now prove resolution as well as fetch and wiring, so the paragraph explaining why a caller cannot place an assertion, and the `#105` reference, are replaced by a description of what the fixture asserts and why a missing dictionary cannot pass.

### 5. Documentation

- `docs/workflows/lint-text.md`: two rows in the inputs table; the `### cspell file coverage` sentence "The workflow runs `cspell .` using the consumer's cspell config" becomes conditional on the new inputs; the preset section records that `cspell-config` suppresses the cspell preset; one Usage example targeting an explicit config.
- `.github/workflows/AGENTS.md`, bullet 6: "cspell's resolution fixture is outside the checkout" now names both fixtures and says what each is for.
- `docs/development.md:431-436`: a companion sentence for the in-checkout workflow-level fixture, explaining why it does not undercut the out-of-checkout rationale. The workflow installs dictionaries into `RUNNER_TEMP` or the workspace root, never into `tests/fixtures/cspell-extra-dict/node_modules`, so a bare import there still exercises the beside-`cspell-lib` path rather than an ordinary `node_modules` walk from the fixture.
- `CHANGELOG.md`: a new `### Added` section above the existing `### Fixed` under `## [Unreleased]`.
- Root `README.md`: no change. The `lint-text` row is a one-line summary and the tables are deliberately flat.

## Out of scope

- `--no-progress`, which `run-cspell` passes and `lint-text.yml` does not. Adding it would change output for every existing consumer and is unrelated to this issue.
- The `yamllint .` versus `node_modules` interaction under `use-consumer-versions: true`, already noted in `run-ci.yml` and left alone.
- The interpolation gaps tracked in [#115](https://github.com/cboone/gh-actions/issues/115).

## Verification

1. `npm ci`, then `make lint lint-md format-check spell lint-yaml`.
2. Confirm the fixture asserts what it claims. On a clean tree, `npx cspell --config tests/fixtures/cspell-extra-dict/cspell.json tests/fixtures/cspell-extra-dict/amostra.md` must fail, because `@cspell/dict-pt-pt` is in no manifest. After `npm install --no-save @cspell/dict-pt-pt@3.0.6` it must pass. Restore the tree afterwards.
3. Run all ten scheduling scenarios: `node tests/fixtures/generate-text-lint-scheduling.mjs <scenario>` for each name in the generator's `scenarios` object, confirming none throws `Unhandled condition input`.
4. Plant the defect the jobs exist to catch. On the pushed branch, temporarily blank `extra-cspell-packages` on `text-extra-dicts` and confirm the job goes red where it previously stayed green. This is the assertion issue #105 asks for, so it is worth demonstrating once rather than assuming. Revert before the pull request is ready for review.
5. Branch CI green across `text`, `text-extra-dicts`, `text-extra-dicts-consumer`, `text-lint-scheduling` and the `install-cspell-dictionaries` matrix.
