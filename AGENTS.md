# Gh Actions

## Overview

A collection of reusable GitHub Actions composite actions and reusable workflows
for CI/CD pipelines. All tool downloads use pinned versions with SHA-256 checksum
verification. The repository is consumed by 26+ downstream repos.

## Repository Structure

```text
actions/
  create-gh-release/     # Create GitHub Release with gh
  create-pull-request/   # Wrapper: peter-evans/create-pull-request (SHA-pinned)
  install-cspell-dictionaries/ # Install cspell dictionary packages pinned to a version and sha512
  install-pinned-tool/   # Install a release binary pinned to a version and SHA-256
  run-cspell/            # Install and run cspell spell checker
  run-gitleaks/          # Install and run gitleaks secret scanner
  run-markscribe/        # Install and run markscribe README template generator
  run-reuse/             # Install and run REUSE compliance checker
  run-trufflehog/        # Install and run trufflehog secret scanner
  set-up-actionlint/     # Install actionlint
  set-up-clap-validator/ # Build clap-validator from a pinned commit
  set-up-golangci-lint/  # Install golangci-lint
  set-up-goreleaser/     # Install GoReleaser
  set-up-scrut/          # Install scrut CLI test runner
  set-up-shellcheck/     # Install shellcheck
  set-up-shfmt/          # Install shfmt
.github/
  workflows/
    analyze-with-codeql.yml                 # Reusable: GitHub CodeQL security analysis
    create-gh-release-from-changelog.yml    # Reusable: create GitHub Release from changelog
    deploy-to-pages.yml                     # Reusable: GitHub Pages build and deploy
    lint-github-actions.yml                 # Reusable: actionlint and shellcheck
    lint-shell.yml                          # Reusable: ShellCheck and shfmt
    lint-text.yml                           # Reusable: markdownlint, Prettier, cspell, yamllint
    publish-to-npm.yml                      # Reusable: npm publish to registry
    release-go-binaries.yml                 # Reusable: GoReleaser release
    release-rust-binaries.yml               # Reusable: Rust binary release with matrix builds
    release-zig-binaries.yml                # Reusable: Zig cross-compile release
    run-go-ci.yml                           # Reusable: Go test, lint, build, scrut, format check
    run-lean-ci.yml                         # Reusable: Lean lake build, lake lint, lake test
    run-rust-ci.yml                         # Reusable: Rust test, clippy, fmt, deny, audit, typos
    run-scrut-tests.yml                     # Reusable: scrut CLI snapshot tests
    run-zig-ci.yml                          # Reusable: Zig test, format, build, cross-compile, scrut
    scan-for-secrets.yml                    # Reusable: gitleaks and/or trufflehog scanning
    create-gh-release-on-tag.yml            # Self-hosting: runs changelog release on version tags
    run-ci.yml                              # Self-hosting: runs the lint workflows and action self-tests
    scan-for-secrets-with-gitleaks.yml      # Self-hosting: runs scan-for-secrets with gitleaks
    scan-for-secrets-with-trufflehog.yml    # Self-hosting: runs scan-for-secrets with trufflehog
  copilot-instructions.md
docs/
  migrations/            # Major-version migration guides (vN.md)
  plans/                 # Plan documents (todo/ and done/)
  workflows/             # Per-reusable-workflow reference docs (<name>.md)
tests/
  fixtures/              # Inputs for the scrut self-test
  scrut/                 # scrut tests run-ci.yml runs against this repo
```

Each composite action also has a `README.md` next to its `action.yml`
(e.g. `actions/run-cspell/README.md`); see "Documentation layout" below
for details.

## Key Conventions

### Composite Actions vs. Reusable Workflows

Composite actions live in `actions/` and are referenced as
`cboone/gh-actions/actions/<name>@<ref>`. Reusable workflows live in
`.github/workflows/` and are called via `workflow_call`. A reusable
workflow cannot use a composite action from this repo by a `./` path,
which resolves against the caller's checkout. `lint-github-actions.yml`
and `lint-shell.yml` therefore fetch
`actions/install-pinned-tool/install-pinned-tool.sh` from
`job.workflow_repository` at `job.workflow_sha` and run it, the model
`lint-text.yml` uses for its manifests, which keeps the installer on the
workflow's own commit. The other reusable workflows inline their tool
installation. Composite actions reach sibling files in this repo through
`github.action_path`: `set-up-actionlint`, `set-up-shellcheck` and
`set-up-shfmt` run `../install-pinned-tool/install-pinned-tool.sh`.

### Naming

- Use imperative path names for local composite actions and reusable workflows.
- `set-up-*` actions install a tool and add it to `GITHUB_PATH` (install only).
- `run-*` actions install a tool and then execute it (install and run).
- `install-pinned-tool` is the generic installer the `set-up-*` actions build
  on: it takes a tool's URL template and checksum source as inputs rather
  than naming one tool.

### SHA-256 Checksum Verification

Every tool download verifies its SHA-256 checksum against upstream-published
checksum files. The exceptions are shellcheck, scrut, shfmt (3.13.0+),
cargo-audit, and cargo-llvm-cov, whose upstreams do not publish checksum
files suitable for this repo's pinning model; their checksums are committed
in this repo. shellcheck's and shfmt's are input defaults keyed by asset
name: `checksums` in `actions/set-up-shellcheck/action.yml` and
`actions/set-up-shfmt/action.yml`, `shellcheck-checksums` in `lint-shell.yml`
and `lint-github-actions.yml`, and `shfmt-checksums` in `lint-shell.yml`. The
others sit in case statements in the files that install them.

A tool a workflow depends on is installed here, never left to the runner
image, even one every supported image ships. Leaving it to the image floats
its version and can fail open: actionlint is the sharp case, since it skips
every `run:` block and still exits 0 when it cannot find shellcheck, so a job
that does not install one passes vacuously (#85). `run-ci.yml`'s
`Check actionlint runs shellcheck` step guards that integration by linting a
planted `SC2086`.

### Pinning Policy and Trust Model

A condensed summary lives in [README.md](README.md#trust-model-and-pinning).
This section is the canonical longer form.

The repo applies the strongest available pin to each kind of dependency
and refuses to fall back on third-party registry integrity alone for
anything that runs in CI.

- **GitHub Actions (`uses:`)**: pinned to a 40-char commit SHA with a
  `# vX.Y.Z` comment for human readability. `dtolnay/rust-toolchain`
  is the one external action without semver tags; it is annotated with
  `# master @ YYYY-MM-DD` instead.
- **Binary downloads via `curl`**: SHA-256 verified against an upstream
  checksum file or, where upstream does not publish one, against
  hardcoded checksums in this repo (currently shellcheck, scrut, shfmt,
  cargo-audit, cargo-llvm-cov). `actions/install-pinned-tool`
  implements that procedure once for any release binary.
- **Python tools (yamllint)**: installed via `uv pip install
--require-hashes -r requirements/yamllint.txt` against a manifest
  generated by `uv pip compile --generate-hashes`. Every transitive
  dep is hash-pinned. Workflows fetch the manifest at
  `job.workflow_repository` and `job.workflow_sha`, the repository and
  commit the workflow file itself came from, so a tampered PyPI
  response cannot pass the per-package hash check.
- **npm tools running in workflows** (markdownlint-cli2, prettier,
  cspell): installed via `npm ci` against the workflow repository's
  `package-lock.json`, fetched at the same `job.workflow_repository`
  and `job.workflow_sha`. Per-package sha512 integrity is enforced.
  `lint-text.yml` exposes a `use-consumer-versions: true` opt-in that
  runs `npm ci` against the consumer's own committed
  `package-lock.json` instead; npm still enforces sha512 integrity,
  but the trust boundary becomes the consumer's reviewed lockfile
  rather than this repo. Use this when CI must agree with the versions
  a consumer pins locally.
- **Caller-named cspell dictionaries**: cspell bundles only
  English-family dictionaries and a few technical ones, so any other
  natural language needs a package no lockfile here can pin for every
  consumer. `lint-text.yml`'s `extra-cspell-packages` and
  `run-cspell`'s `extra-packages` take
  `<name>@<version>  sha512-<base64>` entries, and
  `actions/install-cspell-dictionaries` downloads each tarball from its
  deterministic registry URL and verifies it against that integrity
  before npm reads it. The digest is reviewed and committed in the
  calling repository, so the registry supplies bytes rather than trust.
  A package declaring dependencies is refused, in `dependencies`,
  `optionalDependencies` or `peerDependencies` alike, because npm
  installs optional ones by default and resolves peers itself from
  version 7, so all three would come from the registry unverified. The packages install beside
  `cspell-lib`, which is what makes a bare `import` in a config
  elsewhere in the tree resolve: cspell searches `cspell-lib`'s own
  directory as well as the config file's.
- **Rust tooling** (cargo-deny, cargo-nextest, cargo-audit,
  cargo-llvm-cov): installed from binary release tarballs with SHA-256
  verification, never via `cargo install` (which would trust crates.io
  alone). cargo-llvm-cov in particular was migrated off `cargo install
--locked` for this reason.
- **clap-validator** (`set-up-clap-validator`): built from source with
  `cargo install --git <repo> --rev <40-char sha> --locked`. This is a
  different trust path from the `cargo install <crate>` the bullet above
  refuses, not an exception to it: the source is pinned to a commit, which
  no upstream can move, where a crates.io version resolves through the
  index at install time, and `--locked` pins the dependency tree to that
  commit's own `Cargo.lock`. `install-pinned-tool` cannot reach this
  upstream, which publishes nothing to crates.io and whose release assets
  cover neither Linux arm64 nor a file name derivable from a version
  string (0.4.1's are `.zip`, and named
  `clap-validator-0.4.1-127-g152b982-<platform>`, where the middle field is
  a build counter no version string yields). The action rejects a
  `validator-rev` that is not a full 40-character lowercase SHA, so a tag,
  which can be moved, cannot stand in for the commit.
- **`package.json` devDependencies**: exact versions (no `^`/`~`); the
  `package-lock.json` provides per-package sha512 integrity for any
  fresh `npm ci`.
- **npm `overrides`**: scoped to one dependent, never repo-wide.
  markdownlint-cli2 pins `smol-toml` to an exact version that carries a
  DoS advisory (GHSA-7w5x-hrqm-74c2, patched in 1.7.1), and an exact
  pin leaves no room for npm to resolve the fix on its own. The
  override is nested under `markdownlint-cli2` so it reaches only that
  dependency tree: cspell declares `smol-toml: ^1.8.0` and keeps
  resolving inside its own range. A repo-wide override would force
  every dependent to the same version and silently violate ranges that
  were already satisfied. The overridden version is still
  integrity-pinned in `package-lock.json`. Remove the entry once
  markdownlint-cli2 pins a patched `smol-toml` itself.

The general principle: **never let an upstream registry (npm, PyPI,
crates.io) be the sole integrity boundary for anything that runs in
CI.** Registry trust is fine for local developer convenience; it is
not fine for the supply chain feeding 26+ downstream repos.

### Version Pinning

All tool versions are pinned to exact patch releases. The Rust
toolchain is the one explicit exception: `rust-version` and
`rust-toolchain-file` in `run-rust-ci.yml` / `release-rust-binaries.yml` work
together so the consumer repo controls pinning.

- `rust-version`: explicit toolchain string; defaults to empty.
- `rust-toolchain-file`: path to the consumer's `rust-toolchain.toml`;
  default `rust-toolchain.toml`. When `rust-version` is empty, the
  workflow reads the file's `[toolchain] channel` value. If that
  channel is `"stable"`, it floats with rustup; if it is `"1.84.0"`
  (or similar), it is fully pinned.
- The workflow fails fast if neither input resolves to a value.

`set-up-clap-validator` is a second, narrower exception. Its
`rust-version` and `validator-rev` are both required with no default, so
the caller owns both pins and a caller that forgets one is rejected rather
than defaulted; that is deliberate, and it overrides the "Accept a
`version` input with a pinned default" step under "Adding a New Action"
below. Neither belongs in `scripts/check-tool-versions.py`, because this
repo ships no value for either. The `VALIDATOR_REV` and `RUST_VERSION` in
`run-ci.yml` are test fixtures for the self-test job, in the same category
as its shfmt 3.13.1 fixtures.

`node-version` defaults to a specific Node 24 LTS release
(`"24.15.0"`) in `lint-text.yml`, `publish-to-npm.yml`, and
`deploy-to-pages.yml`; callers may override with their own pinned
version.

### Automated Updates

`.github/dependabot.yml` runs weekly and covers two surfaces:

- **`github-actions`**: every external `uses:` reference in
  `.github/workflows/` and `actions/*/action.yml`. Dependabot bumps both
  the SHA and the `# vX.Y.Z` comment.
- **`npm`**: `package.json` devDependencies and `package-lock.json`.

Minor/patch updates are grouped into one PR per ecosystem; major
updates open individual PRs so breaking-change risk stays visible.

Dependabot does **not** track tool version strings inside workflow
`env:` blocks or `inputs.*-version` defaults, nor the hardcoded
SHA-256 checksums for shfmt, scrut, cargo-audit, and cargo-llvm-cov,
nor the yamllint hash manifest. The `check-tool-versions.yml`
workflow runs weekly to fill that gap: it queries each upstream and
opens (or updates) a single tracking issue when something is
outdated. The list of tracked tools and their current pinned versions
lives in `scripts/check-tool-versions.py`.

### Platform Support

Only Linux and macOS runners are supported. Each installer uses a `uname -s`
case statement with `Linux)` and `Darwin)` branches, plus a `*)` catch-all
that exits with an error. Windows is not supported.

### Makefile Target Convention for run-go-ci.yml

Consuming Go repos must provide Makefile targets for each enabled run-go-ci.yml
job: `vet`, `test`, `lint`, `build`, `fmt`. The `fmt` target must be a format
check (exit non-zero on unformatted code), not a write operation.

### Shell Conventions

- Composite actions read an `args` input one argument per line, with a
  `while IFS= read -r` loop into a bash array, so an argument may contain
  spaces.
- The Rust reusable workflows split their `*-args` inputs with `read -r -a`
  into a bash array. That handles simple space-delimited flags; quoting and
  escaping are not supported.
- Inputs are passed to shell steps via `env:` mappings, not inline expressions.
- Tools are installed to `RUNNER_TEMP` and added to `GITHUB_PATH`.
- `actions/install-pinned-tool/install-pinned-tool.sh` stays compatible with
  bash 3.2, the `/bin/bash` on macOS; its header lists what that rules out.

## Documentation layout

The repository's user-facing and agent-facing docs are organized as follows.
Keep this layout intact when adding or editing documentation.

- `README.md` (root) is the canonical source for orientation, the
  per-component Quick Reference, the quickstart, the trust model summary,
  supported platforms, versioning policy, and local development. It does
  not carry per-component reference tables.
- `actions/<name>/README.md` is the canonical source for each composite
  action's full reference (description, caveats, inputs, outputs, usage
  examples). GitHub renders this README when a visitor browses into the
  action's directory.
- `docs/workflows/<name>.md` is the canonical source for each reusable
  workflow's full reference. Reusable workflows do not have their own
  directory under `.github/workflows/` (only `.yml` files live there), so
  workflow docs live in `docs/workflows/`, parallel to `docs/migrations/`.
- `docs/migrations/vN.md` is the canonical source for each major-version
  migration guide (path renames, breaking input changes, removed
  components).
- `AGENTS.md` (this file, with `CLAUDE.md` symlinked to it) is the
  canonical source for repository conventions, agent guidance, and
  contributor procedures. The trust model long form lives here; the
  README has a condensed summary that links back.
- `.github/copilot-instructions.md` is the canonical source for PR-review
  anti-patterns and Copilot-specific guidance.

### Per-component doc template

Use this template when creating a new `actions/<name>/README.md` or
`docs/workflows/<name>.md`. Sections that do not apply to a given
component (no outputs, no secrets) are omitted entirely rather than left
empty.

````markdown
# <name>

<1 to 3 sentence description of what the action or workflow does.>

<Caveats, if any. For example: Makefile-targets requirement, pinned-version
requirement, GITHUB_TOKEN requirement, changelog-format requirement.>

## Inputs

| Name      | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `example` | ...  | ...     | ...         |

## Outputs

| Name      | Description |
| --------- | ----------- |
| `example` | ...         |

## Secrets

| Name      | Required | Description |
| --------- | -------- | ----------- |
| `EXAMPLE` | ...      | ...         |

## Usage

```yaml
- uses: cboone/gh-actions/actions/<name>@v3.2.0
  with:
    example: value
```
````

For reusable workflows, the Usage example uses the `jobs:` form:

```yaml
jobs:
  example:
    uses: cboone/gh-actions/.github/workflows/<name>.yml@v3.2.0
```

All Usage examples pin to the current released tag (currently `@v3.2.0`),
per the existing rule in `.github/copilot-instructions.md`.

## Adding a New Action

1. Create `actions/<name>/action.yml` with `using: composite`.
1. Accept a `version` input with a pinned default.
1. For a release binary, bind
   `${{ github.action_path }}/../install-pinned-tool/install-pinned-tool.sh`
   to an `env:` variable and run it with the tool's URL template and
   checksum source, as `actions/set-up-shfmt/action.yml` does. Keep the
   path in `env:`: for a job that sets `container:`, the runner translates
   host paths in `env:` values but not in an expression written into
   `run:`. Set the installer variables the tool does not use to `""` so a
   caller's job-level `env` cannot reach them. The script detects OS and architecture, downloads, verifies the
   SHA-256, installs to `RUNNER_TEMP`, and appends to `GITHUB_PATH`.
   Anything else detects OS and architecture with `uname -s` / `uname -m`
   case statements, verifies a SHA-256, installs to `RUNNER_TEMP`, and
   appends to `GITHUB_PATH` itself.
1. For `run-*` actions, add a second step that executes the tool.
1. Create `actions/<name>/README.md` from the per-component template
   documented under "Documentation layout" above. GitHub renders this
   README when a visitor browses into the action's directory.
1. Add a row to the Quick Reference table in the root `README.md`, under
   the appropriate group (Linting and formatting, Testing and CI,
   Releasing and publishing, Security and supply chain, or Repository
   chores), linking to the new `actions/<name>/README.md`.

## Adding a New Workflow

1. Create `.github/workflows/<name>.yml` with an `on: workflow_call` trigger.
1. Define inputs with types and defaults; keep permissions minimal.
1. For a release binary, fetch `install-pinned-tool.sh` from
   `job.workflow_repository` at `job.workflow_sha` and run it, as
   `lint-shell.yml` does; a `./` composite action reference would resolve
   against the caller's checkout. Inline anything else, following the
   checksum verification pattern used by existing workflows.
1. Create `docs/workflows/<name>.md` from the per-component template
   documented under "Documentation layout" above. Reusable workflows do
   not have their own directory under `.github/workflows/`, so workflow
   docs live in `docs/workflows/`.
1. Add a row to the Quick Reference table in the root `README.md`, under
   the appropriate group, linking to the new `docs/workflows/<name>.md`.

## Merging Pull Requests

Always merge with a merge commit (`gh pr merge --merge`), and never squash
or rebase. This holds for every pull request in this repository, including
single-commit and Dependabot ones.

The reason is that each commit here is written to stand on its own. A
branch's history separates the substantive change from its plan file, its
lint fixes, and any commits made in response to review, and `git log`
against a single file is how a convention's rationale gets recovered later.
Squashing collapses that into one message, and rebasing discards the merge
point that shows what landed together.

## Releasing

This repository has no GoReleaser config; releases are plain Git tags.
Use the `/release` skill, which analyzes conventional commits,
recommends a version bump, updates CHANGELOG.md, creates a release
commit, and tags it locally. Then push the commit and tag.

Pushing a `v*.*.*` tag triggers `create-gh-release-on-tag.yml`, which
calls `create-gh-release-from-changelog.yml` to publish the GitHub
Release. That workflow reads the notes out of the `## [VERSION]`
section of CHANGELOG.md, so the section must exist before the tag is
pushed or the release job fails. Do not create the GitHub Release by
hand. See the README Versioning section for full details.

When a release introduces breaking changes (path renames, removed inputs,
removed components), document them in `docs/migrations/vN.md` (parallel to
`docs/migrations/v3.md`) and link the new migration guide from the README
Migration section.

## Testing

The repository self-hosts its own workflows as integration tests. The `run-ci.yml`,
`scan-for-secrets-with-gitleaks.yml`, and
`scan-for-secrets-with-trufflehog.yml` files call the reusable workflows from
this same repository. `run-ci.yml` also runs `actions/install-pinned-tool`,
and the `set-up-*` actions built on it, from the checkout on Linux amd64,
Linux arm64 and macOS arm64, including inputs it must reject, and asserts
that actionlint really does shell out to shellcheck. Its `scrut` job calls
`run-scrut-tests.yml` with `setup-uv: true` against `tests/scrut/`, whose
fixture is a PEP 723 script that only runs if uv reached `PATH`.
`actions/install-cspell-dictionaries` is tested on the same three
runners the same way, through `run-cspell` against a fixture kept
outside the checkout: a dictionary installed beside `cspell-lib`
resolves from a config anywhere else in the tree, so a fixture inside
the workspace would resolve through the ordinary `node_modules` walk and
assert nothing. It runs `actions/set-up-clap-validator` on those same
three runners, covering the install, the cache-hit path, and the pins
`check-pins.sh` must reject. There is no unit test framework.

## Local Development

- `make help` lists available targets.
- `make lint` runs actionlint on workflow files.
- `make lint-md` runs markdownlint-cli2 on Markdown files.
- `make format` runs Prettier in write mode.
- `make format-check` runs Prettier in check mode.
- `make spell` runs cspell.
- `make lint-yaml` runs yamllint.
