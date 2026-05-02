# Improve README and User/Agent-Facing Docs

Date: 2026-05-02

## Goal

Make the repository's user-facing and agent-facing documentation easier to use
without losing any of the substance that exists today. The README has grown to
1026 lines and 43 KB, which is past the point where readers can find what they
need quickly. The other docs (`AGENTS.md`,
`.github/copilot-instructions.md`) are healthier but have related issues
worth addressing in the same pass.

## Diagnosis

### `README.md` (1026 lines, 43 KB)

- Opens with `There are many, these are mine.`, which is charming but does not
  tell a first-time visitor what the repo is, who it is for, or why they
  should pick it over alternatives.
- 27 H3 entries (12 composite actions plus 15 reusable workflows), each with
  full Inputs/Outputs/Usage subsections rendered inline. Reading the README
  end-to-end is the only way to discover what is available.
- Grouped only by composite-action vs. reusable-workflow distinction, which is
  an implementation detail rather than a use-case grouping. A reader looking
  for "Rust CI" or "secret scanning" must scan a long flat list under each.
- Reference and orientation are conflated: every entry tries to be both a
  quickstart and a complete reference table.
- Several headline facts are missing or buried:
  - The trust model and pinning policy (the actual differentiator) lives only
    in `AGENTS.md`.
  - Supported platforms (Linux and macOS, no Windows) lives only in
    `AGENTS.md`.
  - There is no end-to-end example showing several pieces composed into a
    realistic CI workflow.
  - Versioning sits at the bottom of the document even though it is
    prerequisite information for every `uses:` line.
- The Migration section (about 40 lines of tables for the v3 path renames)
  will be stale within one or two releases and crowds out current usage
  content.
- The "26+ downstream repos" framing in `AGENTS.md` does not appear in the
  README and is useful context for new readers.

### `AGENTS.md` (211 lines)

- Solid overall, with a clear structure.
- Repository Structure overlaps in intent with the README's per-component
  listing (different audiences, both useful for now).
- Trust Model and Pinning Policy is the most valuable section in the
  repository's docs and is hidden from README readers.
- Local Development make-target list is not mirrored anywhere user-facing.
- "Adding a New Action" and "Adding a New Workflow" do not mention
  documentation at all, which means doc updates are easy to miss in a PR.

### `.github/copilot-instructions.md` (30 lines)

- Roughly 20 unrelated PR-review anti-patterns in one flat bullet list.
- Hard to scan because every item is a paragraph and there is no grouping.
- Each item is referenced individually by reviewers and Copilot, so the
  paragraphs themselves should not be rewritten, only regrouped.
- The "README.md is the single source of truth for usage documentation"
  rule blocks per-component reference docs. The plan now revises this rule
  rather than working around it (see Constraints and Phase 3 below).

### `CHANGELOG.md` (327 lines)

Standard Keep-a-Changelog format. Chronological by design. Out of scope for
this plan.

## Goals for the rewrite

1. Make the README orient first and reference second, instead of treating
   both as equal.
1. Discovery should scale: a reader should locate a relevant action or
   workflow in well under a minute, even with 27 entries.
1. Surface the security and trust model, the actual differentiator, near the
   top of the README.
1. Demonstrate composition with a worked end-to-end example.
1. Move per-component reference docs next to the code they document, so each
   action lives at `actions/<name>/README.md` and each reusable workflow
   lives at `docs/workflows/<name>.md`. The root `README.md` becomes the
   single source of truth for orientation, quickstart, and the per-component
   Quick Reference, but it stops carrying the full inputs/outputs reference
   for every component.
1. Move evergreen-but-stale-prone content (migration tables) out of the
   README into versioned `docs/migrations/vN.md` files.
1. Tighten `.github/copilot-instructions.md` so it scales as more PR-review
   anti-patterns accumulate.
1. Update repository-level guidance (`AGENTS.md`,
   `.github/copilot-instructions.md`) so the new documentation layout is
   stated as a convention, with explicit doc-creation steps in the
   "Adding a New Action" and "Adding a New Workflow" procedures.

## Constraints

- All existing H3 anchors (e.g., `#run-go-ci`, `#scan-for-secrets`) must
  either remain valid in the root `README.md` or be replaced with a redirect
  pattern that does not break in-bound links from PRs, issues, and
  downstream repos. Approach: keep an H3 stub for each component in the
  Quick Reference section that wraps the existing anchor and links out to
  the per-component file. The anchor still resolves; the user lands on a
  one-line pointer that takes them to the full reference.
- All usage examples continue to pin to the current released tag (currently
  `@v3.0.0`), per the existing `.github/copilot-instructions.md` rule.
- Do not bypass markdownlint, Prettier, cspell, or yamllint checks at any
  step.
- Reusable workflows do not have their own directory under
  `.github/workflows/` (only `.yml` files live there), and GitHub does not
  render `.md` files in `.github/workflows/` as directory docs. Workflow
  reference docs therefore live in `docs/workflows/<name>.md`, parallel to
  `docs/migrations/vN.md`.

## Plan

### Phase 1: Restructure `README.md` in place

Target structure:

```text
# GitHub Actions
[1 paragraph: what it is, who it is for, headline value props]

## Quick reference          (NEW: scannable tables grouped by purpose,
                             each row links to the per-component doc)
## Quick start              (NEW: complete worked example)
## Trust model and pinning  (NEW: condensed from AGENTS.md)
## Supported platforms      (NEW: short, from AGENTS.md)
## Versioning               (MOVED UP: prerequisite info)
## Local development        (NEW: short, for contributors)
## License
```

The "Composite actions" and "Reusable workflows" H2 sections are removed.
Their per-component content moves into per-component files (Phase 1c). The
Migration H2 is removed and relocated under `docs/migrations/v3.md`
(Phase 3).

#### Phase 1a: Quick reference tables

Add a top-of-document section that lists every action and workflow grouped
by purpose, with one-line descriptions and links to each component's
per-component doc file. Proposed groupings:

| Group                     | Members                                                                                                                                                               |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Linting and formatting    | `lint-text`, `lint-shell`, `lint-github-actions`, `run-cspell`, `run-reuse`, `set-up-shfmt`, `set-up-actionlint`, `set-up-golangci-lint`                              |
| Testing and CI            | `run-go-ci`, `run-rust-ci`, `run-zig-ci`, `run-scrut-tests`, `set-up-scrut`                                                                                           |
| Releasing and publishing  | `create-gh-release`, `create-gh-release-from-changelog`, `release-go-binaries`, `release-rust-binaries`, `release-zig-binaries`, `publish-to-npm`, `set-up-goreleaser` |
| Security and supply chain | `scan-for-secrets`, `run-gitleaks`, `run-trufflehog`, `analyze-with-codeql`                                                                                           |
| Repository chores         | `create-pull-request`, `deploy-to-pages`, `run-markscribe`                                                                                                            |

Each group renders as a small table with three columns (Component, Type,
What it does). The Component column links to the per-component doc:
`actions/<name>/README.md` for composite actions and
`docs/workflows/<name>.md` for reusable workflows.

To keep the existing in-page anchors working, each row's Component cell is
also wrapped in an H4 stub (or equivalent invisible anchor) so links like
`README.md#run-go-ci` continue to resolve. The reader lands on the one-line
pointer in the Quick Reference and clicks through.

Edge cases worth confirming with the user:

- `run-markscribe` could go under Releasing (README generation for release
  artifacts) or Repository chores. Proposed: chores.
- `deploy-to-pages` could go under Releasing or chores. Proposed: chores.

#### Phase 1b: Quick start

Add one realistic end-to-end example that composes three or four building
blocks into a typical project setup. Proposed shape:

- A `ci.yml` calling `lint-github-actions`, `lint-text`, `lint-shell`,
  `run-go-ci`, and `scan-for-secrets`.
- A `release.yml` calling `release-go-binaries` on tag push.

Both examples copy-paste-runnable, pinned to the current released tag
(`@v3.0.0`), per the existing rule in `.github/copilot-instructions.md`.

#### Phase 1c: Move per-component reference content into per-component files

For each composite action, create `actions/<name>/README.md`. For each
reusable workflow, create `docs/workflows/<name>.md`. Each per-component doc
contains the content currently inlined in the root README:

- Top-line description (1 to 3 sentences).
- Caveats, if any (e.g., Makefile-targets requirement, pinned-version
  requirement, `GITHUB_TOKEN` requirement, changelog-format requirement).
- `## Inputs` table.
- `## Outputs` table, if applicable.
- `## Secrets` table, if applicable.
- `## Usage` section with one or more examples, pinned to `@v3.0.0`.

Use a consistent template across all 27 files so they look the same; the
template is documented in `AGENTS.md` (Phase 2). After this move, the root
README contains no per-component reference tables; readers reach them via
the Quick Reference table.

Per-component files are an opportunity to add **more usage examples per
component** that did not fit in a unified README (for instance, a
`run-rust-ci` doc can show standard, nextest, and coverage variants
side-by-side without bloating any single page). Adding examples is
optional in this phase; the bar is parity with the current README plus any
context that was previously squeezed out for length.

#### Phase 1d: Trust model and pinning section

Condense the Trust Model and Pinning Policy from `AGENTS.md` into about 150
to 200 words for the README:

- One sentence per pin category: GitHub Actions, `curl` downloads, Python
  via `uv`, npm tools, Rust tooling, `package.json` devDependencies.
- The principle "never let an upstream registry be the sole integrity
  boundary for anything that runs in CI" reproduced verbatim as a short
  callout.
- Link to `.github/workflows/check-tool-versions.yml` for the
  automated-update story (currently absent from the README).
- Link to the full version in `AGENTS.md` for readers who want the long
  form.

The full version stays in `AGENTS.md`; no content is removed.

#### Phase 1e: Other content moves

- Add a 3-line **Supported platforms** section (Linux and macOS only; every
  installer guards via `uname -s` case statement; Windows not supported).
- Add a **Local development** section with the make-target list currently
  only in `AGENTS.md`.
- Reorder so that **Versioning** appears before the per-component reference
  (it is prerequisite information for every `uses:` line).

### Phase 2: Update `AGENTS.md`

#### Phase 2a: Document the new layout

Add a new H2 section, **Documentation layout**, that states the convention:

- The root `README.md` is the canonical source for orientation, quickstart,
  the per-component Quick Reference, the trust model summary, supported
  platforms, versioning policy, and local development.
- Each composite action's full reference (description, caveats, inputs,
  outputs, usage examples) lives in `actions/<name>/README.md`. GitHub
  renders this when a visitor browses into the action's directory.
- Each reusable workflow's full reference lives in
  `docs/workflows/<name>.md`. Reusable workflows do not have their own
  directory; `docs/workflows/` is parallel to `docs/migrations/`.
- Major-version migration guides for path renames live in
  `docs/migrations/vN.md`.
- Each per-component file follows a shared template documented in
  `AGENTS.md` (see below).

Add a per-component doc template:

```markdown
# <name>

<1 to 3 sentence description>

<Caveats, if any>

## Inputs

<table>

## Outputs

<table, if applicable>

## Secrets

<table, if applicable>

## Usage

<one or more usage examples pinned to the current released tag>
```

#### Phase 2b: Update the procedures

Update **Adding a New Action** to add steps:

1. Existing five steps unchanged.
1. Create `actions/<name>/README.md` from the per-component template.
1. Add a row to the Quick Reference table in the root `README.md` under
   the appropriate group, linking to the new per-component file.

Update **Adding a New Workflow** to add steps:

1. Existing four steps unchanged.
1. Create `docs/workflows/<name>.md` from the per-component template.
1. Add a row to the Quick Reference table in the root `README.md` under
   the appropriate group.

Update **Releasing** to point at `docs/migrations/vN.md` as the home for
major-version migration guides.

#### Phase 2c: Cross-references

- Add a one-line note at the top of Trust Model and Pinning Policy reading
  "A condensed summary lives in `README.md`; this is the canonical longer
  form."
- Leave the Repository Structure tree in place; agent context benefits from
  the comprehensive listing even when the README has its own grouping. Add
  the new `docs/workflows/` and `docs/migrations/` paths to the tree.

### Phase 3: Extract migration content and revise the source-of-truth rule

- Create `docs/migrations/v3.md` containing the current README Migration
  section verbatim: the Composite Action Paths and Reusable Workflow Paths
  tables, plus the surrounding paragraphs about not renaming external
  actions and updating branch protection.
- Replace the README Migration section with a one-line pointer:
  `See [docs/migrations/v3.md](docs/migrations/v3.md) for the v3 path
  renames.`
- Establish `docs/migrations/vN.md` as the canonical home for future
  major-version migration guides. Note this in `AGENTS.md` Releasing
  (Phase 2b).
- Revise the existing `.github/copilot-instructions.md` rule
  "README.md is the single source of truth for usage documentation. Do not
  suggest creating per-action or per-workflow README files." with the
  following replacement, which encodes the new layout:

  > **Documentation layout**: The root `README.md` is the canonical source
  > for orientation, quickstart, the per-component Quick Reference, trust
  > model, supported platforms, versioning, and local development. Each
  > composite action's reference docs live at `actions/<name>/README.md`.
  > Each reusable workflow's reference docs live at
  > `docs/workflows/<name>.md`. Major-version migration guides live at
  > `docs/migrations/vN.md`. Do not duplicate per-component reference
  > content in the root `README.md`, and do not move it back. Per-component
  > files follow the template documented in `AGENTS.md`.

### Phase 4: Regroup `.github/copilot-instructions.md`

Reorganize the flat list under H3 subheadings without rewriting any
individual item, so reviewers and Copilot can find related rules together.
Proposed groups:

```text
## PR Review

### Repository structure and documentation
- Single Copilot instructions file
- Documentation layout (REVISED per Phase 3, replaces "single source of
  truth" rule)
- Done plans are historical records
- README usage examples pin to the current released tag

### Reusable workflows and composite actions
- Reusable workflows are intentionally self-contained
- Reusable workflows split args inputs with read -r -a
- Newline-delimited args inputs (composite actions)
- Composite action input defaults support expressions
- Workflow VERSION env vars do not need supported_version guards
- Case statements on uname already guard against unsupported platforms
- Problem matcher regexps target Linux/macOS path formats only

### Tool installation and pinning
- scrut checksums are hardcoded
- shfmt checksums are hardcoded
- cargo-llvm-cov is installed from a binary release with hardcoded
  SHA-256 checksums
- scrut tarball extraction uses --strip-components=1
- test -x is the correct verification for markscribe

### Workflow specifics
- run-go-ci.yml requires Makefile targets
- run-zig-ci.yml uses Zig commands directly, not Makefile targets
- create-gh-release-from-changelog.yml uses gh (pre-installed)
- release-zig-binaries.yml maps Zig target triples to release filenames
- Changelog awk index() includes the closing bracket

### Versioning and dependency hygiene
- Versioning uses semantic versioning with exact version tags
- Dependabot directories: (plural) is supported and intentional
- actionlint path globs support brace expansion
```

Each item stays a one-paragraph bullet so existing PR-comment quotations of
the rules continue to match verbatim, with the single exception of the
"Documentation layout" rule, which is replacing the "single source of
truth" rule and is intentionally rewritten.

## Implementation order

Each phase is its own commit with a `docs:` prefix.

1. **Phase 3** (migration extraction and rule revision). Lowest risk; frees
   roughly 40 lines from the README and lands the rule change before any
   later phase depends on it.
1. **Phase 2a** (Documentation layout section in `AGENTS.md`, including the
   per-component template). Establishes the template before Phase 1c writes
   27 files against it.
1. **Phase 1c** (Move per-component reference content into per-component
   files). 27 new files (12 action READMEs and 15 workflow docs). Largest
   diff but mechanical.
1. **Phase 1a** (Quick reference tables). Now possible because per-component
   files exist to link to.
1. **Phase 1b** (Quick start).
1. **Phase 1d** (Trust model and pinning section in README).
1. **Phase 1e** (Supported platforms, Local development, Versioning
   reorder).
1. **Phase 2b** (Update "Adding a New Action" and "Adding a New Workflow"
   procedures in `AGENTS.md`).
1. **Phase 2c** (`AGENTS.md` cross-references).
1. **Phase 4** (copilot-instructions regrouping).

Phases 1a and 1c are intentionally adjacent: 1c creates the link targets
that 1a depends on. Phase 2a precedes 1c so the template exists before the
27 per-component files are written.

## Verification

After each phase:

- `make lint-md` (markdownlint-cli2) passes against all changed files.
- `make spell` (cspell) passes.
- `make format-check` (Prettier) passes.
- `make lint-yaml` passes if any YAML changed.
- All anchor links inside the README resolve (no broken `#anchor`
  references).
- All cross-doc links resolve (`README.md` to `actions/<name>/README.md`,
  `README.md` to `docs/workflows/<name>.md`,
  `README.md` to `docs/migrations/v3.md`,
  `README.md` to `AGENTS.md`, etc.).

After all phases:

- Root `README.md` line count below ~300 (down from 1026), with savings
  from migration extraction (about 40 lines), per-component reference
  removal (about 700 lines moved out), and the new orientation content
  added back (about 100 lines).
- 12 files exist under `actions/<name>/README.md`, one per composite
  action.
- 15 files exist under `docs/workflows/<name>.md`, one per reusable
  workflow.
- The Quick Reference table lists all 27 components, each linking to its
  per-component file. No orphan files; no missing rows. A simple grep can
  enforce this:

  ```bash
  comm -3 \
    <(ls actions/ | sort) \
    <(grep -oE 'actions/[a-z-]+/README.md' README.md | sed 's|actions/||;s|/README.md||' | sort -u)
  ```

  And the analogous check for `docs/workflows/`. These can run as part of
  CI later if useful.
- Re-read each Quick Reference category and confirm every action and
  workflow appears exactly once and is correctly grouped.
- Cross-check that every per-component file follows the template documented
  in `AGENTS.md`.

## Risks and open questions

1. **Anchor preservation across the move.** External links like
   `README.md#run-go-ci` must continue to resolve. The plan keeps an H3 (or
   H4) anchor stub in the Quick Reference section for each component;
   verify in practice that GitHub's anchor generation matches the original
   slug exactly. Pre-flight on a small sample (e.g., move just `run-cspell`
   first, push, click an existing external link).
1. **27 new files to keep in sync with the Quick Reference table.** A
   simple grep verification (above) catches drift. Optional CI gate later.
1. **Categorization edge cases** for `run-markscribe` and
   `deploy-to-pages`. Confirm placement with the user.
1. **Per-component template consistency.** Initial 27 files should be
   written from a single template (Phase 2a) rather than ad hoc, otherwise
   later edits will normalize style and balloon the diff.
1. **Whether the AGENTS.md Repository Structure listing should eventually
   be trimmed** once the README Quick Reference is the canonical inventory.
   Defer; agent docs benefit from comprehensive in-doc context.
1. **Whether to inline a small "downstream consumers" callout** (the
   "26+ downstream repos" framing) in the README intro, or leave that
   detail in `AGENTS.md`. Proposed: inline a one-line mention in the README
   intro, keep the detail in `AGENTS.md`.

## Out of scope

- Auto-generating Inputs tables from `action.yml` files. Would require a
  generator pipeline; significant new infrastructure. The per-component
  files are still hand-maintained for now.
- `CHANGELOG.md`. Chronological by design; not a usability problem.
- Adding badges, screenshots, or marketing content.
- Restructuring done plans under `docs/plans/done/`.
- Moving any content out of `AGENTS.md` (only adding cross-references and
  the new Documentation layout section).
- A CI check that enforces the Quick Reference table is in sync with the
  per-component files. Useful future work; not required for this plan to
  land.
