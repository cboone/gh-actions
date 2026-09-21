# Install uv through install-pinned-tool

Issue: [#102](https://github.com/cboone/gh-actions/issues/102)

## Context

[#87](https://github.com/cboone/gh-actions/issues/87) extracted the pinned-tool install into `actions/install-pinned-tool`, and [#82](https://github.com/cboone/gh-actions/issues/82) routed `run-scrut-tests.yml`'s uv install through it. Three hand-rolled uv installers predate that work and remain:

| Location                                          | Platforms    | Lines |
| ------------------------------------------------- | ------------ | ----- |
| `.github/workflows/lint-text.yml:350-370`         | Linux x86_64 | ~20   |
| `.github/workflows/check-tool-versions.yml:31-49` | Linux x86_64 | ~18   |
| `actions/run-reuse/action.yml:25-78`              | all four     | ~53   |

All three verify their download, so none is unsafe. The cost is that the install procedure has to be changed in four places, and two of them silently only work on Linux amd64.

Beyond the issue's stated scope, the seven-line uv recipe (`tool`, `version`, `url-template`, `checksums-url-template`, `os-names`, `arch-names`, `archive-member`) is repeated nine times across the repository. This change adds `actions/set-up-uv` so the action-side and in-repo-workflow callers depend on one thing, and gives external consumers a standalone action alongside `set-up-scrut`, `set-up-shfmt` and `set-up-shellcheck`.

The intended outcome: no hand-rolled uv installer anywhere, the recipe stated in as few places as the runner permits, and every refactored path exercised by CI.

## Decisions

Taken with the user before planning:

1. `check-tool-versions.yml` reaches the installer by `./` path, not by the fetch-from-`job.workflow_repository` pattern the issue prescribes.
2. `actions/set-up-uv` lands in this change rather than a follow-up.
3. `run-reuse` gets a fixture-based `reuse lint` self-test.

## Constraints that change the issue's prescription

Two mechanical facts override what the issue body and the chosen options describe. Both are stated here so the divergence is deliberate and reviewable.

**A. A composite action cannot reference a sibling action by `./` path.** The path resolves against the caller's workspace, not the gh-actions checkout. The repository states this at `actions/run-cspell/action.yml:71` and `docs/development.md:11-13`. Consequences:

- The issue's `- uses: ./../install-pinned-tool` snippet is not implementable. `run-reuse` instead binds `${{ github.action_path }}/../install-pinned-tool/install-pinned-tool.sh` to an `INSTALLER` variable in `env:` and runs it, exactly as `set-up-shfmt`, `set-up-actionlint` and `set-up-shellcheck` do.
- `run-reuse` cannot delegate to `set-up-uv` either. It carries the uv recipe itself. `set-up-uv` therefore reduces the recipe's copies rather than eliminating them.

**B. One of `run-ci.yml`'s five uv installs is the self-test of the uv recipe, not a consumer of it.** The block at `run-ci.yml:552-562` carries `id: uv`, is titled "target triples, nested member, per-asset `.sha256`", and its `install-dir` output is asserted at `:596-600`. Converting it to `set-up-uv` would delete the coverage that proves `install-pinned-tool` handles uv's packaging. It stays as an `install-pinned-tool` call. The other four convert.

Recipe copies, before and after:

| File                      | Before                  | After                           |
| ------------------------- | ----------------------- | ------------------------------- |
| `actions/set-up-uv`       | none                    | 1 (new, canonical)              |
| `actions/run-reuse`       | 1 hand-rolled installer | 1 recipe                        |
| `lint-text.yml`           | 1 hand-rolled installer | 1 recipe (reusable workflow)    |
| `check-tool-versions.yml` | 1 hand-rolled installer | 0 (`uses: ./actions/set-up-uv`) |
| `run-scrut-tests.yml`     | 1 recipe                | 1 recipe (reusable workflow)    |
| `run-ci.yml`              | 5 recipes               | 1 recipe (the self-test)        |

Nine copies and three hand-rolled installers become five copies and none.

## Changes

### 1. New `actions/set-up-uv`

`action.yml` modeled on `actions/set-up-actionlint/action.yml`, which shares uv's shape (upstream checksum file, nested archive member). One input, `version`, defaulting to `"0.12.17"`. All nine installer variables listed, with the unused ones set to `""` per the caller-environment-leakage rule in `actions/AGENTS.md`. `INSTALLER` bound in `env:` for container-path translation. A trailing `Report uv version` step, matching every other `set-up-*` action.

```yaml
INSTALLER: ${{ github.action_path }}/../install-pinned-tool/install-pinned-tool.sh
TOOL: uv
VERSION: ${{ inputs.version }}
URL_TEMPLATE: https://github.com/astral-sh/uv/releases/download/{version}/uv-{arch}-{os}.tar.gz
CHECKSUM: ""
CHECKSUMS: ""
CHECKSUMS_URL_TEMPLATE: https://github.com/astral-sh/uv/releases/download/{version}/uv-{arch}-{os}.tar.gz.sha256
ARCHIVE_MEMBER: uv-{arch}-{os}/uv
OS_NAMES: linux=unknown-linux-gnu darwin=apple-darwin
ARCH_NAMES: amd64=x86_64 arm64=aarch64
```

`README.md` from the [per-component template](../development.md#per-component-doc-template), plus a Quick Reference row in the root `README.md` under Repository chores, both required by `actions/AGENTS.md`.

### 2. `actions/run-reuse/action.yml`

Replace the `uname` target-triple case and its curl/verify/extract block with the `INSTALLER` binding above, substituting `VERSION: ${{ inputs.uv-version }}`. Keep the `uv-version` input and its `0.12.17` default unchanged; `docs/migrations/v4.md:198` documents it and no interface changes. The old step ended with `"${install_dir}/uv" --version`, so preserve that signal as a separate `Report uv version` step rather than dropping it.

The two following steps (`Install reuse with hash-pinned requirements`, `Run reuse`) are untouched. `install-pinned-tool.sh` installs into `${RUNNER_TEMP}/uv-bin`, the same directory the hand-rolled code used, so nothing downstream moves.

### 3. `.github/workflows/check-tool-versions.yml`

Replace the install step with `uses: ./actions/set-up-uv` and drop `UV_VERSION` from the job `env:`. This workflow is not reusable (`on: schedule` plus `workflow_dispatch`, no `workflow_call`) and already runs `actions/checkout` at `:30`, so the `./`-path objection that forces the fetch pattern elsewhere does not apply. It gains no dependence on the `job` context and no GitHub Enterprise Server caveat.

### 4. `.github/workflows/lint-text.yml`

This one is a reusable workflow, so it fetches the script. Add a `Fetch install-pinned-tool` step gated on `inputs.run-yamllint`, modeled on `run-scrut-tests.yml:76-96`, with the GHES guard message pointing at `run-yamllint: false` (the wording `lint-text.yml:378-385` already uses for its yamllint manifest). Replace the install step with the env-driven `run: bash "${RUNNER_TEMP}/install-pinned-tool.sh"`.

Keep the workflow-level `UV_VERSION: 0.12.17` and bind `VERSION: ${{ env.UV_VERSION }}`, so the file keeps one pin site. Unused installer variables are not set to `""` here: reusable workflows do not inherit caller `env`, which is why `run-scrut-tests.yml` omits them too.

Both steps must stay above `Lint tools ready` (`:403-407`), the gate the linters depend on. The job has no `defaults: run: shell:`, so neither step needs a `shell:` key.

### 5. `.github/workflows/run-ci.yml`

- Convert the four consumer uv installs (`:67-76`, `:266-275`, `:319-328`, `:1230-1239`) to `uses: ./actions/set-up-uv`.
- Leave `:552-562` as an `install-pinned-tool` call, per constraint B, and leave the `uv 0.12.17 --version` and `install-dir` assertions at `:571-601` alone.
- Extend the wrapper re-test (`:603-643`) to cover `set-up-uv`: add `${RUNNER_TEMP}/uv-bin` to the teardown `rm -rf`, add a `Set up uv through the wrapper` step, and add `"uv 0.12.17 --version"` to the assertion loop. That job's matrix is Linux amd64, Linux arm64 and macOS arm64, satisfying the installer-coverage rule in `.github/workflows/AGENTS.md`.
- Add a `reuse` job: checkout, then `uses: ./actions/run-reuse` with newline-delimited `args` of `--root`, `tests/fixtures/reuse`, `lint`. Model the job comment on `trufflehog-positive-control` (`:35-79`), which is the closest existing shape (a `run-*` action exercised straight from the checkout).

The default `args: lint` path stays uncovered, because a bare invocation would lint the repository root and this repository is not REUSE-compliant. Note that in the job comment rather than leaving it implicit.

### 6. New `tests/fixtures/reuse/`

Three files: `REUSE.toml`, `LICENSES/MIT.txt` (a copy of the repository's own `LICENSE` text) and `sample.txt`. Verified locally against reuse 6.2.0, the pinned version in `requirements/reuse.txt:255`:

- `reuse --root tests/fixtures/reuse lint` exits 0 and reports `Files with copyright information: 1 / 1`.
- Run from inside a git repository whose other files are unannotated, `--root` still scopes to the fixture, so the surrounding repository does not leak into the result.
- Adding one unannotated file under the fixture turns it red: exit 1, `1 / 2`. The check can fail, so it is worth having.

The fixture is plain `.toml` and `.txt`, so Prettier, markdownlint and yamllint do not touch it. cspell scans it, and every term it contains (`SPDX`, the MIT text) already passes elsewhere in the repository.

### 7. Documentation and audit surfaces

These are load-bearing and go stale silently, so each is part of this change rather than a follow-up.

- `scripts/check-tool-versions.py:125-139`: rewrite the uv `notes` string. `UV_VERSION` disappears from `check-tool-versions.yml`, `set-up-uv`'s default appears, and `run-ci.yml` drops from five installs to one plus two wrapper assertions.
- `.github/dependabot.yml:11-19`: the comment cites `UV_VERSION: 0.12.17` as its example of an untracked version string. Checked during execution and left unchanged: `lint-text.yml` keeps its `UV_VERSION`, so the example is still accurate.
- `docs/development.md:13-22`: `lint-text.yml` now fetches the installer as well as its manifests, and `set-up-uv` and `run-reuse` join the list of actions running `../install-pinned-tool/install-pinned-tool.sh`.
- `docs/development.md:481-490`: add the new `reuse` job to the self-hosted integration-test paragraph.
- `.github/copilot-instructions.md:23`: the list of workflows that fetch the installer is already missing `run-scrut-tests.yml` and now also needs `lint-text.yml`.
- `actions/run-reuse/README.md`: update any prose describing the uv install; the `uv-version` default row is unchanged.
- `CHANGELOG.md` under `## [Unreleased]`: an Added entry for `set-up-uv` and Changed entries for the three refactors and the new `run-reuse` coverage, following the `#87` and `#85` entries at `:252-292` for tone and detail.

## Verification

Local, after the edits:

1. `make lint`, `make lint-md`, `make format-check`, `make spell`, `make lint-yaml`.
2. `uv run scripts/check-tool-versions.py` prints `All pinned tool versions are current.`
3. `uv tool run --from 'reuse[charset-normalizer]==6.2.0' reuse --no-multiprocessing --root tests/fixtures/reuse lint` exits 0.
4. Plant the defect for the new self-test: add an unannotated file under `tests/fixtures/reuse/`, confirm the lint exits 1, then remove it.
5. `grep -rn "0\.12\.17"` and confirm every surviving site is intended and every removed one is gone.

On the branch, through CI:

1. The `text` job calls `lint-text.yml` with `run-yamllint: true`, so the refactored fetch-and-install path executes.
2. The `install-pinned-tool` job covers `set-up-uv` on Linux amd64, Linux arm64 and macOS arm64, and still covers the raw uv recipe through the retained self-test.
3. The new `reuse` job covers `run-reuse` end to end: uv on `PATH`, the hash-pinned manifest resolved, and `reuse lint` actually run.
4. `gh workflow run check-tool-versions.yml` on the branch exercises the fourth path, which no push-triggered job reaches.

## Commits

Conventional Commits, each referencing `(#102)`, in an order where every commit leaves CI coherent:

1. `feat: add set-up-uv action (#102)` with its README and Quick Reference row.
2. `refactor: install uv through install-pinned-tool in run-reuse (#102)`.
3. `refactor: install uv through install-pinned-tool in lint-text and check-tool-versions (#102)`.
4. `test: cover set-up-uv and run-reuse in run-ci (#102)` with the fixture.
5. `docs: update uv install references for install-pinned-tool (#102)` covering the audit script, Dependabot comment, development reference, Copilot instructions and CHANGELOG.

Per the repository convention for `cboone` repositories, this plan file is committed and retained.
