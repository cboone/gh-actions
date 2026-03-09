# GitHub Copilot Instructions for Gh Actions

For full project conventions, see AGENTS.md in the repository root.

## PR Review

- **Done plans are historical records**: Files in `docs/plans/done/` are completed plan documents preserved for reference. They may not match the final implementation. Do not flag discrepancies between done plan content and the actual codebase.
- **Reusable workflows are intentionally self-contained**: Reusable workflows (`.github/workflows/`) duplicate tool installation logic from composite actions (`actions/`) by design. They are called via `workflow_call` from other repositories that do not have access to the local composite actions. Do not suggest replacing inline install steps with composite action references in reusable workflows.
- **Case statements on uname already guard against unsupported platforms**: Tool installation steps use `case "$(uname -s)"` with an explicit `*) exit 1` fallback. This already rejects unsupported operating systems (including Windows) with a clear error message. Do not suggest adding separate RUNNER_OS guard steps when a case statement with a catch-all exit already exists.
- **Newline-delimited `args` inputs**: Actions that accept an `args` input use newline-delimited values parsed with a `while IFS= read -r` loop into a bash array. Each argument goes on its own line, which allows arguments containing spaces. Do not suggest reverting to `read -r -a` (which splits on whitespace and breaks arguments with spaces) or using `eval` (which introduces command injection risk).
- **scrut upstream does not publish checksums**: The scrut tool installation intentionally lacks checksum verification because scrut upstream does not publish checksum or signature files. This limitation is already documented in inline comments. Do not suggest adding integrity verification, provenance checks, or alternative install methods (such as `go install`) for scrut. Scrut is a Rust project and cannot be installed via `go install`.
