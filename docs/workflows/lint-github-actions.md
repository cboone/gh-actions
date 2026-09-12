# lint-github-actions

Run actionlint to validate GitHub Actions workflow files.

**Permissions:** `contents: read`

## Inputs

| Name                 | Type   | Default    | Description                   |
| -------------------- | ------ | ---------- | ----------------------------- |
| `actionlint-version` | string | `"1.7.12"` | actionlint version to install |
| `timeout-minutes`    | number | `10`       | Job timeout in minutes        |

### How the workflow installs actionlint

The job runs the script behind
[install-pinned-tool](../../actions/install-pinned-tool/README.md), which it
fetches over `raw.githubusercontent.com` from `${{ job.workflow_repository }}`
at `${{ job.workflow_sha }}`: the repository and commit the workflow file
itself came from, which is whatever ref the caller pinned. The actionlint
archive is verified against the `checksums.txt` actionlint publishes with each
release, so any `actionlint-version` with such a release installs.

Fetching at the workflow's own commit rules out two setups, as it does for
[lint-text](lint-text.md):

- **GitHub Enterprise Server.** The `job.workflow_*` properties are not
  available there, so the job fails with an `::error::` before actionlint
  runs. Run actionlint in your own job with
  [set-up-actionlint](../../actions/set-up-actionlint/README.md) instead.
- **Private forks of this repo.** `raw.githubusercontent.com` serves public
  repositories only, so a private fork cannot supply the script; the same
  workaround applies.

## Usage

```yaml
jobs:
  github:
    uses: cboone/gh-actions/.github/workflows/lint-github-actions.yml@v3.1.1
```
