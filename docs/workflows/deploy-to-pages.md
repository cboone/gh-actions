# deploy-to-pages

Build a static site and deploy it to GitHub Pages. Optionally sets up Go
and/or Node.js before running the build command.

`timeout-minutes` applies to both jobs and bounds execution only. The
`deploy` job runs in the `github-pages` environment, and time it spends
waiting on that environment's protection rules (required reviewers, wait
timer) is not execution time: it falls under GitHub's separate,
non-configurable 30-day limit on environment approvals. The two cannot
share a clock, since the 360-minute default would otherwise cancel every
job awaiting approval after six hours. Size this input for the deployment,
not for an approver.

`actions/deploy-pages` polls the Pages deployment API under its own
10-minute timeout, so a `timeout-minutes` below 10 cuts the deployment off
before the action can report its own clearer error.

With `setup-node: true`, dependencies install with
`npm ci --include=dev --no-audit --no-fund --ignore-scripts` when
`package-lock.json` or `npm-shrinkwrap.json` is present. Without a lockfile the
build fails rather than resolving versions at build time; set
`allow-npm-install: true` to opt into `npm install`. Lifecycle scripts stay off
unless `run-install-scripts: true`, which a build needing a `postinstall` step
has to set.

The npm cache follows the lockfile: with one present the build caches on it,
and with none `setup-node` is told not to cache at all. Otherwise a repository
whose `package.json` names npm in `packageManager` gets `setup-node`'s automatic
caching, which fails on the missing lockfile before the install step can say
which input to set.

`build-command` runs in the checked-out workspace, which the workflow checks out
with `persist-credentials: false`. It does not inherit a Git credential from
`.git/config`, so a command that has to authenticate to GitHub needs a token
of its own, through `gh` and `GH_TOKEN` or an explicit remote.

**Permissions:** `contents: read`, `pages: write`, `id-token: write`

## Inputs

| Name                  | Type    | Default         | Description                                              |
| --------------------- | ------- | --------------- | -------------------------------------------------------- |
| `build-command`       | string  |                 | Command to build the site (required)                     |
| `artifact-path`       | string  | `./_site`       | Path to the built site directory                         |
| `runs-on`             | string  | `ubuntu-latest` | Runner label                                             |
| `setup-go`            | boolean | `false`         | Set up Go before building                                |
| `go-version-file`     | string  | `go.mod`        | File to read the Go version from                         |
| `setup-node`          | boolean | `false`         | Set up Node.js before building                           |
| `node-version`        | string  | `"24.21.0"`     | Node.js version to install                               |
| `allow-npm-install`   | boolean | `false`         | Permit `npm install` when the repository has no lockfile |
| `run-install-scripts` | boolean | `false`         | Run dependency lifecycle scripts while installing        |
| `timeout-minutes`     | number  | `15`            | Job timeout in minutes                                   |

## Usage

```yaml
jobs:
  pages:
    uses: cboone/gh-actions/.github/workflows/deploy-to-pages.yml@v4.1.0
    with:
      build-command: "npm run build"
      artifact-path: ./dist
      setup-node: true
```
