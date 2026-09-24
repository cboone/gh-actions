# publish-to-npm-with-oidc

Publish an npm package to npmjs.com through npm's trusted publishing. The job
presents a GitHub OIDC token, npm validates it against a publisher configured on
the package, and no credential is stored anywhere. Public packages also get
provenance attestations, so the published tarball carries a verifiable link back
to the workflow run and the commit that produced it.

Use [publish-to-npm](publish-to-npm.md) for GitHub Packages and for any other
registry: trusted publishing works only against `https://registry.npmjs.org`,
and this workflow refuses any other `registry-url` before it does anything else.

The two workflows are separate files because a caller must grant every
permission the workflow it calls declares, and a nested job's permissions are
checked before its `if:` condition is evaluated. A single workflow with an
auth-mode input would therefore force `id-token: write` on callers that publish
with a token and will never mint an OIDC token.

**Requires:** npm 11.5.1 or later and Node 22.14.0 or later. In practice that
means `node-version` 24.5.0 or later, the first release whose bundled npm is new
enough: no Node 22 or 23 release ships one, so npm's Node floor is necessary
without being sufficient. The default `24.21.0` bundles npm 11.19.0. The
workflow checks both versions after installing Node and fails naming the version
to use, because npm below those versions reports only that authentication
failed. It deliberately does not install a newer npm itself: an unpinned
`npm install -g npm@latest` would make the registry the sole integrity boundary
for the tool doing the publishing.

**Permissions:** `contents: read`, `id-token: write`. The calling job must grant
both, or the run fails at startup before any job begins.

## Configuring the publisher

This happens once per package, on npmjs.com, outside any workflow. On the
package's Settings page, add a trusted publisher for GitHub Actions and fill in:

| Field                | Value                                                               |
| -------------------- | ------------------------------------------------------------------- |
| Organization or user | The owner of **your** repository                                    |
| Repository           | **Your** repository, the one holding the package source             |
| Workflow filename    | The file in **your** repository that calls this workflow            |
| Environment          | Optional; if you set one, pass the same name as `environment` below |

The workflow filename is your own release workflow, not
`publish-to-npm-with-oidc.yml`. npm validates the calling workflow rather than
the one containing the `npm publish` command, which is what makes trusted
publishing through a reusable workflow work at all.

## Inputs

| Name                  | Type    | Default                      | Description                                              |
| --------------------- | ------- | ---------------------------- | -------------------------------------------------------- |
| `node-version`        | string  | `"24.21.0"`                  | Node.js version to install                               |
| `registry-url`        | string  | `https://registry.npmjs.org` | npm registry URL; only npmjs.com supports OIDC           |
| `provenance`          | boolean | `true`                       | Publish provenance attestations                          |
| `environment`         | string  | `""`                         | Environment for the publish job; empty for none          |
| `allow-npm-install`   | boolean | `false`                      | Permit `npm install` when the repository has no lockfile |
| `run-install-scripts` | boolean | `false`                      | Run dependency lifecycle scripts while installing        |
| `timeout-minutes`     | number  | `10`                         | Job timeout in minutes                                   |

## Secrets

None. Passing a publishing token to this workflow is not possible, which is the
point of it.

## Behavior worth knowing

**Provenance.** npm generates attestations on its own for public packages, and
skips them for packages published with restricted access. Set
`provenance: false` for a restricted package only if npm reports the skip as an
error; the input writes `NPM_CONFIG_PROVENANCE=false` and nothing else.

**Environments.** A publisher may name a deployment environment, and the OIDC
claim it is matched against comes from this workflow's publish job, not from
yours: `environment` is not one of the keywords a job calling a reusable
workflow may use. Pass the name through the `environment` input instead, and it
must match what the publisher names. The default, empty, runs the job with no
environment and leaves the claim absent, which is what a publisher configured
without one expects. Setting it also puts the environment's protection rules,
such as required reviewers, in front of the publish.

**No dependency cache.** `setup-node` runs with `package-manager-cache: false`,
so a publish never restores a cache an earlier job wrote. Clearing the `cache`
input alone would not be enough: `setup-node` enables npm caching on its own
whenever `package.json` names npm in `packageManager` or
`devEngines.packageManager`.

**Installs need a lockfile.** With `package-lock.json` or `npm-shrinkwrap.json`
present, dependencies install with
`npm ci --include=dev --no-audit --no-fund --ignore-scripts`. Without one, the
job fails rather than resolving versions at publish time; set
`allow-npm-install: true` to opt into `npm install`. Lifecycle scripts stay off
unless `run-install-scripts: true`, and `npm publish` still runs the package's
own `prepack` and `prepare` scripts either way.

## Usage

```yaml
name: Release

on:
  push:
    tags: ["v*"]

jobs:
  publish:
    permissions:
      contents: read
      id-token: write
    uses: cboone/gh-actions/.github/workflows/publish-to-npm-with-oidc.yml@v4.1.0
```

The publisher registered on npmjs.com for this example names the repository
holding it and `release.yml`, the file above, and leaves Environment empty.

For a publisher scoped to an environment, and for the protection rules that
come with one:

```yaml
jobs:
  publish:
    permissions:
      contents: read
      id-token: write
    uses: cboone/gh-actions/.github/workflows/publish-to-npm-with-oidc.yml@v4.1.0
    with:
      environment: release
```
