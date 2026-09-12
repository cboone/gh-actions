# Branch Review: feature/87-extract-the-pinned-tool-install-into-one-composite

Base: main (merge base: 17f94b0)
Commits: 7
Files changed: 20 (4 added, 16 modified, 0 deleted, 0 renamed)
Reviewed through: 56b2b51
Review fixes: f597a95, c72455a, 25fab8e

## Summary

The branch extracts the pinned release-binary installer that four places in
the repository hand-rolled into one script, `actions/install-pinned-tool/install-pinned-tool.sh`,
and a composite action around it, so other repositories can install any
pinned, SHA-256-verified release binary with one `uses:`. `set-up-actionlint`
and `set-up-shfmt` now run the script through `github.action_path`, and
`lint-shell.yml` and `lint-github-actions.yml` fetch it at their own commit
through the `job` context. shfmt version overrides work for the first time,
paired with committed checksums, and CI exercises the action on three runner
types.

## Changes by Area

### Installer action

A bash 3.2 compatible script configured entirely by environment variables:
URL templates over `{version}`, `{os}` and `{arch}` whose platform tokens can
be renamed, exactly one checksum source (single digest, per-asset table, or
upstream checksum file), resolve-then-download-then-verify, single-member tar
extraction, and `::error::` annotations with distinct exit codes. The
composite action maps nine inputs onto those variables and exposes
`install-dir`.

- `actions/install-pinned-tool/install-pinned-tool.sh`
- `actions/install-pinned-tool/action.yml`
- `actions/install-pinned-tool/README.md`

### Composite action wrappers

Both wrappers keep their inputs and defaults and run the sibling script, with
unused installer variables set empty so a caller's job-level `env` cannot
reach it. `set-up-shfmt` gains a `checksums` input and drops its version gate.

- `actions/set-up-actionlint/action.yml`, `actions/set-up-actionlint/README.md`
- `actions/set-up-shfmt/action.yml`, `actions/set-up-shfmt/README.md`

### Reusable workflows

Each gains a `Fetch install-pinned-tool` step (job-context guard naming a
GitHub Enterprise Server workaround, retried `curl` into `RUNNER_TEMP`) and an
`env:`-only install step. `lint-shell.yml` gains `shfmt-checksums`.

- `.github/workflows/lint-shell.yml`
- `.github/workflows/lint-github-actions.yml`
- `.github/actionlint.yaml` (comment only)

### CI self-hosting

A matrix job runs the action on `ubuntu-latest`, `ubuntu-24.04-arm` and
`macos-latest`: four direct installs covering each checksum source and
archive shape, the two wrappers after clearing the direct installs, and four
rejection cases that run the script under `/bin/bash` and assert each exit
code and message. A new `shell` job self-hosts `lint-shell.yml`.

- `.github/workflows/run-ci.yml`

### Documentation

- `README.md`: Quick Reference row and trust-model sentence.
- `CHANGELOG.md`: Added and Changed entries under `[Unreleased]`.
- `docs/workflows/lint-shell.md`, `docs/workflows/lint-github-actions.md`:
  new input, install mechanism, and limitations.
- `AGENTS.md`: structure, reusable-workflow model, naming, checksum
  locations, new-action and new-workflow procedures, testing, shell
  conventions.
- `.github/copilot-instructions.md`: the fetch model and its two rejected
  alternatives, shfmt checksum locations, the `REQ_REPO` / `REQ_SHA`
  bindings, the bash 3.2 constraint, literal `checksums` keys.

### Tooling metadata and planning

- `cspell.json`: `bsdtar`, `fosforo`, `tolower`.
- `scripts/check-tool-versions.py`: the shfmt note names both checksum
  defaults.
- `docs/plans/done/2026-09-11-extract-pinned-tool-install-action.md`: the plan.

## File Inventory

**Added (4):**

- `actions/install-pinned-tool/README.md`
- `actions/install-pinned-tool/action.yml`
- `actions/install-pinned-tool/install-pinned-tool.sh`
- `docs/plans/done/2026-09-11-extract-pinned-tool-install-action.md`

**Modified (16):** `.github/actionlint.yaml`, `.github/copilot-instructions.md`,
`.github/workflows/lint-github-actions.yml`, `.github/workflows/lint-shell.yml`,
`.github/workflows/run-ci.yml`, `AGENTS.md`, `CHANGELOG.md`, `README.md`,
`actions/set-up-actionlint/README.md`, `actions/set-up-actionlint/action.yml`,
`actions/set-up-shfmt/README.md`, `actions/set-up-shfmt/action.yml`,
`cspell.json`, `docs/workflows/lint-github-actions.md`,
`docs/workflows/lint-shell.md`, `scripts/check-tool-versions.py`

**Deleted (0), renamed (0).**

## Notable Changes

- **New public API.** `actions/install-pinned-tool`, plus `shfmt-checksums` on
  `lint-shell.yml` and `checksums` on `set-up-shfmt`. All additive.
- **Supply chain.** Two reusable workflows now execute a script fetched from
  `raw.githubusercontent.com` at `job.workflow_sha`. Integrity is bound to the
  commit SHA, the same trust `lint-text.yml` already places in its manifests;
  no new `uses:` references and no dependency changes.
- **Compatibility.** `lint-shell.yml` and `lint-github-actions.yml` now depend
  on the `job.workflow_*` properties, so on GitHub Enterprise Server the first
  needs `run-shfmt: false` and the second is unsupported, and a private fork
  cannot serve the script. Recorded under Changed in `CHANGELOG.md`; worth
  weighing when choosing the release's version bump.
- **CI.** Adds macOS and Linux ARM runners to `run-ci.yml`. The rejection
  cases run the installer directly and capture its output, so the expected
  failures raise no annotations on the PR.

## Plan Compliance

Plan: `docs/plans/done/2026-09-11-extract-pinned-tool-install-action.md`

**Verdict: good compliance.** Every planned change is implemented as designed,
and every local verification step was run. The only items outstanding are
the three CI verification steps, which cannot run until the PR exists.

**Overall progress: 11/14 items done (79%).**

### Done

1. **`install-pinned-tool.sh`.** All eight behaviors: validation, platform
   detection with checked renames, placeholder rendering with a leftover-brace
   error and unrendered `checksums`, digest resolution before download with
   the specified lookup rules, file download with retries into a `mktemp -d`
   staging directory, `sha256sum` / `shasum` verification, single-member
   extraction with a named missing-member error, and `GITHUB_PATH` /
   `GITHUB_OUTPUT` publication with cleanup. Caveat: bash 3.2 compatibility
   needed a fix found in local testing (see Deviations).
1. **`action.yml`.** Nine inputs mapped through `github.action_path`;
   `install-dir` output; no defaults for the three required inputs.
1. **Wrappers.** `set-up-actionlint` unchanged in behavior; `set-up-shfmt`
   `checksums` input with the v3.13.1 default and no version gate; version
   prints moved to their own steps.
1. **Reusable workflows.** Fetch steps with the job-context guard, the
   `Fetching from` log line and retries; `shfmt-checksums`; the fetch carries
   the shfmt install's `if:`.
1. **`run-ci.yml`.** Matrix job with the planned installs and assertions, plus
   the planned negative cases asserted by exit code and message (see
   Deviations); `shell` job.
1. **Documentation.** Every listed file, including all Copilot and `AGENTS.md`
   sub-items, the `actionlint.yaml` comment and the `check-tool-versions.py`
   note.
1. **Local verification 1.** ShellCheck and `shfmt -d` on both scripts,
   including shfmt 3.13.1 installed by the script itself; additionally
   ShellCheck 0.9.0, the runner image's version.
1. **Local verification 2.** 31 cases under `/bin/bash` 3.2 with bsdtar and
   bash 5.3 with GNU tar, covering shfmt, actionlint, uv, shellcheck and
   typos.
1. **Local verification 3.** All nine planned negative cases plus uppercase,
   binary-marker, CRLF, conflicting-entry, unsafe-version, download-failure and
   missing-runner-variable cases.
1. **Local verification 4.** Prettier, markdownlint, cspell, actionlint and
   yamllint across the repository.
1. **Commits.** Seven Conventional Commits in the planned order, each linted
   before it landed.

### Not started

1. **CI verification 1.** `install-pinned-tool` green on all three runners.
1. **CI verification 2.** `actionlint` and `shell` jobs green with the
   `Fetching from` line in their logs.
1. **CI verification 3.** `text` green.

### Deviations

- **`"$@"` instead of the style guide's `"${@}"`** (approach). bash 3.2 treats
  an empty `"${@}"` as unbound under `set -u`, which failed all 31 local cases.
  Reasonable and documented in the script header, `AGENTS.md` and the Copilot
  instructions; filed upstream as cboone/agent-harness-plugins#390.
- **Distinct exit codes** (64, 65, 66, 69, 71) (addition). Not in the plan;
  follows the Bash style guide's request for distinct, documented codes.
  Reasonable.
- **Asset-name and `checksums-url-template` validation** (addition). Hardening
  beyond the plan's validation list. Reasonable.
- **Wrappers blank unused installer variables** (addition). Composite actions
  inherit the caller's job `env`, so a stray `CHECKSUMS` or `OS_NAMES` would
  otherwise reach the script. Justified.
- **CI clears the direct installs before the wrapper checks** (addition).
  Without it the wrapper assertions would pass on binaries the earlier steps
  left behind. Justified.
- **Extra `AGENTS.md` hygiene** (addition). Testing and Shell Conventions
  notes, and a stale `run-ci.yml` line in the structure listing corrected.
  Reasonable.
- **Rejection tests run the script directly** (approach, after review). The
  plan specified `continue-on-error` composite steps and an outcome check;
  c72455a replaced them with direct `/bin/bash` runs that assert each exit
  code and message, added a plain-http case, and added a `shfmt-single`
  install for the single `checksum` input. That proves why each case fails,
  covers bash 3.2 on macOS, and raises no annotations. An improvement on the
  plan.
- **Commit 1 carried two cspell words** (ordering). The plan put words with
  commit 2, but the plan itself used `bsdtar` and `fosforo`. Harmless.
- **The `install-pinned-tool` README intro grew across commits 2, 4 and 5**
  (ordering), so each commit's docs describe only what exists at that commit.
  Consistent with the plan's "each green on its own".

### Fidelity concerns

- The design relies on `job.workflow_sha` being populated for a
  `./`-referenced reusable workflow on `pull_request`. #83's `text` job
  established that, but the PR's `actionlint` and `shell` jobs are the first
  run of the pattern for these two workflows.
- Out-of-scope items were not dropped: the remaining inline installers are
  cboone/gh-actions#92, and the cspell dot-path gap found during verification
  is cboone/gh-actions#93.

## Code Quality Assessment

An independent reviewer read the full diff without this branch's context and
exercised the installer under bash 3.2 and 5.3, with bsdtar and GNU tar, on
top of the author's own local suite.

### Verdict

**Ready to merge.** Nothing blocking was found: every bad input tried fails
closed with its documented exit code, and no path installs an unverified
binary. The findings that warranted changes are fixed in f597a95, c72455a and
25fab8e. The remaining risk is that CI has not yet run the matrix job or the
fetch steps on real runners.

### Strengths

- **Fails closed throughout.** The expected digest is resolved and checked as
  64 hex characters before the download; the comparison is a quoted literal;
  the installed file is the verified download or a member extracted from it;
  the staging directory is removed by an EXIT trap that does not fire early
  inside command substitutions.
- **Inputs never reach shell unquoted.** Everything arrives through `env:`;
  tool, version, platform-token and asset names are pattern-checked, which
  keeps `&` and `\` out of bash substitutions; archive members cannot be
  absolute or contain `..`.
- **Literal checksum keys.** A version bumped without its checksums fails with
  `No checksum entry for <asset>` rather than a generic mismatch.
- **One table, four copies, all correct.** The shfmt v3.13.1 lines are
  identical everywhere they appear and match the upstream release digests.
- **No env leakage.** The composite actions blank the installer variables they
  do not use; reusable workflows cannot receive a caller's `env`.

### Findings

| #   | Severity     | Finding                                                                                                           | Resolution                                                                                                                                 |
| --- | ------------ | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Non-blocking | `curl --location` followed redirects to plain http, so the README's https-only claim did not hold                 | Fixed in f597a95: `--proto '=https'` in `download()` and both fetch steps; a redirect to http now exits 69, verified locally               |
| 2   | Non-blocking | GNU tar needs `archive-member` spelled exactly as the archive lists it, while bsdtar ignores a leading `./`       | Fixed in f597a95: documented in the README and the input description, and the missing-member error states the rule                         |
| 3   | Non-blocking | The CI rejection steps asserted only that each step failed, and no success case used the single `checksum` input  | Fixed in c72455a: rejections run the script under `/bin/bash` and assert exit code and message; a `shfmt-single` install covers `checksum` |
| 4   | Nit          | Nothing said the installer path must stay in `env:`, where the runner translates host paths for `container:` jobs | Fixed in 25fab8e: comments in the three actions, `AGENTS.md`, and a Copilot instruction                                                    |
| 5   | Nit          | bash 3.2 was not exercised in CI                                                                                  | Fixed in c72455a: the rejection cases run under macOS's `/bin/bash`, which is 3.2                                                          |

### Remaining

- **First CI run.** The three-runner matrix, the `actionlint` and `shell` jobs'
  fetch at the PR's own commit, and ShellCheck from the runner image all run
  for the first time on the PR. ShellCheck 0.9.0, the image's version, passes
  both scripts locally.
- **Retry on a refused redirect.** `--retry-all-errors` retries an http
  redirect that `--proto` refuses before failing. It still fails closed; not
  worth special-casing.
- **Local test driver.** The 31-case suite used during development lives in
  the session scratchpad and is not committed; the CI matrix job is the
  committed test.
- **Pre-existing, tracked separately.** cspell never checks dot-paths
  (cboone/gh-actions#93); the remaining inline installers are
  cboone/gh-actions#92.
