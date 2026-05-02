# deploy-to-pages

Build a static site and deploy it to GitHub Pages. Optionally sets up Go
and/or Node.js before running the build command.

**Permissions:** `contents: read`, `pages: write`, `id-token: write`

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
    uses: cboone/gh-actions/.github/workflows/deploy-to-pages.yml@v3.0.0
    with:
      build-command: "npm run build"
      artifact-path: ./dist
      setup-node: true
```
