<!-- cspell:ignore returncode -->

# Batch lint-shell script discovery (#124)

## Context

`lint-shell.yml`'s **Find shell scripts** step spawns one `shfmt -f` process per
tracked file, inside a `while` loop over `git ls-files -z`. On a repository with
many tracked files that is thousands of processes to answer a question one call
can answer.

The loop exists because shfmt's NUL-separated find mode, `-f=0`, listed
explicitly supplied non-shell files until 3.14.1. #61 pinned 3.14.1 as the
default but left the loop in place, because `shfmt-version` is a caller
overridable input: a consumer pinning an older shfmt would still reach a batched
path and would silently get prose, JSON and binaries fed to ShellCheck and the
format check.

Measured here against shfmt 3.14.1, batching is now safe and path-faithful. One
`shfmt -f=0` call over `./-`, `-leading-dash`, a path with spaces, a path with a
literal newline, a nested `.sh` and a prose file returns exactly the four shell
files, in input order, with every original path byte-for-byte intact.

The outcome is that a default run discovers in one pass, while a caller who
pins an older shfmt keeps today's correct behavior rather than silently linting
non-shell files.

## Decision: probe the binary, then fall back

Discovery measures the installed shfmt once, by asking it to classify a prose
file in NUL-separated find mode:

- The binary filters it out, so the batched path runs.
- The binary echoes it back, or rejects `-f=0` outright, so the per-file loop
  runs and a `::notice::` says why.

A behavioral probe rather than a parsed `shfmt --version`, because the version
string reads `(devel)` for a source build, says nothing about backports, and
cannot distinguish a release that lacks the `-f=0` flag entirely from one that
has it and gets it wrong. The probe tests the exact property discovery depends
on.

This keeps `shfmt-version`'s contract unchanged, so no major release and no
migration guide.

## Changes

### 1. `.github/workflows/lint-shell.yml` — the **Find shell scripts** step

Restructure into three parts. Load the `write-bash-scripts` skill first.

**Filter once, into a shared manifest.** Keep today's `git ls-files -z` read and
its two guards, but write the surviving paths to
`${RUNNER_TEMP}/discovery-input.txt` instead of testing each one with shfmt. This
loop spawns nothing; the `[[ -f ]]` / `[[ -L ]]` tests are shell builtins.

- `[[ ! -f "${path}" || -L "${path}" ]]` still drops submodule directories and
  symlinks to untracked files. This guard is load-bearing for the batched path
  too: a directory argument makes shfmt walk it, which would pull untracked
  files out of a submodule.
- `-` still becomes `./-`, and the batched call preserves that spelling.
- Redirect the whole loop once (`done < ... > ...`) rather than appending per
  iteration.

Truncate `${RUNNER_TEMP}/shell-scripts.txt` up front, as today, so a stale
manifest cannot leak between runs. If `discovery-input.txt` is empty, skip both
the probe and discovery and fall straight through to the existing `found=false`
notice and job-summary write.

**Probe.** Write a prose file with no shell extension and no shebang to
`${RUNNER_TEMP}`, then classify it:

```bash
batched=true
if ! shfmt -f=0 -- "${probe}" > "${probe_out}"; then
  batched=false
elif [[ -s "${probe_out}" ]]; then
  batched=false
fi
```

`if !` is what keeps a shfmt too old to accept `-f=0` from aborting the step
under `set -e`; its stderr still reaches the log and explains the fallback. The
probe lives in `RUNNER_TEMP`, outside the checkout, so it cannot reach the
manifest.

**Discover.** One call, or the loop:

```bash
if [[ "${batched}" == true ]]; then
  xargs -0 shfmt -f=0 -- < "${RUNNER_TEMP}/discovery-input.txt" \
    > "${RUNNER_TEMP}/shell-scripts.txt"
else
  echo "::notice::${msg}"
  while IFS= read -r -d '' path; do
    shfmt -f -- "${path}" > "${RUNNER_TEMP}/shell-candidate.txt"
    if [[ -s "${RUNNER_TEMP}/shell-candidate.txt" ]]; then
      printf '%s\0' "${path}"
    fi
  done < "${RUNNER_TEMP}/discovery-input.txt" \
    >> "${RUNNER_TEMP}/shell-scripts.txt"
fi
```

Plain `xargs -0`, matching the neighboring **Run ShellCheck** step; the
emptiness guard above means it never sees empty input, so `-r` is unnecessary.
`xargs` chunking keeps the call within `ARG_MAX` and preserves input order
across chunks.

Build the notice with the `msg=` accumulation this file already uses, and have
it name both causes and the remedy: the pinned shfmt does not filter explicitly
supplied non-shell files in its NUL-separated find mode, so discovery is
checking one file at a time; pin shfmt 3.14.1 or later for a single pass.

Send it to `::notice::` only, not to `GITHUB_STEP_SUMMARY`, which the existing
test asserts stays empty on the success path.

Replace the `#124` comment with one explaining the probe.

### 2. `tests/check-shell-discovery.py` — drive both branches

The existing cases must pass unchanged. They will: whichever branch the runner's
shfmt selects, the manifest is the same.

Add a `shfmt` shim helper that writes a wrapper into a directory prepended to
`PATH`, passing the real shfmt's absolute path through the environment. Two
shims, each intercepting `-f=0` only and delegating everything else with `exec`:

- **legacy**: prints every explicit file argument NUL-separated, reproducing the
  pre-3.14.1 echo-back. Forces the fallback branch.
- **modern**: calls the real shfmt with `-f` once per argument and emits the
  path NUL-separated when that output is non-empty. An independent oracle for
  the fixed `-f=0`, and path-faithful, so the `tools/path\nwith newline` fixture
  survives it where a newline-mode shim would not. Forces the batched branch.

New assertions against the populated fixture:

1. Under the legacy shim, the manifest equals `expected` and the slow-path
   notice appears.
2. Under the modern shim, the manifest equals `expected` and the notice does
   not appear.
3. Both equal the manifest the real shfmt produces, which is the property that
   makes the fallback trustworthy.
4. The probe file's path appears in neither manifest.
5. The empty index and the non-shell-only index still report `found=false`
   under both shims, covering the emptiness guard on the batched path.

The shims make this hermetic: no download, no second shfmt install, correct
whichever version CI happens to have.

### 3. `docs/workflows/lint-shell.md`

Rewrite the discovery paragraph. It currently ends by citing #124 as pending
work. Replace it with what the step now does: one `shfmt -f=0` call over the
tracked regular files, original paths retained in a NUL-separated manifest, `-`
passed as `./-`, submodule contents and symlinks excluded; and the probe, said
plainly, including that an older pin still discovers correctly, one file at a
time, and emits a notice. Load `write-markdown` first.

Leave the Usage example pinning `shfmt-version: 3.13.1` alone. It still works,
and it is now also the documented illustration of the fallback.

### 4. `CHANGELOG.md`

Add a `### Changed` entry under `## [Unreleased]` in the house style: what
changed, why the loop existed, and what an older pin gets. Reference `(#124)`.

### 5. `docs/development.md`

Add a sentence to the testing section recording that `check-shell-discovery.py`
drives both discovery branches with `shfmt` shims, and that real-binary coverage
of both comes free: the `install-pinned-tool` matrix runs the test under a real
3.13.1 on three runners, exercising the fallback, while the `shell` and
`shellcheck-only` jobs call `lint-shell.yml` at the default 3.14.1, exercising
the batched path against this repository's own tree.

## Verification

Local:

1. `uv run tests/check-shell-discovery.py` — all cases, both shims. Local shfmt
   is 3.14.1, so the real-binary run takes the batched path.
2. Plant a defect to prove the new code can fail: make the modern shim drop a
   discovered path and confirm assertion 3 goes red; make the batched branch
   skip the `[[ -L ]]` guard and confirm the symlink fixture appears. Revert
   both.
3. `make lint`, `make lint-md`, `make format-check`, `make spell`,
   `make lint-yaml`. Run `make format` first if Prettier reflows anything.
4. `uv run scripts/check-tool-versions.py` — no version strings move, so this
   must still pass clean.

On the pull request:

- `install-pinned-tool` (ubuntu-latest, ubuntu-24.04-arm, macos-latest) runs the
  test under a real shfmt 3.13.1, which is the fallback branch against the
  actual old binary rather than a shim.
- `shell` and `shellcheck-only` run `lint-shell.yml` at the default 3.14.1 over
  this repository, which is the batched branch end to end. Both must find the
  same scripts the current workflow finds; a regression shows up as ShellCheck
  or shfmt findings on files that are not shell.

Not covered: a shfmt old enough to reject `-f=0` outright. The probe handles it
by construction and the legacy shim covers the echo-back case, but no such
binary is installed anywhere in CI.

## Plant table

Measured, not predicted. Each defect was planted on its own against the
committed check, the suite run, and the tree reverted. The `->` column records
what fired, which is not always the assertion the row was written to test.

| Planted defect                                                            | Instrument expected to catch it            | What actually happened                                                                                                                  | Test that covers it now                                        |
| ------------------------------------------------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Drop the `[[ -L ]]` guard, so symlinks reach the batched call             | Manifest equality                          | FAILED, `assert manifest(runtime) == expected, found`                                                                                   | `Tracked discovery`                                            |
| Remove the `-` to `./-` rewrite                                           | Manifest equality                          | FAILED, same assertion                                                                                                                  | `Tracked discovery`                                            |
| Append a `RUNNER_TEMP` probe artifact to the discovery input              | A dedicated no-probe-in-manifest assertion | FAILED, but on plain manifest equality at the real-binary run. The dedicated arm could never be the one to fire                         | `Tracked discovery`. The dedicated arm was removed as subsumed |
| Invert the probe verdict, `elif [[ ! -s ]]`                               | Wrapper manifest equality                  | FAILED, `assert manifest(runtime) == expected, (label, shimmed)`                                                                        | `Batched and per-file discovery agree`                         |
| The same, with the legacy and modern wrappers deleted                     | Nothing                                    | PASSED, defect invisible. A clean-tree control with those wrappers deleted also passed, so the suite still ran                          | Those two wrappers are the only coverage                       |
| Print the slow-path notice on the batched branch too                      | The notice assertion                       | FAILED, `assert (SLOW_PATH_NOTICE in shimmed.stdout) == (label != "modern")`                                                            | `Batched and per-file discovery agree`                         |
| Make the modern wrapper's oracle drop every path                          | Wrapper manifest equality                  | FAILED, so the oracle is load-bearing rather than agreeing trivially                                                                    | `Batched and per-file discovery agree`                         |
| Drop the `!` from the probe guard                                         | The refusing wrapper                       | FAILED on the notice assertion, but through the modern wrapper: deleting the refusing wrapper still failed. Not this wrapper's coverage | `Batched and per-file discovery agree`                         |
| Remove the probe guard entirely, so a non-zero probe exit aborts the step | The refusing wrapper                       | FAILED, `assert shimmed.returncode == 0`. Deleting the refusing wrapper made it pass, so this row is that wrapper's alone               | `Batched and per-file discovery agree`, refusing wrapper       |

Two corrections this produced. The no-probe-in-manifest assertion was written
and then measured to be unreachable, so it was deleted rather than left as an
arm that reads like a check and is not one. And the message on commit
`c45e2f4` claims the refusing wrapper is what catches a dropped `!`; the row
above shows the modern wrapper catching it, and the row below it is the one the
refusing wrapper actually carries. The commit stands as written because history
is not rewritten here; this table is the correction.

Rows nothing covers: the batched call is never exercised against a real shfmt
3.14.1 from inside this check on a runner that pins 3.13.1 for the installer
cases. The `shell` and `shellcheck-only` jobs cover that against this
repository's own tree instead, which is why they are named in the reference.

## Commits

Conventional Commits, signed, `(#124)` on each:

1. `perf: discover shell scripts in one batched shfmt call (#124)` — the
   workflow step and the test together, since the test executes the literal run
   block and the two cannot land apart.
2. `docs: record batched shell discovery and its fallback (#124)` —
   `docs/workflows/lint-shell.md`, `docs/development.md`, `CHANGELOG.md`.
