# Gitleaks trusted-base review ledger

Reviewed structural tree: `b3410d9ec0361da39a49dbe9ff2bf1c407c86ea0`.

## Structural loop

Nit round: anti-patterns reported 0 findings; report-only simplify reported 1.

Both ran in fresh read-only `codex exec` contexts, stdin closed, model `gpt-6.1-sol`, effort `high`, window `872000`. All scoped files were read. The simplify cleanup angles ran inline in its reviewer; no editing pass ran. Types are unchanged. The repository metadata was checked by the worker before review; reviewer network lookups were unavailable.

Evidence: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/structural-gate/receipt.json`. Raw reports and the matching before/after scope live under `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/structural-1`.

- Reviewer label: `suggestion`. Our severity: Nit. Select the filename assertion through an explicit expectation. Take: replace diagnostic-dependent filename assertion selection with an explicit `expectSecret` flag. Review again: no, this changes test assertions only.

Structural end state: ended: fixes changed no behavior. The anti-pattern result itself is clean at Nit by inspection. No Important or Critical finding was downgraded.

## Plants and validation

An initial plant attempt failed during repeated dependency-link setup; its gate refused the success post. The setup now verifies an existing link instead of creating a nested link. Failed evidence is retained under `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/plants-gate-1`. Replacement evidence is pending. Final local checks and CI are pending.

## Helper snapshots

| Bundle                 | Source version | Manifest SHA-256                                                   |
| ---------------------- | -------------- | ------------------------------------------------------------------ |
| `lint-and-fix`         | `1.5.1`        | `2aca67206ce6661b5d20ef55d37f1910300572e1f46683946301ef3c4cc64ae4` |
| `plant-defects`        | `1.2.1`        | `8a7b0881450f4663db8e07e9fb4b9890db56afcfb5df3575f683a8ccd85f5e2e` |
| `review-anti-patterns` | `1.2.1`        | `a7fa1183042bb6ac53a0ffbc604908c90922f0a517df122753ec3285bb629f9b` |
| `review-pr-with-codex` | `2.3.5`        | `a2e6ab3a740adf224f7f1b0c9a015e5e679137d6a74caf5a1b17c31e359ba441` |
| `trim-comments`        | `3.0.1`        | `1237657eb5d3c5535bc6695f39dc97a51e2876a248079500d0a3616ede11c7d8` |
| `trim-text`            | `1.3.1`        | `07248706d03ea056ca83d554ba16791b6b807c7e9ad3c626e93b345e64e45d68` |

Copies are unchanged snapshots under `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/helpers`; regular-file SHA-256, membership, ownership and modes are verified before invocation.

## Focused review: design stop

Nit round used code, errors, tests and comments in fresh read-only Codex contexts, stdin closed, `gpt-6.1-sol`, `high`, window `872000`. Types were omitted because the change introduces no type design. Every selected aspect completed and its schema and snapshot were validated through the checked post below.

Receipt: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/design-stop-gate/receipt.json`. Raw reports: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/focused-review-1/out`. The same gate reproduces the path-rule regression with the installed gitleaks binary, comparing repository-relative and absolute source paths.

### code

Reported findings: 1.

- **code-review: Absolute source paths silently disable working-tree path rules.**
  - Reviewer label: `critical`. Our severity: Critical.
  - Evidence: For working-tree scans, gitleaks matches rule paths against the paths emitted from --source without removing an absolute prefix. Changing from '.' to source_dir therefore disables existing repository-relative rules such as path = '^src/'. Secrets covered by those rules can now pass undetected on PR and push events. Confirmed with gitleaks 8.30.1 against an existing fixture: a path-scoped rule exited 1 with '.', but exited 0 with the absolute source path. Anchored allowlist paths also stop matching.
  - Take or record: Take, pending the conductor design decision. The reachable working-tree path can silently miss configured credential detections.
  - Review again: Yes, after the production fix, continue at Important round without resetting the Nit round.

### errors

Reported findings: 0.

### tests

Reported findings: 2.

- **The full-history fixtures cannot detect a regression to working-tree scanning.**
  - Reviewer label: `important`. Our severity: Important.
  - Evidence: Rating: 7/10. Every detection fixture leaves the synthetic secret at HEAD, including the full-history cases. Adding --no-git unconditionally would therefore preserve every expected result while silently missing secrets committed and subsequently removed. The existing self-hosted scan provides no positive control for this distinction.
  - Take or record: Take: add a secret removed before HEAD, distinguishing full-history from working-tree scans.
  - Review again: Test-only changes alone do not advance the loop; the production fix will require another round.

- **Config path validation lacks symlink boundary coverage.**
  - Reviewer label: `suggestion`. Our severity: Nit.
  - Evidence: Rating: 6/10. The path-rejection cases cover literal traversal but no symlinks, and the fixture creates only regular files. Replacing canonical resolution with lexical normalization could still pass these tests while allowing a base config symlink to resolve into the proposed checkout and load its widened allowlist. The dangling default-config branch is also uncovered.
  - Take or record: Take: add external, internal and dangling config symlink boundaries.
  - Review again: No separate round for tests alone; include in the production-fix review.

### comments

Reported findings: 0.

The focused loop is stopped at its design gate with findings unresolved. It has no clean end state. No reviewer label was downgraded. No push or PR has occurred. Trims, Semgrep baseline, final lint, tidy, final receipts and CI remain unrun.

The conductor is asked to choose the structural fix. The proposed direction is to restore `--source .` from the proposed checkout while resolving config extensions to trusted base files before invocation. This requires a reviewed design for config preparation; no such helper has been implemented.

## Approved design revision

TOOLING answered the design question on start gate record `881db69b`, opening the
restart gate. Gitleaks now runs from the proposed checkout with `--source .`.
The base config and extensions are serialized to trusted temporary files; the
helper and uv action come from `job.workflow_repository` at `job.workflow_sha`.
No package dependency was added.

The base supplies `.gitleaksignore`, or an empty file. Pinned gitleaks 8.30.1 also
loads the source ignore file despite an explicit ignore flag. The workflow saves
that source file outside the checkout during scanning and restores it on exit;
working-tree mode scans its contents separately with trusted rules.

The anchored-rule, anchored-allowlist, history-only and symlink cases are now
implemented, together with actual PR ignore fingerprints and restoration checks.
Validation of this revision is pending its checked post. The next focused round
is Important; the Nit round remains used. No push or PR has occurred.

## Focused Important round

Code, errors, tests and comments completed in fresh read-only Codex contexts with the same explicit model, effort and window. Scope comparison found no lasting changes during review. Evidence: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/important-1-gate/receipt.json`.

- **code-review: Explicit tool installation is missing for uv in the regression job.** Reviewer label: `important`. Our severity: Important.
  - Evidence: The fixture executes the workflow's `uv run` command, but this job installs only Node and gitleaks. On a runner without uv, the first PR fixture fails with exit 127; an image-provided uv also bypasses the reviewed version. AGENTS.md requires: "Install required tools explicitly unless their runner-provided use is documented in the development reference." No runner-provided uv exception is documented.
  - Take or record: take. Install pinned uv explicitly in the fixture CI job.
  - Review again: production and CI edits require the next Important round; tests/docs alone do not.

- **code-review: Actionable errors are lost during config preparation.** Reviewer label: `important`. Our severity: Important.
  - Evidence: The handler discards every exception's cause and file context. Malformed TOML in an extended rules file, a missing extension, and an ENOSPC failure writing prepared files all produce the same config-validity message. The scan correctly fails, but users cannot identify the failing file or distinguish configuration problems from runner failures.
  - Take or record: take. Preserve sanitized operation, filename and cause diagnostics; distinguish validation from I/O failures.
  - Review again: production and CI edits require the next Important round; tests/docs alone do not.

- **Escaped custom regexes lack a preservation regression test.** Reviewer label: `suggestion`. Our severity: Nit.
  - Evidence: Rating: 6/10. The new preparer parses and reserializes every PR configuration, but the custom-rule fixtures use only the regex "token". Incorrectly escaping backslashes could therefore pass these tests while silently disabling a consumer rule containing \b or \s. The repository's self-scan has no positive control proving such a rule still detects its intended input.
  - Take or record: take. Add an escaped custom-regex preservation case and a serialization plant.
  - Review again: production and CI edits require the next Important round; tests/docs alone do not.

- **write-markdown: Document the new GitHub Enterprise Server restriction.** Reviewer label: `important`. Our severity: Important.
  - Evidence: The new pull-request path always fetches helpers using job.workflow_repository and job.workflow_sha. This document already states that GitHub Enterprise Server does not populate those contexts, but limits that warning to trufflehog-allowlist. A GHES caller using gitleaks now cannot reliably fetch the workflow-owned helpers, even with both allowlist inputs unset; the new documentation omits this compatibility restriction.
  - Take or record: take. Document the GitHub Enterprise Server restriction; also fail closed before helper checkout when workflow context is unavailable.
  - Review again: production and CI edits require the next Important round; tests/docs alone do not.

The initial Critical path-rule finding and its test-coverage takes are addressed by the source-relative design and new controls. Important round is not clean; fixes follow, then the second Important round. No label was downgraded. The compatibility finding also exposed a worker-identified Critical boundary: missing workflow context must not let checkout fall back to the caller repository/ref and execute proposed helper code. Add a failing-context guard before that checkout and test it. This is a local fail-closed fix within the approved design.

### Generated plant evidence

<!-- checked-plants:start -->

## Verified plants and controls

plant pr-config-discovery: named assertion reached; red exit 1; restored; green exit 0.

plant explicit-config-from-head: named assertion reached; red exit 1; restored; green exit 0.

plant extensions-from-head: named assertion reached; red exit 1; restored; green exit 0.

plant ignore-trusted-config: named assertion reached; red exit 1; restored; green exit 0.

plant weaken-exit-assertion: named assertion reached; red exit 1; restored; green exit 0.

plant weaken-diagnostic-assertion: named assertion reached; red exit 1; restored; green exit 0.

plant anchored-path: named assertion reached; red exit 1; restored; green exit 0.

plant history-scope: named assertion reached; red exit 1; restored; green exit 0.

plant config-symlink: named assertion reached; red exit 1; restored; green exit 0.

plant dangling-config: named assertion reached; red exit 1; restored; green exit 0.

plant source-ignore: named assertion reached; red exit 1; restored; green exit 0.

plant trusted-ignore: named assertion reached; red exit 1; restored; green exit 0.

plant restore-ignore: named assertion reached; red exit 1; restored; green exit 0.

control comment-control: green control verified; control exit 0; restored; green exit 0.

Evidence: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/plants-run-3/results.json`.

<!-- checked-plants:end -->

Plant gate: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/plants-gate-3/receipt.json`. This is evidence for its recorded tree; final-tree receipts remain required.

## Focused review completion

The second Important round completed with code, errors, tests and comments in fresh read-only Codex contexts (`gpt-6.1-sol`, `high`, window `872000`).

- `code`: 0 findings in the validated report.
- `errors`: 0 findings in the validated report.
- `tests`: 0 findings in the validated report.
- `comments`: 0 findings in the validated report.

Focused end state: clean at Important. Round sequence: Nit, Important, Important. The Critical path-rule finding, worker-identified missing-context boundary, Important history coverage, CI uv dependency, diagnostic and GHES documentation findings, and Nit symlink/regex tests are addressed. No severity was downgraded and no recurring defect stopped the loop.

Evidence: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/important-2-gate/receipt.json`. Reports and matching scopes: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/focused-review-3`.

The latest plant attempt was refused because the newly added escaped-regex case also uses an anchored path and intercepted the anchored-path plant before its named marker. The runner correctly refused publication; retained failure receipt: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/plants-gate-4/receipt.json`. Move that test after the dedicated anchored-path controls, then rerun the complete plant group. Trims, Semgrep, final lint, tidy, final-tree receipts and CI remain ahead.

## Trims and baseline security scan

Comment trim proposed no edits. Prose trim proposed 2 rewrites; both were applied while preserving meaning. Both ran once in fresh read-only Codex contexts with `gpt-6.1-sol`, effort `low`, window `872000`. No proposals were declined. Raw replies are under `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/trims`. Plant scripts contain only protected shebang/directive comments; patch and serialized evidence stayed unchanged.

Baseline Semgrep scanned a disposable shared clone of the committed branch, with `SEMGREP_REPO_NAME=cboone/gh-actions`, `--config p/ci` and `--baseline-commit` set to the actual origin/main merge base. Results: 0 findings; 0 errors. JSON: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/semgrep.json`. Receipt: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/semgrep-gate/receipt.json`.

The final lint step and exact-tree tidy remain. Final-tree receipts and CI status are recorded in the external handoff registry, rather than duplicated as stale totals here.

## Final lint step

`lint-and-fix --no-push` completed through the checked post below. The cspell dictionary was extended for API names and status terms in the branch records and fixtures. No production behavior changed. Markdownlint and Prettier ran check-only because the project prohibits rewriting Scrut snapshots; their broad fix commands were not run. Actionlint, yamllint, cspell and shellcheck have no applicable auto-fix mode; shfmt ran with `-d`. No required local lint was skipped. Workflow installation matrices and scheduled version audits remain CI-only.

Repository commands: `make lint`, `make lint-yaml`, `make lint-md`, `make format-check`, `make spell`, plus shellcheck and shfmt over tracked shell scripts. Existing actionlint and the matching hash-pinned yamllint environment were reused; nothing was installed. Receipt: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/lint-gate-2/receipt.json`.

The implementation is complete. The plan moves to `docs/plans/done/` before exact-tree signed tidy. The final external registry records head-bound suite, lint, plant and Semgrep receipts after all repository edits; it is the authority for PR readiness and CI.

## Critical serializer correction

A worker compatibility probe found a distinct Critical defect after the first
final gate: Python key lowercasing changes a valid Unicode spelling of
`condition` into a key gitleaks does not recognize. The trusted AND condition
then becomes the default OR condition and permits the marker. Reviewer label:
not applicable, worker finding. Severity: Critical. Take: preserve original key
names and only locate extension/path keys case-insensitively. Review again:
Critical-only, continuing the prior round count. This is a different mechanism
from the earlier absolute-path defect, not a recurrence of that mechanism.

The production preparer reproduced the native-versus-prepared difference in
`/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/unicode-blocker-gate/receipt.json`.
Publication was held and the old readiness registry marked blocked. The helper
now checks collisions without rewriting names. A real-gitleaks Unicode condition
case and a key-normalization plant cover this boundary. No dependency or public
input was added. A fresh final gate is required after the correction.

## Critical review completion

The continuing Critical round completed with code, errors, tests and comments in fresh read-only Codex contexts (`gpt-6.1-sol`, `high`, window `872000`).

- `code`: 0 findings in the validated report.
- `errors`: 0 findings in the validated report.
- `tests`: 0 findings in the validated report.
- `comments`: 0 findings in the validated report.

Focused end state: clean at Critical. Sequence: Nit, Important, Important, Critical. Original key spellings now survive preparation, and the real-gitleaks Unicode condition regression verifies the correction. No label was downgraded. The new serialization mechanism was distinct from the earlier source-path issue.

Receipt: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/critical-gate/receipt.json`. Raw reports: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/focused-review-4/out`. The previous final receipt applies only to its recorded tree and is superseded for readiness by the replacement final gate.

## Corrected tree validation

The targeted trim after the Critical correction proposed no changes. It ran read-only with `gpt-6.1-sol`, effort `low`, window `872000`, restricted to new comment/prose units. Reply: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/trims-correction/reply.md`.

The corrected committed tree was scanned against its actual origin/main merge base in the disposable shared clone: 0 Semgrep findings and 0 errors. The complete lint-and-fix check set then ran without skipped local lint. Receipt: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-157/evidence/correction-gate/receipt.json`.

The unpublished branch is rebuilt as logical signed commits with an exact-tree backup at `fix/157-gitleaks-base-config-pre-tidy-corrected`. The replacement final gate is the authority for current-tree suite, lint, Semgrep, plant, signature and ancestry claims; earlier receipts retain only their stated scope.
