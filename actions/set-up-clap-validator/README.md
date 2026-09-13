# set-up-clap-validator

Build [clap-validator](https://github.com/free-audio/clap-validator), the
conformance checker for [CLAP](https://github.com/free-audio/clap) audio
plugins, from a pinned commit, cache the result, and add it to `PATH`. The
commit is the pin, because a tag can be moved to another commit, and
`--locked` extends that pin to the dependency tree. Running the validator is
left to the calling job. Linux and macOS runners only.

clap-validator is not published to crates.io and its release assets cover
neither Linux arm64 nor a name derivable from a version string, so this
action builds it rather than downloading a verified binary the way
[install-pinned-tool](../install-pinned-tool/README.md) does. The pins are
checked by `check-pins.sh` next to this file, configured through environment
variables named after the inputs (`validator-rev` is `VALIDATOR_REV`).

- **Pins.** Both inputs are required and neither is defaulted, so a caller
  that forgets one fails loudly rather than validating against an arbitrary
  version. GitHub does not enforce `required:` for a composite action's
  inputs, passing an omitted one through as the empty string, so the action
  rejects it itself with exit code 64.
- **A commit, not a tag.** `validator-rev` must be a full 40-character
  lowercase commit SHA; a tag, a branch or a short SHA fails the step even
  though `cargo --rev` would accept all three. clap-validator reporting
  version `0.4.1` does not mean two binaries are the same, so the tag is not
  the identity that matters. Resolve a tag to its commit with
  `gh api repos/free-audio/clap-validator/git/ref/tags/0.4.1 --jq '.object.sha'`.
- **Cache.** The key is
  `clap-validator-<os>-<arch>-<image>-<validator-rev>-rust<rust-version>`,
  naming every input to the build. `<image>` names this environment, as
  `ubuntu:24.04` or `macos:15`: OS and architecture alone do not separate
  ubuntu-22.04 from ubuntu-24.04, which are both Linux and X64 and carry
  different glibc versions, so a matrix over both would otherwise restore a
  binary that cannot exec. It comes from `ID` and `VERSION_ID` in
  `/etc/os-release` on Linux, both required since an `ID` alone reads the
  same for every release of a distribution, or the major product version on
  macOS. Both describe whatever userspace the build runs in, container or
  not. The runner's own `ImageOS` is deliberately never used: it names the
  host VM, so a job that sets `container:` would read `ubuntu24` whatever
  the container held, and two containers on one runner would land on the
  same key. An environment that can describe itself through neither source
  is refused rather than pooled with every other one, and `image-label`
  says what to call it. The two halves are joined with a colon, which the
  os-release spec allows in neither, so `foo` with `12` cannot collide with
  `foo1` with `2`; `image-label` forbids the colon for the same reason, so
  no label can spell a derived identifier. There are no `restore-keys`: a partial match would silently supply a validator built
  from a different commit, which is the failure the pinning exists to
  prevent. Restore and save are separate steps, so the save happens
  explicitly on the success path. Two jobs racing a cold cache both build;
  the loser's save logs a warning and does not fail.
- **Build isolation.** Cargo takes configuration from three places, and
  the build closes each. `CARGO_HOME` points at an action-owned directory,
  emptied on each rebuild, so the runner's `config.toml` is not read. The
  build runs from a fresh `/tmp` directory, so cargo's search of the working
  directory and its parents finds neither the workspace's
  `.cargo/config.toml` nor the runner's own. From the environment it clears
  the variables that change what the compiler produces: `RUSTFLAGS`,
  `CARGO_ENCODED_RUSTFLAGS`, `CARGO_BUILD_RUSTFLAGS`, `CARGO_BUILD_TARGET`,
  `RUSTC`, `RUSTC_WRAPPER`, `RUSTC_WORKSPACE_WRAPPER`, their
  `CARGO_BUILD_RUSTC`, `CARGO_BUILD_RUSTC_WRAPPER` and
  `CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER` spellings, and every
  `CARGO_TARGET_<triple>_RUSTFLAGS`, `_LINKER` and `_RUNNER`. That last part
  is a list rather than a boundary: a `CARGO_PROFILE_*` override, or a
  variable Cargo adds in future, would still reach the build. Scrubbing to
  an allowlist would close that, at the cost of dropping the proxy and
  certificate variables a self-hosted runner needs to fetch the source. It is a tool the
  job runs rather than part of what the job builds, and the cache key names
  only the pins and the environment: a setting that changed the binary
  would be invisible to the key, and `CARGO_BUILD_TARGET` in particular
  would cache a binary that cannot run on the runner that built it. A
  consequence worth knowing: the build does not share the runner's cargo
  registry cache, so a cache miss re-downloads the dependency sources.
- **Toolchain.** `rustup` and `cargo` must be on `PATH`, as they are on
  GitHub-hosted Linux and macOS images. `rust-version` is installed with
  `--profile minimal` only when the cache misses, so a cache hit installs no
  Rust at all and compiles nothing: the restored binary is standalone. Pin
  it because clap-validator 0.4.1 declares MSRV 1.95.0 and is edition 2024,
  which the runner image's preinstalled Rust may or may not satisfy from one
  refresh to the next. It must name one release, since the key records what
  was passed rather than what rustup resolved it to. `stable`, `beta` and
  `nightly` are refused, with or without a host triple appended, and so is a
  partial version such as `1.97`, which rustup reads as the newest `1.97.x`.
  Either way a hit would go on serving the binary an older compiler built.
  That is the same reason `validator-rev` refuses a tag, and it is why this
  input is stricter than
  [run-rust-ci](../../docs/workflows/run-rust-ci.md)'s, which caches no
  compiled artifact against the toolchain name. A three-component version and
  a dated nightly such as `nightly-2026-01-01` each name one release and are
  accepted. Either may carry a host triple, as
  `1.97.1-x86_64-apple-darwin` does, which is how an arm64 macOS runner
  builds an x86_64 validator for x86_64 plugins. The triple is not checked
  against the runner: rustup is the authority on which toolchains exist for
  a host, and a mismatched one fails there rather than here. It does reach
  the cache key, so a host-qualified toolchain never shares a key with a
  bare one.
- **Install location.** The binary is installed as
  `$RUNNER_TEMP/clap-validator/bin/clap-validator`, which is `cargo install
--root`'s own layout rather than the `$RUNNER_TEMP/<tool>-bin/<tool>` the
  download-based actions use. Installing somewhere this action owns, instead
  of `~/.cargo/bin`, keeps the cached path to exactly what was built here.
- **Running the validator.** `clap-validator validate <bundle>` stays in the
  calling job on purpose: it is the gate, and the gate should be readable in
  the job that runs it. The action installs and exposes the tool, nothing
  more.

## Inputs

| Name            | Type   | Default  | Description                                                                                                |
| --------------- | ------ | -------- | ---------------------------------------------------------------------------------------------------------- |
| `validator-rev` | string | required | clap-validator commit to build, as a full 40-character lowercase SHA                                       |
| `rust-version`  | string | required | Rust toolchain naming one release, such as `1.97.1`                                                        |
| `image-label`   | string | `""`     | What to call this environment in the cache key, with no colon; needed only where it cannot describe itself |

## Outputs

| Name          | Description                                                                 |
| ------------- | --------------------------------------------------------------------------- |
| `install-dir` | Directory holding the binary (`$RUNNER_TEMP/clap-validator/bin`), on `PATH` |
| `cache-hit`   | `true` when the build came from the cache, so nothing was compiled          |

## Usage

```yaml
- uses: cboone/gh-actions/actions/set-up-clap-validator@v3.1.1
  with:
    # Tag 0.4.1, resolved to its commit.
    validator-rev: 152b9823e992d782c5c1fd33bca0295478b919aa
    rust-version: "1.97.1"
- run: clap-validator validate build/MyPlugin.clap
```

Jobs that validate different builds of the same plugin need the same pins,
because a key written twice can drift and a drifted key still passes: it
just pays a full Rust build on every run instead of none. Declare them once
at workflow level:

```yaml
env:
  VALIDATOR_REV: 152b9823e992d782c5c1fd33bca0295478b919aa
  RUST_VERSION: "1.97.1"

jobs:
  validate-native:
    runs-on: macos-latest
    steps:
      - uses: cboone/gh-actions/actions/set-up-clap-validator@v3.1.1
        with:
          validator-rev: ${{ env.VALIDATOR_REV }}
          rust-version: ${{ env.RUST_VERSION }}
      - run: clap-validator validate zig-out/MyPlugin.clap
```
