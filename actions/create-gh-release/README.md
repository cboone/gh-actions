# create-gh-release

Create a GitHub Release with `gh release create`. Thin alternative to
[`softprops/action-gh-release`](https://github.com/softprops/action-gh-release)
for callers that need asset uploads, auto-generated release notes, and
draft/prerelease flags. The `gh` CLI ships preinstalled on GitHub-hosted
runners, so no binary download or checksum table is needed.

For changelog-driven releases, prefer the
[create-gh-release-from-changelog](../../docs/workflows/create-gh-release-from-changelog.md)
reusable workflow. Reach for `create-gh-release` when you need to attach
files or auto-generate notes from merged PRs.

`body`, `body-path`, and `generate-release-notes` are mutually exclusive.

## Inputs

| Name                     | Type    | Default                  | Description                                                 |
| ------------------------ | ------- | ------------------------ | ----------------------------------------------------------- |
| `tag-name`               | string  | `${{ github.ref_name }}` | Git tag for the release                                     |
| `name`                   | string  | `""`                     | Release title (defaults to the tag name when empty)         |
| `body`                   | string  | `""`                     | Inline release notes                                        |
| `body-path`              | string  | `""`                     | Path to a file containing release notes                     |
| `generate-release-notes` | boolean | `false`                  | Auto-generate release notes from merged pull requests       |
| `files`                  | string  | `""`                     | Newline-delimited file paths to attach (globs are expanded) |
| `draft`                  | boolean | `false`                  | Create the release as a draft                               |
| `prerelease`             | boolean | `false`                  | Mark the release as a prerelease                            |
| `target-commitish`       | string  | `""`                     | Commit SHA, branch, or tag to point the release at          |
| `token`                  | string  | `${{ github.token }}`    | GitHub token (must have `contents: write`)                  |

## Outputs

| Name  | Description                |
| ----- | -------------------------- |
| `url` | URL of the created release |

## Usage

```yaml
- uses: cboone/gh-actions/actions/create-gh-release@v3.0.0
  with:
    files: |
      dist/*.tar.gz
      dist/*.zip
    generate-release-notes: true
```
