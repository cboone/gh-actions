<!-- cspell:ignore semgrep runpy unrun -->

# Shell discovery review ledger

## Evidence

Work: <https://github.com/cboone/gh-actions/issues/144>. Full local review order.
Codex runs use gpt-6.1-sol, high effort, 872000 tokens, read-only sandbox and
closed stdin. Prompts are complete, nonempty and SHA-256 recorded before launch.
Reviewers receive a committed head, held unchanged until all runs exit.

Owned helper manifests, outside the checkout:

- `plant-defects` 1.2.1: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-144/worker/evidence/plant-defects.json`; SHA-256 `fbb6ec9024abe95f095cd8daef30ac7b8a9dd6159f431a812742855f4237fbce`.
- `review-pr-with-codex` 2.3.5: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-144/worker/evidence/review-pr-with-codex.json`; SHA-256 `86965afb1c15cbe7cf3b42aaf7bd5bad92c409a86b15030bbdaefac9a3e5454a`.
- `review-anti-patterns` 1.2.1: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-144/worker/evidence/review-anti-patterns.json`; SHA-256 `01fde3c778ed9f79eae493882dd937ef106f27c9d5ea31eb2fc631e7f672b0a4`.
- `trim-text` 1.3.1: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-144/worker/evidence/trim-text.json`; SHA-256 `95fe08d3e7ab284aabc7015c53f66e9f2d06198e125829e74eee487c23d7b57a`.

## Structural Nit round

Frozen head: `5f2deedc02839650cc6ee0e3071fc7f3e7f952ce`.
Earlier drifted and empty-prompt attempts were malformed, neither clean nor used
rounds. TOOLING accepted the sequencing correction under `89ba6ee6`; shared
runner changes belong to the separate plugin issue. Process completion was
observed by the worker; that claim is unverified here. The anti-pattern JSON validator and simplify validator each exited 0 in
this strict recording call.
Anti-pattern findings: 0. Simplify findings: 1.
Simplify covered four cleanup angles inline; no independent fan-out ran.

- Reviewer label: suggestion. Express the injected Bash as a multiline literal.
  Our severity: Nit, readability only. Take: raw multiline literal.
  Review again: no behavior change from this cleanup alone.
- Self-observation: preflight recognizes only a literal `trap DEBUG` spelling.
  Our severity: Important, because quoted handlers escape the fixture guard.
  Take: recognize handler-bearing traps and add preflight controls.
  Review again: yes, the validity check changes behavior.

The combined loop continues at Important after these takes. Runtime claims from
reviewers are unverified here; execution evidence is separate.

## Plant attempts

The first plant gate was refused: its direct-write mutant reached a neighboring
success assertion before its intended failure assertion. No credit. The corrected
patch restores both direct-write paths. Final plants must rerun on the final tree;
earlier receipts are not final-head claims.

## Structural Important round and recurrence stop

Frozen head: `d0450dd9ba86bb1a13697b439a6fe79e8bee8383`.
The JSON validators ran as checks of the recording/post gate. Receipt: /Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-144/worker/evidence/recurrence-post-gate/receipt.json.

- Reviewer label: `important`. Sibling input forms: multiline DEBUG handlers still pass preflight
  Our severity: Important; the preflight can accept forbidden instrumentation.
  Take: required, pending the conductor's structural design call.
  Review again: yes, the guard changes behavior.

Important round 1 ended: stopped: recurring defect. The correction below resolves this stop.
The regex cannot cross a newline inside a DEBUG handler. The finding repeats
the previously corrected instrumentation-guard class. Runtime reproduction
remains unverified. TOOLING owns the structural call and restart gate; the
next structural round remains Important round 2. Exact reviewed shell-wrapper
forms and an inventory of embedded Bash are proposed for assessment.

Correctness review, trims, semgrep, lint-and-fix, tidy, final plants and CI are
unrun. No PR exists. The Bash wrappers also need shebangs before lint.

## Structural correction and Important round 2

TOOLING approved exact fixture forms plus a whole-file substring backstop.
The inventory pins both Bash wrappers and the complete Python fixture source,
covering every embedded shell literal. Backstop checks precede hash comparison.
The dedicated preflight plant group covers single-line and multiline handlers,
unlisted edits and the remaining prohibited forms, with an unchanged-inventory
control. Wrapper shebangs were added.

Frozen reviewed head: `592c577f827a1eca18a64d8941eaae6f79c417b4`.
JSON validations and the correction receipt verification gate this record.
Receipt: /Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-144/worker/evidence/structural-close-gate/receipt.json.

Anti-pattern findings: 0. Simplify findings: 1.
Reviewer label: suggestion. Centralize the duplicated empty-result notice.
Our severity: Nit, repeated test wording. Take: a test-only constant and refreshed
fixture digest. Review again: no, expected behavior is unchanged.

Structural loop end: ended: fixes changed no behavior. The anti-pattern portion
is clean at Important. The malformed initial attempts consumed no rounds; the
valid loop used Nit, Important round 1 and Important round 2. Simplify ran each
time, with all cleanup angles inline and no independent fan-out.

The installation/version smoke remains CI-only by TOOLING's call; other local
Scrut specs use the existing executable. No new installation is authorized.

## Correctness Nit round

Frozen head: `5e0499df39afe9b576e41b5d26bb5d5eb627446d`.
Applicable aspects: code, errors, tests and comments. Types skipped because no
type definitions changed. Each output has a process-completion record, prompt
hash and schema validation. Receipt: /Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-144/worker/evidence/correctness-close-gate/receipt.json.

- code: 0 findings.
- errors: 1 findings.
  Reviewer label: `suggestion`. errors: Actionable feedback is missing when an assertion has no message.
  Our severity: Nit. Take: preserve assertion source location while retaining named verdicts.
  Review again: no; these are test and test-diagnostic changes only.
- tests: 1 findings.
  Reviewer label: `suggestion`. Test coverage: Verify partial-output isolation in the per-file fallback.
  Our severity: Nit. Take: add deterministic fallback partial-output coverage and a fallback-specific plant.
  Review again: no; these are test and test-diagnostic changes only.
- comments: 0 findings.

Correctness loop end: ended: fixes changed no behavior. No production code was
changed by the takes. The fixture digest was refreshed for the reviewed test
extension. Validation and final plants remain separate from reviewer claims.

## Trim round

Codex gpt-6.1-sol, low effort, 872000 tokens; read-only, closed stdin.
Frozen head: `f1b2e610edc966ce82d419c0576532efca81513e`.
Receipt: /Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-144/worker/evidence/trims-close-gate/receipt.json.
The completion records, reports and unchanged-code AST comparison gate this
record. The inventory digest was refreshed after comment-only edits.

- comments: 3 proposals; success.
  Took: """Decode the NUL-separated manifest the discovery step wrote.""" → """Decode the discovery step's NUL-separated manifest."""
  Took: """How many tracked paths survived the step's -f/-L filter.""" → """Count tracked paths surviving the step's -f/-L filter."""
  Took: """How many times the step invoked shfmt through the wrapper.""" → """Count the step's shfmt invocations through the wrapper."""
  Retained: docs/reviews/2026-11-06-lint-shell-discovery-plants/check.py:28: Declined shortening '# Loading the fixture imports every dependency without running main.' to '# Import every fixture dependency without running main.' This file is committed audit evidence, which the invocation requires preserving. The following runpy.run_path call uses run_name="preflight", while the fixture calls main only under its **main** guard. This evidence supports the retained explanation; execution remains unrun.
- text: 0 proposals; no-op.

No production behavior changed. Source format, lint and tests are included in
the following local validation; the trim runs did not execute repository checks.

## Baseline scan and lint-and-fix

The initial baseline scan ran in a disposable shared clone against the merge
base, using `SEMGREP_REPO_NAME=cboone/gh-actions`. Its receipt is /Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-144/worker/evidence/semgrep-gate-1/receipt.json. This earlier-tree receipt is not final-head evidence; the final gate scans again.

Lint-and-fix ran with no push, using existing installed tools and lockfile npm
dependencies. Formatters were limited to this branch's files; Scrut snapshots
were never rewritten. The first lint gate stopped at spelling; standalone shell
checks were not reached. It is not a complete lint pass. Its recorded check
exits are [2].

Fixes add local spelling directives for tool identifiers and a shell option
name, and remove an unused template-only error-marker exclusion. Actual assertion,
traceback, syntax and import-error exclusions remain. No production behavior
changed. The complete rerun gates this record and commit. Receipt: /Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-144/worker/evidence/lint-gate-2/receipt.json.

Tidy, current-main integration, final tests, final plants and CI follow. The
final claim registry will reference receipts for the final tree.
