# Branch Review: fix/111-fail-trufflehog-on-findings

Base: `main` (merge base: `0d53592`)
Commits: 2
Files changed: 7 (2 added, 5 modified, 0 deleted, 0 renamed)
Reviewed through: `abeeb9a`

## Summary

This branch fixes issue #111 by making both TruffleHog entry points fail when they report findings. It preserves the existing verified/unknown result filter, explains that gate's limits, and adds a deterministic positive control that proves removing `--fail` restores the defect.

## Changes by Area

- **Scan failure behavior:** Both the composite action and reusable workflow append `--fail`. The workflow now selects its scope with a Bash array and receives the input through an environment mapping, consistent with repository conventions. Files: `actions/run-trufflehog/action.yml`, `.github/workflows/scan-for-secrets.yml`.
- **Regression coverage:** A dependency-free Python script extracts and executes the literal scan steps. A custom detector verifies synthetic data through a local HTTP server, covering both entry points and both scopes with clean scans, findings, and removal of `--fail`. CI installs pinned TruffleHog and uv before running the control. Files: `tests/trufflehog-positive-control.py`, `.github/workflows/run-ci.yml`.
- **Documentation:** Component references explain exit code 183 and the exclusion of unverified results. The completed plan records the design and validation. Files: `actions/run-trufflehog/README.md`, `docs/workflows/scan-for-secrets.md`, `docs/plans/done/2026-09-16-fail-trufflehog-on-findings.md`.

## File Inventory

Added (2):

- `docs/plans/done/2026-09-16-fail-trufflehog-on-findings.md`
- `tests/trufflehog-positive-control.py`

Modified (5):

- `.github/workflows/run-ci.yml`
- `.github/workflows/scan-for-secrets.yml`
- `actions/run-trufflehog/README.md`
- `actions/run-trufflehog/action.yml`
- `docs/workflows/scan-for-secrets.md`

No files were deleted or renamed.

## Notable Changes

Reported verified and unknown findings now fail downstream jobs instead of returning success. Unverified results remain excluded, so revoked credentials and detections without verification remain outside this gate. No public inputs, dependency manifests, or tool version defaults change. The new CI job has read-only contents permission, a timeout, and a SHA-pinned checkout action.

## Plan Compliance

**Verdict: good compliance. Overall progress: 4/4 items done (100%).**

Plan: `docs/plans/done/2026-09-16-fail-trufflehog-on-findings.md`.

1. **Done:** Add `--fail` to both entry points. Both literal scan commands include it, and the positive control confirms exit 183 for findings.
1. **Done:** Retain and explain `--results=verified,unknown`. Both commands preserve the filter; adjacent comments explain the noise policy and unknown results, and both component references document the excluded coverage.
1. **Done:** Add a deterministic positive control. Synthetic data and local verification exercise all four combinations, including clean scans and removal of the flag. Removing the marker file before history scans establishes that the finding comes from Git history.
1. **Done:** Validate the pinned version and create signed issue-referencing commits. During review, all five project checks passed and the control passed with TruffleHog 3.95.2. Both reviewed commit objects contain PGP signatures and reference #111; signature authenticity was not independently verified.

No partially completed or outstanding items were found. Moving scope selection into Bash is a reasonable approach adjustment that follows the environment-mapping convention. Adding the CI job supports the planned regression coverage. There are no problematic deviations or fidelity concerns.

Hosted CI execution remains pending: no PR or Actions run was found for this branch during review. This limitation is accurately recorded in the plan and does not invalidate the completed local checks.

## Code Quality Assessment

**Verdict: ready for merge from code review, subject to hosted CI passing. No blocking findings.**

The production change is small and preserves argument boundaries and error propagation. Documentation clearly describes the gate's coverage. The control tests actual source commands rather than copied invocations, asserts the specific findings exit code, and checks that the precise original defect is detected. Temporary fixtures, bounded subprocess calls, and server cleanup keep the test isolated from the checkout.

Review item 1 (code-change): **resolved**. The control reads the expected TruffleHog version from the action's quoted patch-version default, removing the duplicate pin. Missing or invalid defaults produce a clear assertion error. The reader remains dependency-free, consistent with the scan-step extraction.

Validation performed during review:

- `make lint`, `make lint-yaml`, `make lint-md`, `make format-check`, and `make spell`: passed.
- Positive control with TruffleHog 3.95.2 on macOS arm64: all four combinations returned 0 for clean scans and 183 for findings; removal of `--fail` was detected in every combination.
- Repository status: `cboone/gh-actions` is active and is not a fork; the checkout was clean before review.

## Review Resolution

Total items: 1. Resolved: 1. Skipped: 0.

- Item 1: derive the expected version from action metadata. Updated `tests/trufflehog-positive-control.py` and confirmed that version extraction follows a changed pin and rejects missing or invalid defaults using temporary fixtures.
- The full positive control passed again with TruffleHog 3.95.2 across both entry points and scopes, including detection of removal of `--fail`.
- Ruff lint and format checks passed for the modified Python control. Markdown lint, Prettier and spelling checks passed for this review and the modified control where applicable.
- Hosted CI confirmation remains pending and was outside this local review-resolution task.
