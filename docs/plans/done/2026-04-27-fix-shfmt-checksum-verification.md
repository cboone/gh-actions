# Fix shfmt Checksum Verification

## Context

Issue #38: `actions/setup-shfmt` and the `shell-lint.yml` reusable workflow both default to shfmt `v3.13.0` and fail at the `Install shfmt` step with `curl: (22) The requested URL returned error: 404`. The 404 is on `https://github.com/mvdan/sh/releases/download/v${VERSION}/sha256sums.txt`. Starting with shfmt v3.13.0 (released 2026-03-09), upstream deliberately stopped publishing `sha256sums.txt` because GitHub now exposes native digests for release assets (mvdan/sh#1283, mvdan/sh#1309). Every shfmt release from v3.13.0 onward is affected, so the breakage is permanent under the current implementation.

This blocks every consumer pinned to `cboone/gh-actions@v2` (or any ref whose default is `3.13.0`), including the failing job referenced in the issue.

## Approach

Switch shfmt to **hardcoded per-platform SHA-256 checksums**, matching the precedent established for scrut in `docs/plans/done/2026-03-08-scrut-checksum-verification.md` and codified in `.github/copilot-instructions.md` ("scrut checksums are hardcoded"). This keeps verification intact, requires no new tooling (no GitHub API calls, no jq, no auth), and is consistent with how the repo already handles tools whose upstream doesn't publish checksum files. Bumping shfmt versions becomes a manual recompute step, identical to the scrut workflow.

The issue also lists option 1 (use GitHub's native release-asset digest API) as an alternative. We are not taking that route: it requires a network round-trip plus JSON parsing in every install step, has no precedent in this repo, and offers no security benefit over a hardcoded checksum that was computed once from the same release artifact.

## Files to modify

| File                               | Change                                                                                                   |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `actions/setup-shfmt/action.yml`   | Replace `sha256sums.txt` fetch with hardcoded per-platform checksum case statement                       |
| `.github/workflows/shell-lint.yml` | Apply identical change to the duplicated install step (intentional duplication)                          |
| `.github/copilot-instructions.md`  | Add bullet documenting shfmt's hardcoded checksums and version-bump procedure                            |
| `README.md`                        | Update the two `3.12.0` defaults to `3.13.0` (current action default; preexisting drift, fix while here) |
| `CHANGELOG.md`                     | Add an `Unreleased` entry under `### Fixed` describing the breakage and the fix                          |

## Implementation steps

### Step 1: Compute SHA-256 checksums for shfmt v3.13.0

Download the four supported platform binaries from `https://github.com/mvdan/sh/releases/download/v3.13.0/` and compute SHA-256 hashes:

- `shfmt_v3.13.0_linux_amd64`
- `shfmt_v3.13.0_linux_arm64`
- `shfmt_v3.13.0_darwin_amd64`
- `shfmt_v3.13.0_darwin_arm64`

Use `curl -sSfL ... -o <file>` then `sha256sum <file>` (Linux) or `shasum -a 256 <file>` (macOS).

### Step 2: Update `actions/setup-shfmt/action.yml`

Pattern to mirror: `actions/setup-scrut/action.yml` lines 39-60 (supported-version guard) and lines 67-78 (verification block).

Within the existing `run:` block:

1. After the `arch` `case` statement, insert a `supported_version` guard that errors if `VERSION` is not `3.13.0`, mentioning that checksums must be updated to use a different version.
2. After the guard, insert a `case "${os}-${arch}"` statement that sets `expected` to the hardcoded checksum for each of the four supported platforms, with a `*)` catch-all that exits with `No checksum available for ${os}-${arch}`.
3. Delete the line that fetches `sha256sums.txt` and the `grep | head -1 | awk` block that parses it.
4. Keep the existing `sha256sum` / `shasum -a 256` fallback block that computes `actual` from the downloaded binary and the comparison block that exits non-zero on mismatch.
5. Update the `version` input description to note that only the version with pinned checksums is supported (mirroring the scrut input description).

### Step 3: Update `.github/workflows/shell-lint.yml`

Apply the identical change to the `Install shfmt` step (lines 68-118). This duplication is intentional per the project's "Reusable workflows are intentionally self-contained" rule: callers in other repositories cannot reference local composite actions.

### Step 4: Update `.github/copilot-instructions.md`

Add a new bullet, modeled on the existing `**scrut checksums are hardcoded**` bullet, that says:

- shfmt uses hardcoded SHA-256 checksums because upstream stopped publishing `sha256sums.txt` starting with v3.13.0 (mvdan/sh#1283, mvdan/sh#1309).
- The checksums live in `actions/setup-shfmt/action.yml` and `.github/workflows/shell-lint.yml`.
- When bumping the shfmt version, download all four platform binaries (linux-amd64, linux-arm64, darwin-amd64, darwin-arm64) and recompute SHA-256 checksums; update both files together.

### Step 5: Update `README.md`

The current README shows `3.12.0` as the default in two places (lines 116 and 542) while the actual action and workflow already default to `3.13.0`. Update both to `3.13.0` so the docs match the code post-fix.

### Step 6: Update `CHANGELOG.md`

Add an `Unreleased` section (or append to it if present) under `### Fixed` describing the bug and the switch to hardcoded checksums, in the conventional commit style used elsewhere in the file.

### Step 7: Commit

Single commit, conventional-commits format, referencing the issue:

```text
fix: hardcode shfmt SHA-256 checksums to handle missing sha256sums.txt (#38)
```

Per project convention, GPG-sign the commit.

## Reference files (patterns to follow)

- `actions/setup-scrut/action.yml` lines 39-78: canonical hardcoded-checksum + supported-version-guard + verification block
- `docs/plans/done/2026-03-08-scrut-checksum-verification.md`: the precedent plan this fix mirrors
- `.github/copilot-instructions.md` line 11 (`**scrut checksums are hardcoded**`): the bullet style to copy

## Verification

1. **Local sanity check (macOS)**: with `RUNNER_TEMP=/tmp` and `VERSION=3.13.0`, run the shell body of `actions/setup-shfmt/action.yml`'s install step. It should download `shfmt_v3.13.0_darwin_arm64`, compute a SHA-256 that matches the hardcoded value, `chmod +x` the binary, and `shfmt --version` should print `v3.13.0`.
2. **Negative test**: temporarily corrupt one byte of the hardcoded `expected` value and rerun. The step must fail with `Checksum verification failed for shfmt_v3.13.0_darwin_arm64`. Revert.
3. **Unsupported-version test**: rerun with `VERSION=3.12.0`. The step must fail at the `supported_version` guard with the "update the checksums" message.
4. **CI verification**: push the branch. The repo self-hosts `github-lint` (actionlint) via `.github/workflows/ci.yml`; that must pass. The repository does not self-host `shell-lint.yml`, so end-to-end shell-lint coverage is exercised by downstream consumers (e.g., the `swing-left/swing-left-cc-plugins` job referenced in the issue) once a release is cut.
5. **Release**: per repo conventions, releases are pure Git tags. After merge, follow the `/release` skill workflow to cut a `v2.1.4` (or appropriate) patch release so consumers pinned to `@v2` pick up the fix.
