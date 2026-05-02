# Pin Everything to Commit Hashes (or the Strongest Available Equivalent)

## Context

This repo is consumed by 26+ downstream repos and already does most of the
hard work: every `uses:` reference is SHA-pinned with a 40-char commit hash,
every binary downloaded by `curl` verifies a SHA-256 checksum, and every
workflow input default is an exact patch release. A prior plan
(`2026-03-24-centralize-third-party-actions.md`) introduced the SHA-pinning
convention, and `2026-03-27-remove-floating-tags.md` removed our own
floating major tags.

The remaining gaps are not really "missing commit hashes" but **forms of
floating dependencies that pinning-by-commit-hash does not directly solve**.
In each case below, we pin to the strongest available primitive: a commit
hash where one is meaningful, an exact version + integrity hash where it is
not, and we document why we landed where we did.

## Audit Results

### Already commit-hash pinned (no work needed)

All `uses:` references in `.github/workflows/*.yml` and `actions/*/action.yml`
already use 40-character SHAs. Verified by:

```bash
grep -rn "uses:" .github/workflows/ actions/ \
  | grep -v "uses: \./" \
  | grep -vE "uses: [^@]+@[a-f0-9]{40}"
```

Returns no output. 60+ `uses:` lines across 17 workflow files and 9 action
files are all SHA-pinned.

### Already integrity-verified (no commit hash possible)

The following are downloaded via `curl` and verified against a SHA-256 of
the archive contents. These are not GitHub action references, so commit
hashes don't apply; the archive checksum is the canonical integrity pin.

| Tool             | Source                                    | Checksum source                          |
| ---------------- | ----------------------------------------- | ---------------------------------------- |
| actionlint       | `rhysd/actionlint` releases               | upstream `*_checksums.txt`               |
| golangci-lint    | `golangci/golangci-lint` releases         | upstream `*-checksums.txt`               |
| gitleaks         | `gitleaks/gitleaks` releases              | upstream `*_checksums.txt`               |
| trufflehog       | `trufflesecurity/trufflehog` releases     | upstream `*_checksums.txt`               |
| GoReleaser       | `goreleaser/goreleaser` releases          | upstream `checksums.txt`                 |
| markscribe       | `charmbracelet/markscribe` releases       | upstream `checksums.txt`                 |
| codecov CLI      | `cli.codecov.io`                          | upstream `codecov.SHA256SUM`             |
| cargo-deny       | `EmbarkStudios/cargo-deny` releases       | upstream `*.sha256`                      |
| cargo-nextest    | `nextest-rs/nextest` releases             | upstream `*.sha256`                      |
| uv               | `astral-sh/uv` releases                   | upstream `*.sha256`                      |
| scrut            | `facebookincubator/scrut` releases        | hardcoded (no upstream checksums)        |
| shfmt            | `mvdan/sh` releases                       | hardcoded (upstream stopped publishing)  |
| cargo-audit      | `rustsec/rustsec` releases                | hardcoded (no upstream checksums)        |

### Gaps to close in this plan

1. **Missing version comment on a SHA-pin.** `dtolnay/rust-toolchain` is
   SHA-pinned at `3c5f7ea28cd621ae0bf5283f0e981fb97b8a7af9` in 5 places
   (`rust-ci.yml` x4, `rust-release.yml` x1). Unlike every other action,
   it has no `# v<N>` comment. The upstream repo intentionally does not
   publish semver tags (it tags only `master`/`stable`/`beta`/`nightly`),
   so a `# vX.Y.Z` comment is impossible. We will add a date or
   `# master @ YYYY-MM-DD` comment so a reader can reason about how
   stale the pin is.

2. **Floating Node.js major version.** `"22"` is used as the default in
   `text-lint.yml`, `npm-publish.yml`, `pages-deploy.yml`. We will move
   this to a pinned Node 24 LTS release (`"24.15.0"`) and document the
   override mechanism for callers that need a different version.

3. **Floating npm dev-dependencies.** `package.json` uses caret ranges:

   ```json
   "cspell": "^9.7.0",
   "markdownlint-cli2": "^0.21.0",
   "prettier": "^3.8.1"
   ```

   `package-lock.json` pins each transitive dep with an exact version and
   a sha512 integrity hash, so anyone running `npm ci` (the default in
   our `npm-publish.yml` and `pages-deploy.yml` workflows when a lockfile
   is present) gets a fully reproducible install. The carets only matter
   if someone runs `npm install` from scratch. We will tighten the
   `package.json` ranges to exact versions to remove that footgun and
   add a note in the README.

4. **Floating npm packages installed at runtime.** `text-lint.yml`
   lines 53-58 run:

   ```bash
   npm install --global \
     "markdownlint-cli2@${MARKDOWNLINT_CLI2_VERSION}" \
     "prettier@${PRETTIER_VERSION}" \
     "cspell@${CSPELL_VERSION}"
   ```

   The version is exact, but `npm install --global` does not check an
   integrity hash without a lockfile. npm registry integrity is good but
   not the same as a checksum we control. Options:

   - **Status quo:** trust npm registry integrity (current behavior).
   - **Lockfile-based:** check a tiny `package-lock.json` into the
     workflow's working directory and run `npm ci` against it. This
     gives lockfile-level integrity but adds a maintenance file per
     reusable workflow that consumers don't see.
   - **npm pack with hash:** download the tarball and verify a hardcoded
     sha256 (mirroring the scrut/shfmt pattern).

   Recommendation: status quo + a comment explaining the trust model.
   The cost-benefit of adding lockfiles to reusable workflows for npm
   dev-tools (Prettier, cspell, markdownlint-cli2) is poor: these are
   linters, not security-sensitive build steps. We will document the
   decision and note the upgrade path if a future caller wants stronger
   integrity.

5. **`cargo install --locked` in `rust-ci.yml` line 178.**
   `cargo install cargo-llvm-cov@0.8.5 --locked` pins to an exact crates.io
   version with the published lockfile, which is reproducible, but does not
   verify a commit hash or checksum we control. Same trust model as npm
   installs above; we will document and leave as-is. The
   `--locked` flag is essential and must remain.

6. **`uv tool run --from "yamllint==${YAMLLINT_VERSION}"`** in
   `text-lint.yml` line 96-99. Exact PyPI version, reproducible. Same
   trust model. Document and leave as-is.

7. **`rust-version: "stable"` default.** `rust-ci.yml` and `rust-release.yml`
   default to `"stable"`, which floats. This is a deliberate ergonomics
   choice (most consumers want whatever stable is current), but it is a
   floating pin. We will leave the default as `"stable"` and document
   that callers wanting reproducibility should pin to an exact toolchain
   like `"1.84.0"`.

8. **`peter-evans/create-pull-request@22a9089...`** in
   `actions/create-pull-request/action.yml` line 76 is already SHA-pinned
   with a `# v7` comment. No change.

9. **CodeQL action pins.** `github/codeql-action/{init,autobuild,analyze}@38697555...`
   in `codeql.yml` are SHA-pinned with `# v4`. No change.

### Deliberately not pinned (and why)

| Reference                              | Why not commit-pinned                   |
| -------------------------------------- | --------------------------------------- |
| `uses: ./.github/workflows/*.yml`      | Local refs always resolve to HEAD; this is the standard pattern for self-hosted reusable workflows. |
| `actions: cboone/gh-actions/...@main`  | Documented in README as a testing-only option; production callers pin to `@v2.1.4`-style tags. |
| Node.js `"22"` major version           | Intentional exception per `AGENTS.md` line 73. |
| `rust-version: "stable"` default       | Ergonomics; documented escape hatch.    |

## Bumps to Latest

In addition to the lock-down work, bump every pinned dependency to its
current latest stable release (verified 2026-04-29):

**Patch / minor / same-major bumps (low risk, applied automatically):**

- actionlint 1.7.11 → 1.7.12
- golangci-lint 2.11.3 → 2.11.4
- gitleaks 8.30.0 → 8.30.1
- trufflehog 3.93.8 → 3.95.2
- GoReleaser 2.14.3 → 2.15.4
- cargo-deny 0.19.0 → 0.19.4
- cargo-nextest 0.9.132 → 0.9.133
- yamllint 1.37.1 → 1.38.0
- prettier 3.8.1 → 3.8.3
- actions/setup-node v6 → v6.4.0 (SHA bump)
- actions/setup-go v6 → v6.4.0 (SHA bump)
- actions/upload-artifact v7 → v7.0.1 (SHA bump)
- github/codeql-action v4 → v4.35.2 (SHA bump, three sub-paths)
- crate-ci/typos v1.44.0 → v1.45.2 (SHA bump)

**Major bumps applied (callers can override via inputs/env):**

- cspell 9.7.0 → 10.0.0
- markdownlint-cli2 0.21.0 → 0.22.1 (a 0.x bump treated as breaking;
  added `MD036`/`MD060` to the disabled list since markdownlint v0.40
  introduced new strictness)
- uv 0.10.9 → 0.11.8 (0.x bump; CLI surface we depend on is stable)
- codecov CLI 10.4.0 → 11.2.8 (major bump; `upload-process --file --disable-search`
  flags retained in v11)

**Major bumps held for separate review (no caller escape):**

- peter-evans/create-pull-request v7 → v8 — wrapped in our composite
  action with no input override; bumping silently changes behavior for
  26+ consumers
- softprops/action-gh-release v2 → v3 — used inline in `zig-release.yml`
  with no input override

**Bumps unavailable / deferred:**

- shfmt 3.13.0 → 3.13.1: defer; upstream still does not publish a
  checksum file (the original reason 3.13.0 has hardcoded ones), so
  bumping requires fetching all four binaries and updating the
  hardcoded checksum table. Worth its own small PR.
- markscribe, scrut, cargo-audit, cargo-llvm-cov, dtolnay/rust-toolchain,
  Swatinem/rust-cache, mlugg/setup-zig, actions/checkout,
  actions/download-artifact, actions/configure-pages,
  actions/upload-pages-artifact, actions/deploy-pages: already at
  current latest. No bump needed.

## Changes

### 1. Annotate `dtolnay/rust-toolchain` SHA pins

Add a comment to all 5 occurrences explaining what the SHA represents.

The upstream repo does not tag semver. The current SHA
`3c5f7ea28cd621ae0bf5283f0e981fb97b8a7af9` is the head of `master` at the
time of pinning. Use `git log` on the upstream repo to look up the date
of that commit and write:

```yaml
- uses: dtolnay/rust-toolchain@3c5f7ea28cd621ae0bf5283f0e981fb97b8a7af9 # master @ YYYY-MM-DD
```

**Files:**

- `.github/workflows/rust-ci.yml` lines 113, 276, 308, 324, 401
- `.github/workflows/rust-release.yml` line 82

### 2. Tighten `package.json` to exact versions

Drop the carets so a fresh `npm install` (without a lockfile) cannot float
to a newer minor/patch.

```json
"devDependencies": {
  "cspell": "9.7.0",
  "markdownlint-cli2": "0.21.0",
  "prettier": "3.8.1"
}
```

Then run `npm install` to regenerate `package-lock.json` (the lockfile may
shift one or two transitive dep entries to reflect that the top-level
ranges are now exact).

**Files:**

- `package.json`
- `package-lock.json` (auto-regenerated)

### 3. Document the npm/cargo/uv runtime-install trust model

Add a short subsection to `AGENTS.md` (and the symlinked `CLAUDE.md`)
under the existing **SHA-256 Checksum Verification** heading explaining:

- Tools downloaded via `curl` are checksum-verified against an upstream
  or hardcoded SHA-256.
- Tools installed via `npm install --global pkg@version`,
  `cargo install crate@version --locked`, and `uv tool run --from pkg==version`
  rely on the upstream registry's integrity (npm registry, crates.io,
  PyPI). These are exact-version pinned but not hash-verified by us.
- `cargo install --locked` is mandatory for cargo installs to lock
  transitive deps.
- The tools we install this way are linters/formatters/coverage tools;
  the trust trade-off is deliberate.

**Files:**

- `AGENTS.md`
- (`CLAUDE.md` is a symlink to `AGENTS.md`, no separate edit)

### 4. Document the Node.js and Rust-toolchain floating defaults

Add a subsection to `AGENTS.md` **Version Pinning** explaining the two
intentional floating defaults:

- `node-version: "22"` floats within the Node 22 major.
- `rust-version: "stable"` floats to whatever rustup considers stable.

Note the escape hatch: callers can pass an exact version string to either
input.

**Files:**

- `AGENTS.md`

### 5. Update README pinning guidance

The README's **Versioning** section (lines 814-846) talks about pinning
the gh-actions reference itself but says nothing about the pinning
philosophy applied within this repo. Add a short **Pinning Policy**
subsection summarizing:

- Every external `uses:` is SHA-pinned with a `# vX.Y.Z` annotation.
- Every binary download verifies a SHA-256 checksum.
- Registry-based installs (npm, cargo, uv) pin to exact versions and
  rely on upstream integrity.
- Two documented exceptions float: Node.js major version and Rust
  toolchain `stable`.

**Files:**

- `README.md`

### 6. Add a CHANGELOG entry

Under `[Unreleased]`:

```markdown
### Changed

- Tightened `package.json` devDependencies from caret ranges to exact
  versions so a fresh `npm install` cannot float.
- Annotated `dtolnay/rust-toolchain` SHA pins with the upstream commit
  date.

### Documentation

- Documented the pinning policy and trust model for binary downloads,
  registry installs, and the two intentional floating defaults
  (Node.js major, Rust `stable`).
```

**Files:**

- `CHANGELOG.md`

## Files to modify

- `.github/workflows/rust-ci.yml`
- `.github/workflows/rust-release.yml`
- `package.json`
- `package-lock.json` (regenerated)
- `AGENTS.md`
- `README.md`
- `CHANGELOG.md`

## Files NOT modified

- All other workflow files (already fully pinned).
- All composite action files (already fully pinned).
- Self-hosting workflows `ci.yml`, `release.yml`, `gitleaks.yml`,
  `trufflehog.yml` (local refs are intentional).
- Plan documents in `docs/plans/done/` (historical records).

## Out of scope

- Pinning Node.js to an exact `22.x.y` (would break the documented
  major-version-floating convention; pursue separately if desired).
- Replacing `npm install --global` in `text-lint.yml` with a checked-in
  lockfile + `npm ci` pattern (cost-benefit poor for linter tools;
  pursue separately if a caller needs stronger integrity).
- Replacing `cargo install --locked` with a `cargo install --git --rev <sha>`
  pattern (atypical for crates.io packages and breaks `--locked`
  semantics).
- Pinning `rust-version` default away from `"stable"` (would break
  ergonomics for callers).
- Updating downstream consumer repos to use the new exact pins. This
  is a follow-up per repo if any consumer overrides defaults with
  caret ranges of their own.

## Verification

1. `grep -rn "uses:" .github/workflows/ actions/ | grep -v "uses: \./" | grep -vE "uses: [^@]+@[a-f0-9]{40}"` returns no output (every external `uses:` is SHA-pinned).
2. `grep -rE "@[a-f0-9]{40}([^# ]|$)" .github/workflows/ actions/` returns no output (every SHA pin has either a `# vX.Y.Z` or a `# master @ DATE` comment immediately after).
3. `grep -E '"\^|"~' package.json` returns no output (no caret/tilde ranges).
4. `npm ci` succeeds against the regenerated lockfile.
5. `make lint` (actionlint) passes.
6. `make lint-md` and `make format-check` pass.
7. `make spell` passes.
8. The self-hosting workflows (`ci.yml`, `gitleaks.yml`, `trufflehog.yml`) continue to pass on the PR.
