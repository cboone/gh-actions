# run-lean-ci

Run Lean test, lint, and build steps on a Lake project via
`leanprover/lean-action`. Each step is gated on a `run-*` input so
callers can disable individual checks.

Unlike `run-go-ci.yml`, `run-rust-ci.yml`, and `run-zig-ci.yml`, this
workflow runs a single job with conditional steps rather than one job
per check. Lean projects with a Mathlib dependency download a large
toolchain and Mathlib cache during setup; splitting build, lint, and
test into separate jobs would multiply that setup cost on every run.
`leanprover/lean-action` handles `elan` install, the Mathlib build
cache, and `lake build`. After it returns, this workflow runs
`lake lint` and `lake test` directly so the consumer's own Lake `lint`
and `test` targets are exercised (lean-action's built-in `lint` step
runs `lake exe runLinter` from Batteries instead, which is not always
what callers want).

**Permissions:** `contents: read`

## Inputs

| Name                | Type    | Default         | Description                                                           |
| ------------------- | ------- | --------------- | --------------------------------------------------------------------- |
| `runs-on`           | string  | `ubuntu-latest` | Runner label (Windows is not supported)                               |
| `run-build`         | boolean | `true`          | Run `lake build` via `leanprover/lean-action`                         |
| `run-lint`          | boolean | `true`          | Run `lake lint` after the build                                       |
| `run-test`          | boolean | `true`          | Run `lake test` after the build                                       |
| `use-mathlib-cache` | string  | `auto`          | Mathlib cache control passed to lean-action (`auto`, `true`, `false`) |
| `timeout-minutes`   | number  | `30`            | Job timeout in minutes                                                |

## Usage

Default usage (build, lint, and test, with auto-detected Mathlib cache):

```yaml
jobs:
  lean:
    uses: cboone/gh-actions/.github/workflows/run-lean-ci.yml@v3.0.0
```

For a project without a `testDriver` (no `lake test` target):

```yaml
jobs:
  lean:
    uses: cboone/gh-actions/.github/workflows/run-lean-ci.yml@v3.0.0
    with:
      run-test: false
```

For a project that does not depend on Mathlib:

```yaml
jobs:
  lean:
    uses: cboone/gh-actions/.github/workflows/run-lean-ci.yml@v3.0.0
    with:
      use-mathlib-cache: "false"
```
