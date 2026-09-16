# Branch Review: fix/106-check-zig-manifest-formatting

Base: `main` (merge base: `129cb37`)
Commits: 2
Files changed: 4 (1 added, 3 modified, 0 deleted, 0 renamed)
Reviewed through: `028640c`

## Summary

The branch closes the Zig manifest formatting gap by including `build.zig.zon` in the default formatting check. It adds a `fmt-paths` input so callers can select other source layouts, and documents the changed default and input limitations.

## Changes by Area

- **Zig formatting:** `.github/workflows/run-zig-ci.yml` adds the default `build.zig build.zig.zon src`, passes the input through `env`, splits it into a Bash array, rejects empty lists, and invokes `zig fmt --check` with quoted arguments.
- **User documentation:** `docs/workflows/run-zig-ci.md` describes the default, missing-manifest behavior, single-line space-separated input contract, and a custom-layout example. `CHANGELOG.md` records the fix and compatibility implications under Unreleased.
- **Plan record:** `docs/plans/done/2026-09-16-check-zig-manifest-formatting.md` retains the approved approach and validation results.

## File Inventory

Added (1):

- `docs/plans/done/2026-09-16-check-zig-manifest-formatting.md`

Modified (3):

- `.github/workflows/run-zig-ci.yml`
- `CHANGELOG.md`
- `docs/workflows/run-zig-ci.md`

No files were deleted or renamed.

## Notable Changes

The default formatting job now fails for missing or unformatted `build.zig.zon` files. Callers without a manifest can preserve their layout by overriding `fmt-paths`. There are no dependency, permission, or external action pin changes. Usage examples follow the repository convention of retaining the current released tag until release preparation.

## Plan Compliance

**Verdict: good compliance, 5/5 items done (100%).** The matching plan is `docs/plans/done/2026-09-16-check-zig-manifest-formatting.md`.

1. **Done:** Add `fmt-paths` with the specified default. The workflow defines the input exactly as planned.
1. **Done:** Pass through an environment variable and parse a Bash array. The implementation avoids shell expression interpolation and preserves each parsed argument when invoking Zig.
1. **Done:** Document defaults, custom paths, and parsing limitations. The reference includes a custom example and explicitly excludes quoting, escaping, glob expansion, and paths containing spaces.
1. **Done:** Record the changed default in Unreleased. The changelog explains that existing callers can now fail for missing or unformatted manifests.
1. **Done:** Validate linting, documentation formatting, and default/custom Zig behavior. Independent review checks reproduced the recorded local validation.

No approach deviations, scope additions, omissions, or ordering concerns were found. The implementation satisfies the plan's intent. The plan requires behavioral validation, which was performed, but does not require a committed regression test.

## Code Quality Assessment

**Verdict: ready to merge. No blocking findings.**

The change is small, readable, and consistent with the repository's Bash array parsing convention. Empty inputs fail with a clear diagnostic. Quoted array expansion prevents shell evaluation and unintended glob expansion. Documentation covers the changed default and the supported input contract; there are no unfinished implementations or new TODO markers.

### Validation

- `make lint`, `make lint-yaml`, `make lint-md`, `make spell`, and `make format-check` passed.
- `git diff --check 129cb37..HEAD` passed.
- The temporary validation script executes the actual formatting step extracted from the workflow under macOS `/bin/bash` with strict shell settings and Zig 0.16.0. A formatted default layout passes; an unformatted manifest fails while the old command passes. Custom directories fail when unformatted and pass after formatting. A missing manifest fails by default and passes with an override excluding it. Empty and whitespace-only inputs fail.

### Suggestion and limits

Consider retaining behavioral coverage in the repository's self-tests so later changes to the default paths or parsing cannot silently restore the gap. The current evidence comes from local validation and a temporary script, not a committed regression test. Linux and hosted GitHub Actions execution were not exercised during this review, and other Zig versions were not tested.
