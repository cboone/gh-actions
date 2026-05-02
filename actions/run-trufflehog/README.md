# run-trufflehog

Install trufflehog binary and run a scan.

## Inputs

| Name      | Type   | Default                    | Description                     |
| --------- | ------ | -------------------------- | ------------------------------- |
| `version` | string | `3.95.2`                   | trufflehog version to install   |
| `args`    | string | `filesystem --directory .` | Arguments to pass to trufflehog |

## Usage

```yaml
- uses: cboone/gh-actions/actions/run-trufflehog@v3.0.0
```
