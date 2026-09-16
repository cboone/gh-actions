# Branch Review: fix/112-run-all-enabled-text-linters

Base: `origin/main` (merge base: `578e623b`)
Commits reviewed: 8
Files changed: 14 (5 added, 9 modified, 0 deleted, 0 renamed)
Reviewed through: `eabe636`

## Summary

Every enabled text linter reports findings after an earlier linter fails, provided setup succeeds and the run is not cancelled. The branch also contains an explicitly authorized Linux arm64 Scrut source-build repair, introduced after CI exposed an incorrectly packaged upstream executable. Issue [#120](https://github.com/cboone/gh-actions/issues/120) tracks the broader packaging investigation.

## Changes by Area

- **Text lint execution:** yamllint setup precedes all checks. Readiness and cancellation-aware conditions allow later enabled checks to execute after a lint failure while preserving job failure.
- **Scheduling coverage:** ten runner-executed composite fixtures copy production conditions and assert readiness, tool outcomes and the composite action's final outcome. The fixture omits the unsupported `failure()` expression in composite step environment values.
- **Scrut installation:** the action and standalone reusable workflow build source on Linux arm64 with a pinned commit, verified archive SHA-256, Rust 1.97.1 and a committed dependency lockfile. The workflow fetches the helper and lockfile from its own repository and commit. Other platforms retain checksum-pinned binaries.
- **Integration coverage:** `scrut-arm64` exercises the reusable workflow. The Zig formatting matrix invokes `./actions/set-up-scrut`, including on Linux arm64, and executes the installed tool. The UV-only job selects its own spec file.
- **Maintenance and documentation:** Dependabot includes the action's Rust setup pin. Component references and the development trust model document the source-build exception. The PR description includes the expanded scope and validation.

## File Inventory

Added (5):

- `actions/set-up-scrut/Cargo.lock`
- `actions/set-up-scrut/build-from-source.sh`
- `docs/plans/done/2026-09-16-run-all-enabled-text-linters.md`
- `docs/reviews/2026-09-16-fix-112-run-all-enabled-text-linters.md`
- `tests/fixtures/generate-text-lint-scheduling.mjs`

Modified (9):

- `.github/dependabot.yml`
- `.github/workflows/lint-text.yml`
- `.github/workflows/run-ci.yml`
- `.github/workflows/run-scrut-tests.yml`
- `actions/set-up-scrut/README.md`
- `actions/set-up-scrut/action.yml`
- `docs/development.md`
- `docs/workflows/lint-text.md`
- `docs/workflows/run-scrut-tests.md`

The earlier package manifest changes no longer differ from the synchronized base branch. This inventory includes the review document itself.

## Plan Compliance

All four text-lint plan items are implemented: setup ordering, readiness and cancellation gates, user documentation, and local validation. Suggested runner coverage is implemented and passed CI. The Scrut exception is an additional user-authorized scope item, documented in the trust model and tracked in #120.

## Code Quality Assessment

Scheduling preserves normal failure propagation. Only the outer fixture invocation allows an expected failure. Runner assertions cover success, early failure, all tool failures, setup failure, each disabled tool, all disabled tools, and yamllint alone. Cancellation and a deliberately failing reusable-workflow job are not exercised by these fixtures.

The source build verifies bytes before extraction, uses dependency checksums with `--locked`, selects the pinned compiler and native target explicitly, and builds outside the consumer checkout. Helper transport restrictions and the GHES context error are follow-up repairs. The action has actual Linux arm64 execution coverage through the Zig formatting job.

Outstanding requests concern changelog entries and the inline Scrut installers in `run-go-ci.yml` and `run-zig-ci.yml`, which still consume the incorrectly packaged arm64 archive. Updating those additional files requires a scope decision under the monitoring workflow. The PR is not declared ready while these findings remain pending.

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
- Helper HTTPS restrictions and GHES context error: follow-up repairs pending fresh CI.
- Additional Go/Zig installers and changelog: scope decision pending.
