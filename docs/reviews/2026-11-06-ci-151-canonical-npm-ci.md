# Canonical CI npm installs

Scope: use one locked install command in `run-ci.yml` and enforce its flags
through the existing npm fixture. The reusable workflow parity rule stays intact.

The lockfile's direct development dependencies are cspell, markdownlint-cli2,
prettier and yaml. Inspect both lockfile installation metadata and the installed
package manifests before relying on disabled lifecycle scripts.

Review path: the brief's small-change path, one Codex Nit round, because this
config and test change stays below about 100 lines and changes no authentication,
access, credential handling, input validation or CI permissions. Use the full
order if review finds an Important or Critical defect or the scope expands.

Plant: add a CI job whose install omits `--ignore-scripts`; the `ci-install`
scenario must reject that job at the canonical-flags assertion. Preserve the
existing publish install and lockfile-probe parity assertions.

Evidence and receipts live outside the checkout under the session mailbox's
`evidence/` directory. Final validation uses an argv JSON manifest there, on a
committed head containing current `origin/main`. CI validation follows the PR.
