# Composite action instructions

Read [the development reference](../docs/development.md) before adding or changing an action, particularly its trust model and action procedure.

- Use `using: composite`. `set-up-*` installs; `run-*` adds execution. Downloaded tools accept a pinned version default unless the documented interface deliberately makes the caller supply the pin. Runner-provided tools follow their documented exception.
- For release binaries, use `install-pinned-tool/install-pinned-tool.sh`. Bind its `github.action_path` location through `env:` so container jobs translate the host path. Set unused installer variables to empty strings to prevent caller environment leakage.
- Keep the generic installer Bash 3.2 compatible. Release-binary installers detect OS and architecture, reject unsupported systems, verify SHA-256, install to `RUNNER_TEMP`, then update `GITHUB_PATH`. Wrapper, npm, Python and source-built actions follow their applicable trust path in the development reference.
- Pass inputs through `env:`. Composite `args` inputs are one argument per line, parsed with `while IFS= read -r` into arrays so spaces within an argument are preserved.
- `set-up-clap-validator` requires both a caller-provided Rust version and a full lowercase 40-character source revision; there are no defaults. Use its locked, source-pinned install contract.
- Caller-supplied cspell dictionaries require exact package versions and reviewed sha512 digests. Reject packages with dependencies, optional dependencies or peer dependencies; install beside `cspell-lib` so configuration outside the checkout resolves them.
- Create or update the action README and root Quick Reference entry in the same change. Descriptions, inputs, outputs, caveats and examples belong in the component README.
- Exercise changes through the repository's CI self-tests with both success cases and rejected inputs. Keep integrity and argument parsing boundaries explicit in coverage.
