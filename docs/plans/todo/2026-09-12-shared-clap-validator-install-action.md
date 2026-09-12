# Shared clap-validator install action

Issue: [#88](https://github.com/cboone/gh-actions/issues/88)

## Context

`cboone/fosforo` and `cboone/springer` each carry a copy of the same
composite action at `.github/actions/clap-validator/action.yml`, which
builds [clap-validator](https://github.com/free-audio/clap-validator), the
CLAP plugin conformance checker, from a pinned commit and puts it on
`PATH`. The two copies are functionally identical: a diff shows only
comment re-wrapping and the plugin name in the header comment. A third
audio plugin repo would copy it a third time, and the cache key is the
part that hurts when it drifts, because a drifted key still passes and
just pays a full Rust build on every run.

This adds one reusable copy here and keeps every recorded reason behind
the original's shape. The pins stay caller-supplied with no defaults, the
cache key stays exact with no `restore-keys`, and `clap-validator
validate` stays out of the action so the gate remains readable in the job
that runs it.

Nothing about CLAP or clap-validator exists in this repository yet, so
this is greenfield apart from the documentation conflicts below.

## Decisions

Three points needed resolving before implementation, and all three are
settled:

1. **Name: `set-up-clap-validator`**, not the `install-clap-validator`
   the issue suggests. `AGENTS.md` reserves `set-up-*` for actions that
   install a tool and add it to `GITHUB_PATH` without running it, and
   `install-*` for `install-pinned-tool`, the one generic installer. The
   issue's path is simply what fosforo calls it locally.
1. **Document the `cargo install` carve-out.** `AGENTS.md`, `README.md`
   and `.github/copilot-instructions.md` all currently say Rust tooling is
   installed from binary release tarballs "never via `cargo install`
   (which would trust crates.io alone)". This action's mechanism is a
   different trust path and the docs must say so, or the action reads as a
   policy violation to every reviewer and to Copilot.
1. **Full self-test coverage** in `run-ci.yml`: the three-runner matrix
   `install-pinned-tool` uses, plus a cache-hit assertion and rejection
   cases.

### Why `cargo install --git` stays, despite the ban

clap-validator 0.4.1 does publish prebuilt binaries carrying
GitHub-native SHA-256 digests, and their names even embed the commit
(`clap-validator-0.4.1-127-g152b982-ubuntu-22.04.zip`). They are still
not usable here:

- There is no Linux arm64 asset at all, only `ubuntu-22.04` (amd64).
- The assets are `.zip`; `install-pinned-tool` extracts only from tar.
- The `127-g152b982` fragment is `git describe` output and cannot be
  derived from a version string, so it defeats the `{version}` templating
  the installer is built around.

`cargo install --git <repo> --rev <40-char sha> --locked` is a genuinely
different trust boundary from `cargo install <crate>`: the source is
pinned to a commit, which no upstream can move, and `--locked` pins the
dependency tree to the repository's committed `Cargo.lock`. crates.io
serves the transitive dependencies but does not choose them.

### Required inputs need an explicit guard

GitHub does not enforce `required: true` for composite action inputs. An
omitted input arrives as the empty string, so "a caller that forgets
should fail loudly" needs code, not just the `required:` key. The guard
also enforces "pin by commit, not by tag" structurally, by rejecting
anything that is not a lowercase 40-character SHA; `cargo --rev` would
happily accept a tag.

The guard lives in a sibling script rather than inline in `action.yml` for
two reasons. It lets `run-ci.yml` exercise the rejection cases by invoking
the script directly, the pattern reviewed and landed for
`install-pinned-tool`, instead of `continue-on-error` steps that would
leave nine spurious error annotations on every green CI run. And it puts
the guard in front of ShellCheck and shfmt, which `lint-shell.yml` already
runs over the repository's scripts.

## Changes

### 1. `actions/set-up-clap-validator/check-pins.sh` (new)

Validates the two pins and derives what the rest of the action needs.
Follows `install-pinned-tool.sh`: same header shape (purpose, author,
date, the environment variables with their action inputs in parentheses,
an exit-code block), `set -euo pipefail`, `readonly E_USAGE=64` and
`readonly E_PLATFORM=71`, and bash 3.2 compatibility, since the rejection
tests run it under `/bin/bash` on macOS.

Reads `VALIDATOR_REV`, `RUST_VERSION`, `RUNNER_OS`, `RUNNER_ARCH`,
`RUNNER_TEMP` and `GITHUB_OUTPUT`. Rejects, with `::error::` annotations
and accumulated status so one run reports every problem:

- an empty `validator-rev` or `rust-version`, exit 64;
- a `validator-rev` that is not 40 lowercase hex characters, exit 64;
- a `uname -s` that is neither `Linux` nor `Darwin`, exit 71, satisfying
  the platform guard the README's "Supported platforms" section promises
  of every installer.

On success writes two `GITHUB_OUTPUT` values:

- `cache-key`, as
  `clap-validator-<RUNNER_OS>-<RUNNER_ARCH>-<rev>-rust<rust-version>`,
  byte-identical to the key fosforo writes inline, since `RUNNER_OS` and
  `RUNNER_ARCH` carry the same values as `runner.os` and `runner.arch`;
- `install-dir`, as `${RUNNER_TEMP}/clap-validator/bin`.

Single-sourcing the key here is also what keeps the line under yamllint's
120-character limit: written inline in `with:`, the key expression is 122
characters. A comment records the literal shape so a reader of
`action.yml` does not have to open the script to learn it.

### 2. `actions/set-up-clap-validator/action.yml` (new)

`name: Set up clap-validator`, a folded `description:`, then
`validator-rev` and `rust-version` as `required: true` with no `default:`
key, matching how `install-pinned-tool` declares its required inputs.
Outputs `install-dir` and `cache-hit`. Steps, in order:

1. `Check the pins` (`id: pins`) runs `check-pins.sh` with the script path
   bound in `env:` as `install-pinned-tool`'s callers do, because a job
   that sets `container:` gets host paths in `env:` translated and
   expressions in `run:` not.
1. `Restore the cached validator` (`id: cache`) uses
   `actions/cache/restore@55cc8345863c7cc4c66a329aec7e433d2d1c52a9 # v6.1.0`,
   the SHA already pinned for `actions/cache` in `run-lean-ci.yml`, with
   `path: ${{ runner.temp }}/clap-validator` and the derived key. No
   `restore-keys`.
1. `Build clap-validator`, `if: steps.cache.outputs.cache-hit != 'true'`,
   running `rustup toolchain install "${RUST_VERSION}" --profile minimal
--no-self-update` then `cargo "+${RUST_VERSION}" install --git
https://github.com/free-audio/clap-validator --rev "${VALIDATOR_REV}"
--locked --root "${RUNNER_TEMP}/clap-validator"`.
1. `Cache the built validator`, same `if:`, using `actions/cache/save` at
   the same SHA with `key: ${{ steps.cache.outputs.cache-primary-key }}`
   so restore and save cannot diverge.
1. `Put clap-validator on PATH`, appending the derived install directory
   with `printf '%s\n' "${INSTALL_DIR}" >> "${GITHUB_PATH}"`, the spelling
   every other action in the repo uses.
1. `Report clap-validator version`, matching `set-up-shfmt` and
   `set-up-actionlint`. A comment must note this checks that the binary
   runs and is not a check of the pin: the reported `0.4.1` names the
   release the commit sits on, which is the whole reason the pin is a
   commit.

Comments carry over the recorded reasons from fosforo, rewritten for a
repo-agnostic caller: why restore and save are split, why the install goes
somewhere the action owns rather than `~/.cargo/bin`, why there are no
`restore-keys`, what `--locked` and `--root` buy, and that two jobs racing
a cold cache make the loser's save warn rather than fail.

### 3. `actions/set-up-clap-validator/README.md` (new)

From the per-component template in `AGENTS.md`: H1 is the directory name,
the `action.yml` description as the lead paragraph, caveat prose with no heading,
then `## Inputs`, `## Outputs` and `## Usage` with the example pinned to
`@v3.1.1`. Caveats to state:

- `rustup` and `cargo` must be on `PATH`; they are on GitHub-hosted Linux
  and macOS images. A cache hit installs no toolchain at all, because the
  restored binary is standalone.
- Both pins are required with no defaults, and `validator-rev` must be a
  full lowercase commit SHA.
- The binary lands at `$RUNNER_TEMP/clap-validator/bin/clap-validator`,
  not the `$RUNNER_TEMP/<tool>-bin/<tool>` the other actions use, because
  `cargo install --root` chooses the `bin/` subdirectory.
- Running the validator is the caller's job, with a one-line example.
- Nothing here needs a `scripts/check-tool-versions.py` entry, since the
  action pins no version of its own.

### 4. `.github/workflows/run-ci.yml`

A `set-up-clap-validator` job alongside `install-pinned-tool`, following
its shape: `name: set-up-clap-validator (${{ matrix.runner }})`,
`fail-fast: false` over `ubuntu-latest`, `ubuntu-24.04-arm` and
`macos-latest`, `permissions: contents: read`, `defaults: run: shell:
bash`. `timeout-minutes` goes above `install-pinned-tool`'s 10, since a
cold cache builds from source.

Job-level `env:` holds the fixtures, with a comment that they are
fixtures and not pins this repo ships, because both inputs are required
and have no defaults, so nothing here reaches a consumer:
`VALIDATOR_REV: 152b9823e992d782c5c1fd33bca0295478b919aa` (tag 0.4.1
resolved to its commit, verified against the GitHub API) and
`RUST_VERSION: "1.97.1"` (what fosforo and springer build with;
clap-validator 0.4.1 declares MSRV 1.95.0 and is edition 2024).

Steps: check out, call the action, assert `command -v clap-validator`
resolves to exactly the action's own install directory and that
`--version` reports `0.4.1` and that the `install-dir` output matches,
then call the action a second time and assert `cache-hit` is `true`, which
exercises the warm path on every run rather than only after some earlier
run populated the cache. Assertions accumulate `status` and `exit
"${status}"` so one run reports everything.

Rejections go in one step with the `check_rejection` helper from the
`install-pinned-tool` job, invoking `check-pins.sh` under `env -i` with
`GITHUB_OUTPUT=/dev/null` and rewriting `::error::` prefixes through `sed`
so expected failures raise no annotations. Cases: empty `validator-rev`
(64), empty `rust-version` (64), a `validator-rev` of `0.4.1` (64), and a
`validator-rev` that is 40 characters but not hex (64).

The workflow's header comment enumerates what each job covers and must be
extended to name this one.

### 5. `.github/dependabot.yml`

`directories:` currently lists only `/` and `/actions/create-pull-request`,
so Dependabot's `github-actions` manager does not see other action
directories despite what the file's header comment implies. Add
`/actions/set-up-clap-validator`, or the two `actions/cache` pins will
never be bumped.

### 6. Documentation for the carve-out

- `AGENTS.md`: a bullet in "Pinning Policy and Trust Model" for
  `cargo install --git --rev <40-char sha> --locked`, stating what each
  flag pins and why this is not the crates.io-only path the neighboring
  Rust bullet forbids; the new action in the "Repository Structure" tree,
  alphabetically after `set-up-actionlint/`; a sentence in "Version
  Pinning" recording that `rust-version` here is required with no default,
  unlike `run-rust-ci.yml`'s consumer-controlled pin and unlike the
  "Accept a `version` input with a pinned default" line in "Adding a New
  Action"; and the new self-test job in "Testing".
- `README.md`: a matching bullet in the condensed "Trust model and
  pinning" list, and a Quick Reference row under "Testing and CI" after
  `set-up-scrut`, linking `actions/set-up-clap-validator/README.md`.
- `.github/copilot-instructions.md`: an entry under "Tool installation and
  pinning" saying this action's `cargo install --git --rev` is deliberate
  and must not be flagged against the `never via cargo install` bullet,
  and that its required inputs without defaults are deliberate too.

### 7. `CHANGELOG.md`

One entry at the top of `### Added` under `## [Unreleased]`, in the house
style: component in backticks, inputs and behavior described, ending
`(#88)` with no period.

### 8. `cspell.json`, if needed

`rustup` and `fosforo` are already in `words`; `clap`, `validator` and
`springer` pass on the bundled dictionaries. `MSRV` is the likely new
word. Add whatever `make spell` reports, in case-insensitive alphabetical
position on the existing single line.

## Verification

Local, from the repository root:

1. `make lint` runs actionlint, which covers `.github/workflows/run-ci.yml`
   and every `actions/*/action.yml`.
1. `make lint-yaml` runs yamllint, whose 120-character limit is the one to
   watch in the new `action.yml` and the new CI job.
1. `make lint-md`, `make format-check` and `make spell` cover the two new
   Markdown files, the edited docs and this plan.
1. `shellcheck actions/set-up-clap-validator/check-pins.sh` and
   `shfmt -d` on it, which is what `lint-shell.yml` will run in CI.
1. Run `check-pins.sh` directly for each rejection case and for the
   success case, asserting the exit codes and the two `GITHUB_OUTPUT`
   lines, before relying on CI to do it.

End to end, the real check is the `set-up-clap-validator` job in CI on the
PR: a cold-cache build on all three runners, the binary resolving to the
action's own directory and reporting `0.4.1`, the second call hitting the
cache, and all four rejections failing with exit 64 and no annotations.

## Out of scope

- Migrating `cboone/fosforo` and `cboone/springer` onto this action. Both
  are separate repositories and need their own pull requests, and this
  action cannot be referenced by tag until the next release cuts one.
- A `scripts/check-tool-versions.py` entry. The action pins nothing of its
  own, and the `run-ci.yml` fixtures are test fixtures, which that script
  already treats as exempt.
- Zip support in `install-pinned-tool`, which is what a prebuilt-binary
  path for clap-validator would need, along with an upstream that ships a
  Linux arm64 asset.
