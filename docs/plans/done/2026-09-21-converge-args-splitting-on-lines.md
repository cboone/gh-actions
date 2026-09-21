# Decide whether `*-args` splitting should converge on the line-based form

Closes [#96](https://github.com/cboone/gh-actions/issues/96).

## Context

[#89](https://github.com/cboone/gh-actions/issues/89) established that this
repository splits argument inputs two ways and documented both. It deferred the
question of whether they should converge on the line-based form, and that
deferral became #96.

That question has since been answered in practice, but nowhere that a reader
would find it. [#115](https://github.com/cboone/gh-actions/issues/115) shipped
in v4.0.0 and took the decision explicitly, in
`docs/plans/done/2026-09-20-bind-workflow-inputs-through-env.md`:

> **Splitting form.** `read -r -a` into a bash array, matching the Rust and Zig
> workflows and `.github/workflows/AGENTS.md`. The newline-delimited composite
> form would break every caller passing a multi-flag string.

Three things follow from that, and each makes converging a worse trade than #96
assumed when it was filed:

- **The scope is larger than #96 lists.** #96 names four `read -r -a` sites in
  two workflows. There are now ten, covering nine inputs across six workflows:
  `test-flags`, `goreleaser-args`, `test-args` (twice), `clippy-args`,
  `extra-components`, `build-args`, `fmt-paths`, `cross-targets` and `targets`.
- **The form is enforced and published.**
  `tests/fixtures/check-workflow-arg-binding.mjs` asserts a newline guard at
  every split site and pins the exact site list.
  `.github/workflows/AGENTS.md` instructs preserving the interface.
  `docs/migrations/v4.md` tells consumers that a multi-line value is rejected
  and to fold it onto one line. Converging would reverse that published advice
  one major after it shipped.
- **`goreleaser-args` is no longer a third case.**
  [#95](https://github.com/cboone/gh-actions/issues/95) closed as part of #115,
  so the item in #96's scope that asked to resolve it is already done, and it
  resolved toward `read -r -a`.

Against that, nothing is blocked. A code search across the `cboone`,
`swing-left` and `vote-forward` organizations finds no consumer setting
`test-args`, `clippy-args`, `build-args`, `goreleaser-args`, `fmt-paths`,
`cross-targets` or `extra-components`. The only consumer value found is a plain
space-delimited `test-flags`. No caller needs an argument containing a space
today, and the case that would silently lose data, a multi-line value, is
rejected with a diagnostic rather than truncated.

**Outcome:** the two forms stay. The work is to record that decision where a
future reader or agent will meet it, so the question is not reopened from the
same stale premise a third time.

## Decision

Composite actions keep one argument per line, parsed with `while IFS= read -r`.
Reusable workflows keep `read -r -a` with the newline guard. Revisit only for a
caller that actually needs an argument containing a space, and then only
alongside other breaking changes in the same major.

## Changes

### 1. `docs/development.md`, § Shell Conventions

Add a continuation paragraph to the second bullet, the one describing the
reusable-workflow form, after the sentence ending `which is not redundant.`
The section currently states both forms without saying why they differ or that
the difference is intentional, which is the gap that let #89 and #96 both treat
it as an oversight. The file already uses blank-line-separated continuation
paragraphs inside list items (see the reuse dependency note at line 120) and
bare `(#85)`-style issue references (line 80).

Proposed wording:

> The divergence from the composite form is deliberate and settled (#96).
> Converging the workflows on one argument per line would turn a caller's
> `test-args: --all-features --no-fail-fast` into a single malformed argument,
> a second breaking migration one major after v4 bound these inputs through
> `env:` and told callers to fold multi-line values onto one line. What the
> line form buys is an argument containing a space, which no current consumer
> passes, and the case that would otherwise lose data is rejected with a
> diagnostic rather than truncated. Composite actions carry no equivalent
> installed base, so they keep the more capable form. Revisit only for a caller
> that needs it, and alongside other breaking changes in the same major.

### 2. `.github/workflows/AGENTS.md`

The bullet at line 8 already says `Preserve this interface instead of adopting
composite actions' newline-delimited convention.` Extend that sentence to name
the settled question and where the reasoning lives, so an agent reading only
the scoped instructions knows the decision exists rather than inferring a
defect:

> Preserve this interface instead of adopting composite actions'
> newline-delimited convention; #96 settled that, and the development
> reference records why.

### 3. Close #96 with the reasoning

Post a comment on #96 recording the decision, the three findings above, and the
condition under which it would be revisited, then let the pull request close the
issue. A question issue should carry its answer, not just a closed state.

## Explicitly not doing

Each of these is a scope item from #96 that the decision makes void. Listing
them keeps the next reader from treating the issue body as an unfinished
checklist:

- Rewriting the split sites to `while IFS= read -r`.
- Reverting the `### Shell Conventions` bullets to a single convention.
- Changing the two bullets in `.github/copilot-instructions.md`. Lines 24 and 25
  already describe both forms correctly and tell reviewers not to propose
  converging them.
- Changing the `*-args` descriptions in `docs/workflows/run-rust-ci.md` and
  `docs/workflows/release-rust-binaries.md` to say "one per line". They
  correctly say the value is split on whitespace.
- Writing `docs/migrations/v5.md`. Nothing breaks.
- Sweeping consuming repositories for values needing a rewrite. The sweep was
  run to make the decision, not to prepare a migration, and found nothing to
  rewrite.

No `CHANGELOG.md` entry. This records why existing behavior is what it is and
changes nothing a consumer can observe, matching how `8cf53e5` and similar
documentation-only commits landed.

## Verification

```bash
make format-check   # Prettier, including the new continuation paragraph
make lint-md        # markdownlint
make spell          # cspell
make lint-yaml      # yamllint, unchanged files but cheap
```

No workflow or fixture changes, so `make lint` (actionlint) and the
`workflow-arg-binding` job cover the same ground they did before. Confirm that
by rereading the diff: it must touch only `docs/development.md`,
`.github/workflows/AGENTS.md` and this plan.

Then read `docs/development.md` § Shell Conventions and
`.github/workflows/AGENTS.md` end to end and check that a reader who arrives
with the question #96 asks finds the answer without opening GitHub.

## Observed, not changed

`CHANGELOG.md:867`, in the released v1.0.0 section, reads `Split composite
action args with read -r -a using newline-delimited inputs`, which describes two
mutually exclusive things. It predates the March 2026 change recorded in
`docs/plans/done/2026-03-08-fix-composite-action-args-spacing.md` that moved
composite actions to the line form. Released changelog sections are a historical
record, so leave it. Worth a separate issue if the wording keeps misleading
readers.
