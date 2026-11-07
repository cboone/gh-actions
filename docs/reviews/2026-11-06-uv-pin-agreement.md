# uv pin agreement

Scope: compare uv install pins across workflow and action definitions through
the existing workflow argument binding job. No callers or release pins change.

Plan: extend the shared YAML document walk, add the data-driven pin assertion
and its Scrut case, then plant each partial bump and an all-pins control. Run
the full local review order because the reproducible plant fixtures exceed the
small-change limit. Reviews use the immutable base
`74ce8ebe9290a8ac24310432204582c8b4483c14`.

The version audit’s hardcoded uv value is deferred: reading YAML correctly
without adding a parser dependency needs separate audit error handling and
regression coverage. The static agreement check covers the install sources.

Final validation results are retained in external checked-gate receipts.

## Structural review, Nit round

Read-only Codex runs: `gpt-6.1-sol`, high effort, 872000 context.
Anti-pattern output validated with result-check.jq; simplify output validated
with codex-aspects. Both validation commands exited 0 in the recording call.

- Reviewer label: nit. Our severity: Nit. Take: move the
  generator contract comment to the function it describes. Review again: no,
  this changes comments only. Docs drift: the step-key comment now describes the wrong generator.

Simplify findings: 0, from the validated output. Four cleanup
angles ran inline in the read-only reviewer. Structural loop end state:
**ended: fixes changed no behavior**.

Evidence: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-139/evidence/structural/`.

Helper snapshots:

- `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-139/evidence/plants`, source version 1.2.1; manifest
  SHA-256 `8a7b0881450f4663db8e07e9fb4b9890db56afcfb5df3575f683a8ccd85f5e2e`.
- `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-139/evidence/review`, source version 2.3.5; manifest
  SHA-256 `a2e6ab3a740adf224f7f1b0c9a015e5e679137d6a74caf5a1b17c31e359ba441`.
- `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-139/evidence/anti`, source version 1.2.1; manifest
  SHA-256 `a7fa1183042bb6ac53a0ffbc604908c90922f0a517df122753ec3285bb629f9b`.
- `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-139/evidence/trimComments`, source version 3.0.1; manifest
  SHA-256 `1237657eb5d3c5535bc6695f39dc97a51e2876a248079500d0a3616ede11c7d8`.
- `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-139/evidence/trimText`, source version 1.3.1; manifest
  SHA-256 `07248706d03ea056ca83d554ba16791b6b807c7e9ad3c626e93b345e64e45d68`.
- `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-139/evidence/lint`, source version 1.5.1; manifest
  SHA-256 `2aca67206ce6661b5d20ef55d37f1910300572e1f46683946301ef3c4cc64ae4`.

## Focused review, Nit round

Read-only Codex aspects: code, errors, tests and comments, using
`gpt-6.1-sol`, high effort, 872000 context. Types skipped because no typed
interface changes; simplify was covered in structural review. Each output
validated with codex-aspects, and run statuses retain their process exits.

The code, errors, tests and comments reviews each reported 0 findings from their validated JSON.

End state: **clean at Nit**. No further focused round is required.
Evidence: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-139/evidence/focused/`; recording receipt: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-139/evidence/focused-gate/receipt.json`.

## Trims

One read-only trim-comments round and one trim-text round ran on
`gpt-6.1-sol`, low effort, 872000 context. Their non-empty replies classified
the selected files and supplied complete proposals. The proposed generator
comment and prose reductions were taken; no behavior changed. The outputs
are `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-139/evidence/trim-comments.md` and `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-139/evidence/trim-prose.md`.

## Semgrep limitation and acceptance

The `p/ci` baseline scan reports a Pro-engine-only operator in
`javascript.crypto-js.cryptojs-weak-algorithm.cryptojs-weak-algorithm` on the
plant verdict fixture. The scan command and rules remain unchanged. TOOLING
authorized acceptance only when there are no findings and every error names
that exact rule and fixture, with the Pro-engine-only diagnostic. Any other
error, path or finding refuses the gate. A checked plant changes the rule ID
to prove that refusal. The final gate retains the scan and acceptance result.

## Lint and final validation

`lint-and-fix --no-push` used the documented Makefile checks and the
tracked-file shell checks. Fixers were scoped to branch files; Scrut snapshots
were not reformatted. The spelling dictionary now recognizes the scanner
and library identifiers used by the engine-limitation fixture.

- actionlint: exit 0, from the verified lint receipt.
- yamllint: exit 0, from the verified lint receipt.
- markdownlint: exit 0, from the verified lint receipt.
- Prettier: exit 0, from the verified lint receipt.
- cspell: exit 0, from the verified lint receipt.
- shellcheck: exit 0, from the verified lint receipt.
- shfmt: exit 0, from the verified lint receipt.

Receipt: `/Users/ctm/.local/state/codex-mailboxes/tooling/gh-actions-139/evidence/lint-gate-3/receipt.json`.
The final gate reruns the complete local set, both plant manifests and the
baseline scan on the tidied head. Installer matrices remain CI-only.
