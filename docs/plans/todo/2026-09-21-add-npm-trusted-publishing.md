# Support npm trusted publishing with provenance in publish-to-npm

Addresses [#137](https://github.com/cboone/gh-actions/issues/137).

## Context

`publish-to-npm.yml` authenticates with a long-lived `NODE_AUTH_TOKEN` that the
caller stores as a secret. npm's trusted publishing, generally available since
July 2025, removes the credential: the job presents a GitHub OIDC token, npm
validates it against a publisher configured on the package, and nothing
long-lived is stored anywhere. Public packages published that way also get
provenance attestations automatically, so the published tarball carries a
verifiable link back to the workflow run and commit that produced it.

Two smaller weaknesses sit in the same workflow. It enables `setup-node`'s
dependency cache during a publish, which lets a poisoned cache entry influence
what gets published, and it falls back to `npm install` whenever no lockfile is
present, which both drops the lockfile integrity boundary and runs lifecycle
scripts from whatever the registry resolves at that moment. `deploy-to-pages.yml`
carries the same fallback.

The intended outcome: a caller can publish with no stored credential and get
provenance for free, the token path keeps working for GitHub Packages and other
registries that have no OIDC support, the publish job no longer restores a
cache, and neither workflow can reach `npm install` without the caller saying
so.

## External facts this design rests on

Each of these was checked against upstream documentation or measured directly,
rather than assumed.

- npm trusted publishing requires npm CLI 11.5.1 or later and Node 22.14.0 or
  later, and works only against `https://registry.npmjs.org`.
- npm validates the **calling** workflow's filename, not the workflow that runs
  `npm publish`. npm's own documentation calls this out for `workflow_call`:
  "validation checks the calling workflow's name instead of the workflow that
  actually contains the publish command." A consumer therefore registers its own
  repository and its own release workflow filename, and this reusable workflow
  stays invisible to the publisher configuration. Trusted publishing through a
  reusable workflow is viable because of that, and the documentation has to say
  it plainly, because the opposite guess is the natural one.
- Provenance is generated without `--provenance` under trusted publishing, for
  public packages only, and `NPM_CONFIG_PROVENANCE=false` turns it off.
- `actions/setup-node`'s `package-manager-cache` input (present at the pinned
  v7.0.0) defaults to true and enables npm caching on its own whenever
  `package.json` names npm in `packageManager` or `devEngines.packageManager`.
  Clearing the `cache:` input is therefore not enough to keep a publish job off
  the cache.
- **A nested job's permissions are validated before its `if:` is evaluated.**
  Measured on 2026-09-21 with four runs on a throwaway branch: a caller granting
  `contents: read` alone fails at startup against a called workflow whose
  _skipped_ job declares `id-token: write`, while the identical call from a
  caller granting `id-token: write` starts, runs the token job and skips the
  other. Splitting a workflow into per-mode jobs therefore cannot spare a
  token-path caller the OIDC grant, which is what decided the shape below.

## Decisions taken

1. **Two workflows, one per auth mode.** `publish-to-npm.yml` keeps
   `contents: read`, `packages: write`; a new `publish-to-npm-with-oidc.yml`
   declares `contents: read`, `id-token: write`. Neither caller grants a
   permission its mode cannot use. The `auth: trusted|token` input the issue
   proposed would have meant one workflow declaring the union of both modes'
   permissions, so every token-path caller, including
   `cboone/cboone-alpine-plugins`, would have had to grant `id-token: write` to
   a job that will never mint an OIDC token. The caller chooses by which
   workflow it calls instead.
1. **Hardened install defaults, released as v5.0.0** with escape-hatch inputs.
   README's versioning policy counts a changed default as breaking, and
   `cboone/cboone-alpine-plugins` is a real caller with no lockfile, so the
   migration guide has a concrete case to describe.
1. **The OIDC workflow fails fast against a non-npmjs registry.** The input
   stays, defaulting to `https://registry.npmjs.org`, so a caller who copies
   `registry-url: https://npm.pkg.github.com` across from the token workflow
   gets a message naming the other workflow rather than an opaque 401, and a
   registry that gains OIDC support later needs no interface change.
1. **The install logic is duplicated, not extracted.** A reusable workflow's
   `./` action path resolves against the caller's checkout, so a
   repository-owned composite action would have to be fetched from
   `job.workflow_repository` at `job.workflow_sha` for what is a ten-line shell
   block. The fixture holds the three copies identical instead.

## Step 1: publish-to-npm.yml, the token path

Keeps its permissions, its `NODE_AUTH_TOKEN` secret and its publish step. Three
changes:

- Two new optional inputs, `allow-npm-install` (boolean, default false) and
  `run-install-scripts` (boolean, default false).
- `setup-node` gets `package-manager-cache: false` and loses `cache:` and
  `cache-dependency-path:`, so a publish never restores a cache.
- The install ternary is replaced by the shared step in step 3.

## Step 2: publish-to-npm-with-oidc.yml, the trusted path

New reusable workflow. `permissions: contents: read`, `id-token: write`, no
secrets at all. Inputs: `node-version`, `registry-url` (default
`https://registry.npmjs.org`), `provenance` (boolean, default true),
`allow-npm-install`, `run-install-scripts`, `timeout-minutes`. Steps:

- **Check the registry**, before anything else, failing when `registry-url` does
  not normalize to `https://registry.npmjs.org` and naming `publish-to-npm.yml`
  as the workflow for other registries.
- Checkout, then `setup-node` with the registry and `package-manager-cache:
false`.
- **Check the versions**, after `setup-node` so it reads the Node that will do
  the publishing, failing with a message naming `node-version` when `node` is
  below 22.14.0 or `npm` below 11.5.1. Comparison is a small bash function
  splitting on `.`, not `sort -V`, so the fixture can run the same step on
  macOS. A prerelease sorts below the release it precedes, so an npm
  `11.5.1-rc.0` does not clear a minimum of 11.5.1. Installing a newer npm is deliberately not offered: an unpinned
  `npm install -g npm@latest` would make the registry the sole integrity
  boundary, which the trust model forbids.
- Detect the lockfile, then the shared install step.
- An `environment` input, empty by default, applied to the job. Added after the
  branch review: the OIDC token's `environment` claim comes from this job, and a
  job calling a reusable workflow may not declare an environment of its own, so
  without the input a trusted publisher scoped to an environment is unreachable.
  Measured on 2026-09-24, along with `workflow_ref` naming the caller and
  `job_workflow_ref` naming this repository.
- **Disable provenance**, guarded by `if: ${{ !inputs.provenance }}`, writing
  `NPM_CONFIG_PROVENANCE=false` to `GITHUB_ENV`. Deliberately a conditional step
  rather than `NPM_CONFIG_PROVENANCE: ${{ inputs.provenance }}` on the publish
  step: npm reads an env config set to the empty string as true, and forcing
  `true` turns npm's automatic skip for a restricted package into a hard error.
- `npm publish`, with no `NODE_AUTH_TOKEN` binding anywhere in the file.

## Step 3: the shared install step

Replaces the `npm ci` / `npm install` ternary in all three places, byte-identical
in each, with only the `env:` bindings differing where the lockfile-detection
step's id differs:

```yaml
- name: Install dependencies
  shell: bash
  env:
    LOCKFILE: ${{ steps.<detect>.outputs.<path> }}
    ALLOW_NPM_INSTALL: ${{ inputs.allow-npm-install }}
    RUN_INSTALL_SCRIPTS: ${{ inputs.run-install-scripts }}
  run: |
    args=(--include=dev --no-audit --no-fund)
    [[ "${RUN_INSTALL_SCRIPTS}" == "true" ]] || args+=(--ignore-scripts)
    if [[ -n "${LOCKFILE}" ]]; then
      npm ci "${args[@]}"
    elif [[ "${ALLOW_NPM_INSTALL}" == "true" ]]; then
      echo "::warning::No lockfile found; npm install resolves versions at run time."
      npm install "${args[@]}"
    else
      echo "::error::No package-lock.json or npm-shrinkwrap.json found. Commit a lockfile, or set allow-npm-install: true."
      exit 1
    fi
```

The flag set matches what this repository's own CI already uses. Both entries
leave `INTERPOLATION_ALLOWLIST` in
`tests/fixtures/check-workflow-arg-binding.mjs`, which its staleness assertions
will demand; the allowlist drops from eight entries to six, and the four
documents that describe it as "two ternaries" change with it.

`deploy-to-pages.yml` gains the two inputs and keeps its `setup-node` cache: it
builds, it does not publish.

## Step 4: tests

A new fixture, `tests/fixtures/check-npm-publish.mjs`, in the established shape:
it reads the production steps out of the YAML through
`tests/fixtures/workflow-steps.mjs` and executes them under the runner's bash
against stubs that record their argument vector. A new
`tests/scrut/npm-publish.md` drives it one scenario per section, and a new
`run-ci.yml` job runs it on `ubuntu-latest` and `macos-latest`, matching the
`workflow-arg-binding` job it sits beside.

Scenarios:

- `registry`: the check accepts the npmjs registry in its documented spellings
  and rejects the GitHub Packages default, naming the token workflow.
- `versions`: the gate passes at exactly 22.14.0 and 11.5.1, passes above, and
  fails below each, with stub `node` and `npm` on `PATH`.
- `install`: with a lockfile present it runs `npm ci` with `--ignore-scripts`;
  without one and `allow-npm-install: true` it runs `npm install`; without one
  and the default it exits 1 and never invokes npm; `run-install-scripts: true`
  drops `--ignore-scripts` and nothing else.
- `parity`: the three install `run:` blocks are identical strings, which is what
  keeps the duplication honest.
- `shape`: static assertions that the OIDC workflow declares `id-token: write`
  and no `packages: write`, declares no secrets and binds `NODE_AUTH_TOKEN`
  nowhere, that the token workflow declares no `id-token`, and that both publish
  workflows set `package-manager-cache: false` and no `cache:`.

The `shape` scenario is what a future change to the permission blocks has to get
past, given that no CI job can call either publish workflow end to end without a
publishable package to point it at.

## Step 5: documentation

- `docs/workflows/publish-to-npm-with-oidc.md`: new. The npmjs.com publisher
  setup naming the caller's own repository and release workflow filename, the
  `id-token: write` grant, the version minimums, what provenance does and when
  to turn it off, why the cache is off.
- `docs/workflows/publish-to-npm.md`: the two install inputs, the cache change,
  and a pointer to the OIDC workflow.
- `docs/workflows/deploy-to-pages.md`: the two new inputs and the changed
  install behavior.
- `docs/migrations/v5.md`, linked from README's Migration section: the lockfile
  requirement, the lifecycle-script change, and how to move a token publish to
  trusted publishing. `cboone/cboone-alpine-plugins` publishes with no lockfile
  and is the worked example.
- `README.md`: a Quick Reference row for the new workflow, and the v5 migration
  link.
- `CHANGELOG.md` under `[Unreleased]`, referencing (#137).
- `docs/development.md`: the argument-binding paragraph loses the two ternaries,
  the testing section gains the new fixture and job, the `node-version` default
  list gains the new workflow, and the measured nested-job permission behavior
  is recorded.
- `.github/workflows/AGENTS.md`, root `AGENTS.md` and
  `.github/copilot-instructions.md`: the same allowlist sentence, in the three
  places it is repeated.

The npm CLI and Node minimums are floors that npm imposes, not versions this
repository ships, so they stay out of `scripts/check-tool-versions.py`.

## Verification

```bash
make lint          # actionlint, with shellcheck over the new run: blocks
make lint-yaml
make format-check
make lint-md
make spell         # pass .github/ paths explicitly; cspell skips dot-paths
npm ci
node tests/fixtures/check-workflow-arg-binding.mjs policy
node tests/fixtures/check-npm-publish.mjs install   # and each other scenario
scrut test tests/scrut/npm-publish.md
```

On the pull request: the new job green on both runners, and
`workflow-arg-binding` still green, since the allowlist changed underneath it.

Manual verification, which is the issue's own done-when and needs a package on
npmjs.com rather than GitHub Packages:

1. Configure a trusted publisher on the test package: the consuming repository,
   and the filename of the workflow that calls this one.
1. Call `publish-to-npm-with-oidc.yml` from a job granting `id-token: write` and
   `contents: read`, passing no secrets.
1. Expect: the run publishes, and the package page shows the provenance
   attestation linking back to the run.
1. Re-run an existing token-path publish unchanged, and confirm it still
   publishes and that its caller needed no new permission.

## Follow-ups, not in this change

- A `dry-run` input, with a `working-directory` or fixture package, would let
  `run-ci.yml` self-host both publish workflows the way it self-hosts the
  others, and would turn the `shape` assertions into an end-to-end test. Filed
  as [#152](https://github.com/cboone/gh-actions/issues/152).
- `run-ci.yml`'s own six `npm ci` invocations use two different flag sets, which
  this change leaves alone rather than widening its own diff. Filed as
  [#151](https://github.com/cboone/gh-actions/issues/151).
- `cboone/cboone-alpine-plugins` needs either a committed lockfile or
  `allow-npm-install: true` before it moves to v5.
- The manual verification above is the issue's own done-when and is still
  outstanding: it needs a package on npmjs.com and a merged tag.
