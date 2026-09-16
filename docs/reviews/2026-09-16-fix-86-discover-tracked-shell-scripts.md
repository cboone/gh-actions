# Branch Review: fix/86-discover-tracked-shell-scripts

Base: `main` (merge base: `129cb373`)
Commits: 3
Files changed: 5 (2 added, 3 modified, 0 deleted, 0 renamed)
Reviewed through: `701a57e`

## Summary

The branch fixes shell discovery so extension-less scripts anywhere in the tracked tree receive ShellCheck and shfmt checks. It preserves unusual filenames through a NUL-separated manifest and makes an empty discovered set visible through a notice and job summary. Regression coverage executes the workflow's actual discovery and checker blocks.

## Changes by Area

- **Shell discovery and execution:** `.github/workflows/lint-shell.yml` installs pinned shfmt whenever either checker is enabled, discovers regular files from the Git index with `shfmt -f`, and passes the original paths safely to both checkers. Discovery failures propagate, submodule directories are excluded, and the format check retains EditorConfig settings.
- **Regression coverage and CI:** `tests/check-shell-discovery.py` exercises temporary Git indexes and real checker failures. `.github/workflows/run-ci.yml` runs it in the existing Linux amd64, Linux arm64, and macOS arm64 installer matrix and adds a ShellCheck-only workflow invocation.
- **Documentation:** `docs/workflows/lint-shell.md` explains tracked discovery, empty-set signaling, EditorConfig behavior, and installation when formatting is disabled. `docs/plans/done/2026-09-16-discover-tracked-shell-scripts.md` retains the approved scope and validation results.

## File Inventory

### New files (2)

- `docs/plans/done/2026-09-16-discover-tracked-shell-scripts.md`
- `tests/check-shell-discovery.py`

### Modified files (3)

- `.github/workflows/lint-shell.yml`
- `.github/workflows/run-ci.yml`
- `docs/workflows/lint-shell.md`

No files were deleted or renamed.

## Notable Changes

ShellCheck-only consumers now require the pinned shfmt installation because discovery depends on it. Repositories without shell scripts also fetch the installer and shfmt when either checker is enabled; disabling both skips these steps. These behavior changes are documented. Dependency versions, checksum defaults, permissions, and external action pins are unchanged.

## Plan Compliance

**Verdict: Good compliance. All 6/6 approved items are done (100%).**

Plan: [Discover tracked shell scripts](../plans/done/2026-09-16-discover-tracked-shell-scripts.md).

1. **Done: Install pinned shfmt before discovery.** Installation and discovery share the condition that either checker is enabled, including ShellCheck-only runs.
1. **Done: Discover tracked scripts while preserving spaces.** `git ls-files -z`, quoted per-file discovery, and NUL-separated checker input preserve spaces, newlines, and leading dashes. Tests cover nested extension-less scripts, ordinary extensions, non-shell and untracked files, and submodule contents.
1. **Done: Report an empty discovered set.** Discovery emits a notice and writes the job summary before both checker steps are skipped. Tests cover empty and non-shell-only indexes and distinguish Git failures from an empty set.
1. **Done: Preserve EditorConfig.** The format check introduces no style flags. Its explanatory comment and regression test verify that two-space EditorConfig indentation is accepted and four-space indentation is rejected.
1. **Done: Update documentation and add regression coverage.** The workflow reference describes the resulting behavior, and the new test executes the actual shell blocks rather than a separate discovery implementation. CI includes the three-runner test and ShellCheck-only invocation.
1. **Done: Validate and create signed issue-referencing commits.** Relevant local checks pass. All three commits contain GPG signature blocks and use Conventional Commits subjects referencing issue #86. Signature validity was not independently verified.

**Deviations:** The implementation uses per-file `shfmt -f` rather than batching with `-f=0`. This is a justified, documented adjustment for the pinned release's handling of explicitly supplied non-shell files. The extra filename, submodule, and Git-failure cases extend validation within the approved scope. No problematic omissions or ordering violations were found.

**Fidelity:** The implementation meets the plan's intent, including checker execution and failure-path coverage. Hosted GitHub Actions execution is still unverified; no PR exists for this branch at review time.

## Code Quality Assessment

**Verdict: Ready for PR review, with no blocking code findings. Merge readiness remains subject to hosted CI results.**

The discovery loop is readable and preserves filenames without round-tripping through newline-separated action outputs. Tool failures propagate instead of reporting an empty set, checker arguments include `--`, and checker execution retains the existing input conditions. Documentation explains the new shfmt dependency and Git-index requirement accurately.

The regression test is strong: it checks exact manifest membership, excludes untracked content, exercises empty indexes and Git failures, and confirms that both linters report actual defects before accepting corrected fixtures. Extracting the actual workflow run blocks keeps these checks tied to production behavior. The extractor intentionally depends on the current YAML indentation and literal block structure, so structural workflow changes may require test updates.

**Issues to address:** None identified.

**Validation performed during review:**

- Regression test passed locally on macOS arm64 with shfmt 3.13.1 and ShellCheck 0.11.0. The shfmt binary's SHA-256 matched the committed platform checksum.
- The same regression test also passed with the locally installed shfmt 3.14.1.
- `make lint`, `make lint-yaml`, `make lint-md`, `make format-check`, and `make spell` passed.
- Review covered the full branch diff, commit messages, matched plan, issue #86, surrounding CI steps, repository guidance, and component documentation.

**Remaining validation:** Confirm the hosted reusable-workflow jobs and all three regression-test matrix entries pass after publication. Local execution validates shell behavior but does not exercise GitHub expressions, installer fetching, or the other runner platforms.
