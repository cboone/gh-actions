# run-gitleaks

Install gitleaks binary and run a scan.

## Inputs

| Name      | Type   | Default     | Description                                 |
| --------- | ------ | ----------- | ------------------------------------------- |
| `version` | string | `8.30.1`    | gitleaks version to install                 |
| `args`    | string | (see below) | Arguments to pass to gitleaks, one per line |

Default `args`:

```text
detect
--source
.
```

## Usage

```yaml
- uses: cboone/gh-actions/actions/run-gitleaks@v4.1.0
```

Each argument goes on its own line, so an argument may contain spaces:

```yaml
- uses: cboone/gh-actions/actions/run-gitleaks@v4.1.0
  with:
    args: |-
      detect
      --source
      .
```
