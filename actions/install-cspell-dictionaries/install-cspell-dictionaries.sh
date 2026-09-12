#!/usr/bin/env bash
# install-cspell-dictionaries.sh -- Install cspell dictionary packages from
# npm, each pinned to an exact version and verified against a caller-supplied
# sha512, beside an existing cspell installation.
# Author: Christopher Boone
# Date: 2026-09-12
#
# Configured entirely through environment variables, so the
# install-cspell-dictionaries composite action, the run-cspell action and
# lint-text.yml all drive it the same way. The action input each variable
# carries is in parentheses:
#
#   PACKAGES (packages)        one `<name>@<version>  sha512-<base64>` entry
#                              per line
#   INSTALL_DIR (install-dir)  npm project directory whose node_modules
#                              already holds cspell
#
# The packages land in INSTALL_DIR/node_modules, beside cspell-lib. cspell
# resolves a bare `import` specifier against cspell-lib's own directory as
# well as the config file's, so a config anywhere else in the tree reaches
# them: see tryImportResolve in cspell-lib's resolveFile.js and srcDirectory
# in its pkg-info.mjs. That is what lets a consumer write the idiomatic
# `"import": ["@cspell/dict-pt-pt/cspell-ext.json"]` and stay unaware of
# where CI put the tools.
#
# Each tarball is downloaded from its deterministic registry URL and verified
# against the caller's integrity before npm reads it, so the registry is
# never the integrity boundary. A package declaring dependencies of any kind
# is refused: npm would resolve those from the registry unverified, and
# nothing may reach node_modules that the caller did not hash. That covers
# optionalDependencies, which npm installs by default, and peerDependencies,
# which npm resolves on its own from version 7.
#
# RUNNER_TEMP must be set, as it is on every Actions runner.
#
# Compatible with bash 3.2, the /bin/bash on macOS: no associative arrays, no
# ${var,,}, no mapfile, and positional parameters are expanded as "$@", the
# only spelling bash 3.2 exempts from set -u when there are none ("${@}"
# fails there). An empty array is never expanded as "${array[@]}" for the
# same reason. openssl computes the digest because base64's single-line
# option is spelled -w0 on GNU and -b0 on BSD. rm, mv and tar take short
# options because the BSD variants on macOS lack the long forms.
#
# escape_data, fail, cleanup, require_runner_env and download mirror
# install-pinned-tool.sh's. Each script is fetched on its own at a workflow's
# commit, so both stay self-contained rather than sharing a library that
# would double the fetch.
#
# Exit codes:
#   0  - Installed, or nothing to install
#   64 - Invalid or missing input
#   65 - Integrity malformed or mismatched
#   66 - Package tarball rejected: unreadable, or it declares dependencies
#   69 - Download failed
#   70 - npm failed to install a verified tarball

set -euo pipefail

readonly E_USAGE=64
readonly E_INTEGRITY=65
readonly E_PACKAGE=66
readonly E_DOWNLOAD=69
readonly E_INSTALL=70

readonly DOWNLOAD_RETRIES=3
readonly DOWNLOAD_RETRY_DELAY=5

readonly REGISTRY='https://registry.npmjs.org'

# An npm package name is lowercase and optionally scoped; the version is
# exact, with optional prerelease or build metadata. A range, a dist-tag, and
# a git, file or URL spec all match none of this, and neither does a leading
# '-', which would reach curl and npm as an option.
readonly SPEC_PATTERN='^(@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*@[0-9]+\.[0-9]+\.[0-9]+([-+][0-9A-Za-z.-]+)*$'
# A 64-byte digest is always 88 base64 characters, the last two padding.
readonly INTEGRITY_PATTERN='^sha512-[A-Za-z0-9+/]{86}==$'

# Staging directory for downloads and unpacking, removed on exit.
WORK_DIR=""

# Encode text as workflow-command data, as @actions/core's escapeData does:
# % becomes %25, CR %0D and LF %0A, so the text stays on one line and can
# neither end a command early nor start another.
# Arguments:
#   $1 - text
function escape_data() {
  local text="${1}"
  local percent='%'
  local cr=$'\r'
  local lf=$'\n'
  text="${text//"${percent}"/%25}"
  text="${text//"${cr}"/%0D}"
  text="${text//"${lf}"/%0A}"
  printf '%s' "${text}"
}

# Emit an ::error:: annotation, then exit. The headline and the detail lines
# can repeat caller input, so each is encoded with escape_data. A detail line
# must also begin with fixed text: the runner reads any output line that
# starts with "::", after trimming leading whitespace, as a workflow command.
# Arguments:
#   $1 - exit code
#   $2 - headline for the annotation
#   $3... - detail lines, printed to stderr after the headline
function fail() {
  local exit_code="${1}"
  local headline="${2}"
  shift 2
  printf '::error::%s\n' "$(escape_data "${headline}")" >&2
  local line
  for line in "$@"; do
    printf '%s\n' "$(escape_data "${line}")" >&2
  done
  exit "${exit_code}"
}

function cleanup() {
  local exit_code="${?}"
  if [[ -n "${WORK_DIR}" ]]; then
    rm -rf "${WORK_DIR}"
  fi
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

# Fail unless each named command is on PATH.
# Arguments:
#   $@ - command names
function require_command() {
  local name
  for name in "$@"; do
    if ! command -v "${name}" >/dev/null 2>&1; then
      fail "${E_USAGE}" "${name} is not on PATH; it is needed to install cspell dictionaries."
    fi
  done
}

# Download a URL to a file.
# Arguments:
#   $1 - https:// URL
#   $2 - destination path
function download() {
  local url="${1}"
  local destination="${2}"
  echo "Downloading ${url}" >&2
  # --proto '=https' also governs every redirect --location follows, so a
  # redirect cannot downgrade the transfer to plain http. --retry-all-errors
  # is what makes --retry cover the HTTP errors that --fail reports, such as
  # a registry answering 404 briefly after a publish.
  if ! curl --silent --show-error --fail --location --proto '=https' \
    --retry "${DOWNLOAD_RETRIES}" --retry-delay "${DOWNLOAD_RETRY_DELAY}" \
    --retry-all-errors --output "${destination}" "${url}"; then
    fail "${E_DOWNLOAD}" "Download failed: ${url}"
  fi
}

# Print a file's SHA-512 in npm's integrity format: the algorithm name, a
# hyphen, and the base64 of the raw digest, which is what a package's
# dist.integrity holds.
# Arguments:
#   $1 - file path
function compute_integrity() {
  local file_path="${1}"
  local digest
  digest="$(openssl dgst -sha512 -binary "${file_path}" | openssl base64 -A)"
  printf 'sha512-%s' "${digest}"
}

# Fail unless a package tarball declares no dependencies npm would go to the
# registry for. All three fields count: npm installs optionalDependencies by
# default, and resolves peerDependencies automatically from npm 7 on. None of
# them would be covered by the caller's integrity, so only a package that
# declares no dependency at all can be installed under that integrity alone.
# Arguments:
#   $1 - tarball path
#   $2 - <name>@<version>, for error messages
function require_no_dependencies() {
  local tarball="${1}"
  local spec="${2}"
  local manifest
  if ! manifest="$(tar -x -z -O -f "${tarball}" package/package.json 2>/dev/null)"; then
    fail "${E_PACKAGE}" "${spec}: the tarball holds no package/package.json."
  fi
  # Each name is reported with the field that declared it, so the message
  # names what to remove rather than only that something is there. node's
  # diagnostics go to a file rather than into the capture, so a warning on
  # stderr can never be mistaken for a dependency name.
  local dependencies
  if ! dependencies="$(printf '%s' "${manifest}" |
    node -p 'const m = JSON.parse(require("fs").readFileSync(0, "utf8")); ["dependencies", "optionalDependencies", "peerDependencies"].flatMap((f) => Object.keys(m[f] || {}).map((d) => d + " (" + f + ")")).join(", ")' \
      2>"${WORK_DIR}/node-stderr")"; then
    fail "${E_PACKAGE}" "${spec}: package.json in the tarball could not be read." \
      "node reported: $(tr '\n' ' ' <"${WORK_DIR}/node-stderr")"
  fi
  if [[ -n "${dependencies}" ]]; then
    fail "${E_PACKAGE}" "${spec} declares dependencies: ${dependencies}." \
      "Only a package that declares none can be installed under its own" \
      "integrity, because npm would resolve these from the registry" \
      "unverified. Dictionary packages ship data and normally declare none."
  fi
}

function main() {
  require_runner_env RUNNER_TEMP
  require_command curl node npm openssl tar

  local packages="${PACKAGES:-}"
  local install_dir="${INSTALL_DIR:-}"

  if [[ -z "${install_dir}" ]]; then
    fail "${E_USAGE}" "install-dir is not set."
  fi
  if [[ ! -d "${install_dir}" ]]; then
    fail "${E_USAGE}" "install-dir is not a directory: '${install_dir}'."
  fi
  local node_modules="${install_dir}/node_modules"
  if [[ ! -d "${node_modules}/cspell-lib" ]]; then
    fail "${E_USAGE}" "cspell is not installed in ${node_modules}." \
      "A dictionary is resolved through cspell-lib's own directory, so cspell" \
      "must already be installed where the dictionaries are going beside it."
  fi

  # Read every entry before downloading anything, so a malformed one fails
  # without a single request having been made.
  local specs=()
  local integrities=()
  # Package names already seen, space delimited on both sides so a match is
  # always a whole name. Two entries naming one package would unpack to a
  # single directory and leave the second move with nothing to find.
  local seen=" "
  local line spec integrity extra name
  while IFS= read -r line; do
    # A trailing carriage return would otherwise ride along on the last
    # field and fail its pattern for a reason the message does not show.
    line="${line%$'\r'}"
    # The inner read trims the surrounding whitespace the outer one keeps,
    # and splits the entry's two fields.
    read -r spec integrity extra <<<"${line}"
    if [[ -z "${spec}" ]]; then
      continue
    fi
    case "${spec}" in
    '#'*) continue ;;
    esac
    if [[ -z "${integrity}" || -n "${extra}" ]]; then
      fail "${E_USAGE}" "packages: expected '<name>@<version>  sha512-<base64>', got '${line}'."
    fi
    if [[ ! "${spec}" =~ ${SPEC_PATTERN} ]]; then
      fail "${E_USAGE}" "packages: '${spec}' is not <name>@<version> with an exact version." \
        "A version range, a dist-tag such as latest, and a git, file or URL" \
        "spec are all rejected: the integrity pins one published tarball."
    fi
    if [[ ! "${integrity}" =~ ${INTEGRITY_PATTERN} ]]; then
      fail "${E_INTEGRITY}" "packages: '${integrity}' is not a sha512 integrity for ${spec}." \
        "Expected sha512- and 88 base64 characters, as printed by" \
        "npm view ${spec} dist.integrity"
    fi
    name="${spec%@*}"
    if [[ "${seen}" == *" ${name} "* ]]; then
      fail "${E_USAGE}" "packages: ${name} is named more than once." \
        "List each package once, at the one version its integrity pins."
    fi
    seen="${seen}${name} "
    specs+=("${spec}")
    integrities+=("${integrity}")
  done < <(printf '%s\n' "${packages}")

  local -i count=${#specs[@]}
  if ((count == 0)); then
    echo "No cspell dictionaries requested." >&2
    return 0
  fi

  WORK_DIR="$(mktemp -d "${RUNNER_TEMP}/cspell-dictionaries.XXXXXX")"
  trap cleanup EXIT
  mkdir -p "${WORK_DIR}/download" "${WORK_DIR}/unpack"

  local tarballs=()
  local -i index
  local version asset url tarball actual
  for ((index = 0; index < count; index++)); do
    spec="${specs[index]}"
    integrity="${integrities[index]}"
    name="${spec%@*}"
    version="${spec##*@}"
    # A scope stays in the path but not in the file name, so
    # @cspell/dict-pt-pt@3.0.6 is served as
    # /@cspell/dict-pt-pt/-/dict-pt-pt-3.0.6.tgz. Two scopes can publish the
    # same unscoped name, so the entry's position keeps the staged files
    # apart.
    asset="${name##*/}-${version}.tgz"
    url="${REGISTRY}/${name}/-/${asset}"
    tarball="${WORK_DIR}/download/${index}-${asset}"

    download "${url}" "${tarball}"
    actual="$(compute_integrity "${tarball}")"
    if [[ "${actual}" != "${integrity}" ]]; then
      fail "${E_INTEGRITY}" "Integrity verification failed for ${spec}" \
        "Expected: ${integrity}" \
        "Actual:   ${actual}"
    fi
    echo "Verified ${actual} for ${spec}" >&2
    require_no_dependencies "${tarball}" "${spec}"
    tarballs+=("${tarball}")
  done

  # npm unpacks the verified tarballs in a directory of its own, so it can
  # neither reify nor prune the pinned tree the dictionaries are about to
  # join, and reaches no registry: every package here declares no dependency
  # and is already on disk. --omit holds that second property independently
  # of the manifest check above, so no registry package can enter the staging
  # tree even if a tarball slipped past it.
  printf '%s\n' '{ "name": "cspell-dictionaries", "version": "0.0.0", "private": true }' \
    >"${WORK_DIR}/unpack/package.json"
  if ! (cd "${WORK_DIR}/unpack" &&
    npm install --ignore-scripts --no-audit --no-fund \
      --omit=dev --omit=optional --omit=peer "${tarballs[@]}"); then
    fail "${E_INSTALL}" "npm failed to unpack the verified dictionary tarballs."
  fi

  local unpacked target
  for ((index = 0; index < count; index++)); do
    spec="${specs[index]}"
    name="${spec%@*}"
    unpacked="${WORK_DIR}/unpack/node_modules/${name}"
    # npm names the directory after the tarball's own package.json, so a
    # tarball that is not the package it was fetched as lands elsewhere.
    if [[ ! -f "${unpacked}/package.json" ]]; then
      fail "${E_INSTALL}" "npm did not unpack ${name} from its verified tarball."
    fi
    target="${node_modules}/${name}"
    # A scoped package needs its scope directory. Removing the target first
    # means neither a directory nor a link already there is followed.
    mkdir -p "${target%/*}"
    rm -rf "${target}"
    mv "${unpacked}" "${target}"
    echo "Installed ${spec} to ${target}" >&2
  done
}

main "$@"
