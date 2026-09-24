# Review instructions

<!-- BEGIN set-up-review-config -->

## What Important means here

Reserve Important for findings that would break behavior, lose or leak data, or break the build or a release, and for the checklist rules below. Other style, naming and wording findings are Nit at most.

### write-bash-scripts (Bash script files)

- **Strict mode**: An executable script sets `set -euo pipefail` near the top. Sourced libraries are exempt.
- **Quoted expansions**: Variable expansions and command substitutions are quoted, as in `"${var}"` and `"$(cmd)"`, unless word splitting is intended and commented.
- **Arrays for lists**: Lists of arguments or file names are held in arrays and expanded as `"${array[@]}"`, never built by splitting a string.
- **Masked exit codes**: `local` or `readonly` is declared separately from a command substitution, so the command's failure is not hidden behind the declaration's success.
- **Checked commands**: A command whose failure matters is checked with `if` or `||` wherever `set -e` does not apply, such as inside conditions, functions called from conditions, and non-final pipeline stages.
- **Safe increments**: Counters use `((i += 1))`, not `((i++))`, which returns a failure status when `i` is 0 and so exits under `set -e`. The increment in a `for ((...))` header is fine.
- **No eval**: `eval` is not used, especially on anything built from input; arrays replace it.
- **Pipeline scope**: Variables set inside `cmd | while read` are not relied on afterwards, since the loop runs in a subshell. Process substitution (`done < <(cmd)`) keeps them.
- **Safe temporary files**: Temporary files and directories come from `mktemp` and are removed by a `trap ... EXIT` handler.
- **Option-safe globs**: Wildcards that reach commands such as `rm` start with `./`, so a file name beginning with `-` is not parsed as an option.
- **No ls parsing**: File lists come from globs or `find -print0`, never from parsing `ls` output.
- **Privileged writes**: Root-owned files are written with `sudo tee`, not `sudo echo ... >`, and scripts never rely on SUID or SGID.
- **Bash 3.2 compatibility**: A script that can run on a stock Mac avoids `readarray`, `mapfile`, `declare -A`, `${var,,}`, namerefs and `[[ -v ]]`, and guards possibly empty arrays under `set -u` as `${array[@]+"${array[@]}"}`. A script that needs bash 4 checks `BASH_VERSINFO` and exits with a clear message.

### write-scrut-tests (Scrut test files)

- **Binary through a variable**: Tests call the tool under test through an environment variable such as `"${TOOL_BIN}"`, never through a fixed or relative path.
- **Asserted exit codes**: Every block that expects a failure ends with its exit code, such as `[1]`.
- **Isolated side effects**: Commands that create, modify or delete files run in a temporary directory from `$(mktemp -d "${TMPDIR:-/tmp}/scrut.XXXXXX")`, never in the repository or a fixed location.
- **Deterministic output**: Output whose order can vary is sorted, and versions, timestamps, hashes and paths are matched with `(glob)`, so the test does not fail at random.
- **Intentional snapshot updates**: After a snapshot update, `(glob)` and `(regex)` lines have not been replaced with the literal values of one run.
- **One command per zsh block**: In zsh plugin tests, each block has a single `$` line, because further `$` lines are read as expected output, and `ERR_EXIT` is not set at file level.

### write-markdown (Markdown files)

- **Working links**: Relative links point to files that exist, and heading anchors match a heading that exists, after renames and moves in the same pull request.
- **Defined references**: Every reference-style link has a matching definition.
- **Rendered structure**: Blank lines surround headings, lists, code blocks, block quotes and tables, so each renders as intended instead of merging into the paragraph above it.
- **Consistent tables**: Every table row has the same number of columns as the header row, so no cell is dropped or shifted.

## Nits

This file does not carry the checklists' Nit rules. An agent reading it may not open another file, so what it guarantees is the Important rules above; the full Nit lists live in the checklists under `.github/skills/code-review/`, where Copilot code review applies them file by file. Report the Nits you can see in the diff yourself, and when one matches a rule you know from a checklist, start the finding with the checklist name and the rule name, for example `write-go-code: Checked errors`.

## Cap the nits

Report at most five Nits per review. If you found more, say "plus N similar items" in the summary instead of posting them inline. If everything you found is a Nit, lead the summary with "No blocking issues."

## After the first review

On later reviews of the same pull request, post Important findings only and do not raise new Nits.

## Do not report

- Anything these CI checks already report: `actionlint`, `shellcheck`, `shfmt`, `markdownlint-cli2`, `prettier`, `cspell`, `yamllint`.
- Changes in these paths: `package-lock.json`, `actions/set-up-scrut/Cargo.lock`, `docs/plans/done/**`, `tests/fixtures/cspell-extra-dict/**`, `.github/skills/code-review/*.md` except `SKILL.md`.
- Anything a checklist's Do not flag section excludes.

Rules outside this block take precedence over it.

<!-- END set-up-review-config -->

## Always check

Repository-specific rules that no CI check and no installed checklist covers, so review is the only thing that catches a regression.

- **SHA-pinned actions**: Every remote `uses:` reference is a full 40-character commit SHA with a trailing version comment, including org-controlled actions. A bare or floating semver tag is insufficient. The one documented exception is `dtolnay/rust-toolchain`, which keeps a dated default-branch comment because upstream publishes no semver tags; do not report it as unpinned.
- **Checkout credentials**: Every `actions/checkout` step sets `persist-credentials: false`, so the job's token does not stay in `.git/config` for later steps and workspace uploads to read. The one documented exception is the Homebrew tap checkout in `release-rust-binaries.yml`, which sets `true` because the push step that follows needs it; do not report that one. A new checkout that persists its credential also needs an entry in `tests/check-checkout-credentials.mjs` naming the consuming step. See [checkout credentials](docs/development.md#checkout-credentials).
- **Verified downloads**: A new binary download carries a SHA-256 verified before the bytes are used, a new Python dependency a reviewed hash manifest, and a new npm tool an exact version with lockfile integrity. Never leave an upstream registry as the sole integrity boundary for CI. See the [pinning policy](docs/development.md#pinning-policy-and-trust-model) for the checksum exceptions that are already settled.
- **Component documentation in the same change**: A new composite action adds `actions/<name>/README.md` and a new reusable workflow adds `docs/workflows/<name>.md`, in the same change as the `action.yml` or workflow file, along with a row in the root README's Quick Reference. A breaking release adds `docs/migrations/vN.md` and links it.
- **CHANGELOG before a release tag**: A release tag's matching CHANGELOG section exists before the tag is pushed. Tag-triggered CI creates the GitHub Release, so a manually created release is a defect.
