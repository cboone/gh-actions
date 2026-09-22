# publish-to-npm

Publish an npm package to a registry, authenticating with a token the caller
supplies. Suits GitHub Packages, a private registry, and anything else without
OIDC support.

For npmjs.com, prefer
[publish-to-npm-with-oidc](publish-to-npm-with-oidc.md): it stores no
credential at all and publishes provenance attestations with the package.

**Permissions:** `contents: read`, `packages: write`

## Inputs

| Name                  | Type    | Default                      | Description                                              |
| --------------------- | ------- | ---------------------------- | -------------------------------------------------------- |
| `node-version`        | string  | `"24.21.0"`                  | Node.js version to install                               |
| `registry-url`        | string  | `https://npm.pkg.github.com` | npm registry URL                                         |
| `allow-npm-install`   | boolean | `false`                      | Permit `npm install` when the repository has no lockfile |
| `run-install-scripts` | boolean | `false`                      | Run dependency lifecycle scripts while installing        |
| `timeout-minutes`     | number  | `10`                         | Job timeout in minutes                                   |

## Secrets

| Name              | Required | Description                               |
| ----------------- | -------- | ----------------------------------------- |
| `NODE_AUTH_TOKEN` | Yes      | Authentication token for the npm registry |

## Behavior worth knowing

**No dependency cache.** `setup-node` runs with `package-manager-cache: false`,
so a publish never restores a cache an earlier job wrote, which a poisoned entry
could otherwise ride into the published artifact. Clearing the `cache` input
alone would not be enough: `setup-node` enables npm caching on its own whenever
`package.json` names npm in `packageManager` or `devEngines.packageManager`.

**Installs need a lockfile.** With `package-lock.json` or `npm-shrinkwrap.json`
present, dependencies install with
`npm ci --include=dev --no-audit --no-fund --ignore-scripts`. Without one, the
job fails rather than resolving versions at publish time; set
`allow-npm-install: true` to opt into `npm install`. Lifecycle scripts stay off
unless `run-install-scripts: true`, and `npm publish` still runs the package's
own `prepack` and `prepare` scripts either way.

## Usage

```yaml
jobs:
  publish:
    uses: cboone/gh-actions/.github/workflows/publish-to-npm.yml@v4.1.0
    secrets:
      NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
