# lint-github-actions

Run actionlint to validate GitHub Actions workflow files. Embedded shell in
every `run:` block is linted too, by the pinned shellcheck actionlint shells
out to.

**Permissions:** `contents: read`

## Inputs

| Name                   | Type   | Default              | Description                                                  |
| ---------------------- | ------ | -------------------- | ------------------------------------------------------------ |
| `actionlint-version`   | string | `"1.7.12"`           | actionlint version to install                                |
| `shellcheck-version`   | string | `"0.11.0"`           | shellcheck version to install                                |
| `shellcheck-checksums` | string | the v0.11.0 archives | `sha256sum`-format lines for the shellcheck release archives |
| `timeout-minutes`      | number | `10`                 | Job timeout in minutes                                       |

### Why shellcheck is pinned here

actionlint shells out to `shellcheck` for every `run:` block, which is the
only thing that lints the embedded shell in a workflow file. With no
`shellcheck` on `PATH` it skips all of them and still exits 0, so a job that
leaves shellcheck to the runner image is a vacuous pass on any image without
one, with nothing in the log to say so.

So the job installs shellcheck to an exact version, verified against a
committed SHA-256, and reports both tool versions before running actionlint.
The `shellcheck` line in that report is the only evidence that the
integration had anything to shell out to. Pinning it also keeps this job and
[lint-shell](lint-shell.md) on the same shellcheck, where the runner image's
copy would let a runner image update change what both report with no change
to any version you pinned.

### How the workflow installs its tools

The job runs the script behind
[install-pinned-tool](../../actions/install-pinned-tool/README.md), which it
fetches over `raw.githubusercontent.com` from `${{ job.workflow_repository }}`
at `${{ job.workflow_sha }}`: the repository and commit the workflow file
itself came from, which is whatever ref the caller pinned. The actionlint
archive is verified against the `checksums.txt` actionlint publishes with each
release, so any `actionlint-version` with such a release installs.

The `ubuntu-latest` image ships ShellCheck 0.9.0, so the first run on a
version of this workflow that pins 0.11.0 can report findings from checks
added since (SC2327 to SC2332 among them). Fix them, add a
`# shellcheck disable=` directive, or pin `shellcheck-version: 0.9.0` with
that release's checksum while you work through them.

shellcheck publishes no checksum file and no digests in its release notes, so
its digests are committed as the `shellcheck-checksums` default. The keys are
asset names, so overriding `shellcheck-version` without `shellcheck-checksums`
fails with `No checksum entry for shellcheck-v<version>.linux.x86_64.tar.xz`
rather than installing an unverified binary. The job runs on `ubuntu-latest`,
so an override needs at least the `linux.x86_64` line.

Fetching at the workflow's own commit rules out two setups, as it does for
[lint-text](lint-text.md):

- **GitHub Enterprise Server.** The `job.workflow_*` properties are not
  available there, so the job fails with an `::error::` before actionlint
  runs. Run actionlint in your own job with
  [set-up-shellcheck](../../actions/set-up-shellcheck/README.md) and
  [set-up-actionlint](../../actions/set-up-actionlint/README.md) instead.
- **Private forks of this repo.** `raw.githubusercontent.com` serves public
  repositories only, so a private fork cannot supply the script; the same
  workaround applies.

## Usage

```yaml
jobs:
  github:
    uses: cboone/gh-actions/.github/workflows/lint-github-actions.yml@v5.0.0
```

Another shellcheck version, with the checksum for the `ubuntu-latest`
archive:

```yaml
jobs:
  github:
    uses: cboone/gh-actions/.github/workflows/lint-github-actions.yml@v5.0.0
    with:
      shellcheck-version: 0.10.0
      shellcheck-checksums: |
        6c881ab0698e4e6ea235245f22832860544f17ba386442fe7e9d629f8cbedf87  shellcheck-v0.10.0.linux.x86_64.tar.xz
```
