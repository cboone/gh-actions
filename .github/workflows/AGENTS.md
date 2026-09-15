# Workflow instructions

Read [the development reference](../../docs/development.md) before editing reusable workflows, pins or release behavior.

- Reusable workflows expose typed `workflow_call` inputs and minimal permissions. Local `./` action references resolve against the caller. Fetch helpers, hash manifests and npm lockfiles from `job.workflow_repository` at `job.workflow_sha`.
- Install required tools explicitly. Keep shellcheck available to actionlint and preserve the self-test that demonstrates shell blocks are actually checked.
- Rust `*-args` inputs use `read -r -a`: simple space-delimited flags, without quoting/escaping support. Preserve this interface instead of adopting composite actions' newline-delimited convention.
- Consumer Rust toolchains come from explicit `rust-version`, or the configured `rust-toolchain-file`; fail if neither yields a value. clap-validator's test pins are fixtures, not defaults to add to the tool-version audit.
- `run-go-ci.yml` consumers must provide enabled `vet`, `test`, `lint`, `build` and `fmt` Make targets. `fmt` checks and fails on unformatted code; it does not write.
- Keep installer self-tests across Linux amd64, Linux arm64 and macOS arm64. cspell's resolution fixture is outside the checkout; the scrut fixture proves uv reaches `PATH`; clap-validator checks installation, cache hits and rejected pins.
- Update `../../docs/workflows/<name>.md` and the root component index together with workflow interfaces. Release notes come from the matching CHANGELOG section; tag CI creates the release.
