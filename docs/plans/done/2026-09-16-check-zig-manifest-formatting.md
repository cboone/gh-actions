# Check Zig manifest formatting

Issue: [#106](https://github.com/cboone/gh-actions/issues/106)

## Approved plan

1. Add `fmt-paths` to `run-zig-ci.yml`, defaulting to `build.zig build.zig.zon src`.
1. Pass the input through an environment variable and parse a Bash argument array.
1. Document the default, custom paths, and space-separated path limitations.
1. Record the changed default in the Unreleased changelog.
1. Validate workflow linting, documentation formatting, and Zig behavior for default and custom paths.

## Validation

- Zig 0.16.0 with the workflow's actual formatting step under macOS Bash 3.2: formatted default layout passes; unformatted manifest fails while the previous command passes.
- A custom source directory fails when unformatted and passes after formatting; the default excludes that directory.
- A missing manifest fails the default; an override without the manifest passes.
- Empty and whitespace-only path lists fail with an input error.
- `make lint` and `make lint-yaml` pass.
- `make lint-md`, `make spell`, Prettier checks on the edited workflow and user documentation, and `git diff --check` pass.
- Markdown lint fixes and Prettier formatting applied to the edited documentation and plan before filing the completed plan here.
