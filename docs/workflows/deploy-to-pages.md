# deploy-to-pages

Build a static site and deploy it to GitHub Pages. Optionally sets up Go
and/or Node.js before running the build command.

**Permissions:** `contents: read`, `pages: write`, `id-token: write`

`timeout-minutes` applies to both the `build` and `deploy` jobs and bounds
execution only. The `deploy` job runs in the `github-pages` environment, and
any time it spends waiting on that environment's protection rules (required
reviewers, wait timer) is not execution time: it falls under GitHub's
separate, non-configurable 30-day limit on environment approvals, and under
the 35-day limit on a workflow run. Sizing `timeout-minutes` for the
deployment itself is therefore correct, with no allowance needed for an
approver. Note also that `actions/deploy-pages` polls the Pages deployment
API under its own 10-minute timeout, so a `timeout-minutes` below 10 cuts
the deployment off before the action can report its own clearer error.

## Inputs

| Name              | Type    | Default         | Description                          |
| ----------------- | ------- | --------------- | ------------------------------------ |
| `build-command`   | string  |                 | Command to build the site (required) |
| `artifact-path`   | string  | `./_site`       | Path to the built site directory     |
| `runs-on`         | string  | `ubuntu-latest` | Runner label                         |
| `setup-go`        | boolean | `false`         | Set up Go before building            |
| `go-version-file` | string  | `go.mod`        | File to read the Go version from     |
| `setup-node`      | boolean | `false`         | Set up Node.js before building       |
| `node-version`    | string  | `"24.15.0"`     | Node.js version to install           |
| `timeout-minutes` | number  | `15`            | Job timeout in minutes               |

## Usage

```yaml
jobs:
  pages:
    uses: cboone/gh-actions/.github/workflows/deploy-to-pages.yml@v3.1.1
    with:
      build-command: "npm run build"
      artifact-path: ./dist
      setup-node: true
```
