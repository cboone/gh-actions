# Bump pinned tool versions (#61)

## Context

`scripts/check-tool-versions.py` audits the tool version strings Dependabot cannot
see: workflow `env:` blocks, `inputs.*-version` defaults, committed SHA-256 tables
and the hash-pinned Python manifests. Its weekly run opened [#61](https://github.com/cboone/gh-actions/issues/61)
reporting twelve outdated pins. Downstream repositories consume these defaults, so
a stale pin means every consumer runs an old linter, scanner or release tool until
the default moves.

The issue body is a snapshot from when it was filed. Four upstreams have published
newer releases since, so this plan pins to what upstream publishes today, which is
what leaves the audit clean after the change.

Three tools carry committed checksums because upstream publishes no checksum file:
shfmt, cargo-audit and cargo-llvm-cov. Their digests must be regenerated from the
new release assets or the install step fails. Everything else verifies against an
upstream checksum file at runtime, so only the version string moves.

## Targets

| Tool             | From      | To        | Extra work                               |
| ---------------- | --------- | --------- | ---------------------------------------- |
| golangci-lint    | `2.11.4`  | `2.13.2`  | none                                     |
| trufflehog       | `3.95.2`  | `3.97.5`  | none                                     |
| goreleaser       | `2.15.4`  | `2.18.2`  | none                                     |
| codecov CLI      | `11.2.8`  | `11.3.1`  | none                                     |
| cargo-deny       | `0.19.4`  | `0.20.2`  | none                                     |
| cargo-nextest    | `0.9.133` | `0.9.145` | none                                     |
| uv               | `0.11.8`  | `0.12.17` | thirteen call sites                      |
| shfmt            | `3.13.1`  | `3.14.1`  | three committed checksum tables          |
| cargo-audit      | `0.22.1`  | `0.22.2`  | committed checksums, `supported_version` |
| cargo-llvm-cov   | `0.8.5`   | `0.9.1`   | committed checksums, `supported_version` |
| reuse            | `5.0.2`   | `6.2.0`   | regenerate the hashed manifest           |
| Node.js LTS (24) | `24.15.0` | `24.21.0` | none                                     |

Verified current: actionlint `1.7.12`, gitleaks `8.30.1`, markscribe `0.8.1`,
scrut `0.4.3`, shellcheck `0.11.0`, yamllint `1.38.0`. No change.

Every tool also has a row in `scripts/check-tool-versions.py`. Bump each row in the
same commit as its pin so the audit script never disagrees with the workflows.

## Upstream compatibility review

Checked before planning, so the bumps are deliberate rather than mechanical.

- **cargo-deny 0.20.0** refactored the CLI and removed deprecated flags. This repo
  runs a bare `cargo deny check`, which is unaffected. It adds a
  `bans.std-replacements` lint, so a consumer with a `[bans]` section may see new
  findings.
- **cargo-llvm-cov 0.9.0** changes `--show-missing-lines` output only. This repo
  uses `--lcov --output-path`, which is unaffected.
- **uv 0.12.0** breaking changes cover `uv init` layout, legacy source
  distribution archive formats and pre-release resolution. The paths used here
  (`uv venv`, `uv pip install --require-hashes`, `uv pip compile --generate-hashes`,
  `uv run --script`) are unaffected.
- **shfmt 3.14.0** adds `--detect` but records no change to `-f`. The per-file
  discovery loop in `lint-shell.yml` exists because `-f=0` misreports explicitly
  supplied non-shell files, so that claim has to be retested rather than assumed.
- **reuse 6.0.0** is the one bump with consumer-visible behavior changes: `lint`
  now reads entire files instead of the first 4 KiB, a new "Invalid SPDX License
  Expressions" criterion can fail repositories that previously passed, "Bad
  licenses" is now scanned only under `LICENSES/`, and `python-magic` replaces
  `binaryornot`. This repository is not REUSE-licensed and `run-ci.yml` has no
  `run-reuse` self-test, so CI here will not exercise any of it. Verify locally
  against a throwaway fixture (see Verification) and call it out in the changelog.
- **golangci-lint, trufflehog, goreleaser, codecov CLI, cargo-nextest** keep their
  release asset naming and checksum files at the new versions. Confirmed against
  the release asset listings.

## Work

### 1. shfmt 3.13.1 to 3.14.1

Regenerate the four digests, then update in lockstep:

- Committed tables: `actions/set-up-shfmt/action.yml` (`checksums` default, plus the
  description prose naming v3.13.1) and `.github/workflows/lint-shell.yml`
  (`shfmt-checksums` default).
- Defaults: `actions/set-up-shfmt/action.yml`, `.github/workflows/lint-shell.yml`.
- Docs: `actions/set-up-shfmt/README.md` and `docs/workflows/lint-shell.md` input
  tables; `actions/install-pinned-tool/README.md` shfmt example, including the
  `gh api repos/mvdan/sh/releases/tags/v3.13.1` recipe line and the four digest
  lines in that example.
- `.github/workflows/run-ci.yml`: the wrapper assertion
  (`for spec in "shfmt 3.13.1 --version" ...` in **Check the wrapper installs**)
  asserts `set-up-shfmt`'s default, so it becomes `3.14.1`.

Leave the direct-install fixtures at 3.13.1: the `version:`/`checksums:` pair, the
matrix `shfmt-sha256` digests, the **Check the installed binaries** assertions and
the `wrong-checksum`, `no-checksum-source` and `plain-http-url` rejection cases all
pin 3.13.1 explicitly and keep passing. The issue says so too.

One fixture does need re-deriving. The `version-bumped-without-checksums` rejection
case pairs `VERSION=3.14.1` with a 3.13.1 checksums table to prove a forgotten
checksum bump fails closed. Once 3.14.1 is the real pin, that pairing no longer
reads as "bumped past the table". Move it to `VERSION=3.15.0` against the 3.14.1
table and update the expected message to `No checksum entry for shfmt_v3.15.0_`.
`install-pinned-tool.sh` resolves the digest before downloading, so a version that
does not exist upstream never reaches the network.

Two override examples currently name 3.14.1 to demonstrate overriding the default:
`actions/set-up-shfmt/README.md` and `docs/workflows/lint-shell.md`. Once 3.14.1 is
the default they no longer illustrate anything, so point them at 3.13.1 with its
committed digests.

Retest the `-f=0` claim under 3.14.1. If it still misreports, update the version in
the comments in `.github/workflows/lint-shell.yml` and `docs/workflows/lint-shell.md`.
If upstream fixed it, leave the loop in place, correct the prose to name the last
affected version, and open a follow-up issue rather than reworking discovery here.

### 2. cargo-audit 0.22.2 and cargo-llvm-cov 0.9.1

Both live in `.github/workflows/run-rust-ci.yml` and take the same three literal
edits per tool: the comment naming the version, `supported_version`, and the four
`expected=` digests in the `case "${target}"` block. Then the input default
(`audit-version`, `llvm-cov-version`) and the matching row in
`docs/workflows/run-rust-ci.md`.

The `supported_version` gate rejects any other version outright, which matters most
for cargo-llvm-cov: its asset name carries no version, so the gate is the only thing
standing between a bumped default and a confusing digest mismatch.

### 3. uv 0.11.8 to 0.12.17

Authoritative: `UV_VERSION` in `.github/workflows/lint-text.yml` and
`.github/workflows/check-tool-versions.yml`; the `uv-version` default in
`actions/run-reuse/action.yml` and `.github/workflows/run-scrut-tests.yml`.

Self-test sites in `.github/workflows/run-ci.yml`: four `version: 0.11.8` installs
and the `"uv 0.11.8 --version"` assertion string.

Docs: `actions/run-reuse/README.md`, `docs/workflows/run-scrut-tests.md`,
`actions/install-pinned-tool/README.md`, and the `UV_VERSION: 0.11.8` example in the
`.github/dependabot.yml` header comment.

### 4. Node.js 24.15.0 to 24.21.0

Defaults in `.github/workflows/lint-text.yml`, `.github/workflows/publish-to-npm.yml`
and `.github/workflows/deploy-to-pages.yml`; the five hardcoded `node-version` pins
in `.github/workflows/run-ci.yml`; the three `docs/workflows/*.md` input tables, the
usage examples in `actions/run-cspell/README.md` and
`actions/install-cspell-dictionaries/README.md`, and the paragraph naming all three
workflows in `docs/development.md`.

Leave `package.json`'s `engines.node` floor alone. It is a minimum, not a pin.

### 5. reuse 5.0.2 to 6.2.0

Set `requirements/reuse.in` to `reuse==6.2.0`, then regenerate the manifest whole
with the newly pinned uv:

```bash
cd requirements && uv pip compile --generate-hashes reuse.in -o reuse.txt
```

Do not hand-edit `requirements/reuse.txt`. The dependency set changes: `binaryornot`
drops out, `python-magic` arrives, and `boolean.py` becomes transitive through
`license-expression`.

### 6. Tools with upstream checksum files

Version string and documentation only, no checksum work.

- **golangci-lint**: `actions/set-up-golangci-lint/action.yml`,
  `.github/workflows/run-go-ci.yml`, plus the action README table and usage example
  and `docs/workflows/run-go-ci.md`.
- **trufflehog**: two independent defaults in `actions/run-trufflehog/action.yml`
  and `.github/workflows/scan-for-secrets.yml`, plus both doc tables.
  `tests/trufflehog-positive-control.py` parses the default out of the action with a
  regex expecting a double-quoted three-part version at its current indentation, so
  it follows the bump as long as that shape is preserved.
- **goreleaser**: `actions/set-up-goreleaser/action.yml`,
  `.github/workflows/release-go-binaries.yml`, plus both doc tables and both usage
  examples.
- **codecov CLI**: defaults in `.github/workflows/run-go-ci.yml` and
  `.github/workflows/run-rust-ci.yml`, plus both doc tables.
- **cargo-deny** and **cargo-nextest**: defaults in
  `.github/workflows/run-rust-ci.yml`, plus their `docs/workflows/run-rust-ci.md`
  rows.

### 7. Changelog

One consolidated `### Changed` entry under `## [Unreleased]`, following the bullet
list style the 2.2.0 entry used for the previous bulk bump, referencing `(#61)`.
Give reuse its own sub-bullet naming the behavior changes consumers will see, and
annotate cargo-deny, cargo-llvm-cov and reuse as major or 0.x-breaking bumps.

## Regenerating the committed checksums

GitHub serves each release asset's SHA-256 in its metadata, which is the recipe
`actions/install-pinned-tool/README.md` already documents:

```bash
gh api repos/mvdan/sh/releases/tags/v3.14.1 \
  --jq '.assets[] | "\(.digest | sub("^sha256:"; ""))  \(.name)"'
```

Use the same call for `taiki-e/cargo-llvm-cov` at `v0.9.1` and for
`rustsec/rustsec` at `cargo-audit/v0.22.2`. Then download all twelve assets and hash
them locally, and treat the committed value as confirmed only where the two agree.
The metadata digest and a local hash are independent of each other; one alone is a
single point of failure for the value the whole trust model rests on.

Assets to cover, four each: shfmt `linux_amd64`, `linux_arm64`, `darwin_amd64`,
`darwin_arm64`; cargo-audit and cargo-llvm-cov `x86_64-unknown-linux-gnu`,
`aarch64-unknown-linux-gnu`, `x86_64-apple-darwin`, `aarch64-apple-darwin`.

## Verification

Local, before pushing:

1. `uv run scripts/check-tool-versions.py` prints `All pinned tool versions are current.`
   This is the single strongest signal that nothing was missed.
2. `grep -rn` each outgoing version across the tree. Only `CHANGELOG.md`,
   `docs/plans/`, `docs/reviews/`, the deliberate shfmt fixtures and the unrelated
   `0.11.8`/`5.0.2` matches in `Cargo.lock` and `package-lock.json` should remain.
3. Install shfmt 3.14.1 from the committed digests and run
   `uv run tests/check-shell-discovery.py` against it. This executes the workflow's
   real discovery and checker blocks and settles the `-f=0` question.
4. Install reuse from the regenerated `requirements/reuse.txt` into a scratch venv
   with `uv pip install --require-hashes`, confirm `reuse --version` reports 6.2.0,
   and run `reuse lint` against a small throwaway REUSE-compliant fixture to confirm
   the tool runs rather than failing on the `python-magic` dependency change.
5. `make lint`, `make lint-md`, `make format-check`, `make spell`, `make lint-yaml`.
   Run `make format` first if Prettier reflows any table.

On the pull request, CI covers what cannot be checked locally: the runner matrix
installs shfmt, actionlint, shellcheck and uv on Linux amd64, Linux arm64 and macOS
and asserts each reported version; the rejection controls prove the installer still
fails closed; and the TruffleHog positive control re-derives the pin from the action.

Nothing here exercises `run-reuse`, `run-rust-ci.yml`'s cargo-audit and
cargo-llvm-cov install steps, `release-go-binaries.yml` or `publish-to-npm.yml`.
Those land verified by inspection and by the digest cross-check above.

## Commits

Small and per-group, each one self-contained with its documentation and its
`scripts/check-tool-versions.py` row, all signed and referencing `(#61)`:

1. `chore: bump shfmt to 3.14.1 (#61)`
2. `chore: bump cargo-audit and cargo-llvm-cov (#61)`
3. `chore: bump uv to 0.12.17 (#61)`
4. `chore: bump Node.js to 24.21.0 (#61)`
5. `chore: bump reuse to 6.2.0 (#61)`
6. `chore: bump tools with upstream checksum files (#61)`
7. `docs: record the tool version bumps in the changelog (#61)`

The plan file is committed and retained, per the convention for `cboone` repositories.

## Follow-ups, not this change

- `.github/dependabot.yml` says committed checksums cover "shfmt/scrut/cargo-audit".
  It has covered shellcheck and cargo-llvm-cov for some time. Worth a separate
  documentation fix.
- If shfmt 3.14.1 fixed `-f=0`, the per-file discovery loop in `lint-shell.yml`
  could collapse back to a single batched call. That is a behavior change with its
  own test surface and belongs in its own issue. Filed as #124.

## Outcome

All twelve pins landed, in six commits plus the changelog. The audit
comparison reports every pinned tool current, including the six this plan
did not touch.

Two things differed from the plan.

**shfmt fixed `-f=0`.** The plan treated this as open. Testing 3.13.1 and
3.14.1 side by side against an explicitly supplied non-shell file confirms
the defect and its repair: under 3.13.1, `shfmt -f=0 -- notes` prints
`notes`, and a batched call prints every file given to it; under 3.14.1
both agree with `-f` and print only real shell files. The per-file loop in
`lint-shell.yml` therefore stays for a different reason than the one
originally recorded, which the comment and the reference now give:
`shfmt-version` is caller-overridable, so an older shfmt still reaches
that code path. Collapsing the loop is left to its own issue.

**`reuse lint` could not be verified under multiprocessing.** The sandbox
refuses the semaphore system call `ProcessPoolExecutor` needs, so the fixture
runs used `--no-multiprocessing`. That is an environment limit, not a
property of reuse 6.2.0, and the default path is what CI will exercise.

Checksum regeneration used both sources the plan called for. All twelve
digests agreed between the release asset metadata and a locally computed
hash of the downloaded asset.
