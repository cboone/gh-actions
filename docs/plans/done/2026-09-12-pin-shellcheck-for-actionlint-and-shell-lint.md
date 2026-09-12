# Pin shellcheck for actionlint and shell lint

Issue: [#85](https://github.com/cboone/gh-actions/issues/85)

## Context

`lint-github-actions.yml` and `lint-shell.yml` both depend on `shellcheck`, and
neither installs it: it resolves from whatever the runner image provides. Two
problems follow.

**The failure mode is silent.** `actionlint` shells out to `shellcheck` for
every `run:` block, which is the only thing in `lint-github-actions.yml` that
lints embedded shell. With no `shellcheck` on `PATH` it skips all of them and
still exits 0. Measured locally with actionlint 1.7.12 against a planted
`SC2086`:

| `shellcheck` on `PATH` | actionlint exit | output            |
| ---------------------- | --------------- | ----------------- |
| yes                    | 1               | `SC2086` reported |
| no                     | 0               | nothing at all    |

So if the runner image ever drops ShellCheck, or a caller runs the workflow on
a `runs-on` that lacks it, the job stays green and stops linting embedded
shell, with nothing in the log to say so. This is the worse of the two
problems, and it is conspicuous in a repo where `actionlint` and `shfmt` are
both pinned to an exact version with a verified checksum.

**The version floats.** Both workflows lint with the image's `shellcheck`, so a
runner image update changes what they report with no change to any pinned
version in any of the 26+ consuming repos. That is what #61 covers for the
tools that are pinned.

Intended outcome: `shellcheck` is pinned and checksum-verified like every other
tool this repo installs, the log carries positive evidence that `actionlint`
had something to shell out to, and CI proves the integration is live rather
than assumed.

### Upstream facts

`koalaman/shellcheck` v0.11.0 publishes no checksum file and no checksums in
its release notes, so the digests are committed here, as shfmt's are. Verified
against the release asset metadata and by extracting both archives:

- Assets: `shellcheck-v{version}.{os}.{arch}.tar.xz`, with `{os}` in
  `linux`/`darwin` and `{arch}` in `x86_64`/`aarch64` (so `arch-names:
amd64=x86_64 arm64=aarch64`, no `os-names`). All four platforms this repo
  supports have an asset.
- Member: `shellcheck-v{version}/shellcheck`, a regular file, listed with no
  `./` prefix, so GNU tar and bsdtar both accept that spelling.
- `.tar.xz` is the first xz asset this repo installs; `install-pinned-tool`
  already lets tar detect the compression, and nothing in CI exercises it yet.
- `shellcheck --version` prints the version on the **second** line, behind
  `ShellCheck - shell script analysis tool`.

## Changes

### 1. New `actions/set-up-shellcheck`

`action.yml` (`using: composite`) and `README.md`, modelled on
`actions/set-up-shfmt` (which is the closest precedent: committed checksums,
no upstream checksum file):

- `version` input, default `"0.11.0"`.
- `checksums` input, default the four committed `sha256sum`-format lines below.
- One step running the sibling
  `${{ github.action_path }}/../install-pinned-tool/install-pinned-tool.sh`
  through `env:`, with `ARCHIVE_MEMBER: shellcheck-v{version}/shellcheck`,
  `ARCH_NAMES: amd64=x86_64 arm64=aarch64`, and every unused installer
  variable set to `""` so a caller's job-level `env` cannot reach them.
  `INSTALLER` stays in `env:` for the `container:` path translation, as in the
  two existing wrappers.
- A `Report shellcheck version` step, matching its siblings.

The checksum table, used verbatim in all four places it appears:

```text
8c3be12b05d5c177a04c29e3c78ce89ac86f1595681cab149b65b97c4e227198  shellcheck-v0.11.0.linux.x86_64.tar.xz
12b331c1d2db6b9eb13cfca64306b1b157a86eb69db83023e261eaa7e7c14588  shellcheck-v0.11.0.linux.aarch64.tar.xz
3c89db4edcab7cf1c27bff178882e0f6f27f7afdf54e859fa041fca10febe4c6  shellcheck-v0.11.0.darwin.x86_64.tar.xz
56affdd8de5527894dca6dc3d7e0a99a873b0f004d7aabc30ae407d3f48b0a79  shellcheck-v0.11.0.darwin.aarch64.tar.xz
```

### 2. `.github/workflows/lint-github-actions.yml`

- Add `shellcheck-version` (default `"0.11.0"`) and `shellcheck-checksums`
  inputs, described like `lint-shell.yml`'s `shfmt-checksums`.
- Add an `Install shellcheck` step after `Install actionlint`, reusing the
  installer the existing `Fetch install-pinned-tool` step already downloads.
- Add a `Report tool versions` step before `Run actionlint`, printing
  `actionlint -version` and `shellcheck --version`. It is a hard guard as well
  as evidence: a missing binary exits 127 and fails the step. Comment it with
  why `shellcheck` is not optional here, in the terms the issue quotes from
  fosforo.
- Extend the fetch step's GHES error message to name `set-up-shellcheck`
  alongside `set-up-actionlint`.

No `run-shellcheck` toggle: `actionlint` always wants it.

### 3. `.github/workflows/lint-shell.yml`

- Add the same two inputs.
- Reorder so each tool's install sits next to its run: checkout, find scripts,
  fetch installer, install shellcheck, run ShellCheck, install shfmt, run
  shfmt check.
- Widen the fetch step's condition to
  `(inputs.run-shellcheck || inputs.run-shfmt) && steps.find-scripts.outputs.found == 'true'`,
  and update its comment, which currently says the step carries the shfmt
  install's condition.
- Update its GHES error message: with both linters needing the installer, the
  workaround is `set-up-shellcheck` plus `set-up-shfmt` in the caller's own
  job, not `run-shfmt: false`.

No separate report step here. `lint-shell.yml` runs `shellcheck` itself, so a
missing binary already fails the step through `xargs`; only the floating
version was wrong. The `Run ShellCheck` step prints `shellcheck --version`
before linting, so the log says which version produced the findings now that
a caller can override it.

### 4. `.github/workflows/run-ci.yml`

The `install-pinned-tool` matrix job (Linux amd64, Linux arm64, macOS arm64)
gains, mirroring how shfmt and actionlint are already covered:

- A direct `./actions/install-pinned-tool` install of shellcheck, which is the
  repo's first CI coverage of an xz archive.
- `shellcheck 0.11.0 --version` in the installed-binaries check. That loop
  truncates each tool's output to its first line, where shellcheck prints its
  version on the second, so change it to collapse newlines into spaces instead
  of truncating; the log stays one line per tool and every existing spec still
  matches.
- `shellcheck-bin` in the step that clears the direct installs.
- `Set up shellcheck through the wrapper`, plus shellcheck in the wrapper
  check.
- A new `Check actionlint runs shellcheck` step: pipe a workflow with a planted
  `SC2086` into `actionlint -` (it reads stdin, so no fixture file is needed
  and `lint-github-actions.yml` never sees one) and assert a non-zero exit and
  `SC2086` in the output. Keep the planted script inside single quotes so
  shellcheck does not flag the outer `run:` block. This is the regression guard
  for the whole bug class: if `actionlint` ever stops finding `shellcheck`, or
  changes how it discovers it, this fails.

  Only the positive case is asserted. Asserting that a missing `shellcheck`
  exits 0 would pin upstream's fail-open behavior, which is the behavior we
  would _want_ to see change.

The guard lives here rather than in `lint-github-actions.yml` deliberately.
This repo pins actionlint's default version and self-hosts its own workflows,
so a self-test here catches the regression at the commit that could introduce
it, without putting an output-format assertion into a workflow 26+ repos call.

### 5. Tracking and docs

- `scripts/check-tool-versions.py`: a `shellcheck` entry pinned at `0.11.0`
  against `github_latest_release("koalaman/shellcheck")`, with notes naming
  every site whose committed checksums and version strings must be regenerated
  on a bump (`set-up-shellcheck`, both lint workflows, `run-ci.yml`). Add
  shellcheck to the module docstring's list of hardcoded checksum tables.
- `cspell.json`: add `koalaman`. (`shellcheck` and `aarch64` are already
  accepted.)
- `docs/workflows/lint-github-actions.md` and `docs/workflows/lint-shell.md`:
  inputs tables, how shellcheck is installed and why, the reworded GHES and
  private-fork workarounds, and a usage example overriding the version with
  its checksum.
- `actions/set-up-actionlint/README.md`: a caveat that actionlint needs
  `shellcheck` on `PATH` to lint `run:` blocks, silently skips them without
  it, and pairs with `set-up-shellcheck`. A consumer composing
  `set-up-actionlint` by hand hits the same bug this issue is about.
- `actions/install-pinned-tool/README.md`: name `set-up-shellcheck` in the
  paragraph listing the wrappers that run the script.
- `README.md`: a `set-up-shellcheck` row in the Linting and formatting quick
  reference, and shellcheck in the trust model's committed-checksums list.
- `AGENTS.md`: the repository tree, the composite-vs-workflow paragraph naming
  the wrappers that run the installer, the SHA-256 checksum verification
  exceptions, and the pinning policy's binary-download bullet.
- `CHANGELOG.md` `[Unreleased]`: **Added** for `set-up-shellcheck` and the four
  new workflow inputs; **Fixed** for the vacuous pass in
  `lint-github-actions.yml` and the floating version in both workflows.

### Out of scope

- #61's broader floating-version concerns for tools that are already pinned.
- The remaining inline installers listed as out of scope in
  `docs/plans/done/2026-09-11-extract-pinned-tool-install-action.md`.
- Passing `actionlint -shellcheck <path>` explicitly. `GITHUB_PATH` prepends,
  so the pinned install already wins, and the version report prints what
  `PATH` resolves, which is the same binary actionlint finds.

## Commits

Conventional Commits, each referencing `(#85)`. `feat` for the additive
changes and `fix` for the behavior fix, rather than one prefix for the whole
issue: `/release` reads these to recommend the bump, and a new action plus new
inputs is a minor bump, not a patch.

1. `feat(set-up-shellcheck): install a pinned shellcheck (#85)`
1. `fix(lint-github-actions): install and report a pinned shellcheck (#85)`
1. `fix(lint-shell): lint with a pinned shellcheck (#85)`
1. `test(run-ci): assert actionlint shells out to shellcheck (#85)`
1. `chore(check-tool-versions): track shellcheck (#85)`
1. `docs: record the pinned shellcheck (#85)`

## Verification

Local, on this darwin/arm64 machine:

1. `make lint`, `make lint-yaml`, `make lint-md`, `make format-check`,
   `make spell`. Watch for yamllint `line-length`: the new `URL_TEMPLATE` is
   about 130 characters and passes only because
   `allow-non-breakable-inline-mappings` exempts a value with no spaces, the
   same exemption the actionlint template already relies on.
1. Drive `install-pinned-tool.sh` directly under `/bin/bash` (3.2) and under
   Homebrew bash, with `RUNNER_TEMP`, `GITHUB_PATH` and `GITHUB_OUTPUT` in the
   scratchpad, using the new URL template, arch renames, member and committed
   checksums. The installed binary should report `version: 0.11.0`, and
   `GITHUB_PATH` and `GITHUB_OUTPUT` should hold the expected lines.
1. Confirm the planted `SC2086` assertion the way `run-ci.yml` will run it, and
   confirm it fails when `shellcheck` is hidden from `PATH` (the table in
   Context, reproduced against the edited assertion).
1. Run `actionlint` over the edited workflows with the local shellcheck, to
   confirm the new `run:` blocks, including the single-quoted planted fixture,
   raise nothing.

In CI, on the PR:

1. `run-ci.yml`'s `actionlint` job exercises the new install and report steps
   in `lint-github-actions.yml` through the `job.workflow_*` fetch path.
1. Its `shell` job exercises `lint-shell.yml`'s pinned shellcheck against this
   repo's own scripts.
1. Its `install-pinned-tool` job exercises the direct xz install, the
   `set-up-shellcheck` wrapper and the planted-`SC2086` assertion on all three
   runners.
