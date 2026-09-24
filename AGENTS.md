# Gh Actions

## Overview

Reusable composite actions and workflows for downstream CI/CD. Tool downloads use pinned versions and verified checksums. [README.md](README.md) owns orientation and the component index.

## Critical constraints

- Support Linux and macOS only; installers reject unsupported platforms.
- Composite actions live in `actions/`; reusable workflows in `.github/workflows/` use `workflow_call`.
- A reusable workflow's `./` action path resolves against the caller's checkout. Fetch repository-owned helpers and manifests from `job.workflow_repository` at `job.workflow_sha`. Composite actions use `github.action_path` for sibling files.
- Callers must grant every permission a called workflow declares, including for a job an `if:` will skip, so a mode needing a privileged scope gets its own workflow. `publish-to-npm.yml` and `publish-to-npm-with-oidc.yml` stay separate for that reason; do not merge them behind an auth input.
- Install required tools explicitly unless their runner-provided use is documented in the development reference. In particular, actionlint can pass without examining shell blocks when shellcheck is absent; keep the CI control that plants `SC2086`.
- Ordinary data and argument inputs must reach shell commands through `env:` mappings, with quoted variables and explicit argument arrays. Explicit command inputs such as `scrut-setup-cmd`, `scrut-build-cmd` and `build-command` intentionally execute through `run:`, and are the whole allowlist the `workflow-arg-binding` CI job enforces. The npm workflows choose between `npm ci` and `npm install` inside the step, from `env:`, and their install steps are byte-identical copies that `check-npm-publish.mjs` holds together. Release binaries install under `RUNNER_TEMP` and use `GITHUB_PATH` or an absolute invocation path; other trust paths follow the development reference. The generic installer must remain Bash 3.2 compatible.
- Use imperative names: `set-up-*` installs; `run-*` installs and executes.

## Pinning Policy and Trust Model

Use the strongest supported pin: full SHA plus a version comment for Actions; SHA-256 for binary downloads; reviewed hash manifests for Python; lockfile integrity for npm tools. Never make an upstream registry the sole integrity boundary for CI. Exact devDependency versions and dependent-scoped npm overrides preserve reviewed dependency boundaries.

Every `actions/checkout` sets `persist-credentials: false`, so the job's token does not stay in `.git/config` for later steps to read. The only exception is the Homebrew tap checkout in `release-rust-binaries.yml`, which pushes; `tests/check-checkout-credentials.mjs` enforces the rule.

The full policy, checksum exceptions, consumer-controlled Rust pins, source-pinned clap-validator installation, dictionary integrity rules and automated update coverage live in [the development reference](docs/development.md#pinning-policy-and-trust-model). Read it before changing any dependency or install path. Preserve `dtolnay/rust-toolchain`'s dated default-branch comment because upstream supplies no semver tags.

## Navigation and scoped instructions

Read the scoped file before editing its directory, including from a root session. Preserve every paired `CLAUDE.md -> AGENTS.md` symlink.

- [actions/AGENTS.md](actions/AGENTS.md): composite action interfaces, installer contracts and argument parsing.
- [.github/workflows/AGENTS.md](.github/workflows/AGENTS.md): reusable workflow execution, version sources and self-tests.
- [docs/AGENTS.md](docs/AGENTS.md): component documentation, migrations and release reference.
- [Development reference](docs/development.md): detailed contributor procedures, trust model, adding components, releasing and integration-test coverage.
- `.github/copilot-instructions.md`: intentional review conventions.
- `scripts/check-tool-versions.py`: version audit for tool strings and checksum surfaces that Dependabot does not update.

## Documentation layout

Root README carries orientation and flat Quick Reference tables. Each action owns `actions/<name>/README.md`; each reusable workflow owns `docs/workflows/<name>.md`; breaking releases have `docs/migrations/vN.md`. Create component documentation in the same change and link it from the appropriate README group. Read the [component template](docs/development.md#per-component-doc-template); do not duplicate full reference tables in the root README.

## Merging Pull Requests

Always merge with a merge commit (`gh pr merge --merge`), never squash or rebase, including single-commit and Dependabot PRs. Individual commits preserve each change's rationale and the merge point records what landed together.

## Releasing

Use the `release` skill and [release procedure](docs/development.md#releasing). Releases are Git tags, without GoReleaser. The matching CHANGELOG section must exist before pushing a release tag. Tag-triggered CI creates the GitHub Release; do not create it manually. Breaking changes require a migration guide and README link.

## Local Development

Use the pinned npm dependencies (`npm ci`) and the repository Makefile:

```bash
make help
make lint          # actionlint
make lint-md       # markdownlint
make format        # Prettier writes
make format-check
make spell         # cspell
make lint-yaml     # yamllint
```

`npm run lint:md:fix` fixes Markdown. Run relevant format and lint checks after edits. CI self-tests installers on its supported runner matrix; see [testing](docs/development.md#testing) for controls and fixtures.

Keep this root concise, specialized procedures in the reference, and scoped instructions paired. Verify each global-plus-root-plus-nested instruction chain remains within 32 KiB.

## Code Review Rules

<!-- BEGIN set-up-review-config -->

- Review each changed file against its checklist in `.github/skills/code-review/`; the `SKILL.md` there maps file patterns to checklists.
- Rules under a checklist's Important heading are P1. All other checklist rules are P2 or lower.
- Start each finding with the checklist name and the rule name, for example `write-go-code: Checked errors`.
- Do not report what these CI checks already report: `actionlint`, `shellcheck`, `shfmt`, `markdownlint-cli2`, `prettier`, `cspell`, `yamllint`.
- Do not review these paths: `package-lock.json`, `actions/set-up-scrut/Cargo.lock`, `docs/plans/done/**`, `tests/fixtures/cspell-extra-dict/**`, `.github/skills/code-review/*.md` except `SKILL.md`.
- Claude Code Review takes its severities from `REVIEW.md`.
- Rules outside this block take precedence over it.

<!-- END set-up-review-config -->
