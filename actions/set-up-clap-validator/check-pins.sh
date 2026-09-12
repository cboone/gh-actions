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
#   IMAGE_LABEL (image-label)      what to call this environment in the key,
#                                  where it cannot describe itself
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
# RUNNER_OS, RUNNER_ARCH, RUNNER_TEMP and GITHUB_OUTPUT must be set, as
# they are on every Actions runner. Three values are written to
# GITHUB_OUTPUT:
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
# <image> names the userspace the binary was built against, because
# RUNNER_OS and RUNNER_ARCH do not: ubuntu-22.04 and ubuntu-24.04 are both
# Linux/X64 and carry different glibc versions, so without it a binary built
# on one would be restored on the other and die at exec. It comes from ID
# and VERSION_ID in /etc/os-release on Linux, both required since an ID
# alone reads the same for every release of a distribution, or the major
# product version on macOS. Both describe whatever userspace the build runs
# in, container or not, and both are spelled <name>:<version>: joining them
# without a separator would let `foo` with `12` and `foo1` with `2` land on
# one key, and the os-release spec allows a colon in neither field.
#
# The runner's own ImageOS is never consulted, though it looks like the
# obvious answer on a GitHub-hosted runner. It names the host VM, so a job
# that sets `container:` reads ubuntu24 whatever the container holds, and
# two containers on one runner would land on the same key. Where the
# environment cannot describe itself, IMAGE_LABEL says what to call it, and
# that is safe for the same reason: a caller sets it deliberately. With
# neither, the run stops rather than pooling this environment with every
# other one.
#
# rust-version must name one release, because the key records what was
# passed rather than what rustup resolved it to. `stable`, `beta` and
# `nightly` are refused, with or without a host triple appended, since each
# moves to a new compiler on its own schedule. So is a partial version:
# rustup reads 1.97 as the newest 1.97.x, so a later patch would be built
# under a key already naming an older compiler's binary. That is the same
# reason validator-rev refuses a tag. A three-component version and a dated
# nightly such as nightly-2026-01-01 each name one release and are
# accepted.
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
#   64 - Invalid or missing input, image-label included
#   71 - Unsupported operating system

set -euo pipefail

readonly E_USAGE=64
readonly E_PLATFORM=71

# A commit SHA as git and cargo spell it. Anchored, so neither a shorter
# prefix nor a value carrying a newline can match.
readonly REV_PATTERN='^[0-9a-f]{40}$'

# A rustup toolchain name, such as 1.97.1 or nightly-2026-01-01.
# Deliberately no whitespace, so the value is a single argument to rustup
# and cargo and a single line in the cache key.
readonly RUST_VERSION_PATTERN='^[A-Za-z0-9][A-Za-z0-9._+-]*$'

# A version naming one release: three components, optionally followed by a
# host triple. Two components are not enough, since rustup reads 1.97 as
# the newest patch in that line rather than as a release.
readonly EXACT_VERSION_PATTERN='^[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9._+-]+)?$'

# What may stand as the <image> component of the cache key. Checked rather
# than stripped to: two labels that differ only in characters a strip would
# remove, `ubuntu/22.04` and `ubuntu22.04`, would otherwise collide on one
# key and trade binaries built against different libraries.
readonly IMAGE_PATTERN='^[A-Za-z0-9][A-Za-z0-9._:-]*$'

# What a caller may pass as image-label: the same, minus the colon. A
# derived value always carries exactly one, joining two fields that the
# os-release spec forbids one in, so no label can spell a derived value and
# the two sources cannot land on the same key.
readonly IMAGE_LABEL_PATTERN='^[A-Za-z0-9][A-Za-z0-9._-]*$'

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
  # Anything rustup resolves at install time moves out from under the cache
  # key, which records only what was passed. A channel is the obvious case,
  # bare or with a host triple appended. `1.97` is the quiet one: rustup
  # takes it and installs the newest 1.97.x, so a later patch release would
  # be built under a key that already names an older compiler's binary.
  # Rejecting both is the same reason validator-rev refuses a tag. Only a
  # dated nightly and a three-component version name one release.
  case "${RUST_VERSION}" in
  nightly-[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] | nightly-[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*) ;;
  stable | beta | nightly | stable-* | beta-* | nightly-*)
    fail "${E_USAGE}" "rust-version must not be a floating channel (stable, beta, nightly, with or without a host triple), because the cache key cannot follow where one moves; pass an exact version such as 1.97.1, or a dated nightly."
    ;;
  *)
    if [[ ! "${RUST_VERSION}" =~ ${EXACT_VERSION_PATTERN} ]]; then
      fail "${E_USAGE}" "rust-version must name one release, as 1.97.1 does; rustup resolves a partial version such as 1.97 to the newest patch in that line, which the cache key cannot follow."
    fi
    ;;
  esac

  local kernel
  kernel="$(uname -s)"
  case "${kernel}" in
  Linux | Darwin) ;;
  *) fail "${E_PLATFORM}" "Unsupported operating system: ${kernel}. Linux and macOS runners only." ;;
  esac

  # RUNNER_OS and RUNNER_ARCH are the same on ubuntu-22.04 and ubuntu-24.04,
  # whose glibc versions are not, so a third component has to say which
  # userspace the binary was built against or one would be restored on the
  # other and die at exec.
  #
  # /etc/os-release and sw_vers are read because they describe whatever
  # userspace the build actually runs in, container or not, which is the
  # question the component answers.
  local image=""
  case "${kernel}" in
  Linux)
    # Both fields or neither: VERSION_ID is optional in os-release, and an
    # ID on its own says `ubuntu` for every Ubuntu release alike, which is
    # the sharing this is here to stop. A field carrying a colon is refused
    # the same way, since the colon is what makes the pair unambiguous.
    if [[ -r /etc/os-release ]]; then
      image="$(awk -F= '$1=="ID"{gsub(/"/,"",$2); id=$2} $1=="VERSION_ID"{gsub(/"/,"",$2); v=$2} END{if (id != "" && v != "" && id !~ /:/ && v !~ /:/) printf "%s:%s", id, v}' /etc/os-release 2>/dev/null || true)"
    fi
    ;;
  Darwin)
    # Only with a version in hand: a bare `macos:` would pass the pattern
    # below and put every macOS release on one key, which is the sharing
    # this component exists to prevent.
    local macos_version
    macos_version="$(sw_vers -productVersion 2>/dev/null | cut -d. -f1 || true)"
    if [[ -n "${macos_version}" ]]; then
      image="macos:${macos_version}"
    fi
    ;;
  esac
  # image-label, never ImageOS. ImageOS names the host VM, so in a job that
  # sets `container:` it reads ubuntu24 whatever the container is, and
  # taking it whenever the derivation came up short would hand two
  # containers on one runner the same key: the collision this component
  # exists to prevent, reintroduced at the point the derivation failed.
  # image-label carries no such meaning, because a caller only sets it
  # deliberately, for an environment that could not describe itself.
  if [[ -z "${image}" ]]; then
    if [[ -n "${IMAGE_LABEL:-}" && ! "${IMAGE_LABEL}" =~ ${IMAGE_LABEL_PATTERN} ]]; then
      fail "${E_USAGE}" "image-label must match [A-Za-z0-9][A-Za-z0-9._-]*. The colon is reserved for the identifier this action derives, so that a label cannot spell one."
    fi
    image="${IMAGE_LABEL:-}"
  fi
  # Keying on nothing, or on a label that collides with another after
  # sanitizing, is the shared-key case this exists to prevent. Both are
  # refused rather than patched over.
  if [[ ! "${image}" =~ ${IMAGE_PATTERN} ]]; then
    fail "${E_PLATFORM}" "Could not identify this environment, which the cache key needs to tell environments with incompatible libraries apart. Pass image-label naming it, matching [A-Za-z0-9][A-Za-z0-9._-]*."
  fi

  local cache_root="${RUNNER_TEMP}/clap-validator"
  local install_dir="${cache_root}/bin"
  local cache_key="clap-validator-${RUNNER_OS}-${RUNNER_ARCH}-${image}-${VALIDATOR_REV}-rust${RUST_VERSION}"

  # GitHub caps a cache key at 512 characters. Checked here so a long
  # rust-version or image-label is reported as the input error it is,
  # rather than surfacing later as a restore failure about the key.
  if [[ "${#cache_key}" -gt 512 ]]; then
    fail "${E_USAGE}" "The resulting cache key is ${#cache_key} characters, past GitHub's 512-character limit. Shorten rust-version or image-label."
  fi

  {
    printf 'cache-key=%s\n' "${cache_key}"
    printf 'cache-root=%s\n' "${cache_root}"
    printf 'install-dir=%s\n' "${install_dir}"
  } >>"${GITHUB_OUTPUT}"
  echo "Pinned clap-validator to ${VALIDATOR_REV}, built with Rust ${RUST_VERSION}" >&2
}

main "$@"
