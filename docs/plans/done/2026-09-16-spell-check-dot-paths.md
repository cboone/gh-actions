# Spell-check dot-paths

Issue: [#93](https://github.com/cboone/gh-actions/issues/93)

## Approved changes

1. Enable `enableGlobDot` and `useGitignore` in `cspell.json` and add the five existing technical words reported by the issue.
1. Document consumer opt-in settings in `docs/workflows/lint-text.md`.
1. Correct the coverage comment in `.github/workflows/run-ci.yml` to account for configured exclusions.
1. Verify local and CI spelling commands include dot-paths and exclude ignored local directories, run relevant formatting and lint checks, and create signed commits referencing #93.

## Validation

Before the fix, pinned cspell 10.3.0 checks 97 files with no spelling issues.

After the fix, both `make spell` and CI's `cspell .` command check 132 files with no spelling issues, including all 24 files under `.github/`, `.claude/settings.json`, and root dot-configs.

A temporary unknown-word probe under `.github/` fails the ordinary recursive scan with exactly one issue. Identical probes under gitignored `.local/` and `.workmux/` are excluded. All probes were removed after validation.

`make lint-md`, `make format-check`, `make lint-yaml`, and `git diff --check` pass. YAML lint uses a temporary `UV_CACHE_DIR` because the sandbox cannot write the default uv cache.

## Additional findings addressed

The worktree's `.git` pointer is a file, so `ignorePaths` now excludes both `.git` and `.git/`. The expanded scan also reaches existing `neighbouring` and `unlinted` vocabulary, which is added to `words`. File-local cspell directives cover intentional Portuguese fixture vocabulary and a malformed integrity sample in `run-ci.yml`.
