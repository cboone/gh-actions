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

```yaml
- uses: cboone/gh-actions/actions/create-pull-request@v3.0.0
  with:
    branch: chore/update-data
    commit-message: "chore: update generated data"
    title: "chore: update generated data"
    body: "Automated update."
    labels: automation
    delete-branch: true
```
