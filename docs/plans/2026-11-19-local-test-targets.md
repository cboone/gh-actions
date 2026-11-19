# Local test targets

Expose existing CI test commands through the Makefile without changing their
assertions, runner matrices, setup steps or action pins. Issue:
[cboone/gh-actions#138](https://github.com/cboone/gh-actions/issues/138).

## Basis and scope

The first check confirmed that main has no test targets and no overlapping PR.
The sibling agent-harness-plugins Makefile supplies the useful precedent:
central fixture bindings and aggregate targets. Extend this repository's
Makefile rather than introduce a runner or dependency manager.

TOOLING relayed approval from the Overnight worker setup Inbox answer at
11:04 PM EST on November 18: install locked dependencies and repository-owned,
pinned, checksum-verified tools inside the worktree. Global installation stays
outside scope. The initial dependency stop is resolved by that answer.

## Implementation

- Add individual targets for existing Scrut, Python and Node checks, plus
  `test-scrut`, `test-python`, `test`, and `test-all` aggregates.
- Bind Scrut fixtures centrally with absolute paths; allow executable overrides.
- Replace direct CI test commands with the matching targets. Keep GitHub Actions
  integration and installer fixtures, runner matrices and setup steps intact.
- Expose binary-download tests and the release audit separately from default
  tests, retaining CI's cache and artifact paths.
- Document prerequisites, local commands, network targets and CI-only coverage.
  Do not broaden `setup` or change any pins.

## Validation and completion

Run the existing suites through their targets and verify failure propagation
with checked plants. Complete the full structural, focused and trim review
order, lint-and-fix without push, and exact-tree signed-commit tidy. Persist
review counts and evidence in the review ledger. Open a ready PR and report to
TOOLING; never merge.
