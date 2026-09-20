# lint-shell

Run ShellCheck and shfmt on tracked shell scripts. Discovery uses shfmt's
shell extensions and shebang detection throughout the tracked tree, including
extension-less scripts in any directory. Untracked build output is excluded.
Discovery requires the Git index provided by the workflow's checkout step;
full Git history is not required. Submodule contents and symlinks are not included.

shfmt is installed before discovery whenever either checker is enabled,
including with `run-shfmt: false`. An empty discovered set emits a notice and
writes to the job summary before skipping both checks. Disabling both checkers
skips installation and discovery.

The format check uses `shfmt -d` without style flags so it reads
`.editorconfig`. Adding a style flag such as `-i 2` disables those settings.

Discovery checks each tracked regular file with `shfmt -f` and retains its
original path in a NUL-separated manifest for both checkers, except that a file
named exactly `-` is passed as `./-` so it cannot be interpreted as stdin. A
single batched `-f=0` call would be cheaper, but shfmt only stopped listing
explicitly supplied non-shell files in that mode at 3.14.1, and `shfmt-version`
is caller-overridable, so per-file `-f` stays correct for any pin.
Collapsing the loop is tracked in [#124](https://github.com/cboone/gh-actions/issues/124).

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
| `shfmt-version`        | string  | `"3.14.1"`           | shfmt version to install                                     |
| `shfmt-checksums`      | string  | the v3.14.1 binaries | `sha256sum`-format lines for the shfmt release binaries      |
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
which fetches nothing. With either checker enabled, the installer is fetched
even when there are no shell scripts, because discovery requires shfmt.

## Usage

```yaml
jobs:
  shell:
    uses: cboone/gh-actions/.github/workflows/lint-shell.yml@v3.2.0
```

Another version of either tool, with the checksum for the `ubuntu-latest`
asset:

```yaml
jobs:
  shell:
    uses: cboone/gh-actions/.github/workflows/lint-shell.yml@v3.2.0
    with:
      shellcheck-version: 0.10.0
      shellcheck-checksums: |
        6c881ab0698e4e6ea235245f22832860544f17ba386442fe7e9d629f8cbedf87  shellcheck-v0.10.0.linux.x86_64.tar.xz
      shfmt-version: 3.13.1
      shfmt-checksums: |
        fb096c5d1ac6beabbdbaa2874d025badb03ee07929f0c9ff67563ce8c75398b1  shfmt_v3.13.1_linux_amd64
```
