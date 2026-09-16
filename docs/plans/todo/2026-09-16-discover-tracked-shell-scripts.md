# Discover tracked shell scripts

Issue: [#86](https://github.com/cboone/gh-actions/issues/86)

## Approved changes

1. Install pinned shfmt before discovery when either checker is enabled.
1. Discover tracked shell scripts with `git ls-files` and shfmt, preserving paths with spaces.
1. Report an empty discovered set through a notice and job summary.
1. Preserve `.editorconfig` by keeping style flags out of `shfmt -d`.
1. Update workflow documentation and add regression coverage for discovery and checker execution.
1. Run relevant validation and create signed commits referencing the issue.

## Validation

Exercise the workflow's shell steps against temporary Git indexes containing extension-less scripts in nested directories, paths with spaces, ordinary extension-based scripts, non-shell files, and untracked scripts. Check empty discovery and confirm both linters report defects in discovered scripts. Run actionlint, YAML lint, Markdown lint, Prettier, and cspell.
