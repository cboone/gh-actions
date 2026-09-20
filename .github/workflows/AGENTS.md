# Workflow instructions

Read [the development reference](../../docs/development.md) before editing reusable workflows, pins or release behavior.

- Reusable workflows expose typed `workflow_call` inputs and minimal permissions. Local `./` action references resolve against the caller. Fetch repository-owned helpers, hash manifests and default npm lockfiles from `job.workflow_repository` at `job.workflow_sha`. Preserve `lint-text`'s `use-consumer-versions: true` opt-in to the caller's reviewed lockfile.
- Install required tools explicitly unless their runner-provided use is documented in the development reference. Keep shellcheck available to actionlint and preserve the self-test that demonstrates shell blocks are actually checked.
- Argument, flag, path-list and target-list inputs use `env:` plus `read -r -a` into a quoted array: simple space-delimited values, without quoting, escaping, glob or variable expansion, and a multi-line value is rejected rather than truncated to its first line. Preserve this interface instead of adopting composite actions' newline-delimited convention. Only the documented command inputs (`scrut-setup-cmd`, `scrut-build-cmd`, `build-command`) may interpolate into `run:`; the `workflow-arg-binding` job enforces that.
- Consumer Rust toolchains come from explicit `rust-version`, the configured `rust-toolchain-file`, or the legacy `rust-toolchain` fallback; fail if none yields a value. clap-validator's test pins are fixtures, not defaults to add to the tool-version audit.
- `run-go-ci.yml` consumers must provide enabled `vet`, `test`, `lint`, `build` and `fmt` Make targets. `fmt` checks and fails on unformatted code; it does not write.
- Keep installer self-tests across Linux amd64, Linux arm64 and macOS arm64. cspell's resolution fixture is outside the checkout; the scrut fixture proves uv reaches `PATH`; clap-validator checks installation, cache hits and rejected pins.
- Update `../../docs/workflows/<name>.md` and the root component index together with workflow interfaces. Release notes come from the matching CHANGELOG section; tag CI creates the release.
