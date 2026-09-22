# Branch Review: fix/133-disable-checkout-credential-persistence

Base: main (merge base: bbe1518)
Commits: 2
Files changed: 35 (2 added, 33 modified, 0 deleted, 0 renamed)
Reviewed through: 4cea761

## Summary

Every `actions/checkout` in the repository now sets `persist-credentials: false`, so the job's
token no longer sits in `.git/config` where later steps and workspace uploads can read it. One
checkout keeps its credential, the Homebrew tap checkout in `release-rust-binaries.yml`, and it
now says so explicitly and carries a name. A new `checkout-credentials` CI job runs
`tests/check-checkout-credentials.mjs` over every workflow and composite action so the default
cannot come back unnoticed, and the rule is written into the trust model, the review checklists
and the agent instructions.

## Changes by Area

### Workflow security

`persist-credentials: false` added to 44 checkout steps across 18 workflow files. The 45th, the
Homebrew tap checkout, gains `persist-credentials: true`, a `name:`, and an eight-line comment
naming the step that consumes the credential and recording that the token is the caller's
tap-scoped `HOMEBREW_TAP_TOKEN` in `homebrew-tap/.git/config` rather than the job's
`GITHUB_TOKEN`.

Files: all 18 of `.github/workflows/*.yml` that contain a checkout.

### Test infrastructure

`tests/fixtures/workflow-steps.mjs` gains `allSteps()`, with `runSteps()` and a new
`usesSteps()` filtering it. This replaces three near-identical copies of the workflow and action
walk rather than adding a fourth. `tests/check-checkout-credentials.mjs` asserts the policy and
is wired into a new single-runner `checkout-credentials` job.

Files: `tests/fixtures/workflow-steps.mjs`, `tests/check-checkout-credentials.mjs`,
`.github/workflows/run-ci.yml`.

### Documentation and review configuration

A new `### Checkout Credentials` section in the trust model, a step in the "Adding a New
Workflow" checklist, a rule in `REVIEW.md`'s "Always check" list, a note in the Copilot review
conventions explaining the intentional exception, bullets in the root and workflow agent
instructions, a paragraph in the README trust-model summary, and caller-visible notes in five
workflow docs.

Files: `docs/development.md`, `REVIEW.md`, `.github/copilot-instructions.md`, `AGENTS.md`,
`.github/workflows/AGENTS.md`, `README.md`, `actions/create-pull-request/README.md`,
`docs/workflows/{deploy-to-pages,run-go-ci,run-zig-ci,run-scrut-tests,release-rust-binaries}.md`,
`CHANGELOG.md`, `cspell.json`.

## File Inventory

Added (2):

- `tests/check-checkout-credentials.mjs`
- `docs/plans/todo/2026-09-21-disable-checkout-credential-persistence.md`

Modified (33):

- 18 workflow files under `.github/workflows/`
- `.github/workflows/AGENTS.md`, `.github/copilot-instructions.md`
- `AGENTS.md`, `README.md`, `REVIEW.md`, `CHANGELOG.md`, `cspell.json`
- `docs/development.md`, 5 files under `docs/workflows/`
- `actions/create-pull-request/README.md`
- `tests/fixtures/workflow-steps.mjs`

No files were deleted or renamed.

## Notable Changes

- **Security-relevant by design.** This is the `artipacked` exposure class. The behavior change
  is real for the four workflows that accept a caller-supplied command (`build-command`,
  `scrut-setup-cmd`, `scrut-build-cmd`): those commands no longer inherit a Git credential.
- **Not a breaking release, and the claim is evidenced.** Every value in use across the consuming
  repositories is a tool install or a compile: `go run ./build.go` (that file contains no `git`
  and no `exec.Command`), `"true"`, `go build -o ./bin/quod ./cmd/quod`, and several uv/zsh
  installs. None runs an authenticated Git operation.
- **New CI job**, adding roughly one runner-minute per CI run (checkout, Node, `npm ci`, a YAML
  read).
- **`cspell.json`** gains `artipacked`, `extraheader`, `unsets`, `zizmor`.
- **No dependency changes.** `package.json` and `package-lock.json` are untouched; the checker
  uses the already-pinned `yaml` devDependency.

## Plan Compliance

**Verdict: strong compliance.** Every planned change landed, and the two scope additions are
both justified rather than drift. Two items from the plan's own verification section remain
open, neither of which is a code defect.

**Overall progress: 5/5 change sections done (100%); 4/6 verification steps done (67%).**

### Done

1. **`persist-credentials: false` on every checkout** — the plan said 43 of 44; the branch has 44
   of 45, because the new CI job contributes a checkout of its own. Counts cross-check three
   ways: `grep` finds 44 `false` and 1 `true`, and the checker independently reports 45 checkouts
   with 1 persisting.
2. **The exception made explicit** — `persist-credentials: true`, a `name:`, and a comment naming
   the consuming step, the token's scope and its location. The plan's rejection of the tokenized
   push URL is recorded in `docs/development.md` rather than left as an undocumented decision.
3. **CI guard** — `usesSteps()` added beside `runSteps()`, checker written, job placed after
   `workflow-arg-binding` as planned, file-header comment block extended in the repository's
   established "what this catches" style.
4. **Documentation** — all eight planned surfaces updated.
5. **CHANGELOG** — `### Changed` and `### Added` entries under `[Unreleased]`, each referencing
   `(#133)`, including the explicit non-breaking justification.

### Deviations

- **Scope addition: `README.md` trust-model paragraph.** Not in the plan. Justified:
  `docs/development.md` states that "A condensed summary lives in
  README.md#trust-model-and-pinning", so adding a trust-model rule to one and not the other would
  have left the pair the reference itself points at out of step. Reasonable.
- **Scope addition: a fourth assertion branch in the checker.** The plan listed three assertions;
  the implementation also rejects a non-boolean value, so a quoted `"false"` — truthy to the
  action, and therefore credential-persisting while reading as if it were not — cannot pass.
  Clearly beneficial, and the kind of gap this repository's checks normally close.
- **Scope addition: four `cspell.json` words.** A mechanical consequence of the prose.

No approach deviations, no scope omissions, no ordering violations.

### Fidelity

The implementation follows the plan's intent, not merely its letter. Two places where that shows:

- The plan asked for a comment naming the consuming step. The implementation also gives the step
  a `name:`, which is what actually makes the exemption key survive a reordering; an unnamed step
  keys on its index. The checker's own header comment and `workflow-steps.mjs` both record why.
- The plan's verification step 2 asked for planted defects. All four failure classes were planted
  and confirmed red, including the `assertExactlyOne` path, which required deleting the whole tap
  step rather than just renaming it. The rename case is caught by a different assertion, so
  proving `assertExactlyOne` is live took a separate plant.

### Open verification steps

- **CI has not run.** The branch is not pushed. `run-ci.yml` self-hosts the reusable workflows, so
  a push is what actually exercises the edited checkouts end to end, along with the new job.
- **The inspection reasoning is not yet recorded anywhere durable.** The release, publish and
  pages workflows are tag- and deploy-triggered and cannot run on this branch. The reasoning that
  no step in them runs `git` against a remote exists in the plan's verification section but was
  meant for the PR description, and there is no PR yet.

## Code Quality Assessment

**Verdict: ready to merge once CI is green.** No correctness defects. The change is uniform,
independently verifiable, and better instrumented than the issue asked for. The findings below
are polish on the new checker, not blockers.

### Strengths

- **The counts cross-check.** `grep`, the checker, and the plan's stated totals agree, and the
  checker derives its number from the same YAML parse the rest of the test harness uses rather
  than from a regex over text.
- **The refactor removes duplication instead of adding it.** `workflow-steps.mjs` had the same
  walk written three times with the `run:` filter inlined in each; it is now one walk with two
  thin filters, and the existing `workflow-arg-binding` scenarios all still pass.
- **The exemption is keyed on something stable.** Naming the tap step is the difference between
  an exemption that survives a step being inserted above it and one that silently detaches.
- **Diagnostics are lists, not booleans.** A failure names every offending step, so a bulk
  regression reports as a bulk regression.
- **The documentation answers the questions a reader will actually have**, including the two
  things that look like they need the credential and do not, with the upstream source cited for
  the `peter-evans/create-pull-request` claim rather than asserted from memory.
- **The security claim about the tap is precise**: the persisted credential is a different,
  narrower token, in a different `.git/config`, than the one the change is removing elsewhere.

### Issues to address

1. **`PERSISTS_CREDENTIALS` values are never read** (`tests/check-checkout-credentials.mjs:22`).
   The map's values are rationale strings, but only `.has()`, `.keys()` and `.size` are used. A
   reader will reasonably assume the rationale surfaces in a diagnostic; it does not. Either
   include it in the "listed as persisting its credential, but sets false" message, or make this
   a `Set` and move the rationale into the comment above it.
2. **The success line's count is misleading** (`tests/check-checkout-credentials.mjs:51`).
   `keys.length` is every `uses:` step, so the line reads "127 steps scanned, 1 persisting", which
   invites reading 127 as the number of checkouts. Counting checkouts would both be accurate and
   give a number a reviewer can cross-check against `grep`.
3. **Three distinct failures share one heading** (`tests/check-checkout-credentials.mjs:48`). An
   unlisted `true`, a non-boolean value, and a listed entry whose step was renamed all report
   under "whose persist-credentials value is not allowed". The rename case is the one most likely
   to occur, and that heading points at the wrong problem. Running `assertExactlyOne` before the
   `unexpected` assertion, or separating the rename case, would name the real cause.

### Suggestions

- **`actions/AGENTS.md` says nothing about the rule**, although the checker covers
  `actions/**/action.yml`. Someone adding a composite action reads that file, not
  `.github/workflows/AGENTS.md`. No action checks out today, so this is latent rather than a gap
  in coverage, but one line would close the loop.
- **The `actions/checkout` SHA in `actions/create-pull-request/README.md` is a new drift
  surface** that Dependabot does not update, since it lives in a fenced block. It matches existing
  precedent, `actions/setup-node@820762…` already appears the same way in
  `install-cspell-dictionaries/README.md` and `run-cspell/README.md`, so this is consistent rather
  than novel. If the drift is worth tracking, `scripts/check-tool-versions.py` already carries
  doc-surface notes for other tools and could grow one.
- **The plan is still in `docs/plans/todo/`.** Every recent change in this repository moved its
  plan to `docs/plans/done/` in a separate `docs:` commit on the same branch (`15aa4d7`,
  `10c5e92`, `3fe839e`, and seven more). Worth doing before the PR is ready.
- **There is no `make` target for the new checker**, so it can only be run by hand locally. That
  is the current state of every check in `tests/`, and issue #138 already tracks adding test
  targets; the new checker is one more caller for it.

### Completeness

No TODO, FIXME, HACK or XXX comments, no stubs, no commented-out code, no placeholder values. The
new test file is complete and exercised. Documentation was updated alongside the behavior change
rather than deferred. The zizmor ignore comment the exception will need is correctly left to
issue #134, and the plan records that hand-off explicitly rather than leaving it implied.
