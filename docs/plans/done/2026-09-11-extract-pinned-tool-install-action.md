# Extract the pinned-tool install into one composite action (#87)

## Context

`lint-github-actions.yml`, `lint-shell.yml`, `actions/set-up-actionlint` and
`actions/set-up-shfmt` each carry the same installer inline: `uname` to an OS
and arch token, download to `$RUNNER_TEMP`, compare a SHA-256 with a
`sha256sum` / `shasum -a 256` fallback, extract a named member or `chmod +x`,
append to `$GITHUB_PATH`. The copies differ only in where the expected checksum
comes from. The shfmt copies keep theirs in a `case` inside `run:` and refuse
any version but 3.13.1, so `shfmt-version` is decorative
([#87](https://github.com/cboone/gh-actions/issues/87)).

The same procedure is hand-written in `cboone/fosforo` (shfmt, shellcheck, ruff,
typos, actionlint) and `cboone/springer` (typos). Those copies pin one
`linux_amd64` SHA-256 per tool and use target-triple asset names
(`x86_64-unknown-linux-musl`) and nested or `./`-prefixed archive members
(`ruff-x86_64-unknown-linux-gnu/ruff`, `./typos`), so the shared installer has
to cover all three.

### Intended outcome

One installer, `actions/install-pinned-tool`, which other repositories consume
as `cboone/gh-actions/actions/install-pinned-tool@<sha>`. Every copy in this
repo named above runs the same script, a version bump is an input change, and
[#85](https://github.com/cboone/gh-actions/issues/85) (shellcheck) becomes one
more install step.

### Decisions

- **Reusable workflows fetch the script at their own commit.** They `curl`
  `actions/install-pinned-tool/install-pinned-tool.sh` from
  `job.workflow_repository` at `job.workflow_sha` into `$RUNNER_TEMP`, the
  trust model `lint-text.yml` already uses for its manifests. The script and
  the workflow stay on one commit, the change ships in one release, and PR CI
  runs the code under review.
- **Two alternatives rejected.** `uses: cboone/gh-actions/actions/...@<sha>`
  needs a tagged release before anything can pin to it, and after that the
  workflows lag the action by a release, with a Dependabot self-bump after every
  release. `actions/checkout` into the workspace was rejected in #83: the
  checkout lands in the consumer's tree and gets linted, and `lint-shell.yml`'s
  `find . -name '*.sh'` would lint it too.
- **Accepted cost.** `lint-shell.yml` and `lint-github-actions.yml` inherit
  `lint-text.yml`'s limitations: no `job.workflow_*` on GitHub Enterprise
  Server, and no `raw.githubusercontent.com` for private forks.
- **Path.** `actions/install-pinned-tool/`, where this repo keeps externally
  consumed actions, rather than the `.github/actions/` the issue sketched.
- **Composite actions reach the script as a sibling** through
  `github.action_path`, the idiom `actions/run-cspell/action.yml` and
  `actions/run-reuse/action.yml` already use, so the `set-up-*` wrappers need
  no self-referencing pin either.

## Changes

### 1. `actions/install-pinned-tool/install-pinned-tool.sh`

The single copy of the logic. It takes an environment-variable interface, so
the composite action, the wrappers and the workflows drive it identically. It
stays compatible with bash 3.2 (macOS `/bin/bash`): no associative arrays, no
`${var,,}`, no `mapfile`. Invoke `write-bash-scripts` before writing it.

| Input                    | Env                      | Required     | Purpose                                               |
| ------------------------ | ------------------------ | ------------ | ----------------------------------------------------- |
| `tool`                   | `TOOL`                   | yes          | Binary name; installs as `<install-dir>/<tool>`       |
| `version`                | `VERSION`                | yes          | Exact version, no default anywhere                    |
| `url-template`           | `URL_TEMPLATE`           | yes          | `https://` URL with `{version}`, `{os}`, `{arch}`     |
| `checksum`               | `CHECKSUM`               | one of three | One SHA-256, applied on every platform                |
| `checksums`              | `CHECKSUMS`              | one of three | `sha256sum` lines, one per platform asset             |
| `checksums-url-template` | `CHECKSUMS_URL_TEMPLATE` | one of three | `https://` URL of an upstream `sha256sum`-format file |
| `archive-member`         | `ARCHIVE_MEMBER`         | no           | Tar member to extract; omit for a bare binary         |
| `os-names`               | `OS_NAMES`               | no           | Renames `{os}`, e.g. `darwin=macos`                   |
| `arch-names`             | `ARCH_NAMES`             | no           | Renames `{arch}`, e.g. `amd64=x86_64 arm64=aarch64`   |

The one output is `install-dir`, which is `$RUNNER_TEMP/<tool>-bin`, matching
the `actionlint-bin` and `shfmt-bin` directories used today.

In order, the script:

1. **Validates.** `tool` matches `^[A-Za-z0-9][A-Za-z0-9._-]*$` and `version`
   matches `^[A-Za-z0-9][A-Za-z0-9._+-]*$`, which also keeps `&` and `/` out of
   bash pattern-substitution replacements. Both templates start with
   `https://`. Exactly one checksum source is set. `RUNNER_TEMP`, `GITHUB_PATH`
   and `GITHUB_OUTPUT` are set.
1. **Detects the platform.** `uname -s` gives `linux` or `darwin`; `uname -m`
   gives `amd64` (`x86_64`) or `arm64` (`arm64`, `aarch64`); anything else exits
   with today's `Unsupported operating system` / `architecture` messages. These
   are the tokens Go release tooling uses. `os-names` and `arch-names` rename
   them as whitespace-separated `key=value` pairs; a key other than the four
   canonical tokens, or an unsafe value, is an error, so a typo cannot silently
   fall back to the default spelling.
1. **Renders placeholders** in `url-template`, `checksums-url-template` and
   `archive-member`. A leftover `{` or `}` is an error, which catches a
   misspelled placeholder. The checksum text is never rendered: its keys are literal asset
   names, so a version bumped without its checksums fails with
   `No checksum entry for shfmt_v3.14.1_linux_amd64` rather than a mismatch.
1. **Resolves the expected digest before downloading the asset.** It is taken
   from `checksum`, or by exact asset-name lookup in `checksums` or in the
   downloaded checksum file. The lookup skips blank and `#` lines, strips a
   leading `*` binary-mode marker and any directory prefix from the name field,
   and treats zero matches or two conflicting matches as an error. The result is
   lowercased and must be 64 hex characters.
1. **Downloads to a file** in a `mktemp -d` staging directory under
   `$RUNNER_TEMP`, with `curl -sSfL --retry 3 --retry-delay 5
--retry-all-errors`, logging the URL. Nothing consumes the bytes before
   they verify; the asset is never piped into `tar`.
1. **Verifies** with `sha256sum`, falling back to `shasum -a 256`. A mismatch
   prints `Expected:` and `Actual:` and exits 1, as today.
1. **Installs.** With `archive-member`, `tar -xf` (GNU tar and bsdtar both
   detect the compression) extracts only that member into the staging
   directory, then `install -m 0755` copies it to `<install-dir>/<tool>`; a
   missing member is a named error. Without it, `install -m 0755` copies the
   download itself.
1. **Publishes** the install directory to `$GITHUB_PATH`, writes
   `install-dir=` to `$GITHUB_OUTPUT`, and removes the staging directory.

Failures surface as `::error::` annotations, with detail lines on stderr.

### 2. `actions/install-pinned-tool/action.yml`

Maps each input to its environment variable and runs `bash "${INSTALLER}"`
with `INSTALLER: ${{ github.action_path }}/install-pinned-tool.sh`, then
exposes the step's `install-dir` output. `tool`, `version` and `url-template`
have no defaults; the script, not the runner, enforces them.

### 3. `actions/set-up-actionlint` and `actions/set-up-shfmt`

Inputs and defaults stay. The install step becomes an `env:` block plus
`bash "${INSTALLER}"` with
`INSTALLER: ${{ github.action_path }}/../install-pinned-tool/install-pinned-tool.sh`.
The version print moves to its own step (`actionlint -version`,
`shfmt --version`), resolved through `PATH`.

- `set-up-actionlint`: `checksums-url-template` points at
  `actionlint_{version}_checksums.txt`, with `archive-member: actionlint`.
  Behavior is unchanged.
- `set-up-shfmt`: a new optional `checksums` input defaults to the four v3.13.1
  lines, and the `supported_version` gate goes away. Overriding `version` works
  when paired with `checksums`; overriding it alone still fails, now naming the
  missing asset.

### 4. `lint-github-actions.yml` and `lint-shell.yml`

Each gains a `Fetch install-pinned-tool` step: `REQ_REPO` / `REQ_SHA` bound in
the step's own `env:` (they cannot be hoisted), the `lint-text.yml` guard
naming both properties and GitHub Enterprise Server, `echo "Fetching from
${base}"`, and a retried `curl`. Each tool then gets an install step with only
`env:` and `bash "${RUNNER_TEMP}/install-pinned-tool.sh"`.

- `lint-github-actions.yml`: actionlint, configured as in the wrapper. The
  fetch is unconditional.
- `lint-shell.yml`: a new `shfmt-checksums` input (string, defaulting to the
  four v3.13.1 lines) sits next to `shfmt-version`. The fetch carries the shfmt
  install's `if:`, so a job that installs nothing never reads the job context.
  The inline `case` and version gate go away.

```yaml
- name: Install shfmt
  if: inputs.run-shfmt && steps.find-scripts.outputs.found == 'true'
  env:
    TOOL: shfmt
    VERSION: ${{ inputs.shfmt-version }}
    URL_TEMPLATE: https://github.com/mvdan/sh/releases/download/v{version}/shfmt_v{version}_{os}_{arch}
    CHECKSUMS: ${{ inputs.shfmt-checksums }}
  run: bash "${RUNNER_TEMP}/install-pinned-tool.sh"
```

### 5. `.github/workflows/run-ci.yml`

- **An `install-pinned-tool` job** with a matrix over `ubuntu-latest`
  (linux/amd64), `ubuntu-24.04-arm` (linux/arm64) and `macos-latest`
  (darwin/arm64), with `fail-fast: false`, `timeout-minutes: 10`,
  `permissions: contents: read` and `defaults.run.shell: bash` for
  `pipefail`. It runs `uses: ./actions/install-pinned-tool` for shfmt 3.13.1
  (bare binary, `checksums` table), actionlint 1.7.12 (archive, upstream
  checksum file) and uv 0.11.8 (the repo's existing pin: target triples through
  `os-names` / `arch-names`, nested member `uv-{arch}-{os}/uv`, per-asset
  `.sha256`). It then runs the two wrappers and asserts that each `command -v`
  resolves under `$RUNNER_TEMP` and reports the pinned version. Three negative
  cases run with `continue-on-error: true`: a wrong `checksum`, a version bumped
  without its checksums (the issue's scenario), and no checksum source. A final
  step asserts that each `steps.<id>.outcome` is `failure`.
- **A `shell` job**, `uses: ./.github/workflows/lint-shell.yml`, which runs the
  migrated workflow end to end at the PR's own SHA and lints the new script and
  `scripts/install-actionlint` with ShellCheck and shfmt.

The existing `actionlint` job already runs the migrated
`lint-github-actions.yml`.

### 6. Documentation

Invoke `write-markdown` before editing any of these.

- `actions/install-pinned-tool/README.md` (new, from the per-component
  template). Caveats cover:
  - Linux and macOS only.
  - Tar archives or bare binaries, `https://` only, and exactly one checksum
    source.
  - The placeholder vocabulary and how to rename it.
  - Provenance: a committed checksum pins what the caller reviewed, while an
    upstream checksum file served from the same release only proves the asset
    matches what that release serves at fetch time.
  - How to produce a checksum: `shasum -a 256` on the asset, or the release
    asset's `digest` from `gh api`.

  Usage examples: shfmt (per-platform table), actionlint (upstream checksum
  file), typos (single `checksum`, `./typos` member, `-musl` triple) and uv
  (per-asset `.sha256`).

- `actions/set-up-shfmt/README.md`: a `checksums` row, and the override
  procedure in place of the "only the pinned version" caveat.
- `docs/workflows/lint-shell.md`: a `shfmt-checksums` row, the same caveat
  swap, and a short subsection on how the workflow reaches its installer, with
  the GitHub Enterprise Server and private-fork limitation and `run-shfmt: false`
  as the escape hatch.
- `docs/workflows/lint-github-actions.md`: the same subsection, stating that
  GitHub Enterprise Server is not supported, since actionlint is the whole job.
- `README.md`: a Quick Reference row under "Security and supply chain", and the
  trust-model bullet for binary downloads names the shared installer.
- `AGENTS.md` (`CLAUDE.md` is a symlink to it):
  - A Repository Structure entry.
  - "Composite Actions vs. Reusable Workflows" restated as present-tense facts:
    no `./` refs, the two lint workflows fetch the installer through the job
    context, and the other workflows inline their installers.
  - A Naming line: `install-pinned-tool` is the generic installer the `set-up-*`
    actions build on.
  - "Adding a New Action" and "Adding a New Workflow" point release-binary
    installs at the script.
  - The SHA-256 section names where shfmt's checksums live.
- `.github/copilot-instructions.md`:
  - Restate "Reusable workflows are intentionally self-contained" and name the
    two rejected alternatives, so review does not reopen them.
  - Point the shfmt entry at the `checksums` / `shfmt-checksums` defaults and
    their format.
  - Extend the `REQ_REPO` / `REQ_SHA` entry to the two lint workflows.
  - Add that the script stays bash 3.2 compatible.
- `.github/actionlint.yaml`: the comment names more than `lint-text.yml`. The
  pattern already covers every workflow and stays unchanged.
- `scripts/check-tool-versions.py`: the shfmt note names the two checksum
  defaults to regenerate on a bump.
- `CHANGELOG.md` `[Unreleased]`:
  - Added: the action, `shfmt-checksums`, and `set-up-shfmt`'s `checksums`.
  - Changed: the two workflows and two wrappers run the shared installer, and
    the two workflows now depend on the job context.

### Out of scope

- #85 adds shellcheck: one more install step per workflow once this lands.
- The remaining inline installers, for a follow-up issue:
  - Workflows: `run-go-ci`, `run-rust-ci`, `run-zig-ci`, `run-scrut-tests`,
    `scan-for-secrets`, `release-go-binaries`, and `lint-text`'s uv step.
  - Actions: `set-up-golangci-lint`, `set-up-goreleaser`, `set-up-scrut`,
    `run-gitleaks`, `run-trufflehog`, `run-markscribe` and `run-reuse`.
  - `scripts/install-actionlint`.
- After release, fosforo and springer adopt `install-pinned-tool@<sha>`.

## Verification

Locally, on this darwin/arm64 machine:

1. Run `shellcheck` and `shfmt -d` (which reads `.editorconfig`'s 2-space
   indent) on the script and `scripts/install-actionlint`. Repeat shfmt at
   3.13.1, the version CI pins, installed by the script itself.
1. Drive the script under `/bin/bash` 3.2 and under Homebrew bash, with
   `RUNNER_TEMP`, `GITHUB_PATH` and `GITHUB_OUTPUT` in the scratchpad. Install:
   - shfmt 3.13.1
   - actionlint 1.7.12
   - uv 0.11.8
   - shellcheck 0.11.0 (arch renames, nested member
     `shellcheck-v{version}/shellcheck`)
   - typos 1.50.1 (`./typos` member, single `checksum` from the `gh api`
     digest)

   Each binary should run and report its version, and `GITHUB_PATH` and
   `GITHUB_OUTPUT` should hold the expected lines.

1. Negative cases, each exiting non-zero with its own message: wrong checksum,
   missing entry, no source, two sources, unknown placeholder, bad `os-names`
   key, missing archive member, `http://` URL, unsafe tool name.
1. The linters at their pinned versions: `npm ci`, then
   `./node_modules/.bin/markdownlint-cli2 "**/*.md"`, `prettier --check .` and
   `cspell .`; then `make lint` and `make lint-yaml`. This plan is linted too,
   since the ignore lists cover `docs/plans/done/` but not `docs/plans/todo/`.

In CI, on the PR:

1. `install-pinned-tool` is green on all three runners, the negative-case
   assertion included.
1. `actionlint` and the new `shell` job are green, and each log shows
   `Fetching from https://raw.githubusercontent.com/cboone/gh-actions/<sha>`
   followed by the installer's download line.
1. `text` is green.

## Commits

Conventional Commits, each green on its own:

1. `docs: plan the pinned-tool installer extraction (#87)`
1. `feat(install-pinned-tool): add a composite action for pinned release binaries (#87)`:
   the script, `action.yml`, README, Quick Reference row, CHANGELOG and cspell
   words.
1. `ci(run-ci): exercise install-pinned-tool on Linux and macOS runners (#87)`
1. `feat: build set-up-actionlint and set-up-shfmt on install-pinned-tool (#87)`:
   both wrappers, `checksums`, their READMEs, wrapper assertions in the CI job,
   and CHANGELOG.
1. `feat: install lint-shell and lint-github-actions tools through install-pinned-tool (#87)`:
   both workflows, `shfmt-checksums`, the workflow docs, the actionlint.yaml
   comment and CHANGELOG.
1. `ci(run-ci): self-host lint-shell.yml (#87)`
1. `docs: describe the shared installer in AGENTS.md and the Copilot instructions (#87)`:
   including the `check-tool-versions.py` note.
