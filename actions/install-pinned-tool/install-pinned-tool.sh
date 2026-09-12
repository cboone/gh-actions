#!/usr/bin/env bash
# install-pinned-tool.sh -- Install a release binary pinned to an exact
# version and SHA-256, and put it on the GitHub Actions PATH.
# Author: Christopher Boone
# Date: 2026-09-11
#
# Configured entirely through environment variables, so the
# install-pinned-tool composite action, the set-up-* actions and the
# reusable workflows in this repository all drive it the same way. The
# action input each variable carries is in parentheses:
#
#   TOOL (tool)                      binary name; installs as <install-dir>/<tool>
#   VERSION (version)                exact version, substituted for {version}
#   URL_TEMPLATE (url-template)      https:// URL of the release asset
#   CHECKSUM (checksum)              one SHA-256, applied on every platform
#   CHECKSUMS (checksums)            sha256sum-format lines, one per asset
#   CHECKSUMS_URL_TEMPLATE           https:// URL of an upstream checksum file
#     (checksums-url-template)
#   ARCHIVE_MEMBER (archive-member)  the binary's path inside a tar archive
#   OS_NAMES (os-names)              renames for {os}, such as darwin=macos
#   ARCH_NAMES (arch-names)          renames for {arch}, such as amd64=x86_64
#
# Exactly one of CHECKSUM, CHECKSUMS and CHECKSUMS_URL_TEMPLATE must be
# set. {os} is linux or darwin and {arch} is amd64 or arm64 unless
# renamed. The two URL templates and ARCHIVE_MEMBER take {version}, {os}
# and {arch}. CHECKSUMS never does: its keys are literal asset names, so a
# version bumped without its checksums finds no entry instead of matching
# a stale one.
#
# RUNNER_TEMP, GITHUB_PATH and GITHUB_OUTPUT must be set, as they are on
# every Actions runner. The install directory, recreated on every run, is
# appended to GITHUB_PATH and written to GITHUB_OUTPUT as install-dir.
#
# Compatible with bash 3.2, the /bin/bash on macOS: no associative arrays,
# no ${var,,}, no mapfile, and positional parameters are expanded as "$@",
# the only spelling bash 3.2 exempts from set -u when there are none
# ("${@}" fails there). tar, install and rm take short options because the
# BSD variants on macOS lack the long forms.
#
# Exit codes:
#   0  - Installed
#   64 - Invalid or missing input
#   65 - Checksum entry missing, malformed, conflicting, or mismatched
#   66 - Archive member missing from the archive, or not a regular file
#   69 - Download failed
#   71 - Unsupported operating system or architecture

set -euo pipefail

readonly E_USAGE=64
readonly E_CHECKSUM=65
readonly E_MEMBER=66
readonly E_DOWNLOAD=69
readonly E_PLATFORM=71

readonly DOWNLOAD_RETRIES=3
readonly DOWNLOAD_RETRY_DELAY=5

readonly NAME_PATTERN='^[A-Za-z0-9][A-Za-z0-9._-]*$'
readonly VERSION_PATTERN='^[A-Za-z0-9][A-Za-z0-9._+-]*$'
readonly ASSET_PATTERN='^[A-Za-z0-9][A-Za-z0-9._+~-]*$'
readonly SHA256_PATTERN='^[0-9a-f]{64}$'

# Staging directory for downloads and extraction, removed on exit.
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

# Print the canonical OS token for this runner: linux or darwin.
function detect_os() {
  local kernel
  kernel="$(uname -s)"
  case "${kernel}" in
  Linux) printf 'linux' ;;
  Darwin) printf 'darwin' ;;
  *) fail "${E_PLATFORM}" "Unsupported operating system: ${kernel}" ;;
  esac
}

# Print the canonical architecture token for this runner: amd64 or arm64.
function detect_arch() {
  local machine
  machine="$(uname -m)"
  case "${machine}" in
  x86_64) printf 'amd64' ;;
  arm64 | aarch64) printf 'arm64' ;;
  *) fail "${E_PLATFORM}" "Unsupported architecture: ${machine}" ;;
  esac
}

# Print the spelling an upstream uses for a canonical platform token.
# A key outside the canonical set is an error, so a typo cannot silently
# fall back to the default spelling.
# Arguments:
#   $1 - canonical token, e.g. darwin
#   $2 - renames as whitespace-separated key=value pairs, e.g. darwin=macos
#   $3 - space-separated canonical tokens the renames may use as keys
#   $4 - input name for error messages, e.g. os-names
# Outputs:
#   Writes the renamed token, or the canonical one, to stdout
function rename_token() {
  local token="${1}"
  local renames="${2}"
  local allowed_keys="${3}"
  local input_name="${4}"
  local result="${token}"
  local pair key value
  while IFS= read -r pair; do
    [[ -z "${pair}" ]] && continue
    if [[ "${pair}" != *=* ]]; then
      fail "${E_USAGE}" "${input_name}: expected key=value, got '${pair}'."
    fi
    key="${pair%%=*}"
    value="${pair#*=}"
    case " ${allowed_keys} " in
    *" ${key} "*) ;;
    *) fail "${E_USAGE}" "${input_name}: unknown key '${key}'; expected one of: ${allowed_keys}." ;;
    esac
    if [[ ! "${value}" =~ ${NAME_PATTERN} ]]; then
      fail "${E_USAGE}" "${input_name}: '${value}' is not a valid name for ${key}."
    fi
    if [[ "${key}" == "${token}" ]]; then
      result="${value}"
    fi
  done < <(printf '%s\n' "${renames}" | tr -s '[:space:]' '\n')
  printf '%s' "${result}"
}

# Substitute {version}, {os} and {arch} in a template. Any brace left over
# afterwards belongs to an unrecognized or misspelled placeholder, and is
# an error.
# Arguments:
#   $1 - template
#   $2 - input name for error messages
#   $3 - version
#   $4 - OS token
#   $5 - architecture token
# Outputs:
#   Writes the rendered string to stdout
function render() {
  local template="${1}"
  local input_name="${2}"
  local version="${3}"
  local os="${4}"
  local arch="${5}"
  local version_placeholder='{version}'
  local os_placeholder='{os}'
  local arch_placeholder='{arch}'
  local rendered="${template}"
  # The replacement values are validated against NAME_PATTERN or
  # VERSION_PATTERN, which keeps & and \ out of them; both are special in
  # the replacement half of ${var//pattern/replacement} on bash 5.2.
  rendered="${rendered//"${version_placeholder}"/${version}}"
  rendered="${rendered//"${os_placeholder}"/${os}}"
  rendered="${rendered//"${arch_placeholder}"/${arch}}"
  if [[ "${rendered}" == *[{}]* ]]; then
    fail "${E_USAGE}" "${input_name} has an unrecognized placeholder: ${template}" \
      "Recognized placeholders: {version}, {os}, {arch}."
  fi
  printf '%s' "${rendered}"
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
  # a CDN answering 404 briefly after a release.
  if ! curl --silent --show-error --fail --location --proto '=https' \
    --retry "${DOWNLOAD_RETRIES}" --retry-delay "${DOWNLOAD_RETRY_DELAY}" \
    --retry-all-errors --output "${destination}" "${url}"; then
    fail "${E_DOWNLOAD}" "Download failed: ${url}"
  fi
}

# Print the SHA-256 recorded for an asset in sha256sum-format text.
# Blank lines and # comments are skipped. A leading * (binary mode), any
# directory prefix and a trailing carriage return on the file name are
# ignored, so upstream files written by sha256sum, shasum or goreleaser
# all match on the bare asset name.
# Arguments:
#   $1 - asset file name
#   $2 - file holding the checksum lines
#   $3 - description of the checksum source, for error messages
# Outputs:
#   Writes the digest, lowercased, to stdout
function lookup_checksum() {
  local asset_name="${1}"
  local checksums_file="${2}"
  local source_label="${3}"
  local matches
  matches="$(awk -v name="${asset_name}" '
    NF >= 2 && $1 !~ /^#/ {
      entry = $2
      sub(/\r$/, "", entry)
      sub(/^\*/, "", entry)
      sub(/^.*\//, "", entry)
      if (entry == name) print tolower($1)
    }
  ' "${checksums_file}" | sort -u)"
  if [[ -z "${matches}" ]]; then
    fail "${E_CHECKSUM}" "No checksum entry for ${asset_name} in ${source_label}."
  fi
  local lf=$'\n'
  if [[ "${matches}" == *"${lf}"* ]]; then
    fail "${E_CHECKSUM}" "Conflicting checksum entries for ${asset_name} in ${source_label}." \
      "Entries: ${matches//"${lf}"/, }"
  fi
  printf '%s' "${matches}"
}

# Print the SHA-256 of a file, using sha256sum where it exists (Linux)
# and shasum -a 256 otherwise (macOS).
# Arguments:
#   $1 - file path
function compute_sha256() {
  local file_path="${1}"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${file_path}" | awk '{print $1}'
  else
    shasum -a 256 "${file_path}" | awk '{print $1}'
  fi
}

function main() {
  require_runner_env RUNNER_TEMP GITHUB_PATH GITHUB_OUTPUT

  local tool="${TOOL:-}"
  local version="${VERSION:-}"
  local url_template="${URL_TEMPLATE:-}"
  local checksum="${CHECKSUM:-}"
  local checksums="${CHECKSUMS:-}"
  local checksums_url_template="${CHECKSUMS_URL_TEMPLATE:-}"
  local archive_member="${ARCHIVE_MEMBER:-}"

  if [[ ! "${tool}" =~ ${NAME_PATTERN} ]]; then
    fail "${E_USAGE}" "tool must be a plain binary name matching ${NAME_PATTERN}, got '${tool}'."
  fi
  if [[ ! "${version}" =~ ${VERSION_PATTERN} ]]; then
    fail "${E_USAGE}" "version for ${tool} must match ${VERSION_PATTERN}, got '${version}'."
  fi
  if [[ "${url_template}" != https://* ]]; then
    fail "${E_USAGE}" "url-template for ${tool} must be an https:// URL, got '${url_template}'."
  fi
  if [[ -n "${checksums_url_template}" && "${checksums_url_template}" != https://* ]]; then
    fail "${E_USAGE}" "checksums-url-template for ${tool} must be an https:// URL, got '${checksums_url_template}'."
  fi
  # The URLs and the archive member reach curl, tar and the log, so none may
  # carry a line break or other control character, and a URL may not contain
  # whitespace at all.
  if [[ "${url_template}" == *[[:space:][:cntrl:]]* ]]; then
    fail "${E_USAGE}" "url-template for ${tool} must not contain whitespace or control characters."
  fi
  if [[ "${checksums_url_template}" == *[[:space:][:cntrl:]]* ]]; then
    fail "${E_USAGE}" "checksums-url-template for ${tool} must not contain whitespace or control characters."
  fi
  if [[ "${archive_member}" == *[[:cntrl:]]* ]]; then
    fail "${E_USAGE}" "archive-member for ${tool} must not contain control characters."
  fi

  local -i source_count=0
  if [[ -n "${checksum}" ]]; then
    source_count=$((source_count + 1))
  fi
  if [[ -n "${checksums}" ]]; then
    source_count=$((source_count + 1))
  fi
  if [[ -n "${checksums_url_template}" ]]; then
    source_count=$((source_count + 1))
  fi
  if ((source_count != 1)); then
    fail "${E_USAGE}" "Set exactly one of checksum, checksums and checksums-url-template for ${tool}; ${source_count} are set."
  fi

  local os arch
  os="$(detect_os)"
  arch="$(detect_arch)"
  os="$(rename_token "${os}" "${OS_NAMES:-}" 'linux darwin' 'os-names')"
  arch="$(rename_token "${arch}" "${ARCH_NAMES:-}" 'amd64 arm64' 'arch-names')"

  local asset_url asset_name
  asset_url="$(render "${url_template}" 'url-template' "${version}" "${os}" "${arch}")"
  asset_name="${asset_url##*/}"
  if [[ ! "${asset_name}" =~ ${ASSET_PATTERN} ]]; then
    fail "${E_USAGE}" "url-template for ${tool} must end in an asset file name matching ${ASSET_PATTERN}, got '${asset_name}'."
  fi

  local member=""
  if [[ -n "${archive_member}" ]]; then
    member="$(render "${archive_member}" 'archive-member' "${version}" "${os}" "${arch}")"
    # A leading '-' would reach tar as an option rather than a member name,
    # and GNU tar has options that run commands.
    if [[ "${member}" == /* || "${member}" == -* || "/${member}/" == */../* ]]; then
      fail "${E_USAGE}" "archive-member for ${tool} must be a relative path that neither starts with '-' nor contains '..', got '${member}'."
    fi
  fi

  WORK_DIR="$(mktemp -d "${RUNNER_TEMP}/${tool}-download.XXXXXX")"
  trap cleanup EXIT
  mkdir -p "${WORK_DIR}/download" "${WORK_DIR}/extract"

  # Resolve the expected digest before downloading the asset, so a missing
  # entry fails without fetching anything it could not verify.
  local expected checksums_url
  if [[ -n "${checksum}" ]]; then
    expected="$(printf '%s' "${checksum}" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')"
  elif [[ -n "${checksums}" ]]; then
    printf '%s\n' "${checksums}" >"${WORK_DIR}/checksums"
    expected="$(lookup_checksum "${asset_name}" "${WORK_DIR}/checksums" 'the checksums input')"
  else
    checksums_url="$(render "${checksums_url_template}" 'checksums-url-template' "${version}" "${os}" "${arch}")"
    download "${checksums_url}" "${WORK_DIR}/checksums"
    expected="$(lookup_checksum "${asset_name}" "${WORK_DIR}/checksums" "${checksums_url}")"
  fi
  if [[ ! "${expected}" =~ ${SHA256_PATTERN} ]]; then
    fail "${E_CHECKSUM}" "Malformed SHA-256 for ${asset_name}: '${expected}'."
  fi

  # Download to a file and verify it before anything reads the bytes; the
  # asset is never piped into tar.
  local asset_path="${WORK_DIR}/download/${asset_name}"
  download "${asset_url}" "${asset_path}"
  local actual
  actual="$(compute_sha256 "${asset_path}")"
  if [[ "${actual}" != "${expected}" ]]; then
    fail "${E_CHECKSUM}" "Checksum verification failed for ${asset_name}" \
      "Expected: ${expected}" \
      "Actual:   ${actual}"
  fi
  echo "Verified SHA-256 ${actual} for ${asset_name}" >&2

  # A fresh directory every time, so neither a directory nor a link already at
  # this path is followed when the binary is installed. tool is validated
  # above, so this is always a direct child of RUNNER_TEMP.
  local install_dir="${RUNNER_TEMP}/${tool}-bin"
  rm -rf "${install_dir}"
  mkdir "${install_dir}"
  if [[ -n "${member}" ]]; then
    # Only the named member is extracted, so documentation and man pages
    # packed beside the binary never land on disk. tar detects the
    # compression itself on both GNU tar and bsdtar, and `--` ends its
    # options so the member is never parsed as one.
    # tar's own messages can begin with the member name, so they are captured
    # and reported behind fixed text instead of reaching the log directly.
    local tar_output
    local lf=$'\n'
    if ! tar_output="$(tar -x -f "${asset_path}" -C "${WORK_DIR}/extract" -- "${member}" 2>&1)"; then
      fail "${E_MEMBER}" "Could not extract ${member} from ${asset_name}." \
        "tar reported: ${tar_output//"${lf}"/ | }" \
        "Spell archive-member exactly as 'tar -tf' lists it: GNU tar (Linux) treats" \
        "./NAME and NAME as different members, where bsdtar (macOS) accepts either."
    fi
    # The installed file must be the verified member itself, never what a
    # link inside the archive points at. find's -type f does not follow
    # symlinks, and -links 1 rules out a hard link to any other file.
    if [[ -z "$(find "${WORK_DIR}/extract/${member}" -prune -type f -links 1 2>/dev/null)" ]]; then
      fail "${E_MEMBER}" "${member} in ${asset_name} is not a regular file."
    fi
    install -m 0755 "${WORK_DIR}/extract/${member}" "${install_dir}/${tool}"
  else
    install -m 0755 "${asset_path}" "${install_dir}/${tool}"
  fi

  printf '%s\n' "${install_dir}" >>"${GITHUB_PATH}"
  printf 'install-dir=%s\n' "${install_dir}" >>"${GITHUB_OUTPUT}"
  echo "Installed ${tool} ${version} to ${install_dir}/${tool}" >&2
}

main "$@"
