# run-trufflehog

Install trufflehog binary and run a scan.

Reported findings fail the action (TruffleHog exit code 183). The scan reports
verified credentials and unknown results caused by verification errors.
Unverified results are excluded to limit noise from invalid credentials, so
revoked credentials and detections without verification are outside this gate.

## Inputs

| Name      | Type   | Default     | Description                                   |
| --------- | ------ | ----------- | --------------------------------------------- |
| `version` | string | `3.95.2`    | trufflehog version to install                 |
| `args`    | string | (see below) | Arguments to pass to trufflehog, one per line |

Default `args`:

```text
filesystem
--directory
.
```

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
