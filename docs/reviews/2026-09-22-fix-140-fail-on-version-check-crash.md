# Branch Review: fix/140-fail-on-version-check-crash

Base: `main` (merge base: `bbe1518`)
Commits: 4
Files changed: 8 (2 added, 6 modified, 0 deleted, 0 renamed)
Lines: +509 / -7
Reviewed through: `80bf1ab`

## Summary

The branch closes issue #140: `check-tool-versions.yml` treated every exit
status other than `2` as "something is outdated" and piped the report straight
into `gh issue edit --body-file`, so an audit run that crashed before writing
anything blanked the tracking issue while the job reported green. The step now
rejects a status outside the audit's documented `0`, `1`, `2`, refuses a
non-zero status paired with an empty report, and publishes `GITHUB_OUTPUT` only
once both hold. A new checker executes the workflow's literal shell block
against stand-in audits, wired into CI as `tool-version-reporting`, because the
scheduled workflow is the only other thing that runs that block.

## Changes by Area

### Version check workflow

`Run version check` gains two guards and an ordering change. The report group
is printed before either guard so a rejected run still leaves its partial
output in the log, and the step outputs are written last so an unvalidated
status cannot reach the `if:` conditions below it. A `report` variable replaces
four repetitions of `${RUNNER_TEMP}/report.md`.

- `.github/workflows/check-tool-versions.yml`

### Test coverage

`tests/check-tool-version-reporting.py` reads the literal `Run version check`
block out of the workflow and runs it against Bash stand-ins with fixed
streams and exit statuses, in the shape of `tests/check-shell-discovery.py`.
Seven cases: three documented exits publish and preserve the report, two
empty-report crashes are refused, a status outside the contract is refused
against a deliberately non-empty report, and a missing audit is refused at
bash's `127`. `run-ci.yml` gains a `tool-version-reporting` job on
`ubuntu-latest`.

- `tests/check-tool-version-reporting.py` (new)
- `.github/workflows/run-ci.yml`

### Documentation

A Testing paragraph in the development reference records what each refusal
case is the sole coverage for, why the block runs under `bash -e -c` rather
than adding `pipefail`, and the plant-table finding that the two guards overlap.
README notes that the audit's exit statuses are its whole contract. The plan
carries a filled-in plant table and moves to `docs/plans/done/`.

- `docs/development.md`, `README.md`, `CHANGELOG.md`
- `docs/plans/done/2026-09-21-fail-on-version-check-crash.md` (new)
- `cspell.json`

## File Inventory

New files (2):

- `tests/check-tool-version-reporting.py`
- `docs/plans/done/2026-09-21-fail-on-version-check-crash.md`

Modified files (6):

- `.github/workflows/check-tool-versions.yml`
- `.github/workflows/run-ci.yml`
- `CHANGELOG.md`
- `README.md`
- `cspell.json`
- `docs/development.md`

Deleted files: none. Renamed files: none.

## Notable Changes

- **CI configuration**: one new job, `tool-version-reporting`, on
  `ubuntu-latest`. It pins `actions/checkout` to the same SHA every other job
  in the file uses and reaches `set-up-uv` by `./` path, which is correct for a
  non-reusable workflow that checks this repository out.
- **Linter configuration**: `cspell.json` gains `nounset`, `unparseable` and
  `unvalidated`. No ignore paths or regexes were relaxed.
- **No dependency, schema or API changes.** No new action pins, no checksum
  surfaces touched, and `scripts/check-tool-versions.py` itself is byte for
  byte unchanged.

## Plan Compliance

Plan: `docs/plans/done/2026-09-21-fail-on-version-check-crash.md`

**Compliance verdict: good compliance.** Every planned change landed, the
verification section was executed rather than asserted, and the one place the
work exceeded the plan is recorded in the plan itself rather than left
implicit. The single gap is the last verification step, which cannot run before
the pull request exists.

**Overall progress: 8/9 items done (89%)**, the outstanding item being
verification step 5.

### Done

1. **Rewrite the `Run version check` block** — implemented as specified,
   including the `report` variable, the `::group::Report`-first ordering, the
   `case` status guard, the emptiness guard and the deferred `GITHUB_OUTPUT`
   write. The plan's decision to keep POSIX `[ ... ]` tests to match the file
   rather than adopt the repository's more common `[[ ... ]]` was honored.
2. **`tests/check-tool-version-reporting.py`** — all seven planned cases are
   present with the planned assertions. See the fidelity note below on how
   `run_block` was reused.
3. **`run-ci.yml` job** — `tool-version-reporting` with the planned steps, the
   planned single-runner justification, and the header comment entry.
4. **Documentation** — development reference, README and CHANGELOG all updated
   as planned.
5. **Verification 1** — the checker passes all seven cases.
6. **Verification 2** — the plant table was executed, one plant at a time, with
   results recorded from the runs.
7. **Verification 3** — `uv run scripts/check-tool-versions.py` exits `1` with
   a populated table; the audit script is unchanged in the diff.
8. **Verification 4** — `make lint`, `make lint-yaml`, `make lint-md`,
   `make format-check` and `make spell` all clean.

### Not started

- **Verification 5** (item 9 of 9): `gh workflow run check-tool-versions.yml`
  on the branch, the only exercise of the real step against the real audit on a
  runner. It needs the branch pushed, so it is correctly outstanding rather
  than skipped.

### Deviations

- **Scope addition: commit `5da7dfe`.** The plan listed three commits; there
  are four. The extra one strengthens two assertions after planting showed the
  `missing audit` case passing with the status guard deleted. This is the plant
  table doing its job, it is justified, and the plan was updated to list it.
- **Scope addition: `cspell.json`.** Not in the plan. Three words were needed
  by the new prose and comments. Reasonable, and the alternative (per-file
  `cspell:ignore` lines) would have been worse for words spanning YAML,
  Markdown and Python.
- **Fidelity: `run_block` was copied, not shared.** The plan said "Reuse
  `check-shell-discovery.py`'s `run_block` extraction". The implementation
  reproduces that function verbatim rather than importing it. This matches the
  repository's existing shape, where each PEP 723 checker carries its own
  extraction helper and `trufflehog-positive-control.py` has a third,
  regex-based variant, and a shared module would need an import path that
  `uv run --script` does not naturally provide. Defensible, but it is the
  letter of the plan rather than its word.

### Fidelity concerns

None that undermine intent. The guards match the issue's suggested approach,
and the two additions beyond it (ordering the report group first, deferring the
outputs) are each covered by an assertion that nothing else sees, which the
plant table measured rather than assumed.

## Code Quality Assessment

**Overall quality: ready to merge after the accuracy fix below.** The change is
small, the reasoning is written down where the next reader will hit it, and the
coverage claim was measured instead of asserted. The findings are one factual
error in comments and prose, plus nits.

### Strengths

- **The coverage is real, and it was proved.** Four plants, applied one at a
  time against committed code, each recorded with the assertion that actually
  fired. The first plant found a genuine defect in the test: with the status
  guard deleted, status `127` fell through to the empty-report guard, whose
  message also contains `exited 127`, so the `missing audit` case was covering
  neither guard. That is exactly the failure mode planting exists to find, and
  it was fixed rather than written down and lived with.
- **Two assertions that nothing else can make.** The empty-`GITHUB_OUTPUT` and
  report-group checks each catch an ordering change that leaves every exit
  status and annotation identical. The development reference says so, which is
  what stops a later reader deleting them as redundant.
- **Comments explain why, not what.** Each guard carries the failure it exists
  for. The test explains why it deliberately does not copy
  `check-shell-discovery.py`'s `-o pipefail`, which is the kind of divergence
  that otherwise looks like an oversight and gets "fixed".
- **Deferring `GITHUB_OUTPUT` is the right instinct.** It is redundant today,
  since a failed step skips the rest, and it stops being redundant the moment
  someone adds `if: always()` downstream.
- **Blast radius is minimal.** The audit script is untouched, the three
  downstream steps keep their existing conditions, and the happy paths are
  asserted alongside the refusals so the guards cannot narrow the contract.

### Issues to address

1. **Inaccurate claim that the workflow only runs on a schedule (P2).**
   `check-tool-versions.yml` has both `schedule` and `workflow_dispatch`, so
   "only runs on a schedule" is false in three places:
   - `.github/workflows/run-ci.yml:27` — "That workflow only runs on a schedule"
   - `docs/development.md:562` — "runs only on a weekly schedule"
   - `CHANGELOG.md:15` — "That workflow runs only on a weekly schedule"

   The substantive point survives, since `workflow_dispatch` is manual and no
   push-triggered job reaches the block, but the sentence as written is wrong
   and this repository's comments are held to describing current behavior. The
   job comment at `run-ci.yml:403` ("runs weekly on a schedule") is accurate
   and needs no change. Suggested wording: "runs only on a schedule or a manual
   dispatch, so no push-triggered job executes the block".

2. **Misdirecting deictic in a workflow comment (P3).**
   `.github/workflows/check-tool-versions.yml:59` ends "so the report below is
   not an issue body". The report is printed above that comment, not below.
   "the report it wrote" would be unambiguous.

### Suggestions

Non-blocking.

- **`run_block` fails opaquely.** If the step is renamed or its indentation
  changes,
  `tests/check-tool-version-reporting.py:41` raises `IndexError: list index out
of range` rather than naming the missing step.
  `tests/trufflehog-positive-control.py:64` raises an `AssertionError` that
  says which step it could not find. The check still goes red either way, so
  this is diagnosis quality, not coverage. It is inherited verbatim from
  `check-shell-discovery.py`, so fixing it here alone would make the two copies
  diverge; fixing both is a reasonable follow-up issue.
- **A meaningless argument in the missing-audit case.**
  `tests/check-tool-version-reporting.py:175` passes `status=0, output=""`
  alongside `install=False`. Both are inert, but `status=0` reads as though the
  stand-in exits 0, which is the opposite of what the case asserts. Defaulting
  `status` and `output` in `execute`, or taking the missing-audit case through
  its own helper, would remove the contradiction.
- **`[ -s ]` accepts a whitespace-only report.** A report of a single newline
  passes the emptiness guard and would still overwrite the tracking issue with
  effectively nothing. Every crash shape the issue names produces a completely
  empty stdout, so this is unreachable from the current script rather than a
  live hole, and the issue's suggested approach specified `-s`. Worth a sentence
  somewhere if it is being accepted deliberately.
- **Status `0` with an empty report is unguarded and untested.** It would close
  the tracking issue claiming everything is current. It is unreachable, since
  the script only returns `0` after the tool loop completes and always prints
  the current-versions line, but the asymmetry with the non-zero guard is not
  written down anywhere.
- **Inconsistent annotation style within one block.** The status guard writes
  its message inline; the emptiness guard builds `msg` first. That difference
  exists
  only to stay under yamllint's 120-character limit. Harmless, but a reader
  will look for a reason.
- **Commits 1 and 2 would not pass `make spell` in isolation.** `unparseable`
  and `unvalidated` first appear there and enter `cspell.json` in commit 4. CI
  gates the pull request head rather than individual commits, so nothing is
  broken; noted only because the repository merges with merge commits and keeps
  individual commits readable.

### Completeness

No TODO, FIXME, HACK or XXX markers, no stubs, no commented-out code, no
partial refactors. New behavior has tests, the reference and README are updated
in the same change, and the CHANGELOG entry is under `[Unreleased]` with the
issue reference. The plan moved to `docs/plans/done/` with its verification
section reflecting what was run.

## Resolution

Addressed on 2026-09-22. Seven of the eight items were fixed; the eighth has no
fix that this repository's conventions permit.

| #   | Summary                                      | Status                | Commit    |
| --- | -------------------------------------------- | --------------------- | --------- |
| 1   | "only runs on a schedule" is false           | Resolved              | `c5b305a` |
| 2   | "the report below" points the wrong way      | Resolved              | `8b5edea` |
| 3   | `run_block` raises a bare `IndexError`       | Resolved, both copies | `11ebe55` |
| 4   | Inert `status=0` in the missing-audit case   | Resolved              | `11ebe55` |
| 5   | `[ -s ]` accepts a whitespace-only report    | Accepted, documented  | `8b5edea` |
| 6   | Status `0` with an empty report is unguarded | Accepted, documented  | `8b5edea` |
| 7   | Inline message vs. `msg` within one block    | Resolved              | `8b5edea` |
| 8   | Commits 1–2 fail `make spell` in isolation   | Skipped               | —         |

Items 5 and 6 were accepted rather than closed. Both are unreachable from the
current audit script, and the workflow comment now says why: every failure the
guard exists for leaves stdout completely empty, so a whitespace-aware test
would reject nothing `[ -s ]` does not, and `main()` returns `0` only after the
tool loop completes, a path that always prints the current-versions line.

Item 3 was fixed in `tests/check-shell-discovery.py` as well as the new
checker, so the two verbatim copies of `run_block` stay identical. Both now
raise an `AssertionError` naming the missing step and its workflow.

Item 8 is skipped. `unparseable` and `unvalidated` first appear in commits
`f41ea20` and `deb202b` and enter `cspell.json` in `80bf1ab`, so neither of
those two commits passes `make spell` alone. Moving the word list earlier means
amending or rebasing, which this repository does not do, and CI gates the pull
request head rather than individual commits, so nothing is actually broken.

The plant table was re-run after these changes: all four plants are still
caught, and both status-guard cases still fire when that guard is removed.
