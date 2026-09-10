# Fix `lint-text.yml`: `github.job_workflow_sha` does not exist (#83)

## Context

`lint-text.yml` is unusable on its default inputs. Every consumer that calls it
hits this before a single linter runs:

```text
##[error]github.job_workflow_sha is empty; this workflow must be called via workflow_call.
```

Reported in [#83](https://github.com/cboone/gh-actions/issues/83) and reproduced
by `cboone/audio-tools`
([failing run](https://github.com/cboone/audio-tools/actions/runs/33202871894/job/98956457628)).

### Root cause

`github.job_workflow_sha` is not a real context property and never has been. The
January 2023 OIDC changelog announced it as something that would reach the
`github` context, but only the OIDC token claim ever shipped.
[actions/runner#2417](https://github.com/actions/runner/issues/2417) tracked the
gap from February 2023; GitHub eventually deleted the claim from the contexts
documentation rather than implementing it.

GitHub closed the gap on the **`job`** context instead, announced in the
[Actions changelog on 2026-09-03](https://github.blog/changelog/2026-09-03-github-actions-early-september-2026-updates/):
`job.workflow_ref`, `job.workflow_sha`, `job.workflow_repository`, and
`job.workflow_file_path`. For a job defined directly in a workflow these mirror
the `github.workflow_*` values; for a job that comes from a reusable workflow
they describe the reusable workflow file, which is exactly what this repo needs.
They are documented as unavailable on GitHub Enterprise Server.

The repository already held the evidence. `.github/actionlint.yaml` exists for
the sole purpose of suppressing
`property "job_workflow_sha" is not defined in object type`. actionlint was
right; the suppression hid a correct diagnostic behind a comment asserting the
opposite.

### Why nothing caught it

Nothing in CI exercises `lint-text.yml`. `run-ci.yml` self-hosts only
`lint-github-actions.yml`, which is self-contained and never reaches back into
this repo. The four `raw.githubusercontent.com` fetches in `lint-text.yml` are
the only place the repo depends on this value, and they shipped in v3.0.0
without a consumer exercising them.

### Blast radius

A code search across `cboone` repos shows four repos already routing around
this, which sets up the post-release follow-up list:

- `cboone/audio-tools`: `text-lint.yml` first job inlined; note in `AGENTS.md`.
- `cboone/springer`: same inlining; notes in `AGENTS.md`,
  `.github/actions.instructions.md`, and a plan document.
- `cboone/zhang-yeung-inequality`: deliberately held on the pre-v3
  `text-lint.yml` path and pin, with an instruction not to migrate while #83 is
  open. Tracked in that repo's #15.
- `cboone/agent-harness-plugins`: a plan document references #83.

### Intended outcome

`lint-text.yml` works on default inputs; this repo's own CI catches the same
class of failure in future; the corrected mechanism is written down where the
next reader will find it; and the four repos above can drop their workarounds.

## Changes

### 1. `.github/workflows/lint-text.yml`: read from the `job` context

Four steps bind the broken value in a step-level `env:` block, guard on it, and
interpolate it into a URL whose repo slug is hardcoded:

- `Apply markdownlint preset` fetches `presets/<preset>/.markdownlint-cli2.jsonc`
- `Apply cspell preset` fetches `presets/<preset>/cspell.jsonc`
- `Install lint tools (sha512-verified via gh-actions lockfile)` fetches
  `package.json` and `package-lock.json`
- `Install yamllint with hash-pinned requirements` fetches
  `requirements/yamllint.txt`

Give each the same preamble:

```yaml
env:
  REQ_REPO: ${{ job.workflow_repository }}
  REQ_SHA: ${{ job.workflow_sha }}
run: |
  if [ -z "${REQ_REPO}" ] || [ -z "${REQ_SHA}" ]; then
    msg="job.workflow_sha is unavailable, so this workflow cannot fetch its"
    msg="${msg} own pinned manifests. It is not populated on GitHub"
    msg="${msg} Enterprise Server. Set use-consumer-versions: true to install"
    msg="${msg} from your own committed package-lock.json instead."
    echo "::error::${msg}" >&2
    exit 1
  fi
  base="https://raw.githubusercontent.com/${REQ_REPO}/${REQ_SHA}"
  echo "Fetching from ${base}"
```

Four things change beyond the property name.

**The repo slug stops being hardcoded.** `cboone/gh-actions` becomes
`${{ job.workflow_repository }}`, which resolves to whichever repository the
caller actually pinned. That fixes a second latent bug: a fork calling its own
copy currently fetches upstream's manifests at a SHA that does not exist
upstream, so every fetch 404s. It introduces one regression to document rather
than solve: a **private** fork cannot serve manifests over
`raw.githubusercontent.com`, where the hardcoded slug at least reached a working
public upstream. `actions/checkout` would not rescue that case either, since its
README requires a PAT for a private secondary repository.

**The preset guards become lazy.** Today the emptiness check runs before the
local-config detection loop, so a consumer that ships `.markdownlint-cli2.jsonc`
_and_ sets `preset: lean-math` fails on a value it never needed. Move the guard
and the `base=` assignment inside the `if [ "${has_local_md}" -eq 0 ]` branch
(and its cspell equivalent). This is what makes a complete GitHub Enterprise
Server configuration possible: `use-consumer-versions: true` plus `preset: ""`
plus `run-yamllint: false` then touches none of the four fetches and stays fully
integrity-checked.

**Each guard names its own escape hatch.** The npm step points at
`use-consumer-versions: true`; the yamllint step at `run-yamllint: false`; the
preset steps at shipping a local config. That turns "the workflow is unusable"
into "usable with a documented configuration," which is what the issue wanted.

**The fetches get an echo and a retry.** `echo "Fetching from ${base}"` makes
the CI log proof that the value resolved, so the next failure of this class is
self-diagnosing. `curl -sSfL --retry 3 --retry-delay 5 --retry-all-errors`
covers CDN cache lag on a merge commit created seconds before the job starts;
`--retry-all-errors` is required because `-f` turns a 404 into an error plain
`--retry` will not retry.

Delete the comment block on the npm step asserting that "job_workflow_sha is
always set when a job comes from a reusable workflow" and state what is true.

Keep the four preamble copies. Hoisting `REQ_REPO`/`REQ_SHA` into the
workflow-level or job-level `env:` block is **not legal**: the `job` context is
available in `jobs.<job_id>.steps.env`, `.run`, and `.if`, but not in
`jobs.<job_id>.env`, `jobs.<job_id>.if`, or `jobs.<job_id>.with`. The duplication
is forced by the platform, not chosen.

### 2. Keep `curl` and `raw.githubusercontent.com`

Issue #83 suggests `actions/checkout` with `repository: ${{ job.workflow_repository }}`
and `ref: ${{ job.workflow_sha }}` instead. Reject it: `actions/checkout` throws
`Repository path ... is not under ...` for any `path:` outside
`$GITHUB_WORKSPACE`, so a checkout of this repo lands inside the consumer's tree
and is then linted by `prettier --check .`, `cspell .`, and
`markdownlint-cli2 "**/*.md"`. That cannot be fixed from the reusable workflow,
because the ignore files that would suppress it belong to the consumer. Fetching
into `RUNNER_TEMP` keeps the workspace clean and matches what the composite
actions already do through `github.action_path/../..`
(`actions/run-cspell/action.yml:36-52`, `actions/run-reuse/action.yml:80-103`).

Also reject two alternatives so they are not raised again in review:

- **A tag fallback** when the value is empty (issue suggestion 2) pairs workflow
  logic from one commit with a lockfile from another, silently coarsens a pin
  the caller deliberately made exact, and needs bumping every release. The lazy
  guards above deliver the same "not unusable" outcome without degrading a pin.
- **A single tarball fetch** from `codeload.github.com/<repo>/tar.gz/<sha>` would
  collapse four requests into one and bring `presets/` along, but it downloads
  more, gains no integrity, and obscures exactly which manifests the trust model
  rests on.

### 3. `.github/actionlint.yaml`: update the suppression

actionlint 1.7.12 does not know the `job.workflow_*` properties either, verified
locally against a stdin probe. Its source has no reference to
`workflow_repository`, so the suppression is not going away in the next release.
Replace the single `job_workflow_sha` pattern with one anchored pattern that
covers all four properties and cannot silence a genuine error on some other
object type:

```yaml
- 'property "workflow_(sha|repository|ref|file_path)" is not defined in object type \{check_run_id:'
```

`check_run_id` is distinctive to the `job` object type, and YAML single quotes
leave `\{` intact for Go's regexp. Rewrite the file's comment: actionlint
predates the properties GitHub shipped on 2026-09-03, rather than the current
text's claim that GitHub documents a `github` context property actionlint fails
to recognize. The suppression should be deleted, not carried forward, once
upstream knows the properties.

### 4. `scripts/check-tool-versions.py`: note the actionlint dependency

actionlint is already tracked (around line 102), so the weekly issue surfaces a
new release, but it would report "1.7.13 available" without saying why anyone
cares. Add a `note=` in the style already used for scrut, shfmt, and yamllint:
on bump, re-check whether the `job.workflow_*` properties are recognized and
delete `.github/actionlint.yaml` if so.

### 5. `.github/workflows/run-ci.yml`: regression coverage

Add a second job so this repo exercises the workflow it ships:

```yaml
text:
  uses: ./.github/workflows/lint-text.yml
  with:
    run-cspell: true
    run-yamllint: true
```

Name it `text`, matching the usage examples in `docs/workflows/lint-text.md`;
naming it `text-lint` would produce the check name
`Run CI / text-lint / Text lint`, since the reusable workflow's internal job is
already `text-lint`.

A `./` reference still produces a reusable-workflow job, so `job.workflow_sha`
should be populated and the fetch path genuinely exercised. That last point is
the one real unknown in this plan: the properties are a week old and there is no
field evidence for the local-reference case. The `echo "Fetching from ${base}"`
line makes the first CI run the experiment. If the value comes back empty for
`./` refs, that surfaces on the PR rather than after release, and the fallback
is a lesser test (call with `use-consumer-versions: true`, which proves nothing
about #83).

The merge-commit half is already verified: `raw.githubusercontent.com` serves a
commit reachable only through `refs/pull/N/merge`, tested against a live PR. It
is also the semantically right SHA, since `pull_request` reads the workflow file
from the merge commit.

Delete the `paths-ignore` blocks entirely rather than trimming them. Removing
just `"**/*.md"` and `"docs/**"` would still leave `LICENSE`, `.editorconfig`,
and `.claude/**` filtered while `cspell .` scans `LICENSE` and
`prettier --check .` checks `.claude/settings.json`, so a PR touching only those
files skips CI and the violation lands on an unrelated PR later. Actions minutes
are free on this public repo and `concurrency` with `cancel-in-progress` is
already set, so the filter was not buying anything.

One gap stays open, worth stating rather than chasing: this repo ships
`.markdownlint-cli2.jsonc` and `cspell.json`, so both preset steps take their
local-config branch and the preset `curl` itself is never exercised. Covering it
would need a consumer without local configs. Since all four steps build `base`
from the same two variables, the npm step proves the expression, and the
residual risk is a typo in the path segment after `${base}`.

### 6. Documentation

- `AGENTS.md:103`: `github.job_workflow_sha` becomes `job.workflow_sha`.
- `README.md:146`: "against **this repo's** `package-lock.json`" becomes the
  workflow repository's, now that the slug is dynamic.
- `.github/copilot-instructions.md:50`: the brace-glob entry cites
  `job_workflow_sha` errors as its empirical evidence; point it at
  `workflow_sha`. Add two anti-pattern entries: that `github.job_workflow_sha`
  does not exist and `job.workflow_sha` / `job.workflow_repository` are the
  correct properties; and that the repeated `REQ_REPO`/`REQ_SHA` step `env:`
  blocks cannot be hoisted to job or workflow level, since Copilot reviews this
  repo on every push and that is exactly the deduplication it will propose.
- `docs/workflows/lint-text.md`: a short subsection on how the workflow reaches
  back into this repo, naming the two properties, and stating the complete
  GitHub Enterprise Server configuration (`use-consumer-versions: true`,
  `preset: ""`, `run-yamllint: false`) plus the private-fork limitation.
- `CHANGELOG.md`: a `### Fixed` entry under the existing `## [Unreleased]`
  heading, referencing #83 and naming v3.0.0 and v3.1.0 as affected.

## Verification

Local, before pushing:

```bash
npm ci   # node_modules is absent in this checkout
./node_modules/.bin/markdownlint-cli2 "**/*.md"
./node_modules/.bin/prettier --check .
./node_modules/.bin/cspell .
make lint        # actionlint, with the updated suppression
make lint-yaml
```

Call the binaries directly rather than through `make lint-md`, `make
format-check`, and `make spell`: those targets use `npx`, which without a
populated `node_modules` resolves the latest published version instead of the
pinned one, and the pinned versions are what CI will run.

`make lint` must pass without new suppressions. If actionlint reports anything
beyond the four `job.workflow_*` properties, the expression is wrong.

Because `run-ci.yml` will run these linters on this repo for the first time,
expect version drift to surface violations that the locally installed tools do
not show: CI pins cspell 10.3.0 and markdownlint-cli2 0.23.2 (markdownlint
0.41.1). The plan document itself is linted, since `.prettierignore` and the
markdownlint `ignores` list cover `docs/plans/done/` but not `docs/plans/todo/`.
New words go alphabetically into the `words` array in `cspell.json`.

In CI, on the PR:

1. The `text` job must go green. That is the real test: it proves
   `job.workflow_sha` is populated for a `./`-referenced reusable-workflow job
   and that `raw.githubusercontent.com/<repo>/<sha>/...` resolves for a
   `pull_request` merge commit.
1. Confirm in the log that `Fetching from https://raw.githubusercontent.com/cboone/gh-actions/<sha>`
   appears for both the npm step and the yamllint step, and that neither was
   skipped.

After merge:

1. Cut v3.1.1 with the `/release` skill, push the commit and tag, and let
   `create-gh-release-on-tag.yml` publish the release. The release also bumps the
   `@v3.1.0` pins in `README.md` and the `docs/workflows/*.md` usage examples.
1. Point `cboone/audio-tools` and `cboone/springer` back at the reusable
   workflow, remove their inlined steps, and delete the `AGENTS.md` and
   `.github/actions.instructions.md` notes describing the workaround.
1. Migrate `cboone/zhang-yeung-inequality` from the pre-v3 `text-lint.yml` pin to
   `lint-text.yml@v3.1.1`, closing its #15.
1. Close #83 with the root cause, since the issue's own diagnosis stops at "the
   context value arrives empty."

## Commits

Conventional Commits, each self-contained and green on its own. The ordering
matters: the enforcing CI job lands last, so it is never knowingly red.

1. `docs: plan the lint-text job-context fix (#83)` for this document, formatted
   with the pinned Prettier, plus any `cspell.json` words it needs.
1. `fix(lint-text): resolve the workflow repo and SHA from the job context (#83)`
   for the four steps in `lint-text.yml` plus `.github/actionlint.yaml` plus the
   `CHANGELOG.md` entry. The workflow and the actionlint config are inseparable,
   because `make lint` fails if either lands alone; commit `ac0f6de` set the
   precedent of carrying the CHANGELOG entry alongside.
1. `docs: correct github.job_workflow_sha references to job.workflow_sha (#83)`
   for `AGENTS.md`, `README.md`, `.github/copilot-instructions.md`,
   `docs/workflows/lint-text.md`, and the `scripts/check-tool-versions.py` note.
1. `ci(run-ci): self-host lint-text.yml as regression coverage for #83` for the
   new job and the `paths-ignore` removal.
1. `fix(lint): resolve violations surfaced by the pinned tool versions`, only if
   the first run of the new job reveals cspell 10.3.0 or markdownlint 0.41.1
   findings that the locally installed versions did not. Kept separate so the
   #83 fix stays reviewable.
