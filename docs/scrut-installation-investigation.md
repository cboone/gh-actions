# Scrut release packaging and installation

Investigation for [#120](https://github.com/cboone/gh-actions/issues/120), audited on 2026-09-16. Upstream inspection is read-only.

## Release asset audit

All 32 published Linux/macOS archives, four per release, were downloaded and hashed. The [reviewed asset manifest](../tests/fixtures/scrut-release-assets.json) records each URL, archive SHA-256, extracted executable SHA-256, labeled platform and actual platform. Within every release, the two Linux executables are byte-identical x86-64 files, and the two macOS executables are byte-identical arm64 files. Archive checksums establish integrity, but do not establish executable compatibility.

| Release | Linux x86-64 asset | Linux arm64 asset     | macOS arm64 asset | macOS x86-64 asset      | Observed native version |
| ------- | ------------------ | --------------------- | ----------------- | ----------------------- | ----------------------- |
| v0.4.3  | ELF x86-64         | ELF x86-64, incorrect | Mach-O arm64      | Mach-O arm64, incorrect | `scrut 0.4.3`           |
| v0.4.2  | ELF x86-64         | ELF x86-64, incorrect | Mach-O arm64      | Mach-O arm64, incorrect | `scrut 0.4.1`           |
| v0.4.1  | ELF x86-64         | ELF x86-64, incorrect | Mach-O arm64      | Mach-O arm64, incorrect | `scrut 0.4.1`           |
| v0.4.0  | ELF x86-64         | ELF x86-64, incorrect | Mach-O arm64      | Mach-O arm64, incorrect | `scrut 0.4.0`           |
| v0.3.0  | ELF x86-64         | ELF x86-64, incorrect | Mach-O arm64      | Mach-O arm64, incorrect | `scrut 0.3.0`           |
| v0.2.3  | ELF x86-64         | ELF x86-64, incorrect | Mach-O arm64      | Mach-O arm64, incorrect | `scrut 0.2.3`           |
| v0.2.2  | ELF x86-64         | ELF x86-64, incorrect | Mach-O arm64      | Mach-O arm64, incorrect | `scrut 0.2.1`           |
| v0.2.1  | ELF x86-64         | ELF x86-64, incorrect | Mach-O arm64      | Mach-O arm64, incorrect | `scrut 0.2.1`           |

v0.2.1 uses `.tar.zst` and Rust target triples in asset names; subsequent releases use `.tar.gz` and OS/architecture names. Neither naming scheme prevents the defect. Rolling back does not provide a working arm64 Linux or Intel macOS release asset.

The issue's v0.4.3 Linux arm64 SHA-256 (`a67117f4320d129c7d7073a5e667dbad25e7a83f31480a633108250fe4069dd5`) and v0.4.2 SHA-256 (`5373cc51f85f9b24847a74412b66c4524e987c5b295799b3a98661e7a9f1e944`) match the audited archives.

### Dependencies and execution boundaries

ELF program headers identify `/lib64/ld-linux-x86-64.so.2` as the interpreter in every Linux executable. All reference symbols through `GLIBC_2.34`. v0.2.1 and v0.2.2 need `libgcc_s.so.1`, `libm.so.6`, `libc.so.6` and `ld-linux-x86-64.so.2`; v0.2.3 needs `libgcc_s.so.1` and `libc.so.6`; v0.3.0 through v0.4.3 need `libgcc_s.so.1`, `libm.so.6` and `libc.so.6`. These are dynamically linked glibc builds, including the v0.2.1 assets named `unknown-linux-musl`. They are not static musl binaries and do not support musl-only userspace as shipped.

`otool` identifies a minimum macOS version of 11.0 in all macOS executables. All link `libiconv.2.dylib` and `libSystem.B.dylib`. v0.2.3 and later also link the CoreFoundation framework. SDK versions are 15.2 for v0.2.1 through v0.2.3, 15.0 for v0.3.0, 15.4 for v0.4.0 and 15.5 for v0.4.1 through v0.4.3. Minimum OS load commands alone do not prove execution on older operating systems.

Corrected local execution on macOS 26.6.2 arm64 preserved executable permissions and passed `--version` and one executed snapshot smoke case for all 16 macOS archives, including incorrectly labeled Intel assets. This confirms execution on arm64, not Intel compatibility. Linux executables were inspected locally without execution because the local OS is macOS.

The `scrut-release-audit` CI matrix selects each runner's labeled platform and records version execution and snapshot execution, or the expected native architecture rejection for reviewed defective assets. Its artifacts preserve interpreter, direct dependencies, executable format, hashes and execution results. The matrix covers Linux x86-64, Linux arm64, macOS arm64 and [macOS Intel](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

All four initial audit jobs completed in [Run CI 35119922891](https://github.com/cboone/gh-actions/actions/runs/35119922891) at source head `88f9aa70c8f8b9199db3de0bf08c1c285eab1796`. The eight native Linux x86-64 and eight native macOS arm64 assets passed version execution. All eight labeled Linux arm64 assets were rejected with errno 8 (`Exec format error`); all eight labeled macOS x86-64 assets were rejected with errno 86 (incompatible executable architecture). The version column above matches observed Linux x86-64 and macOS arm64 output, including stale v0.2.2 and v0.4.2 output on both OSes. That initial audit used a skipped smoke fence and normalized file permissions, so it does not establish snapshot execution or original executable permissions. The corrected audit preserves extracted permissions and requires one successful, executed smoke case. Native failures are expected only in the historical audit; installers must use compatible binaries.

## Upstream architecture selection

The release workflow at every published source revision installs `matrix.target`, but invokes `cargo build --release` without `--target`. Archive creation then moves `target/release/scrut`, not `target/<target>/release/scrut`. Installing a Rust target makes it available; it does not select that target for Cargo. The Linux rows run on `ubuntu-24.04`, and the macOS rows on `macos-15`, so both architecture labels receive their runner's host executable. This also explains why the Linux musl label does not describe the actual libc dependency.

| Release | Inspected source revision and release workflow                                                                                                                              |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| v0.4.3  | [04ecce97e63c354e0374961ac977cc678d0f3932](https://github.com/facebookincubator/scrut/blob/04ecce97e63c354e0374961ac977cc678d0f3932/.github/workflows/release-binaries.yml) |
| v0.4.2  | [11604fa9cefbae192308a7495cacd61ecb2d35ce](https://github.com/facebookincubator/scrut/blob/11604fa9cefbae192308a7495cacd61ecb2d35ce/.github/workflows/release-binaries.yml) |
| v0.4.1  | [4373f5e32ad6fa8ea08f33661f546fb064545db8](https://github.com/facebookincubator/scrut/blob/4373f5e32ad6fa8ea08f33661f546fb064545db8/.github/workflows/release-binaries.yml) |
| v0.4.0  | [c5157661bb67b22d0d843996cda5783787945b45](https://github.com/facebookincubator/scrut/blob/c5157661bb67b22d0d843996cda5783787945b45/.github/workflows/release-binaries.yml) |
| v0.3.0  | [2466ad80dcdcb81d18b94f9c2b21a35ea264bbab](https://github.com/facebookincubator/scrut/blob/2466ad80dcdcb81d18b94f9c2b21a35ea264bbab/.github/workflows/release-binaries.yml) |
| v0.2.3  | [a377dfbc16d2f20888cb589ae52d438f897f8300](https://github.com/facebookincubator/scrut/blob/a377dfbc16d2f20888cb589ae52d438f897f8300/.github/workflows/release-binaries.yml) |
| v0.2.2  | [cde5f3a9db7dcb1570f42a8376012750033f1bb0](https://github.com/facebookincubator/scrut/blob/cde5f3a9db7dcb1570f42a8376012750033f1bb0/.github/workflows/release-binaries.yml) |
| v0.2.1  | [f7377c04e30375fe40fabddcce35fba22756f44d](https://github.com/facebookincubator/scrut/blob/f7377c04e30375fe40fabddcce35fba22756f44d/.github/workflows/release-binaries.yml) |

The published tag revisions share the defect. Historical release-run logs and workflow revisions are a separate provenance surface; a tag's workflow alone is not proof of which workflow actually executed to produce an asset. The archive headers and hashes independently establish the packaging failures.

## Installation decision and integrity

| Option                                         | Integrity boundary                                                                         | Decision                                                                                                            |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| Current release binaries                       | Reviewed SHA-256 per archive                                                               | Retain on Linux x86-64 and macOS arm64 only; audit before every update                                              |
| Earlier release binaries                       | Newly reviewed archive SHA-256                                                             | Rejected as a repair: all published Linux arm64 and macOS Intel assets have the same architecture defect            |
| Registry installation                          | Registry-selected source/dependencies                                                      | Rejected as the sole integrity boundary                                                                             |
| Pinned Git source with upstream lockfile       | Full source SHA plus upstream Cargo.lock and `--locked`                                    | Not currently available: v0.4.3 has no committed Cargo.lock                                                         |
| Pinned source archive with repository lockfile | Full source SHA, archive SHA-256, committed crate checksums and `--locked`, exact compiler | Approved for Linux arm64 in PR #119 and macOS x86-64 in issue #120                                                  |
| Repository-owned rebuilt release binaries      | Reviewed binary SHA-256 plus a maintained publishing process                               | Possible follow-up, but introduces another release and update surface; not needed for the approved source exception |

The source build pins v0.4.3 commit `04ecce97e63c354e0374961ac977cc678d0f3932`, source archive SHA-256 `947997a4a7140ee57183eb0cc448774e074e0bc5477c942190da4ac4fd4555cd`, Rust `1.97.1` and [Cargo.lock](../actions/set-up-scrut/Cargo.lock). The initial lockfile is copied byte-for-byte from PR #119 head `e7fd97e9a761e00e37e5153ce61988e5db7ce93e`, with SHA-256 `2fb26c22c12d2ad259a1c6591853f17c7f97752876f377159127f496682590c9`. It pins every registry dependency version and crate checksum. Generating that lockfile is a review operation, not an installer operation. Cargo must reject dependency changes rather than resolve them on the runner.

Source builds add compiler, native linker and crate-download availability requirements. The helper isolates Cargo state for each installation and removes its temporary source tree afterward. A future native binary cache must use an exact key covering the source archive, lockfile, replacement build script, Rust pin, host target and runner userspace, without partial restoration. Reusing binaries across different libc or macOS environments would weaken the compatibility boundary. No such cache is introduced by this exception.

The helper also preserves PR #119's isolation at head `3393581e4f1f588344ff3fb16e01e6a5860d1e05`: a temporary source tree outside the consumer checkout, a separate Cargo home, rejected ancestor Cargo configuration, and removed consumer build/compiler overrides. The exact compiler is selected explicitly and the build passes the compiler's host triple through `--target`, so a consumer's `CARGO_BUILD_TARGET` cannot silently select a foreign architecture. The source build uses the runner's native compiler/linker and userspace, so it is a compatible native build, not a promise of byte-identical binaries across runner images. Rust setup is SHA-pinned; Dependabot covers its action reference. Compiler and lockfile updates remain reviewed changes.

Composite actions read the helper, lockfile and version build script through `github.action_path`. All three reusable workflows fetch them from `job.workflow_repository` at `job.workflow_sha`, outside the caller's workspace. Missing workflow context fails explicitly. This source exception requires GitHub.com when used through reusable workflows; GitHub Enterprise Server cannot supply that context. The composite action can read its local pinned resources without the workflow context.

### Reproducible version reporting

Upstream [build.rs](https://github.com/facebookincubator/scrut/blob/04ecce97e63c354e0374961ac977cc678d0f3932/build.rs) uses Git semver discovery and falls back to a current timestamp. The source archive lacks Git metadata. The committed [replacement build script](../actions/set-up-scrut/build-version.rs) writes `VERSION` from `CARGO_PKG_VERSION`, making `scrut --version` report `scrut 0.4.3`. This replacement is part of the reviewed source-build exception. The helper checks the exact output before exposing the binary. This guarantees stable version reporting, not a fully reproducible binary build.

## Regression coverage

- `scrut-installation` calls the actual standalone reusable workflow across all four supported OS/architecture combinations.
- `scrut-language-installers` runs the actual `set-up-scrut` action and generated composite fixtures containing the production Go/Zig Rust setup, source fetch/build, binary install and snapshot execution steps. It also supplies an ambient cross-compilation target to test native target selection.
- The Go/Zig fixture changes only its workflow-specific context bindings and caller test inputs. It asserts the original `job.workflow_*` bindings before substituting this CI checkout's repository/SHA. It does not run the consumer's Go/Zig build jobs or independently prove those job-context values through a Go/Zig `workflow_call`; the actual standalone workflow call tests that context path.
- Every entry point executes the exact-version, executable-architecture and snapshot assertions in `tests/scrut/installation.md`. The action also remains exercised by the existing Zig formatting matrix.
- `scrut-release-audit` verifies reviewed historical archive and executable hashes before any execution. Correctly packaged native assets must execute successfully. Known architecture defects must be rejected on the intended native runner; that expected failure is audit evidence, not an approved installation path.

### Audit controls

The audit must reject a non-executable archive member and a smoke specification that executes no cases, even when Scrut returns success. [Controls](../tests/check-scrut-release-audit.py) use the real installed binary and production audit function and run in the four-platform installer matrix.

| Planted defect                  | Instrument expected to catch it                          | Observed result                                             | Regression control          |
| ------------------------------- | -------------------------------------------------------- | ----------------------------------------------------------- | --------------------------- |
| Archive executable mode is 0644 | Preserved permissions and executable-mode validity check | Rejected before binary invocation                           | Non-executable archive      |
| Smoke fence is `console`        | Executed smoke-case count                                | Scrut returned 0 with zero cases; auditor rejected it       | Skipped smoke specification |
| Smoke expected output differs   | Real Scrut execution and successful-case count           | Scrut returned 50 with one failed case; auditor rejected it | Failed smoke assertion      |

The valid archive control preserved mode 0755 and passed version and one snapshot case. Both audit protections were also weakened separately in temporary copies: removing the executed-case guard and restoring unconditional chmod each made the corresponding regression control fail with exit 1. The production auditor remained unchanged during those plants. These measurements were observed locally; native CI repetitions require a completed run.

## Maintenance and removal criteria

For an update, inspect all four new native assets before changing a pin. Record the source revision, archive/executable SHA-256, ELF or Mach-O architecture, interpreter, direct dependencies, minimum OS/libc constraints, exact version output and snapshot execution. Add the new assets to the reviewed manifest without rewriting historical entries. The tool-version audit reminds maintainers to update every installer and source-build pin together.

Remove the source exception independently for Linux arm64 or macOS x86-64 only after a corrected upstream release satisfies all of these conditions on that native runner:

1. The extracted executable's format and architecture match the intended platform.
2. Interpreter and shared-library requirements are available on the supported runner userspace; a musl label alone is insufficient.
3. `--version` reports the intended package release, and real snapshot execution passes.
4. The archive SHA-256 is reviewed and committed here, and the release installer is exercised through the action and all three reusable workflow entry points.
5. A completed CI run confirms the installed architecture, version and execution at the exact replacement head.

After both platforms return to corrected binary assets, delete the source helper, lockfile, replacement version script, Rust setup steps and action-specific Dependabot directory. Keep the historical audit and installation assertions. An upstream workflow edit, renamed asset, matching archive checksum or green x86-64 Linux job alone does not satisfy removal criteria.

PR #119 contains overlapping Scrut changes and the separate #112 text-lint repair. Reconcile those changes before merge, and ensure #112's implementation is present before publishing its requested Unreleased note as a release.
