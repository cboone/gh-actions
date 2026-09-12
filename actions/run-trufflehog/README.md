# run-trufflehog

Install trufflehog binary and run a scan.

## Inputs

| Name      | Type   | Default                          | Description                                   |
| --------- | ------ | -------------------------------- | --------------------------------------------- |
| `version` | string | `3.95.2`                         | trufflehog version to install                 |
| `args`    | string | `filesystem`, `--directory`, `.` | Arguments to pass to trufflehog, one per line |

## Usage

```yaml
- uses: cboone/gh-actions/actions/run-trufflehog@v3.1.1
```

Each argument goes on its own line, so an argument may contain spaces:

```yaml
- uses: cboone/gh-actions/actions/run-trufflehog@v3.1.1
  with:
    args: |-
      filesystem
      --directory
      .
```
