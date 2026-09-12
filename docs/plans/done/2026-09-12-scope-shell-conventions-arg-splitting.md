# Scope the Shell Conventions arg-splitting bullet to where each form applies

Addresses [#89](https://github.com/cboone/gh-actions/issues/89).

## Context

`AGENTS.md` has one bullet under `### Shell Conventions` that describes how
`args` inputs are split:

```markdown
- Arguments from `args` inputs are split with `read -r -a` into arrays. This
  handles simple space-delimited flags; quoting and escaping are not supported.
```

It states one repository-wide convention where there are two, and it attaches
the wrong one to the composite actions. Verified against the code:

| Location                                                            | Form                      | Inputs                     |
| ------------------------------------------------------------------- | ------------------------- | -------------------------- |
| `actions/run-cspell`, `run-gitleaks`, `run-trufflehog`, `run-reuse` | `while IFS= read -r line` | `args`                     |
| `.github/workflows/run-rust-ci.yml`                                 | `read -r -a`              | `test-args`, `clippy-args` |
| `.github/workflows/release-rust-binaries.yml`                       | `read -r -a`              | `build-args`               |

The single `read -r -a` under `actions/` is at
`actions/create-gh-release/action.yml:148`. It tokenizes one already-read line
of the `files` input so globs expand per token, nested inside a
`while IFS= read -r line` loop, and carries a comment explaining why. It is a
glob-expansion detail, not the arg-splitting convention.

The consequence is that the bullet's second half, "quoting and escaping are not
supported", is true of `read -r -a` and false of the line-based form. One
argument per line is exactly what lets an argument contain spaces, so the
document tells a reader a supported capability is unsupported, in the half of
the repository where it is supported.

`.github/copilot-instructions.md:21-22` already states both conventions
correctly and separately, so `AGENTS.md` is the sole outlier on the substance.

Two adjacent inaccuracies were found while confirming this and are folded in,
because they are the same defect in the same place a reader would look next:

- `actions/run-gitleaks/README.md:10` and `actions/run-trufflehog/README.md:10`
  render their newline-delimited defaults as single space-separated strings
  (`detect --source .`, `filesystem --directory .`) and omit "one per line"
  from the description. Both `action.yml` files say "one per line", and the
  `run-cspell` and `run-reuse` READMEs already do. A reader copying the
  rendered default passes it as one literal argument.
- `.github/copilot-instructions.md:21` scopes `read -r -a` to "Reusable
  workflows" generally, which is too broad: `release-go-binaries.yml` has a
  `goreleaser-args` input that is not split that way at all.

## Changes

### 1. `AGENTS.md` (lines 211-212)

Replace the single bullet with two scoped bullets:

```markdown
- Composite actions read an `args` input one argument per line, with a
  `while IFS= read -r` loop into a bash array, so an argument may contain
  spaces.
- The Rust reusable workflows split their `*-args` inputs with `read -r -a`
  into a bash array. That handles simple space-delimited flags; quoting and
  escaping are not supported.
```

`release-go-binaries.yml`'s `goreleaser-args` is deliberately left out. It is
neither convention (see follow-up 1 below); documenting a tracked defect inside
a conventions section would entrench it.

### 2. `actions/run-gitleaks/README.md` and `actions/run-trufflehog/README.md`

Fix the `args` row in each Inputs table so the default reads as three discrete
arguments and the description states the splitting rule, matching the wording
already used in `actions/run-reuse/README.md`:

| Name   | Type   | Default                          | Description                                   |
| ------ | ------ | -------------------------------- | --------------------------------------------- |
| `args` | string | `detect`, `--source`, `.`        | Arguments to pass to gitleaks, one per line   |
| `args` | string | `filesystem`, `--directory`, `.` | Arguments to pass to trufflehog, one per line |

Add a `with:` block to each Usage example demonstrating the block-scalar form.
Both READMEs currently show a bare `uses:` with no inputs, so nothing in either
file shows a reader what a correct multi-argument value looks like:

```yaml
- uses: cboone/gh-actions/actions/run-gitleaks@v3.1.1
  with:
    args: |-
      detect
      --source
      .
```

Keep the `@v3.1.1` pin; `.github/copilot-instructions.md` requires usage
examples to name the current released tag.

### 3. `.github/copilot-instructions.md` (line 21)

Narrow the scope from "Reusable workflows" to the two Rust workflows that
actually use the form, and name the inputs as `*-args`. Leave the rest of the
bullet, including its "documented in AGENTS.md" reference, which stays valid
after change 1. Line 22 needs no change.

## Follow-up issues to file

Neither is a documentation change, so both stay out of this PR.

1. **`goreleaser-args` is interpolated inline.**
   `.github/workflows/release-go-binaries.yml:104` runs
   `goreleaser ${{ inputs.goreleaser-args }}`, putting a caller-controlled
   string directly into a `run:` block. It contradicts the next bullet in the
   same `AGENTS.md` section ("Inputs are passed to shell steps via `env:`
   mappings, not inline expressions") and is a shell-injection surface. Fixing
   it means routing the input through `env:` and choosing one of the two
   splitting forms, which changes behavior for callers.

2. **Whether the two forms should converge.** Raised by #89 itself. Moving the
   Rust `*-args` inputs to the line-based form would break any caller passing a
   multi-flag string, so it is major-release material.

## Verification

The change is documentation only; the repository's own linters are the check.

```bash
make format-check   # Prettier, incl. table alignment and the tables above
make lint-md        # markdownlint-cli2
make spell          # cspell
```

Then confirm the claims still hold, which is what #89 was about:

```bash
grep -rn 'read -r -a' actions/ .github/workflows/
```

Every hit must be in `run-rust-ci.yml`, `release-rust-binaries.yml`, or the
annotated glob-expansion block at `actions/create-gh-release/action.yml:148`.
Every `args`-input hit under `actions/` must be `while IFS= read -r line`.

No workflow run is needed: no `.yml` under `.github/workflows/` changes, and
the action `README.md` files are not read at runtime.
