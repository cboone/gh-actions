# Branch Review: fix/112-run-all-enabled-text-linters

Base: `origin/main` (merge base: `129cb373`)
Commits: 2
Files changed: 3 (1 added, 2 modified, 0 deleted, 0 renamed)
Reviewed through: `905694f`

## Summary

This branch lets every enabled text linter report findings after an earlier linter fails. It moves yamllint setup before the checks and adds a shared readiness gate, preserving setup-failure handling, cancellation handling, and a failing job result when any linter fails.

## Changes by Area

- **Workflow execution:** `.github/workflows/lint-text.yml` moves uv and yamllint installation ahead of all checks. A default-success readiness step separates setup from execution; each linter requires readiness, its enabled input, and an uncancelled run.
- **Documentation:** `docs/workflows/lint-text.md` explains reporting and failure behavior. `docs/plans/done/2026-09-16-run-all-enabled-text-linters.md` records the approved approach and local validation.

## File Inventory

- **Added (1):** `docs/plans/done/2026-09-16-run-all-enabled-text-linters.md`
- **Modified (2):** `.github/workflows/lint-text.yml`, `docs/workflows/lint-text.md`
- **Deleted (0), renamed (0).**

## Notable Changes

Step scheduling changes for all four linters. No inputs, defaults, dependency versions, permissions, download verification, or action pins change. The checks retain normal failure propagation through the absence of `continue-on-error`.

## Plan Compliance

**Verdict: Good compliance. All 4/4 approved items are done (100%).**

Plan: `docs/plans/done/2026-09-16-run-all-enabled-text-linters.md`.

1. **Done:** uv and hash-pinned yamllint installation now precede every linter run.
1. **Done:** `Lint tools ready` retains the implicit success gate. All four linter conditions require its successful outcome and combine `!cancelled()` with the corresponding boolean input. Disabled setup steps do not prevent readiness, while a failed setup step does.
1. **Done:** The workflow reference describes continued reporting, job failure, setup failure, and cancellation.
1. **Done:** `make lint`, `make lint-yaml`, `make lint-md`, `make format-check`, and `make spell` passed during this review. `git diff --check` also passed. Both branch commits contain GPG signature headers and reference issue #112; local signature trust was not independently established.

There are no partially completed or pending approved items, scope additions, approach deviations, ordering violations, or fidelity concerns. The plan explicitly records runner integration validation as outstanding; local checks do not establish that runtime behavior.

## Code Quality Assessment

**Verdict: Ready to merge from code review, with runner integration validation outstanding. No blocking findings.**

The change is focused and readable. The readiness step provides one shared setup boundary without repeating every installer condition. Including a status function removes the implicit success restriction from subsequent checks, while the readiness outcome prevents execution after setup failure. This matches [GitHub's documented status-check semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/expressions#status-check-functions). The repeated conditions make each tool's scheduling explicit and are appropriate for four steps.

Normal step failure propagation preserves the job's failure result even if subsequent checks succeed. The boolean inputs still disable their respective checks, and cancellation prevents subsequent checks. No new shell input interpolation, security issue, unfinished implementation, or unrelated refactor is visible in the diff.

**Optional suggestion:** Add runner integration coverage for an early lint failure followed by later checks, a setup failure followed by skipped checks, and disabled-tool behavior. No test coverage was added on this branch, and `gh run list` returned no runs for it. Static checks validate syntax and repository consistency but cannot demonstrate the failure-path scheduling on GitHub's runner.

## Validation

All five repository checks and the branch whitespace check passed. Repository metadata identifies `cboone/gh-actions` as active and not a fork. The working tree was clean before saving this review. This assessment covers the complete three-file branch diff through `905694f`; the review document itself is outside that comparison.

## Review Resolution

- [x] **Item 1, code change:** Add runner integration coverage for continued linting after a lint failure, skipped checks after setup failure, and disabled tools. Implemented in `0ca6408` (`test: cover text linter failure scheduling (#112)`).

`run-ci.yml` now includes ten scheduling scenarios: all checks succeed, the first check fails, all checks fail, yamllint setup fails, each individual tool is disabled, all tools are disabled, and only yamllint is enabled. `tests/fixtures/generate-text-lint-scheduling.mjs` generates composite fixtures from the production workflow's step order and conditions, replacing setup and tool commands with controlled exit codes and binding input references to boolean literals. Expected outcomes are specified separately.

Each scenario asserts readiness and linter step outcomes, accumulated failure status, and the composite action's final outcome. Only the outer test invocation uses `continue-on-error`; production conditions and inner failure propagation are preserved. This tests runner scheduling through a composite action rather than deliberately failing the entire CI job. The existing `text` job remains the integration check for real tool installations and successful lint execution. Cancellation and a deliberately failing reusable-workflow job are not exercised by these fixtures.

The generator declares `yaml` 2.9.0 as an exact development dependency with lockfile integrity. That version already existed in the dependency tree; no package versions changed.

**Validation:** A fresh `npm ci` passed. All ten fixtures generated successfully and their shell commands passed `bash -n`. `make lint`, `make lint-yaml`, `make lint-md`, `make format-check`, and `make spell` passed. npm used a temporary cache because the default cache is outside the writable sandbox.

**Runner status:** Coverage is implemented, but the new runner assertions have not executed. There is no pull request or Actions run for this branch. They will run on the next pull-request CI run or after a push to `main` under the existing workflow triggers.

**Resolution summary:** 1 item resolved, 0 skipped. Runner execution remains pending.
