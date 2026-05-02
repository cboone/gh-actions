# run-markscribe

Install markscribe binary and generate a file from a Go template. Replaces
`charmbracelet/readme-scribe` with a direct binary download and SHA-256
checksum verification.

Callers must set `GITHUB_TOKEN` in the step's `env:` for GitHub API access in
templates.

## Inputs

| Name       | Type   | Default         | Description                         |
| ---------- | ------ | --------------- | ----------------------------------- |
| `version`  | string | `0.8.1`         | markscribe version to install       |
| `template` | string | `README.md.tpl` | Path to the Go template file        |
| `write-to` | string | `README.md`     | Output file path (empty for stdout) |

## Usage

```yaml
- uses: cboone/gh-actions/actions/run-markscribe@v3.0.0
  env:
    GITHUB_TOKEN: ${{ secrets.PERSONAL_GITHUB_TOKEN }}
  with:
    template: "templates/README.md.tpl"
    write-to: "README.md"
```
