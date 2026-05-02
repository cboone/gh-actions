# run-gitleaks

Install gitleaks binary and run a scan.

## Inputs

| Name      | Type   | Default             | Description                   |
| --------- | ------ | ------------------- | ----------------------------- |
| `version` | string | `8.30.1`            | gitleaks version to install   |
| `args`    | string | `detect --source .` | Arguments to pass to gitleaks |

## Usage

```yaml
- uses: cboone/gh-actions/actions/run-gitleaks@v3.0.0
```
