# Local test targets review ledger

## Scope and evidence

Base: `origin/main` at `a8e57a285dcfea4591dcedf29db2d391dff7ee6f`.
Review artifacts: `/tmp/local-target-review.Y12lZx/`; durable copies accompany
the worker mailbox evidence. Existing action pins, runner matrices and installer
integration tests remain unchanged. Direct CI tests now use Makefile targets.

## Structural review

One Nit round: anti-pattern review plus four independent cleanup angles,
`gpt-6.1-sol`, high effort, 872000-token window, standalone read-only contexts.
The anti-pattern run read all 20 original paths with no findings but returned
incomplete after this generated ledger disappeared during discovery. Its result
is retained as incomplete. One supplemental document review covered the ledger
with no findings and verified the generated claims against saved plant evidence.
This was a coverage completion, not a repeated review of the code.

Cleanup-simplification suggested removing three shadowed `SCRUT_BIN` CI
bindings. Our severity: Nit, redundant configuration with no runtime impact.
Take: removed the bindings because the Makefile already provides them. Review
again: no behavior changed. Other cleanup angles returned no findings. Combined
coverage is complete; structural loop ended: fixes changed no behavior.

The cleanup launcher initially refused an unfinished scope file; no reviewer
started from it. A completed scope was supplied, and all four runs validated.
Snapshot comparison found no lasting changes to the original reviewed scope.

## Validation

The existing Scrut documents exercise absolute fixture bindings and executable
selection. The existing Python and Node checks exercise their target dispatch.
Failure propagation for each leaf target is covered by the checked plants below;
`check.sh` also checks aggregate failures and requires evidence of the failed
tool invocation, so a missing target cannot satisfy it. Network checks remain
explicit; GitHub Actions integration tests remain CI-only.

Initial local and network runs are captured in `.local/test.log` and
`.local/network-tests.log`; final tree-bound validation is pending. The first
plant attempt returned setup-error because context-free patches did not apply.
Standard-context patches resolved that setup failure; its failed evidence stays
in the worker mailbox. The success evidence below is renderer-generated.

## Focused review

One Nit round, code/errors/tests/comments, same explicit model settings and
read-only entry point. All four outputs validated; snapshot comparison found
no lasting changes. Types were skipped because no type or schema changed;
editing simplify was not selected. Code, errors and tests returned no findings.

- Reviewer: important, prerequisite completeness. Our severity: Important,
  because following the prerequisite list could fail the default macOS audit
  control. Take: document tar and macOS otool for default tests. Review again:
  documentation only, no runtime behavior changed.
- Reviewer: suggestion, installation side effects. Our severity: Nit, an
  inaccurate blanket claim about target side effects. Take: qualify the claim
  to distinguish existing test tools, lint provisioning and temporary binary
  installation. Review again: documentation only.

The development reference also records runner-provided make, as the tool
installation policy requires. Focused loop ended: fixes changed no behavior.

## Trims and final verification

One comment pass and one prose pass, each standalone read-only Codex,
`gpt-6.1-sol`, low effort, 872000-token window. Both completion checks exited 0.
Applied the Rust coverage comment rewrite and two active-voice prose rewrites.
Declined the two shell-discovery comment rewrites because they remove the
explanation for keeping both real-binary branches. Declined removing the script
filename from its header because the Bash guide requires that header detail.
Generated plant claims, plan authorization evidence and review records stayed
unchanged. No flagged units or cut material.

Final verification uses the lint-and-fix skill without push: Prettier and
Markdown fixes, then actionlint, yamllint, Markdown lint, formatting and spelling
checks. The tracked plant checker also gets Bash syntax, ShellCheck and shfmt
checks. GitHub Actions integrations remain CI-only; no required local tool is
missing. All tools are enforced by repository commands, configs or CI.

The first final gate stopped at a spelling error in this ledger: `make test-all`
exited 2, its spelling command exited 1, and local test prerequisites after
spelling did not run. Checks 2 through 8 exited 0; the commit action was not run.
The failed receipt remains at `worker/final-gate/receipt.json`. The wording was
corrected without changing runtime behavior.

The final checked-gate receipt records the exact tested tree and each exit for
`make test-all`, the plant checker, CI-structure comparison and explicit network
targets. It lives under the worker mailbox at `worker/final-gate-2/`.
The receipt guards a signed lint/documentation commit. After it, exact-tree tidy
rebuilds three logical signed commits while preserving the checked tree; the
mailbox finish report records the tree comparison and receipt verification.
No merge, release, global installation or live configuration change is in scope.

Durable reviewer outputs and logs are in the mailbox's `worker/review-evidence/`.
The structural scope refusal and incomplete review remain recorded separately;
neither is presented as clean. Review counts are one structural Nit round plus
one supplemental ledger review, one focused Nit round and one trim pass per
skill. There were no automatic or confirmation review rounds and no recurrence
or design stops.

<!-- checked-plants:start -->

## Verified plants and controls

plant test-setup-uv: named assertion reached; red exit 1; restored; green exit 0.

plant test-scrut-installation: named assertion reached; red exit 1; restored; green exit 0.

plant test-zig-format-paths: named assertion reached; red exit 1; restored; green exit 0.

plant test-workflow-arg-binding: named assertion reached; red exit 1; restored; green exit 0.

plant test-npm-publish: named assertion reached; red exit 1; restored; green exit 0.

plant test-trufflehog-positive-control: named assertion reached; red exit 1; restored; green exit 0.

plant test-scrut-release-audit: named assertion reached; red exit 1; restored; green exit 0.

plant test-shell-discovery: named assertion reached; red exit 1; restored; green exit 0.

plant test-tool-version-reporting: named assertion reached; red exit 1; restored; green exit 0.

plant test-gitleaks-config-errors: named assertion reached; red exit 1; restored; green exit 0.

plant test-rust-tool-installs: named assertion reached; red exit 1; restored; green exit 0.

plant test-checkout-credentials: named assertion reached; red exit 1; restored; green exit 0.

plant test-gitleaks-base-config: named assertion reached; red exit 1; restored; green exit 0.

plant audit-scrut-releases: named assertion reached; red exit 1; restored; green exit 0.

Evidence: `/Users/ctm/.local/state/codex-mailboxes/tooling/138-local-test-targets/worker/plants-3/results.json`.

<!-- checked-plants:end -->
