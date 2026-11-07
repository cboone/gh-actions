<!-- cspell:ignore semgrep -->

# Truthful shell discovery

Scope: lint-shell discovery's empty-set report and manifest publication,
closing <https://github.com/cboone/gh-actions/issues/144>.

Extend the existing discovery block and its literal-block fixture. Count all
tracked paths and paths excluded by the worktree filter. Describe an empty
result in terms of regular files present in the worktree. Stage both discovery
branches in RUNNER_TEMP and publish their manifest only after success.

Add sparse-index and partial-output failure cases. Commit reproducible plants
for the measured notice, skipped count and publication boundary, with explicit
assertion verdicts and disposable-copy preflight. Use an owned, hash- and
mode-verified plant-defects helper bundle outside the checkout.

Run the full local review order, with structural review first, correctness
review next and trims after code stops changing. Codex reviews use gpt-6.1-sol,
high effort, an 872000-token window and a read-only sandbox, with stdin closed.
Run baseline semgrep in a disposable shared clone, then lint-and-fix without
pushing. Keep signed logical commits and confirm tidy preserves the tree.

Before handoff, fetch main and include its current head. Run the complete local
check set in one strict gate, publish receipts and a claim registry, open a ready
PR and wait for CI. Report to TOOLING; the conductor owns merging. No tags,
releases, caller edits or installations beyond npm ci.
