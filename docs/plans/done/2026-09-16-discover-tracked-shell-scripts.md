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

## Results

Implemented tracked-file discovery with `shfmt -f` per regular file and a NUL-separated manifest. The pinned shfmt 3.13.1 incorrectly lists explicitly supplied non-shell files with `-f=0`, so that mode cannot implement the proposed batching safely.

The regression script executes the workflow's actual discovery and checker shell blocks. It passes with checksum-verified shfmt 3.13.1 and ShellCheck 0.11.0, covering nested extension-less scripts, spaces, newlines, leading dashes, non-shell files, untracked files, submodule contents, empty indexes, non-shell-only indexes, Git failures, real ShellCheck findings, and `.editorconfig` formatting. The existing three-runner installer job runs this script, and a ShellCheck-only reusable-workflow job exercises discovery with formatting disabled.

Local actionlint, YAML lint, Markdown lint, Prettier, and cspell checks passed. Discovery and both checkers also passed on this repository's four tracked shell scripts. GitHub Actions execution remains to be verified after publishing the branch.
