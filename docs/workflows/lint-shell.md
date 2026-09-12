# lint-shell

Run ShellCheck and shfmt on shell scripts. Automatically discovers scripts
by file extension and MIME type.

Both tools are installed from their release assets and verified against the
committed SHA-256 in `shellcheck-checksums` and `shfmt-checksums`. To use
another version of either, pass its checksum with it (see
[Usage](#usage)).

**Permissions:** `contents: read`

## Inputs

| Name                   | Type    | Default              | Description                                                  |
| ---------------------- | ------- | -------------------- | ------------------------------------------------------------ |
| `run-shellcheck`       | boolean | `true`               | Run ShellCheck                                               |
| `run-shfmt`            | boolean | `true`               | Run shfmt format check                                       |
| `shellcheck-version`   | string  | `"0.11.0"`           | shellcheck version to install                                |
| `shellcheck-checksums` | string  | the v0.11.0 archives | `sha256sum`-format lines for the shellcheck release archives |
| `shfmt-version`        | string  | `"3.13.1"`           | shfmt version to install                                     |
| `shfmt-checksums`      | string  | the v3.13.1 binaries | `sha256sum`-format lines for the shfmt release binaries      |
| `timeout-minutes`      | number  | `10`                 | Job timeout in minutes                                       |

### How the workflow installs its tools

The job runs the script behind
[install-pinned-tool](../../actions/install-pinned-tool/README.md), which it
fetches over `raw.githubusercontent.com` from `${{ job.workflow_repository }}`
at `${{ job.workflow_sha }}`: the repository and commit the workflow file
itself came from, which is whatever ref the caller pinned. A `./` action path
cannot do this, because in a reusable workflow it resolves against the
caller's checkout.

Neither upstream publishes a checksum file suitable for this pinning model, so
both sets of digests are committed as input defaults. The keys are asset
names, so overriding a version without its checksums fails with
`No checksum entry for <asset>` rather than installing an unverified binary.
The job runs on `ubuntu-latest`, so an override needs at least the
`linux.x86_64` line for shellcheck or the `linux_amd64` line for shfmt.

shellcheck is pinned rather than taken from the runner image for the reason
[lint-github-actions](lint-github-actions.md#why-shellcheck-is-pinned-here)
records: a runner image update would otherwise change what this job reports
with no change to any version you pinned, and would lint your scripts with a
different shellcheck than the one actionlint shells out to. The
`ubuntu-latest` image ships ShellCheck 0.9.0, so the first run on a version
of this workflow that pins 0.11.0 can report findings from checks added
since (SC2327 to SC2332 among them).

Two limitations follow from fetching at the workflow's own commit, as they do
for [lint-text](lint-text.md):

- **GitHub Enterprise Server.** The `job.workflow_*` properties are not
  available there, so the fetch fails with an `::error::`. Run ShellCheck and
  shfmt in your own job with
  [set-up-shellcheck](../../actions/set-up-shellcheck/README.md) and
  [set-up-shfmt](../../actions/set-up-shfmt/README.md) instead.
- **Private forks of this repo.** `raw.githubusercontent.com` serves public
  repositories only, so a private fork cannot supply the script; the same
  workaround applies.

Neither affects a run with both `run-shellcheck: false` and `run-shfmt: false`,
or with no shell scripts to lint, which fetches nothing.

## Usage

```yaml
jobs:
  shell:
    uses: cboone/gh-actions/.github/workflows/lint-shell.yml@v3.1.1
```

Another version of either tool, with the checksum for the `ubuntu-latest`
asset:

```yaml
jobs:
  shell:
    uses: cboone/gh-actions/.github/workflows/lint-shell.yml@v3.1.1
    with:
      shellcheck-version: 0.10.0
      shellcheck-checksums: |
        6c881ab0698e4e6ea235245f22832860544f17ba386442fe7e9d629f8cbedf87  shellcheck-v0.10.0.linux.x86_64.tar.xz
      shfmt-version: 3.14.1
      shfmt-checksums: |
        76e77641faa025814b77f153b29796b8e6fa2fca03e0c76a691608b86c7ea7bf  shfmt_v3.14.1_linux_amd64
```
