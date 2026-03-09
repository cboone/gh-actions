# Update All Documentation

## Context

The gh-actions repository has a fully implemented set of 7 composite actions and 8 reusable workflows, but the public-facing documentation was never written. The README.md has placeholder TODOs for Installation and Usage, the AGENTS.md is a 5-line stub, and the CHANGELOG.md has no entries. The copilot-instructions.md is well-maintained but could use minor additions.

This plan brings all documentation up to date with the current state of the codebase.

## Files to Update

### 1. AGENTS.md (CLAUDE.md symlinks to this)

**Path:** `/AGENTS.md`

Expand from 5 lines to ~80-100 lines covering:

- **Overview**: Expand to 2-3 sentences (reusable actions + workflows, pinned versions, SHA-256 checksums, 26+ consuming repos)
- **Repository Structure**: Directory tree showing `actions/` (7 actions), `.github/workflows/` (8 reusable + 3 self-hosting), `docs/plans/`, config files
- **Key Conventions**:
  - Composite actions vs. reusable workflows (and why workflows duplicate install logic)
  - `setup-*` (install only) vs. `run-*` (install and run) naming
  - SHA-256 checksum verification pattern (exception: scrut)
  - Tool version pinning (no floating versions; exception: Node.js major version)
  - Platform support (Linux + macOS only; `uname` case statements with catch-all exit)
  - Shell conventions (`read -r -a` for args, env vars for inputs, `RUNNER_TEMP` for installs)
- **Adding a New Action**: Pattern to follow (action.yml structure, OS/arch detection, checksum, GITHUB_PATH)
- **Adding a New Workflow**: Pattern to follow (workflow_call, inputs with defaults, inline tool installation, minimal permissions)
- **Testing**: Self-hosting as integration tests, no unit test framework
- **Local Development**: `make help`, npm scripts for formatting/linting/spelling

### 2. README.md

**Path:** `/README.md`

Rewrite from 16 placeholder lines to comprehensive reference (~400-500 lines):

- **Title and Introduction**: Project description + three design goals (security, simplicity, consistency)
- **Table of Contents**: Links to each major section
- **Composite Actions**: One subsection per action (7 total), each with:
  - One-line description
  - Inputs table (Name, Description, Required, Default)
  - Usage example (`uses: cboone/gh-actions/actions/<name>@v1`)
  - Actions to document: `setup-golangci-lint`, `setup-goreleaser`, `setup-scrut`, `setup-actionlint`, `setup-shfmt`, `run-gitleaks`, `run-trufflehog`
- **Reusable Workflows**: One subsection per workflow (8 total), each with:
  - Description of what the workflow does
  - Permissions required
  - Inputs table (Name, Type, Default, Description)
  - Secrets table (where applicable)
  - Usage example showing `uses: cboone/gh-actions/.github/workflows/<name>@v1`
  - Workflows to document: `go-ci.yml`, `go-release.yml`, `secret-scan.yml`, `text-lint.yml`, `shell-lint.yml`, `github-lint.yml`, `pages-deploy.yml`, `npm-publish.yml`
- **Versioning**: Semantic versioning with floating major tags (`@v1`), what constitutes a breaking change, note that `@main` should be used until v1.0.0 is tagged
- **Quick Start**: Before/after example from the plan doc (25-line workflow to 8-line call)
- **License**: Keep existing text

Input details will be pulled directly from the action.yml and workflow files to ensure accuracy.

### 3. CHANGELOG.md

**Path:** `/CHANGELOG.md`

Populate `[Unreleased]` section with categorized entries based on git history (commits `2eb14da` through `787adfa`):

- **Added**: All 7 composite actions, all 8 reusable workflows, SHA-256 checksum verification, cross-platform support, Codecov coverage upload, gofmt/goimports format checking, scrut CLI test support, self-hosting workflows, linter and formatter configuration, copilot instructions
- Keep entries concise (one line each)

### 4. .github/copilot-instructions.md

**Path:** `/.github/copilot-instructions.md`

Add two new instructions after the existing five:

1. Versioning convention: semantic versioning with floating major tags, do not suggest changes
2. README as single source of truth: do not suggest per-action README files

## Implementation Order

1. AGENTS.md (foundation; copilot-instructions.md references it)
2. README.md (largest file; the main deliverable)
3. CHANGELOG.md (independent; git history analysis)
4. .github/copilot-instructions.md (smallest change; last)

## Commit Strategy

One commit per file, each passing linters:

1. `docs: expand AGENTS.md with repo conventions and contribution guidance`
2. `docs: rewrite README.md with action and workflow reference`
3. `docs: populate CHANGELOG.md with initial feature entries`
4. `docs: add versioning and README instructions to copilot-instructions.md`

## Verification

After each file is written:

1. Run `npx markdownlint-cli2 <file>` to check markdown lint (except CHANGELOG.md, which is in the ignore list)
2. Run `npx prettier --check <file>` to verify formatting
3. Run `npx cspell <file>` to check spelling
4. Visually confirm that input tables, code blocks, and cross-references render correctly

## Key Sources for Content

- Action definitions: `actions/*/action.yml` (7 files) for exact inputs, defaults, and version numbers
- Workflow definitions: `.github/workflows/*.yml` (8 reusable) for exact inputs, secrets, permissions, and defaults
- Design rationale: `docs/plans/todo/2026-03-07-reusable-actions-and-workflows.md`
- Git history: `git log --oneline` for CHANGELOG entries
