# Investigate Scrut installation reliability

Approved on 2026-09-16 for issue #120.

## Scope

1. Audit every published Linux and macOS architecture asset, record archive hashes, executable formats and dependencies, and exercise native assets on supported runners.
2. Inspect historical upstream release workflows to establish the extent and cause of incorrectly named architecture assets.
3. Reuse PR #119's source commit, archive checksum, Rust toolchain and reviewed Cargo.lock for Linux arm64. Extend that exception to the Go and Zig reusable workflows without importing unrelated text-lint implementation.
4. Make source-build version reporting deterministic and verify installed architecture, version and snapshot execution through all four entry points on Linux arm64.
5. Document installation choices, integrity boundaries, source-build maintenance and removal criteria. Add Unreleased notes for this exception and #112, conditioned on its implementation landing.
6. Run repository formatting, linting and relevant installation tests, retain the audit evidence and plan, and make signed Conventional Commits referencing #120.

## Integration boundary

PR #119 remains open at source head `e7fd97e9a761e00e37e5153ce61988e5db7ce93e`. Its Scrut helper and dependency lockfile are the baseline for this change. Overlapping files must be reconciled with that PR before merge; its unrelated text-lint changes are outside this implementation.

The audit found the same architecture-selection defect in macOS x86-64 assets. On 2026-09-16 the user also approved extending the pinned source-build exception to macOS x86-64.

PR #119 subsequently advanced to `3393581e4f1f588344ff3fb16e01e6a5860d1e05`, adding Go/Zig installation repairs, Cargo configuration isolation and both requested changelog entries. This implementation preserves that helper isolation. The #112 changelog entry is already implemented there and should be retained when that PR lands, rather than duplicated here.

GitHub writes target `cboone/gh-actions`. Upstream `facebookincubator/scrut` is read-only for this task.

## Validation

- Pinned npm dependencies; Markdown fix/format pass; `make lint`, `make lint-md`, `make format-check`, `make spell`, `make lint-yaml`.
- ShellCheck, shfmt and Bash syntax checks for modified installer scripts.
- Local release audit and source-build snapshot execution, with native execution boundaries recorded explicitly.
- CI native release audit and integration checks for the action and standalone, Go and Zig workflows on Linux arm64. CI results require an observed completed run.
