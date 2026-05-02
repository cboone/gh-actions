# publish-to-npm

Publish an npm package to a registry. Detects lockfile presence to choose
between `npm ci` and `npm install`.

**Permissions:** `contents: read`, `packages: write`

## Inputs

| Name              | Type   | Default                      | Description                |
| ----------------- | ------ | ---------------------------- | -------------------------- |
| `node-version`    | string | `"24.15.0"`                  | Node.js version to install |
| `registry-url`    | string | `https://npm.pkg.github.com` | npm registry URL           |
| `timeout-minutes` | number | `10`                         | Job timeout in minutes     |

## Secrets

| Name              | Required | Description                               |
| ----------------- | -------- | ----------------------------------------- |
| `NODE_AUTH_TOKEN` | Yes      | Authentication token for the npm registry |

## Usage

```yaml
jobs:
  publish:
    uses: cboone/gh-actions/.github/workflows/publish-to-npm.yml@v3.0.0
    secrets:
      NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
