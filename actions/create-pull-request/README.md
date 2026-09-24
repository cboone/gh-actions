# create-pull-request

SHA-pinned wrapper around
[peter-evans/create-pull-request](https://github.com/peter-evans/create-pull-request).
Centralizes version management so downstream repos do not pin the upstream
action individually.

## Inputs

| Name             | Type    | Default                               | Description                                       |
| ---------------- | ------- | ------------------------------------- | ------------------------------------------------- |
| `token`          | string  | `${{ github.token }}`                 | GITHUB_TOKEN or a personal access token           |
| `branch`         | string  | `create-pull-request/patch`           | The pull request branch name                      |
| `delete-branch`  | boolean | `false`                               | Delete the branch when the PR is merged or closed |
| `base`           | string  | Branch checked out in the workflow    | Pull request base branch                          |
| `commit-message` | string  | `[create-pull-request] automated ...` | The commit message for the changes                |
| `title`          | string  | `Changes by create-pull-request ...`  | The title of the pull request                     |
| `body`           | string  | `""`                                  | The body of the pull request                      |
| `labels`         | string  | `""`                                  | Comma or newline-separated labels                 |
| `assignees`      | string  | `""`                                  | Comma or newline-separated assignees              |
| `draft`          | boolean | `false`                               | Create the pull request as a draft                |

## Outputs

| Name                     | Description                                         |
| ------------------------ | --------------------------------------------------- |
| `pull-request-number`    | The pull request number                             |
| `pull-request-url`       | The URL of the pull request                         |
| `pull-request-operation` | Operation performed: created, updated, closed, none |
| `pull-request-head-sha`  | The commit SHA of the pull request branch           |
| `pull-request-branch`    | The branch name of the pull request                 |

## Usage

Check out with `persist-credentials: false`. The action pushes with the `token`
input, not with a credential left behind in `.git/config`: upstream saves and
unsets any persisted `extraheader`, configures its own, pushes, then restores
it. Leaving the default in place only leaves the job's token readable by every
later step.

```yaml
- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
  with:
    persist-credentials: false

- uses: cboone/gh-actions/actions/create-pull-request@v4.1.0
  with:
    branch: chore/update-data
    commit-message: "chore: update generated data"
    title: "chore: update generated data"
    body: "Automated update."
    labels: automation
    delete-branch: true
```
