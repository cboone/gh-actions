# Update lean-math Preset Branch for v3 Conventions

Date: 2026-05-02

## Context

This branch (`feature/text-lint-yml-add-lean-math-preset-for-pandoc`)
landed a single commit, `a2940ec`, that adds the `lean-math` preset to
`.github/workflows/text-lint.yml` and bundles a docs/CHANGELOG/cspell
update with it. Since that commit, `main` has advanced 40+ commits with
two sweeping changes that intersect heavily with this branch:

1. **v2.2.0 (PR #49) — Action and workflow renames.** Every reusable
   workflow whose name was not already imperative was renamed:
   - `text-lint.yml` → `lint-text.yml` (the file this branch edits)
   - `install_dir` env in that workflow renamed from `text-lint-tools`
     → `lint-text-tools`
   - All `setup-*` actions → `set-up-*`, `gh-release` →
     `create-gh-release`, etc.
2. **v3.0.0 release (PR #50) — Documentation overhaul.** The README was
   rewritten as an orientation document with a Quick Reference table.
   Per-workflow reference docs (Inputs, Usage) were extracted to
   `docs/workflows/<name>.md`; per-action reference docs to
   `actions/<name>/README.md`. The README no longer carries inline
   per-component input tables. The "README is single source of truth"
   rule was explicitly retired in `.github/copilot-instructions.md`.
3. **Tag pinning.** Examples in docs now pin to `@v3.0.0` rather than
   `@v2.1.4`.
4. **Workmux ignore.** `.markdownlint-cli2.jsonc` on main now ignores
   `.workmux/`, so the local-only markdownlint failure observed during
   the original implementation is gone.
5. **`cspell.json` on main grew several words** (`binaryornot`,
   `commitish`, `elif`, `fsfe`, `markupsafe`, `nullglob`, `shopt`,
   `tomlkit`).

The branch's semantic contribution (the `preset` input plus the
`presets/lean-math/` bundle) does not need to change. Only its
attachment points need to move to fit the new layout.

## Goal

Land the same feature on top of v3.0.0, but reshaped to match the
post-v3 conventions: renamed workflow path, per-component doc layout,
v3 tag in usage examples, and a clean merge over the docs and cspell
churn that has happened since the original commit.

The original commit `a2940ec` will be replaced (rebased away). The
final commit on this branch will apply cleanly against `origin/main`,
with zero references to the pre-rename workflow path and zero edits to
the README's per-workflow input table (which no longer exists there).

## Conflict surface

Files touched by `a2940ec` and their fate after this rework:

| Path on `a2940ec`                                | Fate                                                                                              |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| `.github/workflows/text-lint.yml`                | Path no longer exists on main. Reapply the same edits to `.github/workflows/lint-text.yml`.       |
| `presets/lean-math/.markdownlint-cli2.jsonc`     | Clean add. Keep as-is.                                                                            |
| `presets/lean-math/cspell.jsonc`                 | Clean add. Keep as-is.                                                                            |
| `README.md` (preset section + table edit)        | Drop entirely. The README no longer documents per-workflow inputs. Move content to docs/workflows. |
| `CHANGELOG.md` (Unreleased entry)                | Reword and reapply under main's empty `[Unreleased]` block. Keep below the v3.0.0 / v2.2.0 lines. |
| `cspell.json` (added `presets/`, four words)     | Reapply against main's enlarged words list. Confirm `Pandoc`, `citekeys`, `zhang`, `yeung` still needed. |

New attachment points required after the move:

- `docs/workflows/lint-text.md`: extend the existing per-workflow doc
  on main to include the new `preset` input row in the Inputs table,
  add a "Preset configs" subsection (precedence rules, what
  `lean-math` contains, where the preset sources live in this repo),
  and add a second Usage example showing the academic-Markdown shape
  pinned to `@v3.0.0`.

The root README does not need a new entry. `lint-text` already has a
Quick Reference row pointing at `docs/workflows/lint-text.md`, and the
preset is an input on that workflow, not a new workflow of its own.

## Strategy

**Reset and reapply, not three-way rebase.** Three of the six touched
files (workflow YAML, README, CHANGELOG) have changed substantially on
main, including a path rename. A `git rebase origin/main` would either
auto-follow the rename (and then conflict on every line) or fail the
rename detection (and add the deleted file back). A clean redo is
faster, lower-risk, and produces a smaller commit that reads well in
isolation.

Concretely:

1. Hard-reset the branch to `origin/main`.
2. Reapply the workflow edits to the new `lint-text.yml` path,
   adjusting the comment that previously said "fetch from this repo at
   the workflow's own SHA (same supply-chain model as the npm and
   yamllint installs)" to refer to the renamed install steps if
   needed.
3. Re-add the two preset files exactly as they exist post-Prettier
   today (the format is already canonical and has been validated).
4. Add the per-workflow doc updates to `docs/workflows/lint-text.md`
   per the layout in `AGENTS.md` "Documentation layout" section.
5. Reapply the cspell.json delta on top of main's larger words list:
   add `presets/` to `ignorePaths` and add `Pandoc`, `citekeys`,
   `yeung`, `zhang` to `words` (alphabetically, preserving main's
   ordering style).
6. Add a single CHANGELOG entry under `[Unreleased]` describing the
   feature with the same substance as the previous commit's body but
   referencing the new path (`lint-text.yml`, not `text-lint.yml`).
7. Lint and validate locally.
8. Commit as a single `feat(lint-text): add lean-math preset for
   Pandoc-academic configs` commit, GPG-signed, closing #37.

## Step-by-step actions

### 1. Reset to main

```text
git fetch origin main
git reset --hard origin/main
```

This drops `a2940ec` from the branch tip; the same change set will be
re-created in step 7 against the post-v3 layout.

### 2. Reapply workflow edits to `lint-text.yml`

Edits to `.github/workflows/lint-text.yml`:

- Add a `preset` input under `workflow_call.inputs` (same description
  block as the original commit).
- Add a `Validate preset input` step before `actions/checkout`, using
  the `case "${PRESET}" in "" | lean-math) ;; *) error ;; esac`
  pattern.
- Add an `Apply preset configs` step between `setup-node` and
  `Install lint tools`. Behavior unchanged from the original commit:
  guard on `inputs.preset != ''`, fail fast if `job_workflow_sha` is
  empty, fetch
  `https://raw.githubusercontent.com/cboone/gh-actions/${REQ_SHA}/presets/${PRESET}/<file>`,
  drop into the workspace only when no local config exists for that
  tool.

The `install_dir` rename from `text-lint-tools` to `lint-text-tools`
in the existing `Install lint tools` step is already on main and does
not need to be reapplied. The `Apply preset configs` step does not
allocate an install_dir (it writes config files directly into the
checkout root), so no name change is needed.

### 3. Add the preset files

Recreate `presets/lean-math/.markdownlint-cli2.jsonc` and
`presets/lean-math/cspell.jsonc` with the exact contents from the
original commit (post-Prettier, byte-for-byte equivalent to the
configs in `cboone/zhang-yeung-inequality`). Confirm with `git show
a2940ec:presets/lean-math/.markdownlint-cli2.jsonc` and the cspell
counterpart.

### 4. Update `docs/workflows/lint-text.md`

Append a new row to the Inputs table:

```text
| `preset`           | string  | `""`        | Optional preset config bundle (see below) |
```

After the table, add a `### Preset configs` subsection explaining the
precedence rules (local config wins, else preset is fetched and
dropped in, else built-in defaults), the valid values (`""`,
`"lean-math"`), and a one-paragraph summary of what the `lean-math`
preset actually changes (markdownlint relaxations, cspell regex
ignores for LaTeX math/Pandoc citations, `project-words` dictionary
pointer at `./cspell-words.txt`). Note that preset sources live at
`presets/<name>/` in this repo, fetched at the workflow's own SHA.

Add a second Usage example below the existing one, showing the
paper-backed-Lean shape and pinned to `@v3.0.0`:

```yaml
jobs:
  text:
    uses: cboone/gh-actions/.github/workflows/lint-text.yml@v3.0.0
    with:
      run-cspell: true
      run-prettier: false
      preset: lean-math
```

### 5. Reapply cspell.json delta

Two edits, both under `git show origin/main:cspell.json`:

- `ignorePaths`: append `"presets/"` so the preset's own
  `cspell.jsonc` is not auto-discovered as a config when running
  `npx cspell .` here.
- `words`: insert `"Pandoc"`, `"citekeys"`, `"yeung"`, `"zhang"` in
  alphabetical position. Note: main's words list is already
  case-mixed (`Doptimize`, `GOPATH`, `Makefiles`, `Swatinem` appear
  alongside lowercase entries), so the four additions can keep their
  natural casing.

Verify these are still needed by running `npx cspell .` after step 6.

### 6. CHANGELOG entry

Under `[Unreleased]`, add a single bullet under a new `### Added`
heading. Substantively the same as the original commit's CHANGELOG
entry, but reworded to reference `lint-text.yml` rather than
`text-lint.yml`. Place it before the existing `[3.0.0]` block, not
inside it.

### 7. Lint and validate

```text
make lint
make lint-yaml
make format-check
make spell
make lint-md
```

`make lint-md` should now pass cleanly (main ignores `.workmux/`).

### 8. Commit

Single commit, GPG-signed:

```text
feat(lint-text): add lean-math preset for Pandoc-academic configs

Closes #37.
```

Body explains the feature, the supply-chain model (fetch from this
repo at `job_workflow_sha`), the precedence rules (local config
wins), and the byte-for-byte match against the canonical configs in
`cboone/zhang-yeung-inequality`.

### 9. Move this plan to done

After the commit lands, `git mv
docs/plans/todo/2026-05-02-update-lean-math-preset-branch-for-v3-conventions.md
docs/plans/done/` and amend (or follow-up commit, per CLAUDE.md's
"NEVER amend" rule, this becomes a follow-up commit).

## Verification

A successful execution of this plan should produce:

- A branch with one commit ahead of `origin/main`, no merge commits.
- `git diff origin/main...HEAD --stat` showing only:
  - `.github/workflows/lint-text.yml` (modified)
  - `CHANGELOG.md` (modified)
  - `cspell.json` (modified)
  - `docs/workflows/lint-text.md` (modified)
  - `presets/lean-math/.markdownlint-cli2.jsonc` (added)
  - `presets/lean-math/cspell.jsonc` (added)
  - `docs/plans/done/2026-05-02-update-lean-math-preset-branch-for-v3-conventions.md` (added; or kept in `todo/` until the follow-up commit)
- Zero references to the old `text-lint.yml` path anywhere in the
  diff.
- All `lint-text.yml` Usage examples in the diff pinned to `@v3.0.0`.
- All local lint commands clean.

## Out of scope

- Changing the preset's regex content or the markdownlint rule list.
  Both have been validated against `cboone/zhang-yeung-inequality`
  byte-for-byte and should not drift at this stage.
- Adding additional presets (e.g. a `swift-package` or `rust-cli`
  preset). The `preset` input is designed to grow, but only
  `lean-math` is in scope for #37.
- Cutting a release that includes this feature. That belongs to a
  separate PR-and-tag operation after merge.
