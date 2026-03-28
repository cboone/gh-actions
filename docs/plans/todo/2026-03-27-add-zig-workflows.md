# Add zig-ci.yml and zig-release.yml reusable workflows

Issue: #22

## Context

Zig projects currently have no reusable CI or release workflows in this
repository. During the bootstrap of cboone/seine (a Zig CLI project), all CI and
release workflows had to be written inline. Adding `zig-ci.yml` and
`zig-release.yml` brings Zig to parity with Go's first-class support
(`go-ci.yml`, `go-release.yml`) and unblocks CI/release for Zig projects across
the 26+ downstream repos.

Related: cboone/cboone-cc-plugins#223 (adds Zig support to the plugin ecosystem)

## New files

### 1. `.github/workflows/zig-ci.yml`

Reusable Zig CI workflow following the `go-ci.yml` pattern.

**Inputs (13):**

| Input               | Type    | Required | Default                                                                     |
| ------------------- | ------- | -------- | --------------------------------------------------------------------------- |
| `zig-version`       | string  | yes      | (none)                                                                      |
| `runs-on`           | string  | no       | `ubuntu-latest`                                                             |
| `run-test`          | boolean | no       | `true`                                                                      |
| `run-fmt`           | boolean | no       | `true`                                                                      |
| `run-build`         | boolean | no       | `true`                                                                      |
| `run-cross-compile` | boolean | no       | `false`                                                                     |
| `cross-targets`     | string  | no       | `x86_64-linux-gnu aarch64-linux-gnu x86_64-macos aarch64-macos x86_64-windows-gnu` |
| `run-scrut`         | boolean | no       | `false`                                                                     |
| `scrut-build-cmd`   | string  | no       | `zig build`                                                                 |
| `scrut-env`         | string  | no       | `""`                                                                        |
| `scrut-test-dir`    | string  | no       | `tests/`                                                                    |
| `scrut-setup-cmd`   | string  | no       | `""`                                                                        |
| `timeout-minutes`   | number  | no       | `20`                                                                        |

**Permissions:** `contents: read`

**Jobs (5, all conditional on their `run-*` input):**

1. **Test** - checkout, setup-zig, `zig build test`
2. **Format** - checkout, setup-zig, `zig fmt --check src/ build.zig`
3. **Build** - checkout, setup-zig, `zig build`
4. **Cross compile** - checkout, setup-zig, bash loop over `cross-targets` running
   `zig build -Dtarget=... -Doptimize=ReleaseSafe` with `::group::` log grouping
5. **Scrut** - checkout, setup-zig, optional setup cmd, build cmd, inline scrut
   install (copied from `go-ci.yml`), run scrut tests with env var processing

**Key design decisions:**

- Uses `mlugg/setup-zig@d1434d08867e3ee9daa34448df10607b98908d29 # v2` (community
  standard, handles caching)
- Runs Zig commands directly (not via Makefile) since Zig projects idiomatically
  use `build.zig` as their build system. This is a deliberate difference from
  `go-ci.yml`.
- Cross-compile uses a single-job bash loop (not matrix strategy) because Zig
  cross-compilation needs no extra toolchains, so parallelization provides
  negligible benefit
- Scrut job copies the exact inline scrut installation from `go-ci.yml` (hardcoded
  v0.4.3 checksums, no `supported_version` guard per copilot-instructions.md
  convention)

### 2. `.github/workflows/zig-release.yml`

Reusable Zig release workflow. Fundamentally different from `go-release.yml`
because Zig does not use GoReleaser. A single runner cross-compiles all targets.

**Inputs (6):**

| Input             | Type   | Required | Default                                                                     |
| ----------------- | ------ | -------- | --------------------------------------------------------------------------- |
| `zig-version`     | string | yes      | (none)                                                                      |
| `binary-name`     | string | yes      | (none)                                                                      |
| `targets`         | string | no       | `x86_64-linux-gnu aarch64-linux-gnu x86_64-macos aarch64-macos x86_64-windows-gnu` |
| `optimize`        | string | no       | `ReleaseSafe`                                                               |
| `runs-on`         | string | no       | `ubuntu-latest`                                                             |
| `timeout-minutes` | number | no       | `30`                                                                        |

**Permissions:** `contents: write`

**Single job: Release**

Steps:

1. Checkout with `fetch-depth: 0` (needed for `generate_release_notes`)
2. Setup Zig via `mlugg/setup-zig@v2` (SHA-pinned)
3. Build and package (single bash step):
   - Loop over targets, `zig build -Dtarget=... -Doptimize=...`
   - Map Zig target triples to user-friendly `{os}-{arch}` names via case
     statement:
     - `x86_64-linux-*` -> `linux-amd64`
     - `aarch64-linux-*` -> `linux-arm64`
     - `x86_64-macos*` -> `darwin-amd64`
     - `aarch64-macos*` -> `darwin-arm64`
     - `x86_64-windows-*` -> `windows-amd64`
     - `aarch64-windows-*` -> `windows-arm64`
     - `*)` catch-all exits with error
   - Package as `{binary}-{version}-{os}-{arch}.tar.gz` (`.zip` for Windows)
   - Archive contains a directory with the binary inside
   - Generate `checksums.txt` via `sha256sum`/`shasum -a 256` fallback
4. Create GitHub Release via
   `softprops/action-gh-release@153bb8e04406b158c6c84fc1615b65b24149a1fe # v2`
   with `files` glob and `generate_release_notes: true`

**Key design decisions:**

- Binary location assumes Zig default `zig-out/bin/{binary-name}` (`.exe` for
  Windows)
- All inputs passed to shell via `env:` mappings (repo convention)
- Uses `softprops/action-gh-release` (not `gh release create`) because it handles
  multi-file uploads more cleanly
- No explicit `GITHUB_TOKEN` env needed (softprops action uses it automatically
  from job context)

## Files to update

### 3. `CLAUDE.md` (Repository Structure section)

Add under `.github/workflows/`:

```text
    zig-ci.yml           # Reusable: Zig test, format, build, cross-compile, scrut
    zig-release.yml      # Reusable: Zig cross-compile release
```

### 4. `.github/copilot-instructions.md`

- Update scrut checksums bullet: change "All three files" to "All four files" and
  add `.github/workflows/zig-ci.yml` to the list
- Add new bullet: zig-ci.yml uses Zig commands directly, not Makefile targets
- Add new bullet: zig-release.yml target-to-filename mapping convention

### 5. `README.md`

- Add `zig-ci` and `zig-release` to the table of contents (after `npm-publish`,
  before `Versioning`)
- Add `### zig-ci` section with description, permissions, inputs table, and usage
  example
- Add `### zig-release` section with description, permissions, inputs table, and
  usage example
- Usage examples use `@main` per repo convention

### 6. `CHANGELOG.md`

Add under `## [Unreleased]` > `### Added`:

```text
- Reusable workflow `zig-ci.yml` for Zig test, format, build, cross-compile,
  and scrut testing (#22)
- Reusable workflow `zig-release.yml` for Zig cross-compile releases with
  GitHub Release artifact uploads (#22)
```

### 7. `cspell.json`

Add to `words` array (maintaining alphabetical order):

- `mlugg` (for `mlugg/setup-zig` action reference)
- `softprops` (for `softprops/action-gh-release` action reference)

## SHA pins

| Action                     | SHA                                        | Version |
| -------------------------- | ------------------------------------------ | ------- |
| `actions/checkout`         | `de0fac2e4500dabe0009e67214ff5f5447ce83dd` | v6      |
| `mlugg/setup-zig`          | `d1434d08867e3ee9daa34448df10607b98908d29` | v2      |
| `softprops/action-gh-release` | `153bb8e04406b158c6c84fc1615b65b24149a1fe` | v2   |

## Implementation order

1. `zig-ci.yml` (most impactful, unblocks CI)
2. `zig-release.yml` (unblocks binary distribution)
3. Supporting file updates (CLAUDE.md, copilot-instructions.md, README.md,
   CHANGELOG.md, cspell.json)
4. Commit per logical change: one for zig-ci.yml, one for zig-release.yml, one
   for documentation updates

## Verification

- Run `make lint` to validate all workflow files with actionlint
- Run `make lint-md` to check Markdown formatting
- Run `make format-check` to verify Prettier formatting
- Run `make spell` to check spelling (after cspell.json update)
- Manually review workflow YAML for consistency with existing patterns
