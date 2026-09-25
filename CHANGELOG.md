# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [5.0.0] - 2026-09-25

### Added

- `publish-to-npm-with-oidc.yml` reusable workflow: publishes to npmjs.com
  through npm's trusted publishing. The job presents a GitHub OIDC token, npm
  validates it against a publisher configured on the package, and no credential
  is stored anywhere. Public packages also get provenance attestations, so the
  tarball carries a verifiable link back to the run and commit that produced
  it. Declares `contents: read` and `id-token: write`, and no secrets at all
  (#137)

  It is a separate file rather than an auth-mode input on `publish-to-npm.yml`
  because a caller must grant every permission the workflow it calls declares,
  and a nested job's permissions are validated before its `if:` condition is
  evaluated. One workflow covering both modes would have forced
  `id-token: write` on every token-path caller, including ones that will never
  mint an OIDC token.

  The publisher registered on npmjs.com names the caller's own repository and
  the caller's own workflow filename: npm validates the calling workflow, not
  the one containing `npm publish`, which is what makes trusted publishing
  through a reusable workflow work. The workflow refuses a `registry-url` other
  than `https://registry.npmjs.org`, and checks that npm is at least 11.5.1 and
  Node at least 22.14.0, because below those npm reports only that
  authentication failed. The npm check is the one that bites: no Node 22 or 23
  release bundles an npm that new, so it names 24.5.0, the first that does,
  rather than repeating npm's own Node floor

- `allow-npm-install` and `run-install-scripts` inputs on `publish-to-npm.yml`
  and `deploy-to-pages.yml`, each defaulting to false, covering the callers the
  hardened install defaults below would otherwise strand (#137)

- `environment` input on `publish-to-npm-with-oidc.yml`, empty by default. The
  OIDC token's `environment` claim comes from the publish job in this
  repository, and a job calling a reusable workflow may not declare an
  environment of its own, so this input is the only way to satisfy a trusted
  publisher scoped to one. Setting it also puts that environment's protection
  rules, such as required reviewers, in front of the publish (#137)

- `run-ci.yml` `npm-publish` job, on Linux and macOS: runs the registry gate,
  the version gate, the lockfile probe and the shared install step from
  `tests/fixtures/check-npm-publish.mjs` against stubs, and asserts the
  permission split between the two publish workflows. Neither publish workflow
  can be self-hosted, since calling either end to end would publish something
  (#137)

- `run-ci.yml` `tool-version-reporting` job: runs
  `tests/check-tool-version-reporting.py`, which executes
  `check-tool-versions.yml`'s literal `Run version check` block against
  stand-in audits with fixed streams and exit statuses. That workflow runs
  only on a weekly schedule or a manual dispatch, so no push-triggered job
  executed the block, and the statuses it mishandled reported green. Each
  refusal case names the guard
  it covers; the development reference records why (#140)
- `checkout-credentials` job in `run-ci.yml`, running
  `tests/check-checkout-credentials.mjs` over every workflow and
  composite action, so the default cannot come back unnoticed. Five
  things fail it, each with its own diagnostic: a listed exemption that
  no longer names exactly one checkout, whether it was renamed, deleted
  or pointed at a different action; a checkout added without
  `persist-credentials`, a checkout that keeps its credential without
  being listed, a value that is not a YAML boolean, and a listed
  checkout that stopped keeping its credential. The boolean rule matters
  because the action enables persistence only when the normalized input
  equals `TRUE`: `yes` and `on` read as enabling and are not, while a
  quoted `"true"` enables while looking like a string. A passing run
  prints each exemption and its reason.
  `tests/fixtures/workflow-steps.mjs` gains a `usesSteps()` walk beside
  `runSteps()` for it. zizmor's `artipacked` audit (#134) will cover the
  same ground from outside (#133)

### Changed

- **Breaking:** `publish-to-npm.yml` and `deploy-to-pages.yml` refuse to
  install when the repository has no `package-lock.json` or
  `npm-shrinkwrap.json`, instead of silently falling back to `npm install`. The
  fallback resolved versions at publish or deploy time, leaving the registry as
  the only integrity boundary. Set `allow-npm-install: true` to keep it, which
  now also logs a warning saying so (#137)
- **Breaking:** both workflows install with `--ignore-scripts`, so a
  dependency's `preinstall`, `install` and `postinstall` scripts no longer run
  in a job that publishes or deploys. Set `run-install-scripts: true` for a
  build that needs them. The package's own `prepublishOnly`, `prepack` and
  `prepare` scripts still run under `npm publish` (#137)
- `deploy-to-pages.yml` sets `package-manager-cache: false` too, which turns off
  `setup-node`'s automatic caching while leaving the explicit lockfile-keyed
  cache above it untouched; the two inputs are an if/else inside the action. A
  caller whose `package.json` names npm in `packageManager`, and that ships no
  lockfile, otherwise got automatic caching and a `Dependencies lock file is not
found` failure from `setup-node`, before the install step could name the input
  to set (#137)
- `publish-to-npm.yml` sets `package-manager-cache: false` on `setup-node`, so
  a publish no longer restores a dependency cache that an earlier job could
  have poisoned. Clearing the `cache` input alone would not have done it:
  `setup-node` enables npm caching on its own whenever `package.json` names npm
  in `packageManager` or `devEngines.packageManager`. `deploy-to-pages.yml`
  builds rather than publishes and keeps its cache (#137)
- `publish-to-npm-with-oidc.yml`'s version gate orders a prerelease below the
  release it precedes, so an npm `11.5.1-rc.0` no longer satisfies a minimum of
  11.5.1. A prerelease of a higher version still does (#137)
- The install step in all three npm workflows now decides between `npm ci` and
  `npm install` inside the step, reading the lockfile path and the caller's
  opt-in through `env:`. The two `run:` ternaries that chose between those
  literals are gone, and the interpolation allowlist in
  `tests/fixtures/check-workflow-arg-binding.mjs` drops from eight entries to
  six (#137)

- Every `actions/checkout` step sets `persist-credentials: false`. The
  action's default writes the token it authenticated with into the
  checkout's `.git/config` and leaves it there for the rest of the job,
  where every later step can read it, including third-party tooling these
  workflows invoke but do not control, and anything that archives or
  uploads the workspace; zizmor calls that class of exposure
  `artipacked`. Every checkout in the repository took that default,
  including the ones that hand the workspace to GoReleaser, a cargo
  toolchain, `npm ci` beside a publish token, and a caller-supplied
  `build-command`. The `tool-version-reporting` job that #140 added while
  this was open took it too, and the new check caught it on the merge
  (#133)
- The Homebrew tap checkout in `release-rust-binaries.yml` is the single
  exception and now says so: it sets `persist-credentials: true`
  explicitly and is named `Check out the Homebrew tap`, because the
  `Commit and push formula` step pushes with that credential. The token
  is the caller's tap-scoped `HOMEBREW_TAP_TOKEN` in
  `homebrew-tap/.git/config`, not the job's `GITHUB_TOKEN` (#133)
- A `build-command`, `scrut-setup-cmd` or `scrut-build-cmd` no longer
  inherits a Git credential from the workflow's checkout. This is not a
  breaking change: every value in use across the consuming repositories
  is a tool install or a compile, and none runs an authenticated Git
  operation. A command that needs one must be given a token of its own
  (#133)

### Fixed

- `check-tool-versions.yml` fails the job when
  `scripts/check-tool-versions.py` does not run to completion. The step
  routed every non-zero status other than `2` into the `gh issue edit` call
  that rewrites the tracking issue body. An exception outside the per-tool
  `try` in `main()`, an unparseable PEP 723 header, and a uv that cannot
  resolve an interpreter all leave stdout empty, so the step blanked that
  issue's body and the scheduled run still reported green. A status outside
  `0`, `1` and `2` is now rejected, a non-zero status paired with an empty
  report is refused rather than written, and `GITHUB_OUTPUT` is published
  only once both hold, so an unvalidated status cannot reach the steps that
  key on it (#140)

## [4.1.0] - 2026-09-21

### Added

- `set-up-uv` composite action: installs uv pinned to `version` (default
  0.12.17) and adds it to `PATH`. The release archive is verified against
  the per-asset `.sha256` uv publishes beside each platform's tarball.
  Built on `install-pinned-tool`, so it covers Linux and macOS on amd64
  and arm64 (#102)
- `run-ci.yml` `reuse` job: runs `actions/run-reuse` against a new
  `tests/fixtures/reuse` fixture on Linux amd64, Linux arm64 and macOS
  arm64. `run-reuse` had no self-test, and it carries its own copy of the
  uv install recipe because a composite action cannot reach a sibling
  action by a `./` path, so nothing else exercised it. The job passes
  `--root`, since this repository is not itself REUSE-compliant; the
  action's default `args: lint` stays uncovered deliberately (#102)

### Changed

- `lint-text.yml`, `check-tool-versions.yml` and `run-reuse` install uv
  through `install-pinned-tool` instead of their own inline installers.
  The two workflow installs covered Linux x86_64 only and now cover
  Linux and macOS on amd64 and arm64; no workflow currently runs them on
  another platform, so this is latent capability rather than a fix.
  Versions, defaults and checksum sources are unchanged (#102)
- `lint-text.yml` fetches `install-pinned-tool`'s script from
  `job.workflow_repository` at `job.workflow_sha`, the model it already
  uses for its yamllint manifest and its cspell dictionary installer. It
  depended on those `job` context properties before this change, so its
  GitHub Enterprise Server support is unaffected: `run-yamllint: false`
  remains the documented setting there (#102)
- `check-tool-versions.yml` reaches `set-up-uv` by `./` path and no
  longer pins uv itself. It is not a reusable workflow and already checks
  this repository out, so the restriction that forces the other workflows
  to fetch the script does not apply to it (#102)
- `run-ci.yml`'s four consumer uv installs call `set-up-uv` instead of
  repeating the recipe. The install in the `install-pinned-tool` job is
  unchanged: it is what proves the generic installer handles uv's target
  triples, nested archive member and per-asset checksum file, and routing
  it through the wrapper would remove that coverage. The wrapper re-test
  now covers `set-up-uv` alongside `set-up-shfmt`, `set-up-actionlint`
  and `set-up-shellcheck` (#102)

- `lint-shell.yml` discovers shell scripts with a batched `shfmt -f=0` call
  over the tracked file list, rather than one `shfmt -f` process per tracked
  file. The call goes through `xargs`, so a large tree is split across a few
  processes; either way it is a handful instead of one per tracked file.
  Measured over 14,001 paths, discovery went from 32.6s to 0.29s (#124)

  The per-file loop existed because that mode listed explicitly supplied
  non-shell files until shfmt 3.14.0, where the guard in `cmd/shfmt/main.go`
  became `find.val != "false"`. No release note records the change, so it is
  cited from the source. `shfmt-version` stays caller-overridable, so discovery
  measures the binary it was given rather than trusting the pin: it asks shfmt
  to classify a prose file written outside the checkout, and keeps the per-file
  loop, with a notice, when that file comes back or the flag is refused
  outright. shfmt added `-f=0` in 3.11.0, so anything older has no such mode
  and the notice says so rather than claiming the mode filters wrongly.

  A shfmt that cannot be run at all, which exits 126 or above, now fails the
  step with an error naming the exit status and quoting shfmt's own stderr.
  Before, every non-zero exit was read as an old pin, so a missing or
  wrong-architecture binary was reported as a version problem.

  Nothing about the input contract changes. A caller pinning an older shfmt
  discovers exactly the scripts it discovered before, and pays the same process
  per tracked file to do it. What both paths guarantee is unchanged too:
  submodule directories and symlinks to untracked files excluded, a file named
  exactly `-` passed as `./-`, and every original path retained byte for byte
  in the NUL-separated manifest both checkers read.

## [4.0.0] - 2026-09-21

### Added

- `run-trufflehog` gains an `allowlist` input, and `scan-for-secrets.yml` a
  `trufflehog-allowlist` input, each naming a JSON file of reviewed findings.
  An entry matches one finding and only that finding: `commit`, `path`, `line`
  and `detector` must all be equal, so moving a fixture or changing any one
  field fails the scan again. This permits a deliberate credential-shaped
  string in a commit that must not be rewritten, without excluding its file,
  suppressing the detector, or printing the finding (#123)

  Full-history scanning stays strict. A verified finding is never allowlisted,
  so a fixture that turns into a live credential fails even when its tuple is
  listed. Entries key on a commit, so a working-tree finding never matches one.
  An unused entry warns rather than fails, keeping a stale entry visible
  without breaking a scan that legitimately no longer reaches it. A malformed
  allowlist is refused rather than applied loosely: every field is required,
  unknown keys are rejected, and `commit` must be a full 40-character lowercase
  SHA, because a short SHA or a ref can come to mean something else.

  Findings never reach the log. With an allowlist configured, the scan writes
  its JSON to a private temporary file that the checker reads and the step
  deletes, and the report names only the detector, verification state, commit,
  path and line. Matching uses the runner's `jq`, whose absence fails the step
  before scanning rather than skipping the check.

  The gate fails closed on disagreement. If TruffleHog reports results but the
  checker finds none in the file, the step fails instead of reading that as a
  clean scan. With an allowlist set, output formats that would replace the
  JSON being matched are refused rather than silently dropped.

- `lint-text.yml` accepts `cspell-config` and `cspell-files`, matching the
  `config` and `files` inputs `run-cspell` already has. `cspell-config`
  passes `--config` instead of relying on auto-discovery and suppresses the
  cspell half of `preset`; `cspell-files` replaces the `.` argument with
  newline-delimited files and globs. Both default to today's behavior. The
  extra-dictionary self-tests now use them to assert that a skipped install
  fails the job (#105)
- `run-rust-ci.yml` takes `audit-checksums` and `llvm-cov-checksums`,
  `<sha256>  <version>  <target triple>` lines defaulting to the committed
  digests for the pinned versions. cargo-audit and cargo-llvm-cov publish
  no checksum file upstream, and until now a `supported_version` guard
  refused every version but the one whose digests this repo shipped, so
  `audit-version` and `llvm-cov-version` accepted exactly one value each
  and every bump of either broke any caller that had pinned them. A
  caller can now move either version by supplying its digests, and a
  version with no matching entry is still refused before anything is
  downloaded. **Anyone who pinned `audit-version` or `llvm-cov-version`
  explicitly must now pass that version's checksums alongside it, or drop
  the input to take the default**. See
  [the v4 migration guide](docs/migrations/v4.md#rust-tool-versions-now-need-their-checksums)
  (#61)
- `run-ci.yml` gains a `rust-tool-installs` job covering those two
  install blocks on all four supported target triples: the committed
  defaults install and report their version, an unknown version is
  refused before any download, and a digest that does not match its
  archive is refused after one. Nothing previously exercised
  `run-rust-ci.yml`, so its committed digests reached releases unverified
  (#61)

### Changed

- **Breaking:** Every ordinary data and argument input now reaches its shell
  step through an `env:` mapping instead of being interpolated into `run:`
  shell source.
  `test-flags` and `codecov-files` in `run-go-ci.yml`, `codecov-files` in
  `run-rust-ci.yml`, and `goreleaser-args` in `release-go-binaries.yml` were
  the remaining sites, so a caller-supplied value can no longer execute a
  command or change shell syntax. Only the explicit command inputs
  `scrut-setup-cmd`, `scrut-build-cmd` and `build-command` still run through
  `run:`, and the new `workflow-arg-binding` CI job enforces that allowlist
  against every workflow and action (#115, #95)

  Values the shell previously expanded now arrive literally, so a caller
  passing one must update their workflow file. A glob such as
  `--config configs/*.yml` is passed through unexpanded; name the file
  instead, or let the tool glob. `$VAR`, `$(command)`, backticks and `~` are
  no longer expanded; set the value from the caller's own expression. Quoting
  inside the value never worked and still does not: `--foo "a b"` tokenizes to
  `--foo`, `"a`, `b"`. Conversely, `codecov-files` may now contain spaces,
  which previously broke the command. See
  [the v4 migration guide](docs/migrations/v4.md)

- **Breaking:** Argument, flag, path-list and target-list inputs now reject a
  value containing a newline with an `::error::` diagnostic instead of
  silently using only its first line. `read -r -a` stops at the first newline,
  so a multi-line `test-flags`, `goreleaser-args`, `test-args`, `clippy-args`,
  `extra-components`, `build-args`, `fmt-paths`, `cross-targets` or `targets`
  previously lost every line after the first (#115)

- **Breaking:** `run-zig-ci.yml`'s `cross-targets` and
  `release-zig-binaries.yml`'s `targets` now split into an explicit quoted
  array rather than relying on unquoted word splitting, which glob-expanded
  each target triple against the working directory. Both now reject an empty
  or whitespace-only list with a diagnostic naming the input, as does
  `run-rust-ci.yml`'s `extra-components`. `run-zig-ci.yml` previously built
  nothing and reported success; `release-zig-binaries.yml` failed later in its
  checksum step with `shasum: *: No such file or directory` (#115)
- Bump pinned tool defaults to current latest stable releases (#61):
  - golangci-lint 2.11.4 → 2.13.2
  - trufflehog 3.95.2 → 3.97.5
  - GoReleaser 2.15.4 → 2.18.2
  - codecov CLI 11.2.8 → 11.3.1
  - cargo-deny 0.19.4 → 0.20.2 (0.x bump treated as breaking; the CLI
    refactor dropped deprecated flags this repo never passes, and the new
    `bans.std-replacements` lint can report findings against a consumer's
    `deny.toml`)
  - cargo-nextest 0.9.133 → 0.9.145
  - uv 0.11.8 → 0.12.17 (0.x bump; the surface used here is unaffected by
    0.12.0's changes to `uv init`, legacy source distribution archive
    formats and pre-release resolution)
  - shfmt 3.13.1 → 3.14.1 (new hardcoded SHA-256 checksums; upstream
    still publishes no checksum file)
  - cargo-audit 0.22.1 → 0.22.2 (new committed SHA-256 checksums)
  - cargo-llvm-cov 0.8.5 → 0.9.1 (new committed SHA-256 checksums. Its
    `--show-missing-lines` output change does not reach `run-rust-ci.yml`,
    which runs `--lcov --output-path`)
  - Node.js 24 LTS 24.15.0 → 24.21.0
- Bump reuse 5.0.2 → 6.2.0. Listed separately from the bumps above
  because it is the one that changes what `run-reuse` reports for every
  consumer. `reuse lint` now reads entire files rather than the first
  4 KiB, so REUSE information deeper in a file is found and may need
  `REUSE-IgnoreStart` and `REUSE-IgnoreEnd` to suppress; a new Invalid
  SPDX License Expressions criterion can fail a repository that previously
  passed; and the Bad licenses criterion now examines only `LICENSES/`.
  `requirements/reuse.in` now asks for `reuse[charset-normalizer]`, since
  reuse 6 requires `python-magic` against the runner's `libmagic`, which
  no manifest can pin, and needs a declared fallback when that import
  fails. See
  [the v4 migration guide](docs/migrations/v4.md#reuse-lint-reports-more-than-it-used-to)
  (#61)
- `lint-shell.yml` still discovers shell scripts one tracked path at a
  time. shfmt 3.14.1 fixes the `-f=0` defect that motivated the loop, but
  `shfmt-version` is caller-overridable, so an older shfmt can still reach
  that code path (#61)
- Updated pinned GitHub Actions: `github/codeql-action` v4.38.0 to
  v4.38.1 and `crate-ci/typos` v1.50.1 to v1.50.2, both patch releases
  (#131)
- Updated the pinned npm lint toolchain `lint-text.yml` installs: cspell
  10.3.0 to 10.3.3 and Prettier 3.9.6 to 3.9.8 (#122, #130)

### Fixed

- TruffleHog scans fail on reported findings. `run-trufflehog` and
  `scan-for-secrets.yml` pass `--fail`, so a scan reporting a verified or
  unknown result exits 183 instead of succeeding. Callers already passing
  `--fail` or `--no-update` through `args` no longer produce a duplicate flag.
  These fixes landed after v3.2.0 and appear in a release here for the first
  time (#111)
- TruffleHog scans keep the checksum-verified version they installed.
  `--no-update` stops the binary from replacing the pinned version mid-scan
  with whatever upstream had published, which defeated both the pin and its
  checksum (#111)
- `lint-text.yml` runs every enabled linter after setup succeeds even when
  an earlier linter fails, reporting all findings in one run. Any linter
  failure still fails the job; setup failure and cancellation prevent
  subsequent checks (#112)
- Scrut installation on Linux arm64 and macOS x86-64 now builds v0.4.3
  from a pinned source commit with a reviewed archive checksum, Rust 1.97.1
  and a committed dependency lockfile. Upstream's release archives contain
  executables for the wrong architecture. The exception covers `set-up-scrut`,
  `run-scrut-tests.yml`, `run-go-ci.yml` and `run-zig-ci.yml`; source builds
  report the package version consistently. Native installation and historical
  asset audits cover all four supported platform combinations (#120)
- `run-zig-ci.yml` now format-checks `build.zig.zon` alongside `build.zig`
  and `src`. Existing callers with an unformatted or missing manifest now
  fail the default formatting job. The new `fmt-paths` input accepts a
  space-separated path list for other project layouts (#106)

## [3.2.0] - 2026-09-14

### Added

- `set-up-clap-validator` composite action: builds
  [clap-validator](https://github.com/free-audio/clap-validator), the
  conformance checker for CLAP audio plugins, from the commit given in
  `validator-rev` using the toolchain given in `rust-version`, caches the
  result, and adds it to `PATH`. Running `clap-validator validate` is left
  to the calling job. Outputs `install-dir` and `cache-hit`. Linux and
  macOS runners (#88)

  Both pins are required and have no defaults, and each must name one
  thing rather than something resolved later. `validator-rev` must be a
  full 40-character lowercase commit SHA, since a tag can be moved.
  `rust-version` must name one release for the same reason: `stable`,
  `beta` and `nightly` are refused, with or without a host triple, and so
  is a partial version such as `1.97`, which rustup reads as the newest
  `1.97.x`. A three-component version and a dated nightly are accepted.

  The cache key names the runner OS, the architecture, the image and both
  pins, with no `restore-keys`, so a partial match cannot supply a
  validator built from a different commit or against a different libc. The
  image is the userspace the build ran in, read from `/etc/os-release` or
  `sw_vers` rather than from the runner's `ImageOS`, which names the host
  VM and would read alike for every container on it; `image-label` names
  an environment that can describe itself through neither, and refines
  the derived value where there is one, since a distribution release is
  not the whole ABI. The derived halves are joined with a colon, which
  neither may contain and which `image-label` forbids, so a label can
  never spell a derived identifier and the colon count tells the three
  cases apart; callers labelling distinct environments must still make
  those labels distinct. A key past GitHub's 512-character limit is refused with
  a message naming the input that could shorten it.

  The build is kept clear of the caller's Cargo configuration, which the
  key does not describe. `CARGO_HOME` is action-owned, the build runs from
  a fresh `/tmp` directory so cargo's search of parent directories finds
  no `.cargo/config.toml` and a config in any ancestor of it fails the
  step, and the environment variables known to change
  what the compiler produces are cleared: `RUSTFLAGS`, the compiler and
  wrapper overrides in both spellings, and every
  `CARGO_TARGET_<triple>_RUSTFLAGS`, `_LINKER` and `_RUNNER`. That last
  part is a list rather than a boundary, so a `CARGO_PROFILE_*` override,
  or a variable Cargo adds later, still reaches the build. A cache hit
  installs no Rust toolchain and compiles nothing.

- `install-cspell-dictionaries` composite action: installs cspell
  dictionary packages from npm beside an existing cspell installation,
  which is what lets a bare
  `"import": ["@cspell/dict-pt-pt/cspell-ext.json"]` in a config
  elsewhere in the tree resolve. Each
  `<name>@<version>  sha512-<base64>` entry is downloaded from its
  deterministic registry URL and verified against that integrity before
  npm reads it, so the registry supplies bytes rather than trust. A
  version range, a dist-tag, and a package declaring runtime
  dependencies are all refused (#72)
- `lint-text.yml` `extra-cspell-packages` input and `run-cspell`
  `extra-packages` input: name the dictionaries to add. cspell bundles
  English-family dictionaries and a few technical ones, so a repo whose
  prose is in another language previously could not use `run-cspell` at
  all: the dictionary it needed was in neither the pinned tool tree nor
  the workspace, and cspell flagged essentially every word (#72)
- `run-scrut-tests.yml` `setup-uv` and `uv-version` inputs: with
  `setup-uv: true`, the workflow installs the pinned uv release,
  verified against the SHA-256 upstream publishes beside the asset, and
  adds it to `PATH` before `scrut-setup-cmd` runs. A CLI shipped as PEP
  723 scripts no longer needs a hand-rolled runtime install in
  `scrut-setup-cmd`. Linux and macOS runners, amd64 and arm64 (#82)
- `tests/scrut/`: the repository's first scrut tests, run by
  `run-ci.yml` against `run-scrut-tests.yml` with `setup-uv` enabled, so
  the new install path is integration tested on every change (#82)
- `install-pinned-tool` composite action: installs a release binary
  pinned to an exact version and SHA-256 and adds it to `PATH`. The
  asset URL is a template over `{version}`, `{os}` and `{arch}`, with
  `os-names` and `arch-names` for upstreams that spell platforms
  differently; the expected digest comes from exactly one of `checksum`,
  `checksums` (per-platform `sha256sum` lines keyed by asset name) and
  `checksums-url-template` (an upstream checksum file); and
  `archive-member` extracts a single member from a tar archive. The
  asset is downloaded over https only, redirects included, to a file
  and verified before anything reads it. Linux and macOS runners, amd64
  and arm64 (#87)
- `set-up-shfmt` `checksums` input: `sha256sum`-format lines for the
  shfmt release binaries, defaulting to v3.13.1 on four platforms.
  Overriding `version` together with `checksums` installs any shfmt
  release, where the action used to refuse every version but 3.13.1
  (#87)
- `lint-shell.yml` `shfmt-checksums` input: `sha256sum`-format lines
  for the shfmt release binaries, defaulting to v3.13.1's. Overriding
  `shfmt-version` together with `shfmt-checksums` lints with any shfmt
  release, where the workflow used to refuse every version but 3.13.1
  (#87)
- `set-up-shellcheck` composite action: installs shellcheck pinned to
  `version` (default 0.11.0) and verified against `checksums`, whose
  default covers v0.11.0 on Linux and macOS, amd64 and arm64. shellcheck
  publishes no checksum file and no digests in its release notes, so
  overriding `version` needs `checksums` with it. Built on
  `install-pinned-tool` (#85)
- `lint-shell.yml` and `lint-github-actions.yml` `shellcheck-version`
  and `shellcheck-checksums` inputs, with the same defaults (#85)

### Changed

- `set-up-actionlint` and `set-up-shfmt` install through
  `install-pinned-tool`'s script instead of their own inline copies.
  Their inputs, defaults, and checksum sources are unchanged apart from
  `set-up-shfmt`'s new `checksums` input (#87)
- `lint-shell.yml` and `lint-github-actions.yml` install their tools by
  fetching `install-pinned-tool`'s script from
  `job.workflow_repository` at `job.workflow_sha`, the model
  `lint-text.yml` uses for its manifests, instead of carrying inline
  installers. Both now depend on those `job` context properties, which
  GitHub Enterprise Server does not populate, so neither is supported
  there: run the linters in your own job with `set-up-shellcheck`,
  `set-up-shfmt` and `set-up-actionlint` instead. A private fork of this
  repo cannot serve the script either (#87, #85)
- Updated pinned GitHub Actions: `actions/setup-node` to v7.0.0
  (#108), `actions/setup-go` to v7.0.0 (#110), `actions/checkout` to
  v7.0.1, `github/codeql-action` to v4.38.0, `actions/deploy-pages` to
  v5.0.1, `softprops/action-gh-release` to v3.0.3,
  `leanprover/lean-action` to v1.6.0, `Swatinem/rust-cache` to v2.9.2,
  `crate-ci/typos` to v1.50.1 (#107), and `dtolnay/rust-toolchain` to
  its 2026-09-12 master commit (#109)

  Both major bumps are ECMAScript module migrations with dependency
  upgrades, and each action still declares the Node 24 runtime, so no
  runner requirement changes. Three of these change behavior consumers
  can observe:

  - `actions/setup-node` v7 no longer exports a placeholder
    `NODE_AUTH_TOKEN` when `registry-url` is set and the variable is
    unset, so later steps see it unset rather than set to a dummy
    value. `publish-to-npm.yml` is unaffected: its install step never
    had a usable token, current npm leaves the unresolved reference in
    place rather than failing, and the publish step sets the secret
    itself.
  - `dtolnay/rust-toolchain` passes `--force-non-host` to rustup, so a
    toolchain naming a non-host triple installs and fails at the
    action's own `rustc` step instead of at install time. A toolchain
    for the runner's host is unaffected.
  - `crate-ci/typos` v1.49 and v1.50 carry the July and August 2026
    dictionary updates, so the typos job `run-rust-ci.yml` runs when
    `run-typos` is set may flag words that previously passed.

### Fixed

- `lint-github-actions.yml` installs a pinned, checksum-verified
  shellcheck and reports both tool versions before running actionlint,
  instead of leaving shellcheck to the runner image. actionlint shells
  out to shellcheck for every `run:` block, which is the only thing in
  that workflow that lints embedded shell, and with no shellcheck on
  `PATH` it skips all of them and still exits 0: a planted `SC2086`
  passed. On a runner image without ShellCheck, or a `runs-on` that
  lacks it, the job stayed green and silently stopped linting embedded
  shell (#85)

  The `ubuntu-latest` image ships ShellCheck 0.9.0, so a first run on
  this version can report findings from checks added in 0.10.0 and
  0.11.0 (SC2327 to SC2332 among them) that no consumer has seen yet.
  Fix them, add a `# shellcheck disable=` directive, or pin
  `shellcheck-version: 0.9.0` with that release's checksum while you
  work through them.

- `lint-shell.yml` lints with a pinned, checksum-verified shellcheck
  instead of the runner image's, so a runner image update no longer
  changes what it reports with no change to any version a consumer
  pinned, and it lints with the same shellcheck actionlint gets. The
  installer fetch now carries both tools' conditions rather than
  shfmt's alone. The same 0.9.0-to-0.11.0 jump applies to your tracked
  scripts (#85)

- `scan-for-secrets.yml`'s `validate-inputs` job and
  `deploy-to-pages.yml`'s `deploy` job apply their workflow's
  `timeout-minutes` input, as their sibling jobs already did. Both used
  to inherit GitHub's 360-minute default with no way for a caller to
  lower it. Neither workflow gains an input and no default changes.
  `deploy` shares `build`'s input because `timeout-minutes` bounds
  execution: time the job spends awaiting `github-pages` environment
  approval is governed by GitHub's separate 30-day approval limit
  instead, so the ceiling needs no allowance for an approver (#81)

## [3.1.1] - 2026-09-10

### Fixed

- `lint-text.yml` reads the workflow's own repository and commit from
  `job.workflow_repository` and `job.workflow_sha` instead of
  `github.job_workflow_sha`, which is not a real context property and
  always evaluates to the empty string. Every fetch of this repo's
  pinned manifests failed its guard, so on default inputs the workflow
  failed before any linter ran, in v3.0.0 (unconditionally) and v3.1.0
  (unless `use-consumer-versions: true` and no preset and no yamllint).
  The `job` context properties were added on 2026-09-03 (#83)
- `lint-text.yml` builds fetch URLs from `job.workflow_repository`
  rather than a hardcoded `cboone/gh-actions`, so a fork calling its own
  copy fetches its own manifests instead of 404ing on SHAs that do not
  exist upstream. A private fork cannot serve them over
  `raw.githubusercontent.com`; use `use-consumer-versions: true` there
- `lint-text.yml` checks for a local markdownlint or cspell config
  before checking the job context, so a consumer that sets `preset` and
  also ships its own config no longer fails on a value it never uses
- `lint-text.yml` retries its manifest fetches and logs the URL it
  fetches from, so a failure of this class is diagnosable from the run
  log

## [3.1.0] - 2026-09-10

### Added

- `lint-text.yml` `use-consumer-versions` input (boolean, default
  `false`): opt-in to install markdownlint-cli2, Prettier, and cspell
  from the consumer repo's own `package.json` + `package-lock.json`
  via `npm ci` in the workspace, instead of the versions pinned in
  this gh-actions repo. npm still enforces per-package sha512
  integrity, so the trust boundary becomes the consumer's reviewed
  lockfile. Use this when local linting and CI must agree on tool
  versions (e.g. when a consumer pins `cspell ^8` locally but the
  pinned default is v10, and dictionary differences across major
  versions cause divergent results). yamllint is unaffected (#34)
- `lint-text.yml` `preset` input with a `lean-math` value: opt-in
  Pandoc-flavored academic Markdown config bundle. When set and the
  consumer doesn't ship a local markdownlint or cspell config, the
  workflow fetches the preset from this repo (at the workflow's own
  SHA, same supply-chain model as the npm/yamllint installs) and
  drops it into the workspace so the tools auto-discover it. A local
  consumer config always takes precedence. Preset sources live at
  `presets/lean-math/`. Targets Lean + paper-backed formalization
  repos (`shannon-entropy`, `zhang-yeung-inequality`,
  `strength-model`) that previously carried duplicated configs
- `homebrew-desc` input on `release-rust-binaries.yml` for setting the
  generated Homebrew formula's `desc` field. Defaults to the binary
  name when empty, preserving prior behavior (#30)
- `homebrew-depends-on` input on `release-rust-binaries.yml` for
  declaring Homebrew formula dependencies. Each non-empty line of the
  newline-delimited value becomes a separate `depends_on` statement in
  the generated formula: lines starting with `:` are emitted as Ruby
  symbols (e.g. `:macos`), other lines are emitted as quoted strings
  (e.g. `openssl`). Needed for macOS-only tools and tools with
  library dependencies (#31)
- Fail-fast validation in `release-rust-binaries.yml` when
  `homebrew-depends-on` declares `:macos` or `:linux` but the `targets`
  matrix includes a target for the other platform. Prevents generating a
  self-contradictory formula that restricts to one OS while shipping
  bottles for the other (#56)
- Reusable workflow `run-lean-ci.yml` for Lean Lake projects using
  `leanprover/lean-action`. Builds via lean-action (with elan toolchain
  caching and pass-through control over the Mathlib build cache), then
  runs `lake lint` and `lake test` directly so consumers' own Lake
  targets are exercised. Replaces the duplicated single-file Lean CI
  configurations in downstream Lean repos (#36)
- `homebrew-test` input on `release-rust-binaries.yml` for supplying
  custom Ruby code to the generated formula's `test do ... end` block.
  Defaults to `system bin/"<binary>", "--version"` when empty (#55)
- Explicit validation of consumer-installed lint tools in
  `lint-text.yml` when `use-consumer-versions` is true. Each enabled
  tool missing from the consumer's lockfile now fails with a targeted
  `::error::` annotation naming the fix, instead of a bare
  `command not found` later in the run (#60)

### Fixed

- `lint-text.yml` runs `npm ci` only when at least one npm-backed tool
  is enabled, and forces dev dependencies so tools resolve when the
  consumer's environment sets `NODE_ENV=production` (#57)
- `lint-text.yml` applies a preset only for tools the caller actually
  enabled, so a `preset` with `run-cspell: false` no longer fetches a
  cspell config the run never uses (#51)
- `release-rust-binaries.yml` escapes `homebrew-desc` for Ruby
  double-quoted strings, so a description containing a quote or
  backslash no longer produces a formula Ruby cannot parse (#53)
- `run-lean-ci.yml` drops the `lean-toolchain-file` input, which
  suggested control it never had: lean-action reads `lean-toolchain`
  from the repository root regardless (#52)
- Prettier formats Markdown again. The `*.md` exclusion in
  `.prettierignore` rested on markdownlint-cli2 `--fix` handling table
  alignment, which it does not: MD060 has no auto-fix at any version.
  Nothing was aligning tables and the linter could only complain.
  `docs/plans/done/` stays excluded, since reformatting historical
  records can mangle template syntax inside fenced blocks (#84)

### Changed

- Updated the pinned npm lint toolchain: cspell 10.0.0 to 10.3.0,
  markdownlint-cli2 0.22.1 to 0.23.2, Prettier 3.8.3 to 3.9.6 (#90)
- Updated pinned GitHub Actions: `actions/checkout` to v7.0.0 (#70),
  `actions/cache` to v6.1.0 (#74), `github/codeql-action` to v4.37.1,
  `softprops/action-gh-release` to v3.0.2, `crate-ci/typos` to v1.48.0
  (#78), and `dtolnay/rust-toolchain` to its 2026-06-30 master commit
  (#76)

  Three of these change behavior consumers can observe:

  - `actions/checkout` v7 refuses to check out a fork's pull request
    under `pull_request_target` or `workflow_run`. Callers that invoke
    these reusable workflows from either trigger against a fork PR will
    need to restructure those jobs.
  - markdownlint-cli2 0.23 drops support for end-of-life Node 20.
    Callers overriding `lint-text.yml`'s `node-version` to 20 must move
    to 22 or later; the default is unaffected.
  - `crate-ci/typos` v1.48 carries new dictionaries, so `run-typos`
    jobs may flag words that previously passed.

### Security

- Cleared every open npm advisory in the pinned lint toolchain, from
  four high and one moderate down to zero. markdownlint-cli2 0.23.2
  resolves the `js-yaml`, `markdown-it` and `linkify-it` findings
  through its own pinned dependencies; a `smol-toml` override scoped to
  `markdownlint-cli2` covers GHSA-7w5x-hrqm-74c2, which its exact pin
  leaves npm no room to resolve. The override is deliberately scoped
  rather than repo-wide, so cspell keeps resolving inside its own
  declared `^1.8.0` range (#90)

## [3.0.0] - 2026-05-02

### Changed

- **Breaking:** Renamed public composite action paths and reusable workflow
  filenames to use imperative phrasing, including `setup-*` action paths to
  `set-up-*` and `gh-release` to `create-gh-release`. Consumers upgrading to
  the first release with this change must update `uses:` strings. See the
  README migration table for the complete old-to-new path mapping. Old paths
  remain available only on older release tags that predate the rename.

## [2.2.0] - 2026-05-01

### Added

- `zig-version-file` input on `zig-ci.yml` and `zig-release.yml`,
  mirroring `node-version-file` / `go-version-file` /
  `ruby-version-file` in upstream setup actions. Callers can now point
  the workflow at a `.zon` file (typically `build.zig.zon`) and the
  workflow reads `.minimum_zig_version` from it instead of requiring a
  literal version string. `zig-version` is now optional (default
  `""`); when both inputs are set, `zig-version` takes precedence.
  When neither is set, `mlugg/setup-zig` falls back to its own
  auto-detection (#41)
- `actions/gh-release` composite action wrapping `gh release create`.
  Replaces `softprops/action-gh-release` for callers that just need
  asset uploads, auto-generated release notes, and draft/prerelease
  flags. The `gh` CLI is preinstalled on every GitHub-hosted runner, so
  no binary download or checksum table is needed; supply-chain risk is
  the same as the runner itself
- `actions/run-cspell` composite action wrapping the `cspell` CLI.
  Replaces `streetsidesoftware/cspell-action` for repos that already
  lint text via the `text-lint.yml` reusable workflow but want a
  standalone action. Installs cspell from this repo's sha512-pinned
  `package-lock.json` (same trust path as `text-lint.yml`) and
  registers a problem matcher
  (`actions/run-cspell/cspell-matcher.json`) so cspell's default
  `path:line:col - Unknown word` output surfaces as inline
  pull-request annotations
- `actions/run-reuse` composite action wrapping the `reuse` CLI
  (default `reuse lint`) for SPDX/REUSE compliance. Replaces
  `fsfe/reuse-action` with the same hash-pinned uv install pattern
  used for yamllint: every transitive dependency of reuse is
  sha256-pinned in `requirements/reuse.txt` via
  `uv pip compile --generate-hashes`
- `requirements/reuse.in` source manifest and
  `requirements/reuse.txt` autogenerated hash-pinned lockfile pinning
  reuse 5.0.2 and its transitive dependencies
- Dependabot config (`.github/dependabot.yml`) covering both
  `github-actions` (workflows + composite actions with external `uses:`)
  and `npm` (devDependencies). Minor/patch updates are grouped weekly;
  major updates open individual PRs
- Scheduled `check-tool-versions.yml` workflow that runs weekly, queries
  upstream releases for every tool Dependabot does not track (binary
  downloads, hardcoded checksum tables, yamllint, Node LTS), and opens
  or updates a single tracking issue when something is outdated. Closes
  the issue automatically when versions are current
- `scripts/check-tool-versions.py`: uv-managed Python script that powers
  the scheduled check. Hardcodes the current pinned versions and notes
  which bumps require regenerating SHA-256 checksums or hash files
- `requirements/yamllint.txt`: hash-pinned (`uv pip compile
--generate-hashes`) requirements for yamllint and its transitive
  dependencies
- `.github/actionlint.yaml`: ignore-pattern for the
  `github.job_workflow_sha` context property, which actionlint v1.7.12
  does not yet recognise but GitHub provides at runtime in reusable
  workflows

### Changed

- **Hardening** `cargo-llvm-cov` install in `rust-ci.yml`: replace
  `cargo install cargo-llvm-cov@0.8.5 --locked` (which trusted crates.io
  registry integrity) with a checksum-verified binary download from
  `taiki-e/cargo-llvm-cov` releases. Hardcoded SHA-256 table mirrors
  the scrut / cargo-audit / shfmt pattern; new `llvm-cov-version`
  input. Eliminates the registry-only trust path for coverage runs.
- **Hardening** yamllint in `text-lint.yml` and the local `make
lint-yaml`: switch from `uv tool run --from "yamllint==X.Y.Z"`
  (PyPI-registry-only trust) to `uv pip install --require-hashes -r
requirements/yamllint.txt` against a hash-pinned manifest. The
  workflow downloads the manifest from this repo at the workflow's own
  SHA (`github.job_workflow_sha`), so a tampered registry response
  cannot pass the per-package hash check. Every transitive dep of
  yamllint is hash-pinned.
- **Hardening** npm tool installs in `text-lint.yml`: replace `npm
install --global "<pkg>@<version>"` (no integrity check) with `npm ci`
  against this repo's checked-in `package-lock.json`, fetched at the
  workflow's own SHA. Per-package sha512 integrity is now enforced for
  markdownlint-cli2, prettier, and cspell.
- **rust-version pinning**: `rust-ci.yml` and `rust-release.yml`
  default `rust-version` to empty and add a `rust-toolchain-file`
  input (default `rust-toolchain.toml`). A new pre-step resolves the
  toolchain by reading the consumer's `rust-toolchain.toml` channel
  value when `rust-version` is empty. At least one of the two must
  resolve; otherwise the workflow fails fast with a clear error. This
  matches dtolnay/rust-toolchain's lack of native toolchain-file
  support and lets the consumer repo (e.g. `ke`) pin the Rust
  toolchain in the standard idiomatic place.
- **README**: replace every `cboone/gh-actions/...@main` example with
  `@v2.2.0` (the current released tag) and remove `@main` from the
  Pinning section. Branch refs are no longer suggested as a "for
  testing" option; consumers must pin to a release tag.
- Pin `package.json` devDependencies to exact versions (no `^`/`~`) so a
  fresh `npm install` cannot float
- Annotate `dtolnay/rust-toolchain` SHA pins with the upstream commit
  date (the action does not publish semver tags)
- Move default `node-version` from major-only `"22"` to a specific Node
  24 LTS release `"24.15.0"` in `text-lint.yml`, `npm-publish.yml`, and
  `pages-deploy.yml`
- Bump pinned tool defaults to current latest stable releases:
  - actionlint 1.7.11 → 1.7.12
  - golangci-lint 2.11.3 → 2.11.4
  - gitleaks 8.30.0 → 8.30.1
  - trufflehog 3.93.8 → 3.95.2
  - GoReleaser 2.14.3 → 2.15.4
  - cargo-deny 0.19.0 → 0.19.4
  - cargo-nextest 0.9.132 → 0.9.133
  - shfmt 3.13.0 → 3.13.1 (new hardcoded SHA-256 checksums; upstream
    still does not publish a checksum file)
  - yamllint 1.37.1 → 1.38.0
  - codecov CLI 10.4.0 → 11.2.8 (major bump)
  - uv 0.10.9 → 0.11.8
  - cspell 9.7.0 → 10.0.0 (major bump)
  - markdownlint-cli2 0.21.0 → 0.22.1
  - prettier 3.8.1 → 3.8.3
- Bump pinned third-party action SHAs to current latest releases:
  - actions/setup-node v6 → v6.4.0
  - actions/setup-go v6 → v6.4.0
  - actions/upload-artifact v7 → v7.0.1
  - github/codeql-action v4 → v4.35.2
  - crate-ci/typos v1.44.0 → v1.45.2
  - peter-evans/create-pull-request v7 → v8.1.1 (Node 20 → 24 runtime;
    no input changes)
  - softprops/action-gh-release v2 → v3.0.0 (Node 20 → 24 runtime; no
    input changes)
- Disable `MD060` (table-column-style) in `.markdownlint-cli2.jsonc`.
  This rule is new in markdownlint v0.40 (shipped with markdownlint-cli2
  0.22.1) and we don't enforce table-pipe alignment
- Convert one emphasis-as-heading line in
  `docs/plans/done/2026-03-27-add-zig-workflows.md` to a real `####`
  heading so MD036 stays enabled

### Documentation

- Add **Pinning Policy and Trust Model** section to `AGENTS.md`
  describing how each kind of dependency is pinned (commit SHA, archive
  checksum, registry exact version, lockfile integrity). Document the
  Rust toolchain as the one explicit version-pinning exception:
  `rust-version` defaults to empty and `rust-toolchain-file` (default
  `rust-toolchain.toml`) lets the consumer repo control whether the
  channel is pinned (e.g., `"1.84.0"`) or floats with rustup
  (`"stable"`). `node-version` defaults to an exact `"24.15.0"` and is
  not a floating default; callers may override

## [2.1.4] - 2026-04-27

### Fixed

- Hardcode SHA-256 checksums for shfmt v3.13.0 in `setup-shfmt` action and
  `shell-lint.yml` workflow. shfmt upstream stopped publishing
  `sha256sums.txt` starting with v3.13.0 (mvdan/sh#1283, mvdan/sh#1309),
  which broke installation with `curl: (22) ... 404` for every consumer
  pinned to the default version (#38)

### Changed

- Update README defaults for `setup-shfmt` and `shell-lint.yml` from
  `3.12.0` to `3.13.0` to match the actual action and workflow defaults
- Document in README that only the pinned `shfmt` version is supported by
  `setup-shfmt` and `shell-lint.yml`, and that overriding it requires
  updating the hardcoded SHA-256 checksums first (#39)
- Add Copilot instruction documenting shfmt's hardcoded checksum approach,
  version-bump procedure, and asset name + digest cross-check command

## [2.1.3] - 2026-03-30

### Fixed

- Replace `--version` check with executable test (`test -x`) in run-markscribe
  action (#33)

### Changed

- Add Copilot instruction for markscribe `test -x` verification

## [2.1.2] - 2026-03-28

### Fixed

- Extract only markscribe binary from archive instead of entire tarball contents
- Use `--strip-components=1` for markscribe tar extraction to match expected
  install layout

## [2.1.1] - 2026-03-27

### Fixed

- Use exact version in major bump example and soften release wording

### Changed

- Versioning strategy now uses only exact version tags (e.g., `v2.2.0`);
  floating major tags (`v1`, `v2`) are discontinued
- Add single instructions file rule to Copilot instructions

## [2.1.0] - 2026-03-27

### Added

- Reusable workflows `rust-ci.yml` for Rust test, clippy, fmt, deny, audit,
  and typos checking, and `rust-release.yml` for Rust binary releases with
  matrix builds (#21)
- Reusable workflow `zig-ci.yml` for Zig test, format, build, cross-compile,
  and scrut testing (#22)
- Reusable workflow `zig-release.yml` for Zig cross-compile releases with
  GitHub Release artifact uploads (#22)
- Reusable workflow `create-release.yml` for creating GitHub Releases from
  changelog files in Keep a Changelog format
- Self-hosting workflow `release.yml` to create releases on version tag pushes
- Composite action `run-markscribe` to install and run the markscribe README
  template generator with SHA-256 checksum verification
- Composite action `create-pull-request` as a SHA-pinned wrapper around
  peter-evans/create-pull-request for centralized version management
- Reusable workflow `codeql.yml` for GitHub CodeQL security analysis with
  conditional Go setup and SHA-pinned action references
- Reusable workflow `scrut.yml` for standalone scrut CLI snapshot testing
  without Go dependencies
- Exclude `.md` files from Prettier formatting, rely on markdownlint-cli2
  instead

### Changed

- SHA-pin all external action references (`actions/checkout`,
  `actions/setup-go`, `actions/setup-node`, `actions/configure-pages`,
  `actions/upload-pages-artifact`, `actions/deploy-pages`) across all
  reusable workflows
- Bump pinned tool versions across all actions and workflows
- Update GitHub Actions (`actions/checkout`, `actions/setup-go`, etc.) to
  latest major versions
- Bump `picomatch` and `flatted` dev dependencies

### Fixed

- Validate `scrut-env` KEY=VALUE format in `zig-ci.yml`
- SHA-pin `actions/checkout` in `create-release.yml`
- Match markscribe checksum by exact filename to avoid false matches
- Validate `SCRUT_ENV` format in reusable workflows
- Clarify `category-prefix` input description for single-language use
- Address Copilot PR review feedback for Rust workflows and other workflows

## [2.0.0] - 2026-03-09

### Changed

- go-ci.yml now requires consuming repos to have a Makefile with targets:
  `vet`, `test`, and optionally `lint`, `build`, `fmt` (matching enabled jobs)
- go-ci.yml test job runs `make vet` and `make test` instead of direct Go
  commands
- go-ci.yml lint job runs `make lint` instead of `golangci-lint run ./...`
- go-ci.yml build job runs `make build` instead of `go build`
- go-ci.yml format-check job runs `make fmt` instead of inline gofmt/goimports
- go-ci.yml `test-flags` input now only applies when `coverage` is enabled
- Updated `actions/setup-go` from v5 to v6 across go-ci.yml and go-release.yml

### Removed

- go-ci.yml `use-makefile` input (Makefile is now the only execution mode)
- go-ci.yml `build-flags` input (build flags belong in each repo's Makefile)

## [1.0.0] - 2026-03-08

### Added

- Composite action `setup-golangci-lint` to install golangci-lint with a pinned version
- Composite action `setup-goreleaser` to install GoReleaser with a pinned version
- Composite action `setup-scrut` to install scrut CLI testing tool with a pinned version
- Composite action `setup-actionlint` to install actionlint with a pinned version
- Composite action `setup-shfmt` to install shfmt with a pinned version
- Composite action `run-gitleaks` to install and run gitleaks secret scanner
- Composite action `run-trufflehog` to install and run trufflehog secret scanner
- Reusable workflow `go-ci.yml` for Go testing, linting, building, scrut tests, and format checking
- Reusable workflow `go-release.yml` for GoReleaser-based releases
- Reusable workflow `secret-scan.yml` for gitleaks and/or trufflehog scanning
- Reusable workflow `text-lint.yml` for markdownlint, Prettier, cspell, and yamllint
- Reusable workflow `shell-lint.yml` for ShellCheck and shfmt
- Reusable workflow `github-lint.yml` for actionlint
- Reusable workflow `pages-deploy.yml` for GitHub Pages build and deploy
- Reusable workflow `npm-publish.yml` for npm package publishing
- SHA-256 checksum verification for all tool downloads (except scrut, which lacks upstream checksums)
- Cross-platform support for Linux and macOS runners
- Codecov coverage upload support in go-ci workflow
- gofmt and goimports format checking in go-ci workflow
- Scrut inputs for custom build commands (`scrut-build-cmd`), environment variables (`scrut-env`), test directories (`scrut-test-dir`), and setup commands (`scrut-setup-cmd`)
- Self-hosting workflows (`ci.yml`, `gitleaks.yml`, `trufflehog.yml`) as integration tests
- Linter and formatter configuration (markdownlint, Prettier, cspell, editorconfig)

### Fixed

- Install tools to `RUNNER_TEMP` and add to `GITHUB_PATH` instead of writing to system paths
- Extract scrut binary with `--strip-components=1` for correct tarball layout
- Resolve relative paths in `scrut-env` values to absolute paths
- Use `github.token` directly in go-release workflow instead of requiring callers to pass `GITHUB_TOKEN`
- Split composite action args with `read -r -a` using newline-delimited inputs
- Make reusable workflows self-contained (no references to local composite actions)
- Pin all tool versions to exact patch releases with SHA-256 checksum verification
- Avoid running tests twice when coverage is enabled
- Install Codecov CLI for the correct runner OS

[unreleased]: https://github.com/cboone/gh-actions/compare/v5.0.0...HEAD
[5.0.0]: https://github.com/cboone/gh-actions/compare/v4.1.0...v5.0.0
[4.1.0]: https://github.com/cboone/gh-actions/compare/v4.0.0...v4.1.0
[4.0.0]: https://github.com/cboone/gh-actions/compare/v3.2.0...v4.0.0
[3.2.0]: https://github.com/cboone/gh-actions/compare/v3.1.1...v3.2.0
[3.1.1]: https://github.com/cboone/gh-actions/compare/v3.1.0...v3.1.1
[3.1.0]: https://github.com/cboone/gh-actions/compare/v3.0.0...v3.1.0
[3.0.0]: https://github.com/cboone/gh-actions/compare/v2.2.0...v3.0.0
[2.2.0]: https://github.com/cboone/gh-actions/compare/v2.1.4...v2.2.0
[2.1.4]: https://github.com/cboone/gh-actions/compare/v2.1.3...v2.1.4
[2.1.3]: https://github.com/cboone/gh-actions/compare/v2.1.2...v2.1.3
[2.1.2]: https://github.com/cboone/gh-actions/compare/v2.1.1...v2.1.2
[2.1.1]: https://github.com/cboone/gh-actions/compare/v2.1.0...v2.1.1
[2.1.0]: https://github.com/cboone/gh-actions/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/cboone/gh-actions/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/cboone/gh-actions/releases/tag/v1.0.0
