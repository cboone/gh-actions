# run-trufflehog

Install trufflehog binary and run a scan.

Reported findings fail the action (TruffleHog exit code 183). The scan reports
verified credentials and unknown results caused by verification errors.
Unverified results are excluded to limit noise from invalid credentials, so
revoked credentials and detections without verification are outside this gate.

`--no-update` and `--fail` are always set by this action and stripped from
`args`, so the pinned, checksum-verified binary cannot update itself mid-scan
and findings cannot exit successfully.

When `allowlist` is set, the action also owns the output format: it adds
`--json`, strips `--json` from `args`, and refuses `--json-legacy`, `--sarif`
and `--github-actions`, which would replace the output being matched. Without
an allowlist there is nothing to match, so those flags are left alone.

## Inputs

| Name        | Type   | Default     | Description                                   |
| ----------- | ------ | ----------- | --------------------------------------------- |
| `version`   | string | `3.95.2`    | trufflehog version to install                 |
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

The report names the detector, verification state, commit, path and line of
every finding, and nothing else. Raw, decoded and structured values stay out
of the log: the scan writes them to a private temporary file that the checker
reads and the step deletes, and the checker never reads the fields that carry
them. A findings file that does not parse is reported as such without
reproducing what failed to parse.

If TruffleHog reports results but the checker sees none in the file, the two
disagree and the step fails rather than treating the scan as clean.

Matching needs `jq`, which GitHub-hosted Linux and macOS images provide. The
step checks for it, and for the allowlist file, before scanning, so a missing
requirement fails immediately rather than after the scan.

## Usage

```yaml
- uses: cboone/gh-actions/actions/run-trufflehog@v3.2.0
```

Each argument goes on its own line, so an argument may contain spaces:

```yaml
- uses: cboone/gh-actions/actions/run-trufflehog@v3.2.0
  with:
    args: |-
      filesystem
      --directory
      .
```

Scanning full history with an allowlist:

```yaml
- uses: cboone/gh-actions/actions/run-trufflehog@v3.2.0
  with:
    args: |-
      git
      file://.
    allowlist: .github/trufflehog-allowlist.json
```
