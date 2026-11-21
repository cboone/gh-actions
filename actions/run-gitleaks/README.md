# run-gitleaks

Install gitleaks binary and run a scan.

The action applies full redaction and logs each finding's fingerprint, file,
line and rule from a private JSON report, including any usable findings written
before a scanner error. The scan step preserves Gitleaks exit codes, including
a caller-supplied `--exit-code`. The runner must provide `jq`.

With `--exit-code 0`, a completed scan can succeed with findings.
Filenames containing the legacy `##[` marker may trigger runner annotations.
Finding metadata can expose a credential used as a filename.

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
- uses: cboone/gh-actions/actions/run-gitleaks@v6.0.0
```

Each argument goes on its own line, so an argument may contain spaces:

```yaml
- uses: cboone/gh-actions/actions/run-gitleaks@v6.0.0
  with:
    args: |-
      detect
      --source
      .
```

Use scan subcommands such as `detect`, `git`, `dir` or `stdin`. The action
accepts `--redact` and `--redact=100` and rejects other redaction settings.
It reserves `--report-path` (`-r`), `--report-format` (`-f`),
`--report-template`, `--diagnostics` and `--diagnostics-dir`, including
attached values and short option groups.
Use the `gitleaks` binary directly when a separate report or diagnostic
output is needed.

The action trusts `args`. Its checks match the spellings listed above, not
every way an option can reach Gitleaks. Report or diagnostic output a caller
enables another way is the caller's to keep out of logs and artifacts.
