# create-gh-release-from-changelog

Create a GitHub Release from a version tag, extracting release notes from a
changelog file in Keep a Changelog format.

**Permissions:** `contents: write`

## Inputs

| Name              | Type    | Default         | Description                          |
| ----------------- | ------- | --------------- | ------------------------------------ |
| `changelog-file`  | string  | `CHANGELOG.md`  | Path to the changelog file           |
| `draft`           | boolean | `false`         | Create the release as a draft        |
| `prerelease`      | boolean | `false`         | Mark the release as a prerelease     |
| `runs-on`         | string  | `ubuntu-latest` | Runner label (Windows not supported) |
| `timeout-minutes` | number  | `10`            | Job timeout in minutes               |

## Usage

```yaml
jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/create-gh-release-from-changelog.yml@v3.0.0
```
