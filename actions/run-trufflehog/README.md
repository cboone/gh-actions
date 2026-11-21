# run-trufflehog

Install trufflehog binary and run a scan.

Reported findings fail the action. The scan reports verified credentials and
unknown results caused by verification errors. Unverified results are excluded
to limit noise from invalid credentials, so revoked credentials and detections
without verification are outside this gate.

Without `allowlist`, any reported finding fails the step with TruffleHog's own
exit code `183`.

With `allowlist` set, a scan that completes hands its findings to the checker,
whose exit code the step then takes: `0` when every finding is allowed, `1`
when any finding is not, and `2` for an allowlist or scan output it could not
use. If a scan fails after writing usable findings, the checker still reports
them and the step returns TruffleHog's error status.

Only an indeterminate finding whose commit, path, line and detector all match
an entry is allowed. A verified finding fails even when an entry matches it, as
the rules below set out.

`--no-update` and `--fail` are always set by this action and stripped from
`args`, so the pinned, checksum-verified binary cannot update itself mid-scan
and findings cannot exit successfully.

The action controls the output format in both modes. It adds `--json`,
strips `-j`, `--json` and `--no-json` from `args`, and refuses
`--json-legacy`, `--sarif`, `--github-actions` and `--output-report`,
including forms with an attached value.

The action trusts `args`. Its checks match the spellings listed above, not
every way an option can reach TruffleHog: options in an `@file` argument file
are not checked. Report output a caller enables that way is the caller's to
keep out of logs and artifacts.

Each finding's log line contains its detector, verification state, commit,
path and line. For other sources besides Git and Filesystem, the log also
includes the source type and any available location fields. The action
captures scanner JSON and stderr in a private temporary directory and
removes it when the step exits.

Filenames containing the legacy `##[` marker may trigger runner annotations.
Finding metadata can expose a credential used as a filename.

Reporting requires `jq`, which GitHub-hosted Linux and macOS images provide.
The action checks for it before scanning, even when `allowlist` is unset.

## Inputs

| Name        | Type   | Default     | Description                                   |
| ----------- | ------ | ----------- | --------------------------------------------- |
| `version`   | string | `3.97.5`    | trufflehog version to install                 |
| `args`      | string | (see below) | Arguments to pass to trufflehog, one per line |
| `allowlist` | string | `""`        | Path to a JSON allowlist of reviewed findings |

Default `args`:

```text
filesystem
--directory
.
```

## Allowlisting a reviewed finding

Some credential-shaped strings are deliberate and cannot be removed, such as a
synthetic fixture in a commit that must not be rewritten. `allowlist` permits
those exact findings without excluding the file, suppressing the detector, or
printing the finding.

Point it at a JSON file in your checkout:

```json
{
  "version": 1,
  "entries": [
    {
      "reason": "Synthetic URI fixture reviewed in #23; immutable test commit",
      "detector": "URI",
      "commit": "0f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c",
      "path": "test/support/credential_fixtures.ex",
      "line": 42
    }
  ]
}
```

An entry matches one finding and only that finding: all four of `commit`,
`path`, `line` and `detector` must be equal, so changing any of them, or
moving the fixture, fails the scan again. Every field is required, including
`reason`, which records why the finding was accepted. `commit` must be a full
40-character lowercase SHA, because a short SHA or a ref can come to mean
something else.

Three rules keep the gate strict:

- **A verified finding is never allowlisted.** If TruffleHog confirms a
  credential is live, the scan fails even when its tuple is listed. A fixture
  that turns into a real credential cannot go quiet.
- **Entries key on a commit**, so they apply to full-history scans. A
  working-tree finding has no commit and always fails.
- **An unused entry warns rather than fails**, so a stale entry is visible
  without breaking a scan that legitimately no longer reaches it.

An allowed finding also names the entry that covered it and that entry's
`reason`. Both come from your reviewed allowlist. The checker reports invalid
findings JSON without quoting the input.

If TruffleHog reports results but the checker sees none in the file, the two
disagree and the step fails rather than treating the scan as clean.

The action checks that a configured allowlist file exists before scanning.

## Usage

```yaml
- uses: cboone/gh-actions/actions/run-trufflehog@v5.0.0
```

Each argument goes on its own line, so an argument may contain spaces:

```yaml
- uses: cboone/gh-actions/actions/run-trufflehog@v5.0.0
  with:
    args: |-
      filesystem
      --directory
      .
```

Scanning full history with an allowlist:

```yaml
- uses: cboone/gh-actions/actions/run-trufflehog@v5.0.0
  with:
    args: |-
      git
      file://.
    allowlist: .github/trufflehog-allowlist.json
```
