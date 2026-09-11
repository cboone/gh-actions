# lint-shell

Run ShellCheck and shfmt on shell scripts. Automatically discovers scripts
by file extension and MIME type.

shfmt is installed from its release binary and verified against the
committed SHA-256 in `shfmt-checksums`. To use another shfmt version, pass
its checksum with it (see [Usage](#usage)).

**Permissions:** `contents: read`

## Inputs

| Name              | Type    | Default              | Description                                             |
| ----------------- | ------- | -------------------- | ------------------------------------------------------- |
| `run-shellcheck`  | boolean | `true`               | Run ShellCheck                                          |
| `run-shfmt`       | boolean | `true`               | Run shfmt format check                                  |
| `shfmt-version`   | string  | `"3.13.1"`           | shfmt version to install                                |
| `shfmt-checksums` | string  | the v3.13.1 binaries | `sha256sum`-format lines for the shfmt release binaries |
| `timeout-minutes` | number  | `10`                 | Job timeout in minutes                                  |

### How the workflow installs shfmt

The job runs the script behind
[install-pinned-tool](../../actions/install-pinned-tool/README.md), which it
fetches over `raw.githubusercontent.com` from `${{ job.workflow_repository }}`
at `${{ job.workflow_sha }}`: the repository and commit the workflow file
itself came from, which is whatever ref the caller pinned. A `./` action path
cannot do this, because in a reusable workflow it resolves against the
caller's checkout.

The checksum keys are asset names, so overriding `shfmt-version` without
`shfmt-checksums` fails with `No checksum entry for shfmt_v<version>_linux_amd64`
rather than installing an unverified binary. The job runs on `ubuntu-latest`,
so an override needs at least the `linux_amd64` line.

Two limitations follow from fetching at the workflow's own commit, as they do
for [lint-text](lint-text.md):

- **GitHub Enterprise Server.** The `job.workflow_*` properties are not
  available there, so the fetch fails with an `::error::`. Set
  `run-shfmt: false`, which leaves ShellCheck running, or install shfmt in
  your own job with [set-up-shfmt](../../actions/set-up-shfmt/README.md).
- **Private forks of this repo.** `raw.githubusercontent.com` serves public
  repositories only, so a private fork cannot supply the script; the same two
  workarounds apply.

Neither affects a run with `run-shfmt: false` or with no shell scripts to
lint, which fetches nothing.

## Usage

```yaml
jobs:
  shell:
    uses: cboone/gh-actions/.github/workflows/lint-shell.yml@v3.1.1
```

Another shfmt version, with the checksum for the `ubuntu-latest` binary:

```yaml
jobs:
  shell:
    uses: cboone/gh-actions/.github/workflows/lint-shell.yml@v3.1.1
    with:
      shfmt-version: 3.14.1
      shfmt-checksums: |
        76e77641faa025814b77f153b29796b8e6fa2fca03e0c76a691608b86c7ea7bf  shfmt_v3.14.1_linux_amd64
```
