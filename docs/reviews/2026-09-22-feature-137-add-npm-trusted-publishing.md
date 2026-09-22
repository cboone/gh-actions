# Branch Review: feature/137-add-npm-trusted-publishing

Base: main (merge base: bbe1518)
Commits: 4
Files changed: 19 (6 added, 13 modified, 0 deleted, 0 renamed)
Reviewed through: f556b9f

## Summary

The branch adds `publish-to-npm-with-oidc.yml`, which publishes to npmjs.com
through npm's trusted publishing with no stored credential and with provenance
attestations, and hardens how all three npm workflows install dependencies: a
lockfile is now required, lifecycle scripts are off, and a publish no longer
restores a dependency cache. The two publish workflows are deliberately separate
files rather than one workflow with an auth-mode input, a shape forced by a
measured GitHub behavior that upstream does not document. Coverage comes from a
new fixture that runs the production steps against stubs, since neither publish
workflow can be self-hosted without publishing something.

The work is complete and the tree is clean. Two things stand between it and a
merge: one documentation claim about npm's optional Environment field is wrong,
and the issue's primary done-when, an actual publish showing provenance, has not
been exercised.

## Changes by Area

### Publishing workflows

`publish-to-npm-with-oidc.yml` is new: `contents: read` and `id-token: write`,
no secrets, a registry gate that refuses anything but npmjs.com, a version gate
for npm 11.5.1 and Node 22.14.0, and a provenance opt-out that only ever writes
`NPM_CONFIG_PROVENANCE=false`. `publish-to-npm.yml` keeps its token path and
gains the hardened install plus `package-manager-cache: false`.

Files: `.github/workflows/publish-to-npm-with-oidc.yml`,
`.github/workflows/publish-to-npm.yml`

### Dependency installation

All three npm workflows now choose between `npm ci` and `npm install` inside the
step, from `env:` bindings, instead of through a `run:` ternary. Installs pass
`--include=dev --no-audit --no-fund --ignore-scripts`, a missing lockfile is an
error, and `allow-npm-install` and `run-install-scripts` are the escape hatches.

Files: `.github/workflows/deploy-to-pages.yml`,
`.github/workflows/publish-to-npm.yml`,
`.github/workflows/publish-to-npm-with-oidc.yml`

### Tests

`check-npm-publish.mjs` reads the production steps out of the YAML and runs them
under the runner's bash against stubs that report versions or record argument
vectors, across six scenarios. The `workflow-arg-binding` allowlist drops from
eight entries to six now that the ternaries are gone.

Files: `tests/fixtures/check-npm-publish.mjs`, `tests/scrut/npm-publish.md`,
`.github/workflows/run-ci.yml`, `tests/fixtures/check-workflow-arg-binding.mjs`

### Documentation and agent config

A per-component page for the new workflow, a v5 migration guide, the measured
permission behavior recorded in the development reference, and the
"two ternaries" sentence corrected in the three places it is repeated.

Files: `docs/workflows/publish-to-npm-with-oidc.md`,
`docs/workflows/publish-to-npm.md`, `docs/workflows/deploy-to-pages.md`,
`docs/migrations/v5.md`, `docs/development.md`, `README.md`, `CHANGELOG.md`,
`AGENTS.md`, `.github/workflows/AGENTS.md`, `.github/copilot-instructions.md`,
`cspell.json`

## File Inventory

### New files (6)

- `.github/workflows/publish-to-npm-with-oidc.yml`
- `docs/migrations/v5.md`
- `docs/plans/todo/2026-09-21-add-npm-trusted-publishing.md`
- `docs/workflows/publish-to-npm-with-oidc.md`
- `tests/fixtures/check-npm-publish.mjs`
- `tests/scrut/npm-publish.md`

### Modified files (13)

- `.github/copilot-instructions.md`
- `.github/workflows/AGENTS.md`
- `.github/workflows/deploy-to-pages.yml`
- `.github/workflows/publish-to-npm.yml`
- `.github/workflows/run-ci.yml`
- `AGENTS.md`
- `CHANGELOG.md`
- `README.md`
- `cspell.json`
- `docs/development.md`
- `docs/workflows/deploy-to-pages.md`
- `docs/workflows/publish-to-npm.md`
- `tests/fixtures/check-workflow-arg-binding.mjs`

## Notable Changes

**Breaking, released as v5.0.0.** Two defaults change for existing callers: a
lockfile is required, and dependency lifecycle scripts no longer run. Both have
opt-outs, and `docs/migrations/v5.md` covers them.

**Downstream impact is one repository.** Of the three known callers,
`cboone/cboone-alpine-plugins` publishes with no lockfile and will fail until it
commits one or sets `allow-npm-install: true`; the migration guide uses it as
the worked example. `cboone/snappy-sh-site` and `cboone/bopca-sh-site` both call
`deploy-to-pages.yml` without `setup-node`, so the install step never runs for
them and the hardening cannot touch them. All three are pinned at v3.1.0, so
nothing breaks until they upgrade.

**Security posture.** The new path removes a long-lived credential entirely and
adds provenance. `package-manager-cache: false` closes the cache-poisoning route
into a published artifact that a workflow security audit would flag.
`--ignore-scripts` narrows what runs during a publish. No new dependency, no new
action pin, and the one new `uses:` reference is the already-pinned
`actions/setup-node` SHA.

**A platform behavior is now written down.** `docs/development.md` records that
a nested job's permissions are validated before its `if:` is evaluated, with the
date and the experiment that established it.

## Plan Compliance

Plan: `docs/plans/todo/2026-09-21-add-npm-trusted-publishing.md`

**Verdict: good compliance.** Every implementation step in the plan landed, in
the shape the plan describes, and the two deviations both improve on it. The one
gap is the manual verification the plan itself lists, which cannot be done from
here.

Overall progress: 27 of 28 items done, 96%.

### Step 1, publish-to-npm.yml (3/3 done)

Both inputs added; `package-manager-cache: false` set and `cache:` and
`cache-dependency-path:` removed; the ternary replaced. The `shape` scenario
asserts the cache settings, so they cannot regress silently.

### Step 2, publish-to-npm-with-oidc.yml (6/6 done)

Registry gate before the checkout, `setup-node` with caching off, the version gate after it,
shared install, conditional provenance step, and a publish step with no
environment binding at all. The plan's reasoning for the conditional step, that
npm reads an empty env config as true, survives into a comment in the file and
into the fixture's own comment.

### Step 3, shared install step (2/2 done)

Byte-identical in all three workflows, verified by the `parity` scenario rather
than by inspection. `deploy-to-pages.yml` keeps its cache, as planned.

### Step 4, tests (7/7 done, plus one addition)

All five planned scenarios exist, with a sixth, `detect`, covering the lockfile
probe. The scrut spec and the `npm-publish` CI job match the plan, including the
macOS runner for bash 3.2.

### Step 5, documentation (8/8 done)

Every file the plan names was updated, including the three copies of the
argument-binding sentence.

### Verification (1/2 done)

Local checks all ran green: actionlint, yamllint, Prettier, markdownlint, cspell,
both scrut suites. The manual verification, publishing a test package and seeing
provenance on its npm page, has **not started**. It needs a package on npmjs.com
and a merged tag, so it cannot be done from the branch.

### Deviations

1. **`NODE_FOR_NPM: 24.5.0` added to the version gate**, which the plan did not
   anticipate. Justified, and checked against `nodejs.org/dist/index.json`: no
   Node 22 or 23 release bundles npm 11.5.1 or later, 22.x topping out at
   10.9.8, so npm's documented Node floor cannot be met by raising within those
   lines. Without this the diagnostic would have sent a caller on Node 22 to a
   version that cannot help. Reasonable, and an improvement on the plan.
1. **Diagnostic wording differs from the plan's code block.** yamllint's
   120-column limit forced shorter messages, and the registry failure became two
   `::error::` lines instead of one long one. Cosmetic, and the fixture asserts
   the substrings that matter.
1. **A sixth test scenario.** Scope addition, small, and it covers a step that
   would otherwise have had no coverage at all.

### Fidelity concerns

None. The plan's stated intent, that neither caller grants a permission its mode
cannot use and that the duplication stays honest, is what the code and the
`shape` and `parity` scenarios actually enforce.

## Code Quality Assessment

### Overall quality

**Close to merge, with one documentation correction first.** The workflows are
careful, the reasoning is recorded where the next reader will need it, and the
tests exercise the production steps rather than copies of them. Every new check
was confirmed to go red against a planted defect, so the coverage is real rather
than asserted. What is missing is an end-to-end publish and one wrong claim in
the new doc.

### Verified during this review

Two claims the branch rests on were checked rather than trusted:

1. **The OIDC path installs without a token, despite setup-node's .npmrc.** At
   the pinned SHA, setup-node writes `_authToken=${NODE_AUTH_TOKEN}` into the
   .npmrc and exports `NODE_AUTH_TOKEN` **only when the caller supplied one**,
   so on the OIDC path the placeholder stays unresolved. Probed locally with npm
   11.6.2 against that exact config with the variable unset: both `npm install`
   and `npm ci` succeed against registry.npmjs.org. This was the largest latent
   risk in the design and it is closed.
1. **The bundled-npm facts are right.** `nodejs.org/dist/index.json` gives npm
   11.19.0 for the default Node 24.21.0, 10.9.2 for Node 22.14.0, and 24.5.0 as
   the first release clearing npm 11.5.1. The workflow's three constants and the
   documentation agree with it.

### Strengths

- **The central design question was settled by measurement.** The two-workflow
  split is not a preference; it follows from a behavior that four runs
  established and that is now documented with its date.
- **Duplication that policy forces is made safe.** `parity` holds three copies
  byte-identical, so the thing a reviewer would normally flag cannot rot.
- **The tests read production, not a transcription of it.** Steps, input
  defaults and the version constants all come out of the YAML, so a scenario
  cannot drift from what callers get.
- **The non-obvious npm fact is documented prominently**: the trusted publisher
  names the caller's own repository and workflow filename. Getting this wrong is
  the likeliest reason a first attempt fails, and the opposite guess is the
  natural one.
- **Failure messages name the fix**, not just the problem: the input to set, the
  other workflow to call, the Node version to use.

### Issues to address

1. **The Environment row in `docs/workflows/publish-to-npm-with-oidc.md` is
   wrong** (should fix before merge). It says to set npm's optional Environment
   field "only if your calling job names one", but a calling job cannot name
   one: GitHub's supported-keyword list for a job that calls a reusable workflow
   has no `environment`, and the OIDC claim would come from the nested publish
   job here, which declares none. A maintainer who follows that row will
   configure an environment-scoped publisher on npmjs.com and get a rejection
   with nothing in the workflow to explain it. Either say the field must be left
   empty and why, or add an `environment` input so the publish job can run in a
   named environment, which would also let callers attach protection rules to a
   publish. The second is the better feature; the doc correction is required
   either way.
1. **The issue's primary done-when is unexercised** (not a code defect). #137
   asks for a test package that publishes with no token and shows provenance.
   Nothing in CI can cover it, and the fixture's `shape` scenario is a structural
   stand-in, not a substitute. This should be run against a real npmjs.com
   package before the v5 tag, and the result noted on the issue.

### Suggestions

- **`run-ci.yml`'s own installs are now inconsistent.** Five jobs run plain
  `npm ci`, two run `npm ci --ignore-scripts --include=dev --no-audit --no-fund`,
  and this branch adds a sixth plain one to match its neighbor. Consistent with
  the file, but at odds with what the branch argues everywhere else. Worth a
  follow-up issue rather than a change here.
- **The version gate's prerelease leniency is deliberate and tested**, but it
  means an npm `11.5.1-rc.0`, which may predate the OIDC support, passes the
  gate. The comment and the scenario both say this is intended; leaving it is
  defensible, and tightening it would cost a line.
- **The plan sits in `docs/plans/todo/`** though the work is done. Every other
  completed plan in the repository lives in `docs/plans/done/`; moving it at
  merge would match.
- **A `dry-run` input** with a fixture package would let `run-ci.yml` self-host
  both publish workflows, turning the `shape` assertions into a real end-to-end
  test and covering the gap in the second issue above. The plan already lists
  this as a follow-up.
