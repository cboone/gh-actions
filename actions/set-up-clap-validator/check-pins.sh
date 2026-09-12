#!/usr/bin/env bash
# check-pins.sh -- Check the clap-validator and Rust pins a caller passed,
# and derive the cache key and install directory the rest of the action uses.
# Author: Christopher Boone
# Date: 2026-09-12
#
# Configured entirely through environment variables, so the
# set-up-clap-validator composite action and this repository's own CI drive
# it the same way. The action input each variable carries is in parentheses:
#
#   VALIDATOR_REV (validator-rev)  clap-validator commit to build
#   RUST_VERSION (rust-version)    exact Rust toolchain to build it with
#
# GitHub does not enforce `required:` for a composite action's inputs: an
# omitted one arrives as the empty string. Both pins are checked here, so a
# caller that forgets one is told which instead of failing later inside
# rustup or cargo. VALIDATOR_REV must be a full commit SHA because the
# commit is the pin: `cargo --rev` also takes tags and branches, and both
# can be moved to a different commit afterwards.
#
# No ::error:: message repeats an input's value. The runner reads any output
# line beginning with "::" as a workflow command, and those messages are
# emitted before the value has been checked, so the one that never reaches
# the log needs no escaping to be safe there. A step's `with:` block is
# already in the run log when a value needs checking. The success line at
# the end does name both pins, and runs only once each has matched its
# pattern below, neither of which admits a newline or a percent sign.
#
# ImageOS, RUNNER_OS, RUNNER_ARCH, RUNNER_TEMP and GITHUB_OUTPUT must be set,
# as they are on every GitHub-hosted Actions runner. ImageOS alone is
# tolerated as empty, for a self-hosted runner that does not set it. Three
# values are written to GITHUB_OUTPUT:
#
#   cache-key    clap-validator-<os>-<arch>-<image>-<rev>-rust<rust version>
#   cache-root   <RUNNER_TEMP>/clap-validator
#   install-dir  <RUNNER_TEMP>/clap-validator/bin
#
# The key names every input to the build, and the action restores it with no
# restore-keys, so a partial match cannot quietly supply a validator built
# from another commit. Both pins are pattern-checked before they reach the
# key, which is also what keeps a newline in either one from writing a
# second, caller-controlled line to GITHUB_OUTPUT.
#
# <image> is ImageOS, such as ubuntu24 or macos15. RUNNER_OS and RUNNER_ARCH
# do not separate ubuntu-22.04 from ubuntu-24.04, which are both Linux/X64
# and carry different glibc versions, so without it a binary built on one
# would be restored on the other and die at exec. A self-hosted runner
# reports `unknown` and therefore shares one key per OS and architecture;
# a fleet with mixed images should not share a cache across them.
#
# A rust-version naming a channel (`stable`, `nightly`) is accepted, since
# `run-rust-ci.yml` permits one too, but the key cannot track what the
# channel points at: the same key keeps serving the binary built by whatever
# compiler `stable` meant the first time. Pass an exact version to pin it.
#
# cache-root is what `cargo install --root` is given, and the directory the
# cache stores; install-dir is cargo's own layout underneath it, since
# `cargo install --root DIR` writes DIR/bin/<binary>. Both are derived here
# so the build, the cache and PATH cannot come to disagree about the path.
#
# Compatible with bash 3.2, the /bin/bash on macOS: no associative arrays,
# no ${var,,}, no mapfile, and positional parameters are expanded as "$@",
# the only spelling bash 3.2 exempts from set -u when there are none
# ("${@}" fails there).
#
# Exit codes:
#   0  - Pins accepted, cache key, cache root and install directory written
#   64 - Invalid or missing input
#   71 - Unsupported operating system

set -euo pipefail

readonly E_USAGE=64
readonly E_PLATFORM=71

# A commit SHA as git and cargo spell it. Anchored, so neither a shorter
# prefix nor a value carrying a newline can match.
readonly REV_PATTERN='^[0-9a-f]{40}$'

# A rustup toolchain name: a version such as 1.97.1, or a channel such as
# stable. Deliberately no whitespace, so the value is a single argument to
# rustup and cargo and a single line in the cache key.
readonly RUST_VERSION_PATTERN='^[A-Za-z0-9][A-Za-z0-9._+-]*$'

# Emit an ::error:: annotation, then exit.
# Arguments:
#   $1 - exit code
#   $2 - headline for the annotation
function fail() {
  local exit_code="${1}"
  local headline="${2}"
  printf '::error::%s\n' "${headline}" >&2
  exit "${exit_code}"
}

# Fail unless each named runner variable is non-empty.
# Arguments:
#   $@ - variable names
function require_runner_env() {
  local name
  for name in "$@"; do
    if [[ -z "${!name:-}" ]]; then
      fail "${E_USAGE}" "${name} is not set; this script runs on a GitHub Actions runner."
    fi
  done
}

function main() {
  require_runner_env RUNNER_OS RUNNER_ARCH RUNNER_TEMP GITHUB_OUTPUT

  if [[ -z "${VALIDATOR_REV:-}" ]]; then
    fail "${E_USAGE}" "validator-rev is not set; pass the clap-validator commit to build."
  fi
  if [[ ! "${VALIDATOR_REV}" =~ ${REV_PATTERN} ]]; then
    fail "${E_USAGE}" "validator-rev must be a full 40-character lowercase commit SHA, which a tag is not."
  fi

  if [[ -z "${RUST_VERSION:-}" ]]; then
    fail "${E_USAGE}" "rust-version is not set; pass the exact Rust toolchain to build with."
  fi
  if [[ ! "${RUST_VERSION}" =~ ${RUST_VERSION_PATTERN} ]]; then
    fail "${E_USAGE}" "rust-version must be a rustup toolchain name with no spaces, such as 1.97.1."
  fi

  local kernel
  kernel="$(uname -s)"
  case "${kernel}" in
  Linux | Darwin) ;;
  *) fail "${E_PLATFORM}" "Unsupported operating system: ${kernel}. Linux and macOS runners only." ;;
  esac

  # A self-hosted runner need not set ImageOS, and one label is better than
  # refusing to run there; see the header on what that costs.
  local image="${ImageOS:-unknown}"

  local cache_root="${RUNNER_TEMP}/clap-validator"
  local install_dir="${cache_root}/bin"
  local cache_key="clap-validator-${RUNNER_OS}-${RUNNER_ARCH}-${image}-${VALIDATOR_REV}-rust${RUST_VERSION}"

  {
    printf 'cache-key=%s\n' "${cache_key}"
    printf 'cache-root=%s\n' "${cache_root}"
    printf 'install-dir=%s\n' "${install_dir}"
  } >>"${GITHUB_OUTPUT}"
  echo "Pinned clap-validator to ${VALIDATOR_REV}, built with Rust ${RUST_VERSION}" >&2
}

main "$@"
