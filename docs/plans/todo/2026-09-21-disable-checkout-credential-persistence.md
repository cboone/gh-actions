# Disable checkout credential persistence (#133)

## Context

`actions/checkout` writes the job's token into `.git/config` and leaves it there for
the rest of the job, where every later step can read it. This is the vulnerability
class zizmor calls [`artipacked`](https://docs.zizmor.sh/audits/#artipacked): anything
that archives or uploads the workspace carries the token with it.

All 44 `actions/checkout` steps in this repository currently take that default. The
exposure matters most where the blast radius is largest: `release-go-binaries` hands
the workspace to GoReleaser, `release-rust-binaries` runs a cargo toolchain and
uploads artifacts, `publish-to-npm` runs `npm ci` with a publish token also in scope,
and `deploy-to-pages` runs a caller-supplied `build-command`. Because 26+ downstream
repositories call these reusable workflows, fixing it here fixes it everywhere.

The intended outcome: every checkout drops its credential, the single site that
genuinely pushes says so out loud, and a CI check keeps a new checkout from quietly
reintroducing the default.

### What the survey found

Exactly one step in the repository consumes a persisted Git credential: **"Commit and
push formula"** in `release-rust-binaries.yml`, which pushes to the Homebrew tap
checked out at line 327 under `path: homebrew-tap`. Nothing else does.

- The only other `git` invocation in any workflow is `git ls-files` in
  `lint-shell.yml`, which is local.
- `gh` authenticates through `GH_TOKEN` in the environment, so `create-gh-release`,
  `check-tool-versions.yml`'s issue filing and `release-rust-binaries`'s
  `gh release download` are all unaffected.
- GoReleaser reads local history (hence `fetch-depth: 0`) and talks to GitHub through
  `GITHUB_TOKEN` / `HOMEBREW_TAP_TOKEN` in the environment, not through `.git/config`.
- `actions/create-pull-request` does **not** need it, contrary to the issue's guess.
  Upstream `peter-evans/create-pull-request` v8.1.1 saves and unsets any persisted
  `extraheader`, configures its own from the `token` input, pushes, then restores
  (`src/git-config-helper.ts`: `savePersistedAuth`, `configureToken`,
  `restorePersistedAuth`, plus `hideCredentialFiles` for checkout v6 credential
  files). Callers should pair it with `persist-credentials: false`.

### Why this is not a breaking release

A consumer of a reusable workflow cannot inject steps into its jobs. The only
caller-supplied code that runs beside these checkouts is `build-command`,
`scrut-setup-cmd` and `scrut-build-cmd`. Every value in use across the consuming
repositories is a tool install or a compile: `go run ./build.go` (no `git` or
`exec.Command` in that file), `"true"`, `go build -o ./bin/quod ./cmd/quod`, and
several uv/zsh installs. No consumer depends on the persisted token, so this ships as
a minor release with CHANGELOG and per-workflow doc notes, not a major bump with a
migration guide.

## Changes

### 1. Set `persist-credentials: false` on 43 of the 44 checkouts

Add the key to every `actions/checkout` step across `.github/workflows/`. Thirty-eight
of them have no `with:` block today and gain one; six already have a block
(`release-go-binaries.yml:43`, `release-rust-binaries.yml:114`,
`release-zig-binaries.yml:56`, `scan-for-secrets.yml:84` and `:165`,
`release-rust-binaries.yml:327`) and gain one more key.

The pattern, for a step with no `with:` block:

```yaml
- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
  with:
    persist-credentials: false
```

Affected files, with their checkout counts: `run-ci.yml` (12), `run-rust-ci.yml` (6),
`run-go-ci.yml` (5), `run-zig-ci.yml` (5), `scan-for-secrets.yml` (2),
`release-rust-binaries.yml` (2, one of them the exception below), and one each in
`analyze-with-codeql.yml`, `check-tool-versions.yml`,
`create-gh-release-from-changelog.yml`, `deploy-to-pages.yml`,
`lint-github-actions.yml`, `lint-shell.yml`, `lint-text.yml`, `publish-to-npm.yml`,
`release-go-binaries.yml`, `release-zig-binaries.yml`, `run-lean-ci.yml`,
`run-scrut-tests.yml`.

### 2. Make the one exception explicit

`release-rust-binaries.yml:327`, the Homebrew tap checkout, keeps its credential
because "Commit and push formula" pushes with it. Set `persist-credentials: true`
rather than leaving it implicit, give the step a `name:` so the CI check below can key
on something stable, and add a comment naming the step that needs it and noting that
the persisted token is the caller's tap-scoped `HOMEBREW_TAP_TOKEN` in
`homebrew-tap/.git/config`, not the job's `GITHUB_TOKEN`.

The alternative, pushing to an explicit tokenized URL, is rejected: it puts a secret
on a command line, where `ps` and Git's own error output can surface it.

### 3. A CI check that makes a regression fail

`tests/fixtures/workflow-steps.mjs` already walks every step of every workflow and
composite action, but `runSteps()` yields only steps with a `run:` block. Add a
sibling `usesSteps()` generator that yields `uses:` steps under the same
`<file>::<job>::<step name>` key, so the walk covers `actions/` too and a future
composite-action checkout is caught as well.

Add `tests/check-checkout-credentials.mjs`, run directly like the existing
`tests/check-*.py` checkers, asserting:

1. Every `actions/checkout@` step sets `with.persist-credentials` explicitly. An
   absent key fails, which is the regression the issue is about.
2. The value is `false`, except for keys in a `PERSISTS_CREDENTIALS` set, which must
   be exactly `true`.
3. Each `PERSISTS_CREDENTIALS` entry names exactly one real step, reusing
   `assertExactlyOne` from `workflow-steps.mjs`, so an exemption cannot outlive its
   step or widen to a second step that took the same name.

Wire it up as a new `checkout-credentials` job in `run-ci.yml`, placed after
`workflow-arg-binding` since both enforce workflow policy. One runner, not a matrix:
the check reads YAML and executes nothing platform-dependent. It needs
`actions/setup-node`, `npm ci` for the pinned `yaml` package, and the checker. Add a
line to the file-header comment block describing what the job catches, matching the
convention the other jobs there follow.

### 4. Documentation

- **`docs/development.md`**: a new `### Checkout Credentials` subsection at the end of
  the Pinning Policy and Trust Model section, before `### Version Pinning`. State the
  rule, name the single exception and why, record that `gh` and
  `peter-evans/create-pull-request` do not need the credential, and point at
  `tests/check-checkout-credentials.mjs` as the enforcement.
- **`docs/development.md` → "Adding a New Workflow"**: a checklist step requiring
  `persist-credentials: false` on every new checkout.
- **`REVIEW.md` → "Always check"**: a bullet beside the SHA-pinning one. This section
  is outside the `set-up-review-config` managed block, so it survives a regeneration.
- **`.github/workflows/AGENTS.md`**: a bullet stating the rule and the exception.
- **`AGENTS.md`** (root, symlinked as `CLAUDE.md`): one sentence in the Pinning Policy
  and Trust Model block, since this is mandatory policy.
- **`.github/copilot-instructions.md`** → "Workflow specifics": a note explaining the
  intentional `persist-credentials: true`, so review does not flag it as an oversight.
- **`actions/create-pull-request/README.md`**: a note that the action authenticates
  from its own `token` input and callers should check out with
  `persist-credentials: false`.
- **`docs/workflows/`**: a caller-visible note in `deploy-to-pages.md`, `run-go-ci.md`,
  `run-zig-ci.md` and `run-scrut-tests.md` saying that a `build-command`,
  `scrut-setup-cmd` or `scrut-build-cmd` no longer inherits a Git credential and must
  pass a token explicitly if it needs one. In `release-rust-binaries.md`, note that
  the tap checkout is the one that keeps its credential.

### 5. CHANGELOG

A `### Changed` entry under `## [Unreleased]`, referencing `(#133)`, stating the rule,
naming the single exception, and recording that no consumer's command input relied on
the persisted credential so the change is not breaking.

## Verification

1. `node tests/check-checkout-credentials.mjs` passes on the finished tree.
2. Plant the defect the check claims to catch, confirming each fails before reverting:
   remove `persist-credentials` from one checkout (expect the "must set" failure);
   flip one to `true` (expect the "only the listed site may persist" failure); remove
   the tap checkout's `name:` (expect the stale-exemption failure from
   `assertExactlyOne`).
3. `grep -c "persist-credentials" .github/workflows/*.yml` totals 44, and
   `grep -rn "persist-credentials: true"` returns exactly the tap checkout.
4. `make format` then `make format-check`, `make lint`, `make lint-md`, `make spell`,
   `make lint-yaml`. `make lint` installs actionlint through a bare `mktemp -d`, so run
   it outside the sandbox.
5. Push the branch and confirm `run-ci.yml` is green, including the new
   `checkout-credentials` job and the self-hosted calls to `lint-text.yml`,
   `run-scrut-tests.yml` and the rest, which exercise the edited checkouts for real.
6. The release, publish and pages workflows are tag- and deploy-triggered, so CI
   cannot exercise them on this branch. Confirm by inspection that no step in
   `release-go-binaries.yml`, `release-zig-binaries.yml`, `publish-to-npm.yml`,
   `deploy-to-pages.yml` or `create-gh-release-from-changelog.yml` runs `git` against
   a remote, and record that reasoning in the PR description.

## Out of scope

- **zizmor** (#134). This change adds a repository-local guard; the `artipacked` audit
  arrives with that issue. The explicit `persist-credentials: true` on the tap checkout
  will need a `# zizmor: ignore[artipacked]` comment then, which #134 should add.
- Changing how the Homebrew tap push authenticates.
- Updating downstream repositories' pinned `@<sha>` references to this release.
