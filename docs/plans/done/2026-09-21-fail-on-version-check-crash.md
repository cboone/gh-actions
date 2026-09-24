# Fail the version check workflow when the audit script crashes

Issue: [#140](https://github.com/cboone/gh-actions/issues/140)

## Context

`.github/workflows/check-tool-versions.yml`'s `Run version check` step captures
`scripts/check-tool-versions.py`'s exit status and routes on it. Only status `2`
reaches `Fail job on lookup errors`; every other non-zero status falls through to
`Open or update tracking issue`, which runs `gh issue edit --body-file` against
`${RUNNER_TEMP}/report.md`.

The audit script exits `0` when everything is current, `1` when something is
outdated and `2` on lookup errors. Any other status means it did not run to
completion: an unhandled exception outside the per-tool `try` in `main()`, a
`uv run --script` that cannot resolve or download an interpreter for
`requires-python = ">=3.11"`, or a PEP 723 header that stops parsing after an
edit. In each of those the traceback goes to stderr and stdout is empty, so
`report.md` is empty. The step then blanks the tracking issue's body and the
scheduled run reports green. The failure hides twice: the workflow passes, and
the issue that would have shown the problem is the thing that gets erased.

The step depends on the invariant "a non-zero status implies a non-empty
report". That holds today only by accident, because status `1` requires a
non-empty `outdated` list and that list always prints a table. Nothing enforces
it, and nothing fails if it stops being true.

Intended outcome: an audit run that does not complete fails the job loudly, and
the tracking issue is never overwritten with an empty body. The path is covered
by a check that goes red when either guard is removed, because the whole point
of the bug is that this path currently fails green.

## Approach

Guard the step itself rather than the script. The script cannot report its own
crash, and `uv` failing to start it is outside the script entirely, so the
enforcement point has to be the shell block that reads the status.

Three ordered changes inside the `Run version check` block:

1. Print the `::group::Report` block first, so a run that is about to fail still
   shows whatever partial output exists.
2. Reject any status outside `0`, `1`, `2` with a `::error::` annotation naming
   the status.
3. Reject a non-zero status paired with an empty report, naming the refusal to
   overwrite the tracking issue.

Write `GITHUB_OUTPUT` only after both guards pass. The downstream steps are
already skipped when this step fails, since their `if:` conditions carry the
implicit `success()`; withholding the outputs additionally makes the
unvalidated-status state unreachable, so a later `if: always()` on a downstream
step cannot act on it.

Keep the block's existing POSIX `[ ... ]` tests and `${RUNNER_TEMP}` reference
style. `check-tool-versions.yml` uses `[ ... ]` throughout, and a single file
mixing both forms reads worse than either alone. The broader repository favors
`[[ ... ]]`; converting this file is a separate cleanup, not part of this fix.

## Changes

### 1. `.github/workflows/check-tool-versions.yml`

Rewrite the `Run version check` `run:` block. Introduce a `report` variable so
the path appears once, print the report group, then validate, then publish
outputs:

```bash
report="${RUNNER_TEMP}/report.md"
set +e
./scripts/check-tool-versions.py > "${report}"
status=$?
set -e
echo "::group::Report"
cat "${report}"
echo "::endgroup::"
case "${status}" in
  0 | 1 | 2) ;;
  *)
    echo "::error::check-tool-versions.py exited ${status}; expected 0, 1 or 2." >&2
    exit 1
    ;;
esac
if [ "${status}" != "0" ] && [ ! -s "${report}" ]; then
  echo "::error::check-tool-versions.py exited ${status} with an empty report; refusing to overwrite the tracking issue." >&2
  exit 1
fi
{
  echo "status=${status}"
  echo "report-path=${report}"
} >> "${GITHUB_OUTPUT}"
```

Add a comment above the guards recording why they exist: the three statuses are
the script's entire contract, and anything else means it did not finish, so the
report cannot be trusted as an issue body.

### 2. `tests/check-tool-version-reporting.py` (new)

A uv-managed PEP 723 checker in the shape of `tests/check-shell-discovery.py`:
read the literal `Run version check` block out of the workflow without a YAML
dependency, then execute it against stub audit scripts in a temporary workspace.

Reuse `check-shell-discovery.py`'s `run_block` extraction, which splits on the
step name and the `run: |` marker and strips the body's indentation. Give each
case a fresh
`RUNNER_TEMP` and an empty `GITHUB_OUTPUT`.

Execute under `bash -e -c`, not `bash -e -o pipefail -c`. The runner's default
`run:` shell is `bash -e {0}`; this workflow sets no `shell: bash` and no
`defaults.run.shell`, so `pipefail` and `nounset` are absent in production and
the block has to be correct without them. Note that in a comment, since
`check-shell-discovery.py` adds `pipefail` to a workflow that also lacks it.

The stub stands in for `./scripts/check-tool-versions.py` and is a Bash script
that writes fixed stdout and exits a fixed status. The block does not care what
interpreter the real audit uses.

Cases, each asserting the block's exit status, the `GITHUB_OUTPUT` contents and
the annotation text:

- Status `0` with the current-versions line: block succeeds, `status=0` and
  `report-path` are published, and the report file survives for `--body-file`.
- Status `1` with an outdated table: succeeds, `status=1`.
- Status `2` with a lookup-error report: succeeds, `status=2`.
- Status `1` with empty stdout: fails, `GITHUB_OUTPUT` stays empty, the
  annotation names the empty report. This is the crash shape from the issue.
- Status `2` with empty stdout: same refusal, proving the emptiness guard is not
  keyed to status `1`.
- Status `3` with a non-empty report: fails on the status guard, annotation names
  the status. The report is deliberately non-empty so this case cannot pass by
  way of the emptiness guard.
- Stub removed entirely, so the block runs a missing path and gets `127`: fails
  on the status guard. This is the `uv`-cannot-start shape.

Every failing case also asserts `::group::Report` reached stdout, which locks in
diagnostics-before-exit ordering.

### 3. `.github/workflows/run-ci.yml`

Add a `tool-version-reporting` job after `workflow-arg-binding`: checkout,
`uses: ./actions/set-up-uv`, then `uv run --script
tests/check-tool-version-reporting.py`. `ubuntu-latest` alone, because
`check-tool-versions.yml` is scheduled on `ubuntu-latest` and nothing else runs
this block; say so in a comment, the way the Linux-arm64 omission is justified
for `trufflehog-positive-control`. Add the job to the header comment block that
enumerates what each job covers.

### 4. Documentation

- `docs/development.md`, Testing section: a paragraph for the new checker,
  naming what each case is the sole coverage for and recording the planted-defect
  confirmation, in the register the `check-shell-discovery.py` paragraphs use.
- `README.md`: extend the `check-tool-versions.yml` paragraph so it says the
  workflow fails rather than reporting green when the audit does not complete.
- `CHANGELOG.md`: a `### Fixed` entry under `## [Unreleased]` referencing `(#140)`.

## Plant table

Measured after the fix and the checker were committed, so reverting a plant
reverts the plant and not the check it tests. The control run passes all seven
cases; each plant was applied alone and reverted before the next.

| Planted defect                              | Instrument expected to catch it        | What actually happened                                                                                                                                                                                       | Test that covers it now                     |
| ------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------- |
| Delete the `case` status guard              | `unexpected status`, `missing audit`   | `unexpected status` failed at `run["code"] == 1`; the block exited 0 and published `status=3`. `missing audit` **stayed green**: the empty-report guard caught 127 and its message contains `exited 127`      | both, after asserting `expected 0, 1 or 2`  |
| Delete the empty-report guard               | `crash on exit 1`, `crash on exit 2`   | `crash on exit 1` failed at `run["code"] == 1`; the block exited 0 and published `status=1` against an empty report. The status guard cannot see a documented status, so nothing else caught it               | `crash on exit 1`, `crash on exit 2`        |
| Publish `GITHUB_OUTPUT` before both guards  | the empty-outputs assertion            | `crash on exit 1` failed at `run["outputs"] == ""`. Exit status and annotation were unchanged, so that assertion was the only thing that saw it                                                               | all four refusal cases                      |
| Print the report group after both guards    | the group assertion                    | `crash on exit 1` failed at `"::group::Report" in run["stdout"]`. Exit status and annotation were unchanged again                                                                                             | all four refusal cases                      |

The first row is the finding. An assertion naming only the status passed on
either guard's message, so the `missing audit` case was coverage of neither.
Both status cases now assert `expected 0, 1 or 2`, and re-planting the status
guard's removal fails both. The annotation wording and the assertion are a
pair; the development reference says so where the case is described.

## Verification

1. `uv run --script tests/check-tool-version-reporting.py`: seven cases, all
   passing.
2. The plant table above, each plant applied alone and reverted after.
3. `uv run scripts/check-tool-versions.py` still prints its report and exits as
   documented, confirming the audit script itself is untouched.
4. `make lint`, `make lint-yaml`, `make lint-md`, `make format-check` and
   `make spell`.
5. On the branch, `gh workflow run check-tool-versions.yml` exercises the real
   step against the real audit, which no push-triggered job reaches.

## Commits

1. `fix: fail check-tool-versions when the audit does not complete (#140)` —
   the workflow block.
2. `test: cover check-tool-versions reporting against stub audits (#140)` —
   the checker and the `run-ci.yml` job, committed before planting against them.
3. `test: assert which guard refused a version check run (#140)` — the fix for
   the first row of the plant table.
4. `docs: record the version check failure guards (#140)` — reference, README,
   CHANGELOG and this plan.
