# GitHub Copilot Instructions for Gh Actions

For full project conventions, see AGENTS.md in the repository root.

## PR Review

- **Done plans are historical records**: Files in `docs/plans/done/` are completed plan documents preserved for reference. They may not match the final implementation. Do not flag discrepancies between done plan content and the actual codebase.
- **Reusable workflows are intentionally self-contained**: Reusable workflows (`.github/workflows/`) duplicate tool installation logic from composite actions (`actions/`) by design. They are called via `workflow_call` from other repositories that do not have access to the local composite actions. Do not suggest replacing inline install steps with composite action references in reusable workflows.
