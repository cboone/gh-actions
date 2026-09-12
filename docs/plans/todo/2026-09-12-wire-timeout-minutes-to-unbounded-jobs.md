# Wire `timeout-minutes` to the two jobs that never received it

Addresses [#81](https://github.com/cboone/gh-actions/issues/81).

## Context

Two jobs in the reusable workflows set no `timeout-minutes` and so inherit
GitHub's 360-minute default. In both cases the workflow already declares a
`timeout-minutes` input and already applies it to its sibling jobs, so the
value exists and is simply not wired to one job. A caller cannot work
around the gap, because job-level `timeout-minutes` is only settable inside
the callee.

An independent audit of every job in `.github/workflows/` confirms the
issue's finding. These are the only two:

| Workflow               | Job               | Siblings with the input  | Effective ceiling |
| ---------------------- | ----------------- | ------------------------ | ----------------- |
| `scan-for-secrets.yml` | `validate-inputs` | `gitleaks`, `trufflehog` | 360               |
| `deploy-to-pages.yml`  | `deploy`          | `build`                  | 360               |

Every other job without `timeout-minutes` is a job-level `uses:` call
(`create-gh-release-on-tag.yml`, `run-ci.yml`, and both
`scan-for-secrets-with-*.yml` callers), where the key is not permitted and
the callee owns the ceiling.

The intended outcome is that every job in this repository's reusable
workflows carries a caller-configurable ceiling, and that the one
non-obvious interaction found while investigating (environment approval
waits) is recorded where a consumer will see it.

## Resolved: environment approval does not count against `timeout-minutes`

The issue asks this to be confirmed before picking a value for `deploy`,
since that job declares `environment: github-pages` and could sit awaiting
approval. GitHub's documented limits settle it:

- `timeout-minutes` bounds **execution**. Its 360 default mirrors the
  documented hosted-runner ceiling, "Each job in a workflow can run for up
  to 6 hours of execution time."
- Environment approval has its own separate, non-configurable limit: "A
  workflow may wait for up to 30 days on environment approvals."
- The 35-day run limit is documented as covering "execution duration, and
  time spent on waiting and approval", which is GitHub stating outright
  that waiting and approval are not execution duration.
- Approval waits consume no runner time and are not billable, because no
  runner is held.

So `deploy` needs no input of its own and can share `build`'s, exactly as
the issue proposes. The shared 15-minute default is safe.

One supporting detail: `actions/deploy-pages` v5 carries its own
`timeout` input defaulting to `600000` ms (10 minutes) for the deployment
polling it does. The 15-minute job default therefore sits above the
action's own ceiling, so the action reports its own clearer timeout error
first and the job-level value acts as a true backstop.

## Changes

1. `.github/workflows/scan-for-secrets.yml`: add
   `timeout-minutes: ${{ inputs.timeout-minutes }}` to the
   `validate-inputs` job, below `runs-on`, matching the placement in the
   `gitleaks` and `trufflehog` jobs.

1. `.github/workflows/deploy-to-pages.yml`: add the same line to the
   `deploy` job, below `runs-on`, matching the placement in `build`.

1. `docs/workflows/deploy-to-pages.md`: add a caveat paragraph, in the
   slot the per-component doc template reserves for caveats (after the
   description, before `## Inputs`), recording that `timeout-minutes`
   bounds execution only, that time the `deploy` job spends waiting on
   `github-pages` protection rules falls under GitHub's 30-day approval
   limit instead, and that `actions/deploy-pages` polls with its own
   10-minute timeout, so a `timeout-minutes` below 10 preempts it.

1. `CHANGELOG.md`: add a `### Fixed` section to `[Unreleased]` after
   `### Changed`, per Keep a Changelog ordering, with one entry naming
   both jobs and referencing `(#81)`.

No input is added, removed, or redefined, and no default changes. Both
docs already describe `timeout-minutes` generically as "Job timeout in
minutes", which becomes accurate for every job once the fix lands, so
neither Inputs table needs editing.

## Deliberately out of scope

`deploy-to-pages.yml`'s `deploy` job hardcodes `runs-on: ubuntu-latest`
while `build` uses `${{ inputs.runs-on }}`. That asymmetry is adjacent to
the lines being edited but is not this bug, and it looks defensible on its
own terms: `deploy` only calls the Pages API, so pinning it to Linux keeps
a caller who builds on `macos-latest` from paying the 10x macOS rate for
an API call. Left as it is; worth a separate issue if the inconsistency
should be revisited.

## Verification

1. `make lint` runs actionlint over the workflows. The expression
   `${{ inputs.timeout-minutes }}` in a `timeout-minutes` key against a
   `number`-typed input is already proven on the sibling jobs in both
   files, so this should stay clean.

1. `make lint-yaml`, `make lint-md`, and `make format-check` cover the
   YAML and Markdown edits.

1. `scan-for-secrets.yml` is self-hosted through
   `scan-for-secrets-with-gitleaks.yml` and
   `scan-for-secrets-with-trufflehog.yml`, so pushing the branch exercises
   the `validate-inputs` change in this repository's own CI.

1. `deploy-to-pages.yml` is not self-hosted here (this repository publishes
   no Pages site), so actionlint plus review is the available check. The
   change is a single key whose value and placement match the `build` job
   directly above it.

1. Confirm the gap is closed by re-running the audit: every job in
   `.github/workflows/` should either set `timeout-minutes` or be a
   job-level `uses:` call.
