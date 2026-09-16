# Branch Review: fix/112-run-all-enabled-text-linters

Base: `origin/main` (merge base: `79b5f39`)
Commits reviewed: 12, plus the source-build isolation follow-up
Files changed: 20 (6 added, 14 modified, 0 deleted, 0 renamed)
Reviewed through: `32dcd59` and the isolation follow-up working tree

## Summary

Every enabled text linter reports findings after an earlier linter fails, provided setup succeeds and the run is not cancelled. The branch also contains an explicitly authorized Linux arm64 Scrut source-build repair, introduced after CI exposed an incorrectly packaged upstream executable. Issue [#120](https://github.com/cboone/gh-actions/issues/120) tracks the broader packaging investigation.

## Changes by Area

- **Text lint execution:** yamllint setup precedes all checks. Readiness and cancellation-aware conditions allow later enabled checks to execute after a lint failure while preserving job failure.
- **Scheduling coverage:** ten runner-executed composite fixtures copy production conditions and assert readiness, tool outcomes and the composite action's final outcome. The fixture omits the unsupported `failure()` expression in composite step environment values.
- **Scrut installation:** the action and standalone, Go and Zig reusable workflows build source on Linux arm64 with a pinned commit, verified archive SHA-256, Rust 1.97.1 and a committed dependency lockfile. Each workflow fetches the helper and lockfile from its own repository and commit. Other platforms retain checksum-pinned binaries.
- **Integration coverage:** `scrut-arm64` exercises the reusable workflow. The Zig formatting matrix invokes `./actions/set-up-scrut`, including on Linux arm64, and executes the installed tool. The UV-only job selects its own spec file.
- **Maintenance and documentation:** Dependabot includes the action's Rust setup pin. Component references and the development trust model document the source-build exception. The PR description includes the expanded scope and validation.

## File Inventory

Added (6):

- `actions/set-up-scrut/Cargo.lock`
- `actions/set-up-scrut/build-from-source.sh`
- `docs/plans/done/2026-09-16-run-all-enabled-text-linters.md`
- `docs/reviews/2026-09-16-fix-112-run-all-enabled-text-linters.md`
- `tests/fixtures/generate-text-lint-scheduling.mjs`
- `tests/fixtures/generate-scrut-installer.mjs`

Modified (14):

- `.github/dependabot.yml`
- `.github/workflows/lint-text.yml`
- `.github/workflows/run-ci.yml`
- `.github/workflows/run-scrut-tests.yml`
- `.github/workflows/run-go-ci.yml`
- `.github/workflows/run-zig-ci.yml`
- `CHANGELOG.md`
- `actions/set-up-scrut/README.md`
- `actions/set-up-scrut/action.yml`
- `docs/development.md`
- `docs/workflows/lint-text.md`
- `docs/workflows/run-scrut-tests.md`
- `docs/workflows/run-go-ci.md`
- `docs/workflows/run-zig-ci.md`

The earlier package manifest changes no longer differ from the synchronized base branch. This inventory includes the review document itself.

## Plan Compliance

All four text-lint plan items are implemented: setup ordering, readiness and cancellation gates, user documentation, and local validation. Suggested runner coverage is implemented and passed CI. The Scrut exception is an additional user-authorized scope item, documented in the trust model and tracked in #120.

## Code Quality Assessment

Scheduling preserves normal failure propagation. Only the outer fixture invocation allows an expected failure. Runner assertions cover success, early failure, all tool failures, setup failure, each disabled tool, all disabled tools, and yamllint alone. Cancellation and a deliberately failing reusable-workflow job are not exercised by these fixtures.

The source build verifies bytes before extraction, uses dependency checksums with `--locked`, selects the pinned compiler and native target explicitly, and builds in a fresh `/tmp` directory with an isolated Cargo home. It rejects ancestor Cargo configuration and clears Rust compiler, target and profile overrides. Helper transfers restrict initial and redirected protocols to HTTPS; missing GHES workflow-origin contexts receive a targeted error. The action has actual Linux arm64 execution coverage through the Zig formatting job. Upstream's archive build reports a timestamp instead of a release version; the helper validates that output and all four component references document the limitation.

The user authorized the additional Go/Zig installers and changelog scope. Both installers now use the same guarded source-build path; release notes describe text-lint scheduling and all four repaired Scrut installation surfaces. The new runner fixtures extract the Go/Zig workflows' actual installer steps, bind only the workflow-origin contexts to the fixture checkout's commit, and execute the installed tool on Linux arm64. They isolate installer behavior from unrelated language build/test jobs. Fresh CI and exact-head Copilot review remain required.

## Validation

At `eabe636`, every active PR CI check passed, including all ten scheduling scenarios, both Linux arm64 Scrut entry points changed here, and the other installer matrices. Two trufflehog jobs were intentionally skipped in gitleaks-only runs. Run CI evidence: [run 35115461097](https://github.com/cboone/gh-actions/actions/runs/35115461097).

The source-build helper compiled locally and its executable passed both UV integration checks. All five local repository checks, ShellCheck, shfmt and the whitespace check passed before that push. CI at the reviewed commit does not validate subsequent transport and GHES error changes; those require local validation and fresh CI after push.

## Review Resolution

- Runner scheduling coverage: implemented and passed.
- Unsupported composite `failure()` environment expression: replaced by the final action outcome assertion and passed.
- Linux arm64 action and standalone workflow installation: source-build exception implemented and passed.
- Dependabot coverage: action directory added.
- UV-only job selecting Zig specs: narrowed to its own spec and passed.
- PR description scope: expanded to include the authorized source build.
- Review metadata: refreshed against the complete synchronized diff.
- Helper HTTPS restrictions and GHES context error: implemented and passed CI at `e7fd97e`.
- Additional Go/Zig installers and changelog: authorized, implemented and passed CI at `32dcd59`.
- Cargo configuration isolation and timestamp version limitation: implemented; fresh CI pending. Go/Zig installer fixtures now supply conflicting Cargo configuration, compiler flags, wrapper and target settings to verify isolation.
