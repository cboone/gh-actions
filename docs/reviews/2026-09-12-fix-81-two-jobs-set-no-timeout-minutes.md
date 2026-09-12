# Branch Review: fix/81-two-jobs-set-no-timeout-minutes

Base: main (merge base: d78624a)
Commits: 3
Files changed: 7 (2 added, 5 modified, 0 deleted, 0 renamed)
Reviewed through: ddb9c57
Review fixes: ddb9c57

## Summary

The branch closes [#81](https://github.com/cboone/gh-actions/issues/81) by
wiring each of two reusable workflows' existing `timeout-minutes` input to
the one job that never received it: `validate-inputs` in
`scan-for-secrets.yml` and `deploy` in `deploy-to-pages.yml`. Both had been
inheriting GitHub's 360-minute default with no caller recourse, because
job-level `timeout-minutes` is only settable inside the callee. The
substantive work was not the two lines of YAML but resolving the question
the issue held the `deploy` value on: whether time spent awaiting
`github-pages` environment approval consumes the job's ceiling. It does
not, so `deploy` shares `build`'s input and no new input or default was
introduced.

## Changes by Area

### Reusable workflows

Each of the two jobs gains `timeout-minutes: ${{ inputs.timeout-minutes }}`
directly below `runs-on`, the position its siblings already use. No input
is added, removed, or redefined, and no default changes, so the workflows
stay source-compatible for every consumer.

- `.github/workflows/scan-for-secrets.yml`
- `.github/workflows/deploy-to-pages.yml`

### Documentation

`deploy-to-pages.md` gains the caveat pair that records the approval-wait
finding and the `actions/deploy-pages` polling timeout.
`copilot-instructions.md` gains the matching PR-review entry, because
"`deploy` waits for an approver, so raise its ceiling" is a plausible and
wrong suggestion, which is what that file exists to head off. The
`CHANGELOG.md` entry opens a `### Fixed` section under `[Unreleased]`,
after `### Changed`, per Keep a Changelog ordering.

- `docs/workflows/deploy-to-pages.md`
- `.github/copilot-instructions.md`
- `CHANGELOG.md`

### Planning

- `docs/plans/todo/2026-09-12-wire-timeout-minutes-to-unbounded-jobs.md`

## File Inventory

**Added (2):**

- `docs/plans/todo/2026-09-12-wire-timeout-minutes-to-unbounded-jobs.md`
- `docs/reviews/2026-09-12-fix-81-two-jobs-set-no-timeout-minutes.md`

**Modified (5):** `.github/copilot-instructions.md`,
`.github/workflows/deploy-to-pages.yml`,
`.github/workflows/scan-for-secrets.yml`, `CHANGELOG.md`,
`docs/workflows/deploy-to-pages.md`

**Deleted (0), renamed (0).**

## Notable Changes

The only behavioral change is the ceiling itself. A consumer who already
passes `timeout-minutes` now has it honored on two jobs that previously
ignored it, which means a caller who set an aggressive value could see a
job fail that used to run to completion under the 360-minute default. That
is the point of the fix rather than a regression, and the value is the
caller's own. Nobody's default changes.

`deploy` is the one that matters in practice. It runs
`actions/deploy-pages`, which polls a remote API and waits for a
deployment to report success, the shape of step that actually hangs.
`validate-inputs` runs two `case` statements with no network access and no
checkout, so its fix is consistency rather than exposure.

## Plan Compliance

**Verdict: full compliance.** Every change the plan specified landed as
described, with one review-driven correction to the placement of the
documentation it called for, plus one documented addition. The plan's
central research question was resolved before implementation rather than
deferred, which is what it was written to do.

**Overall progress: 4/4 planned changes done (100%)**, plus the issue's
own four-item Work checklist fully addressed.

### Done

1. `scan-for-secrets.yml`'s `validate-inputs` job applies the input.
   Placement matches the `gitleaks` and `trufflehog` jobs.
1. `deploy-to-pages.yml`'s `deploy` job applies the same input. Placement
   matches `build`.
1. `docs/workflows/deploy-to-pages.md` records the approval-wait finding
   and the 10-minute `actions/deploy-pages` polling timeout. Landed first
   in the wrong slot; see Deviations.
1. `CHANGELOG.md` opens `### Fixed` under `[Unreleased]` after
   `### Changed`, with one entry naming both jobs and referencing `(#81)`.

The plan also committed to leaving two things alone, and both held: no
Inputs table was edited, since both docs already describe
`timeout-minutes` generically as "Job timeout in minutes", which the fix
makes true of every job; and `deploy`'s hardcoded `runs-on: ubuntu-latest`
was not touched.

### Deviations

**Caveat placement, corrected (reasonable).** The plan said to put the
caveat "after the description, before `## Inputs`", which is what the
`AGENTS.md` template says. That description is ambiguous, and the first
attempt put it after the `**Permissions:**` line. Checking `run-go-ci.md`
and `lint-shell.md` showed both place caveats between the description and
`**Permissions:**`. Corrected in `ddb9c57`, and the paragraph was split in
two and tightened at the same time, since one dense block buried the one
fact a reader needs.

**Addition: the `copilot-instructions.md` entry (justified).** Not in the
plan. It is the repository's canonical mechanism for recording a decision
a reviewer would plausibly challenge, and the `deploy` timeout value is
exactly such a decision: the reasoning is non-obvious, it took external
research to settle, and the wrong suggestion is the intuitive one. Adding
it keeps the finding from having to be re-derived during review. Small,
additive, and squarely within a documented repository convention.

### Fidelity concerns

None. The plan's stated intent was that every job carry a
caller-configurable ceiling and that the non-obvious interaction be
recorded where a consumer will see it. Both hold, and the recording ended
up in two places rather than one.

## Code Quality Assessment

### Verdict

**Ready to merge.** The change is three lines of YAML across two files,
each an exact structural match for a sibling job in the same file, plus
documentation. The reasoning behind the one judgment call is written down
in three places at the right level of detail for each audience: consumer
(`docs/workflows/`), reviewer (`copilot-instructions.md`), and historical
record (`CHANGELOG.md`, commit body). There is nothing here to hold back.

### Strengths

- **The research question was actually answered, not assumed.** The issue
  flagged the approval-wait interaction as a blocker and the branch
  settled it against GitHub's documented limits rather than picking a
  value and hoping. The decisive argument is a proof by contradiction
  rather than an appeal to a doc page: the 360-minute default and the
  documented 30-day approval window cannot measure the same clock, because
  a shared clock would cancel every awaiting-approval job after six hours.
  That argument survives a doc rewrite.
- **Minimal surface.** No new input, no changed default, no restructuring.
  A consumer upgrading across this change sees no difference unless they
  had already asked for a lower ceiling, which is the bug.
- **The audit was independently reproduced.** Rather than trusting the
  issue's table, every job in `.github/workflows/` was re-checked before
  and after, confirming both that the two named jobs were the only gaps
  and that the six remaining jobs without the key are all job-level
  `uses:` calls, where it is not permitted.
- **A useful second-order detail surfaced.** `actions/deploy-pages` has
  its own 10-minute polling timeout, so the 15-minute default sits above
  it and acts as a real backstop instead of preempting the action's
  clearer error. That also tells a caller why a value below 10 is a bad
  idea, which is now documented.

### Findings

One finding, raised and fixed within the branch:

- **Caveat in the wrong slot** (`docs/workflows/deploy-to-pages.md`,
  fixed in `ddb9c57`). Placed after `**Permissions:**` where the two
  existing docs with caveats place them before it, and long enough that
  the operative fact was buried. Reordered, split in two, tightened.

### Remaining

Nothing blocking. One observation deliberately left out of scope:

- `deploy-to-pages.yml`'s `deploy` job hardcodes `runs-on: ubuntu-latest`
  while `build` uses `${{ inputs.runs-on }}`. It sits on the lines this
  branch edited, but it is not this bug and is defensible on its own
  terms, since `deploy` only calls the Pages API and pinning it to Linux
  keeps a caller building on `macos-latest` from paying the 10x macOS rate
  for an API call. Worth a separate issue only if the asymmetry is judged
  more confusing than the saving is worth.

### Verification performed

`make lint` (actionlint), `make lint-yaml`, `make lint-md`,
`make format-check`, and `make spell` all pass. Because
`scan-for-secrets.yml` is self-hosted through
`scan-for-secrets-with-gitleaks.yml` and
`scan-for-secrets-with-trufflehog.yml`, pushing the branch exercises the
`validate-inputs` change in this repository's own CI.
`deploy-to-pages.yml` is not self-hosted here, as this repository
publishes no Pages site, so actionlint plus review is the available check
on that one; the change is a single key whose value and placement match
the `build` job above it.
