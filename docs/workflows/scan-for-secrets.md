# scan-for-secrets

Run gitleaks, trufflehog, or both to scan for leaked secrets. Supports
full-history and working-tree scan scopes.

TruffleHog findings fail the job. Its scan reports verified credentials and
unknown results caused by verification errors. Unverified results are excluded
to limit noise from invalid credentials, so revoked credentials and detections
without verification are outside the TruffleHog gate.

Without `trufflehog-allowlist`, any reported finding fails the job with
TruffleHog's own exit code 183.

With it set, a scan that completes hands its findings to the checker, whose
exit code the job then takes: `0` when every finding is allowed, `1` when any
finding is not, and `2` for an allowlist or scan output it could not use. A
scan that does not complete never reaches the checker, and the job exits with
TruffleHog's own status instead, so a failed scan is never reported as a clean
one. Only 183, meaning results were found, continues to matching.

Only an indeterminate finding whose commit, path, line and detector all match
an entry is allowed. A verified finding fails even when an entry matches it, as
the rules below set out.

**Permissions:** `contents: read`

## Inputs

| Name                   | Type   | Default        | Description                                              |
| ---------------------- | ------ | -------------- | -------------------------------------------------------- |
| `tool`                 | string | `gitleaks`     | Which tool to run: gitleaks, trufflehog, or both         |
| `scan-scope`           | string | `full-history` | Scan scope: full-history or working-tree                 |
| `gitleaks-version`     | string | `"8.30.1"`     | gitleaks version to install                              |
| `trufflehog-version`   | string | `"3.97.5"`     | trufflehog version to install                            |
| `fetch-depth`          | number | `0`            | Git fetch depth (0 for full history)                     |
| `allowlist-config`     | string | `""`           | Path to a gitleaks allowlist config file. gitleaks only  |
| `trufflehog-allowlist` | string | `""`           | Path to a JSON allowlist of reviewed trufflehog findings |
| `timeout-minutes`      | number | `15`           | Job timeout in minutes                                   |

`allowlist-config` and `trufflehog-allowlist` are separate: the first is a
gitleaks config passed to `gitleaks --config`, the second is this repository's
own allowlist format, described below. Neither affects the other tool.

## Allowlisting a reviewed trufflehog finding

Some credential-shaped strings are deliberate and cannot be removed, such as a
synthetic fixture in a commit that must not be rewritten. `trufflehog-allowlist`
permits those exact findings without excluding the file, suppressing the
detector, or printing the finding.

```yaml
jobs:
  scan:
    uses: cboone/gh-actions/.github/workflows/scan-for-secrets.yml@v5.0.0
    with:
      tool: trufflehog
      trufflehog-allowlist: .github/trufflehog-allowlist.json
```

The file lives in your checkout:

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
`path`, `line` and `detector` must be equal, so changing any of them, or moving
the fixture, fails the scan again. Every field is required, including `reason`,
which records why the finding was accepted. `commit` must be a full
40-character lowercase SHA, because a short SHA or a ref can come to mean
something else.

Three rules keep the gate strict:

- **A verified finding is never allowlisted.** If TruffleHog confirms a
  credential is live, the job fails even when its tuple is listed.
- **Entries key on a commit**, so they apply to full-history scans. A
  working-tree finding has no commit and always fails.
- **An unused entry warns rather than fails**, so a stale entry is visible
  without breaking a scan that legitimately no longer reaches it.

The report names the detector, verification state, commit, path and line of
every finding, and nothing else the scan read. An allowed finding also names
the entry that covered it and that entry's `reason`, so the log says why it was
permitted; both come from your own reviewed allowlist file, not from the
scanned content. Raw, decoded and structured values stay out of the log: the
scan writes them to a private temporary file that the checker reads and the
step deletes, and the checker never reads the fields that carry them. A
findings file that does not parse is reported as such without reproducing what
failed to parse.

If TruffleHog reports results but the checker sees none in the file, the two
disagree and the job fails rather than treating the scan as clean.

Matching needs `jq`, which GitHub-hosted Linux and macOS images provide. The
job checks for it, and for the allowlist file, before scanning, so a missing
requirement fails immediately rather than after the scan.

Setting this input makes the job fetch its checker from
`job.workflow_repository` at `job.workflow_sha`, which GitHub Enterprise Server
does not populate. Leave it unset there, or call the
[run-trufflehog](../../actions/run-trufflehog/README.md) action directly, which
reads the checker from its own action path.

## Usage

```yaml
jobs:
  scan:
    uses: cboone/gh-actions/.github/workflows/scan-for-secrets.yml@v5.0.0
    with:
      tool: both
```
