# GitHub Copilot Instructions for Gh Actions

For full project conventions, see AGENTS.md in the repository root.

## PR Review

- **Done plans are historical records**: Files in `docs/plans/done/` are completed plan documents preserved for reference. They may not match the final implementation. Do not flag discrepancies between done plan content and the actual codebase.
- **Reusable workflows are intentionally self-contained**: Reusable workflows (`.github/workflows/`) duplicate tool installation logic from composite actions (`actions/`) by design. They are called via `workflow_call` from other repositories that do not have access to the local composite actions. Do not suggest replacing inline install steps with composite action references in reusable workflows.
- **Case statements on uname already guard against unsupported platforms**: Tool installation steps use `case "$(uname -s)"` with an explicit `*) exit 1` fallback. This already rejects unsupported operating systems (including Windows) with a clear error message. Do not suggest adding separate RUNNER_OS guard steps when a case statement with a catch-all exit already exists.
- **`read -r -a` is the intended pattern for parsing `args` inputs**: Actions that accept an `args` input use `read -r -a` to split the string into an array. This is intentional. The inputs accept simple space-delimited CLI flags (e.g., `"detect --source ."`), not quoted or escaped arguments. Do not suggest using `eval` or `eval "set --"` as alternatives, since those introduce command injection risk. Do not flag `read -r -a` as unable to handle quoting/escaping; the limitation is accepted and documented by the simple-token contract of these inputs.
