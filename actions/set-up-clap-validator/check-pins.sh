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
# No message repeats an input's value. The runner reads any output line
# beginning with "::" as a workflow command, and a value that never reaches
# the log needs no escaping to be safe there. A step's `with:` block is
# already in the run log when a value needs checking.
#
# RUNNER_OS, RUNNER_ARCH, RUNNER_TEMP and GITHUB_OUTPUT must be set, as they
# are on every Actions runner. Two values are written to GITHUB_OUTPUT:
#
#   cache-key    clap-validator-<os>-<arch>-<rev>-rust<rust version>
#   install-dir  <RUNNER_TEMP>/clap-validator/bin
#
# The key names every input to the build, and the action restores it with no
# restore-keys, so a partial match cannot quietly supply a validator built
# from another commit. Both pins are pattern-checked before they reach the
# key, which is also what keeps a newline in either one from writing a
# second, caller-controlled line to GITHUB_OUTPUT. install-dir is cargo's
# own layout: `cargo install --root DIR` writes DIR/bin/<binary>.
#
# Compatible with bash 3.2, the /bin/bash on macOS: no associative arrays,
# no ${var,,}, no mapfile, and positional parameters are expanded as "$@",
# the only spelling bash 3.2 exempts from set -u when there are none
# ("${@}" fails there).
#
# Exit codes:
#   0  - Pins accepted, cache key and install directory written
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

  local install_dir="${RUNNER_TEMP}/clap-validator/bin"
  local cache_key="clap-validator-${RUNNER_OS}-${RUNNER_ARCH}-${VALIDATOR_REV}-rust${RUST_VERSION}"

  printf 'cache-key=%s\n' "${cache_key}" >>"${GITHUB_OUTPUT}"
  printf 'install-dir=%s\n' "${install_dir}" >>"${GITHUB_OUTPUT}"
  echo "Pinned clap-validator to ${VALIDATOR_REV}, built with Rust ${RUST_VERSION}" >&2
}

main "$@"
