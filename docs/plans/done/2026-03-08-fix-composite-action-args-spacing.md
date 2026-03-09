# Fix composite action args input for arguments with spaces

Addresses [issue #5](https://github.com/cboone/gh-actions/issues/5).

## Context

The `args` input in `actions/run-gitleaks` and `actions/run-trufflehog` uses `read -r -a` to split the input string into an array. This splits on whitespace (IFS), making it impossible to pass arguments containing spaces (e.g., `--config "path with spaces/config.toml"`). The issue was identified during Copilot PR review on PR #4.

Neither composite action is currently referenced by any workflow in this repo (the `secret-scan.yml` workflow has its own inline code), so this change has zero migration cost.

## Approach

Switch from whitespace-delimited to **newline-delimited** argument parsing. Each argument goes on its own line, allowing spaces within individual arguments.

Use a `while IFS= read -r` loop instead of `mapfile` for bash 3.2+ compatibility (macOS runners).

## Files to modify

### 1. `actions/run-gitleaks/action.yml`

**Input definition** (lines 9-12): Update description and change default to multiline `|-` block:

```yaml
  args:
    description: >-
      Arguments to pass to gitleaks, one per line.
    required: false
    default: |-
      detect
      --source
      .
```

**Run step** (lines 73-74): Replace `read -r -a` with while-read loop:

```bash
args=()
while IFS= read -r line; do
  [[ -n "${line}" ]] && args+=("${line}")
done <<< "${GITLEAKS_ARGS}"
gitleaks "${args[@]}" --verbose
```

### 2. `actions/run-trufflehog/action.yml`

Same two changes, adapted for trufflehog:

**Input definition** (lines 9-12):

```yaml
  args:
    description: >-
      Arguments to pass to trufflehog, one per line.
    required: false
    default: |-
      filesystem
      --directory
      .
```

**Run step** (lines 73-74):

```bash
args=()
while IFS= read -r line; do
  [[ -n "${line}" ]] && args+=("${line}")
done <<< "${TRUFFLEHOG_ARGS}"
trufflehog "${args[@]}" --results=verified,unknown
```

### 3. `.github/copilot-instructions.md`

Replace line 10 (the `read -r -a` instruction) with guidance for the new pattern:

```markdown
- **Newline-delimited `args` inputs**: Actions that accept an `args` input use newline-delimited values parsed with a `while IFS= read -r` loop. Each argument goes on its own line, which allows arguments containing spaces. Do not suggest reverting to `read -r -a` (which splits on whitespace and breaks arguments with spaces) or using `eval` (which introduces command injection risk).
```

## Verification

1. Confirm the default values parse correctly: the `|-` block scalar for `detect\n--source\n.` should produce exactly three array elements
2. Confirm arguments with spaces work: an arg like `path with spaces/config.toml` stays as a single array element
3. Confirm empty lines are filtered: trailing newlines from `|` YAML blocks and blank lines do not produce empty arguments
4. Run the `write-shell-scripts` and `lint-and-fix` skills against the modified shell blocks
