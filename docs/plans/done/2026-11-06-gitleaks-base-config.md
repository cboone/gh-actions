# Trusted base configuration for gitleaks

## Goal and scope

Close [the gitleaks configuration trust issue](https://github.com/cboone/gh-actions/issues/157).
On pull requests, scan the proposed tree with the base revision's configuration,
including an explicit `allowlist-config`, or with the built-in default rules.
Other events retain checkout-based configuration. No caller changes or releases.

## Design

Extend `scan-for-secrets.yml` and its existing self-test workflow. Keep scan and
base checkouts separate, pin the latter to the event's immutable base SHA, and
disable persisted credentials on both. Prepare base configs and extensions under
`RUNNER_TEMP`, rewriting extension paths to those trusted copies. Run from the
proposed checkout with `--source .` so anchored path rules retain their meaning.
Always pass an explicit config, generating a default-rules config when
the base has no `.gitleaks.toml`. Explicit config paths must stay within the
base checkout; a missing requested file fails closed.

Use the base's ignore file, or an empty one. Save the proposed ignore file outside
the source during scanning because gitleaks auto-loads it even with an explicit
ignore path; restore it on exit. Scan its contents separately in working-tree mode.

Reuse the existing fixture pattern: execute literal workflow steps with the real
gitleaks binary and temporary Git histories. A
pull-request fixture that widens an allowlist must still expose a synthetic
secret. Cover default discovery, explicit paths, relative extensions, both scan
scopes, clean and allowed controls, invalid inputs and non-PR compatibility.

## Validation and handoff

Commit regression coverage before plants. Run checked plants against config
selection and its assertions. Follow the full security review order: parallel
anti-patterns and report-only simplify, focused aspects, trims, disposable-clone
Semgrep baseline, lint, exact-tree signed tidy, then a ready PR. Preserve review
rounds and checked-gate receipts outside the checkout, with reproducible plant
fixtures committed here. Report stops through the worker mailbox.

Before handoff, fetch `origin/main`, incorporate it if needed and run the full
documented local checks in one strict call on that head. CI must be green before
the conductor merges. The worker stops at its ready PR and receipt handoff.
