# Strict TruffleHog scanning with precise fixture allowlists (#123)

## Context

`v3.2.0` installs TruffleHog 3.95.2 but its scan step passes neither `--no-update` nor `--fail`. A reproduction from Board PR #23 self-updated to 3.97.5, reported an indeterminate historical URI fixture, and still exited `0`. The fixes for that landed on `main` under #111 (`abeeb9a`, `349ecdc`, `f89edb5`), so the scan step now enforces `--no-update --results=verified,unknown --fail` in both entry points, but no tag carries them and `CHANGELOG.md` never recorded them. Consumers pinning a released version still get the failing-open behavior, and a release cut today would describe none of the fix.

Strict scanning also has no false-positive boundary. Board's history holds one intentional credential-shaped URI in an immutable test commit; its current source builds that URI at runtime, so only the historical occurrence needs permitting. TruffleHog offers no mechanism for this: `--exclude-paths` discards a whole file, `--exclude-detectors` discards a whole detector, and `trufflehog:ignore` comments cannot be added to history that must not be rewritten. Every available lever is broader than the finding.

The outcome is a released version carrying the #111 fixes plus an optional allowlist that permits one exactly identified historical finding, keeps full-history scanning failing on everything else, and never prints credential material while doing it.

## Settled decisions

- **Verified findings are never allowlisted.** A finding TruffleHog marks `Verified` fails the job even when its tuple is listed, and the diagnostic says the entry was refused for that reason. A fixture that turns into a live credential cannot go quiet.
- **Bash plus `jq`**, matching every other production path in this repo. `jq` becomes a documented runner-provided dependency of the allowlist path only, and its absence fails closed.
- **JSON allowlist file**, parsed with no dependencies. Each entry carries a required `reason`, which documents the review in a place it cannot drift away from.
- **No allowlist means no behavior change.** With the input empty, the scan step runs exactly the command it runs today, so existing consumers and the existing regressions are untouched.

## Changes

### 1. Allowlist matching helper (new)

Two sibling files beside the action, following the `set-up-scrut` precedent of a script plus its committed companions:

- `actions/run-trufflehog/check-allowlist.sh`: Bash 3.2 compatible, `--findings <path> --allowlist <path>`. Verifies `jq` is on `PATH` and fails with a named requirement if not, resolves the `.jq` program next to itself, runs it, prints the report, and maps the verdict to an exit code.
- `actions/run-trufflehog/check-allowlist.jq`: the whole matching and validation program, kept out of the shell so neither language has to be read through the other's quoting.

Write the shell file under the `write-bash-scripts` skill. `tests/check-shell-discovery.py` must discover it, and `lint-shell.yml` shellcheck and shfmt must pass on it.

**Allowlist schema:**

```json
{
  "version": 1,
  "entries": [
    {
      "reason": "Synthetic URI fixture reviewed in board#23; immutable test commit",
      "detector": "URI",
      "commit": "0f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c",
      "path": "test/support/credential_fixtures.ex",
      "line": 42
    }
  ]
}
```

Validation rejects the file, with the failing entry index and field named, when any of these does not hold. There is no lenient mode:

- the document is an object whose only keys are `version` and `entries`, with `version` equal to `1`
- `entries` is a non-empty array of objects, each with exactly the keys `reason`, `detector`, `commit`, `path`, `line`
- `reason` and `detector` are non-empty strings
- `commit` is 40 lowercase hexadecimal characters, for the same reason `set-up-clap-validator` refuses a tag for `validator-rev`: a short SHA or a ref can come to mean something else
- `path` is a non-empty string with no leading `/` and no `..` segment
- `line` is an integer of at least 1
- no two entries share a `(commit, path, line, detector)` tuple

**Classification**, reading only `DetectorName`, `Verified`, and `SourceMetadata.Data.Git.{commit,file,line}`. `Raw`, `RawV2`, `Redacted`, `ExtraData`, `StructuredData` and `AnalysisInfo` are never read, so they cannot reach the report by accident:

| Finding                                             | Outcome                                           |
| --------------------------------------------------- | ------------------------------------------------- |
| `Verified` is true                                  | Blocked, whether or not a tuple matches           |
| Git source, all four fields equal to an entry       | Allowed, reported with that entry's `reason`      |
| Git source, no entry matches                        | Blocked                                           |
| Filesystem source, or no recognized source metadata | Blocked; entries key on a commit and cannot match |
| Line is not valid JSON, or expected fields missing  | Blocked, and the run fails as a malformed input   |

**Report**, written to stdout with safe metadata only:

```text
trufflehog allowlist: 1 allowed, 1 blocked, 1 entry unused
allowed: detector=URI commit=0f1e2d3c… path=test/support/credential_fixtures.ex line=42 reason=Synthetic URI fixture reviewed in board#23
blocked: detector=URI verified=false commit=9a8b7c6d… path=lib/client.ex line=11 (no matching allowlist entry)
unused entry 0: detector=AWS commit=1122334… path=test/old_fixture.ex line=3 (no finding matched; the entry may be stale)
```

An unused entry warns and never fails, because the same allowlist is used for working-tree scans where no git finding can match it.

**Exit codes:** `0` when nothing is blocked, `1` when at least one finding is blocked, `2` when the allowlist or the findings input is invalid. The distinct `2` lets the regressions tell a refused allowlist apart from a refused finding.

### 2. Composite action: `actions/run-trufflehog/action.yml`

Add an `allowlist` input (string, default `""`, a path in the caller's checkout). Bind the helper through `env:` as `ALLOWLIST_CHECKER: ${{ github.action_path }}/check-allowlist.sh`, which is how sibling files reach container jobs here.

Extend the existing flag-dedupe loop to drop caller-supplied `-j` and `--json` alongside `--no-update` and `--fail`, since the action now owns the output format. Keep the whole thing inside the single `Run trufflehog` step: `tests/trufflehog-positive-control.py` extracts that step by name and executes its literal body, and splitting the work across steps would silently drop it out of coverage.

Step body after the existing argument parsing:

```bash
if [[ -z "${TRUFFLEHOG_ALLOWLIST}" ]]; then
  trufflehog "${args[@]}" --no-update --results=verified,unknown --fail
  exit 0
fi
# Refuse output formats the checker cannot parse instead of silently
# dropping a caller's explicit choice.
# ...reject --json-legacy, --sarif, --github-actions here...
# Findings carry raw credential material, so they stay in a 0600 temporary
# file that only the checker reads and the trap removes.
findings="$(mktemp "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/trufflehog-findings.XXXXXX")"
trap 'rm -f "${findings}"' EXIT
status=0
trufflehog "${args[@]}" --no-update --results=verified,unknown --fail \
  --json > "${findings}" || status=$?
if [[ "${status}" -ne 0 && "${status}" -ne 183 ]]; then
  echo "trufflehog exited ${status} before the allowlist could apply" >&2
  exit "${status}"
fi
"${ALLOWLIST_CHECKER}" --findings "${findings}" --allowlist "${TRUFFLEHOG_ALLOWLIST}"
```

`--fail` stays on, so `183` means findings were reported and anything else is a scan failure that must propagate untouched.

### 3. Reusable workflow: `.github/workflows/scan-for-secrets.yml`

Add a `trufflehog-allowlist` input (string, default `""`). Leave `allowlist-config` alone and reword its description to say gitleaks explicitly, so the two are not confused.

Add a `Fetch allowlist checker` step to the `trufflehog` job, gated on `inputs.trufflehog-allowlist != ''`, following `lint-text.yml`'s idiom: bind `job.workflow_repository` and `job.workflow_sha` in the step's `env:` (the `job` context is unavailable at job level), fail with a named `::error::` when either is empty because GitHub Enterprise Server populates neither, confirm the allowlist file exists in the caller's checkout and that `jq` is present, `curl` both helper files from `raw.githubusercontent.com` at that repository and commit into `${RUNNER_TEMP}`, and publish `ALLOWLIST_CHECKER` through `GITHUB_ENV`. Pinning to the commit the workflow file itself came from is the integrity boundary, exactly as it is for the npm manifests.

Give the `Run trufflehog` step the same tail as the action's, so both extracted bodies stay identical below the argument setup.

### 4. Regression coverage

Extend `tests/trufflehog-positive-control.py` rather than adding a second script: `scan_step`, `sample_history` and `run_scan` are all reused, and the CI job needs no rewiring.

**Confirmed against TruffleHog 3.95.2 before writing the helper**, which changed the fixture design:

- A custom regex detector cannot produce an indeterminate finding. A verifier answering `500`, a refused connection, an unresolvable host and an omitted `verify` block all classify as unverified with no `VerificationError`, so `--results=verified,unknown` drops them. Its `DetectorName` is also always the literal `CustomRegex`, with the configured name only in `ExtraData`.
- The built-in `URI` detector produces the indeterminate case exactly, and hermetically. An `https` URI carrying a username and password, pointing at the loopback address, yields `Verified: false` with `VerificationError: "dialing local IP addresses is not allowed"`, which TruffleHog raises by refusing to dial local addresses, so no network is involved. The finding reports `DetectorName: "URI"` and is included by `--results=verified,unknown`, exiting `183`. This is also a faithful reproduction of Board's fixture. The fixture is assembled at runtime rather than written out here or in the test source, for the same reason Board stopped committing its own: a literal would be a finding in this repository's history, and these scans run against this repository.
- `--json` and `--fail` combine: findings go to stdout as JSON lines, exit is `183`, and stderr carries only TruffleHog's own JSON logs with no credential material.
- Git metadata is `SourceMetadata.Data.Git.{commit,file,line}`; filesystem findings carry `SourceMetadata.Data.Filesystem.{file,line}` and no commit, so they cannot match a commit-keyed entry.

The allowlist regressions therefore use the built-in `URI` detector and a local-address fixture. The existing custom-detector machinery stays where it is, covering the verified path.

- Capture ground truth from the scan itself: run the pinned binary with `--json` against the planted history, read `DetectorName`, `commit`, `file` and `line` out of the finding, and build the allowlist from those values. The test then proves acceptance of the tuple TruffleHog actually emits rather than one hard-coded beside it.
- **Accept:** exact tuple, indeterminate finding, both entry points, full history. Expect exit `0`.
- **Reject, one field at a time:** wrong commit, wrong path, wrong line, wrong detector. Each expects exit `1`, proving no field is ignored.
- **Verified is never allowed:** the verifying detector's finding with its exact tuple listed. Expect exit `1` and a diagnostic naming the refusal.
- **Safe metadata only:** on a blocked finding, assert neither marker string nor the literals `Raw`, `RawV2`, `Redacted`, `StructuredData` appear anywhere in stdout or stderr, and that `detector=`, `commit=`, `path=` and `line=` do.
- **Invalid allowlists:** malformed JSON, unknown key, missing `reason`, short commit, zero line, duplicate tuple. Each expects exit `2`.
- **Stale entry:** an entry matching nothing warns and still exits `0`.
- **Rejected inputs**, as `actions/AGENTS.md` requires: with an allowlist set, the action refuses `--json-legacy`, `--sarif` and `--github-actions`, naming the flag, while a caller's `--json` is dropped like `--fail` and `--no-update`.
- **Planted defect**, matching how the file already proves `--fail` removal is caught: copy the helper, patch out the detector comparison, point `ALLOWLIST_CHECKER` at the copy, and assert the wrong-detector case goes green, then fail if it did not.

Add a `run-ci.yml` job calling `./.github/workflows/scan-for-secrets.yml` with `tool: trufflehog` and `trufflehog-allowlist` set to a committed fixture. The Python test runs extracted step bodies and so cannot reach the fetch step, which needs real workflow context; `job.workflow_sha` does resolve for a local `./` reference, as `lint-shell.yml` already relies on. The fixture entry matches nothing in this repo's clean history, so the job proves the fetch, `jq` and validation path and exits `0` on the stale-entry warning.

### 5. Documentation

- `actions/run-trufflehog/README.md`: the `allowlist` input, the schema, the four enforced flags, `jq`, the verified rule, and what the report deliberately omits.
- `docs/workflows/scan-for-secrets.md`: `trufflehog-allowlist` in the inputs table, `allowlist-config` marked gitleaks-only, the schema, and the GitHub Enterprise Server limitation the fetch step carries.
- `docs/development.md`: add `jq` to the runner-provided tools paragraph near line 45, stating that the checker fails closed when it is missing, which is the answer that paragraph demands after the actionlint case; extend Testing with the new coverage.
- `README.md`: check the Quick Reference rows; expect no change, since it carries no input tables.
- `cspell.json`: add any new words the spell check rejects.

### 6. `CHANGELOG.md`

Under `[Unreleased]`, add the three #111 fixes that were never recorded, under `### Fixed`: findings fail the scan, the pinned version is retained during scans, and enforced boolean flags are deduplicated for existing callers. Add the allowlist under `### Added` for #123. Without the #111 entries the release notes describe none of the fix this release exists to ship.

## Post-merge release

After the pull request merges, on `main`, cut the release with the `release` skill and [the release procedure](../../development.md#releasing): a minor bump for new inputs plus previously unreleased fixes, so `v3.3.0`. Confirm the `## [3.3.0]` section exists before pushing the tag, since `create-gh-release-from-changelog.yml` reads its notes from there and fails without it. Push the release commit and the tag and let tag CI publish the Release; do not create it by hand. The usage examples pinned at `@v3.2.0` in `README.md`, `docs/workflows/scan-for-secrets.md` and `actions/run-trufflehog/README.md` move to the new tag as part of that release.

## Verification

1. Confirm the assumptions the design rests on, against the pinned binary, before writing the helper: that `--json` and `--fail` combine, that a `500` from the verifier yields an `unknown` result included by `--results=verified,unknown`, that the git metadata keys are `commit`, `file` and `line`, and that stderr carries no credential material in JSON mode.
2. The local `trufflehog` is 3.97.5 and the control asserts the pin, so install 3.95.2 into a scratch directory and put it first on `PATH` for the run.
3. `uv run --script tests/trufflehog-positive-control.py`, with every new case exercised and the planted defect confirmed red.
4. `uv run tests/check-shell-discovery.py`, proving the new script is linted rather than skipped.
5. `make format`, then `make lint`, `make lint-md`, `make format-check`, `make spell`, `make lint-yaml`.
6. In CI: the TruffleHog positive control job, the new allowlist job, and `scan-for-secrets-with-trufflehog.yml` on push to `main`.
