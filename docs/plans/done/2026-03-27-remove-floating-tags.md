# Remove Floating Major Tags

## Context

This repository currently maintains floating major tags (`v1`, `v2`) that are
force-updated on each release so callers referencing `@v1` or `@v2` automatically
pick up non-breaking changes. This convention adds complexity to the release
process, requires force-pushing tags (which some tooling and policies discourage),
and provides less auditability than exact version pins. The README usage examples
already reference `@main`, not floating tags, suggesting the convention is not
heavily relied upon in practice. Moving to exact version tags (e.g., `@v2.1.0`)
aligns with the approach used by most GitHub Actions repositories.

## Changes

### 1. README.md (lines 808-847): Rewrite Versioning section

Remove all floating tag references. The updated section should:

- State the project uses semantic versioning with exact version tags
- Keep the version bump definitions (patch/minor/major) as-is
- Simplify the release process to describe a single exact tag per release
- Update the push command example to `git push origin main v2.2.0`
- Update pinning options to recommend exact version tags (e.g., `@v2.1.0`),
  with `@main` as an option for testing
- Remove `@v2` and `@v1` from pinning options

### 2. AGENTS.md (lines 110-119): Update Releasing section

- Line 115: Change "push the commit and both tags (exact + floating major)" to
  "push the commit and tag"
- Lines 117-119: Remove the floating tag paragraph entirely

### 3. CLAUDE.md (lines 110-119): Update Releasing section

Identical changes to AGENTS.md (the sections are currently identical).

### 4. .github/copilot-instructions.md

- Line 14: Replace floating tag convention with exact version tag convention.
  Update the "Do not suggest changes" guard to say "Do not suggest adding
  floating tags."
- Line 21: Remove the `@v2` mention. Simplify to note that usage examples use
  `@main` and the Versioning section explains exact-version pinning for
  production use.

### 5. docs/plans/todo/2026-03-07-reusable-actions-and-workflows.md (lines 55-62)

This plan is still in `todo/` but its work is largely complete. Update the
versioning strategy subsection:

- Remove the "Maintain a floating `v1` tag" bullet
- Update the caller pinning bullet to recommend exact version tags or `@main`

### 6. CHANGELOG.md: Add Unreleased entry

Add under `[Unreleased]`:

```markdown
### Changed

- Versioning strategy now uses only exact version tags (e.g., `v2.2.0`);
  floating major tags (`v1`, `v2`) are discontinued
```

### 7. Delete remote floating tags

After the documentation changes are merged to main:

```bash
git tag -d v1 v2
git push origin :refs/tags/v1 :refs/tags/v2
```

This step happens manually after merge, not as part of the commits.

## Files to modify

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.github/copilot-instructions.md`
- `docs/plans/todo/2026-03-07-reusable-actions-and-workflows.md`
- `CHANGELOG.md`

## Files NOT modified

- Workflow files (no floating tag logic)
- Composite action files (no floating tag references)
- `docs/plans/done/` files (historical records, preserved as-is)

## Out of scope

- The `/release` skill creates both tags. Its behavior will need a separate
  update to stop producing floating tags. This plan covers only the
  documentation and repository-level changes.
- Updating downstream consumers to switch from `@v2` to exact pins. That is
  a follow-up task per repo.

## Verification

1. `grep -r` for `floating` across the repo to confirm no stale references
2. `grep -r '@v1\b\|@v2\b'` (excluding `done/` plans and CHANGELOG comparison
   links) to confirm no remaining floating tag recommendations
3. `make lint` to validate workflow files still pass actionlint
4. `make lint-md` to validate Markdown formatting
5. `make spell` to check for spelling issues
6. Read through the updated README Versioning section for coherence
