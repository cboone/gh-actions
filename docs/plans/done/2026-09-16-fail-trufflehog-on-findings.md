# Fail TruffleHog on findings

Issue: [#111](https://github.com/cboone/gh-actions/issues/111)

## Approved plan

1. Add `--fail` to the reusable workflow and composite action.
1. Retain `--results=verified,unknown` and explain the exclusion of unverified
   results in comments and component documentation.
1. Add a deterministic positive control using synthetic data and local
   verification. Exercise the actual scan commands for working-tree and
   full-history scans, including clean scans and removal of `--fail`.
1. Run project formatting, linting and the positive control with pinned
   TruffleHog 3.95.2, then create signed commits referencing the issue.

## Validation

- Both scan entry points now pass `--fail`, retaining the documented result filter.
- The dependency-free Python control executes the literal Bash steps from their
  YAML files. A custom detector verifies a synthetic marker through a local HTTP
  server; no real credentials or external verification services are involved.
- Disposable Git fixture history is generated with `git fast-import`. The marker
  file is removed before full-history checks, so the finding comes from history.
- With checksum-verified TruffleHog 3.95.2 on macOS arm64, all four combinations
  of entry point and scope returned 0 for clean scans and 183 for findings.
  Removing `--fail` returned 0 and was detected by each assertion.
- `make lint`, `make lint-yaml`, `make lint-md`, `make format-check` and
  `make spell` passed. Ruff formatting and linting passed for the control script.
- `run-ci.yml` runs the control on Linux with the pinned TruffleHog action and uv
  installer. Hosted CI execution remains to be verified after opening a PR.
