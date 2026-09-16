# Run all enabled text linters

Issue: [#112](https://github.com/cboone/gh-actions/issues/112)

## Problem

The tool conditions in `lint-text.yml` imply `success()`, so a failed
linter skips subsequent checks and hides their findings. The yamllint
installation also follows the npm-based checks and is skipped after
their failures.

## Approved changes

1. Move uv and yamllint installation before all linter runs.
1. Add a setup-success gate and use `!cancelled()` with each tool input
   so lint failures allow subsequent checks while setup failures and
   cancellation prevent them.
1. Document reporting and failure behavior in the workflow reference.
1. Run repository formatting, workflow, YAML, Markdown, and spelling
   checks and create signed commits referencing the issue.

## Implementation

All installation steps retain their default success gate. A final setup
step records readiness; each of the four checks requires its successful
outcome. No check uses `continue-on-error`, so findings still fail the job.

## Validation

- `make lint`, `make lint-yaml`, `make lint-md`, `make format-check`, and
  `make spell` passed. The YAML check used a temporary `UV_CACHE_DIR`
  because the default cache is outside the writable sandbox.
- `git diff --check` passed.
- GitHub runner behavior remains to be verified by an integration run.
