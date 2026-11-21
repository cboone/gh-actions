# run-gitleaks

Install gitleaks binary and run a scan.

The action applies full redaction and logs each finding's fingerprint, file,
line and rule from a private JSON report. The scan step preserves Gitleaks
exit codes, including a caller-supplied `--exit-code`. Scanner errors report
the exit status. The runner must provide `jq`.

## Inputs

| Name      | Type   | Default     | Description                  |
| --------- | ------ | ----------- | ---------------------------- |
| `version` | string | `8.30.1`    | gitleaks version to install  |
| `args`    | string | (see below) | Scan arguments, one per line |

Default `args`:

```text
detect
--source
.
```

## Usage

```yaml
- uses: cboone/gh-actions/actions/run-gitleaks@v5.0.0
```

Each argument goes on its own line, so an argument may contain spaces:

```yaml
- uses: cboone/gh-actions/actions/run-gitleaks@v5.0.0
  with:
    args: |-
      detect
      --source
      .
```

Use scan subcommands such as `detect`, `git`, `dir` or `stdin`. The action
accepts `--redact` and `--redact=100` and rejects other redaction settings.
It reserves `--report-path` (`-r`), `--report-format` (`-f`) and
`--report-template`, including attached values and short option groups.
Use the `gitleaks` binary directly when a separate report or diagnostic
output is needed.
