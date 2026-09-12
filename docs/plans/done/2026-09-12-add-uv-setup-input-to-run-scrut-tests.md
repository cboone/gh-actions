# Add a uv setup input to run-scrut-tests.yml

## Context

`run-scrut-tests.yml` installs and checksum-verifies scrut, but it offers no
first-class way to put a language runtime on `PATH` first. A CLI written in an
interpreted language cannot run a single test without one, and the only hook
the workflow exposes is `scrut-setup-cmd`, a `run:` string. A `uses:` step
cannot be templated into it, because GitHub Actions does not accept expressions
in `steps.uses`.

Consumers therefore hand-roll the install. `cboone/audio-tools` ships PEP 723
scripts with `#!/usr/bin/env -S uv run --script` shebangs and currently passes:

```yaml
scrut-setup-cmd: >-
  pipx install 'uv==0.12.7' && echo "$HOME/.local/bin" >> "$GITHUB_PATH"
```

That line reaches for a package manager only because the runner's system Python
is externally managed (PEP 668), it pins uv outside this repo, and the obvious
alternative is an unpinned pipe-to-shell. None of that is the consumer's
problem to solve.

Adding `setup-uv` gives the workflow one pinned, checksum-verified uv install,
keeps the pin inside `gh-actions` alongside every other tool version, and
retires the workaround.

Resolves [#82](https://github.com/cboone/gh-actions/issues/82).

## Decisions

Four choices were settled before drafting, and the rest of this plan assumes
them.

**uv only.** GitHub runners already ship Node, Python, Ruby and Go. uv, Bun and
Deno are the genuinely absent runtimes, and uv is the only one with a concrete
consumer. Bun and Deno ship `.zip` assets that `install-pinned-tool` cannot
handle, so they would each need a first-time third-party action pin for a
speculative need. Left out.

**Install through `install-pinned-tool.sh`, not `astral-sh/setup-uv`.** The
repo's founding plan inventoried `astral-sh/setup-uv` in consuming repos and
marked it "Replace. Installs uv. Direct install script is equivalent."
(`docs/plans/done/2026-03-07-reusable-actions-and-workflows.md:38`). That
decision has been carried out in four places, and #87 generalized it into
`actions/install-pinned-tool`, whose uv recipe is already exercised by
`run-ci.yml:92-102` on Linux amd64, Linux arm64 and macOS arm64. A composite
wrapper is not an option here: a reusable workflow cannot reference a sibling
action by `./` path, so wrapping would mean self-referencing
`cboone/gh-actions/actions/set-up-uv@<sha>` and re-pinning it every release.

**Boolean toggle plus a version input.** `setup-uv` (boolean, default `false`)
matches `lint-text.yml`'s `run-*` toggles; `uv-version` (string, default
`"0.11.8"`) matches the input name and default already used by
`actions/run-reuse/action.yml:11-14`, and keeps the repo's pinned-default
convention so consumers need not name a version.

**Self-host the new path.** `run-scrut-tests.yml` is currently the only
reusable workflow in the repo with no self-test at all, which is a gap
`AGENTS.md:358-366` claims does not exist.

## Changes

### 1. `.github/workflows/run-scrut-tests.yml`

Add two inputs, after `scrut-setup-cmd` and before `runs-on`:

| Name         | Type    | Default  | Description                                   |
| ------------ | ------- | -------- | --------------------------------------------- |
| `setup-uv`   | boolean | `false`  | Install uv and add it to `PATH` before setup  |
| `uv-version` | string  | `0.11.8` | uv version to install when `setup-uv` is true |

Add two steps between `actions/checkout` and the existing `Scrut test setup`
step, both gated on `if: inputs.setup-uv`. Ordering matters: uv must land on
`PATH` before `scrut-setup-cmd` runs, so a consumer can use `uv sync` or
`uv run` there. This also matches `run-go-ci.yml:257-271` and
`run-zig-ci.yml:275-315`, where the language setup precedes `Scrut test setup`.

The first step fetches the installer, copying `lint-shell.yml:84-113` verbatim
apart from the error message: bind `job.workflow_repository` and
`job.workflow_sha` in `env:` (the `job` context is only available on steps),
fail with an `::error::` annotation naming `setup-uv: false` as the GitHub
Enterprise Server workaround, then `curl -sSfL --proto '=https' --retry 3
--retry-delay 5 --retry-all-errors` the script to `${RUNNER_TEMP}`.

The second step runs it with the uv recipe already proven in `run-ci.yml`:

```yaml
- name: Install uv
  if: inputs.setup-uv
  env:
    TOOL: uv
    VERSION: ${{ inputs.uv-version }}
    URL_TEMPLATE: https://github.com/astral-sh/uv/releases/download/{version}/uv-{arch}-{os}.tar.gz
    CHECKSUMS_URL_TEMPLATE: https://github.com/astral-sh/uv/releases/download/{version}/uv-{arch}-{os}.tar.gz.sha256
    OS_NAMES: linux=unknown-linux-gnu darwin=apple-darwin
    ARCH_NAMES: amd64=x86_64 arm64=aarch64
    ARCHIVE_MEMBER: uv-{arch}-{os}/uv
  run: bash "${RUNNER_TEMP}/install-pinned-tool.sh"
```

Only `uv` is installed, not `uvx`, matching `actions/run-reuse/action.yml:76`.
`uv tool run` is the equivalent, and a second invocation would re-download the
whole tarball to extract one more member.

### 2. Self-test fixture

New files, the repository's first scrut coverage:

- `tests/fixtures/hello.py` — a PEP 723 script with a
  `#!/usr/bin/env -S uv run --script` shebang, an inline `# /// script` block
  requiring a Python the runner already has, and a single `print`.
- `tests/scrut/setup-uv.md` — a scrut test asserting that `uv --version`
  answers at all and that the fixture script runs and prints its line. The
  version is matched with `(glob)`, not pinned: `run-ci.yml:112` already
  asserts the exact uv version for the same install path, and a glob keeps the
  fixture runnable against a local uv.

Invoke the `write-scrut-tests` skill before authoring the test file. Write both
files clean against Prettier, markdownlint and cspell rather than adding ignore
entries; Prettier leaves fenced blocks of unrecognized languages alone, so the
scrut assertions survive formatting. Add ignores only if that turns out to be
false.

### 3. `.github/workflows/run-ci.yml`

Add a `scrut` job alongside the existing `actionlint`, `text` and `shell` jobs:

```yaml
scrut:
  uses: ./.github/workflows/run-scrut-tests.yml
  with:
    setup-uv: true
    scrut-test-dir: tests/scrut/
    scrut-env: |
      HELLO_BIN=./tests/fixtures/hello.py
      UV_PYTHON_PREFERENCE=only-system
```

`UV_PYTHON_PREFERENCE=only-system` keeps uv from downloading a managed CPython
build for a script the runner's own interpreter already satisfies. Passing
`HELLO_BIN` as a `./` path also exercises `scrut-env`'s relative-to-absolute
fixup.

### 4. Documentation

- `docs/workflows/run-scrut-tests.md` — two rows in the Inputs table, an
  `### Installing uv` subsection under Inputs (the shape `lint-text.md` uses
  for per-input explanation), and a third Usage example showing a PEP 723 CLI.
  Keep the `@v3.1.1` pin the other examples use.
- `AGENTS.md` — add `tests/` to the Repository Structure tree, and extend the
  Testing section (`:358-366`) to say `run-ci.yml` now calls
  `run-scrut-tests.yml` against that fixture with `setup-uv` enabled.
- `CHANGELOG.md` — an entry under `## [Unreleased]` → `### Added`, ending in
  `(#82)`.
- `scripts/check-tool-versions.py` — add a `notes=` argument to the existing
  `Tool("uv", "0.11.8", ...)` entry at line 125, in the style of the
  `actionlint` entry, listing every place the uv pin has to be bumped
  together.
- `cspell.json` — add `pipx`, which this plan quotes from the issue.

No change is needed to `.github/dependabot.yml` (the `/` github-actions entry
already covers every workflow, and no new `uses:` reference is added), to
`README.md` (the Quick Reference carries only a one-line summary, which is
still accurate), or to `.github/copilot-instructions.md`.

## Out of scope

`run-go-ci.yml` and `run-zig-ci.yml` have their own scrut jobs with the same
`scrut-setup-cmd` escape hatch, and `run-go-ci.yml:52` even documents it as the
place to "install extra dependencies like uv or Python tools". Their consumers
already have a language runtime, so extending `setup-uv` to them is a separate
question. Likewise, refactoring the three other hand-rolled uv installs
(`lint-text.yml:283-303`, `check-tool-versions.yml:32-48`,
`actions/run-reuse/action.yml:25-78`) onto `install-pinned-tool` is worthwhile
but unrelated to this issue. Both are follow-up candidates.

## Verification

Local, before pushing:

```bash
make lint          # actionlint over the changed workflows
make lint-yaml     # yamllint
make lint-md       # markdownlint over the new test and docs
make format-check  # Prettier
make spell         # cspell over the plan, docs and fixture
```

Then confirm the scrut fixture passes against a local uv, so CI is not the
first place it runs:

```bash
scrut test tests/scrut/
```

In CI, the new `scrut` job in `run-ci.yml` is the end-to-end check. It must
show uv installed at the pinned version from `${RUNNER_TEMP}/uv-bin/uv`, the
PEP 723 script executing without a managed-Python download, and the scrut
assertions passing. A failure in the `Fetch install-pinned-tool` step means
`job.workflow_sha` did not resolve for a local `./` workflow reference, which
would contradict how `lint-shell.yml` already works in the same file.

Finally, verify the negative case: with `setup-uv` left at its default, no uv
step runs and the workflow behaves exactly as it does today.
